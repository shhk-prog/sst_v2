#!/bin/bash

# Experiment A Sweep Script
# Device: GPU 2
# Ratios: 0.2 (done), 0.4, 0.6, 0.8
# LRs: 2e-4 (done for r0.2), 1e-4, 5e-5

GPU=2

# 1. Ratio Sweep (at LR 2e-4)
RATIOS=(0.4 0.6 0.8)
for r in "${RATIOS[@]}"; do
    echo "Running Ratio Sweep: Ratio=$r, LR=2e-4"
    python sst_merge_v5/scripts/FT/run_safety_ft_mixed.py --gpu $GPU --mix_ratio $r --lr 2e-4 --total_samples 1400 --epochs 3
done

# 2. LR Sweep (at Ratio 0.2)
LRS=(1e-4 5e-5)
for lr in "${LRS[@]}"; do
    echo "Running LR Sweep: Ratio=0.2, LR=$lr"
    python sst_merge_v5/scripts/FT/run_safety_ft_mixed.py --gpu $GPU --mix_ratio 0.2 --lr $lr --total_samples 1400 --epochs 3
done

echo "All sweeps complete."
