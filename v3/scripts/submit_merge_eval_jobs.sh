#!/bin/bash
# ==============================================================================
# Helper script to submit or inspect Slurm merge evaluation jobs
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

SEEDS=(42 43 44)
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
    echo "=== Slurm 1-GPU Job Mapping (Total 12 Independent Jobs, batch_size=${BATCH_SIZE}) ==="
    printf "%-10s %-10s %-30s %-50s\n" "Task ID" "Seed" "Pattern" "Command Preview"
    echo "----------------------------------------------------------------------------------------------------"
    for i in {0..11}; do
        s_idx=$(( i / NUM_PATTERNS ))
        p_idx=$(( i % NUM_PATTERNS ))
        seed=${SEEDS[$s_idx]}
        pattern=${PATTERNS[$p_idx]}
        cmd="python scripts/merge_eval_parallel.py --config configs/config_main.yaml --seeds ${seed} --limit 320 --batch_size ${BATCH_SIZE} --gpus 0 --patterns ${pattern} --resume"
        printf "%-10d %-10d %-30s %-50s\n" "$i" "$seed" "$pattern" "$cmd"
    done
    echo "----------------------------------------------------------------------------------------------------"
    echo "To submit all 12 jobs via Job Array, run: $0 --submit"
    echo "To specify custom batch size, run e.g.: BATCH_SIZE=8 $0 --submit"
    echo "To submit as 12 separate sbatch jobs, run: $0 --submit-separate"

elif [ "$1" == "--submit" ]; then
    mkdir -p logs
    echo "Submitting Slurm Job Array (12 tasks, batch_size=${BATCH_SIZE})..."
    sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}" scripts/slurm_merge_eval_array.sh

elif [ "$1" == "--submit-separate" ]; then
    mkdir -p logs
    echo "Submitting 12 separate Slurm jobs (batch_size=${BATCH_SIZE})..."
    for i in {0..11}; do
        s_idx=$(( i / NUM_PATTERNS ))
        p_idx=$(( i % NUM_PATTERNS ))
        seed=${SEEDS[$s_idx]}
        pattern=${PATTERNS[$p_idx]}
        job_name="merge_s${seed}_${pattern}"
        echo "Submitting job ${i}: ${job_name} (seed=${seed}, pattern=${pattern})"
        sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}" --job-name="${job_name}" --array="${i}" scripts/slurm_merge_eval_array.sh
    done
    echo "All 12 jobs submitted."

elif [ "$1" == "--help" ]; then
    usage
else
    echo "Unknown option: $1"
    usage
    exit 1
fi
