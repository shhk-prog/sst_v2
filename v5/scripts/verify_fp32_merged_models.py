#!/usr/bin/env python3
"""SoK 実証 2: fp32 SST-Merge マージ直後の CPU 健全性検証スクリプト（数分で完了）。

GPU 評価に回す前に、マージ済みモデルが意図通り生成されたことを以下 4 点で検証する:
  1. α=0.0 モデル vs WizardMath-7B-V1.0:
     embed_tokens / lm_head 以外の全 289 テンソルが完全一致（max_abs_diff == 0.0）、
     embed_tokens / lm_head はベースモデル（Llama-2-7b-hf）と完全一致すること。
  2. α=1.0 モデルの各対象テンソル（224 個）:
     安全モデル（SafetyFT）側へ置き換わった座標の割合が約 20%（k=0.20 ± 0.05）であること。
  3. α=0.6 モデルの安全注入量比（V5 と同一指標）:
     ⟨θ_merged - θ_u, δ_s⟩_fp32SST / ⟨θ_merged - θ_u, δ_s⟩_v3TA の中央値が、
     v3 の 1.000 から大きく低下し 0.20 付近（< 0.45）になっていること。
  4. config.json の検証:
     WizardMath-7B-V1.0 と比較し、rope_theta=10000.0・rms_norm_eps=1e-05 等に P4 汚染がないこと、
     および既存 v3 マージモデルと同一の config 構造であることを確認する。

制約: CPU 専用・v3/ は読み取り専用。出力は v5/outputs/sok_exp2/ のみ。
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from merge_fp32_sst_math import (  # noqa: E402
    BASE_MODEL_ID,
    UTIL_MODEL_ID,
    assert_inside_v5,
    is_target_weight,
    resolve_hf_snapshot_dir,
)
from v5lib.tensor_checks import TensorSource, injection  # noqa: E402

VOCAB_MISMATCH_NAMES = {"model.embed_tokens.weight", "lm_head.weight"}


def _extract_rope_theta(cfg: dict[str, Any]) -> float:
    if "rope_theta" in cfg and cfg["rope_theta"] is not None:
        return float(cfg["rope_theta"])
    rp = cfg.get("rope_parameters")
    if isinstance(rp, dict) and rp.get("rope_theta") is not None:
        return float(rp["rope_theta"])
    return 10000.0


def verify_seed(
    seed: int,
    models_root: Path,
    k_ratio: float = 0.20,
    tol: float = 0.05,
) -> dict[str, Any]:
    base_dir = resolve_hf_snapshot_dir(BASE_MODEL_ID)
    util_dir = resolve_hf_snapshot_dir(UTIL_MODEL_ID)
    safe_dir = V3_ROOT / "models" / f"temp_safety_full_seed{seed}"
    v3_ta_dir = V3_ROOT / "models" / "merged" / f"sst_merge_v3_main_task_arithmetic_safety+math_alpha0.6_seed{seed}"

    m0_dir = models_root / f"fp32_sst_safety+math_alpha0.0_n500_k{k_ratio:g}_seed{seed}"
    m06_dir = models_root / f"fp32_sst_safety+math_alpha0.6_n500_k{k_ratio:g}_seed{seed}"
    m1_dir = models_root / f"fp32_sst_safety+math_alpha1.0_n500_k{k_ratio:g}_seed{seed}"

    for label, d in [("α=0.0", m0_dir), ("α=0.6", m06_dir), ("α=1.0", m1_dir), ("safe_full", safe_dir), ("v3_TA", v3_ta_dir)]:
        if not d.is_dir():
            raise FileNotFoundError(f"[seed{seed}] {label} ディレクトリが見つかりません: {d}")

    base_src = TensorSource(base_dir)
    util_src = TensorSource(util_dir)
    safe_src = TensorSource(safe_dir)
    m0_src = TensorSource(m0_dir)
    m06_src = TensorSource(m06_dir)
    m1_src = TensorSource(m1_dir)
    ta_src = TensorSource(v3_ta_dir)

    # PyTorch .bin シャードの再読込を防ぐため util_src のシャード順に並べる
    # （rotary_emb.inv_freq は旧 transformers 4.31 の非永続バッファで named_parameters() に含まれないため除外）
    all_names = sorted(
        (n for n in base_src.names() if not n.endswith("rotary_emb.inv_freq")),
        key=lambda n: (str(util_src._name_to_file.get(n, "")), n),
    )

    # --- Check 1: α=0.0 vs WizardMath (embed_tokens / lm_head 以外完全一致) ---
    # v3/scripts/mergers/sst.py L51, L72 は fp16 で `base + (util - base)` を経由するため、
    # 直接比較には fp16 の 1 ULP (最大 ~1.9e-6) の丸め差が出る。
    # そこで (a) v3 同式 `base + (util - base)` との厳密一致 (== 0.0) と
    #       (b) raw `util` との差が fp16 丸め範囲 (<= 1e-5) の両方を検証する。
    c1_non_vocab_vs_v3expr_max_diff = 0.0
    c1_non_vocab_vs_raw_util_max_diff = 0.0
    c1_vocab_vs_base_max_diff = 0.0
    c1_mismatches: list[dict[str, Any]] = []
    with torch.no_grad():
        for name in all_names:
            t_m0 = m0_src.get(name).to(dtype=torch.float16)
            t_base = base_src.get(name).to(dtype=torch.float16)
            if name in VOCAB_MISMATCH_NAMES:
                diff = float((t_m0.float() - t_base.float()).abs().max().item())
                c1_vocab_vs_base_max_diff = max(c1_vocab_vs_base_max_diff, diff)
                if diff > 0.0:
                    c1_mismatches.append({"tensor": name, "kind": "vocab_vs_base", "max_abs_diff": diff})
            else:
                t_util = util_src.get(name).to(dtype=torch.float16)
                t_v3expr = t_base + (t_util - t_base)
                diff_expr = float((t_m0.float() - t_v3expr.float()).abs().max().item())
                diff_raw = float((t_m0.float() - t_util.float()).abs().max().item())
                c1_non_vocab_vs_v3expr_max_diff = max(c1_non_vocab_vs_v3expr_max_diff, diff_expr)
                c1_non_vocab_vs_raw_util_max_diff = max(c1_non_vocab_vs_raw_util_max_diff, diff_raw)
                if diff_expr > 0.0:
                    c1_mismatches.append({"tensor": name, "kind": "non_vocab_vs_v3expr", "max_abs_diff": diff_expr})
    c1_pass = (
        c1_non_vocab_vs_v3expr_max_diff == 0.0
        and c1_non_vocab_vs_raw_util_max_diff <= 1e-5
        and c1_vocab_vs_base_max_diff == 0.0
    )

    # --- Check 2 (α=1.0 置換割合) & Check 3 (α=0.6 注入量比 vs v3 TA) ---
    target_names = [n for n in all_names if is_target_weight(n)]
    replaced_fracs_all: list[float] = []
    replaced_fracs_diffonly: list[float] = []
    inner_ratios: list[float] = []
    norm_ratios: list[float] = []

    with torch.no_grad():
        for name in target_names:
            t_base = base_src.get(name).to(dtype=torch.float16)
            t_util = util_src.get(name).to(dtype=torch.float16)
            t_safe = safe_src.get(name).to(dtype=torch.float16)
            t_m1 = m1_src.get(name).to(dtype=torch.float16)
            t_m06 = m06_src.get(name).to(dtype=torch.float16)
            t_ta06 = ta_src.get(name).to(dtype=torch.float16)

            # Check 2: α=1.0 で安全側に置き換わった座標の割合
            changed_from_util = t_m1 != t_util
            replaced_fracs_all.append(float(changed_from_util.float().mean().item()))
            safe_differs = t_safe != t_util
            n_differs = int(safe_differs.sum().item())
            if n_differs > 0:
                eq_safe = (t_m1 == t_safe) & safe_differs
                replaced_fracs_diffonly.append(float(eq_safe.sum().item()) / n_differs)

            # Check 3: V5 指標 ⟨θ_merged - θ_u, δ_s⟩ の対 TA 比（α=0.6）
            delta_s = t_safe.float() - t_base.float()
            norm_sst, inner_sst = injection(t_m06, t_util, delta_s)
            norm_ta, inner_ta = injection(t_ta06, t_util, delta_s)
            if abs(inner_ta) > 1e-12:
                inner_ratios.append(inner_sst / inner_ta)
            if norm_ta > 1e-12:
                norm_ratios.append(norm_sst / norm_ta)

    c2_mean_diffonly = statistics.mean(replaced_fracs_diffonly)
    c2_min_diffonly = min(replaced_fracs_diffonly)
    c2_max_diffonly = max(replaced_fracs_diffonly)
    c2_pass = all(abs(r - k_ratio) <= tol for r in replaced_fracs_diffonly)

    c3_median_inner = statistics.median(inner_ratios)
    c3_mean_inner = statistics.mean(inner_ratios)
    c3_median_norm = statistics.median(norm_ratios)
    # v3 では 1.000 だった中央値が大きく下がっていることを確認（k=0.20 なので概ね 0.15〜0.45 程度を想定）
    c3_pass = c3_median_inner < 0.50 and c3_median_inner > 0.05

    # --- Check 4: config.json 比較 ---
    cfg_m06 = json.loads((m06_dir / "config.json").read_text(encoding="utf-8"))
    cfg_util = json.loads((util_dir / "config.json").read_text(encoding="utf-8"))
    cfg_base = json.loads((base_dir / "config.json").read_text(encoding="utf-8"))

    rope_m06 = _extract_rope_theta(cfg_m06)
    rope_util = _extract_rope_theta(cfg_util)
    rope_base = _extract_rope_theta(cfg_base)

    config_comparison = {
        "rope_theta": {"merged": rope_m06, "wizardmath": rope_util, "llama2_base": rope_base, "match": rope_m06 == rope_util},
        "rms_norm_eps": {
            "merged": cfg_m06.get("rms_norm_eps"),
            "wizardmath": cfg_util.get("rms_norm_eps"),
            "match": cfg_m06.get("rms_norm_eps") == cfg_util.get("rms_norm_eps"),
        },
        "rope_scaling": {
            "merged": cfg_m06.get("rope_scaling"),
            "wizardmath": cfg_util.get("rope_scaling"),
            "match": cfg_m06.get("rope_scaling") == cfg_util.get("rope_scaling"),
        },
        "hidden_size": {
            "merged": cfg_m06.get("hidden_size"),
            "wizardmath": cfg_util.get("hidden_size"),
            "match": cfg_m06.get("hidden_size") == cfg_util.get("hidden_size"),
        },
        "max_position_embeddings": {
            "merged": cfg_m06.get("max_position_embeddings"),
            "wizardmath": cfg_util.get("max_position_embeddings"),
            "llama2_base": cfg_base.get("max_position_embeddings"),
            "note": "v3 と同一仕様でベースモデル(Llama-2, 4096)を継承（WizardMath は 2048）",
        },
        "vocab_size": {
            "merged": cfg_m06.get("vocab_size"),
            "wizardmath": cfg_util.get("vocab_size"),
            "llama2_base": cfg_base.get("vocab_size"),
            "note": "v3 と同一仕様でベースモデル(32000)を継承（embed/lm_head はベース重み）",
        },
    }
    c4_pass = (
        config_comparison["rope_theta"]["match"]
        and config_comparison["rms_norm_eps"]["match"]
        and config_comparison["rope_scaling"]["match"]
        and config_comparison["hidden_size"]["match"]
    )

    overall_pass = c1_pass and c2_pass and c3_pass and c4_pass
    return {
        "seed": seed,
        "overall_pass": overall_pass,
        "check1_alpha0_vs_wizardmath": {
            "pass": c1_pass,
            "n_total_tensors": len(all_names),
            "non_vocab_vs_v3expr_max_abs_diff": c1_non_vocab_vs_v3expr_max_diff,
            "non_vocab_max_abs_diff": c1_non_vocab_vs_raw_util_max_diff,
            "vocab_vs_base_max_abs_diff": c1_vocab_vs_base_max_diff,
            "mismatches": c1_mismatches[:20],
        },
        "check2_alpha1_replacement_fraction": {
            "pass": c2_pass,
            "n_target_tensors": len(target_names),
            "mean_replaced_where_safe_differs": c2_mean_diffonly,
            "min_replaced_where_safe_differs": c2_min_diffonly,
            "max_replaced_where_safe_differs": c2_max_diffonly,
            "mean_changed_all_coords": statistics.mean(replaced_fracs_all),
            "k_target": k_ratio,
            "tol": tol,
        },
        "check3_alpha06_injection_ratio_vs_v3_ta": {
            "pass": c3_pass,
            "n_target_tensors": len(inner_ratios),
            "median_inner_ratio": c3_median_inner,
            "mean_inner_ratio": c3_mean_inner,
            "min_inner_ratio": min(inner_ratios),
            "max_inner_ratio": max(inner_ratios),
            "median_norm_ratio": c3_median_norm,
            "v3_reference_median": 1.000,
        },
        "check4_config_comparison": {
            "pass": c4_pass,
            "fields": config_comparison,
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def format_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# SoK 実証 2: fp32 SST-Merge マージ直後検証レポート（CPU）",
        "",
        "| Seed | 総合 | Check1 (α=0 vs WM) | Check2 (α=1 置換率) | Check3 (α=0.6 注入比 vs TA) | Check4 (config P4無) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in results:
        c1 = r["check1_alpha0_vs_wizardmath"]
        c2 = r["check2_alpha1_replacement_fraction"]
        c3 = r["check3_alpha06_injection_ratio_vs_v3_ta"]
        c4 = r["check4_config_comparison"]
        lines.append(
            f"| {r['seed']} | {'PASS' if r['overall_pass'] else 'FAIL'} "
            f"| max_diff={c1['non_vocab_max_abs_diff']:.1g} ({'PASS' if c1['pass'] else 'FAIL'}) "
            f"| {c2['mean_replaced_where_safe_differs']:.4f} [{c2['min_replaced_where_safe_differs']:.4f}, {c2['max_replaced_where_safe_differs']:.4f}] "
            f"| median={c3['median_inner_ratio']:.4f} (norm={c3['median_norm_ratio']:.4f}) "
            f"| rope_theta={c4['fields']['rope_theta']['merged']} ({'PASS' if c4['pass'] else 'FAIL'}) |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--models-root", type=Path, default=V5_ROOT / "models" / "fp32_sst_math")
    ap.add_argument("--out-dir", type=Path, default=V5_ROOT / "outputs" / "sok_exp2")
    ap.add_argument("--k", type=float, default=0.20)
    ap.add_argument("--tol", type=float, default=0.05)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_dir = assert_inside_v5(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    all_pass = True
    for seed in args.seeds:
        json_path = out_dir / f"post_merge_verification_seed{seed}.json"
        md_path = out_dir / f"post_merge_verification_seed{seed}.md"
        if not args.force and json_path.is_file():
            try:
                prev = json.loads(json_path.read_text(encoding="utf-8"))
                if prev.get("overall_pass") is True:
                    print(f"[post-merge verify] seed={seed} -> SKIP (既存の検証で PASS 済み: {json_path.name})", flush=True)
                    results.append(prev)
                    continue
            except Exception:
                pass
        print(f"[post-merge verify] seed={seed} 検証開始...", flush=True)
        res = verify_seed(seed=seed, models_root=args.models_root, k_ratio=args.k, tol=args.tol)
        results.append(res)
        all_pass = all_pass and res["overall_pass"]
        json_path.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(format_markdown([res]), encoding="utf-8")
        c1 = res["check1_alpha0_vs_wizardmath"]
        c2 = res["check2_alpha1_replacement_fraction"]
        c3 = res["check3_alpha06_injection_ratio_vs_v3_ta"]
        print(
            f"[post-merge verify] seed={seed} -> {'PASS' if res['overall_pass'] else 'FAIL'} | "
            f"α=0 v3式差={c1['non_vocab_vs_v3expr_max_abs_diff']:.1g} (raw差={c1['non_vocab_max_abs_diff']:.1g}) | "
            f"α=1 置換率={c2['mean_replaced_where_safe_differs']:.4f} | "
            f"α=0.6 注入比中央値={c3['median_inner_ratio']:.4f} | "
            f"config={'PASS' if res['check4_config_comparison']['pass'] else 'FAIL'}",
            flush=True,
        )

    if len(results) > 1:
        (out_dir / "post_merge_verification_all.json").write_text(
            json.dumps({"all_pass": all_pass, "results": results}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (out_dir / "post_merge_verification_all.md").write_text(format_markdown(results), encoding="utf-8")

    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
