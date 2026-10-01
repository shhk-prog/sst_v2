"""
Analysis: reaggregate_v3_logs.py (Rigorous Diagnostic Track - P0/P1 Fully Remediated)
Scans real empirical evaluation JSONs from v3/results/.

Strict Rules Adhered (Plan & Audit Report):
1. Zero Metric Invention:
   - NO mock/synthetic numbers (e.g. overrefusal=0.04, vrr_benign=vrr_harmful).
   - If benign VRR or over-refusal was not measured for a candidate, it is strictly None (null).
   - Missing utility is strictly None (null) and flagged as INSUFFICIENT_DATA.
2. Candidate Key Normalization & Exact Pairing:
   - Removes task suffixes (e.g. _utility_math_gsm8k, _harmbench_safety) from model paths
     so that safety, validity, and utility results for the EXACT SAME merged checkpoint bind to one Candidate ID.
3. Method Taxonomy:
   - Excludes 'unknown' completely from primary baseline analysis.
   - Labels v3 'task_arithmetic' as 'legacy_task_arithmetic_linear_patch' (since v3 executed linear interpolation).
   - Separates 'diagonal_sst' and 'data_free_sst' into 'exploratory_sst_track' (NOT mixed with standard baselines).
4. Full Provenance Record:
   - For every candidate, preserves exact source file paths, task counts, judge details, and metric keys.
"""

import os
import sys
import glob
import re
import json
import math
from typing import Dict, Any, List, Optional, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from eval.eval_safety_v4 import is_response_valid
from audit.audit_metrics import compute_secure_merge_metrics


def clean_candidate_model_id(raw_model_str: str) -> str:
    """
    Strips task suffixes and directory prefixes to obtain the unique underlying model/checkpoint key.
    """
    basename = os.path.basename(raw_model_str.rstrip("/"))
    # Remove task suffixes
    task_patterns = [
        r"_utility_.*$",
        r"_harmbench.*$",
        r"_jailbreakbench.*$",
        r"_strongreject.*$",
        r"_wildjailbreak.*$",
        r"_alpaca_eval.*$",
        r"_inst_.*$",
    ]
    cleaned = basename
    for p in task_patterns:
        cleaned = re.sub(p, "", cleaned)
    return cleaned


def extract_utility_metric_from_dict(res_dict: Dict[str, Any]) -> Tuple[Optional[float], Optional[str], Optional[int]]:
    """
    Extracts normalized utility metric (0.0 to 1.0) strictly from vetted benchmark schemas (R2-06).
    Never falls back to arbitrary numerical metadata (e.g. sample_len).
    """
    VETTED_UTILITY_METRIC_KEYS = [
        "exact_match,flexible-extract",
        "math_verify,none",
        "pass@1",
        "pass_at_1",
        "acc,none",
        "acc",
        "exact_match",
        "prompt_level_strict_acc,none",
    ]

    for subtask_name, metrics in res_dict.items():
        if not isinstance(metrics, dict):
            continue
        sample_len = metrics.get("sample_len", metrics.get("n", None))

        for key in VETTED_UTILITY_METRIC_KEYS:
            if key in metrics and metrics[key] is not None:
                try:
                    val = float(metrics[key])
                    # Strictly check finite and reasonable probability / ratio range [0.0, 1.0]
                    if math.isfinite(val) and 0.0 <= val <= 1.0:
                        return val, f"{subtask_name}:{key}", sample_len
                except (ValueError, TypeError):
                    continue

    return None, None, None


