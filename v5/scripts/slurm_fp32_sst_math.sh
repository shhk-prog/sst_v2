#!/bin/bash
#SBATCH --job-name=sok_fp32_sst_math
#SBATCH --output=/mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp2/logs/slurm_%A_%a.log
#SBATCH --error=/mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp2/logs/slurm_%A_%a.log
#SBATCH --partition=h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --array=0-2
#SBATCH --chdir=/mnt/nas/home/hiromi/src/sst_v2/v3

# ==============================================================================
# SoK 実証 2: safety+math の fp32 SST-Merge（厳密 index top-k）再マージ＋検証＋評価
#   - Array 0 -> seed 42, Array 1 -> seed 43, Array 2 -> seed 44
#   - α = 0.0, 0.2, 0.4, 0.6, 0.8, 1.0（各 seed 6 モデル、計 18 モデル）
#   - 逐次保存・途中再開対応:
#       * マージ: 1 α モデルごとに原子保存（保存済みモデルは自動スキップ）
#       * 安全性評価（生成・分類）: 1 件ごとに原子保存（eval_safety_streaming.py）
#       * 有用性評価（lm-eval 生成）: 1 件ごとに JSONL 追記＋fsync（eval_utility_streaming.py）
#       * HarmBench 再分類: 1 件ごとに原子保存（reclassify_harmbench_streaming.py）
#   - マージ直後に CPU 検証（α=0, α=1, α=0.6 注入比, config.json）を通過しない場合は即中止
#   - seed 42 ジョブでは同 GPU で v3 対照モデル 2 本（TA α=0.6 / fp16 SST α=0.6）も再評価
#   - 出力はすべて v5/ 配下（v3/ は読み取り専用）
# ==============================================================================

set -euo pipefail

SEEDS=(42 43 44)
SEED=${SEEDS[${SLURM_ARRAY_TASK_ID}]}
ALPHAS=(0.0 0.2 0.4 0.6 0.8 1.0)
LIMIT=320
BATCH_SIZE=32

ROOT="/mnt/nas/home/hiromi/src/sst_v2"
V3_DIR="${ROOT}/v3"
V5_DIR="${ROOT}/v5"
PYTHON_EXEC="${V3_DIR}/venv_v3/bin/python"
MODELS_ROOT="${V5_DIR}/models/fp32_sst_math"
RESULTS_DIR="${V5_DIR}/results/fp32_sst_math/seed${SEED}"
CONTROLS_DIR="${V5_DIR}/results/fp32_sst_math/controls_seed42"
LOG_DIR="${V5_DIR}/outputs/sok_exp2/logs"

mkdir -p "${MODELS_ROOT}" "${RESULTS_DIR}" "${LOG_DIR}"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ENABLE_V1=0
export HF_ALLOW_CODE_EVAL=1

echo "=================================================="
echo "Job: ${SLURM_ARRAY_JOB_ID:-local}_${SLURM_ARRAY_TASK_ID:-0} | Seed: ${SEED}"
echo "Host: $(hostname) | CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-all}"
echo "Python: ${PYTHON_EXEC}"
echo "Models out: ${MODELS_ROOT}"
echo "Results out: ${RESULTS_DIR}"
echo "Start: $(date -Iseconds)"
echo "=================================================="

# 0. 実行 GPU・環境情報の記録（v5/outputs/sok_exp2/gpu_info_seed${SEED}.json + ログ出力）
GPU_INFO_OUT="${V5_DIR}/outputs/sok_exp2/gpu_info_seed${SEED}.json"
"${PYTHON_EXEC}" - "${SEED}" "${GPU_INFO_OUT}" <<'PYEOF'
import json, os, socket, subprocess, sys
from datetime import datetime, timezone
import torch

seed = int(sys.argv[1])
out_path = sys.argv[2]
cvd = os.environ.get("CUDA_VISIBLE_DEVICES", "")

