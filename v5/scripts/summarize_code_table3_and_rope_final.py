#!/usr/bin/env python3
"""SoK 実環境トラック コード有用性（表 3）・P4 rope_theta 切り分け 確定集計スクリプト（CPU 専用）。

入力:
  - 確定 HumanEval (official_tab_nl, n=164, ロック済み eval_lock.yaml):
      v5/results/runs/20261126-1518_code-table3-and-rope-humaneval/outputs/ (全 33 本)
  - 単体参照 HumanEval:
      WizardCoder-Python-7B-V1.0: 20261126-1413_wizardcoder-humaneval-gate-v2 (official_tab_nl, 50.61%)
      Llama-2-7b-hf / SafetyFT_seed42: 20261126-1357_wizardcoder-humaneval-gate (2.44% / 0.00%, v1形式注記)
  - 安全性評価 (v3 4 ベンチ・公式 3 分類器・HarmBench 再分類済み):
      v3/results/vllm/debug_limit320/merged/seed{42,43,44}/safety+code/<method>/
      v3/results/vllm/debug_limit320/base/
      v5/results/rope_theta_ablation/

方針（指示書 v2 §1, §2.5, §3.4, §4.4 およびユーザー決定）:
  - 実環境トラックのコード有用性はロック済み HumanEval (official_tab_nl) のみに一本化し、
    未検証の MBPP は表 3 および rope_theta 比較表から除外する。
  - 結合 VRR は「従来規則 (is_gibberish) または拡張規則 (文字化け検出) のどちらか一方で崩壊なら無効」
    とし、VRR >= 90% を妥当性下限とする。
  - LED-Merging (v3) は 0/291 テンソル更新（Llama-2-7b-hf ベース 100% 一致）の退化モデルであることを明記する。
  - rope_theta の結論は「設定の取り違え (rope_theta) だけでは崩壊もコード能力喪失も説明できない」
    の範囲にとどめ（1 点確認、語彙数 32,001 と事前学習系統は未分離）、部分的効果も併記する。

制約: CPU 専用・v3/ は読み取り専用。
"""

from __future__ import annotations

import argparse
import math
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from probe_native_classifier import BENCHES  # noqa: E402
from summarize_rope_theta_ablation import eval_safety_dir  # noqa: E402
from v5lib.safeio import read_json, write_json, write_text  # noqa: E402

CODE_HE_DIR = V5_ROOT / "results" / "runs" / "20261126-1518_code-table3-and-rope-humaneval" / "outputs"
WC_GATE_V2_DIR = V5_ROOT / "results" / "runs" / "20261126-1413_wizardcoder-humaneval-gate-v2" / "outputs"
WC_GATE_V1_DIR = V5_ROOT / "results" / "runs" / "20261126-1357_wizardcoder-humaneval-gate" / "outputs"
V3_MERGED_ROOT = V3_ROOT / "results" / "vllm" / "debug_limit320" / "merged"
V3_BASE_ROOT = V3_ROOT / "results" / "vllm" / "debug_limit320" / "base"
V5_ROPE_DIR = V5_ROOT / "results" / "rope_theta_ablation"

SEEDS = (42, 43, 44)
VRR_MIN = 90.0

# (key, label, v3_subdir, v3_safety_prefix_tpl, he_file_tpl, note)
TABLE3_METHODS: list[tuple[str, str, str, str, str, str]] = [
    (
        "task_arithmetic",
        "Task Arithmetic (α=0.6)",
        "task_arithmetic",
        "sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed{seed}",
        "v3_task_arithmetic_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "",
    ),
    (
        "ties",
        "TIES (α=0.6)",
        "ties",
        "sst_merge_v3_main_ties_safety+code_alpha0.6_seed{seed}",
        "v3_ties_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "",
    ),
    (
        "dare",
        "DARE (α=0.6)",
        "dare",
        "sst_merge_v3_main_dare_safety+code_alpha0.6_seed{seed}",
        "v3_dare_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "",
    ),
    (
        "della",
        "DELLA (α=0.6)",
        "della",
        "sst_merge_v3_main_della_safety+code_alpha0.6_seed{seed}",
        "v3_della_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "",
    ),
    (
        "matena_fisher",
        "Fisher Merging",
        "matena_fisher",
        "sst_merge_v3_main_matena_fisher_safety+code_seed{seed}",
        "v3_matena_fisher_seed{seed}_humaneval_official_tab_nl.json",
        "",
    ),
    (
        "diagonal_sst",
        "fp16 SST (v3, α=0.6)",
        "diagonal_sst_main",
        "sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed{seed}",
        "v3_diagonal_sst_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "P5 fp16 桁落ち",
    ),
    (
        "data_free_sst",
        "Data-Free SST (α=0.6)",
        "data_free_sst_main",
        "sst_merge_v3_main_data_free_sst_main_safety+code_alpha0.6_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed{seed}",
        "v3_data_free_sst_alpha0.6_seed{seed}_humaneval_official_tab_nl.json",
        "P5 fp16 桁落ち",
    ),
    (
        "led_merging",
        "LED-Merging† (v3)",
        "led_merging",
        "sst_merge_v3_main_led_merging_safety+code_seed{seed}",
        "v3_led_merging_seed{seed}_humaneval_official_tab_nl.json",
        "退化: 0/291 更新（Llama-2 ベース一致）",
    ),
    (
        "safemerge",
        "SafeMERGE",
        "safemerge",
        "sst_merge_v3_main_safemerge_safety+code_seed{seed}",
        "v3_safemerge_seed{seed}_humaneval_official_tab_nl.json",
        "seed 間で崩壊不安定",
    ),
    (
        "mergealign",
        "MergeAlign",
        "mergealign",
        "sst_merge_v3_main_mergealign_safety+code_seed{seed}",
        "v3_mergealign_seed{seed}_humaneval_official_tab_nl.json",
        "従来規則で全崩壊（繰り返し）",
    ),
]

