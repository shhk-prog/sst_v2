#!/bin/bash
#SBATCH --job-name=merge_eval
#SBATCH --output=logs/slurm_merge_%A/eval_%a.log
#SBATCH --error=logs/slurm_merge_%A/eval_%a.log
#SBATCH --partition=h100
#SBATCH --qos=interactive_nofs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3
#SBATCH --array=0-11

# ==============================================================================
# Slurm Job Array Script for Parallel Merge Evaluation
# ==============================================================================
# 3 Seeds: 42, 43, 44
# 4 Patterns:
#   0: safety+math
#   1: safety+code
#   2: safety+medical
#   3: safety+math+code+medical
# Total jobs = 3 * 4 = 12 (ARRAY_TASK_ID 0 to 11)
# Each job requests 1 GPU and runs independently in Slurm queue.
# ==============================================================================

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_merge_${JOB_ID}"

SEEDS=(42 43 44)
PATTERNS=(
    "safety+math"
    "safety+code"
    "safety+medical"
    "safety+math+code+medical"
)

NUM_PATTERNS=${#PATTERNS[@]}

TASK_ID=${SLURM_ARRAY_TASK_ID:-0}

SEED_INDEX=$(( TASK_ID / NUM_PATTERNS ))
PATTERN_INDEX=$(( TASK_ID % NUM_PATTERNS ))

SEED=${SEEDS[$SEED_INDEX]}
PATTERN=${PATTERNS[$PATTERN_INDEX]}

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

BATCH_SIZE=${BATCH_SIZE:-auto}

echo "=================================================="
echo "Slurm Array Job ID: ${SLURM_ARRAY_JOB_ID:-N/A}_${TASK_ID}"
echo "Running Seed: ${SEED}"
echo "Running Pattern: ${PATTERN}"
echo "Batch Size: ${BATCH_SIZE}"
echo "Configured CPU Threads: ${OMP_NUM_THREADS}"
echo "Assigned CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-0}"
echo "Working Dir: $(pwd)"
echo "=================================================="

PYTHON_EXEC="python"
if [ -f "venv_v3/bin/python" ]; then
    PYTHON_EXEC="venv_v3/bin/python"
elif [ -f "../venv_sst/bin/python" ]; then
    PYTHON_EXEC="../venv_sst/bin/python"
fi

cmd="${PYTHON_EXEC} scripts/merge_eval_parallel.py \
    --config configs/config_main.yaml \
    --seeds ${SEED} \
    --limit 320 \
    --batch_size ${BATCH_SIZE} \
    --gpus 0 \
    --patterns ${PATTERN} \
    --resume"

echo "Executing command:"
echo "${cmd}"
echo "--------------------------------------------------"

eval ${cmd}

