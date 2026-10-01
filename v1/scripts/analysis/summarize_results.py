"""
評価結果を集計してテーブルにまとめるスクリプト

merge_evalフォルダ内の全評価結果を読み込み、
Utility (ROUGE-1) と Safety (Resistance Rate) の比較表を作成
"""

import json
from pathlib import Path
import pandas as pd
import re
from typing import Dict, List, Tuple

#####################################################
# 設定
#####################################################
eval_dir = "../../results/merged/sst_merge"
output_csv = "./merge_eval/summary_results.csv"
#####################################################


def parse_model_name(model_name: str) -> Dict:
    """モデル名を解析してパラメータを抽出
    
    命名規則:
    - SST: A5_A7_sst_a0.5_lw_soft_add, A6_A7_sst_a1.0_nolw_soft_add
    - Baseline: A5_A7_baseline_a0.5
    - 既存手法: A5_A7_ties_a0.5, A6_A7_task_arithmetic_a0.5
    """
    info = {
        "pair": None,
        "method": None,
        "alpha": None,
        "layerwise": None,
    }
    
    # A5_A7 or A6_A7
    if model_name.startswith("A5_A7"):
        info["pair"] = "A5_A7"
    elif model_name.startswith("A6_A7"):
        info["pair"] = "A6_A7"
    
    # Method and alpha
    if "_baseline_" in model_name:
        info["method"] = "baseline"
        # Extract alpha: baseline_a0.5 -> 0.5
        match = re.search(r"_baseline_a([\d.]+)", model_name)
        if match:
            info["alpha"] = float(match.group(1))
    elif "_sst_" in model_name:
        info["method"] = "sst"
        # Extract alpha: sst_a0.5 -> 0.5, sst_a1.0 -> 1.0
        match = re.search(r"_sst_a([\d.]+)", model_name)
        if match:
            info["alpha"] = float(match.group(1))
        # Layer-wise
        info["layerwise"] = "_lw_" in model_name and "_nolw_" not in model_name
    elif "_ties" in model_name:
        info["method"] = "ties"
        # Extract alpha if present: ties_a0.5 or A5_A7_ties_a0.5
        match = re.search(r"_a([\d.]+)", model_name)
        info["alpha"] = float(match.group(1)) if match else 0.5
    elif "_dare" in model_name:
        info["method"] = "dare"
        match = re.search(r"_a([\d.]+)", model_name)
        info["alpha"] = float(match.group(1)) if match else 0.5
    elif "_task_arithmetic" in model_name:
        info["method"] = "task_arithmetic"
        match = re.search(r"_a([\d.]+)", model_name)
        info["alpha"] = float(match.group(1)) if match else 0.5
    
    return info


def load_eval_results(eval_dir: str) -> List[Dict]:
    """評価結果を読み込む"""
    results = []
    eval_path = Path(eval_dir)
    
    for json_file in eval_path.glob("*.json"):
        if json_file.name == "summary_results.json":
            continue
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filename = json_file.stem
        
        # Determine eval type
        if "_repliqa_eval" in filename:
            eval_type = "repliqa"
            model_name = filename.replace("_repliqa_eval_results", "")
        elif "_alpaca_eval" in filename:
            eval_type = "alpaca"
            model_name = filename.replace("_alpaca_eval_results", "")
        elif "_jailbreak_eval" in filename:
            eval_type = "jailbreak"
            model_name = filename.replace("_jailbreak_eval_results", "")
        else:
            continue
        
        # Parse model info
        info = parse_model_name(model_name)
        
        result = {
            "model_name": model_name,
            "pair": info["pair"],
            "method": info["method"],
            "alpha": info["alpha"],
            "layerwise": info["layerwise"],
            "eval_type": eval_type,
        }
        
        # Extract metrics
        if eval_type in ["repliqa", "alpaca"]:
            if "metrics" in data:
                result["rouge1"] = data["metrics"]["rouge1"]["mean"]
                result["rouge2"] = data["metrics"]["rouge2"]["mean"]
                result["rougeL"] = data["metrics"]["rougeL"]["mean"]
        elif eval_type == "jailbreak":
            result["resistance_rate"] = data.get("resistance_rate", None)
            result["attack_success_rate"] = data.get("attack_success_rate", None)
        
        results.append(result)
    
    return results


