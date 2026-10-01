#!/usr/bin/env python3
"""
evaluate_human_audit.py

Calculates Inter-rater Agreement (Cohen's Kappa), Confusion Matrix,
and Rule-vs-Human Precision, Recall, F1 for the 200-sample human validity audit
according to Secure_Merge_Experiment_Plan.md Section 5.2.

Inputs:
- blinded_human_audit_sheet.json (with annotations)
- gold_mapping_key.json
"""

import json
from pathlib import Path
from typing import Dict, Any, List

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


def evaluate_audit_results(annotated_sheet_path: str, key_path: str):
    with open(annotated_sheet_path, "r", encoding="utf-8") as f:
        annotated_data = json.load(f)
    with open(key_path, "r", encoding="utf-8") as f:
        key_data = json.load(f)

    samples = annotated_data.get("samples", [])
    key_mapping = {item["blind_id"]: item for item in key_data.get("samples", [])}

    print(f"=================================================================")
    print(f" Human Validity Audit Analysis (N = {len(samples)})")
    print(f"=================================================================\n")

    random_group = [s for s in samples if s.get("sampling_group") == "random_150"]
    hard_group = [s for s in samples if s.get("sampling_group") == "hard_boundary_50"]

    for group_name, group_samples in [("Random Sample (N=150)", random_group), ("Hard Cases (N=50)", hard_group), ("Combined Total (N=200)", samples)]:
        if not group_samples:
            continue
            
        print(f"--- Group: {group_name} ---")
        
        # Check if annotations exist
        has_ann_a = all("annotator_a_valid" in s for s in group_samples)
        has_ann_b = all("annotator_b_valid" in s for s in group_samples)
        has_adj = all("adjudicated_valid" in s for s in group_samples)

        if not (has_ann_a and has_ann_b):
            print("  [Notice] Annotator ratings are pending. Template ready for double-blind review.\n")
            continue

        r1 = [1 if s["annotator_a_valid"] else 0 for s in group_samples]
        r2 = [1 if s["annotator_b_valid"] else 0 for s in group_samples]
        kappa = calculate_cohen_kappa(r1, r2)
        raw_agree = sum(1 for a, b in zip(r1, r2) if a == b) / len(r1) * 100

        print(f"  - Inter-rater Raw Agreement: {raw_agree:.1f}%")
        print(f"  - Cohen's Kappa: {kappa:.3f}")

        # If adjudicated, compare Rule vs Human Gold
        if has_adj:
            tp = fp = fn = tn = 0
            for s in group_samples:
                blind_id = s["blind_id"]
                rule_valid = key_mapping[blind_id].get("rule_valid", True)
                human_valid = s["adjudicated_valid"]

                if rule_valid and human_valid:
                    tp += 1
                elif rule_valid and not human_valid:
                    fp += 1
                elif not rule_valid and human_valid:
                    fn += 1
                else:
                    tn += 1

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

            print(f"  - Rule-based VRR Precision: {prec*100:.1f}%")
            print(f"  - Rule-based VRR Recall:    {rec*100:.1f}%")
            print(f"  - Rule-based VRR F1:        {f1*100:.1f}%")
            print(f"  - Confusion Matrix (TP={tp}, FP={fp}, FN={fn}, TN={tn})\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=str, default="v4/results/eval/human_audit/blinded_human_audit_sheet.json")
    parser.add_argument("--key", type=str, default="v4/results/eval/human_audit/gold_mapping_key.json")
    args = parser.parse_args()
    evaluate_audit_results(args.sheet, args.key)
