"""
E4: proposed_intervention_merge.py
Behavior-Intervention Guided Constrained Merge (行動介入に基づく非退化制約付きマージ)
Formulation according to Secure_Merge_Experiment_Plan.md Section 10 and Code Audit Remediation (P0-05, P1-03).

Key Principles:
1. Strict Dependency on Empirical E3 Behavioral Maps:
   - Must be dynamically constructed via from_calibration_map.
   - Non-calibrated default weights are REJECTED in production mode.
2. Group-level Norm Constraints:
   - Groups lacking safety improvement are assigned weight 0.0 (no default leakage).
   - Utility and overrefusal degradations are strictly evaluated.
3. High precision FP32/FP64 computation.
"""

import os
import json
import math
import torch
from typing import Dict, Any, List, Optional
from mergers.base_merger import BaseMerger
from analysis.intervention_mapper import classify_tensor_detailed


class ProposedInterventionMerger(BaseMerger):
    def __init__(
        self,
        group_weights: Optional[Dict[str, float]] = None,
        rho_g: float = 0.08,
        total_layers: int = 32,
        eps: float = 1e-8,
        is_dynamic_calibrated: bool = False,
        calibration_provenance: Optional[Dict[str, Any]] = None,
        allow_uncalibrated_smoke_test: bool = False,
    ):
        """
        Args:
            group_weights: Dict mapping group names to scalar coefficient a_g >= 0.
            rho_g: Upper bound on relative update norm per region.
            total_layers: Number of transformer layers.
            eps: Numerical stability constant.
            is_dynamic_calibrated: True if weights originate from real E3 calibration.
            calibration_provenance: Metadata tracing origin map file and thresholds.
            allow_uncalibrated_smoke_test: Explicit bypass for unit testing / mathematical auditing only.
        """
        if not is_dynamic_calibrated and not allow_uncalibrated_smoke_test:
            raise ValueError(
                "PRODUCTION_MERGE_REJECTED: ProposedInterventionMerger must be instantiated via "
                "from_calibration_map with empirical E3 behavioral data. Uncalibrated defaults "
                "are forbidden in scientific runs (P0-05, P1-03)."
            )

        if group_weights is None:
            group_weights = {
                "group1_layers_shallow": 0.2,
                "group2_layers_mid_shallow": 0.3,
                "group3_layers_mid_deep": 0.5,
                "group4_layers_deep": 0.4,
                "group5_norms": 0.1,
                "group6_embed": 0.0,
                "group6_head": 0.0,
            }

        super().__init__(
            name="proposed_intervention_merge",
            config={
                "group_weights": group_weights,
                "rho_g": rho_g,
                "total_layers": total_layers,
                "is_dynamic_calibrated": is_dynamic_calibrated,
                "calibration_provenance": calibration_provenance,
            }
        )
        self.group_weights = group_weights
        self.rho_g = float(rho_g)
        self.total_layers = total_layers
        self.eps = float(eps)
        self.is_dynamic_calibrated = is_dynamic_calibrated
        self.calibration_provenance = calibration_provenance or {}

    @classmethod
    def from_calibration_map(
        cls,
        intervention_map_path: str,
        rho_g: float = 0.08,
        total_layers: int = 32,
        target_asr_reduction_min: float = 0.02,
        max_vrr_drop: float = 0.03,
        max_utility_drop: float = 0.05,
        max_overrefusal_increase: float = 0.03,
    ) -> "ProposedInterventionMerger":
        """
        Dynamically derives group weights from empirical E3 behavioral calibration map (P1-03).
        
        Selection Criteria per region g:
        1. Safety Improvement: delta_asr <= -target_asr_reduction_min (ASR decreases)
        2. Non-Degeneration:
           - delta_vrr >= -max_vrr_drop (Harmful VRR maintained)
           - delta_utility >= -max_utility_drop (Utility not destroyed)
           - delta_overrefusal <= max_overrefusal_increase (Benign overrefusal not inflated)
        3. Any group failing these criteria receives weight 0.0 (no update).
        """
        if not os.path.exists(intervention_map_path):
            raise FileNotFoundError(
                f"E4 BLOCKED: Calibration intervention map not found: {intervention_map_path}. "
                "E4 cannot proceed without empirical E3 behavioral measurements."
            )

        with open(intervention_map_path, "r", encoding="utf-8") as f:
            calib_data = json.load(f)

        if not isinstance(calib_data, dict) or len(calib_data) == 0:
            raise ValueError(
                f"E4 BLOCKED: Calibration map {intervention_map_path} is empty or invalid JSON (R2-09)."
            )

        provenance = {
            "source_map_path": intervention_map_path,
            "target_asr_reduction_min": target_asr_reduction_min,
            "max_vrr_drop": max_vrr_drop,
            "max_utility_drop": max_utility_drop,
            "max_overrefusal_increase": max_overrefusal_increase,
            "evaluated_groups": {},
        }

        group_weights = {}
        all_possible_groups = [
            "group1_layers_shallow",
            "group2_layers_mid_shallow",
            "group3_layers_mid_deep",
            "group4_layers_deep",
            "group5_norms",
            "group6_embed",
            "group6_head",
        ]

        valid_measured_groups_count = 0

        for grp in all_possible_groups:
            stats = calib_data.get(grp)
            if stats is None:
                # Missing calibration data for this group -> zero weight
                group_weights[grp] = 0.0
                provenance["evaluated_groups"][grp] = {"status": "MISSING_DATA", "weight": 0.0}
                continue

            delta_asr = stats.get("delta_asr")
            delta_vrr = stats.get("delta_vrr")
            delta_util = stats.get("delta_utility")
            delta_overref = stats.get("delta_overrefusal")

            # Check that required calibration metrics are present and strictly finite
            is_valid_entry = True
            for m_val in [delta_asr, delta_vrr]:
                if m_val is None or not math.isfinite(float(m_val)):
                    is_valid_entry = False
                    break

            if not is_valid_entry:
                group_weights[grp] = 0.0
                provenance["evaluated_groups"][grp] = {"status": "INCOMPLETE_OR_NON_FINITE_DATA", "weight": 0.0}
                continue

            valid_measured_groups_count += 1

            rejection_reasons = []
            # 1. Non-degeneration checks
            if delta_vrr < -max_vrr_drop:
                rejection_reasons.append(f"VRR_DROP({delta_vrr:.4f} < {-max_vrr_drop})")
            if delta_util is not None and delta_util < -max_utility_drop:
                rejection_reasons.append(f"UTILITY_DROP({delta_util:.4f} < {-max_utility_drop})")
            if delta_overref is not None and delta_overref > max_overrefusal_increase:
                rejection_reasons.append(f"OVERREFUSAL_INCREASE({delta_overref:.4f} > {max_overrefusal_increase})")

            # 2. Safety improvement check
            if delta_asr > -target_asr_reduction_min:
                rejection_reasons.append(f"INSUFFICIENT_ASR_REDUCTION({delta_asr:.4f} > {-target_asr_reduction_min})")

            if rejection_reasons:
                group_weights[grp] = 0.0
                provenance["evaluated_groups"][grp] = {
                    "status": "REJECTED",
                    "weight": 0.0,
                    "reasons": rejection_reasons,
                }
            else:
                # Beneficial region: assign weight proportional to safety gain
                safety_gain = abs(delta_asr)
                assigned_weight = float(min(1.0, max(0.1, safety_gain * 5.0)))
                group_weights[grp] = assigned_weight
                provenance["evaluated_groups"][grp] = {
                    "status": "ACCEPTED",
                    "weight": assigned_weight,
                    "delta_asr": delta_asr,
                    "delta_vrr": delta_vrr,
                }

        if valid_measured_groups_count == 0:
            raise ValueError(
                f"E4 BLOCKED: Calibration map {intervention_map_path} contains no valid finite measured groups (R2-09)."
            )

        return cls(
            group_weights=group_weights,
            rho_g=rho_g,
            total_layers=total_layers,
            is_dynamic_calibrated=True,
            calibration_provenance=provenance,
        )

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> torch.Tensor:
        """
        Applies calibrated group weight and per-region/tensor norm constraint in FP32 precision.
        """
        if not self.is_dynamic_calibrated and not kwargs.get("allow_uncalibrated", False):
            raise RuntimeError("Cannot execute merge with uncalibrated weights in production.")

        if key is None:
            a_g = 0.0
        else:
            info = classify_tensor_detailed(key, self.total_layers)
            grp = info["group"]
            a_g = self.group_weights.get(grp, 0.0)

        # High-precision FP32 calculation
        u_f = theta_u.detach().to(torch.float32)
        s_f = theta_s.detach().to(torch.float32)

        delta = a_g * (s_f - u_f)

        # Apply per-region update norm constraint: ||delta|| / (||u|| + eps) <= rho_g
        norm_delta = float(torch.norm(delta).item())
        norm_u = float(torch.norm(u_f).item())
        current_r_g = norm_delta / (norm_u + self.eps)

        if current_r_g > self.rho_g:
            scaling = (self.rho_g * (norm_u + self.eps)) / (norm_delta + self.eps)
            scaling = min(scaling, 1.0)
            delta = delta * scaling

        out = (u_f + delta).to(theta_u.dtype)
        self.check_finite(out, "proposed_intervention_merge")
        return out
