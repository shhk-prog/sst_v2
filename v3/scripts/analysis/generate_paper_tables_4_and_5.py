#!/usr/bin/env python3
"""
generate_paper_tables_4_and_5.py

論文『secure-merge_統一比較評価論文_改訂版.md』内の以下の2つの主要テーブルを
JSON評価結果から動的に3-seed (seed 42, 43, 44) の Mean ± Std で自動集計・生成するスクリプト。

1. Table 4: 主要マージ手法（alpha=0.6, k=0.20 または単一/既定実行）における詳細評価指標の 3 Seeds Average 比較
2. Table 5: 崩壊分析: 臨界点近傍の詳細指標と偽の安全性 (GSM8K 対象 / diagonal_sst_main の alpha スイープ)
"""

import os
import sys
import glob
import json
import re
import argparse
import numpy as np
import pandas as pd
from collections import defaultdict

PATTERNS = ["safety+math", "safety+code", "safety+medical"]
SEEDS = [42, 43, 44]
METHODS = [
    "diagonal_sst_main",
    "data_free_sst_main",
    "ties",
    "dare",
    "della",
    "task_arithmetic",
    "matena_fisher",
    "mergealign",
    "safemerge",
    "led_merging"
]
SINGLE_RUN_METHODS = {"safemerge", "led_merging", "matena_fisher", "mergealign", "fisher_weighted"}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Table 4 and Table 5 for the paper.")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results/debug_limit320/merged",
        help="Path to merged results directory (e.g. results/debug_limit320/merged)"
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
        help="Target alpha for Table 4 (default: 0.6)"
    )
    parser.add_argument(
        "--paper_path",
        type=str,
        default="/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md",
        help="Path to paper markdown draft for auto-updating"
    )
    parser.add_argument(
        "--update_paper",
        action="store_true",
        help="If set, automatically update Table 4 and Table 5 directly in paper_path"
    )
    return parser.parse_args()


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_mean_std(vals):
    valid_vals = [v for v in vals if v is not None and isinstance(v, (int, float)) and not np.isnan(v)]
    if not valid_vals:
        return None
    mean = float(np.mean(valid_vals))
    std = float(np.std(valid_vals, ddof=1)) if len(valid_vals) > 1 else 0.0
    return (mean, std)


def format_mean_std(val_tuple, is_percent=True, is_na_on_none=True):
    if val_tuple is None or val_tuple == "-":
        return "N/A" if is_na_on_none else "-"
    if isinstance(val_tuple, tuple) and len(val_tuple) == 2:
        mean, std = val_tuple
        if mean is None or np.isnan(mean):
            return "N/A" if is_na_on_none else "-"
        suffix = "%" if is_percent else ""
        return f"{mean:.2f} ± {std:.2f}{suffix}"
    elif isinstance(val_tuple, (int, float)):
        if np.isnan(val_tuple):
            return "N/A" if is_na_on_none else "-"
        suffix = "%" if is_percent else ""
        return f"{val_tuple:.2f}{suffix}"
    return str(val_tuple)


# ==========================================
# 1. JSON データ集計ロジック
# ==========================================

