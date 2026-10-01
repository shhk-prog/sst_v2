import torch
from tqdm import tqdm

from mergers.utils import is_target_weight, get_layer_prior
from mergers.fim import get_fim_tensor


def merge_sst(
    base_model,
    util_models_dict,
    safe_model,
    method,
    sst_ratio,
    variant,
    mask_type,
    layer_wise,
    layer_prior,
    alpha,
    k_ratio,
    fim_b_dict=None,
    fim_h=None,
    norm_standardization=False,
    fisher_normalization=False,
    norm_clipping=False,
    max_norm_ratio=1.5,
):
    merged_state_dict = {}
    fisher_weight_stats = {}
    safe_state = safe_model.state_dict()
    util_states = {k: v.state_dict() for k, v in util_models_dict.items()}

    with torch.no_grad():
        for name, param_base in tqdm(list(base_model.named_parameters()), desc="Merging weights"):
            base_data = param_base.data

            if name not in safe_state:
                merged_state_dict[name] = base_data.clone()
                continue

            param_safe = safe_state[name].data.to(device=base_data.device, dtype=base_data.dtype)
            delta_safe = param_safe - base_data if param_safe.shape == base_data.shape else torch.zeros_like(base_data)
            param_safe_for_merge = base_data + delta_safe

            delta_utils = {}
            for u_name, u_state in util_states.items():
                if name not in u_state:
                    continue

                u_param = u_state[name].data.to(device=base_data.device, dtype=base_data.dtype)
                if u_param.shape == base_data.shape:
                    delta_utils[u_name] = u_param - base_data

            if not delta_utils:
                merged_state_dict[name] = base_data.clone()
                continue

            if norm_standardization:
                safe_norm = torch.linalg.norm(delta_safe)
                util_norms = {k: torch.linalg.norm(v) for k, v in delta_utils.items()}
                total_norm = safe_norm + sum(util_norms.values())
                avg_norm = total_norm / (1 + len(util_norms))
                
                if safe_norm > 0:
                    delta_safe = delta_safe * (avg_norm / safe_norm)
                for u_name in delta_utils:
                    if util_norms[u_name] > 0:
                        delta_utils[u_name] = delta_utils[u_name] * (avg_norm / util_norms[u_name])
                
                param_safe_for_merge = base_data + delta_safe

            delta_util_mean = torch.stack(list(delta_utils.values())).mean(dim=0)
            param_util_mean = base_data + delta_util_mean

            if method == "fisher_weighted":
                f_b = torch.zeros_like(base_data)

                if fim_b_dict:
                    for u_name in delta_utils:
                        if u_name in fim_b_dict:
                            f_b += get_fim_tensor(fim_b_dict[u_name], name, base_data)
                    f_b /= max(len(delta_utils), 1)

                f_h = get_fim_tensor(fim_h, name, base_data)
                denom = f_b + f_h + 1e-6

                w_util = f_b / denom
                w_safe = f_h / denom

                fisher_weight_stats[name] = {
                    "utility_weight_mean": float(w_util.float().mean().item()),
                    "utility_weight_std": float(w_util.float().std().item()),
                    "utility_weight_min": float(w_util.float().min().item()),
                    "utility_weight_max": float(w_util.float().max().item()),
                    "safety_weight_mean": float(w_safe.float().mean().item()),
                    "safety_weight_std": float(w_safe.float().std().item()),
                    "safety_weight_min": float(w_safe.float().min().item()),
                    "safety_weight_max": float(w_safe.float().max().item()),
                }

                merged_state_dict[name] = w_util * param_util_mean + w_safe * param_safe_for_merge
                continue

            if not is_target_weight(name):
                merged_state_dict[name] = param_util_mean + alpha * delta_safe
                continue

            w_layer = 1.0
            if layer_wise:
                for part in name.split("."):
                    if part.isdigit():
                        w_layer = get_layer_prior(
                            int(part),
                            getattr(base_model.config, "num_hidden_layers", 32),
                            layer_prior,
                        )
                        break

            if method == "diagonal_sst":
                f_b = torch.zeros_like(base_data)

                if fim_b_dict:
                    for u_name in delta_utils:
                        if u_name in fim_b_dict:
                            f_b += get_fim_tensor(fim_b_dict[u_name], name, base_data)
                    f_b /= max(len(delta_utils), 1)

                f_h = get_fim_tensor(fim_h, name, base_data)

                if fisher_normalization:
                    f_b_mean = f_b.mean()
                    f_h_mean = f_h.mean()
                    if f_b_mean > 0:
                        f_b = f_b / f_b_mean
                    if f_h_mean > 0:
                        f_h = f_h / f_h_mean

                if sst_ratio == "Fh/Fb":
                    lambda_val = f_h / (f_b + 1e-6)
                elif sst_ratio == "Fh only":
                    lambda_val = f_h
                elif sst_ratio == "1/Fb only":
                    lambda_val = 1.0 / (f_b + 1e-6)
                elif sst_ratio == "magnitude":
                    lambda_val = torch.abs(delta_safe)
                elif sst_ratio == "random":
                    lambda_val = torch.rand_like(base_data)
                else:
                    raise ValueError(f"Unknown sst_ratio: {sst_ratio}")

            elif method == "data_free_sst":
                phi_b = torch.stack([d ** 2 for d in delta_utils.values()]).mean(dim=0)
                phi_h = delta_safe ** 2

                if fisher_normalization:
                    phi_b_mean = phi_b.mean()
                    phi_h_mean = phi_h.mean()
                    if phi_b_mean > 0:
                        phi_b = phi_b / phi_b_mean
                    if phi_h_mean > 0:
                        phi_h = phi_h / phi_h_mean

                if sst_ratio == "Fh/Fb":
                    lambda_val = phi_h / (phi_b + 1e-6)
                elif sst_ratio == "Fh only":
                    lambda_val = phi_h
                elif sst_ratio == "1/Fb only":
                    lambda_val = 1.0 / (phi_b + 1e-6)
                elif sst_ratio == "magnitude":
                    lambda_val = torch.abs(delta_safe)
                elif sst_ratio == "random":
                    lambda_val = torch.rand_like(base_data)
                else:
                    raise ValueError(f"Unknown sst_ratio: {sst_ratio}")
            else:
                raise ValueError(f"Unknown SST method: {method}")

            if mask_type == "hard mask":
                flat_lambda = lambda_val.reshape(-1)
                k_elements = max(1, int(flat_lambda.numel() * k_ratio))
                threshold = torch.topk(flat_lambda, k_elements).values[-1]
                mask = (lambda_val >= threshold).to(dtype=base_data.dtype)
            elif mask_type == "soft mask":
                tau = k_ratio if k_ratio > 0 else 1.0
                mask = torch.sigmoid(torch.log(lambda_val + 1e-8) / tau).to(dtype=base_data.dtype)
            else:
                raise ValueError(f"Unknown mask_type: {mask_type}")

            if variant == "additive":
                merged_state_dict[name] = param_util_mean + alpha * (w_layer * mask * delta_safe)
            elif variant == "interpolation":
                w = torch.clamp(alpha * (w_layer * mask), 0.0, 1.0)
                merged_state_dict[name] = (1.0 - w) * param_util_mean + w * param_safe_for_merge
            else:
                raise ValueError(f"Unknown variant: {variant}")

            if norm_clipping:
                base_norm = torch.linalg.norm(base_data)
                merged_norm = torch.linalg.norm(merged_state_dict[name])
                if merged_norm > base_norm * max_norm_ratio:
                    merged_state_dict[name] = (merged_state_dict[name] / merged_norm) * (base_norm * max_norm_ratio)

    return merged_state_dict, fisher_weight_stats
