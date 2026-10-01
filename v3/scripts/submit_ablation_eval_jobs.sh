#!/bin/bash
# ==============================================================================
# Helper script to submit or inspect Slurm ablation evaluation jobs
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

SAMPLE_SIZES=(50 100 500)
PATTERNS=(
    "safety+math"
    "safety+code"
    "safety+medical"
    "safety+math+code+medical"
)
NUM_PATTERNS=${#PATTERNS[@]}

usage() {
    echo "Usage: $0 [--dry-run|--submit|--submit-separate|--help]"
    echo ""
    echo "Options:"
    echo "  --dry-run          Show the mapping of 12 independent GPU jobs without submitting"
    echo "  --submit           Submit as a Slurm Job Array (12 sub-jobs requesting 1 GPU each)"
    echo "  --submit-separate  Submit as 12 individual sbatch commands with unique job names"
    echo "  --help             Display this help message"
}

BATCH_SIZE=${BATCH_SIZE:-auto}

if [ "$1" == "--dry-run" ] || [ "$#" -eq 0 ]; then
    echo "=== Slurm 1-GPU Ablation Eval Job Mapping (Total 12 Independent Jobs, batch_size=${BATCH_SIZE}) ==="
    printf "%-10s %-12s %-30s %-50s\n" "Task ID" "Sample Size" "Pattern" "Command Preview"
    echo "----------------------------------------------------------------------------------------------------"
    for i in {0..11}; do
        s_idx=$(( i / NUM_PATTERNS ))
        p_idx=$(( i % NUM_PATTERNS ))
        ss=${SAMPLE_SIZES[$s_idx]}
        pattern=${PATTERNS[$p_idx]}
        cmd="python scripts/merge_eval_parallel.py --config configs/config_ablation_n${ss}_tmp.yaml --seeds 42 --limit 320 --batch_size ${BATCH_SIZE} --gpus 0 --patterns ${pattern} --resume"
        printf "%-10d %-12d %-30s %-50s\n" "$i" "$ss" "$pattern" "$cmd"
    done
    echo "----------------------------------------------------------------------------------------------------"
    echo "To submit all 12 jobs via Job Array, run: $0 --submit"
    echo "To specify custom batch size, run e.g.: BATCH_SIZE=32 $0 --submit"
    echo "To submit as 12 separate sbatch jobs, run: $0 --submit-separate"

elif [ "$1" == "--submit" ]; then
    mkdir -p logs
    echo "Submitting Slurm Job Array (12 ablation eval tasks, batch_size=${BATCH_SIZE})..."
    sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}" scripts/slurm_ablation_eval_array.sh

elif [ "$1" == "--submit-separate" ]; then
    mkdir -p logs
    echo "Submitting 12 separate Slurm ablation eval jobs (batch_size=${BATCH_SIZE})..."
    for i in {0..11}; do
        s_idx=$(( i / NUM_PATTERNS ))
        p_idx=$(( i % NUM_PATTERNS ))
        ss=${SAMPLE_SIZES[$s_idx]}
        pattern=${PATTERNS[$p_idx]}
        job_name="ablation_eval_n${ss}_${pattern}"
        echo "Submitting job ${i}: ${job_name} (sample_size=${ss}, pattern=${pattern})"
        sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}" --job-name="${job_name}" --array="${i}" scripts/slurm_ablation_eval_array.sh
    done
    echo "All 12 jobs submitted."

elif [ "$1" == "--help" ]; then
    usage
else
    echo "Unknown option: $1"
    usage
    exit 1
fi
