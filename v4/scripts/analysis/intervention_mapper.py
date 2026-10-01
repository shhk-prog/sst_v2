"""
E3.1: intervention_mapper.py
Generates behavioral intervention parameter maps by perturbing disjoint model parameter groups according to
Secure_Merge_Experiment_Plan.md Section 9.1 and Code Audit Remediation (P0-04, P1-02).

Key Principles:
1. Strict tensor group classification (no ambiguous fallback to embed/head).
2. Production CLI that loads real weights and builds intervention checkpoints one condition at a time.
3. Toy random tensor code isolated to tests/.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
import torch


def classify_tensor_detailed(key: str, total_layers: int = 32) -> Dict[str, str]:
    """
    Strictly classifies a parameter tensor by its architectural group and module type.
    Returns:
        {"group": group_name, "module_type": module_type}
    """
    key_lower = key.lower()

    # Module type
    if "norm" in key_lower:
        mtype = "norm"
    elif any(x in key_lower for x in ["q_proj", "k_proj", "v_proj", "o_proj", "self_attn", "attn"]):
        mtype = "attention"
    elif any(x in key_lower for x in ["gate_proj", "up_proj", "down_proj", "mlp"]):
        mtype = "mlp"
    elif "embed_tokens" in key_lower or "wte" in key_lower:
        mtype = "embed"
    elif "lm_head" in key_lower:
        mtype = "lm_head"
    else:
        mtype = "other"

    # Group classification
    if mtype == "norm":
        return {"group": "group5_norms", "module_type": mtype}
    if mtype == "embed":
        return {"group": "group6_embed", "module_type": mtype}
    if mtype == "lm_head":
        return {"group": "group6_head", "module_type": mtype}

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
            grp = "group1_layers_shallow"
        elif layer_idx < quarter * 2:
            grp = "group2_layers_mid_shallow"
        elif layer_idx < quarter * 3:
            grp = "group3_layers_mid_deep"
        else:
            grp = "group4_layers_deep"
        return {"group": grp, "module_type": mtype}

    return {"group": "unclassified", "module_type": mtype}


def apply_single_condition_intervention(
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    target_groups: List[str],
    alpha: float,
    total_layers: int = 32,
) -> Dict[str, torch.Tensor]:
    """
    Applies intervention for specified groups at scalar alpha in FP32 precision,
    returning a single intervened state dict.
    theta^(g, a) = theta_u + a * (theta_s - theta_u)
    """
    target_set = set(target_groups)
    intervened = {}

    for key, p_u in dict_u.items():
        p_s = dict_s.get(key)
        if p_s is None or not p_u.is_floating_point() or p_u.shape != p_s.shape:
            intervened[key] = p_u.clone()
            continue

        info = classify_tensor_detailed(key, total_layers=total_layers)
        if info["group"] in target_set:
            # High-precision delta calculation
            u_f = p_u.detach().to(torch.float32)
            s_f = p_s.detach().to(torch.float32)
            delta = alpha * (s_f - u_f)
            intervened[key] = (u_f + delta).to(p_u.dtype)
        else:
            intervened[key] = p_u.clone()

    return intervened


def main():
    parser = argparse.ArgumentParser(description="E3.1: Intervention Mapper CLI")
    parser.add_argument("--model-u", type=str, required=True, help="Domain model path (theta_u)")
    parser.add_argument("--model-s", type=str, required=True, help="Safety model path (theta_s)")
    parser.add_argument("--condition", type=str, required=True, help="Condition name (e.g. group3_layers_mid_deep_alpha_0.2)")
    parser.add_argument("--alpha", type=float, default=0.2, help="Intervention intensity alpha")
    parser.add_argument("--groups", type=str, nargs="+", required=True, help="Target groups to intervene")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory to save intervened weights")
    args = parser.parse_args()

    from analysis.characteristic_analyzer import load_model_weights_dict

    print(f"Loading models for condition {args.condition}...")
    dict_u = load_model_weights_dict(args.model_u)
    dict_s = load_model_weights_dict(args.model_s)

    print(f"Applying intervention for groups {args.groups} with alpha={args.alpha}...")
    intervened = apply_single_condition_intervention(dict_u, dict_s, args.groups, alpha=args.alpha)

    os.makedirs(args.output_dir, exist_ok=True)
    out_file = os.path.join(args.output_dir, f"{args.condition}.pt")
    torch.save(intervened, out_file)
    print(f"Saved intervened checkpoint to {out_file}")


if __name__ == "__main__":
    main()
