#!/bin/bash
#SBATCH --job-name=ablation_eval
#SBATCH --output=logs/slurm_ablation_eval_%A/eval_%a.log
#SBATCH --error=logs/slurm_ablation_eval_%A/eval_%a.log
#SBATCH --partition=h100
#SBATCH --qos=interactive_nofs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3
#SBATCH --array=0-11

# ==============================================================================
# Slurm Job Array Script for Parallel Ablation Merge Evaluation
# ==============================================================================
# 3 Sample Sizes: 50, 100, 500
# 4 Patterns:
#   0: safety+math
#   1: safety+code
#   2: safety+medical
#   3: safety+math+code+medical
# Total jobs = 3 * 4 = 12 (ARRAY_TASK_ID 0 to 11)
# Each job requests 1 GPU and runs independently in Slurm queue.
# ==============================================================================

# --submit オプションが指定された場合は sbatch で自身を投入
if [ "$1" == "--submit" ]; then
    mkdir -p logs
    BATCH_SIZE=${BATCH_SIZE:-auto}
    echo "Submitting Ablation Evaluation Slurm Job Array (12 tasks, BATCH_SIZE=${BATCH_SIZE})..."
    sbatch --export=ALL,BATCH_SIZE="${BATCH_SIZE}" "$0"
    exit $?
fi

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_ablation_eval_${JOB_ID}"

SAMPLE_SIZES=(50 100 500)
PATTERNS=(
    "safety+math"
    "safety+code"
    "safety+medical"
    "safety+math+code+medical"
)

NUM_PATTERNS=${#PATTERNS[@]}

TASK_ID=${SLURM_ARRAY_TASK_ID:-0}

SAMPLE_SIZE_INDEX=$(( TASK_ID / NUM_PATTERNS ))
PATTERN_INDEX=$(( TASK_ID % NUM_PATTERNS ))

TARGET_SAMPLE_SIZE=${SAMPLE_SIZES[$SAMPLE_SIZE_INDEX]}
PATTERN=${PATTERNS[$PATTERN_INDEX]}

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

BATCH_SIZE=${BATCH_SIZE:-auto}

# サンプルサイズに応じた一時設定ファイルを準備
CONFIG_TMP="configs/config_ablation_n${TARGET_SAMPLE_SIZE}_tmp.yaml"

if [ ! -f "${CONFIG_TMP}" ]; then
    python3 -c "
import yaml

with open('configs/config_ablation.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

cfg['data']['fim']['sample_sizes'] = [${TARGET_SAMPLE_SIZE}]
cfg['merge']['ablation']['fim_sample_sizes'] = [${TARGET_SAMPLE_SIZE}]

with open('${CONFIG_TMP}', 'w', encoding='utf-8') as f:
    yaml.dump(cfg, f, allow_unicode=True)
"
fi

echo "=================================================="
echo "Slurm Array Job ID: ${SLURM_ARRAY_JOB_ID:-N/A}_${TASK_ID}"
echo "Sample Size: ${TARGET_SAMPLE_SIZE}"
echo "Pattern: ${PATTERN}"
echo "Batch Size: ${BATCH_SIZE}"
echo "Config: ${CONFIG_TMP}"
echo "Assigned CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-0}"
echo "=================================================="

PYTHON_EXEC="python"
if [ -f "venv_v3/bin/python" ]; then
    PYTHON_EXEC="venv_v3/bin/python"
elif [ -f "../venv_sst/bin/python" ]; then
    PYTHON_EXEC="../venv_sst/bin/python"
fi

cmd="${PYTHON_EXEC} scripts/merge_eval_parallel.py \
    --config ${CONFIG_TMP} \
    --seeds 42 43 44 \
    --limit 320 \
    --batch_size ${BATCH_SIZE} \
    --gpus 0 \
    --patterns ${PATTERN} \
    --resume"

echo "Executing command:"
echo "${cmd}"
echo "--------------------------------------------------"

eval ${cmd}
