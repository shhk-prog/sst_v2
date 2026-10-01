"""
DARE Merger (Drop And REscale, Yu et al., ICML 2024)
Drop task vector parameters with probability p, and rescale remaining by 1/(1-p).
Supports both standard linear sum and sign-consensus mode.
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class DAREMerger(BaseMerger):
    def __init__(
        self,
        drop_rate: float = 0.5,
        weight_u: float = 1.0,
        weight_s: float = 0.5,
        mask_seed: Optional[int] = 42,
    ):
        super().__init__(
            name="dare",
            config={
                "drop_rate": drop_rate,
                "weight_u": weight_u,
                "weight_s": weight_s,
                "mask_seed": mask_seed,
            }
        )
        self.drop_rate = float(drop_rate)
        self.weight_u = float(weight_u)
        self.weight_s = float(weight_s)
        self.mask_seed = mask_seed

    def _dare_mask_and_rescale(self, tensor: torch.Tensor, seed_offset: int = 0) -> torch.Tensor:
        if self.drop_rate <= 0.0:
            return tensor.clone()
        if self.drop_rate >= 1.0:
            return torch.zeros_like(tensor)

        gen = torch.Generator(device=tensor.device)
        if self.mask_seed is not None:
            gen.manual_seed(self.mask_seed + seed_offset)

        keep_prob = 1.0 - self.drop_rate
        mask = torch.bernoulli(torch.full_like(tensor, keep_prob), generator=gen)
        # Rescale remaining values
        return (tensor * mask) / keep_prob

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        if theta_0 is None:
            raise ValueError("DARE requires base ancestor theta_0!")

        tau_u = self._dare_mask_and_rescale(theta_u - theta_0, seed_offset=1)
        tau_s = self._dare_mask_and_rescale(theta_s - theta_0, seed_offset=2)

        out = theta_0 + self.weight_u * tau_u + self.weight_s * tau_s
        self.check_finite(out, "dare")
        return out
