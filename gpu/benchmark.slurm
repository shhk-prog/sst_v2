#!/bin/bash
#SBATCH --job-name=llm_bench
#SBATCH --gres=gpu:1
#SBATCH --array=0-29%1
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail


# ================================================================
# Settings
# ================================================================

MODEL="Qwen/Qwen2.5-7B-Instruct"

CPU="${BENCH_CPU}"

RESULT_DIR="results"
LOG_DIR="logs"

mkdir -p "${RESULT_DIR}"
mkdir -p "${LOG_DIR}"


# ================================================================
# Search space
#
# 5 batch sizes
# x 3 input lengths
# x 2 engines
# = 30 conditions per CPU setting
# ================================================================

BATCHES=(1 4 8 16 32)
INPUT_LENGTHS=(128 512 2048)
ENGINES=("transformers" "vllm")

OUTPUT_TOKENS=256
REPEAT=3
WARMUP=1


# ================================================================
# Validate CPU allocation
# ================================================================

if [ -z "${SLURM_CPUS_PER_TASK:-}" ]; then
    echo "ERROR: SLURM_CPUS_PER_TASK is not set"
    exit 1
fi

if [ "${SLURM_CPUS_PER_TASK}" -ne "${CPU}" ]; then
    echo "ERROR: CPU allocation mismatch"
    echo "BENCH_CPU=${CPU}"
    echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK}"
    exit 1
fi


# ================================================================
# Array index -> parameter combination
# ================================================================

N_BATCH=${#BATCHES[@]}
N_INPUT=${#INPUT_LENGTHS[@]}
N_ENGINE=${#ENGINES[@]}

TOTAL=$((N_BATCH * N_INPUT * N_ENGINE))

IDX="${SLURM_ARRAY_TASK_ID}"

if [ "${IDX}" -ge "${TOTAL}" ]; then
    echo "Invalid array index: ${IDX}"
    exit 1
fi


BATCH_INDEX=$((IDX % N_BATCH))
IDX=$((IDX / N_BATCH))

INPUT_INDEX=$((IDX % N_INPUT))
IDX=$((IDX / N_INPUT))

ENGINE_INDEX=$((IDX % N_ENGINE))


BATCH="${BATCHES[$BATCH_INDEX]}"
INPUT="${INPUT_LENGTHS[$INPUT_INDEX]}"
ENGINE="${ENGINES[$ENGINE_INDEX]}"


# ================================================================
# Display configuration
# ================================================================

echo "=================================================="
echo "LLM benchmark"
echo "=================================================="
echo "model             = ${MODEL}"
echo "engine            = ${ENGINE}"
echo "CPU cores         = ${CPU}"
echo "batch / requests  = ${BATCH}"
echo "input tokens      = ${INPUT}"
echo "output tokens     = ${OUTPUT_TOKENS}"
echo "repeat            = ${REPEAT}"
echo "SLURM CPUs        = ${SLURM_CPUS_PER_TASK}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "hostname          = $(hostname)"
echo "=================================================="


# ================================================================
# CPU thread settings
# ================================================================

export OMP_NUM_THREADS="${CPU}"
export MKL_NUM_THREADS="${CPU}"
export OPENBLAS_NUM_THREADS="${CPU}"
export NUMEXPR_NUM_THREADS="${CPU}"

export TOKENIZERS_PARALLELISM=true


# ================================================================
# Output
#
# Write to an independent CSV to avoid concurrent writes.
# ================================================================

OUTPUT="${RESULT_DIR}/result_cpu${CPU}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"


# ================================================================
# Run
# ================================================================

srun \
    --cpu-bind=cores \
    python benchmark_llm.py \
        --engine "${ENGINE}" \
        --model "${MODEL}" \
        --cpu-cores "${CPU}" \
        --batch-size "${BATCH}" \
        --input-tokens "${INPUT}" \
        --output-tokens "${OUTPUT_TOKENS}" \
        --repeat "${REPEAT}" \
        --warmup "${WARMUP}" \
        --dtype bfloat16 \
        --gpu-memory-utilization 0.90 \
        --output "${OUTPUT}"