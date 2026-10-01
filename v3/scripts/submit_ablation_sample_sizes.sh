#!/bin/bash
# ==============================================================================
# Submit Ablation Jobs for Sample Sizes 50, 100, 500 (1 GPU per sample size)
# ==============================================================================

cd "/mnt/nas/home/hiromi/src/sst_v2/v3" || exit 1

mkdir -p logs

echo "Submitting 3-job array to Slurm for sample sizes 50, 100, 500..."
echo "Resources per job: 1 GPU, 16 CPUs, 1 Task"

JOB_OUTPUT=$(sbatch scripts/slurm_ablation_sample_size.sh)
echo "${JOB_OUTPUT}"

JOB_ID=$(echo "${JOB_OUTPUT}" | awk '{print $4}')

if [ -n "${JOB_ID}" ]; then
    echo "=========================================================="
    echo "Slurm Job Array Submitted Successfully!"
    echo "Array Job ID: ${JOB_ID}"
    echo "Tasks: 0 (Sample Size 50), 1 (Sample Size 100), 2 (Sample Size 500)"
    echo "Log directory: logs/slurm_ablation_${JOB_ID}/"
    echo "Check status with: squeue -j ${JOB_ID}"
    echo "=========================================================="
fi
