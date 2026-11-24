#!/usr/bin/env python3
"""
evaluate_human_audit.py

Calculates Inter-rater Agreement (Cohen's Kappa), Confusion Matrix,
and Rule-vs-Human Precision, Recall, F1 for the 200-sample human validity audit
according to Secure_Merge_Experiment_Plan.md / 計画書_v2.md Section 8.

Inputs:
- blinded_human_audit_sheet.json (with annotations)
- gold_mapping_key.json
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def calculate_cohen_kappa(r1: List[int], r2: List[int]) -> float:
    """Calculates Cohen's kappa for two binary or categorical raters."""
    assert len(r1) == len(r2) and len(r1) > 0
    n = len(r1)
    categories = sorted(list(set(r1 + r2)))
    
    # Observed agreement
    po = sum(1 for a, b in zip(r1, r2) if a == b) / n
    
    # Expected agreement
    pe = 0.0
    for c in categories:
        p1 = sum(1 for a in r1 if a == c) / n
        p2 = sum(1 for b in r2 if b == c) / n
        pe += p1 * p2
        
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def parse_validity(val: Any) -> Optional[bool]:
    """Normalizes validity annotation to boolean True/False/None."""
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    val_str = str(val).lower().strip()
    if val_str in ["valid", "true", "1", "non-degenerate", "non_degenerate"]:
        return True
    if val_str in ["invalid", "false", "0", "invalid_degenerated", "degenerate"]:
        return False
    return None  # e.g., hard_to_judge or uncertain


def evaluate_audit_results(annotated_sheet_path: str, key_path: str):
    with open(annotated_sheet_path, "r", encoding="utf-8") as f:
        annotated_data = json.load(f)
    with open(key_path, "r", encoding="utf-8") as f:
        key_data = json.load(f)

    # Support both list and {"samples": [...]}
    if isinstance(annotated_data, dict) and "samples" in annotated_data:
        samples = annotated_data["samples"]
    elif isinstance(annotated_data, list):
        samples = annotated_data
    else:
        raise ValueError("Invalid format in annotated_sheet_path: expected list or dict with 'samples'")

    # Support key_data as dict {id: info} or dict {"samples": [...]}
    if isinstance(key_data, dict) and "samples" in key_data:
        key_mapping = {item.get("blind_id") or item.get("sample_id"): item for item in key_data["samples"]}
    elif isinstance(key_data, dict):
        key_mapping = key_data
    else:
        raise ValueError("Invalid format in key_path: expected dict")

    print(f"=================================================================")
    print(f" Human Validity Audit Analysis (Total Samples: {len(samples)})")
    print(f"=================================================================\n")

    def get_stratum(s: Dict[str, Any]) -> str:
        s_id = s.get("sample_id") or s.get("blind_id")
        stratum = s.get("sampling_group")
        if not stratum and s_id in key_mapping:
            stratum = key_mapping[s_id].get("stratum")
        return stratum or "unknown"

    random_group = [s for s in samples if get_stratum(s) in ["random_sample", "random_150"]]
    hard_group = [s for s in samples if get_stratum(s) in ["hard_case", "hard_boundary_50"]]

    groups = [
        ("Random Sample (N=150: Representative Benchmark)", random_group),
        ("Hard Cases (N=50: Boundary Failure Analysis)", hard_group),
        ("Combined Total (N=200)", samples),
    ]

    for group_name, group_samples in groups:
        if not group_samples:
            continue
            
        print(f"--- Group: {group_name} ---")
        
        # Extract annotations
        ann_a_list, ann_b_list, adj_list = [], [], []
        
        for s in group_samples:
            h = s.get("human_annotation", {})
            if not isinstance(h, dict):
                h = {}

            # Check individual annotator fields
            val_a = parse_validity(
                s.get("annotator_a_valid") or
                h.get("annotator_a_valid") or
                s.get("annotator_a", {}).get("validity") if isinstance(s.get("annotator_a"), dict) else None
            )
            val_b = parse_validity(
                s.get("annotator_b_valid") or
                h.get("annotator_b_valid") or
                s.get("annotator_b", {}).get("validity") if isinstance(s.get("annotator_b"), dict) else None
            )
            val_adj = parse_validity(
                s.get("adjudicated_valid") or
                h.get("adjudicated_valid") or
                h.get("validity") or
                s.get("adjudicated", {}).get("validity") if isinstance(s.get("adjudicated"), dict) else None
            )

            ann_a_list.append(val_a)
            ann_b_list.append(val_b)
            adj_list.append(val_adj)

        # 1. Inter-rater agreement (if 2 annotators provided)
        has_two_annotators = all(a is not None for a in ann_a_list) and all(b is not None for b in ann_b_list)
        if has_two_annotators:
            r1 = [1 if a else 0 for a in ann_a_list]
            r2 = [1 if b else 0 for b in ann_b_list]
            kappa = calculate_cohen_kappa(r1, r2)
            raw_agree = sum(1 for a, b in zip(r1, r2) if a == b) / len(r1) * 100
            print(f"  [Inter-rater Agreement]")
            print(f"    - Raw Agreement: {raw_agree:.1f}%")
            print(f"    - Cohen's Kappa: {kappa:.3f}")
        else:
            filled_a = sum(1 for a in ann_a_list if a is not None)
            filled_b = sum(1 for b in ann_b_list if b is not None)
            if filled_a > 0 or filled_b > 0:
                print(f"  [Inter-rater Agreement] Partial ratings (A: {filled_a}/{len(group_samples)}, B: {filled_b}/{len(group_samples)})")

        # 2. Rule vs Human Gold Comparison (using adjudicated or primary validity)
        valid_pairs = []
        for s, adj in zip(group_samples, adj_list):
            if adj is None:
                continue
            s_id = s.get("sample_id") or s.get("blind_id")
            meta = key_mapping.get(s_id, {})
            # Rule valid: not is_gibberish
            rule_valid = not meta.get("is_gibberish", False)
            valid_pairs.append((rule_valid, adj))

        if valid_pairs:
            tp = sum(1 for r, h in valid_pairs if r and h)
            fp = sum(1 for r, h in valid_pairs if r and not h)
            fn = sum(1 for r, h in valid_pairs if not r and h)
            tn = sum(1 for r, h in valid_pairs if not r and not h)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

            print(f"  [Rule vs Human Gold Comparison] (Evaluated: {len(valid_pairs)}/{len(group_samples)})")
            print(f"    - Rule-based VRR Precision: {prec*100:.1f}%")
            print(f"    - Rule-based VRR Recall:    {rec*100:.1f}%")
            print(f"    - Rule-based VRR F1:        {f1*100:.1f}%")
            print(f"    - Confusion Matrix:         TP={tp}, FP={fp}, FN={fn}, TN={tn}")
        else:
            print("  [Notice] Human annotations are pending (null). Please fill in the sheet.")

        print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=str, default="/mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/blinded_human_audit_sheet.json")
    parser.add_argument("--key", type=str, default="/mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/gold_mapping_key.json")
    args = parser.parse_args()
    evaluate_audit_results(args.sheet, args.key)
