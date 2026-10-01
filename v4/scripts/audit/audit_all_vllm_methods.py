#!/usr/bin/env python3
"""
audit_all_vllm_methods.py

Quickly inspects all merge methods and domains available under v3/results/vllm/
and audits their reusability for v4.
"""

import os
from pathlib import Path

def main():
    vllm_base = Path("v3/results/vllm/debug_limit320/merged")
    if not vllm_base.exists():
        print(f"Directory not found: {vllm_base}")
        return

    seeds = sorted([d for d in os.listdir(vllm_base) if (vllm_base / d).is_dir()])
    print(f"Seeds found in vllm/debug_limit320/merged: {seeds}")

    # Inspect each seed and domain
    records = {}

    for s in seeds:
        s_dir = vllm_base / s
        domains = sorted([d for d in os.listdir(s_dir) if (s_dir / d).is_dir()])
        for dom in domains:
            dom_dir = s_dir / dom
            methods = sorted([m for m in os.listdir(dom_dir) if (dom_dir / m).is_dir()])
            for m in methods:
                m_dir = dom_dir / m
                # Count files
                try:
                    files = [f for f in os.listdir(m_dir) if f.endswith(".json")]
                except Exception:
                    files = []
                key = (dom, m)
                if key not in records:
                    records[key] = {}
                records[key][s] = len(files)

    print("\n=================================================================")
    print(" Complete Inventory of Merge Methods in v3/results/vllm/")
    print("=================================================================")
    print("| Domain | Method Name | Seeds with Results | File Count per Seed |")
    print("|---|---|---|---|")

    for (dom, m), seed_data in sorted(records.items()):
        seeds_present = [s for s, count in sorted(seed_data.items()) if count > 0]
        details = ", ".join([f"{s}:{seed_data[s]}" for s in seeds_present])
        print(f"| {dom} | {m} | {', '.join(seeds_present)} | {details} |")

    # Also inspect model weights under v3/models/merged
    model_base = Path("v3/models/merged")
    if model_base.exists():
        print("\n=================================================================")
        print(" Model Weights Inventory in v3/models/merged/")
        print("=================================================================")
        try:
            model_dirs = sorted([d for d in os.listdir(model_base) if (model_base / d).is_dir()])
            print(f"Total merged model directories found: {len(model_dirs)}")
            
            # Group model dirs by method pattern
            method_patterns = [
                "task_arithmetic", "ties", "dare", "della", "safemerge",
                "led_merging", "matena_fisher", "mergealign",
                "data_free_sst", "diagonal_sst", "ablation"
            ]
            
            for pat in method_patterns:
                matching = [d for d in model_dirs if pat in d]
                math_matching = [d for d in matching if "safety+math" in d]
                print(f"- {pat}: {len(matching)} total models (safety+math: {len(math_matching)})")
        except Exception as e:
            print(f"Error inspecting model_base: {e}")

if __name__ == "__main__":
    main()