ROPE_METHODS: list[tuple[str, str, str, str, str, str, str]] = [
    (
        "task_arithmetic",
        "Task Arithmetic",
        "task_arithmetic",
        "sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed42",
        "rope1e6_safety+code_task_arithmetic_alpha0.6_seed42",
        "v3_task_arithmetic_alpha0.6_seed42_humaneval_official_tab_nl.json",
        "rope1e6_task_arithmetic_alpha0.6_seed42_humaneval_official_tab_nl.json",
    ),
    (
        "dare",
        "DARE",
        "dare",
        "sst_merge_v3_main_dare_safety+code_alpha0.6_seed42",
        "rope1e6_safety+code_dare_alpha0.6_seed42",
        "v3_dare_alpha0.6_seed42_humaneval_official_tab_nl.json",
        "rope1e6_dare_alpha0.6_seed42_humaneval_official_tab_nl.json",
    ),
    (
        "diagonal_sst",
        "fp16 SST (v3)",
        "diagonal_sst_main",
        "sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42",
        "rope1e6_safety+code_diagonal_sst_alpha0.6_seed42",
        "v3_diagonal_sst_alpha0.6_seed42_humaneval_official_tab_nl.json",
        "rope1e6_diagonal_sst_alpha0.6_seed42_humaneval_official_tab_nl.json",
    ),
]


def load_humaneval_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"HumanEval 結果が見つかりません: {path}")
    d = read_json(path)
    if not d.get("completed", False):
        raise ValueError(f"未完了の HumanEval 結果です: {path}")
    return {
        "file": str(path),
        "model_name": d.get("model_name"),
        "prompt_template": d.get("prompt_template"),
        "n_pass": int(d["n_pass"]),
        "n_total": int(d["n_total"]),
        "humaneval_pass1_pct": float(d["humaneval_pass1_pct"]),
        "extraction_fail_pct": float(d["extraction_fail_pct"]),
        "extraction_mode_skew_pct": float(d.get("extraction_mode_skew_pct", 0.0)),
    }


def mean_std(values: list[float | None]) -> tuple[float | None, float | None, int]:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean:
        return None, None, 0
    if len(clean) == 1:
        return clean[0], 0.0, 1
    return statistics.mean(clean), statistics.stdev(clean), len(clean)


