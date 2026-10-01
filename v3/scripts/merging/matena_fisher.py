"""
Matena Fisher-Weighted Averaging for Llama-2 / CausalLM.

Re-implementation of the method from:
  Matena & Wortsman, "Merging Models with Fisher-Weighted Averaging", NeurIPS 2022.
  Official repo: https://github.com/mmatena/model_merging

The official implementation targets TensorFlow + TFBert/TFRoberta + GLUE.
This module re-implements the same formula for PyTorch CausalLM (Llama-2).

Formula:
    theta_merged = sum_i(F_i * theta_i) / (sum_i F_i + epsilon)

    where F_i is the diagonal Fisher Information Matrix for model i,
    and theta_i are the model parameters.

Design decisions (recorded in merge_metadata.json for reproducibility):
  - Target params  : TARGET_MODULE_KEYWORDS only (q/k/v/o/gate/up/down proj).
                     Non-target params are kept from base_model (conservative design).
  - FIM cache      : Reuses existing cache/fim/*.pt (target_modules_only scope).
                     NOTE: If changing to all_params scope, FIM must be recomputed.
  - Normalization  : normalize_fishers=True by default (global L2 norm per model,
                     as recommended by Matena et al.).
"""

import math
import torch
from tqdm import tqdm


# Must match TARGET_MODULE_KEYWORDS in merge.py.
TARGET_MODULE_KEYWORDS = [
    "q_proj",
    "v_proj",
    "k_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def is_target_weight(name: str) -> bool:
    """Return True if the parameter name is a target module weight."""
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def _l2_norm_of_fim(fim: dict) -> float:
    """Compute the global L2 norm of a FIM dict (target params only)."""
    sq_sum = 0.0
    for name, tensor in fim.items():
        if is_target_weight(name):
            sq_sum += float(tensor.float().pow(2).sum().item())
    return math.sqrt(sq_sum) if sq_sum > 0.0 else 1.0


def run_matena_fisher(
    base_model,
    all_models: dict,
    all_fim: dict,
    fisher_floor: float = 1e-6,
    normalize_fishers: bool = True,
) -> tuple:
    """
    Merge models using Fisher-Weighted Averaging (Matena & Wortsman, NeurIPS 2022).

    Formula (per parameter element-wise):
        theta_merged = sum_i(F_i * theta_i) / (sum_i F_i + epsilon)

    All models are treated equally (symmetric), unlike the asymmetric fisher_weighted
    baseline which separates safety FIM and utility FIM roles.

    Args:
        base_model: The base (unmodified) model. Used for:
                    - Non-target module params (conservative: kept as-is from base).
                    - Shape reference for parameter alignment checks.
        all_models: Dict of {model_name: nn.Module}.
                    E.g. {"safety": safe_model, "math": util_model}.
                    All models are treated with equal status.
        all_fim: Dict of {model_name: {param_name: Tensor}}.
                 FIM tensors should be on CPU and cover target_modules only
                 (compatible with existing cache/fim/*.pt format).
                 If a model's FIM is missing for a specific param, fisher_floor
                 is used as a uniform fallback weight.
        fisher_floor: Small constant added to denominator for numerical stability.
                      Also used as minimum FIM value after normalization.
        normalize_fishers: If True, each model's FIM is divided by its global L2 norm
                           before accumulation. Recommended by Matena et al.

    Returns:
        merged_state_dict (dict[str, Tensor]): Merged model state dict.
            - Target module params: FIM-weighted average across all models.
            - Non-target params: copied from base_model (conservative design).
        matena_info (dict): Debug / metadata information for merge_metadata.json.
            Keys: normalized, fisher_floor, num_target_params_merged,
                  num_base_params_kept, model_names, norm_constants.
    """
    model_names = list(all_models.keys())
    if len(model_names) < 2:
        raise ValueError(
            f"[matena_fisher] Need at least 2 models to merge, got {len(model_names)}."
        )

    print(f"[matena_fisher] Merging {len(model_names)} models: {model_names}")
    print(f"[matena_fisher] normalize_fishers={normalize_fishers}, fisher_floor={fisher_floor}")

    # --- Collect state dicts (CPU) ---
    state_dicts = {}
    for name, model in all_models.items():
        state_dicts[name] = {k: v.cpu() for k, v in model.state_dict().items()}
    base_state = {k: v.cpu() for k, v in base_model.state_dict().items()}

    # --- Compute per-model FIM L2 normalization constants ---
    norm_constants = {}
    for name in model_names:
        fim = all_fim.get(name, {})
        if normalize_fishers:
            norm_c = _l2_norm_of_fim(fim)
            print(f"[matena_fisher]   FIM L2 norm for '{name}': {norm_c:.6f}")
        else:
            norm_c = 1.0
        norm_constants[name] = norm_c

    # --- Merge parameters ---
    merged_state_dict = {}
    num_target_params = 0
    num_base_params = 0

    for param_name in tqdm(list(base_state.keys()), desc="[matena_fisher] Merging"):
        base_tensor = base_state[param_name]

        if not is_target_weight(param_name):
            # Non-target params: copy from base_model.
            # This is a conservative design choice; recorded in merge_metadata.json.
            merged_state_dict[param_name] = base_tensor.clone()
            num_base_params += 1
            continue

        # Accumulate Matena formula: theta* = sum(F_i * theta_i) / sum(F_i + eps)
        numerator = torch.zeros_like(base_tensor, dtype=torch.float32)
        denominator = torch.zeros_like(base_tensor, dtype=torch.float32)

        for model_name in model_names:
            theta_i = state_dicts[model_name].get(param_name)
            if theta_i is None or theta_i.shape != base_tensor.shape:
                continue

            theta_i = theta_i.float()

            fim_dict = all_fim.get(model_name, {})
            f_i_raw = fim_dict.get(param_name)

            if f_i_raw is None:
                # FIM missing for this param: use uniform (floor) weight.
                f_i = torch.full_like(base_tensor, fisher_floor, dtype=torch.float32)
            else:
                f_i = f_i_raw.float()
                # Apply global L2 normalization.
                norm_c = norm_constants[model_name]
                if norm_c > 0.0:
                    f_i = f_i / norm_c
                # Clamp to floor for stability.
                f_i = torch.clamp(f_i, min=fisher_floor)

            numerator += f_i * theta_i
            denominator += f_i

        # Add epsilon to denominator for final safety.
        denominator = torch.clamp(denominator, min=fisher_floor)
        merged = numerator / denominator
        merged_state_dict[param_name] = merged.to(dtype=base_tensor.dtype)
        num_target_params += 1

    matena_info = {
        "method": "matena_fisher",
        "normalized": normalize_fishers,
        "fisher_floor": fisher_floor,
        "num_target_params_merged": num_target_params,
        "num_base_params_kept": num_base_params,
        "model_names": model_names,
        "norm_constants": {k: float(v) for k, v in norm_constants.items()},
    }

    print(
        f"[matena_fisher] Done. "
        f"target_params_merged={num_target_params}, "
        f"base_params_kept={num_base_params}"
    )

    return merged_state_dict, matena_info
