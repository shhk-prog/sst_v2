#!/usr/bin/env python3
"""
run_human_audit_sampling.py

Extracts 200 double-blind samples (150 random + 50 hard cases) from v3 responses
for human validity inspection according to Secure_Merge_Experiment_Plan.md Section 5.2.
"""

import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from audit.human_audit_sampler import sample_human_audit_set

def main():
    v3_base = Path("v3/results/vllm/debug_limit320/merged/seed42/safety+math")
    output_dir = "v4/results/eval/human_audit"
    
    # Collect items across representive methods
    representative_methods = ["task_arithmetic", "ties", "dare", "della", "led_merging", "safemerge", "diagonal_sst_main"]
    all_responses = []

    for m in representative_methods:
        m_dir = v3_base / m
        if not m_dir.exists():
            continue
        for fname in os.listdir(m_dir):
            if fname.endswith("harmbench_safety.json") or fname.endswith("strongreject_safety.json"):
                fpath = m_dir / fname
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    res_list = d.get("results", [])
                    for r in res_list:
                        item = dict(r)
                        item["source_method"] = m
                        item["source_file"] = fname
                        all_responses.append(item)
                except Exception:
                    pass

    print(f"Total responses collected from representative methods: {len(all_responses)}")
    paths = sample_human_audit_set(
        eval_results_list=all_responses,
        output_dir=output_dir,
        random_seed=42,
        n_random=150,
        n_hard=50,
    )
    print("\n[Done] Human audit sample sets created:")
    for k, v in paths.items():
        print(f"  - {k}: {v}")

if __name__ == "__main__":
    main()
