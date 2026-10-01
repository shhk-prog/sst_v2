"""
SafeMERGE (Djuhera et al., 2025)
Preserving Safety Alignment in Fine-Tuned LLMs via Selective Layer-Wise Model Merging.
Applies selective layer filtering and directional projection to preserve safety.
"""

import torch
from typing import Optional, List
from mergers.base_merger import BaseMerger


class SafeMergeMerger(BaseMerger):
    FIDELITY_STATUS = "SIMPLIFIED_ADAPTATION (Uses layer-wise filtering; lacks gradient-guided directional optimization)"

    def __init__(
        self,
        target_layers: Optional[List[int]] = None,
        alpha: float = 0.5,
        total_layers: int = 32,
    ):
        # Default: apply to middle-to-late layers where safety features predominantly localize
        if target_layers is None:
            target_layers = list(range(10, 26))
        super().__init__(
            name="safemerge",
            config={"target_layers": target_layers, "alpha": alpha, "total_layers": total_layers, "fidelity": self.FIDELITY_STATUS}
        )
        self.target_layers = set(target_layers)
        self.alpha = float(alpha)
        self.total_layers = total_layers

    def _extract_layer_idx(self, key: Optional[str]) -> Optional[int]:
        if not key:
            return None
        # Parse 'layers.X.' or 'model.layers.X.'
        parts = key.split(".")
        for i, p in enumerate(parts):
            if p == "layers" and i + 1 < len(parts) and parts[i + 1].isdigit():
                return int(parts[i + 1])
        return None

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> torch.Tensor:
        layer_idx = self._extract_layer_idx(key)
        
        # If not in target layers, preserve utility model entirely (or minimal safety patch)
        if layer_idx is not None and layer_idx not in self.target_layers:
            return theta_u.clone()

        # In target layers, merge safety vector
        delta_s = theta_s - (theta_0 if theta_0 is not None else theta_u)
        if theta_0 is not None:
            # theta_u + alpha * delta_s
            out = theta_u + self.alpha * delta_s
        else:
            out = (1.0 - self.alpha) * theta_u + self.alpha * theta_s

        self.check_finite(out, "safemerge")
        return out
