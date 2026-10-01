"""
Unit & Acceptance Test: test_utility_parser.py
Verifies that lm-evaluation-harness format dictionary results are accurately parsed,
scores (exact_match, math_verify, pass@1) are perfectly restored,
and sample_len / metadata counts are NEVER mistaken as utility scores (R2-06).
"""

import sys
import os
import json
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from analysis.reaggregate_v3_logs import parse_v3_result_file, extract_utility_metric_from_dict


class TestUtilityParser(unittest.TestCase):
    def test_lm_eval_dict_extraction(self):
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
        self.assertEqual(score, 0.5)
        self.assertIn("exact_match,flexible-extract", metric_name)
        self.assertEqual(sample_len, 100)

    def test_sample_len_never_extracted_as_utility_score(self):
        """
        R2-06: Verifies that metadata integers like sample_len (164, 1319)
        are NEVER extracted as utility score when custom metric is present.
        """
        humaneval_fixture = {
            "humaneval": {
                "sample_len": 164,
                "pass@1": 0.45,
                "fewshot": 0,
            }
        }
        score, metric_name, sample_len = extract_utility_metric_from_dict(humaneval_fixture)
        self.assertEqual(score, 0.45, "sample_len (164) was erroneously extracted as utility score!")
        self.assertEqual(sample_len, 164)

        # Unvetted/unknown schema should return None, NOT 1319.0
        unvetted_fixture = {
            "unknown_task": {
                "sample_len": 1319,
                "arbitrary_unvetted_metric": 999.0,
            }
        }
        score, metric_name, sample_len = extract_utility_metric_from_dict(unvetted_fixture)
        self.assertIsNone(score, "Unvetted schema was erroneously parsed instead of returning None!")

    def test_lm_eval_file_parser(self):
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
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed["type"], "utility")
            self.assertAlmostEqual(parsed["score"], 0.38362395754359363, places=7)
            self.assertEqual(parsed["n_samples"], 1319)
        finally:
            if os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)


if __name__ == "__main__":
    unittest.main()
