"""
MergeAlign Merger (Thakkar et al., 2024)
Combining Domain and Alignment Vectors with geometric alignment constraints.
Projects alignment vector onto the orthogonal complement of the domain task vector to preserve domain capabilities.
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class MergeAlignMerger(BaseMerger):
    def __init__(self, weight_u: float = 1.0, weight_s: float = 0.5, orthogonalize: bool = True):
        super().__init__(
            name="mergealign",
            config={"weight_u": weight_u, "weight_s": weight_s, "orthogonalize": orthogonalize}
        )
        self.weight_u = float(weight_u)
        self.weight_s = float(weight_s)
        self.orthogonalize = orthogonalize

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        base = theta_0 if theta_0 is not None else theta_u
        tau_u = theta_u - base
        tau_s = theta_s - base

        if self.orthogonalize:
            # Orthogonalize tau_s with respect to tau_u
            dot_product = torch.sum(tau_s * tau_u)
            norm_sq = torch.sum(tau_u * tau_u) + 1e-8
            proj = (dot_product / norm_sq) * tau_u
            tau_s_ortho = tau_s - proj
            # Blend
            delta = self.weight_u * tau_u + self.weight_s * tau_s_ortho
        else:
            delta = self.weight_u * tau_u + self.weight_s * tau_s

        out = base + delta
        self.check_finite(out, "mergealign")
        return out
