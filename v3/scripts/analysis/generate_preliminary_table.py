#!/usr/bin/env python3
"""
generate_preliminary_tables.py

論文『secure-merge_統一比較評価論文_改訂版.md』の Section 6 に挿入する
「予備実験（TrustLLM および BeaverTails）の結果」の 3-seed Mean ± Std 表を自動生成するスクリプト。

JSON ファイル名に "trustllm" または "beavertails" が含まれるものを対象とします。
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
    parser = argparse.ArgumentParser(description="Generate Preliminary Experiment Table for TrustLLM and BeaverTails.")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results/preliminary/merged",
        help="Path to merged results directory"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="results/preliminary_tables",
        help="Directory to save generated markdown and csv files"
    )
    parser.add_argument(
        "--target_alpha",
        type=float,
        default=0.6,
        help="Target alpha for the preliminary table (default: 0.6)"
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
        help="If set, automatically insert/update the preliminary table in paper_path"
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


def collect_preliminary_metrics(results_dir):
    json_files = glob.glob(os.path.join(results_dir, "**", "*.json"), recursive=True)
    data_store = defaultdict(lambda: defaultdict(dict))

    for filepath in json_files:
        filename = os.path.basename(filepath).lower()
        if "summary" in filename or filename.startswith("."):
            continue
            
        # 予備実験のデータ (TrustLLM or BeaverTails) のみを対象
        if "trustllm" not in filename and "beavertails" not in filename:
            continue

        parts = filename.split("_")

        # Seed
        seed = None
        for p in parts:
            if p.startswith("seed") and p[4:].isdigit():
                seed = int(p[4:])
                break

        # Alpha
        alpha = None
        for p in parts:
            if p.startswith("alpha"):
                try:
                    alpha = float(p.replace("alpha", ""))
                except ValueError:
                    pass

        # Method
        method = "base"
        for m in METHODS:
            if m in filename:
                method = m
                break

        # Pattern
        pattern = "base"
        for pt in PATTERNS:
            if pt in filename:
                pattern = pt
                break

        if seed is None:
            seed = 42

        data = load_json(filepath)
        if not data or data.get("status") == "failed":
            continue

        if "trustllm" in filename:
            # 安全性評価
            asr = data.get("asr", data.get("original_asr"))
            gib_ratio = data.get("gibberish_ratio")
            if asr is not None:
                data_store[(pattern, method, alpha)]["trustllm_asr"] = data_store[(pattern, method, alpha)].get("trustllm_asr", {})
                data_store[(pattern, method, alpha)]["trustllm_asr"][seed] = float(asr) * 100.0 if float(asr) <= 1.0 else float(asr)
            if gib_ratio is not None:
                data_store[(pattern, method, alpha)]["gibberish_ratio"] = data_store[(pattern, method, alpha)].get("gibberish_ratio", {})
                data_store[(pattern, method, alpha)]["gibberish_ratio"][seed] = float(gib_ratio)
        elif "beavertails" in filename:
            # 有用性評価 (スコア構造に合わせて適宜調整)
            utility_score = data.get("similarity", data.get("exact_match", data.get("accuracy")))
            if utility_score is not None:
                data_store[(pattern, method, alpha)]["beavertails_utility"] = data_store[(pattern, method, alpha)].get("beavertails_utility", {})
                data_store[(pattern, method, alpha)]["beavertails_utility"][seed] = float(utility_score) * 100.0 if float(utility_score) <= 1.0 else float(utility_score)

    return data_store


def generate_preliminary_table(data_store, target_alpha):
    rows = []
    for pattern in PATTERNS:
        for method in METHODS:
            # ベースライン手法で alpha 指定がないものは alpha=1.0 または None で検索
            if method in SINGLE_RUN_METHODS:
                # 存在するキーを探す
                found_key = None
                for k in data_store.keys():
                    if k[0] == pattern and k[1] == method:
                        found_key = k
                        break
                key = found_key if found_key else (pattern, method, None)
            else:
                key = (pattern, method, target_alpha)

            entry = data_store.get(key, {})
            
            # TrustLLM Raw ASR
            trust_vals = [entry.get("trustllm_asr", {}).get(s) for s in SEEDS]
            trust_ms = get_mean_std(trust_vals)
            
            # Gibberish Ratio
            gib_vals = [entry.get("gibberish_ratio", {}).get(s) for s in SEEDS]
            gib_ms = get_mean_std(gib_vals)
            
            # BeaverTails Utility
            beaver_vals = [entry.get("beavertails_utility", {}).get(s) for s in SEEDS]
            beaver_ms = get_mean_std(beaver_vals)

            rows.append({
                "Pattern": pattern,
                "Method": method,
                "TrustLLM Raw ASR (%)": format_mean_std(trust_ms),
                "Gibberish Ratio (\(\downarrow\), %)": format_mean_std(gib_ms),
                "BeaverTails Utility Score (\(\uparrow\), %)": format_mean_std(beaver_ms)
            })
            
    df = pd.DataFrame(rows)
    return df


def format_table_md(df):
    headers = ["Pattern", "Method", "TrustLLM Raw ASR (%)", "Gibberish Ratio (\(\downarrow\), %)", "BeaverTails Utility Score (\(\uparrow\), %)"]
    md = "| " + " | ".join(headers) + " |\n"
    md += "|:---|:---" + "|---:" * (len(headers) - 2) + "|\n"
    for _, row in df.iterrows():
        r = [str(row.get(h, "N/A")) for h in headers]
        md += "| " + " | ".join(r) + " |\n"
    return md


def update_paper_tables(paper_path, md_table):
    if not os.path.exists(paper_path):
        print(f"Paper file not found: {paper_path}")
        return False

    with open(paper_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 置換用パターン: "予備実験の結果..." みたいなマーカーがあれば置換する。
    # なければ Section 6.1 の本文の直後に差し込む。
    table_header = "**Table 3b: 予備実験（TrustLLM および BeaverTails）における Safety-Utility トレードオフの 3 Seeds Average 比較**\n\n"
    full_table = table_header + md_table + "\n\n"
    
    # 既存の Table 3b を置換
    t_pattern = r"\*\*Table 3b: 予備実験.*?\n\n(?:\|.*?\n)+"
    if re.search(t_pattern, text):
        text = re.sub(t_pattern, full_table, text)
        print("Updated Preliminary Table in paper draft.")
    else:
        # 新規挿入: "以下に、3つの代表的なマージパターン" の直前、または "より広範かつ最新の安全評価ベンチマークへと拡張して検証を行った。" の直後に挿入
        insert_target = r"(より広範かつ最新の安全評価ベンチマークへと拡張して検証を行った。)(?:\n\n)"
        if re.search(insert_target, text):
            text = re.sub(insert_target, r"\1\n\n" + full_table, text)
            print("Inserted Preliminary Table into paper draft.")
        else:
            print("Warning: Could not find insert location in paper draft. Appending to the end of Section 6.1")

    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(text)

    return True


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading and processing preliminary evaluation JSONs from: {args.results_dir} ...")
    data_store = collect_preliminary_metrics(args.results_dir)

    df_pre = generate_preliminary_table(data_store, target_alpha=args.target_alpha)
    md_pre = format_table_md(df_pre)
    
    csv_path = os.path.join(args.output_dir, "table_preliminary_3seed_average.csv")
    md_path = os.path.join(args.output_dir, "table_preliminary_3seed_average.md")

    df_pre.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_pre)

    print("\n" + "=" * 50)
    print(" [Generated Preliminary Table Preview]")
    print("=" * 50)
    print(md_pre)

    print("\n" + "=" * 50)
    print(f"[Success] Saved Preliminary Table CSV to: {csv_path}")
    print(f"[Success] Saved Preliminary Table MD  to: {md_path}")

    if args.update_paper:
        update_paper_tables(args.paper_path, md_pre)


if __name__ == "__main__":
    main()