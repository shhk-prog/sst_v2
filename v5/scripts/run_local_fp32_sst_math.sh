#!/bin/bash
# ==============================================================================
# SoK 実証 2: SLURM を使わず 3 つの seed（42, 43, 44）を 3 枚の GPU で並列実行するランチャー
#
# 使い方（健全な GPU が 3 枚以上あるノード、例: iag-02 上で 1 行実行）:
#   nohup bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_local_fp32_sst_math.sh 0 1 2 \
#     >> /mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp2/logs/local_launcher.log 2>&1 &
#
# オプション環境変数:
#   STAGGER=0     # マージ開始をずらす秒数（空きメモリ < 150GB なら STAGGER=900）
#   CPUS_PER_TASK=8
# ==============================================================================

set -euo pipefail

GPU0="${1:-0}"
GPU1="${2:-1}"
GPU2="${3:-2}"
GPUS=("${GPU0}" "${GPU1}" "${GPU2}")
STAGGER="${STAGGER:-0}"
CPUS_PER_TASK="${CPUS_PER_TASK:-8}"

ROOT="/mnt/nas/home/hiromi/src/sst_v2"
LOG_DIR="${ROOT}/v5/outputs/sok_exp2/logs"
mkdir -p "${LOG_DIR}"

echo "=================================================="
echo "Local Launcher Start: $(date -Iseconds) | Host: $(hostname)"
echo "GPUs: ${GPUS[*]} | STAGGER=${STAGGER}s | CPUS_PER_TASK=${CPUS_PER_TASK}"
nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,memory.total,driver_version --format=csv 2>&1 || true
echo "=================================================="

PIDS=()
for i in 0 1 2; do
    GPU="${GPUS[$i]}"
    CUDA_VISIBLE_DEVICES="${GPU}" \
    SLURM_ARRAY_TASK_ID="${i}" \
    SLURM_CPUS_PER_TASK="${CPUS_PER_TASK}" \
        bash "${ROOT}/v5/scripts/slurm_fp32_sst_math.sh" \
        >> "${LOG_DIR}/local_task${i}.log" 2>&1 &
    PID=$!
    PIDS+=("${PID}")
    echo "task ${i} (GPU ${GPU}) PID ${PID} started at $(date -Iseconds)"
    if [[ "${i}" -lt 2 && "${STAGGER}" -gt 0 ]]; then
        sleep "${STAGGER}"
    fi
done

FAIL=0
for idx in 0 1 2; do
    if wait "${PIDS[$idx]}"; then
        echo "task ${idx} OK at $(date -Iseconds)"
    else
        RC=$?
        echo "task ${idx} FAILED (exit=${RC}) at $(date -Iseconds)"
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
