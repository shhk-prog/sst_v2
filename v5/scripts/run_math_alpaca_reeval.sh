#!/bin/bash
# ==============================================================================
# SoK 数学有用性評価の修復ランチャー（WizardMath 公式 Alpaca-CoT プロンプト）
#
# 使い方:
#   Step A（まず単体スモーク確認: WizardMath-7B-V1.0 で ~50% が出るか確認、約 3〜5 分）:
#     CUDA_VISIBLE_DEVICES=0 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_reeval.sh smoke
#
#   Step B（全 safety+math モデル再評価: seed42/43/44 を指定 GPU で実行、1 件ずつ逐次保存＋途中再開）:
#     CUDA_VISIBLE_DEVICES=1 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_reeval.sh seed 42
#     CUDA_VISIBLE_DEVICES=2 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_reeval.sh seed 43
#     CUDA_VISIBLE_DEVICES=3 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_reeval.sh seed 44
# ==============================================================================

set -euo pipefail

MODE="${1:-smoke}"
SEED_ARG="${2:-42}"

ROOT="/mnt/nas/home/hiromi/src/sst_v2"
V3_DIR="${ROOT}/v3"
V5_DIR="${ROOT}/v5"
PY="${V3_DIR}/venv_v3/bin/python"
EVAL_SCRIPT="${V5_DIR}/scripts/eval_math_alpaca_cot.py"
OUT_ROOT="${V5_DIR}/results/math_alpaca_cot"

mkdir -p "${OUT_ROOT}"

export OMP_NUM_THREADS=8
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ENABLE_V1=0

run_one() {
    local M_NAME="$1"
    local M_PATH="$2"
    local OUT_FILE="$3"
    if [[ ! -d "${M_PATH}" && "${M_PATH}" != *"/"* ]]; then
        echo "[WARN] skip missing path: ${M_PATH}"
        return 0
    fi
    echo "--------------------------------------------------"
    echo "[GSM8K Alpaca-CoT] ${M_NAME} -> $(basename "${OUT_FILE}")"
    "${PY}" "${EVAL_SCRIPT}" \
        --model-path "${M_PATH}" \
        --model-name "${M_NAME}" \
        --output-file "${OUT_FILE}" \
        --limit 320 \
        --max-tokens 512 \
        --gpu-memory-utilization "${GPU_MEM_UTIL:-0.85}"
}

if [[ "${MODE}" == "smoke" ]]; then
    mkdir -p "${OUT_ROOT}/base"
    # WizardMath-7B-V1.0 単体（公式 54.9% 付近・50% 前後が出ることを確認）
    run_one "WizardMath-7B-V1.0" \
        "WizardLMTeam/WizardMath-7B-V1.0" \
        "${OUT_ROOT}/base/WizardMath-7B-V1.0_gsm8k_alpaca_cot.json"
    # Llama-2-7b-hf ベース単体 & SafetyFT seed42 単体（参照点）
    run_one "Llama-2-7b-hf" \
        "meta-llama/Llama-2-7b-hf" \
        "${OUT_ROOT}/base/Llama-2-7b-hf_gsm8k_alpaca_cot.json"
    run_one "SafetyFT_seed42" \
        "${V3_DIR}/models/temp_safety_full_seed42" \
        "${OUT_ROOT}/base/SafetyFT_seed42_gsm8k_alpaca_cot.json"
    exit 0
fi

if [[ "${MODE}" == "seed" ]]; then
    S="${SEED_ARG}"
    OUT_S="${OUT_ROOT}/seed${S}"
    mkdir -p "${OUT_S}"

    # 1. fp32 SST (v5) 全 6 α
    for A in 0.0 0.2 0.4 0.6 0.8 1.0; do
        M_NAME="fp32_sst_safety+math_alpha${A}_n500_k0.2_seed${S}"
        M_PATH="${V5_DIR}/models/fp32_sst_math/${M_NAME}"
        [[ -d "${M_PATH}" ]] && run_one "${M_NAME}" "${M_PATH}" "${OUT_S}/${M_NAME}_gsm8k_alpaca_cot.json"
    done

    # 2. v3 主実験 α スイープ手法（fp16 SST / Data-Free SST / TA / TIES / DARE / DELLA）
    for A in 0.0 0.2 0.4 0.6 0.8 1.0; do
        for PREFIX in \
            "sst_merge_v3_main_diagonal_sst_main_safety+math_alpha${A}_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}" \
            "sst_merge_v3_main_data_free_sst_main_safety+math_alpha${A}_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}" \
            "sst_merge_v3_main_task_arithmetic_safety+math_alpha${A}_seed${S}" \
            "sst_merge_v3_main_ties_safety+math_alpha${A}_seed${S}" \
            "sst_merge_v3_main_dare_safety+math_alpha${A}_seed${S}" \
            "sst_merge_v3_main_della_safety+math_alpha${A}_seed${S}"; do
            M_PATH="${V3_DIR}/models/merged/${PREFIX}"
            [[ -d "${M_PATH}" ]] && run_one "${PREFIX}" "${M_PATH}" "${OUT_S}/${PREFIX}_gsm8k_alpaca_cot.json"
        done
    done

    # 3. v3 単発手法（Matena-Fisher / SafeMERGE / LED-Merging / MergeAlign）
    for PREFIX in \
        "sst_merge_v3_main_matena_fisher_safety+math_seed${S}" \
        "sst_merge_v3_main_safemerge_safety+math_seed${S}" \
        "sst_merge_v3_main_led_merging_safety+math_seed${S}" \
        "sst_merge_v3_main_mergealign_safety+math_seed${S}"; do
        M_PATH="${V3_DIR}/models/merged/${PREFIX}"
        [[ -d "${M_PATH}" ]] && run_one "${PREFIX}" "${M_PATH}" "${OUT_S}/${PREFIX}_gsm8k_alpaca_cot.json"
    done

    echo "完了 (math_alpaca_cot seed=${S}): $(date -Iseconds)"
    exit 0
fi

echo "Unknown mode: ${MODE} (expected 'smoke' or 'seed')" >&2
exit 1
