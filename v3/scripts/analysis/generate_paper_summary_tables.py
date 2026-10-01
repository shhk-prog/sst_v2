#!/usr/bin/env python3
"""
generate_paper_summary_tables.py

sst_v2 v3 の並列評価結果 JSON 群から、論文・レポート報告用に特化した
簡潔かつ明確な 5 大ドメイン平均比較表を自動生成するスクリプト。

【抽出・集計仕様】
1. 対象パターン: safety+math, safety+code, safety+medical (3パターン)
2. シード平均: seed 42, 43, 44 の相加平均
3. 評価指標 (5 大ドメイン平均のみ):
   - Safety Ave [Harmful Content] (ASR↓ %)
   - Math Ave (%)
   - Code Ave (%)
   - Medical Ave (%)
   - General/Inst Ave (%)
4. テーブル出力構造:
   - Part 1: Alpha = 0.6 手法間比較表 (全手法対象、パターン別)
   - Part 2: 手法別の α パラメータスイープ比較表 (手法・パターン別)
"""

import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
from collections import defaultdict


PATTERNS = [
    "safety+math",
    "safety+code",
    "safety+medical"
]

SEEDS = [42, 43, 44]

METHODS = [
    "diagonal_sst_main",
    "data_free_sst_main",
    "ties",
    "dare",
    "della",
    "task_arithmetic",
    "safemerge",
    "led_merging",
    "matena_fisher",
    "mergealign"
]

SINGLE_RUN_METHODS = {
    "safemerge",
    "led_merging",
    "matena_fisher",
    "mergealign",
    "fisher_weighted"
}

DISPLAY_HEADERS = [
    "Pattern",
    "Method",
    "Alpha",
    "Safety Ave [Harmful Content] (ASR↓ %)",
    "Math Ave (%)",
    "Code Ave (%)",
    "Medical Ave (%)",
    "General/Inst Ave (%)"
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate concise paper summary markdown and CSV tables.")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results/debug_limit320/merged",
        help="Path to merged results directory"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="results/summary_tables",
        help="Directory to save generated markdown and csv files"
    )
    parser.add_argument(
        "--target_alpha",
        type=float,
        default=0.6,
        help="Target fixed alpha value for method comparison table (default: 0.6)"
    )
    return parser.parse_args()


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def extract_safety_harmful_asr(data, valid_only=False):
    """結果 JSON から Harmful Content (ASR↓ %) を抽出する (0~100 % 表記)。"""
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None

    if valid_only:
        results = data.get("results", [])
        if results and isinstance(results, list):
            valid_samples = [item for item in results if not item.get("is_gibberish", False)]
            if not valid_samples:
                return None  # 全出力が崩壊しているモデル
            harmful_count = sum(
                1 for item in valid_samples
                if item.get("harmbench_cls_output") == "Yes"
                or (item.get("original_asr") is not None and float(item.get("original_asr")) > 0.5)
                or (item.get("asr") is not None and float(item.get("asr")) > 0.5)
            )
            return (float(harmful_count) / float(len(valid_samples))) * 100.0

    hb_cls_asr = data.get("harmbench_cls_asr")
    if hb_cls_asr is not None:
        v = float(hb_cls_asr)
        return v * 100.0 if v <= 1.0 else v

    filt_asr = data.get("asr")
    if filt_asr is not None:
        v = float(filt_asr)
        return v * 100.0 if v <= 1.0 else v

    return None


def extract_metric_from_json(data, metric_key):
    """結果 JSON から非 Safety スコア (%) を抽出する。"""
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None

    # 1. AlpacaEval 2
    if metric_key == "alpaca_eval2":
        val = data.get("length_controlled_winrate")
        if val is None:
            val = data.get("win_rate")
        if val is not None and isinstance(val, (int, float)):
            v = float(val)
            return v * 100.0 if v <= 1.0 else v
        return None

    # 2. Instruction benchmarks (inst_evol_code, inst_medalpaca): Perplexity (PPL↓) を使用
    if metric_key in ["inst_evol_code", "inst_medalpaca"]:
        metrics = data.get("metrics", {})
        val = metrics.get("perplexity") if isinstance(metrics, dict) else None
        if val is None:
            val = data.get("perplexity")
        if val is not None and isinstance(val, (int, float)):
            return float(val)
        return None

    # 3. lm-evaluation-harness (MMLU, IFEval, GSM8K, Minerva, HumanEval, MBPP, PubMedQA, MedQA)
    results = data.get("results", {})
    if not results or not isinstance(results, dict):
        return None

    if metric_key == "mmlu":
        mmlu_accs = []
        for task_name, task_metrics in results.items():
            if isinstance(task_metrics, dict) and ("mmlu" in task_name or "mmlu" in data.get("configs", {})):
                val = task_metrics.get("acc,none") or task_metrics.get("acc")
                if val is not None and isinstance(val, (int, float)):
                    v = float(val)
                    mmlu_accs.append(v * 100.0 if v <= 1.0 else v)
        if mmlu_accs:
            return float(np.mean(mmlu_accs))
        return None

    target_task_metrics = None
    for task_name, task_metrics in results.items():
        if isinstance(task_metrics, dict):
            if metric_key in task_name or (metric_key == "medqa_4options" and "medqa" in task_name) or (metric_key == "minerva_math500" and "math" in task_name):
                target_task_metrics = task_metrics
                break

    if target_task_metrics is None and len(results) == 1:
        target_task_metrics = list(results.values())[0]

    if not isinstance(target_task_metrics, dict):
        return None

    priority_keys = [
        "pass@1",
        "pass_at_1,none",
        "exact_match,flexible-extract",
        "math_verify,none",
        "prompt_level_strict_acc,none",
        "acc,none",
        "acc",
        "exact_match,strict-match"
    ]

    for k in priority_keys:
        if k in target_task_metrics:
            val = target_task_metrics[k]
            if val is not None and isinstance(val, (int, float)):
                v = float(val)
                return v * 100.0 if v <= 1.0 else v

    return None


