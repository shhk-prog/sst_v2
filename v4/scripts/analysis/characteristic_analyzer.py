"""
E2: characteristic_analyzer.py
Measures physical weight properties and correlates them with behavioral outcomes according to
Secure_Merge_Experiment_Plan.md Section 8 and Secure Merge v4 Code Audit Directives (P0-04, P1-04).

Key Safety & Precision Features:
1. High-precision norm & dot product computations in FP32/FP64 to prevent FP16 overflow/underflow.
2. Direct safetensors/PyTorch checkpoint loading for real LLM weights.
3. Strict finite-value validation on all outputs.
"""

import os
import sys
import json
import math
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
    """
    Computes characteristics for a single tensor using FP32/FP64 precision.
    """
    # Convert to FP32 to prevent FP16 squared-norm overflow
    m_f = theta_m.detach().to(torch.float32)
    u_f = theta_u.detach().to(torch.float32)

    delta_m_u = m_f - u_f
    norm_delta = float(torch.norm(delta_m_u).item())
    norm_u = float(torch.norm(u_f).item())

    # Check finite
    if not (math.isfinite(norm_delta) and math.isfinite(norm_u)):
        raise ValueError(f"Non-finite norm encountered: norm_delta={norm_delta}, norm_u={norm_u}")

    # Relative update magnitude r_g
    r_g = norm_delta / (norm_u + eps)

    # Selectivity: non-zero fraction (threshold at 1e-7 in FP32)
    non_zero_ratio = float((delta_m_u.abs() > 1e-7).to(torch.float32).mean().item())

    metrics = {
        "norm_delta": norm_delta,
        "norm_u": norm_u,
        "relative_update_r_g": r_g,
        "non_zero_ratio": non_zero_ratio,
    }

    # Conflict metrics if tau_s and tau_u can be computed
    if theta_s is not None and theta_0 is not None:
        s_f = theta_s.detach().to(torch.float32)
        z_f = theta_0.detach().to(torch.float32)

        tau_u = u_f - z_f
        tau_s = s_f - z_f
        norm_tau_u = float(torch.norm(tau_u).item())
        norm_tau_s = float(torch.norm(tau_s).item())

        if norm_tau_u > 1e-8 and norm_tau_s > 1e-8:
            # High-precision dot product
            dot_prod = float(torch.sum(tau_u * tau_s).item())
            cos_sim = dot_prod / (norm_tau_u * norm_tau_s)
            # Clamp to [-1.0, 1.0] for precision artifacts
            cos_sim = max(-1.0, min(1.0, cos_sim))
            metrics["cosine_similarity_tau"] = cos_sim

            # Sign conflict ratio
            s_u = torch.sign(tau_u)
            s_s = torch.sign(tau_s)
            active = (s_u != 0) & (s_s != 0)
            if active.any():
                conflict_ratio = float((active & (s_u != s_s)).to(torch.float32).sum().item()) / float(active.to(torch.float32).sum().item())
                metrics["sign_conflict_ratio"] = conflict_ratio

    return metrics


def analyze_state_dicts(
    dict_m: Dict[str, torch.Tensor],
    dict_u: Dict[str, torch.Tensor],
    dict_s: Optional[Dict[str, torch.Tensor]] = None,
    dict_0: Optional[Dict[str, torch.Tensor]] = None,
) -> Dict[str, Any]:
    """
    Analyzes full model state dicts.
    Global accumulations are computed in FP64 (Python float) to prevent overflow.
    """
    layer_stats = {}
    overall_delta_sq = 0.0  # FP64 accumulation
    overall_u_sq = 0.0
    total_params = 0
    total_non_zero_updates = 0

    common_keys = sorted(list(set(dict_m.keys()) & set(dict_u.keys())))

    for key in common_keys:
        p_m = dict_m[key]
        p_u = dict_u[key]

        if not p_m.is_floating_point():
            continue
        if p_m.shape != p_u.shape:
            continue

        p_s = dict_s.get(key) if dict_s else None
        p_0 = dict_0.get(key) if dict_0 else None

        t_stats = compute_tensor_characteristics(p_m, p_u, p_s, p_0)
        layer_stats[key] = t_stats

        # Accumulate overall stats in FP64
        m_f = p_m.detach().to(torch.float32)
        u_f = p_u.detach().to(torch.float32)
        d = m_f - u_f

        d_sq = float(torch.sum(d ** 2).item())
        u_sq = float(torch.sum(u_f ** 2).item())
        overall_delta_sq += d_sq
        overall_u_sq += u_sq
        total_params += p_m.numel()
        total_non_zero_updates += int((d.abs() > 1e-7).sum().item())

    overall_delta_norm = overall_delta_sq ** 0.5
    overall_u_norm = overall_u_sq ** 0.5
    overall_r_g = overall_delta_norm / (overall_u_norm + 1e-8)
    overall_sparsity = float(total_non_zero_updates / max(total_params, 1))

    # Identify layer/tensor of maximum concentration
    max_key = max(layer_stats.keys(), key=lambda k: layer_stats[k]["relative_update_r_g"]) if layer_stats else None
    max_r_g = layer_stats[max_key]["relative_update_r_g"] if max_key else 0.0

    return {
        "overall_relative_update_r_g": overall_r_g,
        "overall_update_norm": overall_delta_norm,
        "overall_u_norm": overall_u_norm,
        "overall_non_zero_ratio": overall_sparsity,
        "total_analyzed_params": total_params,
        "total_analyzed_tensors": len(layer_stats),
        "max_update_layer": max_key,
        "max_update_layer_r_g": max_r_g,
        "concentration_ratio": max_r_g / (overall_r_g + 1e-8),
        "per_tensor_stats": layer_stats,
    }


