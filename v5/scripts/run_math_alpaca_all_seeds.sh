#!/bin/bash
# ==============================================================================
# SoK 数学有用性（WizardMath 公式 Alpaca-CoT GSM8K）可変 GPU 並列ランチャー（1〜3 枚対応）
#   - 引数で渡した GPU 枚数に応じて seed 42, 43, 44 を衝突なく自動割り当て:
#       * 3 枚指定 (例: 0 1 2): GPU0=seed42, GPU1=seed43, GPU2=seed44（3 並列）
#       * 2 枚指定 (例: 1 2)  : GPU1=seed42->seed44(直列), GPU2=seed43（2 並列、OOM なし）
#       * 1 枚指定 (例: 1)    : GPU1=seed42->seed43->seed44（直列）
#   - 使い方（1 行実行）:
#       nohup bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_math_alpaca_all_seeds.sh 1 2 \
#         >> /mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp2/logs/math_alpaca_launcher.log 2>&1 &
# ==============================================================================

set -euo pipefail

if [[ $# -eq 0 ]]; then
    GPUS=(0 1 2)
else
    GPUS=("$@")
fi
N_GPUS=${#GPUS[@]}
SEEDS=(42 43 44)

ROOT="/mnt/nas/home/hiromi/src/sst_v2"
LOG_DIR="${ROOT}/v5/outputs/sok_exp2/logs"
mkdir -p "${LOG_DIR}"

echo "=================================================="
echo "Math Alpaca-CoT Launcher Start: $(date -Iseconds) | Host: $(hostname)"
echo "GPUs (${N_GPUS} parallel): ${GPUS[*]} | Seeds: ${SEEDS[*]}"
nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,memory.total,driver_version --format=csv 2>&1 || true
echo "=================================================="

PIDS=()
WORKER_LABELS=()

for g_idx in $(seq 0 $((N_GPUS - 1))); do
    GPU="${GPUS[$g_idx]}"
    ASSIGNED_SEEDS=()
    for s_idx in "${!SEEDS[@]}"; do
        if (( s_idx % N_GPUS == g_idx )); then
            ASSIGNED_SEEDS+=("${SEEDS[$s_idx]}")
        fi
    done
    if [[ ${#ASSIGNED_SEEDS[@]} -eq 0 ]]; then
        continue
    fi

    (
        set -euo pipefail
        for S in "${ASSIGNED_SEEDS[@]}"; do
            echo "[worker GPU ${GPU}] seed ${S} start $(date -Iseconds)"
            CUDA_VISIBLE_DEVICES="${GPU}" \
                bash "${ROOT}/v5/scripts/run_math_alpaca_reeval.sh" seed "${S}" \
                >> "${LOG_DIR}/math_alpaca_seed${S}.log" 2>&1
            echo "[worker GPU ${GPU}] seed ${S} OK $(date -Iseconds)"
        done
    ) &
    PID=$!
    PIDS+=("${PID}")
    WORKER_LABELS+=("GPU ${GPU} (seeds: ${ASSIGNED_SEEDS[*]})")
    echo "worker GPU ${GPU} (seeds: ${ASSIGNED_SEEDS[*]}) PID ${PID} started at $(date -Iseconds)"
done

FAIL=0
for w_idx in "${!PIDS[@]}"; do
    if wait "${PIDS[$w_idx]}"; then
        echo "worker ${WORKER_LABELS[$w_idx]} OK at $(date -Iseconds)"
    else
        RC=$?
        echo "worker ${WORKER_LABELS[$w_idx]} FAILED (exit=${RC}) at $(date -Iseconds)"
        FAIL=1
    fi
done

if [[ "${FAIL}" -eq 0 ]]; then
    echo "all done: $(date -Iseconds)"
    exit 0
else
    echo "finished with errors: $(date -Iseconds)"
    exit 1
fi
