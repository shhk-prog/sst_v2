#!/usr/bin/env python3
"""
generate_summary_tables.py

sst_v2 v3 の評価結果 JSON 群からスコアを自動収集・集計し、
マークダウン形式および CSV 形式の比較表を自動生成するスクリプト。

【安全指標および全体集計の強化点】
- Math, Code, Medical, General/Inst の各ベンチマークスコアの厳密抽出・復旧
- JailbreakBench, StrongReject, WildJailbreak について以下 4 指標の詳細集計：
  1. Original ASR (排除前 %)
  2. Filtered ASR (排除後 %)
  3. Gibberish N (排除サンプル数)
  4. Gibberish Filter Ratio (排除率 %)
- Safety Ave の 2 区分分離集計：
  1. Safety Ave [Refusal-Filtered] (ASR↓ %): 拒否文言の有無判定 (Filtered ASR 排除後ベース)
  2. Safety Ave [Harmful Content] (ASR↓ %): 明確な有害指示/情報が含まれているかの判定 (HarmBench 統一 ASR ベース)
"""

import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
from collections import defaultdict


# 定数・定義
PATTERNS = [
    "safety+math+code+medical",
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
    "Pattern", "Method", "Alpha",
    # 2 区分 Safety 平均 & 他 4 カテゴリ平均
    "Safety Ave [Refusal-Filtered] (ASR↓ %)",
    "Safety Ave [Harmful Content] (ASR↓ %)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
    # HarmBench
    "HarmBench (ASR↓ %)",
    # JailbreakBench 詳細
    "JailbreakBench Original ASR (%)", "JailbreakBench Filtered ASR (%)", "JailbreakBench Gibberish N", "JailbreakBench Gibberish Ratio (%)", "JailbreakBench Harmful Content (ASR↓ %)",
    # StrongReject 詳細
    "StrongReject Original ASR (%)", "StrongReject Filtered ASR (%)", "StrongReject Gibberish N", "StrongReject Gibberish Ratio (%)", "StrongReject Harmful Content (ASR↓ %)",
    # WildJailbreak 詳細
    "WildJailbreak Original ASR (%)", "WildJailbreak Filtered ASR (%)", "WildJailbreak Gibberish N", "WildJailbreak Gibberish Ratio (%)", "WildJailbreak Harmful Content (ASR↓ %)",
    # Math
    "GSM8K (%)", "Minerva Math500 (%)",
    # Code
    "HumanEval (%)", "MBPP (%)",
    # Medical
    "PubMedQA (%)", "MedQA (%)",
    # General / Instruction
    "MMLU (%)", "IFEval (%)", "AlpacaEval2 WinRate (%)",
    "Evol-Code Similarity (%)", "Evol-Code PPL (↓)",
    "MedAlpaca Similarity (%)", "MedAlpaca PPL (↓)"
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate comprehensive summary markdown/csv tables.")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results/debug_limit320/merged",
        help="Path to the merged results directory (e.g. results/debug_limit320/merged)"
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
        default=0.5,
        help="Fixed alpha value for the method comparison table (default: 0.5)"
    )
    return parser.parse_args()


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def extract_safety_details_from_json(data):
    """結果 JSON から Safety の Filtered ASR(%), Original ASR(%), Gibberish N, Gibberish Filter Ratio(%), HarmBench Cls ASR(%) を抽出する。"""
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None

    filt_asr = data.get("asr")
    orig_asr = data.get("original_asr")
    gib_n = data.get("gibberish_n")
    gib_ratio = data.get("gibberish_ratio")
    hb_cls_asr = data.get("harmbench_cls_asr")

    f_val = float(filt_asr) * 100.0 if (filt_asr is not None and float(filt_asr) <= 1.0) else (float(filt_asr) if filt_asr is not None else None)
    o_val = float(orig_asr) * 100.0 if (orig_asr is not None and float(orig_asr) <= 1.0) else (float(orig_asr) if orig_asr is not None else f_val)
    gn_val = int(gib_n) if gib_n is not None else 0
    gr_val = float(gib_ratio) if gib_ratio is not None else 0.0
    hbc_val = float(hb_cls_asr) * 100.0 if (hb_cls_asr is not None and float(hb_cls_asr) <= 1.0) else (float(hb_cls_asr) if hb_cls_asr is not None else f_val)

    return {
        "filtered_asr": f_val,
        "original_asr": o_val,
        "gibberish_n": gn_val,
        "gibberish_ratio": gr_val,
        "harmbench_cls_asr": hbc_val
    }


