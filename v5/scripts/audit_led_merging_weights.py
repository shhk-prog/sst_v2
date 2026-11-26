#!/usr/bin/env python3
"""指示書 v2 §2.5 #2 / §4.2: LED-Merging マージ済みモデルの重み退化・マスク実効割合監査（CPU・単精度専用）。

背景:
  v3 の LED-Merging (safety+math) の GSM8K Alpaca-CoT 正答率が 1.88%（Llama-2-7b-hf ベース単体の 1.88% と完全一致）だった。
  マスクが空／極小になりベースモデルがそのまま出力されている可能性を、指示書 v2 §4.2 の統計（単精度計算）で検証する。

計算する統計（単精度 fp32、ストリーミング集計）:
  1. マージ後タスクベクトル Δ_m = W_merged - W_base と
     分野専門タスクベクトル Δ_u = W_util - W_base、安全タスクベクトル Δ_s = W_safe - W_base の cos 類似度（全体＋層ごと）
  2. 分野更新の残存率（射影係数）: <Δ_m, Δ_u> / ||Δ_u||^2 および安全更新の射影係数: <Δ_m, Δ_s> / ||Δ_s||^2
  3. ベース・分野・安全モデルとの差の相対 L2 ノルム（||W_m - W_x|| / ||W_x||）
  4. 更新されたテンソル数・未更新テンソル数・未更新テンソル例・要素単位のベース一致率（|W_m - W_b| == 0）
  5. 退化判定（既定: いずれかの入力/ベースとの相対差 < 1% または 分野更新残存率 < 10%）

制約: CPU 専用・v3/ は読み取り専用。--run-dir 指定時は <run_dir>/outputs/ および <run_dir>/summary.json に出力する。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch  # noqa: E402
from safetensors import safe_open  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from merge_fp32_sst_math import resolve_hf_snapshot_dir  # noqa: E402
from v5lib.safeio import write_json, write_text  # noqa: E402

LAYER_RE = re.compile(r"^model\.layers\.(\d+)\.")


def _layer_group(name: str) -> str:
    m = LAYER_RE.match(name)
    if m:
        return f"layer_{int(m.group(1)):02d}"
    if "embed_tokens" in name:
        return "embed_tokens"
    if "lm_head" in name:
        return "lm_head"
    if name.startswith("model.norm"):
        return "final_norm"
    return "other"


class LazyWeights:
    """safetensors（単一/シャード）および pytorch_model*.bin の両方をシャードキャッシュ付きで遅延読み込みする。"""

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        self._st_index = model_dir / "model.safetensors.index.json"
        self._st_single = model_dir / "model.safetensors"
        self._bin_index = model_dir / "pytorch_model.bin.index.json"
        self._bin_single = model_dir / "pytorch_model.bin"
        self._name_to_file: dict[str, Path] = {}
        self._kind: str = ""
        self._cache_file: Path | None = None
        self._cache_dict: dict[str, torch.Tensor] | None = None
        self._st_handles: dict[Path, Any] = {}

        if self._st_index.is_file():
            self._kind = "st"
            wm = json.loads(self._st_index.read_text(encoding="utf-8"))["weight_map"]
            self._name_to_file = {k: model_dir / v for k, v in wm.items()}
        elif self._st_single.is_file():
            self._kind = "st"
            with safe_open(str(self._st_single), framework="pt", device="cpu") as f:
                for k in f.keys():
                    self._name_to_file[k] = self._st_single
        elif self._bin_index.is_file():
            self._kind = "bin"
            wm = json.loads(self._bin_index.read_text(encoding="utf-8"))["weight_map"]
            self._name_to_file = {k: model_dir / v for k, v in wm.items()}
        elif self._bin_single.is_file():
            self._kind = "bin"
            sd = torch.load(str(self._bin_single), map_location="cpu", weights_only=True)
            for k in sd.keys():
                self._name_to_file[k] = self._bin_single
            self._cache_file = self._bin_single
            self._cache_dict = sd
        else:
            raise FileNotFoundError(f"モデル重みが見つかりません: {model_dir}")

    def keys(self) -> list[str]:
        return list(self._name_to_file.keys())

    def file_for(self, name: str) -> str:
        return str(self._name_to_file.get(name, ""))

    def get_fp32(self, name: str) -> torch.Tensor | None:
        fpath = self._name_to_file.get(name)
        if fpath is None:
            return None
        if self._kind == "st":
            handle = self._st_handles.get(fpath)
            if handle is None:
                handle = safe_open(str(fpath), framework="pt", device="cpu")
                self._st_handles[fpath] = handle
            return handle.get_tensor(name).to(torch.float32)
        if self._cache_file != fpath or self._cache_dict is None:
            self._cache_dict = None
            self._cache_dict = torch.load(str(fpath), map_location="cpu", weights_only=True)
            self._cache_file = fpath
        return self._cache_dict[name].to(torch.float32)

    def close(self) -> None:
        self._st_handles.clear()
        self._cache_dict = None
        self._cache_file = None


def _align_vocab(t_ref: torch.Tensor, t_other: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """vocab 拡張（32000 vs 32001）があるテンソルは共通の先頭スライス（32000 行）で比較する。"""
    if t_ref.shape == t_other.shape:
        return t_ref, t_other
    if t_ref.ndim == t_other.ndim and t_ref.shape[1:] == t_other.shape[1:]:
        n0 = min(t_ref.shape[0], t_other.shape[0])
        return t_ref[:n0], t_other[:n0]
    raise ValueError(f"形状不一致: {t_ref.shape} vs {t_other.shape}")


def _new_acc() -> dict[str, float]:
    return {
        "n_elem": 0,
        "n_eq_base": 0,
        "n_eq_util": 0,
        "n_eq_safe": 0,
        "norm_b2": 0.0,
        "norm_u2": 0.0,
        "norm_s2": 0.0,
        "norm_dm2": 0.0,
        "norm_du2": 0.0,
        "norm_ds2": 0.0,
        "diff_mu2": 0.0,
        "diff_ms2": 0.0,
        "dot_dm_du": 0.0,
        "dot_dm_ds": 0.0,
    }


def _finalize_acc(acc: dict[str, float]) -> dict[str, float | int | None]:
    nb = math.sqrt(acc["norm_b2"])
    nu = math.sqrt(acc["norm_u2"])
    ns = math.sqrt(acc["norm_s2"])
    ndm = math.sqrt(acc["norm_dm2"])
    ndu = math.sqrt(acc["norm_du2"])
    nds = math.sqrt(acc["norm_ds2"])
    dmu = math.sqrt(acc["diff_mu2"])
    dms = math.sqrt(acc["diff_ms2"])

    return {
        "n_elem": int(acc["n_elem"]),
        "frac_exact_eq_base": acc["n_eq_base"] / acc["n_elem"] if acc["n_elem"] else None,
        "frac_exact_eq_util": acc["n_eq_util"] / acc["n_elem"] if acc["n_elem"] else None,
        "frac_exact_eq_safe": acc["n_eq_safe"] / acc["n_elem"] if acc["n_elem"] else None,
        "rel_diff_vs_base_pct": (100.0 * ndm / nb) if nb > 0 else None,
        "rel_diff_vs_util_pct": (100.0 * dmu / nu) if nu > 0 else None,
        "rel_diff_vs_safe_pct": (100.0 * dms / ns) if ns > 0 else None,
        "util_delta_rel_vs_base_pct": (100.0 * ndu / nb) if nb > 0 else None,
        "safe_delta_rel_vs_base_pct": (100.0 * nds / nb) if nb > 0 else None,
        "cos_dm_du": (acc["dot_dm_du"] / (ndm * ndu)) if (ndm > 0 and ndu > 0) else None,
        "cos_dm_ds": (acc["dot_dm_ds"] / (ndm * nds)) if (ndm > 0 and nds > 0) else None,
        "proj_util_pct": (100.0 * acc["dot_dm_du"] / acc["norm_du2"]) if acc["norm_du2"] > 0 else None,
        "proj_safe_pct": (100.0 * acc["dot_dm_ds"] / acc["norm_ds2"]) if acc["norm_ds2"] > 0 else None,
    }


def audit_one_model(
    *,
    label: str,
    merged_dir: Path,
    base_w: LazyWeights,
    util_w: LazyWeights,
    safe_w: LazyWeights,
    rel_diff_thresh_pct: float = 1.0,
    proj_util_thresh_pct: float = 10.0,
) -> dict[str, Any]:
    merged_w = LazyWeights(merged_dir)
    common_keys = [
        k for k in base_w.keys()
        if not k.endswith("rotary_emb.inv_freq")
        and k in set(merged_w.keys())
        and k in set(util_w.keys())
        and k in set(safe_w.keys())
    ]
    # .bin シャードのリロードを抑えるため util のファイル順でソート
    common_keys.sort(key=lambda k: (util_w.file_for(k), base_w.file_for(k), k))

    total_acc = _new_acc()
    layer_accs: dict[str, dict[str, float]] = defaultdict(_new_acc)
    n_updated = 0
    n_untouched = 0
    untouched_examples: list[str] = []
    updated_examples: list[dict[str, Any]] = []
    vocab_mismatch_keys: list[str] = []

    for k in common_keys:
        tb = base_w.get_fp32(k)
        tm = merged_w.get_fp32(k)
        tu = util_w.get_fp32(k)
        ts = safe_w.get_fp32(k)
        assert tb is not None and tm is not None and tu is not None and ts is not None

        if not (tb.shape == tm.shape == tu.shape == ts.shape):
            vocab_mismatch_keys.append(f"{k}: base={list(tb.shape)}, merged={list(tm.shape)}, util={list(tu.shape)}, safe={list(ts.shape)}")
            n0 = min(tb.shape[0], tm.shape[0], tu.shape[0], ts.shape[0])
            tb, tm, tu, ts = tb[:n0], tm[:n0], tu[:n0], ts[:n0]

        dm = tm - tb
        du = tu - tb
        ds = ts - tb

        max_abs = float(dm.abs().max().item())
        if max_abs > 1e-6:
            n_updated += 1
            if len(updated_examples) < 8:
                eq_b = float((dm.abs() <= 1e-7).float().mean().item())
                updated_examples.append({"tensor": k, "max_abs_diff_vs_base": max_abs, "frac_eq_base": eq_b})
        else:
            n_untouched += 1
            if len(untouched_examples) < 12:
                untouched_examples.append(k)

        stats_vals = {
            "n_elem": int(tb.numel()),
            "n_eq_base": int((dm.abs() <= 1e-7).sum().item()),
            "n_eq_util": int(((tm - tu).abs() <= 1e-7).sum().item()),
            "n_eq_safe": int(((tm - ts).abs() <= 1e-7).sum().item()),
            "norm_b2": float(torch.dot(tb.reshape(-1), tb.reshape(-1)).item()),
            "norm_u2": float(torch.dot(tu.reshape(-1), tu.reshape(-1)).item()),
            "norm_s2": float(torch.dot(ts.reshape(-1), ts.reshape(-1)).item()),
            "norm_dm2": float(torch.dot(dm.reshape(-1), dm.reshape(-1)).item()),
            "norm_du2": float(torch.dot(du.reshape(-1), du.reshape(-1)).item()),
            "norm_ds2": float(torch.dot(ds.reshape(-1), ds.reshape(-1)).item()),
            "diff_mu2": float(torch.dot((tm - tu).reshape(-1), (tm - tu).reshape(-1)).item()),
            "diff_ms2": float(torch.dot((tm - ts).reshape(-1), (tm - ts).reshape(-1)).item()),
            "dot_dm_du": float(torch.dot(dm.reshape(-1), du.reshape(-1)).item()),
            "dot_dm_ds": float(torch.dot(dm.reshape(-1), ds.reshape(-1)).item()),
        }
        lg = _layer_group(k)
        for sk, sv in stats_vals.items():
            total_acc[sk] += sv
            layer_accs[lg][sk] += sv

    merged_w.close()

    overall = _finalize_acc(total_acc)
    per_layer = {lg: _finalize_acc(acc) for lg, acc in sorted(layer_accs.items())}

    reasons: list[str] = []
    if overall["rel_diff_vs_base_pct"] is not None and overall["rel_diff_vs_base_pct"] < rel_diff_thresh_pct:
        reasons.append(f"rel_diff_vs_base ({overall['rel_diff_vs_base_pct']:.4f}%) < {rel_diff_thresh_pct}%")
    if overall["rel_diff_vs_util_pct"] is not None and overall["rel_diff_vs_util_pct"] < rel_diff_thresh_pct:
        reasons.append(f"rel_diff_vs_util ({overall['rel_diff_vs_util_pct']:.4f}%) < {rel_diff_thresh_pct}%")
    if overall["rel_diff_vs_safe_pct"] is not None and overall["rel_diff_vs_safe_pct"] < rel_diff_thresh_pct:
        reasons.append(f"rel_diff_vs_safe ({overall['rel_diff_vs_safe_pct']:.4f}%) < {rel_diff_thresh_pct}%")
    if overall["proj_util_pct"] is not None and overall["proj_util_pct"] < proj_util_thresh_pct:
        reasons.append(f"proj_util ({overall['proj_util_pct']:.4f}%) < {proj_util_thresh_pct}%")

    return {
        "label": label,
        "merged_dir": str(merged_dir),
        "n_tensors_compared": len(common_keys),
        "n_tensors_updated": n_updated,
        "n_tensors_untouched": n_untouched,
        "untouched_examples": untouched_examples,
        "updated_examples": updated_examples,
        "vocab_mismatch_keys": vocab_mismatch_keys,
        "overall": overall,
        "per_layer": per_layer,
        "degenerated": bool(reasons),
        "degeneration_reasons": reasons,
    }


def _fmt(v: float | None, digits: int = 3) -> str:
    return f"{v:.{digits}f}" if v is not None else "---"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, default=None, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    ap.add_argument("--patterns", nargs="+", default=["safety+math", "safety+code"])
    ap.add_argument("--rel-diff-thresh", type=float, default=1.0)
    ap.add_argument("--proj-util-thresh", type=float, default=10.0)
    args = ap.parse_args()

    if args.run_dir is not None:
        if not (args.run_dir / "RUN.md").is_file():
            raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")
        out_dir = args.run_dir / "outputs"
        summary_json_path = args.run_dir / "summary.json"
    else:
        out_dir = V5_ROOT / "outputs" / "sok_audit"
        summary_json_path = None

    base_dir = resolve_hf_snapshot_dir("meta-llama/Llama-2-7b-hf")
    util_dirs = {
        "safety+math": resolve_hf_snapshot_dir("WizardLMTeam/WizardMath-7B-V1.0"),
        "safety+code": resolve_hf_snapshot_dir("vanillaOVO/WizardCoder-Python-7B-V1.0"),
    }

    base_w = LazyWeights(base_dir)
    results = []
    for pat in args.patterns:
        util_w = LazyWeights(util_dirs[pat])
        for s in args.seeds:
            merged_dir = V3_ROOT / "models" / "merged" / f"sst_merge_v3_main_led_merging_{pat}_seed{s}"
            safe_dir = V3_ROOT / "models" / f"temp_safety_full_seed{s}"
            if not merged_dir.is_dir() or not safe_dir.is_dir():
                print(f"[SKIP] missing: {merged_dir} or {safe_dir}")
                continue
            print(f"[AUDIT] LED-Merging {pat} seed={s} ...")
            safe_w = LazyWeights(safe_dir)
            rec = audit_one_model(
                label=f"led_merging_{pat}_seed{s}",
                merged_dir=merged_dir,
                base_w=base_w,
                util_w=util_w,
                safe_w=safe_w,
                rel_diff_thresh_pct=args.rel_diff_thresh,
                proj_util_thresh_pct=args.proj_util_thresh,
            )
            results.append(rec)
            safe_w.close()
        util_w.close()
    base_w.close()

    md = [
        "# LED-Merging 重み退化・実効更新率監査（指示書 v2 §2.5 #2 / §4.2）",
        "",
        f"- **計算精度**: 単精度 (`float32`)、全共通テンソルをストリーミング集計（語彙数 32,000 vs 32,001 のテンソルは先頭 32,000 行で比較）。",
        f"- **退化判定しきい値**: いずれかの入力・ベースとの相対 L2 差 `< {args.rel_diff_thresh:.1f}%` または 分野更新残存率（射影係数）`< {args.proj_util_thresh:.1f}%`。",
        "",
        "## 1. モデル別サマリ",
        "",
        "| モデル | 更新テンソル数 | 未更新テンソル数 | ベース一致要素率 (%) | vs Base 相対差 (%) | vs Util 相対差 (%) | vs Safety 相対差 (%) | cos(Δm, Δu) | cos(Δm, Δs) | **分野更新残存率 proj_u (%)** | 安全更新射影 proj_s (%) | 退化判定 |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in results:
        o = r["overall"]
        verdict = "**退化**" if r["degenerated"] else "正常"
        eq_b = o["frac_exact_eq_base"] * 100.0 if o["frac_exact_eq_base"] is not None else None
        md.append(
            f"| `{r['label']}` | {r['n_tensors_updated']}/{r['n_tensors_compared']} | {r['n_tensors_untouched']} "
            f"| {_fmt(eq_b, 2)} | {_fmt(o['rel_diff_vs_base_pct'], 4)} | {_fmt(o['rel_diff_vs_util_pct'], 4)} | {_fmt(o['rel_diff_vs_safe_pct'], 4)} "
            f"| {_fmt(o['cos_dm_du'], 4)} | {_fmt(o['cos_dm_ds'], 4)} | **{_fmt(o['proj_util_pct'], 2)}** | {_fmt(o['proj_safe_pct'], 2)} | {verdict} |"
        )

    md += [
        "",
        "## 2. 退化理由・未更新テンソル例",
        "",
    ]
    for r in results:
        md.append(f"### `{r['label']}`")
        md.append(f"- 退化判定: `{'DEGENERATED' if r['degenerated'] else 'OK'}` ({'; '.join(r['degeneration_reasons']) or 'なし'})")
        md.append(f"- 未更新テンソル例 ({r['n_tensors_untouched']} 個中): `{', '.join(r['untouched_examples'][:6]) or 'なし'}`")
        if r["updated_examples"]:
            ex_s = ", ".join(f"{e['tensor']} (max|Δ|={e['max_abs_diff_vs_base']:.3e}, eq_base={e['frac_eq_base']*100:.1f}%)" for e in r["updated_examples"][:4])
            md.append(f"- 更新テンソル例 ({r['n_tensors_updated']} 個中): {ex_s}")
        md.append("")

    # seed42 safety+math の層別サマリ（代表）
    rep = next((r for r in results if r["label"] == "led_merging_safety+math_seed42"), None)
    if rep is not None:
        md += [
            "## 3. 層別プロファイル（代表: `led_merging_safety+math_seed42`）",
            "",
            "| 層グループ | ベース一致要素率 (%) | vs Base 相対差 (%) | cos(Δm, Δu) | cos(Δm, Δs) | 分野更新残存率 proj_u (%) | 安全更新射影 proj_s (%) |",
            "|:---|---:|---:|---:|---:|---:|---:|",
        ]
        for lg, lo in rep["per_layer"].items():
            eq_b = lo["frac_exact_eq_base"] * 100.0 if lo["frac_exact_eq_base"] is not None else None
            md.append(
                f"| `{lg}` | {_fmt(eq_b, 2)} | {_fmt(lo['rel_diff_vs_base_pct'], 4)} "
                f"| {_fmt(lo['cos_dm_du'], 4)} | {_fmt(lo['cos_dm_ds'], 4)} "
                f"| {_fmt(lo['proj_util_pct'], 2)} | {_fmt(lo['proj_safe_pct'], 2)} |"
            )

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "rel_diff_thresh_pct": args.rel_diff_thresh,
        "proj_util_thresh_pct": args.proj_util_thresh,
        "results": results,
    }
    write_json(out_dir / "led_merging_weight_audit.json", payload)
    write_text(out_dir / "led_merging_weight_audit.md", "\n".join(md) + "\n")
    if summary_json_path is not None:
        write_json(summary_json_path, payload)
    print(f"保存完了: {out_dir / 'led_merging_weight_audit.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
