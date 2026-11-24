"""V1〜V9 のテンソル計算（CPU 専用、読み取り専用。FR2.2、NFR2、NFR4）。

- GPU は使わない。テンソルは ``device="cpu"`` に固定し、``cuda`` が使えても使わない。
- 重みや FIM は、テンソルを 1 つずつ読む（``torch.load(..., mmap=True, weights_only=True)``、
  safetensors は ``safe_open`` でテンソル単位）。全体をメモリに載せない。
- 計算の再現は ``v3/scripts/mergers/sst.py`` L119-181 と同じ（fp16 キャスト、
  ``λ = F_h / (F̄_b + 1e-6)``、top-k、``>=``）。

torch と safetensors は、関数の中で import する（このモジュール自体は torch が無くても import できる）。
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np

DEVICE = "cpu"  # 固定。cuda が使えても使わない

TARGET_MODULE_KEYWORDS = ("q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


class TensorLoadError(RuntimeError):
    """テンソルやキャッシュを読めないときの例外（呼び出し側が「判定不能」の理由として記録する）。"""


def is_target_weight(name: str) -> bool:
    """SST の対象テンソルか（v3/scripts/mergers/utils.py の ``is_target_weight`` と同じ）。"""
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def _torch():
    import torch  # 遅延 import

    return torch


# ---------------------------------------------------------------------------
# 読み込み（1 テンソルずつ）
# ---------------------------------------------------------------------------


def load_fim_lazy(path: str | os.PathLike[str]):
    """FIM キャッシュ（``.pt``）を mmap で開く。値は、アクセスしたテンソルだけが読まれる。

    読めなければ ``TensorLoadError``（旧形式で mmap できない、壊れている、など）。
    """
    torch = _torch()
    try:
        obj = torch.load(str(path), map_location="cpu", mmap=True, weights_only=True)
    except Exception as exc:  # 形式の違い、壊れたファイル、ファイルなし。理由を残して呼び出し側に任せる
        raise TensorLoadError(f"FIM キャッシュを読めません: {path}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(obj, dict):
        raise TensorLoadError(f"FIM キャッシュが辞書ではありません: {path}（{type(obj).__name__}）")
    return obj


class TensorSource:
    """モデルのフォルダ（safetensors または PyTorch .bin の単一・分割）を、テンソル単位で読む。"""

    def __init__(self, model_dir: str | os.PathLike[str]):
        self.model_dir = Path(model_dir)
        if not self.model_dir.is_dir():
            raise TensorLoadError(f"モデルのフォルダがありません: {self.model_dir}")
        self._name_to_file: dict[str, Path] = {}
        self._format: str = "safetensors"
        self._cached_bin_path: Path | None = None
        self._cached_bin_dict: dict[str, Any] | None = None

        st_index = self.model_dir / "model.safetensors.index.json"
        st_single = self.model_dir / "model.safetensors"
        bin_index = self.model_dir / "pytorch_model.bin.index.json"
        bin_single = self.model_dir / "pytorch_model.bin"
        try:
            if st_index.is_file():
                self._format = "safetensors"
                with open(st_index, "r", encoding="utf-8") as handle:
                    weight_map = json.load(handle)["weight_map"]
                for name, fname in weight_map.items():
                    self._name_to_file[name] = self.model_dir / fname
            elif st_single.is_file():
                self._format = "safetensors"
                from safetensors import safe_open

                with safe_open(str(st_single), framework="pt", device=DEVICE) as handle:
                    for name in handle.keys():
                        self._name_to_file[name] = st_single
            elif bin_index.is_file():
                self._format = "pytorch_bin"
                with open(bin_index, "r", encoding="utf-8") as handle:
                    weight_map = json.load(handle)["weight_map"]
                for name, fname in weight_map.items():
                    self._name_to_file[name] = self.model_dir / fname
            elif bin_single.is_file():
                self._format = "pytorch_bin"
                data = self._load_bin(bin_single)
                for name in data.keys():
                    self._name_to_file[name] = bin_single
            else:
                raise TensorLoadError(f"重みファイル（safetensors / pytorch_model.bin）が見つかりません: {self.model_dir}")
        except TensorLoadError:
            raise
        except Exception as exc:
            raise TensorLoadError(f"重みの目録を読めません: {self.model_dir}: {exc}") from exc

    def _load_bin(self, path: Path) -> dict[str, Any]:
        """PyTorch .bin シャードを CPU で読み込む（直近 1 シャードのみ保持）。"""
        if self._cached_bin_path == path and self._cached_bin_dict is not None:
            return self._cached_bin_dict
        self._cached_bin_path = None
        self._cached_bin_dict = None
        torch = _torch()
        try:
            obj = torch.load(str(path), map_location="cpu", mmap=True, weights_only=True)
        except Exception:
            try:
                obj = torch.load(str(path), map_location="cpu", weights_only=True)
            except Exception as exc:
                raise TensorLoadError(f"PyTorch .bin を読めません: {path}: {exc}") from exc
        if not isinstance(obj, dict):
            raise TensorLoadError(f"PyTorch .bin が辞書ではありません: {path}（{type(obj).__name__}）")
        self._cached_bin_path = path
        self._cached_bin_dict = obj
        return obj

    def names(self) -> list[str]:
        return sorted(self._name_to_file)

    def has(self, name: str) -> bool:
        return name in self._name_to_file

    def get(self, name: str):
        """1 テンソルだけを読む（CPU）。"""
        path = self._name_to_file.get(name)
        if path is None:
            raise TensorLoadError(f"{self.model_dir} にテンソルがありません: {name}")
        if self._format == "pytorch_bin":
            data = self._load_bin(path)
            if name not in data:
                raise TensorLoadError(f"{path} にテンソルがありません: {name}")
            return data[name].to(device=DEVICE)
        from safetensors import safe_open

        try:
            with safe_open(str(path), framework="pt", device=DEVICE) as handle:
                return handle.get_tensor(name)
        except Exception as exc:
            raise TensorLoadError(f"テンソルを読めません: {path}:{name}: {exc}") from exc


def safetensors_header_shapes(path: str | os.PathLike[str]) -> dict[str, list[int]]:
    """safetensors のヘッダだけを読み、テンソルの形を返す（重みは読まない）。"""
    try:
        with open(path, "rb") as handle:
            header_len = int.from_bytes(handle.read(8), "little")
            if header_len <= 0 or header_len > 100_000_000:
                raise TensorLoadError(f"ヘッダの長さが不正です: {path}: {header_len}")
            header = json.loads(handle.read(header_len).decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise TensorLoadError(f"safetensors のヘッダを読めません: {path}: {exc}") from exc
    return {k: list(v["shape"]) for k, v in header.items() if k != "__metadata__"}


# ---------------------------------------------------------------------------
# V1: 0 の割合
# ---------------------------------------------------------------------------


def zero_fraction(tensor, via_fp16: bool = True) -> float:
    """テンソルの 0 の割合。``via_fp16=True`` は fp16 にキャストした後（V1 の主指標）。"""
    torch = _torch()
    t = tensor.detach().to(device=DEVICE)
    if via_fp16:
        t = t.half()
    return float((t == 0).float().mean().item())


# ---------------------------------------------------------------------------
# V2: λ、マスク、inf
# ---------------------------------------------------------------------------


def lambda_fhfb(fim_h, fim_b_list: Iterable, eps: float = 1e-6):
    """``λ = F_h / (F̄_b + eps)`` を、sst.py と同じ fp16 の演算で求める。

    F_h と各 F_b は fp16 にキャストし、F̄_b は fp16 のまま合計して個数で割る（sst.py L119-127）。
    """
    torch = _torch()
    fb_list = list(fim_b_list)
    f_h = fim_h.detach().to(device=DEVICE, dtype=torch.float16)
    f_b = torch.zeros_like(f_h)
    for fb in fb_list:
        f_b += fb.detach().to(device=DEVICE, dtype=torch.float16)
    f_b /= max(len(fb_list), 1)
    return f_h / (f_b + eps)


def topk_mask(values, k_ratio: float):
    """sst.py L177-181 と同じ hard mask: 上位 k の閾値を取り、``>=`` で選ぶ（同値はすべて含まれる）。"""
    torch = _torch()
    flat = values.reshape(-1)
    k_elements = max(1, int(flat.numel() * k_ratio))
    if flat.device.type == "cpu" and not torch.isnan(flat).any().item():
        arr = flat.detach().numpy()
        idx = len(arr) - k_elements
        threshold = float(np.partition(arr, idx)[idx])
        return values >= threshold
    threshold = torch.topk(flat, k_elements).values[-1]
    return values >= threshold


def mask_ratio(mask) -> float:
    """マスクの 1 の割合。"""
    return float(mask.float().mean().item())


def inf_count(values) -> int:
    """inf（正負）の数。"""
    torch = _torch()
    return int(torch.isinf(values).sum().item())


# ---------------------------------------------------------------------------
# V3: Jaccard と順位相関
# ---------------------------------------------------------------------------


def jaccard(mask_a, mask_b) -> float:
    """2 つの真偽マスクの Jaccard 係数。両方が空なら 1.0（同じ集合）。"""
    a = mask_a.reshape(-1).bool()
    b = mask_b.reshape(-1).bool()
    inter = int((a & b).sum().item())
    union = int((a | b).sum().item())
    return 1.0 if union == 0 else inter / union


def random_mask(shape, k_ratio: float, seed: int):
    """seed 固定の一様乱数で top-k マスクを作る（NFR1）。"""
    torch = _torch()
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    return topk_mask(torch.rand(tuple(shape), generator=generator), k_ratio)


def rankdata_average(values: np.ndarray) -> np.ndarray:
    """同順位に平均順位を付ける順位（1 始まり）。scipy に依存しない（ベクトル化版）。"""
    values = np.asarray(values)
    n = len(values)
    if n == 0:
        return np.empty(0, dtype=np.float64)
    order = np.argsort(values, kind="mergesort")
    sorted_vals = values[order]
    diff = np.empty(n, dtype=bool)
    diff[0] = True
    diff[1:] = sorted_vals[1:] != sorted_vals[:-1]
    starts = np.flatnonzero(diff)
    ends = np.empty_like(starts)
    ends[:-1] = starts[1:] - 1
    ends[-1] = n - 1
    counts = ends - starts + 1
    avg_ranks = (starts + ends) / 2.0 + 1.0
    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = np.repeat(avg_ranks, counts)
    return ranks


def _to_numpy(values) -> np.ndarray:
    """torch のテンソルまたは配列を、1 次元の float64 の numpy 配列にする。"""
    if hasattr(values, "detach"):
        return values.detach().reshape(-1).float().cpu().numpy().astype(np.float64)
    return np.asarray(values, dtype=np.float64).reshape(-1)


def spearman(x, y, max_samples: int = 1_000_000, seed: int = 0) -> float | None:
    """スピアマンの順位相関。座標数が ``max_samples`` を超えるときは、seed 固定で部分抽出する。

    どちらかが定数（順位の分散が 0）なら ``None``。
    """
    xa, ya = _to_numpy(x), _to_numpy(y)
    if xa.shape != ya.shape:
        raise ValueError(f"形が違います: {xa.shape} と {ya.shape}")
    finite = np.isfinite(xa) & np.isfinite(ya)
    xa, ya = xa[finite], ya[finite]
    if len(xa) > max_samples:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(xa), size=max_samples, replace=False)
        xa, ya = xa[idx], ya[idx]
    if len(xa) < 2:
        return None
    rx, ry = rankdata_average(xa), rankdata_average(ya)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = math.sqrt(float((rx * rx).sum()) * float((ry * ry).sum()))
    if denom == 0.0:
        return None
    return float((rx * ry).sum() / denom)


# ---------------------------------------------------------------------------
# V4: fp16 の丸め
# ---------------------------------------------------------------------------


def ulp_fp16(tensor):
    """fp16 での 1 ulp（その値の隣との間隔）を float32 で返す。

    正規数は ``2^(floor(log2|x|) - 10)``。fp16 の非正規数の範囲（|x| < 2^-14）は 2^-24。
    """
    torch = _torch()
    x = tensor.detach().float().abs().clamp_min(2.0 ** -14)
    exponent = torch.floor(torch.log2(x))
    return torch.pow(2.0, exponent - 10.0)


def frac_below_half_ulp(theta_u, delta_s, alpha: float) -> float:
    """``|α·δ_s| < ulp_fp16(θ_u)/2`` となる座標の割合（V4。足しても fp16 で丸められて消える座標）。"""
    torch = _torch()
    half_ulp = ulp_fp16(theta_u.half()) / 2.0
    lost = (alpha * delta_s.detach().float()).abs() < half_ulp
    return float(lost.float().mean().item())


# ---------------------------------------------------------------------------
# V5、V6
# ---------------------------------------------------------------------------


def relative_difference(theta_u, theta_0) -> float:
    """相対差分 ‖θ_u − θ₀‖ / ‖θ₀‖（float32 で計算）。‖θ₀‖ が 0 なら NaN。"""
    diff = theta_u.detach().float() - theta_0.detach().float()
    denom = float(theta_0.detach().float().norm().item())
    return float(diff.norm().item() / denom) if denom > 0 else float("nan")


def injection(theta_merged, theta_u, delta_s) -> tuple[float, float]:
    """(‖θ_merged − θ_u‖, ⟨θ_merged − θ_u, δ_s⟩)。float32 で計算する（V5）。"""
    moved = theta_merged.detach().float() - theta_u.detach().float()
    return float(moved.norm().item()), float((moved * delta_s.detach().float()).sum().item())
