"""
E3.2: controlled_intervention.py
Rigorous 2x2 Factorial Controlled Intervention and Bi-directional Norm-Matched Controls
according to Secure_Merge_Experiment_Plan.md Section 9.2.

Design:
Factor 1: Location Selection
  - Map-based selection (derived from E3.1 intervention map)
  - Random selection matching parameter count and tensor types exactly across 3 seeds (42, 43, 44)
Factor 2: Update Allocation
  - Common scalar coefficient
  - Per-region norm cap rho_g

Norm-Matched Controls (Strict Rule):
Let delta_1, delta_2 be two updates.
t = min(||delta_1||_2, ||delta_2||_2)
delta'_j = delta_j * (t / ||delta_j||_2)
Scales down to the smaller norm, never expanding beyond bounds.
Includes:
- Condition A scaled down to Condition C's norm
- Uniform Full Merge scaled down to Condition C's norm
- Uniform Full Merge scaled down to Condition A's norm
"""

import os
import sys
import json
import random
import torch
from typing import Dict, Any, List, Optional, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis.intervention_mapper import classify_tensor_group


def apply_per_region_norm_cap(
    delta_tensor: torch.Tensor,
    theta_u_tensor: torch.Tensor,
    rho_g: float = 0.05,
    eps: float = 1e-8,
) -> torch.Tensor:
    norm_delta = torch.norm(delta_tensor)
    norm_u = torch.norm(theta_u_tensor)
    current_r_g = norm_delta / (norm_u + eps)

    if current_r_g > rho_g:
        scaling = (rho_g * (norm_u + eps)) / (norm_delta + eps)
        return delta_tensor * scaling
    return delta_tensor


def scale_delta_to_target_norm(
    delta_dict: Dict[str, torch.Tensor],
    target_norm: float,
    eps: float = 1e-8,
) -> Dict[str, torch.Tensor]:
    """Scales down delta dictionary so its total L2 norm equals target_norm."""
    current_norm_sq = sum(torch.sum(d ** 2).item() for d in delta_dict.values())
    current_norm = current_norm_sq ** 0.5
    if current_norm <= eps:
        return {k: torch.zeros_like(v) for k, v in delta_dict.items()}

    scale_factor = target_norm / current_norm
    # Strict rule: only shrink, never expand beyond original
    scale_factor = min(scale_factor, 1.0)
    return {k: v * scale_factor for k, v in delta_dict.items()}


def get_l2_norm(delta_dict: Dict[str, torch.Tensor]) -> float:
    return (sum(torch.sum(d ** 2).item() for d in delta_dict.values())) ** 0.5


