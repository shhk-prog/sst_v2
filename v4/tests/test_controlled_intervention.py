"""
v4/tests/test_controlled_intervention.py
Unit tests verifying exact parameter count, tensor type matching, and strict norm shrinkage for E3.2 (P1-02, P1-04).
"""

import unittest
import torch
from v4.scripts.analysis.controlled_intervention import (
    sample_matched_random_keys,
    build_single_controlled_condition,
    compute_dict_l2_norm,
)
from v4.scripts.analysis.intervention_mapper import classify_tensor_detailed


class TestControlledIntervention(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        # Synthetic 8-layer model with realistic attention, MLP, and norm layers
        self.total_layers = 8
        self.dict_u = {}
        self.dict_s = {}

        for i in range(self.total_layers):
            # Attention q_proj (16x16 = 256 params)
            k_q = f"model.layers.{i}.self_attn.q_proj.weight"
            self.dict_u[k_q] = torch.randn(16, 16)
            self.dict_s[k_q] = torch.randn(16, 16)

            # MLP gate_proj (32x16 = 512 params)
            k_g = f"model.layers.{i}.mlp.gate_proj.weight"
            self.dict_u[k_g] = torch.randn(32, 16)
            self.dict_s[k_g] = torch.randn(32, 16)

            # Norm (16 params)
            k_n = f"model.layers.{i}.input_layernorm.weight"
            self.dict_u[k_n] = torch.randn(16)
            self.dict_s[k_n] = torch.randn(16)

        self.all_keys = list(self.dict_u.keys())
        self.shapes = {k: tuple(self.dict_u[k].shape) for k in self.all_keys}

    def test_random_control_exact_parameter_and_type_matching(self):
        """
        Verify that random control sampling selects the EXACT same parameter count
        and module types as map_keys (P1-02).
        """
        # Let map_keys be deep layers (group4: layers 6, 7)
        map_keys = set(
            k for k in self.all_keys
            if classify_tensor_detailed(k, total_layers=self.total_layers)["group"] == "group4_layers_deep"
        )
        self.assertTrue(len(map_keys) > 0)

        n_params_map = sum(torch.numel(self.dict_u[k]) for k in map_keys)

        # Count map module types
        map_types = [classify_tensor_detailed(k, total_layers=self.total_layers)["module_type"] for k in map_keys]

        # Sample control keys
        control_keys = sample_matched_random_keys(
            map_keys=map_keys,
            all_keys=self.all_keys,
            state_dict_shapes=self.shapes,
            total_layers=self.total_layers,
            seed=42,
        )

        n_params_control = sum(torch.numel(self.dict_u[k]) for k in control_keys)
        control_types = [classify_tensor_detailed(k, total_layers=self.total_layers)["module_type"] for k in control_keys]

        # 1. Total keys must match exactly
        self.assertEqual(len(control_keys), len(map_keys))
        # 2. Total parameters must match exactly
        self.assertEqual(n_params_control, n_params_map)
        # 3. Module type distribution must match exactly
        self.assertEqual(sorted(control_types), sorted(map_types))
        # 4. Control keys must NOT overlap with map_keys
        self.assertEqual(len(control_keys & map_keys), 0)

    def test_norm_shrinkage_only(self):
        """Verify that norm matching strictly shrinks and never expands."""
        # Condition A and Condition C
        res_A, norm_A = build_single_controlled_condition(
            "Condition_A_Map_Common", self.dict_u, self.dict_s,
            beneficial_groups=["group4_layers_deep"], common_alpha=0.5, rho_g=0.03, total_layers=8
        )
        res_C, norm_C = build_single_controlled_condition(
            "Condition_C_Map_Capped", self.dict_u, self.dict_s,
            beneficial_groups=["group4_layers_deep"], common_alpha=0.5, rho_g=0.03, total_layers=8
        )

        # Condition C has capped norm, so norm_C <= norm_A
        self.assertLessEqual(norm_C, norm_A + 1e-6)

        # Matched control A scaled down to C's norm
        res_A_matched, norm_A_matched = build_single_controlled_condition(
            "Control_A_Scaled_to_C_Norm", self.dict_u, self.dict_s,
            beneficial_groups=["group4_layers_deep"], common_alpha=0.5, rho_g=0.03, total_layers=8
        )
        self.assertAlmostEqual(norm_A_matched, norm_C, places=4)


if __name__ == "__main__":
    unittest.main()