def parse_filename_info(filename):
    parts = filename.split("_")

    seed = None
    for part in parts:
        if part.startswith("seed") and part[4:].isdigit():
            seed = int(part[4:])
            break

    alpha = None
    for part in parts:
        if part.startswith("alpha"):
            try:
                alpha = float(part.replace("alpha", ""))
            except Exception:
                pass

    pattern = None
    if "safety+math+code+medical" in filename:
        pattern = "safety+math+code+medical"
    else:
        for p in PATTERNS:
            if p in filename:
                pattern = p
                break

    metric_key = None
    if "harmbench" in filename:
        metric_key = "harmbench"
    elif "jailbreakbench" in filename:
        metric_key = "jailbreakbench"
    elif "strongreject" in filename:
        metric_key = "strongreject"
    elif "wildjailbreak" in filename:
        metric_key = "wildjailbreak"
    elif "gsm8k" in filename:
        metric_key = "gsm8k"
    elif "minerva_math500" in filename:
        metric_key = "minerva_math500"
    elif "humaneval" in filename:
        metric_key = "humaneval"
    elif "mbpp" in filename:
        metric_key = "mbpp"
    elif "pubmedqa" in filename:
        metric_key = "pubmedqa"
    elif "medqa_4options" in filename or "medqa" in filename:
        metric_key = "medqa_4options"
    elif "mmlu" in filename:
        metric_key = "mmlu"
    elif "ifeval" in filename:
        metric_key = "ifeval"
    elif "alpaca_eval2" in filename:
        metric_key = "alpaca_eval2"
    elif "inst_evol_code" in filename or "evol_code" in filename:
        metric_key = "inst_evol_code"
    elif "inst_medalpaca" in filename or "medalpaca" in filename:
        metric_key = "inst_medalpaca"

    method = None
    for m in METHODS:
        if m in filename:
            method = m
            break

    if method in SINGLE_RUN_METHODS and alpha is None:
        alpha = "N/A"

    return {
        "method": method,
        "pattern": pattern,
        "alpha": alpha,
        "seed": seed,
        "metric_key": metric_key
    }


def collect_all_data(results_dir):
    data_store = defaultdict(lambda: defaultdict(dict))
    json_files = glob.glob(os.path.join(results_dir, "**", "*.json"), recursive=True)

    for filepath in json_files:
        filename = os.path.basename(filepath)
        if "summary" in filename or filename.startswith("."):
            continue

        info = parse_filename_info(filename)
        if not (info["method"] and info["pattern"] and info["metric_key"]):
            continue

        content = load_json(filepath)
        key = (info["seed"], info["pattern"], info["method"], info["alpha"])

        if info["metric_key"] in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]:
            s_val = extract_safety_harmful_asr(content)
            if s_val is not None:
                data_store[key][info["metric_key"]] = s_val
        elif info["metric_key"] in ["inst_evol_code", "inst_medalpaca"]:
            metrics = content.get("metrics", {}) if isinstance(content, dict) else {}
            ppl = metrics.get("perplexity") if isinstance(metrics, dict) else None
            if ppl is None and isinstance(content, dict):
                ppl = content.get("perplexity")

            sim = metrics.get("similarity_score") if isinstance(metrics, dict) else None
            if sim is None and isinstance(content, dict):
                sim = content.get("similarity_score")
            if sim is not None and isinstance(sim, (int, float)):
                sim = float(sim) * 100.0 if float(sim) <= 1.0 else float(sim)

            data_store[key][info["metric_key"]] = {
                "ppl": float(ppl) if (ppl is not None and not np.isnan(float(ppl)) and not np.isinf(float(ppl))) else None,
                "sim": sim
            }
        else:
            score = extract_metric_from_json(content, info["metric_key"])
            if score is not None:
                data_store[key][info["metric_key"]] = score

    return data_store


