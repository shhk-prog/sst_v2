"""
v4/tests/test_proposed_intervention_merge.py
Unit tests verifying strict calibration requirement and dynamic weight derivation for E4 (P0-05, P1-03).
"""

import os
import json
import tempfile
import unittest
import torch
from v4.scripts.mergers.proposed_intervention_merge import ProposedInterventionMerger


class TestProposedInterventionMerge(unittest.TestCase):
    def test_uncalibrated_instantiation_rejected_in_production(self):
        """未calibrateの既定重みでの生成はエラーとなる（P0-05）"""
        with self.assertRaises(ValueError) as ctx:
            ProposedInterventionMerger(group_weights={"group1_layers_shallow": 0.2})
        self.assertIn("PRODUCTION_MERGE_REJECTED", str(ctx.exception))

    def test_from_calibration_map_construction_and_zero_weight_for_ineffective_groups(self):
        """
        E3実測地図から正しく重みを導出し、安全性改善のない群や退化群には重み0.0を割り当てる（P1-03）。
        """
        synthetic_calib = {
            "group3_layers_mid_deep": {
                "delta_asr": -0.06,  # Efficacious safety improvement
                "delta_vrr": -0.01,  # Safe
                "delta_utility": -0.01,
                "delta_overrefusal": 0.01,
            },
            "group1_layers_shallow": {
                "delta_asr": 0.01,  # No safety improvement (worse)
                "delta_vrr": 0.00,
            },
            "group5_norms": {
                "delta_asr": -0.05,
                "delta_vrr": -0.10,  # Severe degeneration (VRR drop > 0.03)
            }
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(synthetic_calib, f)
            temp_path = f.name

        try:
            merger = ProposedInterventionMerger.from_calibration_map(temp_path, total_layers=8)
            weights = merger.group_weights

            # Group 3 is accepted with positive weight
            self.assertGreater(weights.get("group3_layers_mid_deep", 0.0), 0.1)

            # Group 1 is rejected (insufficient safety improvement) -> 0.0
            self.assertEqual(weights.get("group1_layers_shallow", 0.0), 0.0)

            # Group 5 is rejected (excessive degeneration) -> 0.0
            self.assertEqual(weights.get("group5_norms", 0.0), 0.0)

            # Non-existent groups receive 0.0
            self.assertEqual(weights.get("group4_layers_deep", 0.0), 0.0)

            self.assertTrue(merger.is_dynamic_calibrated)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
