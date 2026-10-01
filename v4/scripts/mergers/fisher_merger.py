"""
Fisher-Weighted Averaging Merger (Matena and Raffel, NeurIPS 2022)
Formula:
    theta_m = (F_u * theta_u + F_s * theta_s) / (F_u + F_s + eps)
"""

import torch
from typing import Optional, Dict
from mergers.base_merger import BaseMerger


class FisherMerger(BaseMerger):
    def __init__(self, eps: float = 1e-6, default_weight_ratio: float = 1.0):
        super().__init__(name="fisher_weighted", config={"eps": eps, "default_weight_ratio": default_weight_ratio})
        self.eps = float(eps)
        self.default_weight_ratio = float(default_weight_ratio)

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        fim_u: Optional[torch.Tensor] = None,
        fim_s: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        if fim_u is None or fim_s is None:
            # Fallback to empirical magnitude or balanced weights if explicit FIM not supplied
            w_u = torch.ones_like(theta_u)
            w_s = torch.full_like(theta_s, self.default_weight_ratio)
        else:
            w_u = fim_u
            w_s = fim_s * self.default_weight_ratio

        denom = w_u + w_s + self.eps
        out = (w_u * theta_u + w_s * theta_s) / denom
        self.check_finite(out, "fisher")
        return out