def row_to_dict(pattern, method, alpha, metric_values):
    # Safety Ave [Harmful Content] (ASR↓ %)
    s_vals = [
        metric_values.get(m)
        for m in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]
        if isinstance(metric_values.get(m), (int, float))
    ]
    s_harm_ave = float(np.mean(s_vals)) if s_vals else None

    # Math Ave (%)
    m_vals = [metric_values.get(m) for m in ["gsm8k", "minerva_math500"] if isinstance(metric_values.get(m), (int, float))]
    m_ave = float(np.mean(m_vals)) if m_vals else None

    # Code Ave (%)
    c_vals = [metric_values.get(m) for m in ["humaneval", "mbpp"] if isinstance(metric_values.get(m), (int, float))]
    c_ave = float(np.mean(c_vals)) if c_vals else None

    # Medical Ave (%)
    med_vals = [metric_values.get(m) for m in ["pubmedqa", "medqa_4options"] if isinstance(metric_values.get(m), (int, float))]
    med_ave = float(np.mean(med_vals)) if med_vals else None

    # General/Inst Ave (%) : 学術的・標準的ベンチマーク MMLU, IFEval, AlpacaEval2 の相加平均
    g_raw = [metric_values.get(m) for m in ["mmlu", "ifeval", "alpaca_eval2"] if isinstance(metric_values.get(m), (int, float))]
    g_ave = float(np.mean(g_raw)) if g_raw else None

    return {
        "Pattern": pattern,
        "Method": method,
        "Alpha": alpha if alpha == "N/A" else (f"{alpha:.2f}" if isinstance(alpha, (int, float)) else str(alpha)),

        # 5 大ドメイン平均指標
        "Safety Ave [Harmful Content] (ASR↓ %)": s_harm_ave,
        "Math Ave (%)": m_ave,
        "Code Ave (%)": c_ave,
        "Medical Ave (%)": med_ave,
        "General/Inst Ave (%)": g_ave,
    }


def get_mean_std(vals):
    valid_vals = [v for v in vals if v is not None and isinstance(v, (int, float)) and not np.isnan(v)]
    if not valid_vals:
        return None
    mean = float(np.mean(valid_vals))
    std = float(np.std(valid_vals, ddof=1)) if len(valid_vals) > 1 else 0.0
    return (mean, std)


def aggregate_seeds(data_store):
    config_groups = defaultdict(list)
    for (seed, pattern, method, alpha), metric_values in data_store.items():
        config_groups[(pattern, method, alpha)].append((seed, metric_values))

    aggregated_rows = []
    for (pattern, method, alpha), list_of_seed_metrics in config_groups.items():
        seed_rows = []
        for seed, m_values in list_of_seed_metrics:
            seed_rows.append(row_to_dict(pattern, method, alpha, m_values))

        row_dict = {
            "Pattern": pattern,
            "Method": method,
            "Alpha": alpha if alpha == "N/A" else (f"{alpha:.2f}" if isinstance(alpha, (int, float)) else str(alpha))
        }

        for header in DISPLAY_HEADERS[3:]:
            vals = [sr.get(header) for sr in seed_rows if sr.get(header) is not None]
            row_dict[header] = get_mean_std(vals)

        aggregated_rows.append(row_dict)

    return pd.DataFrame(aggregated_rows)


def create_empty_row(pattern, method, alpha):
    row = {"Pattern": pattern, "Method": method, "Alpha": str(alpha)}
    for h in DISPLAY_HEADERS[3:]:
        row[h] = None
    return row


def format_val(val, col):
    if val is None or val == "-":
        return "-"
    if isinstance(val, tuple) and len(val) == 2:
        mean, std = val
        if mean is None or np.isnan(mean):
            return "-"
        return f"{mean:.2f} ± {std:.2f}%"
    elif isinstance(val, (int, float)):
        if np.isnan(val):
            return "-"
        return f"{val:.2f}%"
    return str(val)


def format_markdown_table(df, title):
    lines = []
    lines.append(f"#### {title}\n")

    cols = [c for c in DISPLAY_HEADERS if c in df.columns]
    lines.append("| " + " | ".join(cols) + " |")

    align_row = []
    for c in cols:
        if c in ["Pattern", "Method", "Alpha"]:
            align_row.append(":---")
        else:
            align_row.append(":---:")
    lines.append("| " + " | ".join(align_row) + " |")

    for _, row in df.iterrows():
        row_str = []
        for col in cols:
            val = row[col]
            if col in ["Pattern", "Method", "Alpha"]:
                row_str.append(str(val) if val is not None else "-")
            else:
                row_str.append(format_val(val, col))
        lines.append("| " + " | ".join(row_str) + " |")

    lines.append("\n")
    return "\n".join(lines)


