#!/usr/bin/env python3
"""SoK P5 対照監査: Data-Free SST の fp16 マスク退化測定と 3 手法（SST / Data-Free SST / Matena-Fisher）比較（CPU 専用）。

目的:
  1. v3/scripts/mergers/sst.py L150-181 の `data_free_sst`（fp16 での phi = delta^2 と `>= threshold` マスク）が、
     diagonal_sst と同様に fp16 桁落ちによる全 1 マスク退化を起こすかを CPU 上で全 224 対象テンソルについて実測する。
  2. 同じ重み差分を fp32 + インデックス top-k で計算した場合と対比する。
  3. v3/scripts/merging/matena_fisher.py（fp32 演算・グローバル L2 正規化・連続重み付け）および
     v3/scripts/mergers/sst.py の diagonal_sst / fisher_weighted / data_free_sst の 4 実装を並べ、
     「なぜ Matena-Fisher だけ P5 を免れたか」を対照表（v5/outputs/sok_audit/p5_method_contrast.md）にまとめる。

制約: CPU 専用・v3/ は読み取り専用。出力は v5/outputs/sok_audit/ のみ。
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

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from merge_fp32_sst_math import (  # noqa: E402
    BASE_MODEL_ID,
    assert_inside_v5,
    is_target_weight,
    resolve_hf_snapshot_dir,
)
from v5lib.tensor_checks import TensorSource  # noqa: E402

DOMAIN_MODEL_IDS = {
    "math": "WizardLMTeam/WizardMath-7B-V1.0",
    "code": "vanillaOVO/WizardCoder-Python-7B-V1.0",
    "medical": "medalpaca/medalpaca-7b",
}


def measure_datafree_for_pair(
    domain: str,
    seed: int,
    k_ratio: float = 0.20,
    eps: float = 1e-6,
) -> dict[str, Any]:
    base_dir = resolve_hf_snapshot_dir(BASE_MODEL_ID)
    util_dir = resolve_hf_snapshot_dir(DOMAIN_MODEL_IDS[domain])
    safe_dir = V3_ROOT / "models" / f"temp_safety_full_seed{seed}"

    base_src = TensorSource(base_dir)
    util_src = TensorSource(util_dir)
    safe_src = TensorSource(safe_dir)
    # PyTorch .bin シャードの再読込スラッシングを防ぐため util_src のシャード順に並べる
    target_names = sorted(
        (n for n in base_src.names() if is_target_weight(n)),
        key=lambda n: (str(util_src._name_to_file.get(n, "")), n),
    )

    fp16_mask_ratios: list[float] = []
    fp32_mask_ratios: list[float] = []
    delta_safe_zero_fp16: list[float] = []
    phi_h_zero_fp16: list[float] = []
    phi_b_zero_fp16: list[float] = []
    phi_h_zero_fp32: list[float] = []
    phi_b_zero_fp32: list[float] = []
    total_inf_fp16 = 0
    total_nan_fp16 = 0
    all1_fp16 = 0
    abnormal_fp16 = 0
    layer_all1_24_31 = 0
    layer_total_24_31 = 0

    with torch.no_grad():
        for name in target_names:
            base_t = base_src.get(name).to(dtype=torch.float16)
            util_t = util_src.get(name).to(dtype=torch.float16)
            safe_t = safe_src.get(name).to(dtype=torch.float16)

            delta_safe = safe_t - base_t
            delta_util = util_t - base_t

            # --- v3 data_free_sst (sst.py L150-181): fp16 ---
            phi_b_16 = delta_util ** 2
            phi_h_16 = delta_safe ** 2
            lam_16 = phi_h_16 / (phi_b_16 + eps)

            delta_safe_zero_fp16.append(float((delta_safe == 0).float().mean().item()))
            phi_h_zero_fp16.append(float((phi_h_16 == 0).float().mean().item()))
            phi_b_zero_fp16.append(float((phi_b_16 == 0).float().mean().item()))
            total_inf_fp16 += int(torch.isinf(lam_16).sum().item())
            total_nan_fp16 += int(torch.isnan(lam_16).sum().item())

            flat_16 = lam_16.reshape(-1)
            k_elements = max(1, int(flat_16.numel() * k_ratio))
            arr_16 = flat_16.numpy()
            idx = len(arr_16) - k_elements
            thr_16 = float(np.partition(arr_16, idx)[idx])
            ratio_16 = float((lam_16 >= thr_16).float().mean().item())
            fp16_mask_ratios.append(ratio_16)
            if ratio_16 > 0.99:
                all1_fp16 += 1
            if ratio_16 > k_ratio + 0.05:
                abnormal_fp16 += 1

            # 層番号抽出（L24-31 の集中度）
            parts = name.split(".")
            for p in parts:
                if p.isdigit() and int(p) >= 24:
                    layer_total_24_31 += 1
                    if ratio_16 > 0.99:
                        layer_all1_24_31 += 1
                    break

            # --- 対照: fp32 での phi = delta^2 + 厳密 index top-k ---
            phi_b_32 = delta_util.float() ** 2
            phi_h_32 = delta_safe.float() ** 2
            phi_h_zero_fp32.append(float((phi_h_32 == 0).float().mean().item()))
            phi_b_zero_fp32.append(float((phi_b_32 == 0).float().mean().item()))
            # exact index top-k では常に k_elements / numel になる
            fp32_mask_ratios.append(k_elements / flat_16.numel())

    return {
        "pattern": f"safety+{domain}",
        "seed": seed,
        "n_target_tensors": len(target_names),
        "k_target": k_ratio,
        "eps": eps,
        "delta_safe_zero_mean_fp16": statistics.mean(delta_safe_zero_fp16),
        "phi_h_zero_mean_fp16": statistics.mean(phi_h_zero_fp16),
        "phi_h_zero_mean_fp32": statistics.mean(phi_h_zero_fp32),
        "phi_b_zero_mean_fp16": statistics.mean(phi_b_zero_fp16),
        "phi_b_zero_mean_fp32": statistics.mean(phi_b_zero_fp32),
        "fp16_mask_ratio_mean": statistics.mean(fp16_mask_ratios),
        "fp16_mask_ratio_median": statistics.median(fp16_mask_ratios),
        "fp16_mask_ratio_min": min(fp16_mask_ratios),
        "fp16_mask_ratio_max": max(fp16_mask_ratios),
        "fp16_all1_tensors": all1_fp16,
        "fp16_all1_frac": all1_fp16 / len(target_names),
        "fp16_abnormal_tensors_gt_025": abnormal_fp16,
        "fp16_abnormal_frac": abnormal_fp16 / len(target_names),
        "fp16_L24_31_all1_tensors": layer_all1_24_31,
        "fp16_L24_31_total": layer_total_24_31,
        "fp16_L24_31_all1_frac": (layer_all1_24_31 / layer_total_24_31) if layer_total_24_31 else 0.0,
        "fp16_total_inf": total_inf_fp16,
        "fp16_total_nan": total_nan_fp16,
        "fp32_exact_topk_mean_mask_ratio": statistics.mean(fp32_mask_ratios),
    }


def write_contrast_markdown(df_results: list[dict[str, Any]], out_md: Path) -> None:
    math_r = [r for r in df_results if r["pattern"] == "safety+math"]
    math_phi_h_16 = statistics.mean(r["phi_h_zero_mean_fp16"] for r in math_r) * 100.0
    math_phi_h_32 = statistics.mean(r["phi_h_zero_mean_fp32"] for r in math_r) * 100.0
    math_mask_mean = statistics.mean(r["fp16_mask_ratio_mean"] for r in math_r)
    math_all1_pct = statistics.mean(r["fp16_all1_frac"] for r in math_r) * 100.0
    math_abn_pct = statistics.mean(r["fp16_abnormal_frac"] for r in math_r) * 100.0

    lines = [
        "# SoK P5 対照監査: v3 内での精度設計の違い（SST vs Data-Free SST vs Matena-Fisher）",
        "",
        "## 1. Data-Free SST（`v3/scripts/mergers/sst.py` L150–181）の CPU 実測結果",
        "",
        "`data_free_sst` は FIM を使わず重み差分の二乗 `phi_h = delta_safe ** 2`, `phi_b = delta_util ** 2` を",
        "**`torch.float16` のまま**計算し、`lambda_val = phi_h / (phi_b + 1e-6)` に `>= threshold` のハードマスクを適用している。",
        "fp16 の最小非正規数は $2^{-24} \\approx 5.96 \\times 10^{-8}$ のため、$|\\delta_s| < 2^{-12} \\approx 2.44 \\times 10^{-4}$ の座標は",
        "二乗した瞬間に 0 へ桁落ちする。",
        "",
        "| Pattern | Seed | `delta_safe==0` (fp16) | `phi_h==0` (fp16) | `phi_h==0` (fp32) | `phi_b==0` (fp16) | 実効マスク平均 (k=0.20) | 中央値 | 全1テンソル (>0.99) | 異常テンソル (>0.25) | L24–31 全1 | `inf` 件数 |",
        "|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in df_results:
        lines.append(
            f"| {r['pattern']} | {r['seed']} "
            f"| {r['delta_safe_zero_mean_fp16']*100:.2f}% "
            f"| {r['phi_h_zero_mean_fp16']*100:.2f}% "
            f"| {r['phi_h_zero_mean_fp32']*100:.2f}% "
            f"| {r['phi_b_zero_mean_fp16']*100:.2f}% "
            f"| {r['fp16_mask_ratio_mean']:.4f} "
            f"| {r['fp16_mask_ratio_median']:.4f} "
            f"| {r['fp16_all1_tensors']}/{r['n_target_tensors']} ({r['fp16_all1_frac']*100:.1f}%) "
            f"| {r['fp16_abnormal_tensors_gt_025']}/{r['n_target_tensors']} ({r['fp16_abnormal_frac']*100:.1f}%) "
            f"| {r['fp16_L24_31_all1_tensors']}/{r['fp16_L24_31_total']} ({r['fp16_L24_31_all1_frac']*100:.1f}%) "
            f"| {r['fp16_total_inf']} |"
        )

    lines += [
        "",
        "## 2. 同一リポジトリ（v3）内における 4 実装の P5 対照表",
        "",
        "| 実装（v3 内コード箇所） | 重要度/FIM の計算 dtype | 正規化・下限処理 | 選択/重み付け方式 | P5 退化の発生 | 根拠（実測・コード） |",
        "|:---|:---|:---|:---|:---|:---|",
        "| `diagonal_sst` (`v3/scripts/mergers/sst.py` L118–148, L177–181; `fim.py` L161) | **fp16**（`get_fim_tensor` で `like_tensor.dtype` にキャスト） | なし（`eps=1e-6` 加算のみ、正規化オフ） | ハードマスク `lambda_val >= threshold` | **発生（重度）** | `F_h` の fp16 ゼロ率 79.2%（fp32 では 0.0025%）。60.4% のテンソルが全 1 マスク（L24–31 は 89.3%）、`inf=17,813`、実効マスク平均 0.7043、注入量比中央値 1.000（TA と同等）。 |",
        f"| `data_free_sst` (`v3/scripts/mergers/sst.py` L150–181) | **fp16**（`delta_safe ** 2`, `delta_util ** 2` を fp16 のまま二乗） | なし（`eps=1e-6` 加算のみ） | ハードマスク `lambda_val >= threshold` | **{'発生' if math_all1_pct > 5.0 or math_abn_pct > 5.0 else '限定的/軽微'}** | `safety+math`（3 seed 平均）で `phi_h==0` が fp32 の {math_phi_h_32:.2f}% → fp16 で {math_phi_h_16:.2f}% へ増加。実効マスク平均 {math_mask_mean:.4f}、全 1 テンソル {math_all1_pct:.1f}%、異常 (>0.25) {math_abn_pct:.1f}%。 |",
        "| `fisher_weighted` (`v3/scripts/mergers/sst.py` L74–101; `fim.py` L161) | **fp16**（`get_fim_tensor` で fp16 キャスト） | なし（`denom = f_b + f_h + 1e-6` in fp16） | 連続重み `w_u = f_b/denom, w_s = f_h/denom` | **発生（別形態: ゼロ重み化）** | `f_b`・`f_h` とも fp16 で 0 落ちした座標では `w_u = w_s = 0` となり、出力重み自体が 0 に崩壊するリスクがある（`matena_fisher` と異なり floor も fp32 変換もない）。 |",
        "| `matena_fisher` (`v3/scripts/merging/matena_fisher.py` L48–54, L140–171) | **fp32**（`numerator/denominator` を `float32` 初期化、`theta_i.float()`, `f_i_raw.float()`） | グローバル L2 正規化（fp32）＋ `clamp(min=1e-6)` | 連続加重平均（`>= threshold` マスクなし） | **発生しない（安全）** | `get_fim_tensor` を経由せず `fim_dict.get(param_name).float()` を fp32 で直接計算し、最終保存直前（L171）のみ `base_tensor.dtype` へ戻すため、P5 の桁落ち・全 1 退化は構造的に起きない。 |",
        "",
        "## 3. SoK 論文への示唆",
        "",
        "- **同一コードベース内での対照証拠**: 同じ `v3/cache/fim/*.pt`（fp32）を入力にしていても、`matena_fisher.py`（fp32 演算＋L2 正規化＋floor）は P5 を完全に回避している一方、`sst.py` の `diagonal_sst` / `data_free_sst` は fp16 演算と `>= threshold` の組み合わせにより静かにマスクが退化する。",
        "- **対策の一般性（設計指針）**: FIM や二乗勾配・二乗差分のような微小正値を扱う重要度ベースのマージでは、(a) 重要度比の計算を必ず fp32 以上で行うこと、(b) ハードマスクは閾値比較 `>=` ではなくインデックス `topk().indices` で厳密に $k$ 個選ぶこと、(c) マージ直後に実効マスク比率と対 TA 注入量比を自動検証すること、の 3 点を標準チェックリストとして組み込むべきである。",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=V5_ROOT / "outputs" / "sok_audit")
    ap.add_argument("--k", type=float, default=0.20)
    ap.add_argument("--eps", type=float, default=1e-6)
    args = ap.parse_args()

    out_dir = assert_inside_v5(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pairs = [("math", 42), ("math", 43), ("math", 44), ("code", 42), ("medical", 42)]
    results = []
    for domain, seed in pairs:
        print(f"[data_free_sst 監査] safety+{domain} seed={seed} 計測中...", flush=True)
        r = measure_datafree_for_pair(domain=domain, seed=seed, k_ratio=args.k, eps=args.eps)
        results.append(r)
        print(
            f"  phi_h==0: fp32={r['phi_h_zero_mean_fp32']*100:.2f}% -> fp16={r['phi_h_zero_mean_fp16']*100:.2f}% | "
            f"mask mean={r['fp16_mask_ratio_mean']:.4f}, all1={r['fp16_all1_tensors']}/224 ({r['fp16_all1_frac']*100:.1f}%), "
            f"abn(>0.25)={r['fp16_abnormal_tensors_gt_025']}/224, inf={r['fp16_total_inf']}",
            flush=True,
        )

    json_path = out_dir / "datafree_degeneration.json"
    json_path.write_text(
        json.dumps(
            {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "results": results},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path = out_dir / "p5_method_contrast.md"
    write_contrast_markdown(results, md_path)
    print(f"保存完了: {json_path}, {md_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