def fmt_num(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "---"


def fmt_pm(mean_v: float | None, std_v: float | None) -> str:
    if mean_v is None:
        return "---"
    if std_v is None:
        return f"{mean_v:.2f}"
    return f"{mean_v:.2f} ± {std_v:.2f}"


def aggregate_seed_records(per_seed: list[dict[str, Any]]) -> dict[str, Any]:
    metric_keys_he = ("humaneval_pass1_pct", "extraction_fail_pct")
    metric_keys_s = (
        "rule_vrr",
        "ext_only_vrr",
        "ext_vrr",
        "salad_in_rule_valid_pct",
        "cond_hb_ext",
        "cond_wg_ext",
        "cond_sr_ext",
        "vsr_hb_ext",
        "cond_hb_rule",
        "cond_wg_rule",
        "cond_sr_rule",
    )
    agg: dict[str, Any] = {"n_seeds": len(per_seed)}
    for k in metric_keys_he:
        m, s, n = mean_std([r["humaneval"][k] for r in per_seed])
        agg[k] = {"mean": m, "std": s, "n": n}
    for k in metric_keys_s:
        m, s, n = mean_std([r["safety"][k] for r in per_seed])
        agg[k] = {"mean": m, "std": s, "n": n}
    agg["passes_vrr_gate"] = bool(agg["ext_vrr"]["mean"] is not None and agg["ext_vrr"]["mean"] >= VRR_MIN)
    return agg


def build_all_summaries() -> dict[str, Any]:
    # 1. 単体参照 3 本
    wc_he = load_humaneval_json(WC_GATE_V2_DIR / "WizardCoder-Python-7B-V1.0_humaneval_official_tab_nl.json")
    wc_s = eval_safety_dir(V3_BASE_ROOT, "sst_merge_v3_main_base_WizardCoder")

    sft_seeds_s = [eval_safety_dir(V3_BASE_ROOT, f"sst_merge_v3_main_base_SafetyFT_seed{s}") for s in SEEDS]
    sft_he_s42 = load_humaneval_json(WC_GATE_V1_DIR / "SafetyFT_seed42_humaneval_official.json")
    sft_agg = aggregate_seed_records([{"humaneval": sft_he_s42, "safety": s} for s in sft_seeds_s])

    base_he = load_humaneval_json(WC_GATE_V1_DIR / "Llama-2-7b-hf_humaneval_official.json")

    singles = {
        "wizardcoder": {
            "label": "WizardCoder-Python-7B-V1.0（単体）",
            "humaneval": wc_he,
            "safety": wc_s,
            "note": "公式 55.5% (T=0.2) に対し貪欲法 50.61% (-4.89pp、検証ゲート通過・ロック済み)",
        },
        "safetyft": {
            "label": "SafetyFT（単体、安全性 3 seed / HE seed42）",
            "humaneval": sft_he_s42,
            "safety_agg": sft_agg,
            "note": "安全性全 3 seed VRR=100%, 全 3 分類器 Cond.ASR=0.00%; HE は v1 gate (seed42)",
        },
        "llama2_base": {
            "label": "Llama-2-7b-hf（ベース単体）",
            "humaneval": base_he,
            "safety": None,
            "note": "HE は v1 gate; 安全性は未マージ LED-Merging† (0/291 更新) と同一実体",
        },
    }

    # 2. 表 3: safety+code 全 10 手法 × 3 seed
    table3_rows: list[dict[str, Any]] = []
    for key, label, subdir, s_tpl, he_tpl, note in TABLE3_METHODS:
        per_seed = []
        for s in SEEDS:
            s_dir = V3_MERGED_ROOT / f"seed{s}" / "safety+code" / subdir
            s_res = eval_safety_dir(s_dir, s_tpl.format(seed=s))
            he_res = load_humaneval_json(CODE_HE_DIR / he_tpl.format(seed=s))
            per_seed.append({"seed": s, "safety": s_res, "humaneval": he_res})
        agg = aggregate_seed_records(per_seed)
        table3_rows.append({
            "key": key,
            "label": label,
            "note": note,
            "per_seed": per_seed,
            "agg": agg,
        })

    # 3. rope_theta 確定比較表 (α=0.6, seed42, Before 10,000 vs After 1,000,000)
    rope_rows: list[dict[str, Any]] = []
    for key, label, subdir, v3_pref, v5_pref, he_before_f, he_after_f in ROPE_METHODS:
        v3_dir = V3_MERGED_ROOT / "seed42" / "safety+code" / subdir
        before_s = eval_safety_dir(v3_dir, v3_pref)
        after_s = eval_safety_dir(V5_ROPE_DIR, v5_pref)
        before_he = load_humaneval_json(CODE_HE_DIR / he_before_f)
        after_he = load_humaneval_json(CODE_HE_DIR / he_after_f)
        rope_rows.append({
            "key": key,
            "label": label,
            "before_rope1e4": {"safety": before_s, "humaneval": before_he},
            "after_rope1e6": {"safety": after_s, "humaneval": after_he},
        })

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "humaneval_eval_lock": {
            "prompt_variant": "official_tab_nl",
            "max_tokens": 2048,
            "n_samples": 164,
            "mbpp_included": False,
            "mbpp_policy": "実環境トラックでは未検証のため除外し、検証済み・ロック済み HumanEval に一本化",
        },
        "vrr_definition": "either_rule_or_extended_collapse_is_invalid",
        "vrr_min_pct": VRR_MIN,
        "singles": singles,
        "table3_safety_code": table3_rows,
        "rope_theta_ablation": rope_rows,
    }


