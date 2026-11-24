"""
Inspect available metrics and results across all benchmark files for a representative candidate.
"""
import os
import json
from pathlib import Path

def main():
    p = Path("v3/results/vllm/debug_limit320/merged/seed42/safety+math/task_arithmetic")
    
    files_to_check = [
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_harmbench_safety.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_jailbreakbench_safety.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_strongreject_safety.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_wildjailbreak_safety.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_utility_math_gsm8k.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_utility_math_minerva_math500.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_utility_general_ifeval.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_utility_general_mmlu.json",
        "sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed42_alpaca_eval2.json"
    ]
    
    for fname in files_to_check:
        fpath = p / fname
        print(f"\n==================== {fname} ====================")
        if not fpath.exists():
            print("NOT FOUND")
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        
        if isinstance(d, dict):
            print("Top-level keys:", list(d.keys()))
            if "results" in d and isinstance(d["results"], dict):
                for k, v in d["results"].items():
                    if isinstance(v, dict):
                        print(f"  results['{k}'] numeric fields:")
                        for metric_name, val in v.items():
                            if isinstance(val, (int, float)):
                                print(f"    {metric_name}: {val}")
            elif "results" in d and isinstance(d["results"], list):
                print(f"  results list length: {len(d['results'])}")
                if len(d["results"]) > 0 and isinstance(d["results"][0], dict):
                    print("  sample result item keys:", list(d["results"][0].keys()))
            if "metrics" in d:
                print("  metrics:", d["metrics"])
            if "summary" in d:
                print("  summary:", d["summary"])

if __name__ == "__main__":
    main()
