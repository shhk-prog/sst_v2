"""
v4/tests/test_characteristic_analyzer.py
Unit tests verifying weight characteristics analysis and FP16 overflow prevention (P0-04, P1-04).
"""

import unittest
import torch
from v4.scripts.analysis.characteristic_analyzer import (
    compute_tensor_characteristics,
    analyze_state_dicts,
)


class TestCharacteristicAnalyzer(unittest.TestCase):
    def test_fp16_squared_sum_overflow_prevention(self):
        """
        Verify that 256x256 FP16 ones tensor does NOT overflow to inf.
        In FP16, (ones_256x256 ** 2).sum() overflows to inf because 65536 > FP16_MAX (65504).
        Our implementation must compute norms in FP32 and return finite 256.0.
        """
        t_fp16 = torch.ones(256, 256, dtype=torch.float16)
        t_zero = torch.zeros(256, 256, dtype=torch.float16)

        # Standard FP16 square sum demonstrates overflow:
        raw_fp16_sum = (t_fp16 ** 2).sum().item()
        self.assertTrue(torch.isinf(torch.tensor(raw_fp16_sum)))

        # Our analyzer must prevent this and return exact 256.0 norm
        metrics = compute_tensor_characteristics(t_fp16, t_zero)
        self.assertTrue(torch.isfinite(torch.tensor(metrics["norm_delta"])))
        self.assertAlmostEqual(metrics["norm_delta"], 256.0, places=4)
        self.assertAlmostEqual(metrics["relative_update_r_g"], 256.0 / (0.0 + 1e-8), places=1)

    def test_synthetic_analysis_consistency(self):
        """Verify report statistics on reproducible synthetic state dicts."""
        torch.manual_seed(42)
        theta_0 = torch.randn(32, 32, dtype=torch.float32)
        theta_u = theta_0 + torch.randn(32, 32, dtype=torch.float32) * 0.1
        theta_s = theta_0 + torch.randn(32, 32, dtype=torch.float32) * 0.1
        theta_m = theta_u + torch.randn(32, 32, dtype=torch.float32) * 0.05

        d_0 = {"layer.0.weight": theta_0, "layer.1.weight": theta_0}
        d_u = {"layer.0.weight": theta_u, "layer.1.weight": theta_u}
        d_s = {"layer.0.weight": theta_s, "layer.1.weight": theta_s}
        d_m = {"layer.0.weight": theta_m, "layer.1.weight": theta_u + (theta_s - theta_u) * 0.8}

        report = analyze_state_dicts(d_m, d_u, d_s, d_0)
        self.assertIn("overall_relative_update_r_g", report)
        self.assertIn("concentration_ratio", report)
        self.assertEqual(report["max_update_layer"], "layer.1.weight")
        self.assertGreater(report["concentration_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
