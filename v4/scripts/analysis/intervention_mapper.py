"""
E3.1: intervention_mapper.py
Generates behavioral intervention maps by perturbing 6 disjoint model parameter groups according to
Secure_Merge_Experiment_Plan.md Section 9.1.

Groups:
- Group 1: Transformer Layers 0-7 (excluding Norms)
- Group 2: Transformer Layers 8-15 (excluding Norms)
- Group 3: Transformer Layers 16-23 (excluding Norms)
- Group 4: Transformer Layers 24-31 (excluding Norms)
- Group 5: All LayerNorm / RMSNorm weights
- Group 6: Embedding and LM Head weights

Intervention Formula:
theta^(g, a) = theta_u + a * P_g(theta_s - theta_u),  a in {0.2, 0.6}
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
import torch


def classify_tensor_group(key: str, total_layers: int = 32) -> str:
    key_lower = key.lower()

    # Norm group
    if "norm" in key_lower:
        return "group5_norms"

    # Embed and Head group
    if "embed_tokens" in key_lower or "lm_head" in key_lower:
        return "group6_embed_head"

    # Transformer layers
    parts = key.split(".")
    layer_idx = None
    for i, p in enumerate(parts):
        if p == "layers" and i + 1 < len(parts) and parts[i + 1].isdigit():
            layer_idx = int(parts[i + 1])
            break

    if layer_idx is not None:
        quarter = max(1, total_layers // 4)
        if layer_idx < quarter:
            return "group1_layers_shallow"
        elif layer_idx < quarter * 2:
            return "group2_layers_mid_shallow"
        elif layer_idx < quarter * 3:
            return "group3_layers_mid_deep"
        else:
            return "group4_layers_deep"

    return "group6_embed_head"


def create_intervention_state_dict(
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    active_groups: List[str],
    alpha: float = 0.2,
    total_layers: int = 32,
) -> Dict[str, torch.Tensor]:
    active_set = set(active_groups)
    intervened = {}

    for key, p_u in dict_u.items():
        p_s = dict_s.get(key)
        if p_s is None or not p_u.is_floating_point() or p_u.shape != p_s.shape:
            intervened[key] = p_u.clone()
            continue

        grp = classify_tensor_group(key, total_layers=total_layers)
        if grp in active_set:
            # theta^(g, a) = theta_u + a * (theta_s - theta_u)
            intervened[key] = p_u + alpha * (p_s - p_u)
        else:
            intervened[key] = p_u.clone()

    return intervened


def build_all_single_group_interventions(
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    alphas: List[float] = [0.2, 0.6],
    total_layers: int = 32,
) -> Dict[str, Dict[str, torch.Tensor]]:
    groups = [
        "group1_layers_shallow",
        "group2_layers_mid_shallow",
        "group3_layers_mid_deep",
        "group4_layers_deep",
        "group5_norms",
        "group6_embed_head",
    ]
    interventions = {}

    # 1. Single group interventions: 6 groups x 2 alphas = 12 conditions
    for grp in groups:
        for a in alphas:
            cond_name = f"{grp}_alpha_{a}"
            interventions[cond_name] = create_intervention_state_dict(
                dict_u, dict_s, [grp], alpha=a, total_layers=total_layers
            )

    # 2. Pre-specified group pairs to check interaction (e.g. Mid-deep + Norms, Deep + Embed)
    pair1 = ["group3_layers_mid_deep", "group5_norms"]
    pair2 = ["group4_layers_deep", "group2_layers_mid_shallow"]
    for pair, name in [(pair1, "pair_mid_deep_and_norms"), (pair2, "pair_deep_and_mid_shallow")]:
        for a in alphas:
            cond_name = f"{name}_alpha_{a}"
            interventions[cond_name] = create_intervention_state_dict(
                dict_u, dict_s, pair, alpha=a, total_layers=total_layers
            )

    return interventions


if __name__ == "__main__":
    torch.manual_seed(42)
    # Synthetic smoke test
    u = {"model.layers.5.self_attn.q_proj.weight": torch.randn(8, 8), "model.norm.weight": torch.randn(8)}
    s = {"model.layers.5.self_attn.q_proj.weight": torch.randn(8, 8), "model.norm.weight": torch.randn(8)}

    all_conds = build_all_single_group_interventions(u, s, alphas=[0.2, 0.6], total_layers=32)
    print(f"Generated {len(all_conds)} controlled intervention conditions successfully.")
    for k in list(all_conds.keys())[:5]:
        print(f"  Condition: {k}")
