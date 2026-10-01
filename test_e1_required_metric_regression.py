"""Regression tests for per-benchmark metric completeness.

Run from the repository root:
    python test_e1_required_metric_regression.py --repo-root .

Imports the actual selector file. Does not load models, fetch datasets,
change source files, or execute model-generated code.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

SELECTOR: ModuleType
METRICS = ("asr_all", "asr_valid", "vrr")


def make_candidate() -> dict[str, Any]:
    return {
        "candidate_id": "synthetic-regression-fixture",
        "domain": "math",
        "method": "linear",
        "utility_score": 0.7,
        "asr_all": 0.0,
        "asr_valid": 0.0,
        "vrr_harmful": 1.0,
        "vrr_benign": 1.0,
        "overrefusal": 0.02,
        "safety_metrics_per_benchmark": {
            name: {
                "asr_all": 0.0,
                "asr_valid": 0.0,
                "vrr": 1.0,
                "n_samples": 100,
                "n_unjudged": 0,
            }
            for name in SELECTOR.DEFAULT_REQUIRED_BENCHMARKS
        },
    }


class RequiredMetricRegression(unittest.TestCase):
    def status(self, candidate: dict[str, Any]) -> str:
        status, _ = SELECTOR.evaluate_feasible_region_strict(
            candidate,
            {"overrefusal": 0.02},
            required_benchmarks=SELECTOR.DEFAULT_REQUIRED_BENCHMARKS,
        )
        return status

    def test_complete_candidate_remains_feasible(self) -> None:
        self.assertEqual(self.status(make_candidate()), "FEASIBLE")

    def test_each_required_metric_rejects_null_and_absence(self) -> None:
        # Keep aggregate metrics and counts valid so a different guard
        # cannot accidentally make this test pass.
        for benchmark in SELECTOR.DEFAULT_REQUIRED_BENCHMARKS:
            for metric in METRICS:
                for mode in ("null", "missing"):
                    with self.subTest(benchmark=benchmark, metric=metric, mode=mode):
                        candidate = make_candidate()
                        record = candidate["safety_metrics_per_benchmark"][benchmark]
                        if mode == "null":
                            record[metric] = None
                        else:
                            del record[metric]
                        self.assertEqual(self.status(candidate), "INSUFFICIENT_DATA")

    def test_counts_alone_do_not_establish_complete_measurement(self) -> None:
        candidate = make_candidate()
        benchmark = SELECTOR.DEFAULT_REQUIRED_BENCHMARKS[0]
        candidate["safety_metrics_per_benchmark"][benchmark] = {
            "n_samples": 100, "n_unjudged": 0,
        }
        self.assertEqual(self.status(candidate), "INSUFFICIENT_DATA")

    def test_nonfinite_or_out_of_range_metric_is_rejected(self) -> None:
        for metric in METRICS:
            for value in (float("nan"), float("inf"), -0.1, 1.1):
                with self.subTest(metric=metric, value=repr(value)):
                    candidate = make_candidate()
                    benchmark = SELECTOR.DEFAULT_REQUIRED_BENCHMARKS[0]
                    candidate["safety_metrics_per_benchmark"][benchmark][metric] = value
                    self.assertEqual(self.status(candidate), "INSUFFICIENT_DATA")

    def test_count_validation_is_preserved(self) -> None:
        for metric in ("n_samples", "n_unjudged"):
            for value in (None, float("nan"), float("inf"), -1, True, 0.5):
                with self.subTest(metric=metric, value=repr(value)):
                    candidate = make_candidate()
                    benchmark = SELECTOR.DEFAULT_REQUIRED_BENCHMARKS[0]
                    record = candidate["safety_metrics_per_benchmark"][benchmark]
                    if value is None:
                        del record[metric]
                    else:
                        record[metric] = value
                    self.assertEqual(self.status(candidate), "INSUFFICIENT_DATA")

    def test_select_best_cannot_select_null_metric_candidate(self) -> None:
        candidate = make_candidate()
        benchmark = SELECTOR.DEFAULT_REQUIRED_BENCHMARKS[0]
        candidate["safety_metrics_per_benchmark"][benchmark]["asr_valid"] = None
        result = SELECTOR.select_best_configurations(
            [candidate], {"math": {"overrefusal": 0.02}},
        )
        self.assertEqual(result["math_linear"]["n_feasible"], 0)
        self.assertIsNone(result["math_linear"]["best_candidate"])
        self.assertEqual(result["math_linear"]["status"], "INSUFFICIENT_DATA")

    def test_sensitivity_cannot_count_null_metric_candidate(self) -> None:
        candidate = make_candidate()
        benchmark = SELECTOR.DEFAULT_REQUIRED_BENCHMARKS[0]
        candidate["safety_metrics_per_benchmark"][benchmark]["vrr"] = None
        table = SELECTOR.compute_sensitivity_matrix(
            [candidate], {"math": {"overrefusal": 0.02}},
            asr_thresholds=[0.05], vrr_thresholds=[0.95],
        )
        self.assertEqual(int(table.iloc[0]["math_linear_pass"]), 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    source = args.repo_root.resolve() / "v4/scripts/analysis/e1_selector.py"
    if not source.is_file():
        parser.error(f"Selector file not found: {source}")
    spec = importlib.util.spec_from_file_location("audited_e1_selector", source)
    if spec is None or spec.loader is None:
        parser.error(f"Cannot import selector: {source}")
    global SELECTOR
    SELECTOR = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(SELECTOR)
    except ImportError as exc:
        print(f"Use the project environment with its dependencies: {exc}", file=sys.stderr)
        return 2
    print(f"Testing actual selector: {source}", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RequiredMetricRegression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