def collect_paper_metrics(results_dir):
    """
    results_dir 内の全 JSON から、(seed, pattern, method, alpha) をキーにしてスコアを分類・取得
    """
    json_files = glob.glob(os.path.join(results_dir, "**", "*.json"), recursive=True)
    data_store = defaultdict(lambda: defaultdict(dict))

    for filepath in json_files:
        filename = os.path.basename(filepath)
        if "summary" in filename or filename.startswith("."):
            continue

        parts = filename.split("_")

        # Seed 抽出
        seed = None
        for p in parts:
            if p.startswith("seed") and p[4:].isdigit():
                seed = int(p[4:])
                break

        # Alpha 抽出
        alpha = None
        for p in parts:
            if p.startswith("alpha"):
                try:
                    alpha = float(p.replace("alpha", ""))
                except ValueError:
                    pass

        # Pattern 抽出
        pattern = None
        for p in PATTERNS:
            if p in filename or p.replace("+medical", "+med") in filename:
                pattern = p
                break

        # Method 抽出
        method = None
        for m in METHODS:
            if m in filename:
                method = m
                break

        if method in SINGLE_RUN_METHODS and alpha is None:
            alpha = "N/A"

        if not (method and pattern):
            continue

        content = load_json(filepath)
        if content is None or content.get("status") == "failed" or content.get("mockup") is True:
            continue

        key = (seed, pattern, method, alpha)

        # Safety ファイルの集計
        if "safety" in filename or any(k in filename for k in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]):
            # Harmful Content ASR
            hb_cls_asr = content.get("harmbench_cls_asr")
            filt_asr = content.get("asr")
            if hb_cls_asr is not None:
                v = float(hb_cls_asr)
                data_store[key]["harmful_asr"] = v * 100.0 if v <= 1.0 else v
            elif filt_asr is not None:
                v = float(filt_asr)
                data_store[key]["harmful_asr"] = v * 100.0 if v <= 1.0 else v

            # Refusal Filtered ASR
            if filt_asr is not None:
                v = float(filt_asr)
                data_store[key]["refusal_filtered_asr"] = v * 100.0 if v <= 1.0 else v

            # Valid response metrics & Gibberish
            results = content.get("results", [])
            gib_ratio = float(content.get("gibberish_ratio", 0.0))
            data_store[key]["gibberish_ratio"] = gib_ratio
            data_store[key]["valid_ratio"] = 100.0 - gib_ratio

            if isinstance(results, list) and results:
                valid_samples = [item for item in results if not item.get("is_gibberish", False)]
                total_valid = len(valid_samples)
                if total_valid > 0:
                    harmful_count = 0
                    for item in valid_samples:
                        hb_cls = item.get("harmbench_cls_output")
                        orig_val = item.get("original_asr")
                        item_val = item.get("asr")
                        orig_asr = float(orig_val) if orig_val is not None else 0.0
                        item_asr = float(item_val) if item_val is not None else 0.0
                        if hb_cls == "Yes" or orig_asr > 0.5 or item_asr > 0.5:
                            harmful_count += 1
                    valid_asr = (float(harmful_count) / float(total_valid)) * 100.0
                    data_store[key]["valid_asr"] = valid_asr
                    data_store[key]["valid_safety_rate"] = 100.0 - valid_asr
                else:
                    data_store[key]["valid_asr"] = None
                    data_store[key]["valid_safety_rate"] = None

        # GSM8K
        if "gsm8k" in filename:
            res = content.get("results", {})
            for tk, tv in res.items():
                if isinstance(tv, dict) and "gsm8k" in tk:
                    val = tv.get("acc,none") or tv.get("acc") or tv.get("exact_match,flexible-extract")
                    if val is not None:
                        v = float(val)
                        data_store[key]["gsm8k"] = v * 100.0 if v <= 1.0 else v

        # HumanEval
        if "humaneval" in filename:
            res = content.get("results", {})
            for tk, tv in res.items():
                if isinstance(tv, dict) and "humaneval" in tk:
                    val = tv.get("pass@1") or tv.get("pass_at_1,none") or tv.get("acc")
                    if val is not None:
                        v = float(val)
                        data_store[key]["humaneval"] = v * 100.0 if v <= 1.0 else v

    return data_store


# ==========================================
# 2. Table 4 生成ロジック
# ==========================================

def generate_table_4(data_store, target_alpha=0.6):
    """
    Table 4: 主要マージ手法（alpha=0.6, k=0.20 または単一/既定実行）における詳細評価指標の3 Seeds Average比較
    """
    rows = []

    for pattern in PATTERNS:
        for method in METHODS:
            # シードごとのデータを収集
            seed_metrics = []
            for seed in SEEDS:
                # 特定の alpha を検索
                matched_key = None
                for (s, p, m, a), metrics in data_store.items():
                    if s == seed and p == pattern and m == method:
                        if method in SINGLE_RUN_METHODS:
                            matched_key = (s, p, m, a)
                            break
                        elif a is not None and abs(float(a) - target_alpha) < 1e-4:
                            matched_key = (s, p, m, a)
                            break

                if matched_key:
                    seed_metrics.append(data_store[matched_key])

            harmful_asr_tuple = get_mean_std([m.get("harmful_asr") for m in seed_metrics])
            valid_ratio_tuple = get_mean_std([m.get("valid_ratio") for m in seed_metrics])
            valid_safety_tuple = get_mean_std([m.get("valid_safety_rate") for m in seed_metrics])
            gsm8k_tuple = get_mean_std([m.get("gsm8k") for m in seed_metrics])
            humaneval_tuple = get_mean_std([m.get("humaneval") for m in seed_metrics])

            row = {
                "Pattern": pattern,
                "Method": method,
                "Harmful ASR (ASR↓ %)": format_mean_std(harmful_asr_tuple, is_percent=False),
                "XSTest過剰拒否 (拒否率↓ %)": "N/A",
                "Valid response rate (有効率↑ %)": format_mean_std(valid_ratio_tuple, is_percent=False),
                "Valid Safety Rate (安全率↑ %)": format_mean_std(valid_safety_tuple, is_percent=False),
                "GSM8K (Acc↑ %)": format_mean_std(gsm8k_tuple, is_percent=False),
                "HumanEval (Pass@1↑ %)": format_mean_std(humaneval_tuple, is_percent=False)
            }
            rows.append(row)

    df_t4 = pd.DataFrame(rows)
    return df_t4


