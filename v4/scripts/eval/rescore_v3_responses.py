#!/usr/bin/env python3
"""
rescore_v3_responses.py

Rescores existing v3 responses using strict v4 evaluation standards:
1. Strict Non-degeneracy Check (is_response_valid -> VRR)
2. HarmBench label parsing / re-evaluation
3. Computation of ASR_all, ASR_valid, VRR, VSR via compute_secure_merge_metrics
4. Extraction of Math Utility scores (GSM8K, MATH500)

Saves rescored results in v4 schema:
v4/results/eval/e1_rescored/{candidate_id}_safety_eval.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from audit.audit_metrics import compute_secure_merge_metrics
from eval.eval_safety_v4 import is_response_valid, parse_harmbench_label, evaluate_harmfulness_heuristic

SAFETY_BENCHMARKS = [
    "harmbench_safety",
    "jailbreakbench_safety",
    "strongreject_safety",
    "wildjailbreak_safety",
]


def rescore_single_candidate(cand_info: Dict[str, Any], v3_root: Path, judge_mode: str = "auto") -> Dict[str, Any]:
    """Rescores a single candidate's v3 responses."""
    cand_id = cand_info["candidate_id"]
    full_name = cand_info["full_name"]
    domain = cand_info["domain"]
    method = cand_info["method"]
    seed = cand_info["seed"]
    alpha = cand_info["alpha"]
    
    cand_dir = v3_root / "results" / "vllm" / "debug_limit320" / "merged" / f"seed{seed}" / domain / method
    
    benchmark_metrics = {}
    all_is_harmful = []
    all_is_valid = []
    all_responses_detail = []
    
    for bench in SAFETY_BENCHMARKS:
        fpath = cand_dir / f"{full_name}_{bench}.json"
        if not fpath.exists():
            continue
            
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        results = data.get("results", [])
        bench_is_harmful = []
        bench_is_valid = []
        
        for item in results:
            prompt = item.get("prompt", "")
            resp = item.get("response", "")
            
            # 1. Strict v4 Validity
            valid = is_response_valid(resp)
            bench_is_valid.append(valid)
            all_is_valid.append(valid)
            
            # 2. Harmfulness classification
            # If auto or reuse_harmbench_cls, try using existing classifier output if available
            harmful = False
            cls_out = item.get("harmbench_cls_output") or item.get("classifier_output")
            parsed = parse_harmbench_label(cls_out)
            
            if judge_mode in ["auto", "reuse_cls"] and parsed is not None:
                harmful = parsed
            else:
                # Fallback to heuristic
                harmful = evaluate_harmfulness_heuristic(resp, prompt)
                
            bench_is_harmful.append(harmful)
            all_is_harmful.append(harmful)
            
        # Compute metrics for this benchmark
        b_metrics = compute_secure_merge_metrics(bench_is_valid, bench_is_harmful)
        benchmark_metrics[bench] = {
            "n_samples": len(results),
            "asr_all": b_metrics["asr_all"],
            "asr_valid": b_metrics["asr_valid"],
            "vrr": b_metrics["vrr"],
            "vsr": b_metrics["vsr"],
            "n_valid": sum(1 for v in bench_is_valid if v),
            "n_harmful": sum(1 for h in bench_is_harmful if h is True),
        }
        
    # Aggregate over all safety benchmarks
    agg_metrics = compute_secure_merge_metrics(all_is_valid, all_is_harmful)
    
    # Math Utility Extraction
    math_scores = {}
    fpath_math = cand_dir / f"{full_name}_utility_math.json"
    fpath_gsm = cand_dir / f"{full_name}_utility_math_gsm8k.json"
    fpath_math500 = cand_dir / f"{full_name}_utility_math_minerva_math500.json"
    
    # Try GSM8K
    if fpath_gsm.exists():
        with open(fpath_gsm, "r", encoding="utf-8") as f:
            gsm_data = json.load(f)
            res = gsm_data.get("results", {}).get("gsm8k", {})
            math_scores["gsm8k"] = res.get("exact_match,flexible-extract", res.get("exact_match", 0.0))
            
    # Try MATH500
    if fpath_math500.exists():
        with open(fpath_math500, "r", encoding="utf-8") as f:
            m5_data = json.load(f)
            res = m5_data.get("results", {}).get("minerva_math500", {})
            math_scores["math500"] = res.get("exact_match,flexible-extract", res.get("exact_match", 0.0))
            
    # If not found separately, check aggregate file
    if fpath_math.exists() and ("gsm8k" not in math_scores or "math500" not in math_scores):
        with open(fpath_math, "r", encoding="utf-8") as f:
            m_data = json.load(f)
            r_all = m_data.get("results", {})
            if "gsm8k" in r_all and "gsm8k" not in math_scores:
                math_scores["gsm8k"] = r_all["gsm8k"].get("exact_match,flexible-extract", r_all["gsm8k"].get("exact_match", 0.0))
            if "minerva_math500" in r_all and "math500" not in math_scores:
                math_scores["math500"] = r_all["minerva_math500"].get("exact_match,flexible-extract", r_all["minerva_math500"].get("exact_match", 0.0))

    avg_math = (
        (math_scores.get("gsm8k", 0.0) + math_scores.get("math500", 0.0)) / 2.0
        if math_scores else 0.0
    )

    return {
        "candidate_id": cand_id,
        "method": method,
        "alpha": alpha,
        "seed": seed,
        "source": "v3_rescored",
        "judge_mode": judge_mode,
        "safety_aggregate": {
            "total_samples": len(all_is_harmful),
            "asr_all": agg_metrics["asr_all"],
            "asr_valid": agg_metrics["asr_valid"],
            "vrr_harmful": agg_metrics["vrr"],
            "vsr": agg_metrics["vsr"],
            "n_valid": sum(1 for v in all_is_valid if v),
            "n_harmful": sum(1 for h in all_is_harmful if h is True),
        },
        "safety_by_benchmark": benchmark_metrics,
        "utility": {
            "math_gsm8k": math_scores.get("gsm8k", 0.0),
            "math_minerva500": math_scores.get("math500", 0.0),
            "math_average": avg_math,
        },
        "benign": {
            "status": "REQUIRES_GENERATION",
            "vrr_benign": None,
            "overrefusal_rate": None,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Rescore v3 responses using strict v4 standards.")
    parser.add_argument("--manifest", type=str, default="v4/results/audit/v3_reuse_manifest.json")
    parser.add_argument("--v3-root", type=str, default="v3")
    parser.add_argument("--v4-root", type=str, default="v4")
    parser.add_argument("--method", type=str, default="task_arithmetic")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--judge-mode", type=str, default="auto", choices=["auto", "reuse_cls", "heuristic"])
    args = parser.parse_args()

    v3_base = Path(args.v3_root)
    v4_base = Path(args.v4_root)
    
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    out_dir = v4_base / "results" / "eval" / "e1_rescored"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    targets = [
        c for c in manifest["candidates"]
        if c["classification"] == "RESCORE_ONLY"
        and (args.method == "all" or c["method"] == args.method)
        and (args.seed is None or c["seed"] == args.seed)
    ]
    
    print(f"=================================================================")
    print(f" Rescoring {len(targets)} candidates (Method: {args.method}, Seed: {args.seed})")
    print(f"=================================================================\n")
    print(f"| Alpha | Total Samples | ASR_all | ASR_valid | VRR harmful | VSR | GSM8K | MATH500 | Math Avg |")
    print(f"|---|---|---|---|---|---|---|---|---|")
    
    summary_results = []
    
    for cand in sorted(targets, key=lambda x: x["alpha"]):
        rescored = rescore_single_candidate(cand, v3_base, args.judge_mode)
        summary_results.append(rescored)
        
        # Save individual candidate result
        cand_out_file = out_dir / f"{cand['candidate_id']}_rescored.json"
        with open(cand_out_file, "w", encoding="utf-8") as f:
            json.dump(rescored, f, indent=2)
            
        s_agg = rescored["safety_aggregate"]
        u = rescored["utility"]
        print(
            f"| {rescored['alpha']:.1f} | {s_agg['total_samples']} | "
            f"{s_agg['asr_all']*100:.2f}% | {s_agg['asr_valid']*100:.2f}% | "
            f"{s_agg['vrr_harmful']*100:.2f}% | {s_agg['vsr']*100:.2f}% | "
            f"{u['math_gsm8k']*100:.2f}% | {u['math_minerva500']*100:.2f}% | "
            f"{u['math_average']*100:.2f}% |"
        )
        
    summary_file = out_dir / f"rescore_summary_{args.method}_seed{args.seed}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
        
    print(f"\n[Done] Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
