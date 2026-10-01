"""
LED-Merging (Location-Election-Disjoint, Ma et al., ACL 2025)
Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint.
1. Location: Identify critical parameters for utility and safety.
2. Election: Elect dominant parameters in conflicting coordinates.
3. Disjoint: Merge non-conflicting parameters and resolved conflicts.
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class LEDMerger(BaseMerger):
    FIDELITY_STATUS = "SIMPLIFIED_ADAPTATION (Uses delta magnitude for location election; lacks external gradient saliency)"

    def __init__(
        self,
        top_k_utility: float = 0.3,
        top_k_safety: float = 0.3,
        weight_u: float = 1.0,
        weight_s: float = 0.6,
    ):
        super().__init__(
            name="led_merging",
            config={
                "top_k_utility": top_k_utility,
                "top_k_safety": top_k_safety,
                "weight_u": weight_u,
                "weight_s": weight_s,
                "fidelity": self.FIDELITY_STATUS,
            }
        )
        self.top_k_u = float(top_k_utility)
        self.top_k_s = float(top_k_safety)
        self.weight_u = float(weight_u)
        self.weight_s = float(weight_s)

    def _get_topk_mask(self, tensor: torch.Tensor, ratio: float) -> torch.Tensor:
        k = int(tensor.numel() * ratio)
        if k <= 0:
            return torch.zeros_like(tensor, dtype=torch.bool)
        if k >= tensor.numel():
            return torch.ones_like(tensor, dtype=torch.bool)
        flat = tensor.abs().view(-1)
        th, _ = torch.kthvalue(flat, tensor.numel() - k + 1)
        return tensor.abs() >= th

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

        # 1. Location masks
        mask_u = self._get_topk_mask(tau_u, self.top_k_u)
        mask_s = self._get_topk_mask(tau_s, self.top_k_s)

        # 2. Election on conflict:
        conflict = mask_u & mask_s
        # Election rule: if conflict, pick based on normalized relative magnitude or prioritize safety
        # LED default: elect whichever has higher relative significance
        mag_u = tau_u.abs() / (tau_u.abs().max() + 1e-8)
        mag_s = tau_s.abs() / (tau_s.abs().max() + 1e-8)
        elect_s = conflict & (mag_s >= mag_u)
        elect_u = conflict & (mag_u > mag_s)

        # 3. Disjoint assembly
        final_delta = torch.zeros_like(tau_u)
        # Unique non-conflicting regions
        final_delta += (mask_u & (~conflict)).float() * self.weight_u * tau_u
        final_delta += (mask_s & (~conflict)).float() * self.weight_s * tau_s
        # Elected conflict regions
        final_delta += elect_u.float() * self.weight_u * tau_u
        final_delta += elect_s.float() * self.weight_s * tau_s

        out = base + final_delta
        self.check_finite(out, "led_merging")
        return out