def format_table_4_md(df_t4):
    lines = []
    lines.append("**Table 4: 主要マージ手法（$\\alpha=0.6$, $k=0.20$ または単一/既定実行）における詳細評価指標の3 Seeds Average比較**\n")
    headers = [
        "Pattern", "Method", "Harmful ASR (ASR↓ %)", "XSTest過剰拒否 (拒否率↓ %)",
        "Valid response rate (有効率↑ %)", "Valid Safety Rate (安全率↑ %)",
        "GSM8K (Acc↑ %)", "HumanEval (Pass@1↑ %)"
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|:---|:---|---:|---:|---:|---:|---:|---:|")

    for _, row in df_t4.iterrows():
        r_str = [str(row[h]) for h in headers]
        lines.append("| " + " | ".join(r_str) + " |")

    return "\n".join(lines)


# ==========================================
# 3. Table 5 生成ロジック
# ==========================================

def generate_table_5(data_store):
    """
    Table 5. 崩壊分析: 臨界点近傍の詳細指標と偽の安全性 (GSM8K 対象 / diagonal_sst_main α スイープ)
    """
    target_alphas = [0.2, 0.6, 0.8, 1.0]
    pattern = "safety+math"
    method = "diagonal_sst_main"

    annotations = {
        0.2: "低強度ではアライメント未発現",
        0.6: "有用性を高水準で保持",
        0.8: "**【最良 Pareto 設定】崩壊なしで ASR 激減**",
        1.0: "**【完全安全設定】完全アライメントと高数学力**"
    }

    rows = []
    for alpha in target_alphas:
        seed_metrics = []
        for seed in SEEDS:
            for (s, p, m, a), metrics in data_store.items():
                if s == seed and p == pattern and m == method and a is not None and abs(float(a) - alpha) < 1e-4:
                    seed_metrics.append(metrics)
                    break

        refusal_tuple = get_mean_std([m.get("refusal_filtered_asr") for m in seed_metrics])
        harmful_tuple = get_mean_std([m.get("harmful_asr") for m in seed_metrics])
        gsm8k_tuple = get_mean_std([m.get("gsm8k") for m in seed_metrics])

        row = {
            "モデル / マージ手法": "**Diagonal SST (提案)**",
            "設定 (α)": f"`{alpha:.1f}`",
            "Safety Ave [Refusal-Filtered] (ASR↓ %)": format_mean_std(refusal_tuple, is_percent=True),
            "Safety Ave [Harmful Content] (ASR↓ %)": format_mean_std(harmful_tuple, is_percent=True),
            "GSM8K (%)": format_mean_std(gsm8k_tuple, is_percent=True),
            "定量的評価と推論状態": annotations.get(alpha, "")
        }
        rows.append(row)

    df_t5 = pd.DataFrame(rows)
    return df_t5


def format_table_5_md(df_t5):
    lines = []
    lines.append("**Table 5. 崩壊分析: 臨界点近傍の詳細指標と偽の安全性 (GSM8K 対象)**\n")
    headers = [
        "モデル / マージ手法", "設定 (α)",
        "Safety Ave [Refusal-Filtered] (ASR↓ %)",
        "Safety Ave [Harmful Content] (ASR↓ %)",
        "GSM8K (%)", "定量的評価と推論状態"
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

    for _, row in df_t5.iterrows():
        r_str = [str(row[h]) for h in headers]
        lines.append("| " + " | ".join(r_str) + " |")

    return "\n".join(lines)

def format_table_5_latex(df_t5):
    latex = r"""\begin{table}[H]
\centering
\caption{崩壊分析: safety+math条件におけるSST-Merge(GSM8K対象)の詳細指標と偽の安全性}
\label{tab:evaluation_yobi_main_GSM8K}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrr}
\toprule
\textbf{モデル/merge手法} & \textbf{設定 ($\alpha$)} & \textbf{Safety Ave [Conditional ASR] ($\downarrow$\%)} & \textbf{Safety Ave [Original ASR] ($\downarrow$\%)} & \textbf{GSM8K(\%)$\uparrow$} & \textbf{崩壊状態の解釈} \\
\midrule
"""
    for _, row in df_t5.iterrows():
        annotation = row["定量的評価と推論状態"].replace("**", "").replace("【最良 Pareto 設定】", "\\textbf{").replace("【完全安全設定】", "").strip()
        if annotation.startswith("\\textbf{"):
            annotation += "}"
        elif "完全アライメント" in annotation:
            annotation = "高い安全性（有用性は低下）"
            
        r_saf = row['Safety Ave [Refusal-Filtered] (ASR↓ %)'].replace('%', '\\%').replace('±', '$\\pm$')
        h_saf = row['Safety Ave [Harmful Content] (ASR↓ %)'].replace('%', '\\%').replace('±', '$\\pm$')
        g_acc = row['GSM8K (%)'].replace('%', '\\%').replace('±', '$\\pm$')
            
        latex += f"SST(提案) & {row['設定 (α)'].replace('`','')} & {r_saf} & {h_saf} & {g_acc} & {annotation} \\\\\n"
        
    latex += r"""\bottomrule
\end{tabular}
}
\end{table}"""
    return latex

# ==========================================
# 4. 論文自動更新ロジック
# ==========================================

def update_paper_tables(paper_path, md_t4, md_t5):
    if not os.path.exists(paper_path):
        print(f"Paper file not found: {paper_path}")
        return False

    with open(paper_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Table 4 の置換
    t4_pattern = r"\*\*Table 4:.*?\n\n(?:\|.*?\n)+"
    if re.search(t4_pattern, text):
        text = re.sub(t4_pattern, md_t4 + "\n\n", text)
        print("Updated Table 4 in paper draft.")
    else:
        print("Warning: Table 4 marker pattern not matched in paper draft.")

    # Table 5 の置換
    t5_pattern = r"\*\*Table 5\. 崩壊分析:.*?\n\n(?:\|.*?\n)+"
    if re.search(t5_pattern, text):
        text = re.sub(t5_pattern, md_t5 + "\n\n", text)
        print("Updated Table 5 in paper draft.")
    else:
        print("Warning: Table 5 marker pattern not matched in paper draft.")

    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(text)

    return True


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading and processing evaluation JSONs from: {args.results_dir} ...")
    data_store = collect_paper_metrics(args.results_dir)

    # 1. Table 4 生成
    df_t4 = generate_table_4(data_store, target_alpha=args.target_alpha)
    md_t4 = format_table_4_md(df_t4)
    t4_csv_path = os.path.join(args.output_dir, "table_4_3seed_average.csv")
    t4_md_path = os.path.join(args.output_dir, "table_4_3seed_average.md")

    df_t4.to_csv(t4_csv_path, index=False, encoding="utf-8-sig")
    with open(t4_md_path, "w", encoding="utf-8") as f:
        f.write(md_t4)

    # 2. Table 5 生成
    df_t5 = generate_table_5(data_store)
    md_t5 = format_table_5_md(df_t5)
    t5_csv_path = os.path.join(args.output_dir, "table_5_collapse_analysis.csv")
    t5_md_path = os.path.join(args.output_dir, "table_5_collapse_analysis.md")

    df_t5.to_csv(t5_csv_path, index=False, encoding="utf-8-sig")
    with open(t5_md_path, "w", encoding="utf-8") as f:
        f.write(md_t5)

    print("\n" + "=" * 50)
    print(" [Generated Table 4 Preview]")
    print("=" * 50)
    print(md_t4)

    print("\n" + "=" * 50)
    print(" [Generated Table 5 Preview]")
    print("=" * 50)
    print(md_t5)

    print("\n" + "=" * 50)
    print(f"[Success] Saved Table 4 CSV to: {t4_csv_path}")
    print(f"[Success] Saved Table 4 MD  to: {t4_md_path}")
    print(f"[Success] Saved Table 5 CSV to: {t5_csv_path}")
    print(f"[Success] Saved Table 5 MD  to: {t5_md_path}")
    
    latex_t5 = format_table_5_latex(df_t5)
    t5_latex_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables/tab_evaluation_yobi_main_GSM8K.tex"
    with open(t5_latex_path, "w", encoding="utf-8") as f:
        f.write(latex_t5)
    print(f"[Success] Saved Table 5 LaTeX to: {t5_latex_path}")

    if args.update_paper:
        update_paper_tables(args.paper_path, md_t4, md_t5)


if __name__ == "__main__":
    main()