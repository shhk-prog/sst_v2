"""
Base Merger Interface for Secure Merge v4
All mergers take state dictionaries or weight tensors and merge them adhering to strict mathematical formulations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch


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
        """
        Merge two parameter tensors.
        Args:
            theta_u: Utility / Domain model parameter tensor.
            theta_s: Safety model parameter tensor.
            theta_0: Base / Ancestor model parameter tensor (required by task arithmetic).
        Returns:
            Merged parameter tensor theta_m.
        """
        pass

    def merge_state_dicts(
        self,
        dict_u: Dict[str, torch.Tensor],
        dict_s: Dict[str, torch.Tensor],
        dict_0: Optional[Dict[str, torch.Tensor]] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """Merge full state dictionaries key by key."""
        merged_dict = {}
        for key, p_u in dict_u.items():
            p_s = dict_s.get(key)
            if p_s is None:
                merged_dict[key] = p_u.clone()
                continue
            
            p_0 = dict_0.get(key) if dict_0 is not None else None
            # Only merge floating point tensors with matching shape
            if p_u.is_floating_point() and p_u.shape == p_s.shape:
                merged_dict[key] = self.merge_tensors(p_u, p_s, p_0, key=key, **kwargs)
            else:
                # Fallback for non-matching or integer tensors (e.g. embed sizes)
                merged_dict[key] = p_u.clone()
        return merged_dict

    @staticmethod
    def check_finite(tensor: torch.Tensor, name: str = "tensor") -> None:
        """Verify no NaN or Inf in merged tensor."""
        if not torch.isfinite(tensor).all():
            raise ValueError(f"Merged tensor '{name}' contains NaN or Inf!")
