"""
Standard Task Arithmetic Merger (Ilharco et al., 2023)
Formula:
    tau_u = theta_u - theta_0
    tau_s = theta_s - theta_0
    theta_m = theta_0 + lambda_u * tau_u + lambda_s * tau_s
Note:
    Requires common ancestor theta_0.
    Distinct from Linear direct difference interpolation.
"""

import torch
from typing import Optional
from mergers.base_merger import BaseMerger


class TaskArithmeticMerger(BaseMerger):
    def __init__(self, lambda_u: float = 1.0, lambda_s: float = 0.5):
        super().__init__(name="task_arithmetic", config={"lambda_u": lambda_u, "lambda_s": lambda_s})
        self.lambda_u = float(lambda_u)
        self.lambda_s = float(lambda_s)

    def merge_tensors(
        self,
        theta_u: torch.Tensor,
        theta_s: torch.Tensor,
        theta_0: Optional[torch.Tensor] = None,
        **kwargs
    ) -> torch.Tensor:
        if theta_0 is None:
            raise ValueError(
                "TaskArithmetic requires a valid base ancestor theta_0! "
                "Do not fall back to linear interpolation without base model."
            )
        tau_u = theta_u - theta_0
        tau_s = theta_s - theta_0
        out = theta_0 + self.lambda_u * tau_u + self.lambda_s * tau_s
        self.check_finite(out, "task_arithmetic")
        return out