def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    """結果をサマリーテーブルにまとめる"""
    # Group by model and merge utility/jailbreak results
    model_results = {}
    
    for r in results:
        model_name = r["model_name"]
        if model_name not in model_results:
            model_results[model_name] = {
                "pair": r["pair"],
                "method": r["method"],
                "alpha": r["alpha"],
                "layerwise": r["layerwise"],
            }
        
        if r["eval_type"] in ["repliqa", "alpaca"]:
            model_results[model_name]["utility_type"] = r["eval_type"]
            model_results[model_name]["rouge1"] = r.get("rouge1")
            model_results[model_name]["rouge2"] = r.get("rouge2")
            model_results[model_name]["rougeL"] = r.get("rougeL")
        elif r["eval_type"] == "jailbreak":
            model_results[model_name]["resistance_rate"] = r.get("resistance_rate")
    
    # Convert to DataFrame
    rows = []
    for model_name, data in model_results.items():
        rows.append({
            "model": model_name,
            "pair": data.get("pair"),
            "method": data.get("method"),
            "alpha": data.get("alpha"),
            "layerwise": data.get("layerwise"),
            "utility_type": data.get("utility_type"),
            "ROUGE-1": data.get("rouge1"),
            "ROUGE-2": data.get("rouge2"),
            "ROUGE-L": data.get("rougeL"),
            "Safety (Resistance)": data.get("resistance_rate"),
        })
    
    df = pd.DataFrame(rows)
    
    # Sort by pair, method, alpha
    df = df.sort_values(["pair", "method", "alpha"], na_position='last')
    
    return df


def main():
    print("="*70)
    print("Summarizing Evaluation Results")
    print("="*70)
    
    results = load_eval_results(eval_dir)
    print(f"Loaded {len(results)} evaluation results")
    
    df = create_summary_table(results)
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"\nSaved summary to: {output_csv}")
    
    # Print tables by pair
    for pair in ["A5_A7", "A6_A7"]:
        print(f"\n{'='*70}")
        print(f"{pair} Results")
        print("="*70)
        
        pair_df = df[df["pair"] == pair].copy()
        if len(pair_df) == 0:
            print("No results found")
            continue
        
        # Format for display
        display_df = pair_df[["method", "alpha", "ROUGE-1", "Safety (Resistance)"]].copy()
        display_df["ROUGE-1"] = display_df["ROUGE-1"].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
        display_df["Safety (Resistance)"] = display_df["Safety (Resistance)"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
        
        print(display_df.to_string(index=False))
    
    # Comparison summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    for pair in ["A5_A7", "A6_A7"]:
        pair_df = df[df["pair"] == pair].copy()
        if len(pair_df) == 0:
            continue
        
        print(f"\n{pair}:")
        
        # Baseline best
        baseline_df = pair_df[pair_df["method"] == "baseline"]
        if len(baseline_df) > 0:
            best_utility_idx = baseline_df["ROUGE-1"].idxmax()
            best_safety_idx = baseline_df["Safety (Resistance)"].idxmax()
            print(f"  Baseline - Best Utility (α={baseline_df.loc[best_utility_idx, 'alpha']}): ROUGE-1={baseline_df.loc[best_utility_idx, 'ROUGE-1']:.4f}, Safety={baseline_df.loc[best_utility_idx, 'Safety (Resistance)']:.1%}")
            print(f"  Baseline - Best Safety (α={baseline_df.loc[best_safety_idx, 'alpha']}): ROUGE-1={baseline_df.loc[best_safety_idx, 'ROUGE-1']:.4f}, Safety={baseline_df.loc[best_safety_idx, 'Safety (Resistance)']:.1%}")
        
        # SST best
        sst_df = pair_df[pair_df["method"] == "sst"]
        if len(sst_df) > 0:
            best_utility_idx = sst_df["ROUGE-1"].idxmax()
            best_safety_idx = sst_df["Safety (Resistance)"].idxmax()
            print(f"  SST      - Best Utility (α={sst_df.loc[best_utility_idx, 'alpha']}): ROUGE-1={sst_df.loc[best_utility_idx, 'ROUGE-1']:.4f}, Safety={sst_df.loc[best_utility_idx, 'Safety (Resistance)']:.1%}")
            print(f"  SST      - Best Safety (α={sst_df.loc[best_safety_idx, 'alpha']}): ROUGE-1={sst_df.loc[best_safety_idx, 'ROUGE-1']:.4f}, Safety={sst_df.loc[best_safety_idx, 'Safety (Resistance)']:.1%}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
