"""
TIES Merger (Yadav et al., NeurIPS 2023)
TRIM: Keep top-k fraction of parameters by magnitude.
ELECT SIGN: Find majority sign across task vectors.
DISJOINT MERGE: Average parameters agreeing with majority sign.
"""

import torch
from typing import Optional, List
from mergers.base_merger import BaseMerger


class TIESMerger(BaseMerger):
    def __init__(self, keep_ratio: float = 0.2, weight_u: float = 1.0, weight_s: float = 0.5):
        super().__init__(name="ties", config={"keep_ratio": keep_ratio, "weight_u": weight_u, "weight_s": weight_s})
        self.keep_ratio = float(keep_ratio)
        self.weight_u = float(weight_u)
        self.weight_s = float(weight_s)

    def _trim(self, tensor: torch.Tensor) -> torch.Tensor:
        """Keep top-k absolute values, set rest to zero."""
        k = int(tensor.numel() * self.keep_ratio)
        if k <= 0:
            return torch.zeros_like(tensor)
        if k >= tensor.numel():
            return tensor.clone()
        
        flat = tensor.abs().view(-1)
        threshold, _ = torch.kthvalue(flat, tensor.numel() - k + 1)
        mask = tensor.abs() >= threshold
        return tensor * mask

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        if theta_0 is None:
            raise ValueError("TIES requires base ancestor theta_0!")

        tau_u = self._trim(theta_u - theta_0)
        tau_s = self._trim(theta_s - theta_0)

        # Weighted task vectors
        w_u = self.weight_u * tau_u
        w_s = self.weight_s * tau_s

        # Elect sign
        sum_vector = w_u + w_s
        elected_sign = torch.sign(sum_vector)

        # Disjoint merge: only keep elements where sign matches elected sign
        mask_u = (torch.sign(w_u) == elected_sign) & (w_u != 0)
        mask_s = (torch.sign(w_s) == elected_sign) & (w_s != 0)

        counts = mask_u.float() + mask_s.float()
        counts = torch.clamp(counts, min=1.0)

        merged_delta = (w_u * mask_u.float() + w_s * mask_s.float()) / counts
        out = theta_0 + merged_delta
        self.check_finite(out, "ties")
        return out