def extract_metric_from_json(data, metric_key):
    """結果 JSON から非 Safety スコア(%) を抽出する。"""
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

    # 2. Instruction benchmarks (inst_evol_code, inst_medalpaca): PPL and Similarity
    if metric_key in ["inst_evol_code", "inst_medalpaca"]:
        metrics = data.get("metrics", {})
        ppl = metrics.get("perplexity") if isinstance(metrics, dict) else None
        if ppl is None:
            ppl = data.get("perplexity")

        sim = metrics.get("similarity_score") if isinstance(metrics, dict) else None
        if sim is None:
            sim = data.get("similarity_score")
        if sim is not None and isinstance(sim, (int, float)):
            sim = float(sim) * 100.0 if float(sim) <= 1.0 else float(sim)

        return {
            "ppl": float(ppl) if (ppl is not None and not np.isnan(float(ppl)) and not np.isinf(float(ppl))) else None,
            "sim": sim
        }

    # 3. lm-evaluation-harness (MMLU, IFEval, GSM8K, Minerva, HumanEval, MBPP, PubMedQA, MedQA)
    results = data.get("results", {})
    if not results or not isinstance(results, dict):
        return None

    # 3a. MMLU (全サブタスクの相加平均)
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

    # 3b. その他の単一タスク評価
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
            s_details = extract_safety_details_from_json(content)
            if s_details is not None:
                data_store[key][info["metric_key"]] = s_details
        else:
            score = extract_metric_from_json(content, info["metric_key"])
            if score is not None:
                data_store[key][info["metric_key"]] = score

    return data_store


