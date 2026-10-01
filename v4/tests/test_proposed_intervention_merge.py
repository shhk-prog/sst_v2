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

    def test_empty_or_non_finite_calibration_map_rejected(self):
        """
        R2-09: Verifies that empty JSON or maps lacking valid finite measurements
        strictly raise ValueError (E4 BLOCKED), never allowing calibrated=True.
        """
        # 1. Empty map
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            empty_path = f.name

        try:
            with self.assertRaises(ValueError) as ctx:
                ProposedInterventionMerger.from_calibration_map(empty_path, total_layers=8)
            self.assertIn("E4 BLOCKED", str(ctx.exception))
        finally:
            if os.path.exists(empty_path):
                os.remove(empty_path)

        # 2. Map with only NaN values
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"group1_layers_shallow": {"delta_asr": float("nan"), "delta_vrr": -0.01}}, f)
            nan_path = f.name

        try:
            with self.assertRaises(ValueError) as ctx:
                ProposedInterventionMerger.from_calibration_map(nan_path, total_layers=8)
            self.assertIn("E4 BLOCKED", str(ctx.exception))
        finally:
            if os.path.exists(nan_path):
                os.remove(nan_path)

    def test_calibration_strictly_rejects_missing_utility_or_overrefusal(self):
        """
        R3-07: A group having delta_asr and delta_vrr but lacking delta_utility or delta_overrefusal
        MUST NOT be accepted!
        """
        incomplete_map = {
            "group3_layers_mid_deep": {
                "delta_asr": -0.06,
                "delta_vrr": 0.0,
                # delta_utility and delta_overrefusal missing
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(incomplete_map, f)
            temp_path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                # Should fail because 0 valid complete groups exist
                ProposedInterventionMerger.from_calibration_map(temp_path, total_layers=8)
            self.assertIn("E4 BLOCKED", str(ctx.exception))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_group_wide_common_norm_scaling_maintains_relative_tensor_proportions(self):
        """
        R3-07: In a group with two tensors of sizes 1.0 and 100.0,
        group-wide common norm scaling scales both tensors with the SAME factor s_g,
        unlike per-tensor clipping which distorts them disproportionately.
        """
        complete_map = {
            "group1_layers_shallow": {
                "delta_asr": -0.06,
                "delta_vrr": 0.0,
                "delta_utility": 0.0,
                "delta_overrefusal": 0.0,
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(complete_map, f)
            temp_path = f.name
        try:
            # Set rho_g = 0.01
            merger = ProposedInterventionMerger.from_calibration_map(temp_path, rho_g=0.01, total_layers=8)
            # Create two tensors in the same group (layer 0)
            u_small = torch.ones(10, 10) * 1.0
            u_large = torch.ones(10, 10) * 100.0
            s_small = u_small + 1.0
            s_large = u_large + 1.0

            dict_u = {
                "model.layers.0.self_attn.q_proj.weight": u_small,
                "model.layers.0.self_attn.k_proj.weight": u_large,
            }
            dict_s = {
                "model.layers.0.self_attn.q_proj.weight": s_small,
                "model.layers.0.self_attn.k_proj.weight": s_large,
            }

            merged = merger.merge_state_dicts(dict_u, dict_s)
            delta_small = merged["model.layers.0.self_attn.q_proj.weight"] - u_small
            delta_large = merged["model.layers.0.self_attn.k_proj.weight"] - u_large

            # Both updates should be scaled by the EXACT same common scaling factor!
            ratio_small = (delta_small / (s_small - u_small)).mean().item()
            ratio_large = (delta_large / (s_large - u_large)).mean().item()
            self.assertAlmostEqual(ratio_small, ratio_large, places=5,
                                  msg="Tensors in the same group were scaled with different factors (per-tensor distortion)!")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