def load_model_weights_dict(model_path_or_name: str) -> Dict[str, torch.Tensor]:
    """
    Safely loads state dict from directory containing safetensors or bin.
    """
    from transformers import AutoModelForCausalLM

    if not os.path.exists(model_path_or_name):
        raise FileNotFoundError(f"Model path does not exist: {model_path_or_name}")

    # Check for safetensors first
    st_files = [f for f in os.listdir(model_path_or_name) if f.endswith(".safetensors")]
    if st_files:
        from safetensors.torch import load_file
        state_dict = {}
        for sf in sorted(st_files):
            sf_path = os.path.join(model_path_or_name, sf)
            state_dict.update(load_file(sf_path))
        return state_dict

    # Check for bin files
    bin_files = [f for f in os.listdir(model_path_or_name) if f.endswith(".bin")]
    if bin_files:
        state_dict = {}
        for bf in sorted(bin_files):
            bf_path = os.path.join(model_path_or_name, bf)
            state_dict.update(torch.load(bf_path, map_location="cpu"))
        return state_dict

    # Fallback to HF loader
    model = AutoModelForCausalLM.from_pretrained(model_path_or_name, torch_dtype=torch.float16, low_cpu_mem_usage=True)
    return model.state_dict()


def main():
    parser = argparse.ArgumentParser(description="E2: Weight Characteristic Analyzer (Production CLI)")
    parser.add_argument("--model-m", type=str, required=True, help="Path to merged candidate model checkpoint")
    parser.add_argument("--model-u", type=str, required=True, help="Path to unaligned domain model checkpoint (theta_u)")
    parser.add_argument("--model-s", type=str, default=None, help="Path to aligned safety model checkpoint (theta_s)")
    parser.add_argument("--model-0", type=str, default=None, help="Path to base model checkpoint (theta_0)")
    parser.add_argument("--output", type=str, default="v4/results/e2_characteristics.json", help="Output JSON path")
    args = parser.parse_args()

    print(f"Loading merged model from: {args.model_m}")
    dict_m = load_model_weights_dict(args.model_m)

    print(f"Loading domain model from: {args.model_u}")
    dict_u = load_model_weights_dict(args.model_u)

    dict_s = load_model_weights_dict(args.model_s) if args.model_s else None
    dict_0 = load_model_weights_dict(args.model_0) if args.model_0 else None

    print(f"Analyzing weight characteristics across {len(dict_m)} tensors...")
    report = analyze_state_dicts(dict_m, dict_u, dict_s, dict_0)

    print("E2 Characteristic Analysis Completed:")
    print(f"  Overall r_g: {report['overall_relative_update_r_g']:.6f}")
    print(f"  Overall Update Norm: {report['overall_update_norm']:.4f}")
    print(f"  Non-zero ratio: {report['overall_non_zero_ratio']:.4f}")
    print(f"  Max concentration layer: {report['max_update_layer']} (r_g={report['max_update_layer_r_g']:.6f})")
    print(f"  Concentration ratio: {report['concentration_ratio']:.2f}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved full report to {args.output}")


if __name__ == "__main__":
    main()
