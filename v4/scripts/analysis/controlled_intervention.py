"""
E3.2: controlled_intervention.py
Rigorous 2x2 Factorial Controlled Intervention and Bi-directional Norm-Matched Controls
according to Secure_Merge_Experiment_Plan.md Section 9.2 and Code Audit Directives (P1-02, P1-04).

Key Principles:
1. Exact Parameter-Count and Tensor-Type Matched Random Controls.
2. High-precision FP32/FP64 norm calculation.
3. Strict Shrinkage-Only norm matching (t = min(||delta_1||, ||delta_2||)).
"""

import os
import sys
import json
import random
import math
import argparse
from typing import Dict, Any, List, Optional, Tuple, Set
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis.intervention_mapper import classify_tensor_detailed


def compute_dict_l2_norm(delta_dict: Dict[str, torch.Tensor]) -> float:
    """Computes total L2 norm of delta state dict using FP64 accumulation."""
    norm_sq = 0.0
    for d in delta_dict.values():
        if d is not None and d.is_floating_point():
            d_f = d.detach().to(torch.float32)
            norm_sq += float(torch.sum(d_f ** 2).item())
    return norm_sq ** 0.5


def apply_per_region_norm_cap(
    delta_tensor: torch.Tensor,
    theta_u_tensor: torch.Tensor,
    rho_g: float = 0.05,
    eps: float = 1e-8,
) -> torch.Tensor:
    """Applies per-region/tensor norm cap strictly in FP32."""
    d_f = delta_tensor.detach().to(torch.float32)
    u_f = theta_u_tensor.detach().to(torch.float32)

    norm_delta = float(torch.norm(d_f).item())
    norm_u = float(torch.norm(u_f).item())
    current_r_g = norm_delta / (norm_u + eps)

    if current_r_g > rho_g:
        scaling = (rho_g * (norm_u + eps)) / (norm_delta + eps)
        # Never expand
        scaling = min(scaling, 1.0)
        return (d_f * scaling).to(delta_tensor.dtype)
    return delta_tensor


def scale_delta_to_target_norm(
    delta_dict: Dict[str, torch.Tensor],
    target_norm: float,
    eps: float = 1e-8,
) -> Dict[str, torch.Tensor]:
    """
    Scales down delta dictionary so its total L2 norm equals target_norm.
    Strict rule: Only shrink (scale_factor <= 1.0), never expand.
    """
    current_norm = compute_dict_l2_norm(delta_dict)
    if current_norm <= eps or target_norm <= eps:
        return {k: torch.zeros_like(v) for k, v in delta_dict.items()}

    scale_factor = target_norm / current_norm
    scale_factor = min(scale_factor, 1.0)

    scaled = {}
    for k, v in delta_dict.items():
        v_f = v.detach().to(torch.float32)
        scaled[k] = (v_f * scale_factor).to(v.dtype)
    return scaled


def sample_matched_random_keys(
    map_keys: Set[str],
    all_keys: List[str],
    state_dict_shapes: Dict[str, Tuple[int, ...]],
    total_layers: int = 32,
    seed: int = 42,
) -> Set[str]:
    """
    Samples control keys matching BOTH tensor type and parameter count exactly (P1-02).
    Groups keys by (module_type, shape). For each bucket used by map_keys,
    samples the exact same count from outside map_keys.
    """
    rng = random.Random(seed)

    # Classify all available keys into buckets: (module_type, shape)
    buckets: Dict[Tuple[str, Tuple[int, ...]], List[str]] = {}
    for k in all_keys:
        info = classify_tensor_detailed(k, total_layers=total_layers)
        bucket_key = (info["module_type"], state_dict_shapes[k])
        buckets.setdefault(bucket_key, []).append(k)

    # Count requirements from map_keys
    needed_counts: Dict[Tuple[str, Tuple[int, ...]], int] = {}
    for k in map_keys:
        info = classify_tensor_detailed(k, total_layers=total_layers)
        b_key = (info["module_type"], state_dict_shapes[k])
        needed_counts[b_key] = needed_counts.get(b_key, 0) + 1

    selected_control_keys = set()

    for b_key, count in needed_counts.items():
        # Candidate pool: all keys in this bucket NOT in map_keys
        candidates = [k for k in buckets.get(b_key, []) if k not in map_keys]
        if len(candidates) < count:
            raise ValueError(
                f"CONTROL_MATCH_FAILED: Cannot find {count} available tensors of type/shape {b_key}. "
                f"Available pool has only {len(candidates)}."
            )
        sampled = rng.sample(candidates, count)
        selected_control_keys.update(sampled)

    # Final assertion: total keys and parameter counts must match exactly
    n_params_map = sum(math.prod(state_dict_shapes[k]) for k in map_keys)
    n_params_control = sum(math.prod(state_dict_shapes[k]) for k in selected_control_keys)
    assert len(selected_control_keys) == len(map_keys), "Key count mismatch in control sampling!"
    assert n_params_control == n_params_map, f"Parameter count mismatch! Map: {n_params_map}, Control: {n_params_control}"

    return selected_control_keys


