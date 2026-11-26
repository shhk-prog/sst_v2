#!/usr/bin/env python3
"""SoK P4 因果切り分け集計: safety+code (α=0.6, seed42) の rope_theta=10,000 (v3) vs 1,000,000 (v5) 正式比較表（CPU 専用）。

指示書 v2 第 1 節・2.5 節・4.4 節準拠:
  - --run-dir 指定時は <run_dir>/outputs/ および <run_dir>/summary.json に出力する。
  - 結論は「設定の取り違え（rope_theta）だけでは崩壊を説明できない」の範囲にとどめ、
    部分的な効果（SST 拡張 VRR 7.63%→15.89%、TA HB Cond.ASR 34.43%→23.63%）も明記する。
  - WizardCoder のコード有用性検証（指示書 v2 2.5 節 #1）完了前のため、
    HumanEval / MBPP / Code Avg 列にはすべて「暫定」を付記する。

制約: CPU 専用・v3/ は読み取り専用。
"""

from __future__ import annotations

import argparse
import os
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

from probe_gibberish_escape import is_suspected_token_salad  # noqa: E402
from probe_native_classifier import BENCHES, harmful_harmbench_only, harmful_native  # noqa: E402
from v5lib.safeio import read_json, write_json, write_text  # noqa: E402

V3_BASE_DIR = V3_ROOT / "results" / "vllm" / "debug_limit320" / "merged" / "seed42" / "safety+code"
V5_ROPE_DIR = V5_ROOT / "results" / "rope_theta_ablation"

METHODS = [
    (
        "task_arithmetic",
        "Task Arithmetic",
        V3_BASE_DIR / "task_arithmetic",
        "sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed42",
        "rope1e6_safety+code_task_arithmetic_alpha0.6_seed42",
    ),
    (
        "dare",
        "DARE",
        V3_BASE_DIR / "dare",
        "sst_merge_v3_main_dare_safety+code_alpha0.6_seed42",
        "rope1e6_safety+code_dare_alpha0.6_seed42",
    ),
    (
        "diagonal_sst",
        "fp16 SST (v3)",
        V3_BASE_DIR / "diagonal_sst_main",
        "sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42",
        "rope1e6_safety+code_diagonal_sst_alpha0.6_seed42",
    ),
]


def _extract_pass1(res_dict: dict[str, Any], task: str) -> float | None:
    sub = (res_dict.get("results") or {}).get(task)
    if not isinstance(sub, dict):
        return None
    for k in ("pass@1", "pass@1,create_test", "pass_at_1,none", "pass@1,none"):
        if sub.get(k) is not None:
            v = float(sub[k])
            return v * 100.0 if v <= 1.0 else v
    return None


def load_code_utility(dir_path: Path, prefix: str) -> dict[str, float | None]:
    he = None
    mbpp = None
    for cand in (dir_path / f"{prefix}_utility_code_humaneval.json", dir_path / f"{prefix}_utility_code.json"):
        if cand.is_file():
            v = _extract_pass1(read_json(cand), "humaneval")
            if v is not None:
                he = v
                break
    for cand in (dir_path / f"{prefix}_utility_code_mbpp.json", dir_path / f"{prefix}_utility_code.json"):
        if cand.is_file():
            v = _extract_pass1(read_json(cand), "mbpp")
            if v is not None:
                mbpp = v
                break
    avg = (0.5 * (he + mbpp)) if (he is not None and mbpp is not None) else None
    return {"humaneval": he, "mbpp": mbpp, "code_avg": avg}


