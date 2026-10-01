#!/bin/bash
#SBATCH --job-name=vllm_batch_search
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=1
#SBATCH --array=0-14%1
#SBATCH --output=logs_batch/%x_%A_%a.out
#SBATCH --error=logs_batch/%x_%A_%a.err

set -euo pipefail


# ================================================================
# Settings
# ================================================================

MODEL="Qwen/Qwen2.5-7B-Instruct"

RESULT_DIR="results_batch"
LOG_DIR="logs_batch"

mkdir -p "${RESULT_DIR}"
mkdir -p "${LOG_DIR}"


# ================================================================
# Search space
#
# 5 batches x 3 input lengths = 15 conditions
# ================================================================

BATCHES=(128 160 192 256 320)
INPUT_LENGTHS=(128 512 2048)

GPU_MEMORY_UTILIZATION=0.90
OUTPUT_TOKENS=256

CPU=1
REPEAT=3
WARMUP=1


# ================================================================
# CPU settings
# ================================================================

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=true


# ================================================================
# Array index -> parameters
# ================================================================

N_BATCH=${#BATCHES[@]}
N_INPUT=${#INPUT_LENGTHS[@]}

TOTAL=$((N_BATCH * N_INPUT))

IDX="${SLURM_ARRAY_TASK_ID}"

if [ "${IDX}" -ge "${TOTAL}" ]; then
    echo "ERROR: invalid array index ${IDX}"
    exit 1
fi


BATCH_INDEX=$((IDX % N_BATCH))
IDX=$((IDX / N_BATCH))

INPUT_INDEX=$((IDX % N_INPUT))


BATCH="${BATCHES[$BATCH_INDEX]}"
INPUT="${INPUT_LENGTHS[$INPUT_INDEX]}"


# ================================================================
# Display
# ================================================================

echo "============================================================"
echo "vLLM batch search"
echo "============================================================"
echo "model                  = ${MODEL}"
echo "CPU cores              = ${CPU}"
echo "batch                  = ${BATCH}"
echo "input tokens           = ${INPUT}"
echo "output tokens          = ${OUTPUT_TOKENS}"
echo "gpu memory utilization = ${GPU_MEMORY_UTILIZATION}"
echo "repeat                 = ${REPEAT}"
echo "hostname               = $(hostname)"
echo "CUDA_VISIBLE_DEVICES   = ${CUDA_VISIBLE_DEVICES:-unset}"
echo "============================================================"


# ================================================================
# Output
# ================================================================

OUTPUT="${RESULT_DIR}/result_batch${BATCH}_input${INPUT}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"


# ================================================================
# Run
# ================================================================

srun \
    --cpu-bind=cores \
    python benchmark_vllm_batch.py \
        --model "${MODEL}" \
        --cpu-cores "${CPU}" \
        --batch-size "${BATCH}" \
        --input-tokens "${INPUT}" \
        --output-tokens "${OUTPUT_TOKENS}" \
        --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
        --repeat "${REPEAT}" \
        --warmup "${WARMUP}" \
        --dtype bfloat16 \
        --output "${OUTPUT}"