nvidia_gpus = []
try:
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,uuid,pci.bus_id,memory.total,driver_version",
        "--format=csv,noheader",
    ]
    if cvd:
        cmd.extend(["-i", cvd])
    raw = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    for line in raw.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            nvidia_gpus.append({
                "index": parts[0],
                "name": parts[1],
                "uuid": parts[2],
                "pci_bus_id": parts[3],
                "memory_total": parts[4],
                "driver_version": parts[5],
            })
except Exception as exc:
    nvidia_gpus = [{"error": str(exc)}]

torch_gpus = []
if torch.cuda.is_available():
    for idx in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(idx)
        torch_gpus.append({
            "logical_index": idx,
            "name": torch.cuda.get_device_name(idx),
            "total_memory_gb": round(props.total_memory / (1024 ** 3), 2),
            "compute_capability": f"{props.major}.{props.minor}",
        })

try:
    import vllm
    vllm_ver = getattr(vllm, "__version__", "unknown")
except Exception:
    vllm_ver = None

info = {
    "seed": seed,
    "hostname": socket.gethostname(),
    "slurm_job_id": os.environ.get("SLURM_ARRAY_JOB_ID") or os.environ.get("SLURM_JOB_ID") or "local",
    "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID", ""),
    "cuda_visible_devices": cvd,
    "nvidia_smi_gpus": nvidia_gpus,
    "torch_gpus": torch_gpus,
    "torch_version": torch.__version__,
    "torch_cuda_version": torch.version.cuda,
    "vllm_version": vllm_ver,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

tmp = out_path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(info, f, indent=2, ensure_ascii=False)
    f.flush()
    os.fsync(f.fileno())
os.replace(tmp, out_path)
print("[GPU Info]", json.dumps(info, ensure_ascii=False), flush=True)
PYEOF

# 1. fp32 SST-Merge（② 224 キー・形状整合性検証＋全 224 テンソル実効マスク比率検証＋1 α ごと原子保存）
echo "[Step 1] fp32 SST-Merge 実行 (seed=${SEED}, alphas=${ALPHAS[*]})"
"${PYTHON_EXEC}" "${V5_DIR}/scripts/merge_fp32_sst_math.py" \
    --seeds "${SEED}" \
    --alphas "${ALPHAS[@]}" \
    --k 0.20 \
    --eps 1e-6 \
    --mask-tol 0.05 \
    --mask-mode fp32 \
    --out-models-root "${MODELS_ROOT}" \
    --summary-out "${V5_DIR}/outputs/sok_exp2/mask_summary_seed${SEED}.json" \
    --device cuda

# 1b. マージ直後の CPU 健全性検証（α=0 一致, α=1 置換率~20%, α=0.6 注入比低下, config.json）
echo "[Step 1b] マージ直後 CPU 検証 (seed=${SEED})"
CUDA_VISIBLE_DEVICES="" "${PYTHON_EXEC}" "${V5_DIR}/scripts/verify_fp32_merged_models.py" \
    --seeds "${SEED}" \
    --models-root "${MODELS_ROOT}" \
    --out-dir "${V5_DIR}/outputs/sok_exp2" \
    --k 0.20 \
    --tol 0.05

# 2. 各 α モデルの安全性（4 ベンチ、1 件ずつ保存）＋ Math 有用性（gsm8k, minerva_math500、1 件ずつ保存）評価
cd "${V3_DIR}"
for ALPHA in "${ALPHAS[@]}"; do
    MODEL_NAME="fp32_sst_safety+math_alpha${ALPHA}_n500_k0.2_seed${SEED}"
    MODEL_PATH="${MODELS_ROOT}/${MODEL_NAME}"

    echo "--------------------------------------------------"
    echo "[Step 2a] 安全性評価 (4 bench, 1件ずつ逐次保存): ${MODEL_NAME}"
    "${PYTHON_EXEC}" "${V5_DIR}/scripts/eval_safety_streaming.py" \
        --model_path "${MODEL_PATH}" \
        --config configs/config_main.yaml \
        --tasks harmbench,jailbreakbench,strongreject,wildjailbreak \
        --output_dir "${RESULTS_DIR}" \
        --model_name "${MODEL_NAME}" \
        --limit "${LIMIT}" \
        --batch_size "${BATCH_SIZE}" \
        --use_vllm

    echo "[Step 2b] Math 有用性評価 (gsm8k, minerva_math500, 1件ずつ逐次保存): ${MODEL_NAME}"
    "${PYTHON_EXEC}" "${V5_DIR}/scripts/eval_utility_streaming.py" \
        --model_path "${MODEL_PATH}" \
        --config configs/config_main.yaml \
        --tasks gsm8k,minerva_math500 \
        --output_file "${RESULTS_DIR}/${MODEL_NAME}_utility_math.json" \
        --limit "${LIMIT}" \
        --batch_size "${BATCH_SIZE}" \
        --use_vllm
