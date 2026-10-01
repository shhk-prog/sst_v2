"""
E4: proposed_intervention_merge.py
Behavior-Intervention Guided Constrained Merge (行動介入に基づく非退化制約付きマージ)
Formulation according to Secure_Merge_Experiment_Plan.md Section 10:

    theta_new = theta_u + sum_g a_g * P_g(theta_s - theta_u),  a_g >= 0
    subject to:
    ||a_g * P_g(theta_s - theta_u)|| / (||theta_u,g|| + eps) <= rho_g

Important Principle (Plan Section 10):
- Group weights a_g must NOT be hardcoded as an assumed conclusion.
- Weights must be dynamically derived from E3 Calibration intervention results:
  a_g is allocated proportionally to (Delta ASR / (Delta Degradation + eps)).
- Hardcoded weights in __init__ serve strictly as smoke-test temporary defaults.
"""

import os
import json
import torch
from typing import Dict, Any, List, Optional
from mergers.base_merger import BaseMerger
from analysis.intervention_mapper import classify_tensor_group


class ProposedInterventionMerger(BaseMerger):
    def __init__(
        self,
        group_weights: Optional[Dict[str, float]] = None,
        rho_g: float = 0.08,
        total_layers: int = 32,
        eps: float = 1e-8,
        is_dynamic_calibrated: bool = False,
    ):
        """
        Args:
            group_weights: Dict mapping group names to scalar coefficient a_g.
                           If None, temporary smoke-test defaults are provided.
            rho_g: Upper bound on relative update norm per region.
            total_layers: Number of transformer layers.
            eps: Numerical stability constant.
            is_dynamic_calibrated: Flag indicating whether weights were dynamically computed from Calibration data.
        """
        if group_weights is None:
            # Temporary smoke-test default (NOT an empirical scientific conclusion)
            group_weights = {
                "group1_layers_shallow": 0.2,
                "group2_layers_mid_shallow": 0.3,
                "group3_layers_mid_deep": 0.5,
                "group4_layers_deep": 0.4,
                "group5_norms": 0.1,
                "group6_embed_head": 0.0,
            }
            is_dynamic_calibrated = False

        super().__init__(
            name="proposed_intervention_merge",
            config={
                "group_weights": group_weights,
                "rho_g": rho_g,
                "total_layers": total_layers,
                "is_dynamic_calibrated": is_dynamic_calibrated,
            }
        )
        self.group_weights = group_weights
        self.rho_g = float(rho_g)
        self.total_layers = total_layers
        self.eps = float(eps)
        self.is_dynamic_calibrated = is_dynamic_calibrated

    @classmethod
    def from_calibration_map(
        cls,
        intervention_map_path: str,
        rho_g: float = 0.08,
        total_layers: int = 32,
        target_asr_reduction_min: float = 0.02,
        max_vrr_drop: float = 0.03,
    ) -> "ProposedInterventionMerger":
        """
        Dynamically constructs merger from E3 empirical calibration intervention results.
        Selects and weights regions where safety improves without triggering invalid degeneration.
        """
        if not os.path.exists(intervention_map_path):
            raise FileNotFoundError(
                f"Calibration intervention map not found: {intervention_map_path}. "
                "E4 cannot proceed without empirical E3 measurements."
            )

        with open(intervention_map_path, "r", encoding="utf-8") as f:
            calib_data = json.load(f)

        # Expected format of calib_data: {group_name: {"delta_asr": ..., "delta_vrr": ..., "delta_utility": ...}}
        group_weights = {}
        for grp, stats in calib_data.items():
            delta_asr = stats.get("delta_asr", 0.0)  # negative is safer
            delta_vrr = stats.get("delta_vrr", 0.0)  # negative is degenerated

            # Rule from plan Section 9.1:
            # "ASRが下がってもVRR低下を伴う群は、安全性改善群とは判定しない。"
            if delta_vrr < -max_vrr_drop:
                group_weights[grp] = 0.0  # Rejected due to degeneration
            elif delta_asr < -target_asr_reduction_min:
                # Efficacious safety improvement with preserved validity
                safety_gain = abs(delta_asr)
                group_weights[grp] = float(min(1.0, max(0.1, safety_gain * 5.0)))
            else:
                group_weights[grp] = 0.05  # Minimal baseline update

        return cls(
            group_weights=group_weights,
            rho_g=rho_g,
            total_layers=total_layers,
            is_dynamic_calibrated=True,
        )

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> torch.Tensor:
        if key is None:
            a_g = 0.3
        else:
            grp = classify_tensor_group(key, self.total_layers)
            a_g = self.group_weights.get(grp, 0.0)

        delta = a_g * (theta_s - theta_u)

        # Apply per-region update norm constraint: ||delta|| / (||u|| + eps) <= rho_g
        norm_delta = torch.norm(delta)
        norm_u = torch.norm(theta_u)
        current_r_g = norm_delta / (norm_u + self.eps)

        if current_r_g > self.rho_g:
            scaling = (self.rho_g * (norm_u + self.eps)) / (norm_delta + self.eps)
            delta = delta * scaling

        out = theta_u + delta
        self.check_finite(out, "proposed_intervention_merge")
        return out
