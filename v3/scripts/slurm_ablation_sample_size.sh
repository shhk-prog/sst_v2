#!/bin/bash
#SBATCH --job-name=ablation_sample_size
#SBATCH --output=logs/slurm_ablation_%A/sample_size_%a.log
#SBATCH --error=logs/slurm_ablation_%A/sample_size_%a.log
#SBATCH --partition=h100
#SBATCH --qos=interactive_nofs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3
#SBATCH --array=0-2

# ==============================================================================
# Slurm Job Array Script for Parallel Ablation by Sample Size (50, 100, 500)
# ==============================================================================
# Task 0 -> sample_size = 50  (1 GPU)
# Task 1 -> sample_size = 100 (1 GPU)
# Task 2 -> sample_size = 500 (1 GPU)
# ==============================================================================

if [ -n "${SLURM_SUBMIT_DIR}" ]; then
    cd "${SLURM_SUBMIT_DIR}"
else
    cd "/mnt/nas/home/hiromi/src/sst_v2/v3"
fi

# 環境変数・Pythonパスの設定
export PYTHONPATH=".:${PYTHONPATH}"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

# 仮想環境の有効化
if [ -f "venv_v3/bin/activate" ]; then
    source venv_v3/bin/activate
fi

JOB_ID=${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-test}}
mkdir -p "logs/slurm_ablation_${JOB_ID}"

SAMPLE_SIZES=(50 100 500)
TASK_ID=${SLURM_ARRAY_TASK_ID:-0}
TARGET_SAMPLE_SIZE=${SAMPLE_SIZES[$TASK_ID]}

echo "=========================================================="
echo "Starting Ablation Experiment for Sample Size: ${TARGET_SAMPLE_SIZE}"
echo "Slurm Job ID: ${JOB_ID}, Task ID: ${TASK_ID}"
echo "Running on Host: $(hostname)"
echo "Assigned GPU: ${CUDA_VISIBLE_DEVICES:-0}"
echo "=========================================================="

# 一時的なサンプルサイズ限定 YAML 設定ファイルを動的生成
CONFIG_TMP="configs/config_ablation_n${TARGET_SAMPLE_SIZE}_tmp.yaml"

python3 -c "
import yaml

with open('configs/config_ablation.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# FIM サンプルサイズおよびアブレーションのサンプルサイズを該当サイズのみに上書き
cfg['data']['fim']['sample_sizes'] = [${TARGET_SAMPLE_SIZE}]
cfg['merge']['ablation']['fim_sample_sizes'] = [${TARGET_SAMPLE_SIZE}]

with open('${CONFIG_TMP}', 'w', encoding='utf-8') as f:
    yaml.dump(cfg, f, allow_unicode=True)
"

echo "Generated temporary config: ${CONFIG_TMP}"

# メージ＆評価の一括実行 (stage = all, merge_group = non_mergekit)
python scripts/run_experiments.py \
    --stage merge \
    --config "${CONFIG_TMP}" \
    --merge_group non_mergekit \
    --resume

STATUS=$?

# 一時設定ファイルのクリーンアップ
rm -f "${CONFIG_TMP}"

if [ ${STATUS} -eq 0 ]; then
    echo "[Success] Finished sample size ${TARGET_SAMPLE_SIZE} evaluation successfully."
else
    echo "[Error] Failed execution for sample size ${TARGET_SAMPLE_SIZE} with exit code ${STATUS}."
fi

exit ${STATUS}
