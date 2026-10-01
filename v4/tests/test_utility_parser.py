"""
Unit & Acceptance Test: test_utility_parser.py
Verifies that lm-evaluation-harness format dictionary results are accurately parsed
and that scores (exact_match, math_verify, pass@1) are perfectly restored without zero-filling.
"""

import sys
import os
import json
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from analysis.reaggregate_v3_logs import parse_v3_result_file, extract_utility_metric_from_dict


def test_lm_eval_dict_extraction():
    # Acceptance criteria: lm-eval dict with score 0.5 must be restored to exactly 0.5
    dummy_dict = {
        "gsm8k": {
            "name": "gsm8k",
            "sample_len": 100,
            "exact_match,flexible-extract": 0.5,
            "exact_match_stderr,flexible-extract": 0.05,
        }
    }
    score, metric_name, sample_len = extract_utility_metric_from_dict(dummy_dict)
    assert score == 0.5, f"Expected 0.5, got {score}"
    assert "exact_match,flexible-extract" in metric_name
    assert sample_len == 100
    print("Passed: lm-eval dict extraction restored exact 0.5 score.")


def test_lm_eval_file_parser():
    tmp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        content = {
            "model": "test_merged_model_alpha0.5",
            "task": "utility_math_gsm8k",
            "results": {
                "gsm8k": {
                    "sample_len": 1319,
                    "exact_match,flexible-extract": 0.38362395754359363,
                }
            }
        }
        json.dump(content, tmp_file)
        tmp_file.close()

        parsed = parse_v3_result_file(tmp_file.name)
        assert parsed is not None
        assert parsed["type"] == "utility"
        assert abs(parsed["score"] - 0.38362395754359363) < 1e-7
        assert parsed["n_samples"] == 1319
        print(f"Passed: parsed utility score {parsed['score']:.6f} accurately from fixture file.")
    finally:
        os.remove(tmp_file.name)


if __name__ == "__main__":
    test_lm_eval_dict_extraction()
    test_lm_eval_file_parser()
    print("\nALL UTILITY PARSER ACCEPTANCE TESTS PASSED!")
