"""
Linear Safety-Patch Merger
Formula:
    theta_m = (1 - alpha) * theta_u + alpha * theta_s
            = theta_u + alpha * (theta_s - theta_u)
Properties:
    alpha = 0.0 -> theta_u
    alpha = 1.0 -> theta_s
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class LinearPatchMerger(BaseMerger):
    def __init__(self, alpha: float = 0.5):
        super().__init__(name="linear_safety_patch", config={"alpha": alpha})
        self.alpha = float(alpha)

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        out = (1.0 - self.alpha) * theta_u + self.alpha * theta_s
        self.check_finite(out, "linear_patch")
        return out
