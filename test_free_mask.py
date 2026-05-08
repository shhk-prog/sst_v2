import torch
import torch.nn as nn
from core.sst_merge_data_free import SSTMergeDataFree, FIMCalculatorDataFree, GEVPSolver
import sys

# To see full tensor prints nicely
torch.set_printoptions(precision=4, sci_mode=False)

regularization = 1e-6
gevp_solver = GEVPSolver(regularization)

# FIM in Data-Free are just param squared
params_benign = torch.randn(100) * 10
params_harm = torch.randn(100) * 10

# Simulated magnitude pruning FIM
F_benign = params_benign.pow(2)
F_harm = params_harm.pow(2)

eigenvalues, sorted_indices = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)

# Test top k ratios (hard masking behavior)
print(f"Total params: {len(eigenvalues)}")

mask_5 = gevp_solver.compute_safety_mask(eigenvalues, 0.05)
mask_20 = gevp_solver.compute_safety_mask(eigenvalues, 0.20)
mask_50 = gevp_solver.compute_safety_mask(eigenvalues, 0.50)

print(f"Mask  5% sum: {mask_5.sum().item()} / {len(mask_5)}")
print(f"Mask 20% sum: {mask_20.sum().item()} / {len(mask_20)}")
print(f"Mask 50% sum: {mask_50.sum().item()} / {len(mask_50)}")
print(f"20 == 50? {torch.all(mask_20 == mask_50).item()}")