def parse_v3_result_file(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    # Adapt both v3 schemas and v4 unified evaluation outputs (model_path/task_name/sample_results)
    raw_results = data.get("sample_results") if data.get("sample_results") is not None else data.get("results")
    model_name = data.get("model") or data.get("model_path", "")
    task_name = data.get("task") or data.get("task_name", "")

    # Direct v4 safety output with precomputed metrics
    if "metrics" in data and isinstance(data["metrics"], dict) and ("asr_all" in data["metrics"] or "vrr" in data["metrics"]):
        metrics = data["metrics"]
        n_unjudged = sum(1 for r in raw_results if r.get("is_harmful") is None) if isinstance(raw_results, list) else 0
        return {
            "type": "safety",
            "task": task_name or "v4_safety",
            "model": model_name,
            "file": file_path,
            "n_samples": data.get("n_samples", len(raw_results) if isinstance(raw_results, list) else 0),
            "n_unjudged": n_unjudged,
            "classifier_info": data.get("judge_backend", "v4_classifier"),
            "metrics": metrics,
        }

    # Direct v4 utility output with accuracy or pass_at_1
    if "accuracy" in data or "pass_at_1" in data:
        score = data.get("accuracy") if data.get("accuracy") is not None else data.get("pass_at_1")
        if score is not None:
            return {
                "type": "utility",
                "task": task_name or "v4_utility",
                "model": model_name,
                "file": file_path,
                "n_samples": data.get("n_samples", 0),
                "metric_name": "accuracy" if "accuracy" in data else "pass_at_1",
                "score": float(score),
            }

    if raw_results is None:
        return None

    # Safety tasks
    if isinstance(raw_results, list) and any(st in task_name.lower() for st in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak", "safety"]):
        valid_flags = []
        harmful_flags = []
        unjudged_samples = 0

        for r in raw_results:
            resp = r.get("response", "")
            v_i = is_response_valid(resp)

            # Check v4 is_harmful field or v3 raw_asr
            if "is_harmful" in r:
                h_i = r["is_harmful"]
            else:
                raw_asr = r.get("original_asr")
                if raw_asr is None:
                    raw_asr = r.get("asr")

                h_i = None
                if raw_asr is not None:
                    try:
                        f_asr = float(raw_asr)
                        if math.isfinite(f_asr):
                            h_i = bool(f_asr > 0.5)
                    except (ValueError, TypeError):
                        h_i = None

            if h_i is None:
                unjudged_samples += 1

            # R3-03: VRR must be calculated over all generated outputs.
            # Never exclude unjudged harmfulness from valid_flags!
            valid_flags.append(v_i)
            harmful_flags.append(h_i)

        metrics = compute_secure_merge_metrics(valid_flags, harmful_flags)
        metrics["n_unjudged"] = unjudged_samples

        return {
            "type": "safety",
            "task": task_name,
            "model": model_name,
            "file": file_path,
            "n_samples": len(raw_results),
            "n_unjudged": unjudged_samples,
            "classifier_info": data.get("classifier_type", "benchmark_default"),
            "metrics": metrics,
        }

    # Utility tasks (lm-eval dict format)
    elif isinstance(raw_results, dict):
        score, metric_name, sample_len = extract_utility_metric_from_dict(raw_results)
        if score is not None:
            return {
                "type": "utility",
                "task": task_name or (list(raw_results.keys())[0] if raw_results else "utility"),
                "model": model_name,
                "file": file_path,
                "n_samples": sample_len,
                "metric_name": metric_name,
                "score": score,
            }

    # Utility list format fallback
    elif isinstance(raw_results, list) and any(ut in task_name for ut in ["math", "gsm8k", "code", "humaneval", "mbpp", "utility"]):
        correct_count = 0
        total_count = len(raw_results)
        for r in raw_results:
            if r.get("is_correct") is True or r.get("pass") == 1 or r.get("score", 0) > 0.5:
                correct_count += 1
        score = float(correct_count / total_count) if total_count > 0 else 0.0
        return {
            "type": "utility",
            "task": task_name,
            "model": model_name,
            "file": file_path,
            "n_samples": total_count,
            "metric_name": "list_pass_ratio",
            "score": score,
        }

    return None


def classify_method_track(model_id: str) -> Tuple[str, str]:
    m = model_id.lower()

    if "wizardmath" in m:
        return "domain_math_base", "domain_baseline_track"
    if "wizardcoder" in m:
        return "domain_code_base", "domain_baseline_track"
    if "medalpaca" in m:
        return "domain_medical_base", "domain_baseline_track"
    if "safetyft" in m or "safety_lora" in m or "safety_full" in m:
        return "safety_base", "safety_baseline_track"

    if "diagonal_sst" in m:
        return "diagonal_sst", "exploratory_sst_track"
    if "data_free_sst" in m:
        return "data_free_sst", "exploratory_sst_track"

    if "task_arithmetic" in m:
        return "legacy_task_arithmetic_linear_patch", "standard_baseline_track"

    if "linear" in m:
        return "linear", "standard_baseline_track"
    if "ties" in m:
        return "ties", "standard_baseline_track"
    if "dare" in m:
        return "dare", "standard_baseline_track"
    if "della" in m:
        return "della", "standard_baseline_track"
    if "safemerge" in m:
        return "safemerge", "standard_baseline_track"
    if "led" in m:
        return "led", "standard_baseline_track"
    if "mergealign" in m:
        return "mergealign", "standard_baseline_track"
    if "fisher" in m:
        return "fisher", "standard_baseline_track"

    return "unknown", "excluded_unknown"


def reaggregate_v3_results(
    results_root: str = "v3/results",
    output_dir: str = "v4/results/diagnostic_track",
) -> Dict[str, Any]:
    print(f"\n[Diagnostic Track] Scanning empirical JSON logs in {results_root}...")
    json_files = glob.glob(f"{results_root}/**/*.json", recursive=True)
    print(f"Found {len(json_files)} result files. Binding safety and utility evaluations by normalized Candidate ID...")

    candidates: Dict[str, Dict[str, Any]] = {}

    for f_path in json_files:
        info = parse_v3_result_file(f_path)
        if not info:
            continue

        raw_m = info["model"]
        # Normalize Candidate ID by removing task suffixes
        candidate_id = clean_candidate_model_id(raw_m)
        if not candidate_id:
            candidate_id = clean_candidate_model_id(os.path.basename(f_path).split(".json")[0])

        method_name, track = classify_method_track(candidate_id)
        if track == "excluded_unknown":
            continue

        if candidate_id not in candidates:
            # Infer domain
            domain = "unknown"
            if "math" in candidate_id.lower():
                domain = "math"
            elif "code" in candidate_id.lower():
                domain = "code"
            elif "medical" in candidate_id.lower():
                domain = "medical"

            # Infer alpha
            alpha = None
            for part in candidate_id.split("_"):
                if part.startswith("alpha") and len(part) > 5:
                    try:
                        alpha = float(part.replace("alpha", ""))
                    except Exception:
                        pass

            candidates[candidate_id] = {
                "candidate_id": candidate_id,
                "raw_model_path": raw_m,
                "domain": domain,
                "method": method_name,
                "alpha": alpha,
                "track": track,
                "safety_provenance": {},
                "utility_provenance": {},
                "safety_metrics_per_benchmark": {},
                "utility_scores_per_benchmark": {},
            }

        rec = candidates[candidate_id]
        t_name = info["task"]

        if info["type"] == "safety":
            rec["safety_provenance"][t_name] = {
                "file": info["file"],
                "n_samples": info["n_samples"],
                "classifier": info["classifier_info"],
            }
            rec["safety_metrics_per_benchmark"][t_name] = info["metrics"]
        elif info["type"] == "utility":
            rec["utility_provenance"][t_name] = {
                "file": info["file"],
                "n_samples": info["n_samples"],
                "metric_name": info["metric_name"],
            }
            rec["utility_scores_per_benchmark"][t_name] = info["score"]

    # Compute macro-aggregations and provenance summaries
    categorized_results = {
        "standard_baseline_track": [],
        "exploratory_sst_track": [],
        "domain_baseline_track": [],
        "safety_baseline_track": [],
    }

    for c_id, rec in candidates.items():
        s_b = rec["safety_metrics_per_benchmark"]
        u_b = rec["utility_scores_per_benchmark"]

        # Safety Aggregation (R2-05, R3-03, R3-05: Strict null propagation, no partial benchmark dropping)
        # If any benchmark has missing/null metrics (asr_all, asr_valid, vrr) or unjudged samples, candidate cannot be MEASURED.
        has_any_missing_metric = any(
            m.get("asr_all") is None or m.get("asr_valid") is None or m.get("vrr") is None or m.get("n_unjudged", 0) > 0
            for m in s_b.values()
        )
        asrs_all = [m["asr_all"] for m in s_b.values() if m.get("asr_all") is not None]
        vrrs_harm = [m["vrr"] for m in s_b.values() if m.get("vrr") is not None]
        valid_asrs = [m["asr_valid"] for m in s_b.values() if m.get("asr_valid") is not None]

        if not s_b or has_any_missing_metric or len(asrs_all) != len(s_b) or len(vrrs_harm) != len(s_b) or len(valid_asrs) != len(s_b):
            rec["asr_all"] = None
            rec["vrr_harmful"] = None
            rec["asr_valid"] = None
            rec["safety_status"] = "INSUFFICIENT_DATA"
        else:
            rec["asr_all"] = float(sum(asrs_all) / len(asrs_all))
            rec["vrr_harmful"] = float(sum(vrrs_harm) / len(vrrs_harm))
            rec["asr_valid"] = float(sum(valid_asrs) / len(valid_asrs))
            rec["safety_status"] = "MEASURED"

        # STRICT: NO FAKE ZERO OR DEFAULT VALUES (P0-01)
        rec["vrr_benign"] = None       # Not measured in harmful test logs
        rec["overrefusal"] = None      # Requires dedicated XSTest benign run

        # Utility Aggregation: STRICT null if empty (P0-02)
        if u_b:
            rec["utility_score"] = float(sum(u_b.values()) / len(u_b))
            rec["utility_status"] = "MEASURED"
        else:
            rec["utility_score"] = None
            rec["utility_status"] = "INSUFFICIENT_DATA"

        categorized_results[rec["track"]].append(rec)

    os.makedirs(output_dir, exist_ok=True)
    out_summary_file = os.path.join(output_dir, "diagnostic_reaggregation_summary.json")
    with open(out_summary_file, "w", encoding="utf-8") as f:
        json.dump(categorized_results, f, indent=2)

    print(f"\n[Diagnostic Track Completed]:")
    for trk, items in categorized_results.items():
        measured_both = sum(1 for it in items if it["utility_status"] == "MEASURED" and it["safety_status"] == "MEASURED")
        print(f"  {trk:26s} -> Total Candidates: {len(items):3d} | Measured BOTH Safety & Utility: {measured_both:3d}")

    print(f"Summary saved to: {out_summary_file}")
    return categorized_results


if __name__ == "__main__":
    reaggregate_v3_results()