def render_rope_theta_markdown(data: dict[str, Any]) -> str:
    rows = data["rope_theta_ablation"]
    by_key = {r["key"]: r for r in rows}
    ta_b, ta_a = by_key["task_arithmetic"]["before_rope1e4"], by_key["task_arithmetic"]["after_rope1e6"]
    da_b, da_a = by_key["dare"]["before_rope1e4"], by_key["dare"]["after_rope1e6"]
    st_b, st_a = by_key["diagonal_sst"]["before_rope1e4"], by_key["diagonal_sst"]["after_rope1e6"]

    md = [
        "# SoK P4 切り分け確定比較表: `safety+code` (`α=0.6, seed42`) における `rope_theta` 修正前後",
        "",
        "- **状態**: **確定版**（`20261126-1344_rope-theta-ablation-summary` を置き換え）",
        "- **目的**: `safety+code` の崩壊およびコード能力喪失に対して、`config.json` の `rope_theta` 取り違え（`10,000` vs WizardCoder 正規値 `1,000,000`）を修正するだけで改善するかを 1 点（`α=0.6, seed42`）で確かめる。",
        "- **介入内容**: 既存の `v3` マージ済み重みは 1 ビットも変更せず（シンボリックリンク参照）、`config.json` の `rope_theta` のみ `10,000.0 → 1,000,000.0` に修正して同一プロトコルで再評価した。",
        "- **コード有用性（確定）**: 検証ゲート通過・ロック済み設定（`official_tab_nl`, `max_tokens=2048`, 全 164 問、WizardCoder 単体 `50.61%` [83/164] vs 公式 `55.5%` [温度 0.2]、`20261126-1413_wizardcoder-humaneval-gate-v2` / `20261126-1518_code-table3-and-rope-humaneval`）の HumanEval pass@1 のみを掲載する。未検証の MBPP は実環境トラックの比較表から除外した。",
        "- **妥当性 (VRR) の定義**: 結合 VRR は「従来規則（`is_gibberish`）と拡張規則（文字化け検出）の**どちらか一方でも**崩壊と判定された応答を無効」として算出（下限 `90%`）。",
        "",
        "## 1. 総合比較表（Before: `rope_theta=10,000` vs After: `rope_theta=1,000,000`）",
        "",
        "| 手法 | 条件 (`rope_theta`) | 従来 VRR (%) | 拡張単独 VRR (%) | **結合 VRR (%)** | Valid 中文字化け率 (%) | Cond.ASR HB (結合, %) | Cond.ASR WG (結合, %) | Cond.ASR SR (結合, %) | VSR HB (結合, %) | **HumanEval pass@1 (%)** | HE 正解数 | HE 抽出失敗率 (%) |",
        "|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for cond_label, blk in [("Before (10,000)", r["before_rope1e4"]), ("**After (1,000,000)**", r["after_rope1e6"])]:
            s = blk["safety"]
            h = blk["humaneval"]
            md.append(
                f"| {r['label']} | {cond_label} "
                f"| {fmt_num(s['rule_vrr'])} | {fmt_num(s['ext_only_vrr'])} | **{fmt_num(s['ext_vrr'])}** "
                f"| {fmt_num(s['salad_in_rule_valid_pct'])} "
                f"| {fmt_num(s['cond_hb_ext'])} | {fmt_num(s['cond_wg_ext'])} | {fmt_num(s['cond_sr_ext'])} "
                f"| {fmt_num(s['vsr_hb_ext'])} | **{fmt_num(h['humaneval_pass1_pct'])}** "
                f"| {h['n_pass']}/{h['n_total']} | {fmt_num(h['extraction_fail_pct'])} |"
            )

    md += [
        "",
        "## 2. ベンチマーク別詳細（結合 VRR・文字化け率・3 分類器別 Cond.ASR）",
        "",
        "| 手法 | Bench | Before 文字化け率 (%) | After 文字化け率 (%) | Before 結合 VRR (%) | After 結合 VRR (%) | Before Cond.ASR HB (結合) | After Cond.ASR HB (結合) | Before Cond.ASR Native (結合) | After Cond.ASR Native (結合) |",
        "|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for b in BENCHES:
            sb = r["before_rope1e4"]["safety"]["per_bench"][b]
            sa = r["after_rope1e6"]["safety"]["per_bench"][b]
            md.append(
                f"| {r['label']} | {b} "
                f"| {fmt_num(sb['salad_in_rule_valid_pct'])} | {fmt_num(sa['salad_in_rule_valid_pct'])} "
                f"| {fmt_num(sb['ext_vrr'])} | {fmt_num(sa['ext_vrr'])} "
                f"| {fmt_num(sb['cond_hb_ext'])} | {fmt_num(sa['cond_hb_ext'])} "
                f"| {fmt_num(sb['cond_nat_ext'])} | {fmt_num(sa['cond_nat_ext'])} |"
            )

    md += [
        "",
        "## 3. 結果の解釈と結論（指示書 v2 §4.4・草稿 6.4 節確定文言）",
        "",
        f"- **`DARE`**: `rope_theta` を `1,000,000` に修正しても Valid 中文字化け率は **{fmt_num(da_b['safety']['salad_in_rule_valid_pct'])}% → {fmt_num(da_a['safety']['salad_in_rule_valid_pct'])}%**、結合 VRR は **{fmt_num(da_b['safety']['ext_vrr'])}% → {fmt_num(da_a['safety']['ext_vrr'])}%**、ロック済み HumanEval は **{fmt_num(da_b['humaneval']['humaneval_pass1_pct'])}% ({da_b['humaneval']['n_pass']}/164) → {fmt_num(da_a['humaneval']['humaneval_pass1_pct'])}% ({da_a['humaneval']['n_pass']}/164)** であり、崩壊もコード能力喪失も改善しなかった。",
        f"- **`fp16 SST (v3)`**: `rope_theta` 修正により Valid 中文字化け率は **{fmt_num(st_b['safety']['salad_in_rule_valid_pct'])}% → {fmt_num(st_a['safety']['salad_in_rule_valid_pct'])}%** へ低下し、結合 VRR は **{fmt_num(st_b['safety']['ext_vrr'])}% → {fmt_num(st_a['safety']['ext_vrr'])}%** へ約 2 倍に上昇した（部分的な効果あり）。しかし結合 VRR は依然として 15.89%（下限 90% を大きく下回る）にとどまり、ロック済み HumanEval も **{fmt_num(st_b['humaneval']['humaneval_pass1_pct'])}% → {fmt_num(st_a['humaneval']['humaneval_pass1_pct'])}%** のままで回復しなかった（抽出失敗率は {fmt_num(st_b['humaneval']['extraction_fail_pct'])}% → {fmt_num(st_a['humaneval']['extraction_fail_pct'])}% とやや改善）。",
        f"- **`Task Arithmetic`**: 結合 VRR が 90% 超の TA（{fmt_num(ta_b['safety']['ext_vrr'])}% → {fmt_num(ta_a['safety']['ext_vrr'])}%）では、`rope_theta=1,000,000` への修正により HarmBench 条件付き ASR が **{fmt_num(ta_b['safety']['cond_hb_ext'])}% → {fmt_num(ta_a['safety']['cond_hb_ext'])}%**、WildGuard が **{fmt_num(ta_b['safety']['cond_wg_ext'])}% → {fmt_num(ta_a['safety']['cond_wg_ext'])}%** へ低下し、ロック済み HumanEval も **{fmt_num(ta_b['humaneval']['humaneval_pass1_pct'])}% ({ta_b['humaneval']['n_pass']}/164) → {fmt_num(ta_a['humaneval']['humaneval_pass1_pct'])}% ({ta_a['humaneval']['n_pass']}/164)** へわずかに上昇した（StrongREJECT は {fmt_num(ta_b['safety']['cond_sr_ext'])}% → {fmt_num(ta_a['safety']['cond_sr_ext'])}%）。ただし WizardCoder 単体（50.61%）には遠く及ばない。",
        "- **結論（主張の範囲）**: `rope_theta` の取り違え修正は一部に効く（SST の結合 VRR `7.63% → 15.89%`、TA の HB 条件付き ASR `34.43% → 23.63%` および HumanEval `2.44% → 4.27%`）ものの、**それだけでは崩壊は止まらず、コード能力も回復しない（「設定の取り違え（`rope_theta`）だけでは崩壊を説明できない」）**ことが確定した。",
        "- **切り分けの限界**: WizardCoder-Python-7B-V1.0 は事前学習系統（CodeLlama）だけでなく語彙数（`32,001` vs Llama-2 の `32,000`）もベースと異なるため、残存する崩壊に対して事前学習系統と語彙数のどちらがどの程度効いているかまでは本実験では切り分けていない。また `α=0.6, seed42` の 1 点での確認である。",
    ]
    return "\n".join(md) + "\n"


def render_table3_markdown(data: dict[str, Any]) -> str:
    singles = data["singles"]
    rows = data["table3_safety_code"]

    md = [
        "# SoK 実環境トラック `safety+code` 確定集計表（表 3: 全 10 手法 × 3 seed + 単体参照）",
        "",
        "- **状態**: **確定版**（ロック済み `official_tab_nl` HumanEval 33 本完了後の最終集計）",
        "- **コード有用性設定**: `eval_lock.yaml` 固定済み `eval_code_wizardcoder_official.py --prompt-variant official_tab_nl --max-tokens 2048`（HumanEval 全 164 問、貪欲法）。未検証の MBPP は実環境トラック表 3 から除外した。",
        "- **妥当性 (VRR) の定義**: 結合 VRR は「従来規則（`is_gibberish`）と拡張規則（文字化け検出）の**どちらか一方でも**崩壊と判定された応答を無効」として算出。下限は `VRR ≥ 90%`。",
        "- **LED-Merging† に関する注記**: 公開コード（commit `1149224`）そのままの `v3` LED-Merging 3 モデルは、`20261126-1344_led-merging-weight-audit` により `0/291` テンソル更新（`Llama-2-7b-hf` ベースと 100.00% 一致）と確定しており、HumanEval も 3 seed すべて `2.44% (4/164)` でベース単体と完全一致した。",
        "",
        "## 1. 単体参照モデル（マージなし）",
        "",
        "| モデル | **HumanEval pass@1 (%)** | HE 抽出失敗率 (%) | 従来 VRR (%) | **結合 VRR (%)** | Valid 中文字化け率 (%) | Cond.ASR HB (結合, %) | Cond.ASR WG (結合, %) | Cond.ASR SR (結合, %) | 備考 |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]
    wc = singles["wizardcoder"]
    md.append(
        f"| {wc['label']} | **{fmt_num(wc['humaneval']['humaneval_pass1_pct'])}** ({wc['humaneval']['n_pass']}/164) "
        f"| {fmt_num(wc['humaneval']['extraction_fail_pct'])} "
        f"| {fmt_num(wc['safety']['rule_vrr'])} | **{fmt_num(wc['safety']['ext_vrr'])}** "
        f"| {fmt_num(wc['safety']['salad_in_rule_valid_pct'])} "
        f"| {fmt_num(wc['safety']['cond_hb_ext'])} | {fmt_num(wc['safety']['cond_wg_ext'])} | {fmt_num(wc['safety']['cond_sr_ext'])} "
        f"| {wc['note']} |"
    )
    sft = singles["safetyft"]
    sa = sft["safety_agg"]
    md.append(
        f"| {sft['label']} | **{fmt_num(sft['humaneval']['humaneval_pass1_pct'])}** ({sft['humaneval']['n_pass']}/164) "
        f"| {fmt_num(sft['humaneval']['extraction_fail_pct'])} "
        f"| {fmt_pm(sa['rule_vrr']['mean'], sa['rule_vrr']['std'])} | **{fmt_pm(sa['ext_vrr']['mean'], sa['ext_vrr']['std'])}** "
        f"| {fmt_pm(sa['salad_in_rule_valid_pct']['mean'], sa['salad_in_rule_valid_pct']['std'])} "
        f"| {fmt_pm(sa['cond_hb_ext']['mean'], sa['cond_hb_ext']['std'])} | {fmt_pm(sa['cond_wg_ext']['mean'], sa['cond_wg_ext']['std'])} | {fmt_pm(sa['cond_sr_ext']['mean'], sa['cond_sr_ext']['std'])} "
        f"| {sft['note']} |"
    )
    b = singles["llama2_base"]
    md.append(
        f"| {b['label']} | **{fmt_num(b['humaneval']['humaneval_pass1_pct'])}** ({b['humaneval']['n_pass']}/164) "
        f"| {fmt_num(b['humaneval']['extraction_fail_pct'])} | --- | --- | --- | --- | --- | --- | {b['note']} |"
    )

    md += [
        "",
        "## 2. 表 3 確定集計（`safety+code`, `α=0.6`, 3 seed 平均 ± 標準偏差）",
        "",
        "| 手法 | **HumanEval pass@1 (%)** | HE 抽出失敗率 (%) | 従来 VRR (%) | **結合 VRR (%)** | Valid 中文字化け率 (%) | VRR≥90% | Cond.ASR HB (結合, %) | Cond.ASR WG (結合, %) | Cond.ASR SR (結合, %) | VSR HB (結合, %) | 備考 |",
        "|:---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|---:|:---|",
    ]
    for r in rows:
        a = r["agg"]
        gate_str = "合格" if a["passes_vrr_gate"] else "失格"
        md.append(
            f"| {r['label']} "
            f"| **{fmt_pm(a['humaneval_pass1_pct']['mean'], a['humaneval_pass1_pct']['std'])}** "
            f"| {fmt_pm(a['extraction_fail_pct']['mean'], a['extraction_fail_pct']['std'])} "
            f"| {fmt_pm(a['rule_vrr']['mean'], a['rule_vrr']['std'])} "
            f"| **{fmt_pm(a['ext_vrr']['mean'], a['ext_vrr']['std'])}** "
            f"| {fmt_pm(a['salad_in_rule_valid_pct']['mean'], a['salad_in_rule_valid_pct']['std'])} "
            f"| {gate_str} "
            f"| {fmt_pm(a['cond_hb_ext']['mean'], a['cond_hb_ext']['std'])} "
            f"| {fmt_pm(a['cond_wg_ext']['mean'], a['cond_wg_ext']['std'])} "
            f"| {fmt_pm(a['cond_sr_ext']['mean'], a['cond_sr_ext']['std'])} "
            f"| {fmt_pm(a['vsr_hb_ext']['mean'], a['vsr_hb_ext']['std'])} "
            f"| {r['note']} |"
        )

    md += [
        "",
        "## 3. seed 別詳細（seed 42 / 43 / 44 全 30 本）",
        "",
        "| 手法 | Seed | HumanEval pass@1 (%) | HE 正解数 | HE 抽出失敗率 (%) | 従来 VRR (%) | 結合 VRR (%) | Valid 中文字化け率 (%) | Cond.ASR HB (結合) | Cond.ASR WG (結合) | Cond.ASR SR (結合) |",
        "|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for ps in r["per_seed"]:
            h = ps["humaneval"]
            s = ps["safety"]
            md.append(
                f"| {r['label']} | {ps['seed']} "
                f"| {fmt_num(h['humaneval_pass1_pct'])} | {h['n_pass']}/{h['n_total']} | {fmt_num(h['extraction_fail_pct'])} "
                f"| {fmt_num(s['rule_vrr'])} | {fmt_num(s['ext_vrr'])} | {fmt_num(s['salad_in_rule_valid_pct'])} "
                f"| {fmt_num(s['cond_hb_ext'])} | {fmt_num(s['cond_wg_ext'])} | {fmt_num(s['cond_sr_ext'])} |"
            )

    by_key = {r["key"]: r for r in rows}
    ta = by_key["task_arithmetic"]
    sm = by_key["safemerge"]
    led = by_key["led_merging"]
    wc_p1 = singles["wizardcoder"]["humaneval"]["humaneval_pass1_pct"]
    ta_he_m, ta_he_s = ta["agg"]["humaneval_pass1_pct"]["mean"], ta["agg"]["humaneval_pass1_pct"]["std"]
    ta_vrr_m, ta_vrr_s = ta["agg"]["ext_vrr"]["mean"], ta["agg"]["ext_vrr"]["std"]
    ta_hb_m, ta_hb_s = ta["agg"]["cond_hb_ext"]["mean"], ta["agg"]["cond_hb_ext"]["std"]
    sm_he_m, sm_he_s = sm["agg"]["humaneval_pass1_pct"]["mean"], sm["agg"]["humaneval_pass1_pct"]["std"]
    sm_vrr_m, sm_vrr_s = sm["agg"]["ext_vrr"]["mean"], sm["agg"]["ext_vrr"]["std"]
    sm_s42, sm_s43, sm_s44 = sm["per_seed"][0]["humaneval"], sm["per_seed"][1]["humaneval"], sm["per_seed"][2]["humaneval"]
    ta_s42, ta_s43, ta_s44 = ta["per_seed"][0]["humaneval"], ta["per_seed"][1]["humaneval"], ta["per_seed"][2]["humaneval"]
    led_he_m = led["agg"]["humaneval_pass1_pct"]["mean"]
    led_ef_m = led["agg"]["extraction_fail_pct"]["mean"]
    drop_ta = wc_p1 - ta_he_m

    md += [
        "",
        "## 4. 主な確定知見（草稿 6.4 節・表 3・6.8 節用）",
        "",
        f"- **全手法でコード能力がほぼ完全に喪失（単体 `{wc_p1:.2f}%` に対し最大でも `{sm_he_m:.2f}%` 平均）**: 検証・ロック済みの公式プロンプト（WizardCoder 単体 `{wc_p1:.2f}%`）で測り直しても、`safety+code` のマージ済みモデルでは 10 手法中 7 手法（TIES, DARE, DELLA, Fisher Merging, fp16 SST, Data-Free SST, MergeAlign）が 3 seed すべて **`0.00%` (0/164)** となった。",
        "- **かろうじて 0% を上回った 3 手法の実態**:",
        f"  1. **`Task Arithmetic (α=0.6)`**: 結合 VRR `{fmt_pm(ta_vrr_m, ta_vrr_s)}%`（VRR ≥ 90% 合格）だが、HumanEval は `{fmt_pm(ta_he_m, ta_he_s)}%`（seed42: `{ta_s42['humaneval_pass1_pct']:.2f}%`, seed43: `{ta_s43['humaneval_pass1_pct']:.2f}%`, seed44: `{ta_s44['humaneval_pass1_pct']:.2f}%`）にとどまり、WizardCoder 単体（`{wc_p1:.2f}%`）から `-{drop_ta:.1f} pp` 激落、かつ HB Cond.ASR `{fmt_pm(ta_hb_m, ta_hb_s)}%`（安全性も未回復）。",
        f"  2. **`SafeMERGE`**: 結合 VRR は `{fmt_pm(sm_vrr_m, sm_vrr_s)}%` だが、HumanEval は `{fmt_pm(sm_he_m, sm_he_s)}%` と seed 間で極端に不安定（seed42: `{sm_s42['humaneval_pass1_pct']:.2f}%` [ext_fail `{sm_s42['extraction_fail_pct']:.2f}%`], seed43: `{sm_s43['humaneval_pass1_pct']:.2f}%` [ext_fail `{sm_s43['extraction_fail_pct']:.2f}%`], seed44: `{sm_s44['humaneval_pass1_pct']:.2f}%` [ext_fail `{sm_s44['extraction_fail_pct']:.2f}%`]）。数学と同様に単体の能力をほぼ保てていない。",
        f"  3. **`LED-Merging† (v3)`**: 3 seed すべて `{led_he_m:.2f}%` (4/164, ext_fail=`{led_ef_m:.2f}%`) で `Llama-2-7b-hf` ベース単体と 100% 一致（重み `0/291` 更新の退化をコード有用性からも裏付け）。",
        f"- **P4 の確定裏付け**: 従来の未検証設定（WizardCoder 単体 `5.49%`）では「マージによるコード能力喪失」と「評価設定の不備（P6）」が分離できなかったが、単体 `{wc_p1:.2f}%` を通したロック済み設定でもほぼ全手法が `0.00%`〜`{sm_he_m:.2f}%` に崩壊したことで、**異系統マージ（Llama-2 × CodeLlama 系 WizardCoder）による能力喪失が評価器のせいではなく実在する現象**であることが確定した。",
    ]
    return "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    args = ap.parse_args()

    if not (args.run_dir / "RUN.md").is_file():
        raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")

    out_dir = args.run_dir / "outputs"
    data = build_all_summaries()

    rope_md = render_rope_theta_markdown(data)
    table3_md = render_table3_markdown(data)

    write_json(out_dir / "code_table3_and_rope_summary_final.json", data)
    write_text(out_dir / "rope_theta_ablation_summary_final.md", rope_md)
    write_text(out_dir / "code_table3_summary_final.md", table3_md)
    write_json(args.run_dir / "summary.json", {
        "timestamp_utc": data["timestamp_utc"],
        "humaneval_eval_lock": data["humaneval_eval_lock"],
        "vrr_definition": data["vrr_definition"],
        "vrr_min_pct": data["vrr_min_pct"],
        "table3_compact": [
            {
                "key": r["key"],
                "label": r["label"],
                "humaneval_mean_pct": r["agg"]["humaneval_pass1_pct"]["mean"],
                "humaneval_std_pct": r["agg"]["humaneval_pass1_pct"]["std"],
                "ext_vrr_mean_pct": r["agg"]["ext_vrr"]["mean"],
                "ext_vrr_std_pct": r["agg"]["ext_vrr"]["std"],
                "salad_in_valid_mean_pct": r["agg"]["salad_in_rule_valid_pct"]["mean"],
                "cond_hb_ext_mean_pct": r["agg"]["cond_hb_ext"]["mean"],
                "cond_wg_ext_mean_pct": r["agg"]["cond_wg_ext"]["mean"],
                "cond_sr_ext_mean_pct": r["agg"]["cond_sr_ext"]["mean"],
                "passes_vrr_gate": r["agg"]["passes_vrr_gate"],
            }
            for r in data["table3_safety_code"]
        ],
        "rope_theta_compact": [
            {
                "key": r["key"],
                "label": r["label"],
                "before_ext_vrr_pct": r["before_rope1e4"]["safety"]["ext_vrr"],
                "after_ext_vrr_pct": r["after_rope1e6"]["safety"]["ext_vrr"],
                "before_humaneval_pct": r["before_rope1e4"]["humaneval"]["humaneval_pass1_pct"],
                "after_humaneval_pct": r["after_rope1e6"]["humaneval"]["humaneval_pass1_pct"],
                "before_cond_hb_ext_pct": r["before_rope1e4"]["safety"]["cond_hb_ext"],
                "after_cond_hb_ext_pct": r["after_rope1e6"]["safety"]["cond_hb_ext"],
            }
            for r in data["rope_theta_ablation"]
        ],
    })
    print(f"確定集計完了:\n  - {out_dir / 'rope_theta_ablation_summary_final.md'}\n  - {out_dir / 'code_table3_summary_final.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