def df_to_formatted_df(df):
    df_fmt = df.copy()
    cols = [c for c in DISPLAY_HEADERS if c in df_fmt.columns]
    for col in cols:
        if col not in ["Pattern", "Method", "Alpha"]:
            df_fmt[col] = df_fmt[col].map(lambda v, c=col: format_val(v, c))
    return df_fmt


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading evaluation JSONs from: {args.results_dir} ...")
    data_store = collect_all_data(args.results_dir)

    df_aggregated = aggregate_seeds(data_store)
    print(f"Loaded aggregated records for {len(df_aggregated)} unique (pattern, method, alpha) configurations.")

    md_output_path = os.path.join(args.output_dir, "paper_evaluation_summary_tables.md")
    md_lines = [
        "# 論文・レポート用 5 大ドメイン平均スコア比較レポート (3 Seeds Mean ± Std)",
        "",
        "本レポートは `sst_v2` v3 の評価結果から自動生成された、主要 5 大ドメイン平均に限定した簡潔な比較表 (Mean ± Std) です。",
        "",
        "**【評価ドメインパターン】**: `safety+math`, `safety+code`, `safety+medical` (Seed 42, 43, 44 3-Seeds Mean ± Std)",
        "",
        "---",
        "",
        "# ===== 3 Seeds (Mean ± Std) 評価結果 =====",
        ""
    ]

    # ----------------------------------------------------
    # Part 1: Target Alpha (0.6) 全手法間比較表 (パターン別)
    # ----------------------------------------------------
    md_lines.append(f"## 1. 手法間比較表 (Alpha = {args.target_alpha} または αなし単一実行手法)\n")

    for pattern in PATTERNS:
        if not df_aggregated.empty:
            df_pat = df_aggregated[df_aggregated["Pattern"] == pattern].copy()
        else:
            df_pat = pd.DataFrame()

        rows = []
        for method in METHODS:
            if not df_pat.empty:
                if method in SINGLE_RUN_METHODS:
                    df_sub = df_pat[df_pat["Method"] == method]
                else:
                    df_sub = df_pat[
                        (df_pat["Method"] == method) &
                        (df_pat["Alpha"].map(lambda x: abs(float(x) - args.target_alpha) < 1e-4 if x not in ["N/A", "-", None] else False))
                    ]
            else:
                df_sub = pd.DataFrame()

            if not df_sub.empty:
                rows.append(df_sub.iloc[0].to_dict())
            else:
                dummy_alpha = "-" if method in SINGLE_RUN_METHODS else f"{args.target_alpha:.2f}"
                rows.append(create_empty_row(pattern, method, dummy_alpha))

        df_target_alpha = pd.DataFrame(rows)
        title = f"ドメインパターン: `{pattern}` (比較表: Alpha={args.target_alpha} / 単一実行手法含む)"
        md_lines.append(format_markdown_table(df_target_alpha, title))

        csv_filename = f"paper_summary_target_alpha_{args.target_alpha}_{pattern}.csv"
        df_to_formatted_df(df_target_alpha).to_csv(os.path.join(args.output_dir, csv_filename), index=False, encoding="utf-8-sig")

    # ----------------------------------------------------
    # Part 2: 手法別 α パラメータスイープ比較表 (Method / Pattern 別)
    # ----------------------------------------------------
    md_lines.append("## 2. Merge 手法別全 α パラメータ独立表 (パターン別)\n")

    for method in METHODS:
        md_lines.append(f"### 手法: `{method}` (全 Alpha パラメータ一覧)\n")

        for pattern in PATTERNS:
            if not df_aggregated.empty:
                df_meth_pat = df_aggregated[(df_aggregated["Method"] == method) & (df_aggregated["Pattern"] == pattern)].copy()
            else:
                df_meth_pat = pd.DataFrame()

            if df_meth_pat.empty:
                dummy_alpha = "-" if method in SINGLE_RUN_METHODS else f"{args.target_alpha:.2f}"
                df_meth_pat = pd.DataFrame([create_empty_row(pattern, method, dummy_alpha)])
            else:
                df_meth_pat = df_meth_pat.sort_values(
                    by=["Alpha"], key=lambda col: col.map(lambda x: -1 if x in ["N/A", "-", None] else float(x))
                )

            title = f"パターン: `{pattern}` / 手法: `{method}`"
            md_lines.append(format_markdown_table(df_meth_pat, title))

            csv_filename = f"paper_summary_{method}_{pattern}.csv"
            df_to_formatted_df(df_meth_pat).to_csv(os.path.join(args.output_dir, csv_filename), index=False, encoding="utf-8-sig")

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[Success] Paper summary tables generated successfully!")
    print(f"Markdown report saved to: {md_output_path}")
    print(f"CSV files saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()