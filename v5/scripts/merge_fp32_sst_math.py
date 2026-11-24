#!/usr/bin/env python3
"""SoK 実証 2: safety+math の fp32 SST-Merge 再マージスクリプト（v3 からの厳密な 1 要因修正）。

v3/scripts/mergers/sst.py との完全一致を保ちつつ、P5（数値精度によるマスク全 1 退化）の 2 点のみを修正する:
  1. v3/cache/fim/ の既存 fp32 FIM キャッシュを fp32 のまま読み込み、λ = F_h / (F_b + 1e-6) を fp32 で計算する
     （fim.py L161 の fp16 キャストを行わない）。
  2. ハードマスクを `>= threshold` ではなく `torch.topk(..., k_elements).indices` による厳密なインデックス選択にする。

v3 と完全同一に保つ事項（切り分けのため変更しない）:
  - 対象 7 モジュール（q/k/v/o/gate/up/down_proj の weight）、k = 0.20（テンソル単位）、interpolation、layer_wise = False
  - norm 層を含む対象外パラメータ: `param_util_mean + alpha * delta_safe`（Safety は LoRA のため実質 `param_util_mean`）
  - 語彙不一致の embed_tokens / lm_head（32001 vs 32000）: ベースモデルの重み `base_data.clone()`
  - 保存時の config / tokenizer: ベースモデル（meta-llama/Llama-2-7b-hf）のもの

投入前検証機能:
  - ② モデル–FIM キー・形状一致検証: ベースモデル（Llama-2-7b-hf）の全 224 対象パラメータ名・形状が、
    F_h・F_b 両方の FIM キャッシュおよび WizardMath に完全一致することを事前検証（fim.py の黙殺 0 返却経路を遮断）。
  - ③ 1 要因同等性テスト（--mask-mode v3 / --verify-v3-equivalence）:
    v3 と同一の fp16 キャスト＋`>= threshold` を再現し、既存の v3 マージ済みモデル（seed42, α=0.6）と
    全 291 テンソルで差の最大値が 0.0（完全一致）であることを検証する。

安全装置:
  - v3/ へは一切書き込まない（読み取り専用）。出力は v5/ 配下のみ。
  - fp32 モードでは全 224 対象テンソルで `|mask_ratio - k| <= 0.05` かつ `inf == 0, nan == 0` を assert で検証。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))

from v5lib.tensor_checks import TensorSource, safetensors_header_shapes  # noqa: E402

BASE_MODEL_ID = "meta-llama/Llama-2-7b-hf"
UTIL_MODEL_ID = "WizardLMTeam/WizardMath-7B-V1.0"
TARGET_MODULE_KEYWORDS = ("q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
EXPECTED_TARGET_TENSORS = 224


def is_target_weight(name: str) -> bool:
    """v3/scripts/mergers/utils.py の is_target_weight と完全同一。"""
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def assert_inside_v5(path: Path) -> Path:
    resolved = path.resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def _snapshot_has_complete_weights(snap_dir: Path) -> bool:
    """スナップショットに重みファイルが欠損なく存在するか確認する。"""
    st_index = snap_dir / "model.safetensors.index.json"
    if st_index.is_file():
        try:
            wm = json.loads(st_index.read_text(encoding="utf-8"))["weight_map"]
            return all((snap_dir / fname).is_file() for fname in set(wm.values()))
        except Exception:
            return False
    if (snap_dir / "model.safetensors").is_file():
        return True
    bin_index = snap_dir / "pytorch_model.bin.index.json"
    if bin_index.is_file():
        try:
            wm = json.loads(bin_index.read_text(encoding="utf-8"))["weight_map"]
            return all((snap_dir / fname).is_file() for fname in set(wm.values()))
        except Exception:
            return False
    return (snap_dir / "pytorch_model.bin").is_file()


def resolve_hf_snapshot_dir(model_id: str) -> Path:
    """HuggingFace キャッシュから refs/main を優先し、完全な重みを持つスナップショットを解決する。"""
    hub_roots = []
    if os.environ.get("HF_HUB_CACHE"):
        hub_roots.append(Path(os.environ["HF_HUB_CACHE"]))
    if os.environ.get("HF_HOME"):
        hub_roots.append(Path(os.environ["HF_HOME"]) / "hub")
    hub_roots.append(Path.home() / ".cache" / "huggingface" / "hub")

    repo_folder = "models--" + model_id.replace("/", "--")
    for root in hub_roots:
        repo_dir = root / repo_folder
        snaps = repo_dir / "snapshots"
        if not snaps.is_dir():
            continue
        # 1. refs/main が指す正規リビジョンを最優先
        ref_main = repo_dir / "refs" / "main"
        if ref_main.is_file():
            rev = ref_main.read_text(encoding="utf-8").strip()
            cand = snaps / rev
            if cand.is_dir() and _snapshot_has_complete_weights(cand):
                return cand
        # 2. フォールバック: 完全な重みを持つスナップショット
        for cand in sorted([p for p in snaps.iterdir() if p.is_dir()]):
            if _snapshot_has_complete_weights(cand):
                return cand
    raise FileNotFoundError(f"HF キャッシュに完全な重みを持つモデルが見つかりません: {model_id}")


def get_model_tensor_shapes(model_dir: Path) -> dict[str, list[int]]:
    """safetensors ヘッダまたは TensorSource から全テンソル名と形状を取得する。"""
    st_index = model_dir / "model.safetensors.index.json"
    st_single = model_dir / "model.safetensors"
    if st_index.is_file():
        with open(st_index, "r", encoding="utf-8") as f:
            weight_map = json.load(f)["weight_map"]
        shapes: dict[str, list[int]] = {}
        for shard_name in sorted(set(weight_map.values())):
            shapes.update(safetensors_header_shapes(model_dir / shard_name))
        return shapes
    if st_single.is_file():
        return safetensors_header_shapes(st_single)
    # PyTorch .bin フォールバック（必要テンソルのみ形状確認）
    src = TensorSource(model_dir)
    return {name: list(src.get(name).shape) for name in src.names()}


def load_fim_fp32(path: Path) -> dict[str, torch.Tensor]:
    if not path.is_file():
        raise FileNotFoundError(f"FIM キャッシュが見つかりません: {path}")
    obj = torch.load(str(path), map_location="cpu", mmap=True, weights_only=True)
    if not isinstance(obj, dict):
        raise ValueError(f"FIM キャッシュが辞書ではありません: {path}")
    return obj


def verify_model_fim_alignment(
    fim_h: dict[str, torch.Tensor],
    fim_b: dict[str, torch.Tensor],
    base_dir: Path | None = None,
    util_dir: Path | None = None,
) -> dict[str, Any]:
    """② モデルの 224 対象パラメータ名と形状が F_h・F_b（および util モデル）に完全一致することを検証する。

    v3 の fim.py `get_fim_tensor` はキー欠落時に黙ってゼロテンソルを返すため、
    ここで全 224 対象パラメータのキー存在と形状一致を厳密に確認する。
    """
    base_dir = base_dir or resolve_hf_snapshot_dir(BASE_MODEL_ID)
    util_dir = util_dir or resolve_hf_snapshot_dir(UTIL_MODEL_ID)

    base_shapes = get_model_tensor_shapes(base_dir)
    base_target_names = sorted(n for n in base_shapes if is_target_weight(n))

    if len(base_target_names) != EXPECTED_TARGET_TENSORS:
        raise AssertionError(
            f"ベースモデルの対象パラメータ数が想定({EXPECTED_TARGET_TENSORS})と不一致: {len(base_target_names)}"
        )

    missing_in_fh = [n for n in base_target_names if n not in fim_h]
    missing_in_fb = [n for n in base_target_names if n not in fim_b]
    shape_mismatch_fh = [
        {"name": n, "model": base_shapes[n], "fim_h": list(fim_h[n].shape)}
        for n in base_target_names
        if n in fim_h and list(fim_h[n].shape) != base_shapes[n]
    ]
    shape_mismatch_fb = [
        {"name": n, "model": base_shapes[n], "fim_b": list(fim_b[n].shape)}
        for n in base_target_names
        if n in fim_b and list(fim_b[n].shape) != base_shapes[n]
    ]

    # Utility モデル側（WizardMath）のキー存在確認（index のみ高速確認）
    util_src = TensorSource(util_dir)
    missing_in_util = [n for n in base_target_names if not util_src.has(n)]

    errors = []
    if missing_in_fh:
        errors.append(f"F_h 欠落キー {len(missing_in_fh)} 件 (先頭: {missing_in_fh[:3]})")
    if missing_in_fb:
        errors.append(f"F_b 欠落キー {len(missing_in_fb)} 件 (先頭: {missing_in_fb[:3]})")
    if shape_mismatch_fh:
        errors.append(f"F_h 形状不一致 {len(shape_mismatch_fh)} 件 (先頭: {shape_mismatch_fh[:2]})")
    if shape_mismatch_fb:
        errors.append(f"F_b 形状不一致 {len(shape_mismatch_fb)} 件 (先頭: {shape_mismatch_fb[:2]})")
    if missing_in_util:
        errors.append(f"Utility モデル欠落キー {len(missing_in_util)} 件 (先頭: {missing_in_util[:3]})")

    if errors:
        raise AssertionError("モデル–FIM 整合性検証に失敗: " + "; ".join(errors))

    return {
        "base_dir": str(base_dir),
        "util_dir": str(util_dir),
        "n_base_total_tensors": len(base_shapes),
        "n_base_target_tensors": len(base_target_names),
        "n_fim_h_keys": len(fim_h),
        "n_fim_b_keys": len(fim_b),
        "missing_in_fh": 0,
        "missing_in_fb": 0,
        "shape_mismatch_fh": 0,
        "shape_mismatch_fb": 0,
        "missing_in_util": 0,
        "exact_match_224": True,
        "target_names": base_target_names,
    }


def compute_mask_for_tensor(
    fh_raw: torch.Tensor,
    fb_raw: torch.Tensor,
    k_ratio: float,
    eps: float,
    mask_mode: str,
    device: str,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """1 テンソル分のマスクを計算する（mask_mode='fp32' または 'v3'）。"""
    if mask_mode == "fp32":
        fh = fh_raw.detach().to(device=device, dtype=torch.float32)
        fb = fb_raw.detach().to(device=device, dtype=torch.float32)
        lam = fh / (fb + eps)

        n_inf = int(torch.isinf(lam).sum().item())
        n_nan = int(torch.isnan(lam).sum().item())
        fh_zero = float((fh == 0).float().mean().item())
        fb_zero = float((fb == 0).float().mean().item())

        flat = lam.reshape(-1)
        numel = flat.numel()
        k_elements = max(1, int(numel * k_ratio))
        if flat.device.type == "cpu" and not torch.isnan(flat).any().item():
            arr = flat.detach().numpy()
            cut = numel - k_elements
            top_idx_np = np.argpartition(arr, cut)[cut:]
            mask_flat = torch.zeros(numel, dtype=torch.bool, device="cpu")
            mask_flat[torch.from_numpy(top_idx_np.astype(np.int64, copy=False))] = True
        else:
            top_idx = torch.topk(flat, k_elements, largest=True, sorted=False).indices
            mask_flat = torch.zeros(numel, dtype=torch.bool, device=flat.device)
            mask_flat[top_idx] = True
        mask = mask_flat.view_as(lam)
        actual_ratio = float(mask.float().mean().item())
        return mask, {
            "numel": numel,
            "k_elements": k_elements,
            "actual_mask_ratio": actual_ratio,
            "fh_zero_frac": fh_zero,
            "fb_zero_frac": fb_zero,
            "inf_count": n_inf,
            "nan_count": n_nan,
        }

    if mask_mode == "v3":
        # v3/scripts/mergers/fim.py L161 + sst.py L119-181 の完全再現
        fh = fh_raw.detach().to(device=device, dtype=torch.float16)
        fb = fb_raw.detach().to(device=device, dtype=torch.float16)
        # v3 sst.py L119-125: f_b = zeros_like; f_b += get_fim_tensor(...); f_b /= 1
        f_b = torch.zeros_like(fh)
        f_b += fb
        f_b /= 1
        lam = fh / (f_b + eps)

        n_inf = int(torch.isinf(lam).sum().item())
        n_nan = int(torch.isnan(lam).sum().item())
        fh_zero = float((fh == 0).float().mean().item())
        fb_zero = float((f_b == 0).float().mean().item())

        flat = lam.reshape(-1)
        numel = flat.numel()
        k_elements = max(1, int(numel * k_ratio))
        if flat.device.type == "cpu" and not torch.isnan(flat).any().item():
            # CPU の fp16 torch.topk は遅いため同値な np.partition で閾値を取得
            arr = flat.detach().numpy()
            idx = len(arr) - k_elements
            threshold = float(np.partition(arr, idx)[idx])
            mask = lam >= threshold
        else:
            threshold = torch.topk(flat, k_elements).values[-1]
            mask = lam >= threshold
        actual_ratio = float(mask.float().mean().item())
        return mask, {
            "numel": numel,
            "k_elements": k_elements,
            "actual_mask_ratio": actual_ratio,
            "fh_zero_frac": fh_zero,
            "fb_zero_frac": fb_zero,
            "inf_count": n_inf,
            "nan_count": n_nan,
        }

    raise ValueError(f"未知の mask_mode です: {mask_mode}")


def compute_and_verify_masks(
    fim_h: dict[str, torch.Tensor],
    fim_b: dict[str, torch.Tensor],
    target_names: list[str],
    k_ratio: float,
    eps: float,
    mask_tol: float,
    mask_mode: str,
    device: str,
    keep_masks: bool = True,
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    """全対象テンソルのマスクを計算し、fp32 モードでは退化が無いことを厳密検証する。"""
    if not target_names:
        raise RuntimeError("対象テンソル一覧が空です")

    masks: dict[str, torch.Tensor] = {}
    per_tensor: list[dict[str, Any]] = []
    ratios: list[float] = []
    max_abs_err = 0.0
    total_inf = 0
    total_nan = 0

    with torch.no_grad():
        for name in target_names:
            mask, stats = compute_mask_for_tensor(
                fh_raw=fim_h[name],
                fb_raw=fim_b[name],
                k_ratio=k_ratio,
                eps=eps,
                mask_mode=mask_mode,
                device=device,
            )
            actual_ratio = stats["actual_mask_ratio"]
            abs_err = abs(actual_ratio - k_ratio)
            if mask_mode == "fp32":
                if stats["inf_count"] > 0 or stats["nan_count"] > 0:
                    raise AssertionError(
                        f"λ に非有限値が発生しました: {name} (inf={stats['inf_count']}, nan={stats['nan_count']})"
                    )
                if abs_err > mask_tol:
                    raise AssertionError(
                        f"実効マスク比率が許容範囲 {k_ratio} ± {mask_tol} を外れました: {name} -> {actual_ratio:.6f}"
                    )

            total_inf += stats["inf_count"]
            total_nan += stats["nan_count"]
            ratios.append(actual_ratio)
            max_abs_err = max(max_abs_err, abs_err)
            per_tensor.append({"tensor": name, **stats})
            if keep_masks:
                masks[name] = mask.cpu()
            del mask

    summary = {
        "mask_mode": mask_mode,
        "k_target": k_ratio,
        "mask_tolerance": mask_tol,
        "eps": eps,
        "mask_selection": "exact_topk_indices_fp32" if mask_mode == "fp32" else "v3_fp16_ge_threshold",
        "n_target_tensors": len(per_tensor),
        "mean_mask_ratio": sum(ratios) / len(ratios),
        "min_mask_ratio": min(ratios),
        "max_mask_ratio": max(ratios),
        "max_abs_error_from_k": max_abs_err,
        "total_inf_count": total_inf,
        "total_nan_count": total_nan,
        "all_within_tolerance": all(abs(r - k_ratio) <= mask_tol for r in ratios) and total_inf == 0 and total_nan == 0,
        "per_tensor": per_tensor,
    }
    return masks, summary


def verify_v3_equivalence(
    seed: int,
    alpha: float,
    k_ratio: float,
    eps: float,
    v3_model_dir: Path | None = None,
    summary_out: Path | None = None,
) -> dict[str, Any]:
    """③ 1 要因同等性テスト: --mask-mode v3 の出力が既存の v3 マージ済みモデルと完全一致(max_abs_diff==0.0)するか検証する。"""
    if v3_model_dir is None:
        v3_model_dir = (
            V3_ROOT
            / "models"
            / "merged"
            / f"sst_merge_v3_main_diagonal_sst_main_safety+math_alpha{alpha:g}_n500_k{k_ratio:g}_FhFb_interpolation_hardmask_nolayerwise_seed{seed}"
        )
    if not v3_model_dir.is_dir():
        raise FileNotFoundError(f"比較対象の v3 マージ済みモデルが見つかりません: {v3_model_dir}")

    fim_dir = V3_ROOT / "cache" / "fim"
    fim_h_path = fim_dir / f"harmful_safety_Llama2_SafetyFT_n500_seed{seed}.pt"
    fim_b_path = fim_dir / f"benign_math_Llama2_WizardMath_n500_seed{seed}.pt"
    safe_full_dir = V3_ROOT / "models" / f"temp_safety_full_seed{seed}"
    base_dir = resolve_hf_snapshot_dir(BASE_MODEL_ID)
    util_dir = resolve_hf_snapshot_dir(UTIL_MODEL_ID)

    print(f"[v3同等性テスト] 対象 v3 モデル: {v3_model_dir.name}", flush=True)
    fim_h = load_fim_fp32(fim_h_path)
    fim_b = load_fim_fp32(fim_b_path)
    alignment = verify_model_fim_alignment(fim_h, fim_b, base_dir=base_dir, util_dir=util_dir)
    print(f"[v3同等性テスト] ② モデル–FIM 224 テンソル整合性チェック合格", flush=True)

    base_src = TensorSource(base_dir)
    util_src = TensorSource(util_dir)
    safe_src = TensorSource(safe_full_dir)
    v3_src = TensorSource(v3_model_dir)

    # PyTorch .bin シャードの再読込スラッシングを防ぐため util_src のシャード順に並べる
    # （rotary_emb.inv_freq は旧 transformers 4.31 の非永続バッファで named_parameters() に含まれないため除外）
    all_names = sorted(
        (n for n in base_src.names() if not n.endswith("rotary_emb.inv_freq")),
        key=lambda n: (str(util_src._name_to_file.get(n, "")), n),
    )
    max_abs_diff = 0.0
    worst_tensor = None
    nonzero_tensors: list[dict[str, Any]] = []
    n_target_checked = 0
    n_norm_checked = 0
    n_shape_mismatch_checked = 0
    v3_mask_ratios: list[float] = []

    with torch.no_grad():
        for name in all_names:
            base_data = base_src.get(name).to(device="cpu", dtype=torch.float16)
            v3_ref = v3_src.get(name).to(device="cpu", dtype=torch.float16)

            if not safe_src.has(name):
                reproduced = base_data.clone()
            else:
                param_safe = safe_src.get(name).to(device="cpu", dtype=torch.float16)
                delta_safe = (
                    param_safe - base_data if param_safe.shape == base_data.shape else torch.zeros_like(base_data)
                )
                param_safe_for_merge = base_data + delta_safe

                if not util_src.has(name):
                    reproduced = base_data.clone()
                    n_shape_mismatch_checked += 1
                else:
                    param_util = util_src.get(name).to(device="cpu", dtype=torch.float16)
                    if param_util.shape != base_data.shape:
                        reproduced = base_data.clone()
                        n_shape_mismatch_checked += 1
                    else:
                        delta_util = param_util - base_data
                        param_util_mean = base_data + delta_util
                        if not is_target_weight(name):
                            reproduced = param_util_mean + alpha * delta_safe
                            if "norm" in name.lower():
                                n_norm_checked += 1
                        else:
                            mask_bool, stats = compute_mask_for_tensor(
                                fh_raw=fim_h[name],
                                fb_raw=fim_b[name],
                                k_ratio=k_ratio,
                                eps=eps,
                                mask_mode="v3",
                                device="cpu",
                            )
                            v3_mask_ratios.append(stats["actual_mask_ratio"])
                            mask_f16 = mask_bool.to(dtype=torch.float16)
                            w = torch.clamp(alpha * mask_f16, 0.0, 1.0)
                            reproduced = (1.0 - w) * param_util_mean + w * param_safe_for_merge
                            n_target_checked += 1

            diff = float((reproduced.float() - v3_ref.float()).abs().max().item())
            if diff > max_abs_diff:
                max_abs_diff = diff
                worst_tensor = name
            if diff > 0.0:
                n_diff_elems = int((reproduced != v3_ref).sum().item())
                nonzero_tensors.append({"tensor": name, "max_abs_diff": diff, "n_diff_elems": n_diff_elems})

    exact_zero_disk = max_abs_diff == 0.0 and len(nonzero_tensors) == 0

    # 保存済み v3 モデルは GPU 生成のため、CPU との fp16 除算 1 ULP 境界差が極少数出ることがある。
    # 差分テンソルがあれば同一プロセス内で v3/scripts/mergers/sst.py の merge_sst と直接照合し、0.0 一致を確認する。
    in_process_max_abs_diff = 0.0
    in_process_checked_tensors = 0
    if nonzero_tensors:
        v3_scripts_str = str(V3_ROOT / "scripts")
        if v3_scripts_str not in sys.path:
            sys.path.insert(0, v3_scripts_str)
        from mergers.sst import merge_sst as v3_merge_sst  # type: ignore

        class _DummyModel:
            def __init__(self, sd: dict[str, torch.Tensor]) -> None:
                self._sd = sd
                self.config = type("Cfg", (), {"num_hidden_layers": 32})()

            def state_dict(self) -> dict[str, torch.Tensor]:
                return self._sd

            def named_parameters(self):
                return list(self._sd.items())

        diff_names = [x["tensor"] for x in nonzero_tensors]
        b_sd = {n: base_src.get(n).to(device="cpu", dtype=torch.float16) for n in diff_names}
        u_sd = {n: util_src.get(n).to(device="cpu", dtype=torch.float16) for n in diff_names}
        s_sd = {n: safe_src.get(n).to(device="cpu", dtype=torch.float16) for n in diff_names}
        v3_proc_out, _ = v3_merge_sst(
            base_model=_DummyModel(b_sd),
            util_models_dict={"math": _DummyModel(u_sd)},
            safe_model=_DummyModel(s_sd),
            method="diagonal_sst",
            sst_ratio="Fh/Fb",
            variant="interpolation",
            mask_type="hard mask",
            layer_wise=False,
            layer_prior="uniform",
            alpha=alpha,
            k_ratio=k_ratio,
            fim_b_dict={"math": {n: fim_b[n] for n in diff_names}},
            fim_h={n: fim_h[n] for n in diff_names},
        )
        with torch.no_grad():
            for n in diff_names:
                m_bool, _ = compute_mask_for_tensor(fim_h[n], fim_b[n], k_ratio, eps, "v3", "cpu")
                pu = b_sd[n] + (u_sd[n] - b_sd[n])
                ps = b_sd[n] + (s_sd[n] - b_sd[n])
                w = torch.clamp(alpha * m_bool.to(dtype=torch.float16), 0.0, 1.0)
                ours = (1.0 - w) * pu + w * ps
                d = float((ours.float() - v3_proc_out[n].float()).abs().max().item())
                in_process_max_abs_diff = max(in_process_max_abs_diff, d)
                in_process_checked_tensors += 1

    exact_zero_in_process = in_process_max_abs_diff == 0.0
    result = {
        "check": "v3_single_factor_equivalence",
        "seed": seed,
        "alpha": alpha,
        "k_ratio": k_ratio,
        "eps": eps,
        "v3_reference_model": str(v3_model_dir),
        "safe_full_source": str(safe_full_dir),
        "alignment": {k: v for k, v in alignment.items() if k != "target_names"},
        "n_total_tensors_checked": len(all_names),
        "n_target_tensors_checked": n_target_checked,
        "n_norm_tensors_checked": n_norm_checked,
        "n_shape_mismatch_tensors_checked": n_shape_mismatch_checked,
        "v3_reproduced_mean_mask_ratio": sum(v3_mask_ratios) / len(v3_mask_ratios),
        "v3_reproduced_all1_tensors": sum(1 for r in v3_mask_ratios if r > 0.99),
        "disk_gpu_max_abs_diff": max_abs_diff,
        "disk_gpu_worst_tensor": worst_tensor,
        "disk_gpu_n_nonzero_diff_tensors": len(nonzero_tensors),
        "disk_gpu_total_diff_elems": sum(x["n_diff_elems"] for x in nonzero_tensors),
        "disk_gpu_nonzero_tensors_sample": nonzero_tensors[:20],
        "exact_zero_match_disk_gpu": exact_zero_disk,
        "in_process_v3_merge_sst_checked_tensors": in_process_checked_tensors,
        "in_process_v3_merge_sst_max_abs_diff": in_process_max_abs_diff,
        "exact_zero_match_in_process": exact_zero_in_process,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    if summary_out is not None:
        out_path = assert_inside_v5(summary_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[v3同等性テスト] 結果保存: {out_path}", flush=True)

    print(
        f"[v3同等性テスト] 全 {len(all_names)} テンソル検証完了: "
        f"disk(GPU保存)差={max_abs_diff:.8g} ({len(nonzero_tensors)}テンソル/{result['disk_gpu_total_diff_elems']}要素), "
        f"同一プロセス v3.merge_sst 差={in_process_max_abs_diff:.8g}, "
        f"v3再現マスク平均={result['v3_reproduced_mean_mask_ratio']:.4f} "
        f"(全1テンソル={result['v3_reproduced_all1_tensors']}/224)",
        flush=True,
    )
    if not exact_zero_in_process:
        raise AssertionError(
            f"同一プロセス v3.merge_sst と完全一致しませんでした: in_process_max_abs_diff={in_process_max_abs_diff}"
        )
    return result


def run_merge_for_seed(
    seed: int,
    alphas: list[float],
    k_ratio: float,
    eps: float,
    mask_tol: float,
    mask_mode: str,
    out_models_root: Path,
    device: str,
    verify_only: bool,
    force: bool,
) -> dict[str, Any]:
    fim_dir = V3_ROOT / "cache" / "fim"
    fim_h_path = fim_dir / f"harmful_safety_Llama2_SafetyFT_n500_seed{seed}.pt"
    fim_b_path = fim_dir / f"benign_math_Llama2_WizardMath_n500_seed{seed}.pt"
    safety_lora_path = V3_ROOT / "models" / f"safety_lora_seed{seed}"

    print(f"[seed{seed}] fp32 FIM を読み込み中: {fim_h_path.name}, {fim_b_path.name}", flush=True)
    fim_h = load_fim_fp32(fim_h_path)
    fim_b = load_fim_fp32(fim_b_path)

    # ② モデル–FIM キー・形状一致の事前検証（全 224 対象テンソル）
    alignment = verify_model_fim_alignment(fim_h=fim_h, fim_b=fim_b)
    target_names = alignment["target_names"]
    print(
        f"[seed{seed}] ② モデル–FIM 整合性検証合格: "
        f"target={alignment['n_base_target_tensors']}/224, missing_fh=0, missing_fb=0, shape_mismatch=0",
        flush=True,
    )

    masks, mask_summary = compute_and_verify_masks(
        fim_h=fim_h,
        fim_b=fim_b,
        target_names=target_names,
        k_ratio=k_ratio,
        eps=eps,
        mask_tol=mask_tol,
        mask_mode=mask_mode,
        device=device,
        keep_masks=not verify_only,
    )
    del fim_h, fim_b
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    print(
        f"[seed{seed}] マスク検証完了 (mode={mask_mode}): n={mask_summary['n_target_tensors']}, "
        f"mean={mask_summary['mean_mask_ratio']:.6f}, "
        f"range=[{mask_summary['min_mask_ratio']:.6f}, {mask_summary['max_mask_ratio']:.6f}], "
        f"inf={mask_summary['total_inf_count']}, nan={mask_summary['total_nan_count']}",
        flush=True,
    )

    alignment_compact = {k: v for k, v in alignment.items() if k != "target_names"}
    if verify_only:
        return {
            "seed": seed,
            "mask_mode": mask_mode,
            "fim_h_path": str(fim_h_path),
            "fim_b_path": str(fim_b_path),
            "alignment": alignment_compact,
            "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
            "n_target_tensors": mask_summary["n_target_tensors"],
        }

    prefix = "fp32_sst" if mask_mode == "fp32" else "v3repro_sst"
    pending_alphas = []
    for alpha in alphas:
        mdir = out_models_root / f"{prefix}_safety+math_alpha{alpha:.1f}_n500_k{k_ratio:g}_seed{seed}"
        if not force and (mdir / "merge_metadata.json").is_file() and (
            (mdir / "model.safetensors").is_file() or (mdir / "model.safetensors.index.json").is_file()
        ):
            print(f"[seed{seed} α={alpha:.1f}] 既存マージ済みモデルをスキップ: {mdir.name}", flush=True)
        else:
            pending_alphas.append(alpha)

    if not pending_alphas:
        return {
            "seed": seed,
            "skipped": True,
            "alignment": alignment_compact,
            "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
        }

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[seed{seed}] モデル読み込み中 (base, safety_lora, WizardMath) on {device}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, use_fast=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, torch_dtype=torch.float16)
    base_state = {k: v.detach().cpu() for k, v in base_model.state_dict().items()}
    base_param_names = [n for n, _ in base_model.named_parameters()]

    safety_base = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, torch_dtype=torch.float16)
    if device.startswith("cuda"):
        safety_base = safety_base.to(device)
    safe_model = PeftModel.from_pretrained(safety_base, str(safety_lora_path)).merge_and_unload()
    safe_state = {k: v.detach().cpu() for k, v in safe_model.state_dict().items()}
    del safety_base, safe_model
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    util_model = AutoModelForCausalLM.from_pretrained(UTIL_MODEL_ID, torch_dtype=torch.float16)
    util_state = {k: v.detach().cpu() for k, v in util_model.state_dict().items()}
    del util_model

    saved_dirs: list[str] = []
    with torch.no_grad():
        for alpha in pending_alphas:
            model_name = f"{prefix}_safety+math_alpha{alpha:.1f}_n500_k{k_ratio:g}_seed{seed}"
            out_dir = assert_inside_v5(out_models_root / model_name)
            out_dir.mkdir(parents=True, exist_ok=True)
            merged_state: dict[str, torch.Tensor] = {}
            norm_preserved_count = 0
            shape_mismatch_names: list[str] = []
            target_merged_count = 0

            for name in base_param_names:
                base_data = base_state[name].to(device=device, dtype=torch.float16)
                if name not in safe_state:
                    merged_state[name] = base_data.cpu()
                    continue

                param_safe = safe_state[name].to(device=device, dtype=torch.float16)
                delta_safe = (
                    param_safe - base_data if param_safe.shape == base_data.shape else torch.zeros_like(base_data)
                )
                param_safe_for_merge = base_data + delta_safe

                if name not in util_state or util_state[name].shape != base_data.shape:
                    # v3/scripts/mergers/sst.py L53-55 と完全同一（vocab 32001 の embed/lm_head は base_data）
                    merged_state[name] = base_data.cpu()
                    shape_mismatch_names.append(name)
                    continue

                param_util = util_state[name].to(device=device, dtype=torch.float16)
                delta_util = param_util - base_data
                param_util_mean = base_data + delta_util

                if not is_target_weight(name):
                    # v3/scripts/mergers/sst.py L103-105 と完全同一（norm 層等は param_util_mean + alpha * delta_safe）
                    merged_state[name] = (param_util_mean + alpha * delta_safe).cpu()
                    if "norm" in name.lower():
                        norm_preserved_count += 1
                    continue

                # 対象 7 モジュール: マスクによる interpolation（v3 sst.py L191-192 と同式）
                mask_f16 = masks[name].to(device=device, dtype=torch.float16)
                w = torch.clamp(alpha * mask_f16, 0.0, 1.0)
                merged_state[name] = ((1.0 - w) * param_util_mean + w * param_safe_for_merge).cpu()
                target_merged_count += 1

            assert target_merged_count == mask_summary["n_target_tensors"], (
                f"対象テンソル数不一致: {target_merged_count} != {mask_summary['n_target_tensors']}"
            )
            base_model.load_state_dict(merged_state, strict=False)
            base_model.save_pretrained(str(out_dir))
            tokenizer.save_pretrained(str(out_dir))

            meta = {
                "status": "success",
                "experiment": "sok_exp2_fp32_sst_math",
                "method": "diagonal_sst_fp32_indextopk" if mask_mode == "fp32" else "diagonal_sst_v3_repro",
                "mask_mode": mask_mode,
                "pattern": "safety+math",
                "seed": seed,
                "alpha": alpha,
                "k_ratio": k_ratio,
                "eps": eps,
                "variant": "interpolation",
                "layer_wise": False,
                "base_model": BASE_MODEL_ID,
                "util_model": UTIL_MODEL_ID,
                "safety_lora_path": str(safety_lora_path),
                "fim_h_path": str(fim_h_path),
                "fim_b_path": str(fim_b_path),
                "norm_handling": "identical_to_v3_sst_py_L103_105",
                "norm_tensors_count": norm_preserved_count,
                "shape_mismatch_tensors_kept_base": shape_mismatch_names,
                "model_fim_alignment": alignment_compact,
                "mask_verification": mask_summary,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            with open(out_dir / "merge_metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            saved_dirs.append(str(out_dir))
            print(
                f"[seed{seed} α={alpha:.1f}] 保存完了: {out_dir.name} "
                f"(target={target_merged_count}, norm={norm_preserved_count}, "
                f"mean_mask={mask_summary['mean_mask_ratio']:.6f})",
                flush=True,
            )

    del base_model, base_state, safe_state, util_state, masks
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    return {
        "seed": seed,
        "mask_mode": mask_mode,
        "alignment": alignment_compact,
        "saved_dirs": saved_dirs,
        "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ap.add_argument("--k", type=float, default=0.20)
    ap.add_argument("--eps", type=float, default=1e-6)
    ap.add_argument("--mask-tol", type=float, default=0.05)
    ap.add_argument("--mask-mode", default="fp32", choices=["fp32", "v3"], help="fp32=P5修正版 / v3=既存v3再現版")
    ap.add_argument("--out-models-root", type=Path, default=V5_ROOT / "models" / "fp32_sst_math")
    ap.add_argument("--summary-out", type=Path, default=V5_ROOT / "outputs" / "sok_exp2" / "mask_verification_summary.json")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--verify-mask-only", action="store_true", help="重みを保存せず、②整合性＋全対象テンソルマスク比率のみ検証する")
    ap.add_argument(
        "--verify-v3-equivalence",
        action="store_true",
        help="③ --mask-mode v3 が既存 v3 モデル（seed42, α=0.6）と全テンソル完全一致するか検証する",
    )
    ap.add_argument("--v3-ref-model", type=Path, default=None, help="--verify-v3-equivalence 用の参照 v3 モデルパス")
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    assert_inside_v5(args.out_models_root)
    assert_inside_v5(args.summary_out)

    if args.verify_v3_equivalence:
        verify_v3_equivalence(
            seed=args.seeds[0],
            alpha=args.alphas[0] if len(args.alphas) == 1 else 0.6,
            k_ratio=args.k,
            eps=args.eps,
            v3_model_dir=args.v3_ref_model,
            summary_out=args.summary_out,
        )
        return 0

    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    if args.verify_mask_only:
        device = "cpu"

    results = []
    for seed in args.seeds:
        res = run_merge_for_seed(
            seed=seed,
            alphas=args.alphas,
            k_ratio=args.k,
            eps=args.eps,
            mask_tol=args.mask_tol,
            mask_mode=args.mask_mode,
            out_models_root=args.out_models_root,
            device=device,
            verify_only=args.verify_mask_only,
            force=args.force,
        )
        results.append(res)

    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "verify_mask_only" if args.verify_mask_only else "full_merge",
        "mask_mode": args.mask_mode,
        "k_ratio": args.k,
        "mask_tol": args.mask_tol,
        "eps": args.eps,
        "alphas": args.alphas,
        "seeds": args.seeds,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with open(args.summary_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"サマリー保存: {args.summary_out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
