#!/usr/bin/env python3
"""
v3_reuse_audit.py

v3 Asset Reuse Auditor for v4 Production Experiments
According to Secure_Merge_Experiment_Plan.md & v4 Transition Protocol.

Taxonomy of Reusability:
- FULL_REUSE: Canonical checkpoint matches AND response provenance matches AND all evaluations complete.
- RESCORE_ONLY: Raw responses exist and are high quality, but require v4 re-evaluation
                (HarmBench classifier, strict validity check, ASR_valid, VSR calculation).
- DIAGNOSTIC_ONLY: Incompatible architectures (e.g. WizardCoder RoPE mismatch), non-equivalent tokenizers,
                   or legacy merge bugs. Kept strictly for ablation/exploratory reference.
- REGENERATE: Missing responses, unknown seeds/prompts, or missing evaluation dimensions (e.g. Benign Over-refusal).

Outputs:
- v4/results/audit/v3_reuse_manifest.json
- Printed markdown summary audit table
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SAFETY_BENCHMARKS = [
    "harmbench_safety",
    "jailbreakbench_safety",
    "strongreject_safety",
    "wildjailbreak_safety",
]

MATH_UTILITY_BENCHMARKS = [
    "utility_math",
    "utility_math_gsm8k",
    "utility_math_minerva_math500",
]

REQUIRED_SAFETY_COUNTS = {
    "harmbench_safety": 320,
    "jailbreakbench_safety": 100,
    "strongreject_safety": 313,
    "wildjailbreak_safety": 320,
}


def audit_safety_json(filepath: Path) -> Dict[str, Any]:
    """Inspects a safety evaluation JSON file and validates response presence."""
    if not filepath.exists():
        return {"exists": False, "valid": False, "count": 0, "reason": "file_not_found"}
    
    # Fast check: file size must be reasonable (> 1KB)
    fsize = filepath.stat().st_size
    if fsize < 100:
        return {"exists": True, "valid": False, "count": 0, "reason": "file_too_small"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        results = data.get("results", [])
        if not isinstance(results, list) or len(results) == 0:
            return {"exists": True, "valid": False, "count": 0, "reason": "empty_or_invalid_results"}
        
        sample = results[0]
        if "prompt" not in sample or "response" not in sample:
            return {"exists": True, "valid": False, "count": len(results), "reason": "missing_prompt_or_response_field"}
        
        return {
            "exists": True,
            "valid": True,
            "count": len(results),
            "size_bytes": fsize,
            "has_harmbench_cls_output": "harmbench_cls_output" in sample or "classifier_output" in sample,
        }
    except Exception as e:
        return {"exists": True, "valid": False, "count": 0, "reason": f"json_parse_error: {str(e)}"}


def audit_utility_json(filepath: Path) -> Dict[str, Any]:
    """Inspects a math utility JSON file and checks validity."""
    if not filepath.exists():
        return {"exists": False, "valid": False, "samples_count": 0, "score": None}
    
    fsize = filepath.stat().st_size
    if fsize < 100:
        return {"exists": True, "valid": False, "samples_count": 0, "reason": "file_too_small"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        results = data.get("results", {})
        has_samples = "samples" in data and data["samples"] is not None
        
        return {
            "exists": True,
            "valid": True,
            "size_bytes": fsize,
            "has_aggregate_results": bool(results),
            "has_sample_level_logs": has_samples,
            "results_summary": results,
        }
    except Exception as e:
        return {"exists": True, "valid": False, "reason": f"json_parse_error: {str(e)}"}


def inspect_candidate(
    v3_base_dir: Path,
    seed: int,
    domain: str,
    method: str,
    alpha: float,
) -> Dict[str, Any]:
    """Audits a single candidate merge configuration."""
    alpha_str = f"{alpha:.1f}" if alpha in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] else str(alpha)
    cand_name = f"sst_merge_v3_main_{method}_{domain}_alpha{alpha_str}_seed{seed}"
    cand_dir = v3_base_dir / "results" / "vllm" / "debug_limit320" / "merged" / f"seed{seed}" / domain / method
    
    # Checkpoint path check
    model_dir = v3_base_dir / "models" / "merged" / cand_name
    model_exists = model_dir.exists() and (model_dir / "config.json").exists()

    safety_audits = {}
    total_safety_responses = 0
    all_safety_complete = True
    
    for bench in SAFETY_BENCHMARKS:
        fpath = cand_dir / f"{cand_name}_{bench}.json"
        audit_res = audit_safety_json(fpath)
        safety_audits[bench] = audit_res
        if audit_res.get("valid"):
            total_safety_responses += audit_res.get("count", 0)
            req = REQUIRED_SAFETY_COUNTS.get(bench, 0)
            if audit_res.get("count", 0) < req:
                all_safety_complete = False
        else:
            all_safety_complete = False

    # Math utility check
    math_audits = {}
    fpath_math = cand_dir / f"{cand_name}_utility_math.json"
    fpath_gsm = cand_dir / f"{cand_name}_utility_math_gsm8k.json"
    fpath_math500 = cand_dir / f"{cand_name}_utility_math_minerva_math500.json"
    
    math_audits["utility_math"] = audit_utility_json(fpath_math)
    math_audits["gsm8k"] = audit_utility_json(fpath_gsm)
    math_audits["math500"] = audit_utility_json(fpath_math500)
    
    has_math_utility = (
        math_audits["utility_math"].get("valid")
        or (math_audits["gsm8k"].get("valid") and math_audits["math500"].get("valid"))
    )

    # Benign / Over-refusal check (in v3 this was mostly absent or in alpaca_eval2)
    fpath_alpaca = cand_dir / f"{cand_name}_alpaca_eval2.json"
    has_benign = fpath_alpaca.exists()  # AlpacaEval is not XSTest-based over-refusal, so needs regeneration

    # Determine classification
    # Rule:
    # 1. WizardCoder -> DIAGNOSTIC_ONLY (RoPE mismatch)
    # 2. Linear (task_arithmetic) math with full responses -> RESCORE_ONLY (checkpoint equivalence tested separately)
    # 3. Missing responses -> REGENERATE
    
    actions = []
    if "code" in domain:
        classification = "DIAGNOSTIC_ONLY"
        reason = "WizardCoder RoPE mismatch (theta=1M vs 10k) - excluded from primary"
    elif all_safety_complete and has_math_utility:
        # We have responses, but v3 aggregate ASR/VRR needs strict v4 rescoring
        classification = "RESCORE_ONLY"
        actions.append("rescore_safety_harmbench_classifier")
        actions.append("recompute_strict_validity_and_vrr")
        actions.append("generate_benign_overrefusal_xstest")
        if not model_exists:
            actions.append("v4_canonical_remerge_if_checkpoint_needed")
        reason = f"Full safety ({total_safety_responses} responses) and math utility present. Requires v4 rescoring + benign generation."
    elif total_safety_responses > 0:
        classification = "PARTIAL_RESCORE"
        actions.append("rescore_available_responses")
        actions.append("regenerate_missing_benchmarks")
        reason = f"Partial responses ({total_safety_responses}) available."
    else:
        classification = "REGENERATE"
        actions.append("full_generation_v4")
        reason = "No valid v3 responses found."

    return {
        "candidate_id": f"math_{method}_a{alpha_str}_seed{seed}",
        "full_name": cand_name,
        "domain": domain,
        "method": method,
        "alpha": alpha,
        "seed": seed,
        "classification": classification,
        "classification_reason": reason,
        "checkpoint_exists": model_exists,
        "checkpoint_path": str(model_dir) if model_exists else None,
        "safety_evaluations": safety_audits,
        "math_evaluations": math_audits,
        "has_benign_eval": has_benign,
        "required_actions": actions,
    }


def run_audit(v3_root: str, v4_root: str, output_path: Optional[str] = None, filter_methods: Optional[List[str]] = None):
    v3_base = Path(v3_root)
    v4_base = Path(v4_root)
    
    print(f"=================================================================", flush=True)
    print(f" [v4 Transition] v3 Asset Reuse Audit for Production E1", flush=True)
    print(f" Source v3 Directory: {v3_base}", flush=True)
    print(f" Target v4 Directory: {v4_base}", flush=True)
    print(f"=================================================================\n", flush=True)
    
    seeds = [42, 43, 44]
    alphas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    
    all_methods = [
        ("task_arithmetic", "safety+math", "Primary (Linear Safety-Patch)"),
        ("ties", "safety+math", "Baseline (TIES-Merging)"),
        ("dare", "safety+math", "Baseline (DARE-Merging)"),
        ("della", "safety+math", "Baseline (DELLA-Merging)"),
        ("task_arithmetic", "safety+code", "Diagnostic Only (WizardCoder)"),
    ]
    
    if filter_methods:
        methods_to_audit = [m for m in all_methods if m[0] in filter_methods]
    else:
        methods_to_audit = all_methods
    
    all_manifests = []
    
    print(f"| Candidate ID | Method | Domain | Seed | Checkpoint | Safety Resps | Math Util | Classification |", flush=True)
    print(f"|---|---|---|---|---|---|---|---|", flush=True)
    
    for method, domain, label in methods_to_audit:
        for seed in seeds:
            for alpha in alphas:
                info = inspect_candidate(v3_base, seed, domain, method, alpha)
                all_manifests.append(info)
                
                # Count total safety responses
                n_safety = sum(s.get("count", 0) for s in info["safety_evaluations"].values() if s.get("valid"))
                math_ok = "YES" if (info["math_evaluations"]["utility_math"].get("valid") or info["math_evaluations"]["gsm8k"].get("valid")) else "NO"
                ckpt_ok = "YES" if info["checkpoint_exists"] else "NO"
                
                print(f"| {info['candidate_id']} | {method} | {domain} | {seed} | {ckpt_ok} | {n_safety}/1053 | {math_ok} | **{info['classification']}** |", flush=True)
    
    # Summary statistics
    counts = {}
    for m in all_manifests:
        c = m["classification"]
        counts[c] = counts.get(c, 0) + 1
        
    print(f"\n=================================================================", flush=True)
    print(f" Audit Summary by Classification:", flush=True)
    for c, cnt in counts.items():
        print(f"  - {c}: {cnt} candidates", flush=True)
    print(f"=================================================================\n", flush=True)
    
    # Save manifest
    if output_path is None:
        out_dir = v4_base / "results" / "audit"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / "v3_reuse_manifest.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "v4_v3_reuse_manifest_v1",
            "total_candidates_audited": len(all_manifests),
            "summary_counts": counts,
            "candidates": all_manifests,
        }, f, indent=2, ensure_ascii=False)
        
    print(f"[Done] Reusability Manifest saved to: {output_path}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit v3 assets for v4 reuse.")
    parser.add_argument("--v3-root", type=str, default="v3", help="Root directory of v3")
    parser.add_argument("--v4-root", type=str, default="v4", help="Root directory of v4")
    parser.add_argument("--methods", type=str, nargs="+", default=None, help="Filter methods (e.g. task_arithmetic ties)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()
    
    run_audit(args.v3_root, args.v4_root, args.output, args.methods)
