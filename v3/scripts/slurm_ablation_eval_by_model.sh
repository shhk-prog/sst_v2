#!/bin/bash
#SBATCH --job-name=ablation_eval
#SBATCH --output=logs/slurm_ablation_%A/eval_model_%a.log
#SBATCH --error=logs/slurm_ablation_%A/eval_model_%a.log
#SBATCH --partition=h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3

# ==============================================================================
# Slurm Job Array Script for Per-Model Parallel Ablation Evaluation
# ==============================================================================
# Evaluates 1 ablation merged model per task ID (ARRAY_TASK_ID)
# Each job requests 1 GPU and runs independently in Slurm queue.
# ==============================================================================

# --submit オプションが指定された場合は自動で全モデル数を取得し sbatch を投入
if [ "$1" == "--submit" ]; then
    mkdir -p logs
    BATCH_SIZE=${BATCH_SIZE:-32}
    PYTHON_EXEC="python"
    if [ -f "venv_v3/bin/python" ]; then
        PYTHON_EXEC="venv_v3/bin/python"
    elif [ -f "../venv_sst/bin/python" ]; then
        PYTHON_EXEC="../venv_sst/bin/python"
    fi
    MODELS_LIST=$(${PYTHON_EXEC} scripts/merge_eval_parallel.py --config configs/config_ablation.yaml --seeds 42 --limit 320 --list_models 2>/dev/null)
    TOTAL_MODELS=$(echo "${MODELS_LIST}" | grep -c $'\t' || echo "0")
    if [ "${TOTAL_MODELS}" -eq 0 ]; then
        echo "Error: No merged ablation models found to evaluate for configs/config_ablation.yaml"
        exit 1
    fi
    MAX_ARRAY_SIZE=1000
    for (( offset=0; offset<TOTAL_MODELS; offset+=MAX_ARRAY_SIZE )); do
        end_idx=$(( offset + MAX_ARRAY_SIZE - 1 ))
        if [ $end_idx -ge $TOTAL_MODELS ]; then
            end_idx=$(( TOTAL_MODELS - 1 ))
        fi
        chunk_size=$(( end_idx - offset ))
        echo "Submitting Slurm Job Array chunk for ablation models ${offset} to ${end_idx} (array=0-${chunk_size}, BATCH_SIZE=${BATCH_SIZE})..."
        sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}",ARRAY_OFFSET="${offset}" --array=0-${chunk_size} "$0"
    done
    exit 0
fi

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_ablation_${JOB_ID}"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

BATCH_SIZE=${BATCH_SIZE:-32}
ARRAY_OFFSET=${ARRAY_OFFSET:-0}
TASK_ID=$(( SLURM_ARRAY_TASK_ID + ARRAY_OFFSET ))

echo "=================================================="
echo "Slurm Per-Model Ablation Array Job ID: ${SLURM_ARRAY_JOB_ID:-N/A}_${TASK_ID}"
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
    --config configs/config_ablation.yaml \
    --seeds 42 \
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