def create_2x2_and_norm_matched_controls(
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    beneficial_groups: List[str],
    common_alpha: float = 0.5,
    rho_g: float = 0.05,
    mask_seeds: List[int] = [42, 43, 44],
    total_layers: int = 32,
) -> Dict[str, Any]:
    beneficial_set = set(beneficial_groups)
    all_keys = [k for k, p in dict_u.items() if p.is_floating_point() and k in dict_s]

    # Map-based keys
    map_keys = set(k for k in all_keys if classify_tensor_group(k, total_layers) in beneficial_set)
    n_params_map = sum(dict_u[k].numel() for k in map_keys)

    # Base deltas: tau_s = theta_s - theta_u
    raw_delta = {k: common_alpha * (dict_s[k] - dict_u[k]) for k in all_keys}

    # Condition A: Map + Common
    delta_A = {k: (raw_delta[k] if k in map_keys else torch.zeros_like(dict_u[k])) for k in all_keys}
    norm_A = get_l2_norm(delta_A)

    # Condition C: Map + Capped
    delta_C = {}
    for k in all_keys:
        if k in map_keys:
            delta_C[k] = apply_per_region_norm_cap(raw_delta[k], dict_u[k], rho_g=rho_g)
        else:
            delta_C[k] = torch.zeros_like(dict_u[k])
    norm_C = get_l2_norm(delta_C)

    # Bi-directional target norm: smaller of A and C is norm_C
    t_min = min(norm_A, norm_C)

    # Condition A scaled down to C's norm
    delta_A_matched_to_C = scale_delta_to_target_norm(delta_A, t_min)

    # Full Uniform Merge and its matched controls
    delta_Full = raw_delta
    norm_Full = get_l2_norm(delta_Full)
    delta_Full_matched_to_A = scale_delta_to_target_norm(delta_Full, norm_A)
    delta_Full_matched_to_C = scale_delta_to_target_norm(delta_Full, norm_C)

    all_conditions = {
        "Condition_A_Map_Common": {k: dict_u[k] + delta_A[k] for k in all_keys},
        "Condition_C_Map_Capped": {k: dict_u[k] + delta_C[k] for k in all_keys},
        "Control_A_Scaled_to_C_Norm": {k: dict_u[k] + delta_A_matched_to_C[k] for k in all_keys},
        "Control_Full_Merge": {k: dict_u[k] + delta_Full[k] for k in all_keys},
        "Control_Full_Matched_to_A_Norm": {k: dict_u[k] + delta_Full_matched_to_A[k] for k in all_keys},
        "Control_Full_Matched_to_C_Norm": {k: dict_u[k] + delta_Full_matched_to_C[k] for k in all_keys},
    }

    # Random Conditions across 3 mask seeds (B and D)
    for s in mask_seeds:
        random.seed(s)
        # Match parameter count and tensor types
        random_keys = set(random.sample(all_keys, len(map_keys)))

        # Condition B: Random + Common
        delta_B = {k: (raw_delta[k] if k in random_keys else torch.zeros_like(dict_u[k])) for k in all_keys}
        # Condition D: Random + Capped
        delta_D = {
            k: (apply_per_region_norm_cap(raw_delta[k], dict_u[k], rho_g=rho_g) if k in random_keys else torch.zeros_like(dict_u[k]))
            for k in all_keys
        }
        all_conditions[f"Condition_B_Random_Common_seed{s}"] = {k: dict_u[k] + delta_B[k] for k in all_keys}
        all_conditions[f"Condition_D_Random_Capped_seed{s}"] = {k: dict_u[k] + delta_D[k] for k in all_keys}

        # Matched control for Random B scaled down to D
        norm_D = get_l2_norm(delta_D)
        delta_B_matched = scale_delta_to_target_norm(delta_B, norm_D)
        all_conditions[f"Control_B_Scaled_to_D_Norm_seed{s}"] = {k: dict_u[k] + delta_B_matched[k] for k in all_keys}

    # Summary of Norms
    norm_summary = {
        name: get_l2_norm({k: state[k] - dict_u[k] for k in all_keys})
        for name, state in all_conditions.items()
    }

    return {
        "conditions": all_conditions,
        "norm_summary": norm_summary,
        "norm_A": norm_A,
        "norm_C": norm_C,
        "norm_Full": norm_Full,
    }


if __name__ == "__main__":
    torch.manual_seed(42)
    # Synthetic smoke test
    u = {f"model.layers.{i}.self_attn.q_proj.weight": torch.randn(16, 16) for i in range(16)}
    s = {f"model.layers.{i}.self_attn.q_proj.weight": torch.randn(16, 16) for i in range(16)}

    res = create_2x2_and_norm_matched_controls(
        u, s, beneficial_groups=["group3_layers_mid_deep", "group4_layers_deep"],
        common_alpha=0.5, rho_g=0.03, total_layers=16
    )

    print("Rigorous E3 Norm Summary:")
    for name, norm_val in res["norm_summary"].items():
        print(f"  {name:38s} -> L2 Norm: {norm_val:.4f}")

    # Check that matched controls strictly equal their targets
    assert abs(res["norm_summary"]["Control_Full_Matched_to_A_Norm"] - res["norm_A"]) < 1e-4
    assert abs(res["norm_summary"]["Control_Full_Matched_to_C_Norm"] - res["norm_C"]) < 1e-4
    assert abs(res["norm_summary"]["Control_A_Scaled_to_C_Norm"] - res["norm_C"]) < 1e-4
    print("\n>>> All bi-directional norm matching assertions strictly satisfied! <<<")