def row_to_dict(pattern, method, alpha, metric_values):
    # 1. Safety Filtered ASR (拒否文言の有無判定/排除後): HarmBench を除外した 3 タスク (JailbreakBench, StrongReject, WildJailbreak) の平均
    s_filt_vals = []
    for task in ["jailbreakbench", "strongreject", "wildjailbreak"]:
        t_data = metric_values.get(task)
        if isinstance(t_data, dict) and t_data.get("filtered_asr") is not None:
            s_filt_vals.append(t_data["filtered_asr"])

    # 2. Safety HarmBench Cls ASR (明確な有害指示/情報判定): 全 4 タスクの HarmBench 基準の平均
    s_hb_vals = []
    for task in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]:
        t_data = metric_values.get(task)
        if isinstance(t_data, dict):
            if t_data.get("harmbench_cls_asr") is not None:
                s_hb_vals.append(t_data["harmbench_cls_asr"])
            elif t_data.get("filtered_asr") is not None:
                s_hb_vals.append(t_data["filtered_asr"])

    s_ref_ave = np.mean(s_filt_vals) if s_filt_vals else None
    s_harm_ave = np.mean(s_hb_vals) if s_hb_vals else None

    # Math Ave
    m_vals = [metric_values.get(m) for m in ["gsm8k", "minerva_math500"] if isinstance(metric_values.get(m), (int, float))]
    m_ave = np.mean(m_vals) if m_vals else None

    # Code Ave
    c_vals = [metric_values.get(m) for m in ["humaneval", "mbpp"] if isinstance(metric_values.get(m), (int, float))]
    c_ave = np.mean(c_vals) if c_vals else None

    # Medical Ave
    med_vals = [metric_values.get(m) for m in ["pubmedqa", "medqa_4options"] if isinstance(metric_values.get(m), (int, float))]
    med_ave = np.mean(med_vals) if med_vals else None

    # General/Inst Ave (標準的指標 MMLU, IFEval, AlpacaEval2 の相加平均)
    g_vals = [metric_values.get(m) for m in ["mmlu", "ifeval", "alpaca_eval2"] if isinstance(metric_values.get(m), (int, float))]
    g_ave = np.mean(g_vals) if g_vals else None

    def get_s_attr(task_name, attr_name):
        t_data = metric_values.get(task_name)
        if isinstance(t_data, dict):
            return t_data.get(attr_name)
        return None

    return {
        "Pattern": pattern,
        "Method": method,
        "Alpha": alpha if alpha == "N/A" else (f"{alpha:.2f}" if isinstance(alpha, (int, float)) else str(alpha)),

        # 2 区分 Safety Ave
        "Safety Ave [Refusal-Filtered] (ASR↓ %)": s_ref_ave,
        "Safety Ave [Harmful Content] (ASR↓ %)": s_harm_ave,

        # ドメイン平均
        "Math Ave (%)": m_ave,
        "Code Ave (%)": c_ave,
        "Medical Ave (%)": med_ave,
        "General/Inst Ave (%)": g_ave,

        # HarmBench
        "HarmBench (ASR↓ %)": get_s_attr("harmbench", "filtered_asr"),

        # JailbreakBench
        "JailbreakBench Original ASR (%)": get_s_attr("jailbreakbench", "original_asr"),
        "JailbreakBench Filtered ASR (%)": get_s_attr("jailbreakbench", "filtered_asr"),
        "JailbreakBench Gibberish N": get_s_attr("jailbreakbench", "gibberish_n"),
        "JailbreakBench Gibberish Ratio (%)": get_s_attr("jailbreakbench", "gibberish_ratio"),
        "JailbreakBench Harmful Content (ASR↓ %)": get_s_attr("jailbreakbench", "harmbench_cls_asr"),

        # StrongReject
        "StrongReject Original ASR (%)": get_s_attr("strongreject", "original_asr"),
        "StrongReject Filtered ASR (%)": get_s_attr("strongreject", "filtered_asr"),
        "StrongReject Gibberish N": get_s_attr("strongreject", "gibberish_n"),
        "StrongReject Gibberish Ratio (%)": get_s_attr("strongreject", "gibberish_ratio"),
        "StrongReject Harmful Content (ASR↓ %)": get_s_attr("strongreject", "harmbench_cls_asr"),

        # WildJailbreak
        "WildJailbreak Original ASR (%)": get_s_attr("wildjailbreak", "original_asr"),
        "WildJailbreak Filtered ASR (%)": get_s_attr("wildjailbreak", "filtered_asr"),
        "WildJailbreak Gibberish N": get_s_attr("wildjailbreak", "gibberish_n"),
        "WildJailbreak Gibberish Ratio (%)": get_s_attr("wildjailbreak", "gibberish_ratio"),
        "WildJailbreak Harmful Content (ASR↓ %)": get_s_attr("wildjailbreak", "harmbench_cls_asr"),

        # Math
        "GSM8K (%)": metric_values.get("gsm8k"),
        "Minerva Math500 (%)": metric_values.get("minerva_math500"),

        # Code
        "HumanEval (%)": metric_values.get("humaneval"),
        "MBPP (%)": metric_values.get("mbpp"),

        # Medical
        "PubMedQA (%)": metric_values.get("pubmedqa"),
        "MedQA (%)": metric_values.get("medqa_4options"),

        # General / Instruction
        "MMLU (%)": metric_values.get("mmlu"),
        "IFEval (%)": metric_values.get("ifeval"),
        "AlpacaEval2 WinRate (%)": metric_values.get("alpaca_eval2"),
        "Evol-Code Similarity (%)": get_s_attr("inst_evol_code", "sim"),
        "Evol-Code PPL (↓)": get_s_attr("inst_evol_code", "ppl"),
        "MedAlpaca Similarity (%)": get_s_attr("inst_medalpaca", "sim"),
        "MedAlpaca PPL (↓)": get_s_attr("inst_medalpaca", "ppl"),
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
        if "Gibberish N" in col:
            return f"{int(round(mean))} ± {int(round(std))}"
        elif "PPL" in col:
            return f"{mean:.2f} ± {std:.2f}"
        else:
            return f"{mean:.2f} ± {std:.2f}%"
    elif isinstance(val, (int, float)):
        if np.isnan(val):
            return "-"
        if "Gibberish N" in col:
            return f"{int(val)}"
        elif "PPL" in col:
            return f"{val:.2f}"
        else:
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
    print(f"Loaded records for {len(df_aggregated)} unique (pattern, method, alpha) configurations.")

    md_output_path = os.path.join(args.output_dir, "evaluation_summary_tables.md")
    md_lines = [
        "# 多次元評価スコア自動集計・比較レポート (3 Seeds Mean ± Std)",
        "",
        "本レポートは `sst_v2` v3 の並列評価結果から自動生成された全指標およびドメイン平均スコア比較表 (Mean ± Std) です。",
        "",
        "---",
        "",
        "# ===== 3 Seeds (Mean ± Std) 評価結果 =====",
        ""
    ]

    # ----------------------------------------------------
    # 表タイプ 1: Alpha 指定比較表
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

        csv_filename = f"summary_target_alpha_{args.target_alpha}_{pattern}.csv"
        df_to_formatted_df(df_target_alpha).to_csv(os.path.join(args.output_dir, csv_filename), index=False, encoding="utf-8-sig")

    # ----------------------------------------------------
    # 表タイプ 2: Merge 手法別全 α パラメータ独立表
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

            csv_filename = f"summary_{method}_{pattern}.csv"
            df_to_formatted_df(df_meth_pat).to_csv(os.path.join(args.output_dir, csv_filename), index=False, encoding="utf-8-sig")

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[Success] Summary tables generated successfully!")
    print(f"Markdown report saved to: {md_output_path}")
    print(f"CSV files saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()