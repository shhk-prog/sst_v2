"""
Base Merger Interface for Secure Merge v4
All mergers take state dictionaries or weight tensors and merge them adhering to strict mathematical formulations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, List, Tuple
import torch


# Allowlist for non-weight / position / buffer tensors that do not undergo arithmetic merging
MERGE_EXEMPT_ALLOWLIST: Set[str] = {
    "rotary_emb.inv_freq",
    "model.layers.*.self_attn.rotary_emb.inv_freq",
}


def validate_state_dicts(
    dict_u: Dict[str, torch.Tensor],
    dict_s: Dict[str, torch.Tensor],
    dict_0: Optional[Dict[str, torch.Tensor]] = None,
    strict: bool = True,
) -> Tuple[List[str], List[str]]:
    """
    R3-04: Common validation function for weight keys and shapes across ALL mergers.
    Prohibits silent skipping or unverified copying in both BaseMerger and overridden implementations.
    """
    missing_in_s = []
    shape_mismatches = []

    for key, p_u in dict_u.items():
        if any(al in key for al in MERGE_EXEMPT_ALLOWLIST):
            continue
        p_s = dict_s.get(key)
        if p_s is None:
            missing_in_s.append(key)
            continue
        if p_u.shape != p_s.shape:
            shape_mismatches.append(f"{key}: u_shape={p_u.shape} vs s_shape={p_s.shape}")

    if strict:
        if shape_mismatches:
            raise ValueError(
                f"[STRICT MERGER ERROR] Shape mismatches detected between utility and safety models:\n"
                + "\n".join(shape_mismatches[:10])
                + (f"\n... and {len(shape_mismatches) - 10} more" if len(shape_mismatches) > 10 else "")
            )
        if missing_in_s:
            raise ValueError(
                f"[STRICT MERGER ERROR] Missing essential weight keys in safety model:\n"
                + "\n".join(missing_in_s[:10])
                + (f"\n... and {len(missing_in_s) - 10} more" if len(missing_in_s) > 10 else "")
                + "\nSilent copying of utility weights without safety counterpart is rejected (R3-04)."
            )

    return missing_in_s, shape_mismatches


class BaseMerger(ABC):
    """Abstract Base Class for all model merging methods."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        """Merge two parameter tensors."""
        pass

    def merge_state_dicts(
        self,
        dict_u: Dict[str, torch.Tensor],
        dict_s: Dict[str, torch.Tensor],
        dict_0: Optional[Dict[str, torch.Tensor]] = None,
        strict_shape_check: bool = True,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        Merge full state dictionaries key by key.
        Strict Plan Rule:
        Silent fallback on shape mismatch or missing weights is prohibited.
        Only tensors matching the explicit allowlist are exempt from merging.
        """
        validate_state_dicts(dict_u, dict_s, dict_0, strict=strict_shape_check)

        merged_dict = {}
        fim_u_dict = kwargs.get("fim_u")
        fim_s_dict = kwargs.get("fim_s")

        for key, p_u in dict_u.items():
            p_s = dict_s.get(key)
            if p_s is None:
                merged_dict[key] = p_u.clone()
                continue

            p_0 = dict_0.get(key) if dict_0 is not None else None

            # Only merge floating point tensors
            if p_u.is_floating_point():
                # Perform computation in FP32/FP64 to prevent FP16 square-sum overflow (P1-04)
                orig_dtype = p_u.dtype
                p_u_f32 = p_u.to(torch.float32)
                p_s_f32 = p_s.to(torch.float32)
                p_0_f32 = p_0.to(torch.float32) if p_0 is not None else None

                # Extract per-key FIM tensors if provided (R3-06)
                tensor_kwargs = dict(kwargs)
                if isinstance(fim_u_dict, dict):
                    tensor_kwargs["fim_u"] = fim_u_dict.get(key)
                if isinstance(fim_s_dict, dict):
                    tensor_kwargs["fim_s"] = fim_s_dict.get(key)

                merged_f32 = self.merge_tensors(p_u_f32, p_s_f32, p_0_f32, key=key, **tensor_kwargs)
                merged_dict[key] = merged_f32.to(orig_dtype)
            else:
                merged_dict[key] = p_u.clone()

        return merged_dict

    @staticmethod
    def check_finite(tensor: torch.Tensor, name: str = "tensor") -> None:
        """Verify no NaN or Inf in merged tensor."""
        if not torch.isfinite(tensor).all():
            raise ValueError(f"Merged tensor '{name}' contains NaN or Inf!")
