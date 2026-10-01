"""
DELLA Merger (Deep et al., 2024)
Magnitude-based sampling and rescaling for interference reduction.
Parameters with higher magnitude have higher survival probability.
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class DELLAMerger(BaseMerger):
    def __init__(
        self,
        epsilon: float = 0.1,
        weight_u: float = 1.0,
        weight_s: float = 0.5,
        mask_seed: Optional[int] = 42,
    ):
        super().__init__(
            name="della",
            config={
                "epsilon": epsilon,
                "weight_u": weight_u,
                "weight_s": weight_s,
                "mask_seed": mask_seed,
            }
        )
        self.epsilon = float(epsilon)
        self.weight_u = float(weight_u)
        self.weight_s = float(weight_s)
        self.mask_seed = mask_seed

    def _della_sample_and_rescale(self, tensor: torch.Tensor, seed_offset: int = 0) -> torch.Tensor:
        abs_t = tensor.abs()
        max_val = abs_t.max()
        if max_val <= 1e-9:
            return torch.zeros_like(tensor)

        # Survival probability proportional to magnitude
        prob = torch.clamp(self.epsilon + (1.0 - self.epsilon) * (abs_t / max_val), min=1e-4, max=1.0)

        gen = torch.Generator(device=tensor.device)
        if self.mask_seed is not None:
            gen.manual_seed(self.mask_seed + seed_offset)

        mask = torch.bernoulli(prob, generator=gen)
        # Rescale survived elements by 1 / prob
        return (tensor * mask) / prob

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        if theta_0 is None:
            raise ValueError("DELLA requires base ancestor theta_0!")

        tau_u = self._della_sample_and_rescale(theta_u - theta_0, seed_offset=1)
        tau_s = self._della_sample_and_rescale(theta_s - theta_0, seed_offset=2)

        out = theta_0 + self.weight_u * tau_u + self.weight_s * tau_s
        self.check_finite(out, "della")
        return out