def build_single_controlled_condition(
    condition_name: str,
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    beneficial_groups: List[str],
    common_alpha: float = 0.5,
    rho_g: float = 0.05,
    seed: int = 42,
    total_layers: int = 32,
) -> Tuple[Dict[str, torch.Tensor], float]:
    """
    Builds one specific condition on-demand to conserve memory (P1-04).
    Returns (intervened_state_dict, delta_l2_norm).
    """
    all_keys = [k for k, p in dict_u.items() if p.is_floating_point() and k in dict_s]
    shapes = {k: tuple(dict_u[k].shape) for k in all_keys}

    beneficial_set = set(beneficial_groups)
    map_keys = set(k for k in all_keys if classify_tensor_detailed(k, total_layers)["group"] in beneficial_set)

    raw_delta = {}
    for k in all_keys:
        u_f = dict_u[k].detach().to(torch.float32)
        s_f = dict_s[k].detach().to(torch.float32)
        raw_delta[k] = common_alpha * (s_f - u_f)

    # Condition A: Map + Common
    delta_A = {k: (raw_delta[k] if k in map_keys else torch.zeros_like(dict_u[k])) for k in all_keys}
    norm_A = compute_dict_l2_norm(delta_A)

    # Condition C: Map + Capped
    delta_C = {}
    for k in all_keys:
        if k in map_keys:
            delta_C[k] = apply_per_region_norm_cap(raw_delta[k], dict_u[k], rho_g=rho_g)
        else:
            delta_C[k] = torch.zeros_like(dict_u[k])
    norm_C = compute_dict_l2_norm(delta_C)

    target_delta = None

    if condition_name == "Condition_A_Map_Common":
        target_delta = delta_A
    elif condition_name == "Condition_C_Map_Capped":
        target_delta = delta_C
    elif condition_name == "Control_A_Scaled_to_C_Norm":
        target_delta = scale_delta_to_target_norm(delta_A, norm_C)
    elif condition_name == "Control_Full_Merge":
        target_delta = raw_delta
    elif condition_name == "Control_Full_Matched_to_A_Norm":
        target_delta = scale_delta_to_target_norm(raw_delta, norm_A)
    elif condition_name == "Control_Full_Matched_to_C_Norm":
        target_delta = scale_delta_to_target_norm(raw_delta, norm_C)
    elif "Random" in condition_name:
        random_keys = sample_matched_random_keys(map_keys, all_keys, shapes, total_layers=total_layers, seed=seed)
        delta_B = {k: (raw_delta[k] if k in random_keys else torch.zeros_like(dict_u[k])) for k in all_keys}
        delta_D = {
            k: (apply_per_region_norm_cap(raw_delta[k], dict_u[k], rho_g=rho_g) if k in random_keys else torch.zeros_like(dict_u[k]))
            for k in all_keys
        }
        norm_D = compute_dict_l2_norm(delta_D)

        if "Condition_B" in condition_name:
            target_delta = delta_B
        elif "Condition_D" in condition_name:
            target_delta = delta_D
        elif "Control_B_Scaled" in condition_name:
            target_delta = scale_delta_to_target_norm(delta_B, norm_D)

    if target_delta is None:
        raise ValueError(f"Unknown condition name: {condition_name}")

    actual_norm = compute_dict_l2_norm(target_delta)
    result_dict = {k: (dict_u[k].detach().to(torch.float32) + target_delta[k]).to(dict_u[k].dtype) for k in all_keys}
    return result_dict, actual_norm


def main():
    parser = argparse.ArgumentParser(description="E3.2: Controlled Intervention Builder CLI")
    parser.add_argument("--model-u", type=str, required=True, help="Domain model path (theta_u)")
    parser.add_argument("--model-s", type=str, required=True, help="Safety model path (theta_s)")
    parser.add_argument("--condition", type=str, required=True, help="Condition name to generate")
    parser.add_argument("--beneficial-groups", type=str, nargs="+", default=["group3_layers_mid_deep"], help="Beneficial groups from E3.1")
    parser.add_argument("--alpha", type=float, default=0.5, help="Common alpha")
    parser.add_argument("--rho-g", type=float, default=0.05, help="Per-region norm cap")
    parser.add_argument("--seed", type=int, default=42, help="Mask seed for random control")
    parser.add_argument("--output-file", type=str, required=True, help="Output .pt checkpoint file")
    args = parser.parse_args()

    from analysis.characteristic_analyzer import load_model_weights_dict

    print(f"Loading models to generate condition: {args.condition}...")
    dict_u = load_model_weights_dict(args.model_u)
    dict_s = load_model_weights_dict(args.model_s)

    result_dict, norm = build_single_controlled_condition(
        condition_name=args.condition,
        dict_u=dict_u,
        dict_s=dict_s,
        beneficial_groups=args.beneficial_groups,
        common_alpha=args.alpha,
        rho_g=args.rho_g,
        seed=args.seed,
    )

    print(f"Generated {args.condition} with delta L2 Norm: {norm:.6f}")
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    torch.save(result_dict, args.output_file)
    print(f"Saved to {args.output_file}")


if __name__ == "__main__":
    main()