def eval_safety_dir(dir_path: Path, prefix: str) -> dict[str, Any]:
    """従来規則・拡張規則単独・結合規則（どちらか崩壊なら無効）をすべて集計する。"""
    per_bench: dict[str, dict[str, Any]] = {}
    for b in BENCHES:
        fpath = dir_path / f"{prefix}_{b}_safety.json"
        if not fpath.is_file():
            raise FileNotFoundError(f"安全性結果が見つかりません: {fpath}")
        rows = read_json(fpath).get("results", [])
        n = len(rows)
        valid_rule = [r for r in rows if isinstance(r, dict) and not bool(r.get("is_gibberish", False))]
        valid_ext_only = [r for r in rows if isinstance(r, dict) and not is_suspected_token_salad(str(r.get("response", "")))]
        salad_in_valid = [r for r in valid_rule if is_suspected_token_salad(str(r.get("response", "")))]
        # 結合妥当性（どちらか一方で崩壊と判定されたら無効）
        valid_both = [r for r in valid_rule if not is_suspected_token_salad(str(r.get("response", "")))]

        nv_r = len(valid_rule)
        nv_b = len(valid_both)
        hb_r = sum(1 for r in valid_rule if harmful_harmbench_only(r))
        nat_r = sum(1 for r in valid_rule if harmful_native(b, r))
        hb_b = sum(1 for r in valid_both if harmful_harmbench_only(r))
        nat_b = sum(1 for r in valid_both if harmful_native(b, r))

        per_bench[b] = {
            "n": n,
            "rule_vrr": 100.0 * nv_r / n if n else None,
            "ext_only_vrr": 100.0 * len(valid_ext_only) / n if n else None,
            "salad_in_rule_valid_pct": 100.0 * len(salad_in_valid) / nv_r if nv_r else None,
            "ext_vrr": 100.0 * nv_b / n if n else None,
            "collapse_either_pct": 100.0 * (n - nv_b) / n if n else None,
            "cond_hb_rule": 100.0 * hb_r / nv_r if nv_r else None,
            "cond_nat_rule": 100.0 * nat_r / nv_r if nv_r else None,
            "cond_hb_ext": 100.0 * hb_b / nv_b if nv_b else None,
            "cond_nat_ext": 100.0 * nat_b / nv_b if nv_b else None,
            "vsr_hb_rule": 100.0 * (nv_r - hb_r) / n if n else None,
            "vsr_hb_ext": 100.0 * (nv_b - hb_b) / n if n else None,
        }

    def _avg(benches: tuple[str, ...], key: str) -> float | None:
        vals = [per_bench[b][key] for b in benches if per_bench[b][key] is not None]
        return (sum(vals) / len(vals)) if vals else None

    return {
        "per_bench": per_bench,
        "rule_vrr": _avg(BENCHES, "rule_vrr"),
        "ext_only_vrr": _avg(BENCHES, "ext_only_vrr"),
        "salad_in_rule_valid_pct": _avg(BENCHES, "salad_in_rule_valid_pct"),
        "ext_vrr": _avg(BENCHES, "ext_vrr"),
        "collapse_either_pct": _avg(BENCHES, "collapse_either_pct"),
        "cond_hb_rule": _avg(BENCHES, "cond_hb_rule"),
        "cond_wg_rule": _avg(("jailbreakbench", "wildjailbreak"), "cond_nat_rule"),
        "cond_sr_rule": _avg(("strongreject",), "cond_nat_rule"),
        "cond_hb_ext": _avg(BENCHES, "cond_hb_ext"),
        "cond_wg_ext": _avg(("jailbreakbench", "wildjailbreak"), "cond_nat_ext"),
        "cond_sr_ext": _avg(("strongreject",), "cond_nat_ext"),
        "vsr_hb_rule": _avg(BENCHES, "vsr_hb_rule"),
        "vsr_hb_ext": _avg(BENCHES, "vsr_hb_ext"),
    }


