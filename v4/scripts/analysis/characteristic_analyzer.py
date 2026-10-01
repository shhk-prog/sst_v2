"""
E2: characteristic_analyzer.py
Measures physical weight properties and correlates them with behavioral outcomes according to
Secure_Merge_Experiment_Plan.md Section 8.

Properties measured:
1. Update Magnitude & Concentration:
   r_g = ||theta_m,g - theta_u,g|| / (||theta_u,g|| + eps)
   Overall norm, max layer norm, per-layer/per-module profile.
2. Selectivity:
   Non-zero update ratio, mask coverage.
3. Conflict & Importance:
   Cosine similarity between tau_s and tau_u: cos(tau_s, tau_u)
   Sign conflict ratio: fraction of coordinates where sign(tau_s) != sign(tau_u) and both non-zero.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
import torch


def compute_tensor_characteristics(
    theta_m: torch.Tensor,
    theta_u: torch.Tensor,
    theta_s: Optional[torch.Tensor] = None,
    theta_0: Optional[torch.Tensor] = None,
    eps: float = 1e-8,
) -> Dict[str, float]:
    delta_m_u = theta_m - theta_u
    norm_delta = torch.norm(delta_m_u).item()
    norm_u = torch.norm(theta_u).item()

    # Relative update magnitude r_g
    r_g = norm_delta / (norm_u + eps)

    # Selectivity: non-zero fraction (threshold at 1e-7)
    non_zero_ratio = (delta_m_u.abs() > 1e-7).float().mean().item()

    metrics = {
        "norm_delta": norm_delta,
        "norm_u": norm_u,
        "relative_update_r_g": r_g,
        "non_zero_ratio": non_zero_ratio,
    }

    # Conflict metrics if tau_s and tau_u can be computed
    if theta_s is not None and theta_0 is not None:
        tau_u = theta_u - theta_0
        tau_s = theta_s - theta_0
        norm_tau_u = torch.norm(tau_u).item()
        norm_tau_s = torch.norm(tau_s).item()

        if norm_tau_u > 1e-8 and norm_tau_s > 1e-8:
            cos_sim = (torch.sum(tau_u * tau_s) / (norm_tau_u * norm_tau_s)).item()
            metrics["cosine_similarity_tau"] = cos_sim

            # Sign conflict
            s_u = torch.sign(tau_u)
            s_s = torch.sign(tau_s)
            active = (s_u != 0) & (s_s != 0)
            if active.any():
                conflict_ratio = (active & (s_u != s_s)).float().sum().item() / active.float().sum().item()
                metrics["sign_conflict_ratio"] = conflict_ratio

    return metrics


def analyze_state_dicts(
    dict_m: Dict[str, torch.Tensor],
    dict_u: Dict[str, torch.Tensor],
    dict_s: Optional[Dict[str, torch.Tensor]] = None,
    dict_0: Optional[Dict[str, torch.Tensor]] = None,
) -> Dict[str, Any]:
    layer_stats = {}
    overall_delta_sq = 0.0
    overall_u_sq = 0.0
    total_params = 0
    total_non_zero_updates = 0

    for key, p_m in dict_m.items():
        if not p_m.is_floating_point():
            continue
        p_u = dict_u.get(key)
        if p_u is None or p_u.shape != p_m.shape:
            continue
        p_s = dict_s.get(key) if dict_s else None
        p_0 = dict_0.get(key) if dict_0 else None

        t_stats = compute_tensor_characteristics(p_m, p_u, p_s, p_0)
        layer_stats[key] = t_stats

        # Accumulate overall stats
        d = p_m - p_u
        overall_delta_sq += (d ** 2).sum().item()
        overall_u_sq += (p_u ** 2).sum().item()
        total_params += p_m.numel()
        total_non_zero_updates += (d.abs() > 1e-7).sum().item()

    overall_r_g = (overall_delta_sq ** 0.5) / ((overall_u_sq ** 0.5) + 1e-8)
    overall_sparsity = float(total_non_zero_updates / max(total_params, 1))

    # Identify layer of maximum concentration
    max_key = max(layer_stats.keys(), key=lambda k: layer_stats[k]["relative_update_r_g"]) if layer_stats else None
    max_r_g = layer_stats[max_key]["relative_update_r_g"] if max_key else 0.0

    return {
        "overall_relative_update_r_g": overall_r_g,
        "overall_update_norm": overall_delta_sq ** 0.5,
        "overall_non_zero_ratio": overall_sparsity,
        "max_update_layer": max_key,
        "max_update_layer_r_g": max_r_g,
        "concentration_ratio": max_r_g / (overall_r_g + 1e-8),
        "per_tensor_stats": layer_stats,
    }


if __name__ == "__main__":
    torch.manual_seed(42)
    # Smoke test on synthetic state dict
    theta_0 = torch.randn(32, 32)
    theta_u = theta_0 + torch.randn(32, 32) * 0.1
    theta_s = theta_0 + torch.randn(32, 32) * 0.1
    theta_m = theta_u + torch.randn(32, 32) * 0.05

    d_0 = {"layer.0.weight": theta_0, "layer.1.weight": theta_0}
    d_u = {"layer.0.weight": theta_u, "layer.1.weight": theta_u}
    d_s = {"layer.0.weight": theta_s, "layer.1.weight": theta_s}
    d_m = {"layer.0.weight": theta_m, "layer.1.weight": theta_u + (theta_s - theta_u) * 0.8}

    report = analyze_state_dicts(d_m, d_u, d_s, d_0)
    print("E2 Characteristic Analysis Report Summary:")
    print(f"  Overall r_g: {report['overall_relative_update_r_g']:.4f}")
    print(f"  Overall non-zero ratio: {report['overall_non_zero_ratio']:.4f}")
    print(f"  Max concentration layer: {report['max_update_layer']} (r_g={report['max_update_layer_r_g']:.4f})")
    print(f"  Concentration ratio (max/overall): {report['concentration_ratio']:.2f}")
