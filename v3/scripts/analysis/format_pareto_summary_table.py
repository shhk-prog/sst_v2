#!/usr/bin/env python3
"""
format_pareto_summary_table.py

pareto_auc.py で出力された各タスク別の Pareto AUC 集計 CSV ファイル群から、
全タスク横断の比較まとめ表 (Markdown & CSV) を自動生成するスクリプト。
"""

import os
import sys
import glob
import argparse
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(description="Format multi-task Pareto AUC summary table.")
    parser.add_argument(
        "--pareto_dir",
        type=str,
        required=True,
        help="Directory containing pareto_metrics_summary_*.csv files"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Path to save the generated summary markdown table"
    )
    return parser.parse_args()


def generate_pareto_task_summary(pareto_dir, output_file=None):
    if not os.path.exists(pareto_dir):
        print(f"Error: Directory {pareto_dir} does not exist.")
        return

    csv_files = glob.glob(os.path.join(pareto_dir, "pareto_metrics_summary_*.csv"))
    if not csv_files:
        print(f"Error: No pareto_metrics_summary_*.csv files found in {pareto_dir}.")
        return

    task_data = {}
    methods_set = set()

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        # Parse task name from filename (e.g., pareto_metrics_summary_harmbench_safety+math+code+medical.csv)
        base_str = filename.replace("pareto_metrics_summary_", "").replace(".csv", "")
        parts = base_str.split("_")
        task_name = parts[0]  # harmbench, jailbreakbench, strongreject, wildjailbreak, average

        try:
            df = pd.read_csv(csv_path)
            if "Method" in df.columns and "Pareto AUC (mean)" in df.columns:
                for _, row in df.iterrows():
                    method = str(row["Method"])
                    auc = float(row["Pareto AUC (mean)"])
                    methods_set.add(method)
                    if method not in task_data:
                        task_data[method] = {}
                    task_data[method][task_name] = auc
        except Exception as e:
            print(f"Warning: Failed to read {csv_path}: {e}")

    if not task_data:
        print("Error: No valid Pareto AUC records could be extracted.")
        return

    # Define task column order
    ordered_tasks = ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak", "average"]
    present_tasks = [t for t in ordered_tasks if any(t in task_data[m] for m in task_data)]
    
    # Add any extra tasks if present
    for m in task_data:
        for t in task_data[m]:
            if t not in present_tasks:
                present_tasks.append(t)

    records = []
    sorted_methods = sorted(list(methods_set))

    # Priority sorting for methods
    method_order = [
        "diagonal_sst", "data_free_sst", "ties", "task_arithmetic",
        "dare", "della", "safemerge", "led_merging", "matena_fisher", "mergealign"
    ]
    sorted_methods.sort(key=lambda x: method_order.index(x) if x in method_order else 99)

    for method in sorted_methods:
        row_dict = {"Method": method}
        for task in present_tasks:
            val = task_data[method].get(task, None)
            row_dict[task] = f"{val:.4f}" if val is not None else "N/A"
        records.append(row_dict)

    df_result = pd.DataFrame(records)

    # Display columns renaming for cleaner markdown
    rename_cols = {
        "harmbench": "HarmBench AUC",
        "jailbreakbench": "JailbreakBench AUC",
        "strongreject": "StrongReject AUC",
        "wildjailbreak": "WildJailbreak AUC",
        "average": "Average AUC"
    }
    df_result = df_result.rename(columns=rename_cols)

    md_table = df_result.to_markdown(index=False)
    print("\n=== Multi-Task Pareto AUC Summary Table ===")
    print(md_table)
    print("\n")

    if output_file is None:
        output_file = os.path.join(pareto_dir, "pareto_auc_task_summary.md")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 多次元 Pareto AUC タスク別横断比較表\n\n")
        f.write(f"ディレクトリ: `{pareto_dir}`\n\n")
        f.write(md_table)
        f.write("\n")

    csv_output = output_file.replace(".md", ".csv")
    df_result.to_csv(csv_output, index=False)

    print(f"Saved Pareto summary markdown to: {output_file}")
    print(f"Saved Pareto summary CSV to: {csv_output}")


def main():
    args = parse_args()
    generate_pareto_task_summary(args.pareto_dir, args.output_file)


if __name__ == "__main__":
    main()