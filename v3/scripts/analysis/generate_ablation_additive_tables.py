#!/usr/bin/env python3
"""
generate_ablation_additive_tables.py

sst_v2 v3 のアブレーション評価結果 JSON 群からスコアを自動収集・集計し、
特に additive 変分 (addactive) および interpolation 変分との比較表を自動生成する。
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
    "safety+math+code+medical",
    "safety+math",
    "safety+code",
    "safety+medical"
]

SEEDS = [42, 43, 44]


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def extract_safety_harmful_asr(data):
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None

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
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None

    if metric_key == "alpaca_eval2":
        val = data.get("length_controlled_winrate")
        if val is None:
            val = data.get("win_rate")
        if val is not None and isinstance(val, (int, float)):
            v = float(val)
            return v * 100.0 if v <= 1.0 else v
        return None

    if metric_key in ["inst_evol_code", "inst_medalpaca"]:
        metrics = data.get("metrics", {})
        val = metrics.get("similarity_score") if isinstance(metrics, dict) else None
        if val is None:
            val = data.get("similarity_score")
        if val is not None and isinstance(val, (int, float)):
            v = float(val)
            return v * 100.0 if v <= 1.0 else v
        return None

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
    for p in PATTERNS:
        if p in filename:
            pattern = p
            break

    variant = "interpolation"
    if "additive" in filename:
        variant = "additive"

    sst_ratio = "FhFb"
    if "Fh_only" in filename:
        sst_ratio = "Fh_only"
    elif "1Fb_only" in filename:
        sst_ratio = "1Fb_only"
    elif "magnitude" in filename:
        sst_ratio = "magnitude"
    elif "random" in filename:
        sst_ratio = "random"

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
    if "diagonal_sst" in filename:
        method = "diagonal_sst"
    elif "data_free_sst" in filename:
        method = "data_free_sst"
    elif "ties" in filename:
        method = "ties"
    elif "dare" in filename:
        method = "dare"
    elif "della" in filename:
        method = "della"
    elif "task_arithmetic" in filename:
        method = "task_arithmetic"
    elif "safemerge" in filename:
        method = "safemerge"

    return {
        "method": method,
        "pattern": pattern,
        "variant": variant,
        "sst_ratio": sst_ratio,
        "alpha": alpha,
        "seed": seed,
        "metric_key": metric_key
    }


def process_results(results_dir="v3/results"):
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
        if content is None:
            continue

        key = (info["seed"], info["pattern"], info["method"], info["variant"], info["sst_ratio"], info["alpha"])

        if info["metric_key"] in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]:
            s_val = extract_safety_harmful_asr(content)
            if s_val is not None:
                data_store[key][info["metric_key"]] = s_val
        else:
            score = extract_metric_from_json(content, info["metric_key"])
            if score is not None:
                data_store[key][info["metric_key"]] = score

    return data_store


def get_mean_std(vals):
    valid_vals = [v for v in vals if v is not None and isinstance(v, (int, float)) and not np.isnan(v)]
    if not valid_vals:
        return None
    mean = float(np.mean(valid_vals))
    std = float(np.std(valid_vals, ddof=1)) if len(valid_vals) > 1 else 0.0
    return (mean, std)


def format_val(val):
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


def build_summary_dataframe(data_store):
    grouped_by_config = defaultdict(list)
    for (seed, pattern, method, variant, sst_ratio, alpha), metrics in data_store.items():
        if seed is not None and seed not in SEEDS:
            continue
        config_key = (pattern, method, variant, sst_ratio, alpha)
        grouped_by_config[config_key].append(metrics)

    rows = []
    for (pattern, method, variant, sst_ratio, alpha), list_of_metrics in grouped_by_config.items():
        seed_scores = []
        for m_dict in list_of_metrics:
            def safe_val(k):
                v = m_dict.get(k)
                return float(v) if v is not None else None

            def safe_mean(keys):
                vals = [safe_val(k) for k in keys if safe_val(k) is not None]
                return float(np.mean(vals)) if vals else None

            s_score = {
                "Safety Ave [Harmful Content] (ASR↓ %)": safe_mean(["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]),
                "Math Ave (%)": safe_mean(["gsm8k", "minerva_math500"]),
                "Code Ave (%)": safe_mean(["humaneval", "mbpp"]),
                "Medical Ave (%)": safe_mean(["pubmedqa", "medqa_4options"]),
                "General/Inst Ave (%)": safe_mean(["mmlu", "ifeval", "alpaca_eval2", "inst_evol_code", "inst_medalpaca"]),
                "HarmBench (ASR↓ %)": safe_val("harmbench"),
                "GSM8K (%)": safe_val("gsm8k"),
                "HumanEval (%)": safe_val("humaneval"),
                "PubMedQA (%)": safe_val("pubmedqa"),
                "MedQA (%)": safe_val("medqa_4options"),
                "MMLU (%)": safe_val("mmlu")
            }
            seed_scores.append(s_score)

        alpha_str = f"{alpha:.1f}" if isinstance(alpha, (int, float)) else (str(alpha) if alpha is not None else "N/A")

        row = {
            "Pattern": pattern,
            "Method": method,
            "Variant": variant,
            "SST Ratio": sst_ratio,
            "Alpha": alpha_str,
        }

        metric_headers = [
            "Safety Ave [Harmful Content] (ASR↓ %)", "Math Ave (%)", "Code Ave (%)",
            "Medical Ave (%)", "General/Inst Ave (%)", "HarmBench (ASR↓ %)",
            "GSM8K (%)", "HumanEval (%)", "PubMedQA (%)", "MedQA (%)", "MMLU (%)"
        ]

        for h in metric_headers:
            vals = [ss.get(h) for ss in seed_scores if ss.get(h) is not None]
            row[h] = get_mean_std(vals)

        rows.append(row)

    return pd.DataFrame(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate ablation additive summary tables.")
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
        help="Target fixed alpha value for comparison (default: 0.6)"
    )
    return parser.parse_args()


def generate_markdown_report(df, output_path, target_alpha=0.6):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def format_df(sub_df, columns):
        if sub_df.empty:
            return pd.DataFrame(columns=columns)
        cols = [c for c in columns if c in sub_df.columns]
        res = sub_df[cols].copy()
        for c in res.columns:
            if c not in ["Pattern", "Method", "Variant", "SST Ratio", "Alpha"]:
                res[c] = res[c].apply(format_val)
        return res

    summary_cols = [
        "Pattern", "Method", "Variant", "Alpha",
        "Safety Ave [Harmful Content] (ASR↓ %)",
        "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)"
    ]

    detailed_cols = [
        "Pattern", "Method", "Variant", "Alpha",
        "Safety Ave [Harmful Content] (ASR↓ %)",
        "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
        "HarmBench (ASR↓ %)", "GSM8K (%)", "HumanEval (%)", "PubMedQA (%)", "MedQA (%)", "MMLU (%)"
    ]

    target_alpha_str = f"{target_alpha:.1f}"

    md = []
    md.append("# Ablation Additive (Addactive) 集計結果レポート (3 Seeds Mean ± Std)\n")
    md.append("本レポートは SST-Merge v3 におけるアブレーション実験データから、`additive` 変分 (addactive) および `interpolation` 変分との比較スコア (Mean ± Std) を自動集計したものです。\n")

    # 1. Additive vs Interpolation
    md.append(f"## Part 1: Additive vs Interpolation 比較表 (Alpha = {target_alpha_str}, Seed 42-44 Mean ± Std)\n")
    df_p1 = df[df["Alpha"] == target_alpha_str].copy() if not df.empty else df
    df_p1_fmt = format_df(df_p1, summary_cols)
    if not df_p1_fmt.empty:
        md.append(df_p1_fmt.to_markdown(index=False))
    else:
        md.append(f"※ Alpha = {target_alpha_str} の比較データはありませんでした。\n")

    md.append("\n---\n")

    # 2. Additive 変分の Alpha スイープ
    md.append("## Part 2: Additive 変分の Alpha スイープ比較表 (Additive, Seed 42-44 Mean ± Std)\n")
    df_p2 = df[df["Variant"] == "additive"].copy() if not df.empty else df
    df_p2_fmt = format_df(df_p2, detailed_cols)
    if not df_p2_fmt.empty:
        md.append(df_p2_fmt.to_markdown(index=False))
    else:
        md.append("※ Additive 変分のスイープデータはありませんでした。\n")

    md.append("\n---\n")

    # 3. 全アブレーション条件一覧
    md.append("## Part 3: 全アブレーション条件・全変分比較一覧表 (Seeds 42-44 Mean ± Std)\n")
    df_p3_fmt = format_df(df, detailed_cols)
    if not df_p3_fmt.empty:
        md.append(df_p3_fmt.to_markdown(index=False))
    else:
        md.append("※ データはありませんでした。\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return output_path


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "ablation_additive_summary_tables.md")
    csv_path = os.path.join(args.output_dir, "ablation_additive_summary_tables.csv")

    print(f"Processing results from: {args.results_dir} ...")
    data_store = process_results(args.results_dir)
    df = build_summary_dataframe(data_store)
    out_file = generate_markdown_report(df, output_path, target_alpha=args.target_alpha)

    # また CSV 形式でも保存
    df_fmt = df.copy()
    for col in df_fmt.columns:
        if col not in ["Pattern", "Method", "Variant", "SST Ratio", "Alpha"]:
            df_fmt[col] = df_fmt[col].apply(format_val)
    df_fmt.to_csv(csv_path, index=False, encoding="utf-8")

    print(f"Report successfully created at: {out_file}")
    print(f"CSV saved at: {csv_path}")


if __name__ == "__main__":
    main()