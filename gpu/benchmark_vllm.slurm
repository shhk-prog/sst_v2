#!/bin/bash
#SBATCH --job-name=vllm_bench2
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=1
#SBATCH --array=0-44%1
#SBATCH --output=logs_vllm2/%x_%A_%a.out
#SBATCH --error=logs_vllm2/%x_%A_%a.err

set -euo pipefail


# ================================================================
# Settings
# ================================================================

MODEL="Qwen/Qwen2.5-7B-Instruct"

RESULT_DIR="results_vllm2"
LOG_DIR="logs_vllm2"

mkdir -p "${RESULT_DIR}"
mkdir -p "${LOG_DIR}"


# ================================================================
# Search space
#
# 5 batches
# x 3 input lengths
# x 3 GPU memory utilization
# = 45 conditions
# ================================================================

BATCHES=(32 48 64 96 128)
INPUT_LENGTHS=(128 512 2048)
GPU_MEMORY_UTILS=(0.85 0.90 0.95)

OUTPUT_TOKENS=256

REPEAT=3
WARMUP=1


# ================================================================
# Fixed CPU
# ================================================================

CPU=1

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=true


# ================================================================
# Array index -> configuration
# ================================================================

N_BATCH=${#BATCHES[@]}
N_INPUT=${#INPUT_LENGTHS[@]}
N_GPU_MEM=${#GPU_MEMORY_UTILS[@]}

TOTAL=$((N_BATCH * N_INPUT * N_GPU_MEM))

IDX="${SLURM_ARRAY_TASK_ID}"

if [ "${IDX}" -ge "${TOTAL}" ]; then
    echo "ERROR: invalid array index ${IDX}"
    exit 1
fi


BATCH_INDEX=$((IDX % N_BATCH))
IDX=$((IDX / N_BATCH))

INPUT_INDEX=$((IDX % N_INPUT))
IDX=$((IDX / N_INPUT))

GPU_MEM_INDEX=$((IDX % N_GPU_MEM))


BATCH="${BATCHES[$BATCH_INDEX]}"
INPUT="${INPUT_LENGTHS[$INPUT_INDEX]}"
GPU_MEM="${GPU_MEMORY_UTILS[$GPU_MEM_INDEX]}"


# ================================================================
# Display
# ================================================================

echo "============================================================"
echo "vLLM FairShare benchmark"
echo "============================================================"
echo "model                  = ${MODEL}"
echo "CPU cores              = ${CPU}"
echo "batch / requests       = ${BATCH}"
echo "input tokens           = ${INPUT}"
echo "output tokens          = ${OUTPUT_TOKENS}"
echo "gpu memory utilization = ${GPU_MEM}"
echo "repeat                 = ${REPEAT}"
echo "hostname               = $(hostname)"
echo "CUDA_VISIBLE_DEVICES   = ${CUDA_VISIBLE_DEVICES:-unset}"
echo "SLURM_CPUS_PER_TASK    = ${SLURM_CPUS_PER_TASK:-unset}"
echo "============================================================"


# ================================================================
# Output
# ================================================================

GPU_MEM_LABEL="${GPU_MEM/./}"

OUTPUT="${RESULT_DIR}/result_batch${BATCH}_input${INPUT}_mem${GPU_MEM_LABEL}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"


# ================================================================
# Run
# ================================================================

srun \
    --cpu-bind=cores \
    python benchmark_vllm.py \
        --model "${MODEL}" \
        --cpu-cores "${CPU}" \
        --batch-size "${BATCH}" \
        --input-tokens "${INPUT}" \
        --output-tokens "${OUTPUT_TOKENS}" \
        --gpu-memory-utilization "${GPU_MEM}" \
        --repeat "${REPEAT}" \
        --warmup "${WARMUP}" \
        --dtype bfloat16 \
        --output "${OUTPUT}"