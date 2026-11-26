#!/usr/bin/env python3
"""SoK 5.7 節 H3 監査: SafeMERGE の更新層数・コサイン類似度・実効重み差分を CPU で実測する。

目的:
  草稿 5.7 節 H3 の【結果待ち：組み合わせごとの更新層数】を解決するため、
  v3/models/merged/sst_merge_v3_main_safemerge_safety+{math,code,medical}_seed{42,43,44} の
  1. safemerge_layer_weights.json（全 224 行列の cosine・ft_weight・safe_weight・merged・reason）
  2. 実際のマージ済み重みとベースモデル（Llama-2-7b-hf）・専門モデル（WizardMath/WizardCoder/MedAlpaca）との
     相対差分（seed 42、全 32 層＋非対象 norm 層）
  を計測し、「SafeMERGE で異系統でも文字化け 0% だった理由が選択の効きなのか、
  それとも SVD 擬似 LoRA 化により専門モデルの異系統差分がほぼ捨てられた（ベースに留まった）ためか」を確定する。

制約: CPU 専用・v3/ は読み取り専用。出力は v5/outputs/sok_audit/ のみ。
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter
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

from merge_fp32_sst_math import BASE_MODEL_ID, assert_inside_v5, is_target_weight, resolve_hf_snapshot_dir  # noqa: E402
from v5lib.tensor_checks import TensorSource, relative_difference  # noqa: E402

DOMAIN_MODELS = {
    "math": "WizardLMTeam/WizardMath-7B-V1.0",
    "code": "vanillaOVO/WizardCoder-Python-7B-V1.0",
    "medical": "medalpaca/medalpaca-7b",
}


def inspect_layer_weights_json(path: Path) -> dict[str, Any]:
    d = json.loads(path.read_text(encoding="utf-8"))
    layers = d.get("layers", [])
    merged_rows = [x for x in layers if x.get("merged")]
    unmerged_rows = [x for x in layers if not x.get("merged")]
    cosines = [float(x.get("cosine", 0.0)) for x in layers]
    reasons = Counter(str(x.get("reason")) for x in layers)
    ft_w = Counter(float(x.get("ft_weight", 0.0)) for x in layers)
    sf_w = Counter(float(x.get("safe_weight", 0.0)) for x in layers)

    # 32 層単位での集計
    merged_layer_ids = set()
    all_layer_ids = set()
    for x in layers:
        parts = str(x.get("layer", "")).split(".")
        for p in parts:
            if p.isdigit():
                lid = int(p)
                all_layer_ids.add(lid)
                if x.get("merged"):
                    merged_layer_ids.add(lid)
                break

    return {
        "threshold": d.get("threshold"),
        "default_merge_ratio": d.get("default_merge_ratio"),
        "n_projections": len(layers),
        "n_merged_projections": len(merged_rows),
        "n_unmerged_projections": len(unmerged_rows),
        "n_total_transformer_layers": len(all_layer_ids),
        "n_merged_transformer_layers": len(merged_layer_ids),
        "cosine_zero_count": sum(1 for c in cosines if abs(c) < 1e-12),
        "cosine_nonzero_count": sum(1 for c in cosines if abs(c) >= 1e-12),
        "cosine_min": min(cosines) if cosines else None,
        "cosine_max": max(cosines) if cosines else None,
        "cosine_mean": statistics.mean(cosines) if cosines else None,
        "reasons": dict(reasons),
        "ft_weight_counts": {str(k): v for k, v in ft_w.items()},
        "safe_weight_counts": {str(k): v for k, v in sf_w.items()},
    }


def inspect_weight_diffs_seed42(domain: str) -> dict[str, Any]:
    sm_dir = V3_ROOT / "models" / "merged" / f"sst_merge_v3_main_safemerge_safety+{domain}_seed42"
    base_dir = resolve_hf_snapshot_dir(BASE_MODEL_ID)
    util_dir = resolve_hf_snapshot_dir(DOMAIN_MODELS[domain])
    safe_dir = V3_ROOT / "models" / "temp_safety_full_seed42"

    base_src = TensorSource(base_dir)
    util_src = TensorSource(util_dir)
    safe_src = TensorSource(safe_dir)
    sm_src = TensorSource(sm_dir)

    all_names = sorted(
        (n for n in base_src.names() if not n.endswith("rotary_emb.inv_freq")),
        key=lambda n: (str(util_src._name_to_file.get(n, "")), n),
    )

    target_diff_vs_base: list[float] = []
    target_diff_vs_util: list[float] = []
    target_diff_vs_safe: list[float] = []
    util_diff_vs_base: list[float] = []
    norm_diff_vs_base: list[float] = []
    norm_diff_vs_util: list[float] = []
    changed_target_tensors = 0
    changed_norm_tensors = 0

    with torch.no_grad():
        for name in all_names:
            t_base = base_src.get(name).to(dtype=torch.float16)
            t_sm = sm_src.get(name).to(dtype=torch.float16)
            d_base = relative_difference(t_sm, t_base)
            has_util = util_src.has(name)
            t_util = util_src.get(name).to(dtype=torch.float16) if has_util else None
            shape_ok = t_util is not None and t_util.shape == t_base.shape

            if is_target_weight(name):
                target_diff_vs_base.append(d_base)
                if d_base > 1e-7:
                    changed_target_tensors += 1
                if shape_ok:
                    target_diff_vs_util.append(relative_difference(t_sm, t_util))
                    util_diff_vs_base.append(relative_difference(t_util, t_base))
                if safe_src.has(name):
                    t_safe = safe_src.get(name).to(dtype=torch.float16)
                    target_diff_vs_safe.append(relative_difference(t_sm, t_safe))
            elif "norm" in name.lower():
                norm_diff_vs_base.append(d_base)
                if d_base > 1e-7:
                    changed_norm_tensors += 1
                if shape_ok:
                    norm_diff_vs_util.append(relative_difference(t_sm, t_util))

    return {
        "pattern": f"safety+{domain}",
        "seed": 42,
        "changed_target_tensors": changed_target_tensors,
        "total_target_tensors": len(target_diff_vs_base),
        "changed_norm_tensors": changed_norm_tensors,
        "total_norm_tensors": len(norm_diff_vs_base),
        "median_rel_diff_safemerge_vs_base_target": statistics.median(target_diff_vs_base),
        "median_rel_diff_safemerge_vs_util_target": statistics.median(target_diff_vs_util),
        "median_rel_diff_safemerge_vs_safe_target": statistics.median(target_diff_vs_safe),
        "median_rel_diff_util_vs_base_target": statistics.median(util_diff_vs_base),
        "median_rel_diff_safemerge_vs_base_norm": statistics.median(norm_diff_vs_base),
        "median_rel_diff_safemerge_vs_util_norm": statistics.median(norm_diff_vs_util),
    }


def main() -> int:
    out_dir = assert_inside_v5(V5_ROOT / "outputs" / "sok_audit")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rows = []
    for domain in ("math", "code", "medical"):
        for seed in (42, 43, 44):
            p = V3_ROOT / "models" / "merged" / f"sst_merge_v3_main_safemerge_safety+{domain}_seed{seed}" / "safemerge_layer_weights.json"
            if p.is_file():
                info = inspect_layer_weights_json(p)
                json_rows.append({"pattern": f"safety+{domain}", "seed": seed, **info})

    weight_rows = []
    for domain in ("math", "code", "medical"):
        print(f"[SafeMERGE H3 監査] safety+{domain} seed42 重み差分計測中...", flush=True)
        w = inspect_weight_diffs_seed42(domain)
        weight_rows.append(w)
        print(
            f"  target changed={w['changed_target_tensors']}/{w['total_target_tensors']}, "
            f"norm changed={w['changed_norm_tensors']}/{w['total_norm_tensors']}, "
            f"vs_base={w['median_rel_diff_safemerge_vs_base_target']*100:.2f}%, "
            f"vs_util={w['median_rel_diff_safemerge_vs_util_target']*100:.2f}%, "
            f"util_vs_base={w['median_rel_diff_util_vs_base_target']*100:.2f}%",
            flush=True,
        )

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "layer_weights_json_summary": json_rows,
        "weight_diff_seed42": weight_rows,
    }
    (out_dir / "safemerge_h3_audit.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    md = [
        "# SoK 5.7 節 H3 監査: SafeMERGE の更新層数と実効重み差分",
        "",
        "## 1. `safemerge_layer_weights.json` の集計（全 3 組み合わせ × 3 seed）",
        "",
        "| Pattern | Seed | 対象行列数 | `merged=True` 行列数 | `merged=True` 層数 (/32) | `cosine==0` 行列数 | cosine 範囲 | `ft/safe` 重み |",
        "|:---|:---:|---:|---:|---:|---:|:---:|:---|",
    ]
    for r in json_rows:
        md.append(
            f"| {r['pattern']} | {r['seed']} | {r['n_projections']} | {r['n_merged_projections']} "
            f"| {r['n_merged_transformer_layers']}/{r['n_total_transformer_layers']} "
            f"| {r['cosine_zero_count']}/{r['n_projections']} "
            f"| [{r['cosine_min']:.4f}, {r['cosine_max']:.4f}] "
            f"| ft={r['ft_weight_counts']}, safe={r['safe_weight_counts']} |"
        )

    md += [
        "",
        "## 2. 保存済み SafeMERGE 重みの相対差分（seed 42、中央値）",
        "",
        "| Pattern | 変更対象行列 | 変更 norm 層 | ‖SafeMERGE−Base‖/‖Base‖ (target) | ‖SafeMERGE−Util‖/‖Util‖ (target) | ‖Util−Base‖/‖Base‖ (target) | ‖SafeMERGE−Base‖/‖Base‖ (norm) | ‖SafeMERGE−Util‖/‖Util‖ (norm) |",
        "|:---|:---:|:---:|---:|---:|---:|---:|---:|",
    ]
    for w in weight_rows:
        md.append(
            f"| {w['pattern']} | {w['changed_target_tensors']}/{w['total_target_tensors']} "
            f"| {w['changed_norm_tensors']}/{w['total_norm_tensors']} "
            f"| {w['median_rel_diff_safemerge_vs_base_target']*100:.2f}% "
            f"| {w['median_rel_diff_safemerge_vs_util_target']*100:.2f}% "
            f"| {w['median_rel_diff_util_vs_base_target']*100:.2f}% "
            f"| {w['median_rel_diff_safemerge_vs_base_norm']*100:.4f}% "
            f"| {w['median_rel_diff_safemerge_vs_util_norm']*100:.2f}% |"
        )

    (out_dir / "safemerge_h3_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"保存完了: {out_dir / 'safemerge_h3_audit.md'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
