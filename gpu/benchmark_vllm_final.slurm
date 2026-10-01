#!/bin/bash
#SBATCH --job-name=vllm_final_search
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=1
#SBATCH --array=0-7%1
#SBATCH --output=logs_final/%x_%A_%a.out
#SBATCH --error=logs_final/%x_%A_%a.err

set -euo pipefail

MODEL="Qwen/Qwen2.5-7B-Instruct"

RESULT_DIR="results_final"
LOG_DIR="logs_final"

mkdir -p "${RESULT_DIR}"
mkdir -p "${LOG_DIR}"

BATCHES=(320 384 448 512)
INPUT_LENGTHS=(128 512)

CPU=1
GPU_MEMORY_UTILIZATION=0.90
OUTPUT_TOKENS=256
REPEAT=5
WARMUP=1

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=true

N_BATCH=${#BATCHES[@]}
N_INPUT=${#INPUT_LENGTHS[@]}

TOTAL=$((N_BATCH * N_INPUT))

IDX="${SLURM_ARRAY_TASK_ID}"

if [ "${IDX}" -ge "${TOTAL}" ]; then
    echo "Invalid array index: ${IDX}"
    exit 1
fi

BATCH_INDEX=$((IDX % N_BATCH))
IDX=$((IDX / N_BATCH))

INPUT_INDEX=$((IDX % N_INPUT))

BATCH="${BATCHES[$BATCH_INDEX]}"
INPUT="${INPUT_LENGTHS[$INPUT_INDEX]}"

echo "============================================================"
echo "Final vLLM batch search"
echo "============================================================"
echo "model                  = ${MODEL}"
echo "CPU                    = ${CPU}"
echo "batch                  = ${BATCH}"
echo "input                  = ${INPUT}"
echo "output                 = ${OUTPUT_TOKENS}"
echo "gpu_memory_utilization = ${GPU_MEMORY_UTILIZATION}"
echo "repeat                 = ${REPEAT}"
echo "hostname               = $(hostname)"
echo "CUDA_VISIBLE_DEVICES   = ${CUDA_VISIBLE_DEVICES:-unset}"
echo "============================================================"

OUTPUT="${RESULT_DIR}/result_batch${BATCH}_input${INPUT}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"

srun \
    --cpu-bind=cores \
    python benchmark_vllm_final.py \
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