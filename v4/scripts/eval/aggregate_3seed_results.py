#!/usr/bin/env python3
"""
aggregate_3seed_results.py

Aggregates 3-seed rescored results for Math Production E1 candidates.
Computes Mean ± Std for ASR_all, ASR_valid, VRR harmful, VSR, and GSM8K.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

def main():
    seeds = [42, 43, 44]
    alphas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    methods = ["task_arithmetic", "ties", "dare", "della"]
    base_dir = Path("v4/results/eval/e1_rescored")

    for method in ["task_arithmetic"]:
        print(f"\n=================================================================")
        print(f" 3-Seed Aggregate Performance Table: {method} (Linear Safety-Patch)")
        print(f"=================================================================")
        print("| Alpha | ASR_all (mean±std) | ASR_valid (mean±std) | VRR harmful (mean±std) | VSR (mean±std) | GSM8K (mean±std) |")
        print("|---|---|---|---|---|---|")

        table_data = []
        for a in alphas:
            asrs_all = []
            asrs_valid = []
            vrrs = []
            vsrs = []
            gsm8ks = []
            
            for s in seeds:
                path = base_dir / f"rescore_summary_{method}_seed{s}.json"
                if not path.exists():
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                matched = [d for d in data if abs(d["alpha"] - a) < 1e-5]
                if not matched:
                    continue
                item = matched[0]
                asrs_all.append(item["safety_aggregate"]["asr_all"] * 100)
                asrs_valid.append(item["safety_aggregate"]["asr_valid"] * 100)
                vrrs.append(item["safety_aggregate"]["vrr_harmful"] * 100)
                vsrs.append(item["safety_aggregate"]["vsr"] * 100)
                gsm8ks.append(item["utility"]["math_gsm8k"] * 100)
                
            row = {
                "alpha": a,
                "asr_all_mean": float(np.mean(asrs_all)),
                "asr_all_std": float(np.std(asrs_all)),
                "asr_valid_mean": float(np.mean(asrs_valid)),
                "asr_valid_std": float(np.std(asrs_valid)),
                "vrr_mean": float(np.mean(vrrs)),
                "vrr_std": float(np.std(vrrs)),
                "vsr_mean": float(np.mean(vsrs)),
                "vsr_std": float(np.std(vsrs)),
                "gsm8k_mean": float(np.mean(gsm8ks)),
                "gsm8k_std": float(np.std(gsm8ks)),
            }
            table_data.append(row)
            print(
                f"| {a:.1f} | {row['asr_all_mean']:.2f} ± {row['asr_all_std']:.2f}% | "
                f"{row['asr_valid_mean']:.2f} ± {row['asr_valid_std']:.2f}% | "
                f"{row['vrr_mean']:.2f} ± {row['vrr_std']:.2f}% | "
                f"{row['vsr_mean']:.2f} ± {row['vsr_std']:.2f}% | "
                f"{row['gsm8k_mean']:.2f} ± {row['gsm8k_std']:.2f}% |"
            )

        out_summary = base_dir / f"3seed_aggregate_{method}.json"
        with open(out_summary, "w", encoding="utf-8") as f:
            json.dump(table_data, f, indent=2)
        print(f"\n[Saved] Aggregate table saved to: {out_summary}")

if __name__ == "__main__":
    main()
