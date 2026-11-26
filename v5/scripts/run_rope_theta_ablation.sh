#!/bin/bash
# ==============================================================================
# SoK P4 因果切り分け実験: safety+code (α=0.6, seed42) で rope_theta=1,000,000 に直した 3 モデルの評価
#   - 対象: task_arithmetic, dare, diagonal_sst（重みは v3 のシンボリックリンク、config.json のみ修正）
#   - 1 件ずつ逐次保存（eval_safety_streaming.py / eval_utility_streaming.py / reclassify_harmbench_streaming.py）
#   - 使い方（iag-02 などの健全な GPU ノード上で実行）:
#       CUDA_VISIBLE_DEVICES=0 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_rope_theta_ablation.sh
# ==============================================================================

set -euo pipefail

ROOT="/mnt/nas/home/hiromi/src/sst_v2"
V3_DIR="${ROOT}/v3"
V5_DIR="${ROOT}/v5"
PY="${V3_DIR}/venv_v3/bin/python"
MODELS_ROOT="${V5_DIR}/models/rope_theta_ablation"
RESULTS_DIR="${V5_DIR}/results/rope_theta_ablation"

mkdir -p "${RESULTS_DIR}"

export OMP_NUM_THREADS=8
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ENABLE_V1=0
export HF_ALLOW_CODE_EVAL=1

# 0. シンボリックリンクモデルの作成（冪等）
"${PY}" "${V5_DIR}/scripts/prepare_rope_theta_ablation.py"

cd "${V3_DIR}"
for KEY in task_arithmetic_alpha0.6_seed42 dare_alpha0.6_seed42 diagonal_sst_alpha0.6_seed42; do
    MODEL_NAME="rope1e6_safety+code_${KEY}"
    MODEL_PATH="${MODELS_ROOT}/${MODEL_NAME}"

    echo "=================================================="
    echo "[rope_theta=1e6 評価] ${MODEL_NAME} | Start: $(date -Iseconds)"
    echo "=================================================="

    "${PY}" "${V5_DIR}/scripts/eval_safety_streaming.py" \
        --model_path "${MODEL_PATH}" \
        --config configs/config_main.yaml \
        --tasks harmbench,jailbreakbench,strongreject,wildjailbreak \
        --output_dir "${RESULTS_DIR}" \
        --model_name "${MODEL_NAME}" \
        --limit 320 \
        --batch_size 32 \
        --use_vllm

    "${PY}" "${V5_DIR}/scripts/eval_utility_streaming.py" \
        --model_path "${MODEL_PATH}" \
        --config configs/config_main.yaml \
        --tasks humaneval,mbpp \
        --output_file "${RESULTS_DIR}/${MODEL_NAME}_utility_code.json" \
        --limit 320 \
        --batch_size 32 \
        --use_vllm
done

"${PY}" "${V5_DIR}/scripts/reclassify_harmbench_streaming.py" \
    --results_dir "${RESULTS_DIR}" \
    --output_summary_dir "${RESULTS_DIR}/summary_tables" \
    --batch_size 32 \
    --update_primary_asr

echo "=================================================="
echo "[rope_theta=1e6 評価] 全完了: $(date -Iseconds)"
echo "=================================================="
