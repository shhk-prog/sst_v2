"""
v4/tests/test_e1_selector.py
Unit tests verifying strict feasible region checks and missing metric rejection (P0-01, P1-01).
Uses standard unittest to avoid external test runner dependencies.
"""

import math
import unittest
from v4.scripts.analysis.e1_selector import (
    evaluate_feasible_region_strict,
    select_best_configurations,
    is_valid_finite,
)

DOMAIN_BASELINES = {
    "math": {"overrefusal": 0.02},
    "code": {"overrefusal": 0.02},
}


class TestE1Selector(unittest.TestCase):
    def test_missing_benign_vrr_must_be_insufficient_data(self):
        """無害評価を含まない候補は、有害ASR=0・有害VRR=1でも INSUFFICIENT_DATA"""
        cand = {
            "candidate_id": "cand_no_benign",
            "domain": "math",
            "method": "linear",
            "params": {"alpha": 0.5},
            "asr_all": 0.00,
            "asr_valid": 0.00,
            "vrr_harmful": 1.00,
            "vrr_benign": None,  # Missing!
            "overrefusal": 0.03,
            "utility_score": 0.65,
        }
        status, reason = evaluate_feasible_region_strict(cand, DOMAIN_BASELINES["math"])
        self.assertEqual(status, "INSUFFICIENT_DATA")
        self.assertIn("MISSING_OR_NON_FINITE_VRR_BENIGN", reason)

    def test_missing_utility_must_be_insufficient_data(self):
        """utilityなしはnull保持。最適候補を選ばない"""
        cand = {
            "candidate_id": "cand_no_utility",
            "domain": "math",
            "method": "linear",
            "params": {"alpha": 0.5},
            "asr_all": 0.01,
            "asr_valid": 0.01,
            "vrr_harmful": 0.99,
            "vrr_benign": 0.99,
            "overrefusal": 0.03,
            "utility_score": None,  # Missing!
        }
        status, reason = evaluate_feasible_region_strict(cand, DOMAIN_BASELINES["math"])
        self.assertEqual(status, "INSUFFICIENT_DATA")
        self.assertIn("MISSING_OR_NON_FINITE_UTILITY", reason)

    def test_nan_or_inf_metrics_must_be_insufficient_data(self):
        """NaN/Inf指標は不適格 (INSUFFICIENT_DATA)"""
        cand_nan = {
            "candidate_id": "cand_nan",
            "domain": "math",
            "method": "linear",
            "params": {"alpha": 0.5},
            "asr_all": float("nan"),
            "asr_valid": 0.01,
            "vrr_harmful": 0.99,
            "vrr_benign": 0.99,
            "overrefusal": 0.03,
            "utility_score": 0.50,
        }
        status, reason = evaluate_feasible_region_strict(cand_nan, DOMAIN_BASELINES["math"])
        self.assertEqual(status, "INSUFFICIENT_DATA")

        cand_inf = {
            "candidate_id": "cand_inf",
            "domain": "math",
            "method": "linear",
            "params": {"alpha": 0.5},
            "asr_all": 0.01,
            "asr_valid": float("inf"),
            "vrr_harmful": 0.99,
            "vrr_benign": 0.99,
            "overrefusal": 0.03,
            "utility_score": 0.50,
        }
        status, reason = evaluate_feasible_region_strict(cand_inf, DOMAIN_BASELINES["math"])
        self.assertEqual(status, "INSUFFICIENT_DATA")

    def test_infeasible_when_constraint_violated(self):
        """制約違反時は INFEASIBLE"""
        cand = {
            "candidate_id": "cand_high_asr",
            "domain": "math",
            "method": "linear",
            "params": {"alpha": 0.5},
            "asr_all": 0.08,  # Exceeds 0.05
            "asr_valid": 0.01,
            "vrr_harmful": 0.99,
            "vrr_benign": 0.99,
            "overrefusal": 0.03,
            "utility_score": 0.65,
            "safety_metrics_per_benchmark": {
                "harmbench": {"asr_all": 0.08, "asr_valid": 0.01, "vrr": 0.99},
                "jailbreakbench": {"asr_all": 0.08, "asr_valid": 0.01, "vrr": 0.99},
                "strongreject": {"asr_all": 0.08, "asr_valid": 0.01, "vrr": 0.99},
                "wildjailbreak": {"asr_all": 0.08, "asr_valid": 0.01, "vrr": 0.99},
            }
        }
        status, reason = evaluate_feasible_region_strict(cand, DOMAIN_BASELINES["math"])
        self.assertEqual(status, "INFEASIBLE")
        self.assertIn("ASR_ALL_EXCEEDED", reason)

    def test_feasible_and_selection(self):
        """完全準拠時は FEASIBLE かつ最高utility候補が選ばれる"""
        valid_benchmarks = {
            "harmbench": {"asr_all": 0.01, "asr_valid": 0.01, "vrr": 0.98, "n_samples": 100, "n_unjudged": 0},
            "jailbreakbench": {"asr_all": 0.01, "asr_valid": 0.01, "vrr": 0.98, "n_samples": 100, "n_unjudged": 0},
            "strongreject": {"asr_all": 0.01, "asr_valid": 0.01, "vrr": 0.98, "n_samples": 100, "n_unjudged": 0},
            "wildjailbreak": {"asr_all": 0.01, "asr_valid": 0.01, "vrr": 0.98, "n_samples": 100, "n_unjudged": 0},
        }
        cands = [
            {
                "candidate_id": "cand_1",
                "domain": "math",
                "method": "linear",
                "params": {"alpha": 0.3},
                "asr_all": 0.02,
                "asr_valid": 0.02,
                "vrr_harmful": 0.97,
                "vrr_benign": 0.97,
                "overrefusal": 0.04,
                "utility_score": 0.55,
                "safety_metrics_per_benchmark": valid_benchmarks,
            },
            {
                "candidate_id": "cand_2",
                "domain": "math",
                "method": "linear",
                "params": {"alpha": 0.5},
                "asr_all": 0.01,
                "asr_valid": 0.01,
                "vrr_harmful": 0.99,
                "vrr_benign": 0.99,
                "overrefusal": 0.03,
                "utility_score": 0.62,  # Higher utility
                "safety_metrics_per_benchmark": valid_benchmarks,
            },
        ]
        summary = select_best_configurations(cands, DOMAIN_BASELINES)
        self.assertIn("math_linear", summary)
        self.assertEqual(summary["math_linear"]["status"], "FEASIBLE_FOUND")
        self.assertEqual(summary["math_linear"]["best_candidate"]["candidate_id"], "cand_2")
        self.assertEqual(summary["math_linear"]["n_feasible"], 2)


if __name__ == "__main__":
    unittest.main()
