#!/usr/bin/env bash
# 指示書 v2 §2.5 #3: MedAlpaca-7B 公式医療評価検証ゲート（MedQA-USMLE 4-options）
set -euo pipefail

RUN_DIR=""
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.85}"
LIMIT="${LIMIT:-320}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$RUN_DIR" || ! -f "$RUN_DIR/RUN.md" ]]; then
  echo "ERROR: --run-dir <dir_with_RUN.md> は必須です（指示書 v2 §1.4）" >&2
  exit 1
fi

V3_PY="/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python"
SCRIPT="/mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_medical_medalpaca_official.py"

run_one() {
  local mpath="$1"
  local mname="$2"
  local variant="$3"
  shift 3
  local cmd=("$V3_PY" "$SCRIPT" --run-dir "$RUN_DIR" --model-path "$mpath" --model-name "$mname" --prompt-variant "$variant" --limit "$LIMIT" --gpu-memory-utilization "$GPU_MEM_UTIL" "$@")
  printf '%q ' "${cmd[@]}" >> "$RUN_DIR/commands.sh"
  echo "" >> "$RUN_DIR/commands.sh"
  "${cmd[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
}

echo "=== MedAlpaca MedQA Gate Start: $(date -Iseconds) | Host: $(hostname) | CVD=${CUDA_VISIBLE_DEVICES:-unset} ===" | tee -a "$RUN_DIR/logs/run.log"
nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used --format=csv | tee -a "$RUN_DIR/logs/run.log"

for V in official_qa plain_qa; do
  run_one "meta-llama/Llama-2-7b-hf" "Llama-2-7b-hf" "$V"
  BASE_ACC=$("$V3_PY" -c "import json; print(json.load(open('$RUN_DIR/outputs/Llama-2-7b-hf_medqa_${V}.json'))['medqa_acc_pct'])")
  run_one "/mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed42" "SafetyFT_seed42" "$V" --base-acc "$BASE_ACC"
  run_one "medalpaca/medalpaca-7b" "MedAlpaca-7B" "$V" --base-acc "$BASE_ACC"
done

echo "=== MedAlpaca MedQA Gate Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
