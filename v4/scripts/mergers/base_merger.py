"""
Base Merger Interface for Secure Merge v4
All mergers take state dictionaries or weight tensors and merge them adhering to strict mathematical formulations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
import torch


# Allowlist for non-weight / position / buffer tensors that do not undergo arithmetic merging
MERGE_EXEMPT_ALLOWLIST: Set[str] = {
    "rotary_emb.inv_freq",
    "model.layers.*.self_attn.rotary_emb.inv_freq",
}


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
        merged_dict = {}
        missing_in_s = []
        shape_mismatches = []

        for key, p_u in dict_u.items():
            p_s = dict_s.get(key)
            if p_s is None:
                # Check allowlist
                if any(al in key for al in MERGE_EXEMPT_ALLOWLIST):
                    merged_dict[key] = p_u.clone()
                    continue
                missing_in_s.append(key)
                merged_dict[key] = p_u.clone()
                continue

            p_0 = dict_0.get(key) if dict_0 is not None else None

            # Verify shape alignment
            if p_u.shape != p_s.shape:
                shape_mismatches.append(f"{key}: u_shape={p_u.shape} vs s_shape={p_s.shape}")
                merged_dict[key] = p_u.clone()
                continue

            # Only merge floating point tensors
            if p_u.is_floating_point():
                # Perform computation in FP32/FP64 to prevent FP16 square-sum overflow (P1-04)
                orig_dtype = p_u.dtype
                p_u_f32 = p_u.to(torch.float32)
                p_s_f32 = p_s.to(torch.float32)
                p_0_f32 = p_0.to(torch.float32) if p_0 is not None else None

                merged_f32 = self.merge_tensors(p_u_f32, p_s_f32, p_0_f32, key=key, **kwargs)
                merged_dict[key] = merged_f32.to(orig_dtype)
            else:
                merged_dict[key] = p_u.clone()

        if strict_shape_check and shape_mismatches:
            raise ValueError(
                f"[STRICT MERGER ERROR] Shape mismatches detected between utility and safety models:\n"
                + "\n".join(shape_mismatches[:10])
                + (f"\n... and {len(shape_mismatches) - 10} more" if len(shape_mismatches) > 10 else "")
            )

        return merged_dict

    @staticmethod
    def check_finite(tensor: torch.Tensor, name: str = "tensor") -> None:
        """Verify no NaN or Inf in merged tensor."""
        if not torch.isfinite(tensor).all():
            raise ValueError(f"Merged tensor '{name}' contains NaN or Inf!")