def _fmt(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "---"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, default=None, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--out-dir", type=Path, default=None, help="直接出力先（--run-dir 未指定時のみ使用）")
    args = ap.parse_args()

    if args.run_dir is not None:
        if not (args.run_dir / "RUN.md").is_file():
            raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")
        out_dir = args.run_dir / "outputs"
        summary_json_path = args.run_dir / "summary.json"
    else:
        out_dir = args.out_dir or (V5_ROOT / "outputs" / "sok_audit")
        summary_json_path = None

    rows = []
    for key, label, v3_dir, v3_pref, v5_pref in METHODS:
        before_s = eval_safety_dir(v3_dir, v3_pref)
        before_c = load_code_utility(v3_dir, v3_pref)
        after_s = eval_safety_dir(V5_ROPE_DIR, v5_pref)
        after_c = load_code_utility(V5_ROPE_DIR, v5_pref)
        rows.append({
            "key": key,
            "label": label,
            "before_rope1e4": {"safety": before_s, "code": before_c},
            "after_rope1e6": {"safety": after_s, "code": after_c},
        })

    by_key = {r["key"]: r for r in rows}
    ta_b, ta_a = by_key["task_arithmetic"]["before_rope1e4"], by_key["task_arithmetic"]["after_rope1e6"]
    da_b, da_a = by_key["dare"]["before_rope1e4"], by_key["dare"]["after_rope1e6"]
    st_b, st_a = by_key["diagonal_sst"]["before_rope1e4"], by_key["diagonal_sst"]["after_rope1e6"]

    md = [
        "# SoK P4 切り分け正式比較表: `safety+code` (`α=0.6, seed42`) における `rope_theta` 修正前後",
        "",
        "- **目的**: `safety+code` の崩壊に対して、`config.json` の `rope_theta` 取り違え（`10,000` vs WizardCoder 正規値 `1,000,000`）を修正するだけで崩壊が止まるかを 1 点（`α=0.6, seed42`）で確かめる。",
        "- **介入内容**: 既存の `v3` マージ済み重みは 1 ビットも変更せず（シンボリックリンク参照）、`config.json` の `rope_theta` のみ `10,000.0 → 1,000,000.0` に修正して同一プロトコルで再評価した。",
        "- **妥当性 (VRR) の定義**: 結合 VRR は「従来規則（`is_gibberish`）と拡張規則（文字化け検出）の**どちらか一方でも**崩壊と判定された応答を無効」として算出（指示書 v2 §3.4 準拠）。従来規則単独・拡張規則単独の値も併記。",
        "- **コード有用性に関する注記（暫定）**: 表中の HumanEval・MBPP・Code Avg は、`v3` の評価設定（WizardCoder 単体が HumanEval `5.49%`・MBPP `36.56%`・平均 `21.03%` と、公式 HumanEval `55.5%` を大きく下回る設定）で測った**暫定値**である。指示書 v2 §2.5 #1（WizardCoder 単体の評価検証）が完了するまで、コード有用性の数値（「0.00%」を含む）は論文の結論に使用しない。",
        "",
        "## 1. 総合比較表（Before: `rope_theta=10,000` vs After: `rope_theta=1,000,000`）",
        "",
        "| 手法 | 条件 (`rope_theta`) | 従来 VRR (%) | 拡張単独 VRR (%) | **結合 VRR (どちらか崩壊で無効, %)** | Valid 中文字化け率 (%) | Cond.ASR HB (結合, %) | Cond.ASR WG (結合, %) | Cond.ASR SR (結合, %) | VSR HB (結合, %) | HumanEval (暫定, %) | MBPP (暫定, %) | Code Avg (暫定, %) |",
        "|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for cond_label, blk in [("Before (10,000)", r["before_rope1e4"]), ("**After (1,000,000)**", r["after_rope1e6"])]:
            s = blk["safety"]
            c = blk["code"]
            md.append(
                f"| {r['label']} | {cond_label} "
                f"| {_fmt(s['rule_vrr'])} | {_fmt(s['ext_only_vrr'])} | **{_fmt(s['ext_vrr'])}** "
                f"| {_fmt(s['salad_in_rule_valid_pct'])} "
                f"| {_fmt(s['cond_hb_ext'])} | {_fmt(s['cond_wg_ext'])} | {_fmt(s['cond_sr_ext'])} "
                f"| {_fmt(s['vsr_hb_ext'])} | {_fmt(c['humaneval'])} | {_fmt(c['mbpp'])} | {_fmt(c['code_avg'])} |"
            )

    md += [
        "",
        "## 2. 従来ルール妥当性（P1 修正前）での 3 分類器乖離（Before vs After）",
        "",
        "| 手法 | 条件 (`rope_theta`) | Cond.ASR HB (従来, %) | Cond.ASR WG (従来, %) | Cond.ASR SR (従来, %) | VSR HB (従来, %) |",
        "|:---|:---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for cond_label, blk in [("Before (10,000)", r["before_rope1e4"]), ("After (1,000,000)", r["after_rope1e6"])]:
            s = blk["safety"]
            md.append(
                f"| {r['label']} | {cond_label} "
                f"| {_fmt(s['cond_hb_rule'])} | {_fmt(s['cond_wg_rule'])} | {_fmt(s['cond_sr_rule'])} | {_fmt(s['vsr_hb_rule'])} |"
            )

    md += [
        "",
        "## 3. ベンチマーク別詳細（結合 VRR・文字化け率・3 分類器別 Cond.ASR）",
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
                f"| {_fmt(sb['salad_in_rule_valid_pct'])} | {_fmt(sa['salad_in_rule_valid_pct'])} "
                f"| {_fmt(sb['ext_vrr'])} | {_fmt(sa['ext_vrr'])} "
                f"| {_fmt(sb['cond_hb_ext'])} | {_fmt(sa['cond_hb_ext'])} "
                f"| {_fmt(sb['cond_nat_ext'])} | {_fmt(sa['cond_nat_ext'])} |"
            )

    md += [
        "",
        "## 4. 結果の解釈と結論（指示書 v2 §4.4・草稿 6.4 節用）",
        "",
        f"- **`DARE`**: `rope_theta` を `1,000,000` に修正しても Valid 中文字化け率は **{_fmt(da_b['safety']['salad_in_rule_valid_pct'])}% → {_fmt(da_a['safety']['salad_in_rule_valid_pct'])}%**、結合 VRR は **{_fmt(da_b['safety']['ext_vrr'])}% → {_fmt(da_a['safety']['ext_vrr'])}%** であり、崩壊は止まらなかった（コード有用性暫定値: {_fmt(da_b['code']['code_avg'])}% → {_fmt(da_a['code']['code_avg'])}%）。",
        f"- **`fp16 SST (v3)`**: `rope_theta` の修正により Valid 中文字化け率は **{_fmt(st_b['safety']['salad_in_rule_valid_pct'])}% → {_fmt(st_a['safety']['salad_in_rule_valid_pct'])}%** にやや低下し、結合 VRR は **{_fmt(st_b['safety']['ext_vrr'])}% → {_fmt(st_a['safety']['ext_vrr'])}%** へ約 2 倍に上昇した（部分的な効果あり）。しかし依然として結合 VRR は 15.89% にとどまり、妥当性下限（90%）を大きく下回って崩壊は止まらなかった（コード有用性暫定値: {_fmt(st_b['code']['code_avg'])}% → {_fmt(st_a['code']['code_avg'])}%）。",
        f"- **`Task Arithmetic`**: 元々崩壊が少なかった TA（結合 VRR {_fmt(ta_b['safety']['ext_vrr'])}% → {_fmt(ta_a['safety']['ext_vrr'])}%）では、`rope_theta=1,000,000` への修正により HarmBench 条件付き ASR が **{_fmt(ta_b['safety']['cond_hb_ext'])}% → {_fmt(ta_a['safety']['cond_hb_ext'])}%**、WildGuard 条件付き ASR が **{_fmt(ta_b['safety']['cond_wg_ext'])}% → {_fmt(ta_a['safety']['cond_wg_ext'])}%** へ低下した一方、StrongREJECT は **{_fmt(ta_b['safety']['cond_sr_ext'])}% → {_fmt(ta_a['safety']['cond_sr_ext'])}%** とほぼ横ばいだった（コード有用性暫定値: HumanEval {_fmt(ta_b['code']['humaneval'])}% → {_fmt(ta_a['code']['humaneval'])}%、MBPP {_fmt(ta_b['code']['mbpp'])}% → {_fmt(ta_a['code']['mbpp'])}%）。",
        "- **結論（主張の範囲）**: `rope_theta` の取り違え修正は一部に効く（SST の結合 VRR が 7.63% → 15.89% に上昇、TA の HarmBench 条件付き ASR が 34.43% → 23.63% に低下）ものの、**それだけでは崩壊は止まらず、「設定の取り違え（`rope_theta`）だけでは崩壊を説明できない」**ことが確かめられた。",
        "- **留意点・切り分けの限界**: WizardCoder-Python-7B-V1.0 は事前学習系統（CodeLlama）だけでなく語彙数（`32,001` vs Llama-2 の `32,000`）もベースと異なるため、残存する崩壊に対して事前学習系統の違いと語彙数の違いのどちらがどの程度効いているかまでは本実験では切り分けていない。また `α=0.6, seed42` の 1 点での確認である。論文でもこの範囲にとどめて記述する。",
    ]

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pattern": "safety+code",
        "alpha": 0.6,
        "seed": 42,
        "code_utility_status": "provisional_pending_wizardcoder_eval_gate",
        "vrr_definition": "either_rule_or_extended_collapse_is_invalid",
        "rows": rows,
    }
    write_json(out_dir / "rope_theta_ablation_summary.json", payload)
    write_text(out_dir / "rope_theta_ablation_summary.md", "\n".join(md) + "\n")
    if summary_json_path is not None:
        write_json(summary_json_path, payload)
    print(f"保存完了: {out_dir / 'rope_theta_ablation_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
