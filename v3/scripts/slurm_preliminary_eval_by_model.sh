#!/bin/bash
#SBATCH --job-name=prelim_eval
#SBATCH --output=logs/slurm_prelim_%A/eval_model_%a.log
#SBATCH --error=logs/slurm_prelim_%A/eval_model_%a.log
#SBATCH --partition=h100
#SBATCH --nodelist=iag-03
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3

# ==============================================================================
# Slurm Job Array Script for Per-Model Parallel Preliminary Evaluation
# ==============================================================================
# 既存のモデルディレクトリ（models/merged 等）から一括でモデルパスを収集し、
# 予備実験（TrustLLM / BeaverTails）用の評価を1モデルごとに並列で実行します。
# ==============================================================================

# --submit オプションが指定された場合は自動で全モデル数を取得し sbatch を投入
if [ "$1" == "--submit" ]; then
    mkdir -p logs
    
    MODEL_DIR=${2:-"models/merged"}
    LIMIT=${3:-320}
    OUTPUT_DIR=${4:-"results/preliminary/merged"}
    
    # config.json が存在するディレクトリから main モデルのみ抽出 (ablation 除外、ソート)
    MODELS_LIST=($(find "${MODEL_DIR}" -type f -name "config.json" -exec dirname {} \; | grep -v "ablation" | sort))
    TOTAL_MODELS=${#MODELS_LIST[@]}
    
    if [ "${TOTAL_MODELS}" -eq 0 ]; then
        echo "Error: No main models found in ${MODEL_DIR}"
        exit 1
    fi
    CHUNK_SIZE=500
    CONCURRENT_JOBS=20
    echo "Submitting Per-Model Preliminary Eval Slurm Job Array (${TOTAL_MODELS} main models total, in chunks of ${CHUNK_SIZE})..."
    
    for (( start=0; start<TOTAL_MODELS; start+=CHUNK_SIZE )); do
        end=$(( start + CHUNK_SIZE - 1 ))
        if [ "$end" -ge "$TOTAL_MODELS" ]; then
            end=$(( TOTAL_MODELS - 1 ))
        fi
        echo "Submitting sbatch array=${start}-${end}%${CONCURRENT_JOBS}..."
        sbatch --export=ALL,MODEL_DIR="${MODEL_DIR}",LIMIT="${LIMIT}",OUTPUT_DIR="${OUTPUT_DIR}" --array=${start}-${end}%${CONCURRENT_JOBS} "$0"
    done
    exit 0
fi

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_prelim_${JOB_ID}"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

TASK_ID=${SLURM_ARRAY_TASK_ID:-0}
MODEL_DIR=${MODEL_DIR:-"models/merged"}
LIMIT=${LIMIT:-320}
OUTPUT_DIR=${OUTPUT_DIR:-"results/preliminary/merged"}

# モデルリストの再取得（ablation 除外、インデックスで指定）
MODELS_LIST=($(find "${MODEL_DIR}" -type f -name "config.json" -exec dirname {} \; | grep -v "ablation" | sort))
TARGET_MODEL=${MODELS_LIST[$TASK_ID]}

echo "=================================================="
echo "Slurm Per-Model Prelim Array Job ID: ${SLURM_ARRAY_JOB_ID:-N/A}_${TASK_ID}"
echo "Target Model: ${TARGET_MODEL}"
echo "Limit: ${LIMIT}"
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

cmd="${PYTHON_EXEC} scripts/eval/eval_preliminary.py \
    --model_path \"${TARGET_MODEL}\" \
    --output_dir \"${OUTPUT_DIR}\" \
    --limit ${LIMIT}"

echo "Executing command:"
echo "${cmd}"
echo "--------------------------------------------------"

eval ${cmd}