done

# 3. HarmBench 13B 分類器による全安全性結果の 1 件ずつ逐次再分類（v3 と同一判定・途中再開対応）
echo "--------------------------------------------------"
echo "[Step 3] HarmBench 逐次再分類 (1件ずつ保存): ${RESULTS_DIR}"
"${PYTHON_EXEC}" "${V5_DIR}/scripts/reclassify_harmbench_streaming.py" \
    --results_dir "${RESULTS_DIR}" \
    --output_summary_dir "${RESULTS_DIR}/summary_tables" \
    --batch_size "${BATCH_SIZE}" \
    --update_primary_asr

# 4. seed 42 のみ: GPU 差の対照として既存 v3 モデル 2 本を同じ GPU で再評価（1 件ずつ逐次保存）
if [[ "${SEED}" == "42" ]]; then
    mkdir -p "${CONTROLS_DIR}"
    CTRL_NAMES=(
        "ctrl_v3_task_arithmetic_safety+math_alpha0.6_seed42"
        "ctrl_v3_diagonal_sst_safety+math_alpha0.6_seed42"
    )
    CTRL_PATHS=(
        "${V3_DIR}/models/merged/sst_merge_v3_main_task_arithmetic_safety+math_alpha0.6_seed42"
        "${V3_DIR}/models/merged/sst_merge_v3_main_diagonal_sst_main_safety+math_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42"
    )

    for i in 0 1; do
        C_NAME="${CTRL_NAMES[$i]}"
        C_PATH="${CTRL_PATHS[$i]}"
        echo "--------------------------------------------------"
        echo "[Step 4a] 対照モデル安全性評価 (4 bench, 1件ずつ保存): ${C_NAME}"
        "${PYTHON_EXEC}" "${V5_DIR}/scripts/eval_safety_streaming.py" \
            --model_path "${C_PATH}" \
            --config configs/config_main.yaml \
            --tasks harmbench,jailbreakbench,strongreject,wildjailbreak \
            --output_dir "${CONTROLS_DIR}" \
            --model_name "${C_NAME}" \
            --limit "${LIMIT}" \
            --batch_size "${BATCH_SIZE}" \
            --use_vllm

        echo "[Step 4b] 対照モデル Math 有用性評価 (1件ずつ保存): ${C_NAME}"
        "${PYTHON_EXEC}" "${V5_DIR}/scripts/eval_utility_streaming.py" \
            --model_path "${C_PATH}" \
            --config configs/config_main.yaml \
            --tasks gsm8k,minerva_math500 \
            --output_file "${CONTROLS_DIR}/${C_NAME}_utility_math.json" \
            --limit "${LIMIT}" \
            --batch_size "${BATCH_SIZE}" \
            --use_vllm
    done

    echo "[Step 4c] 対照モデル HarmBench 逐次再分類 (1件ずつ保存): ${CONTROLS_DIR}"
    "${PYTHON_EXEC}" "${V5_DIR}/scripts/reclassify_harmbench_streaming.py" \
        --results_dir "${CONTROLS_DIR}" \
        --output_summary_dir "${CONTROLS_DIR}/summary_tables" \
        --batch_size "${BATCH_SIZE}" \
        --update_primary_asr
fi

echo "=================================================="
echo "完了 (seed=${SEED}): $(date -Iseconds)"
echo "=================================================="
