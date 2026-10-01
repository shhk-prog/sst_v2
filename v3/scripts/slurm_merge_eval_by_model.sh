#!/bin/bash
#SBATCH --job-name=merge_mod_eval
#SBATCH --output=logs/slurm_merge_%A/eval_model_%a.log
#SBATCH --error=logs/slurm_merge_%A/eval_model_%a.log
#SBATCH --partition=h100
#SBATCH --nodelist=iag-03
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
# (Note: --array is omitted here because it is dynamically injected by submit_merge_eval_by_model.sh)
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3

# ==============================================================================
# Slurm Job Array Script for Per-Model Parallel Evaluation
# ==============================================================================
# Evaluates 1 model per task ID (ARRAY_TASK_ID)
# Each job requests 1 GPU and runs independently in Slurm queue.
# ==============================================================================

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_merge_${JOB_ID}"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

BATCH_SIZE=${BATCH_SIZE:-32}
ARRAY_OFFSET=${ARRAY_OFFSET:-0}
TASK_ID=$(( SLURM_ARRAY_TASK_ID + ARRAY_OFFSET ))

echo "=================================================="
echo "Slurm Per-Model Array Job ID: ${SLURM_ARRAY_JOB_ID:-N/A}_${TASK_ID}"
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
    --seeds 42 43 44 \
    --limit 320 \
    --batch_size ${BATCH_SIZE} \
    --gpus 0 \
    --model_index ${TASK_ID} \
    --use_vllm \
    --resume"

echo "Executing command:"
echo "${cmd}"
echo "--------------------------------------------------"

eval ${cmd}
