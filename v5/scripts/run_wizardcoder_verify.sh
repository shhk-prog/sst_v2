#!/usr/bin/env bash
# 指示書 v2 §2.5 #1: WizardCoder-Python-7B-V1.0 公式 HumanEval 検証ゲート実行ランチャー
# 使い方（iag-03 GPU 2 など空き GPU 1 枚で実行）:
#   RUN_DIR=$(CUDA_VISIBLE_DEVICES="" /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/python \
#     /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/new_run.py \
#     --name wizardcoder-humaneval-gate \
#     --why "WizardCoder単体のHumanEval公式形式を検証ゲートに通す（指示書v2 §2.5 #1）" \
#     --what "Llama-2-7b-hf / SafetyFT_seed42 / WizardCoder-Python-7B-V1.0 を公式Alpaca-Code形式でHumanEval全164問評価" \
#     --paper-use "P6事例・コード有用性評価ロック")
#   CUDA_VISIBLE_DEVICES=2 bash /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/run_wizardcoder_verify.sh --run-dir "$RUN_DIR"
set -euo pipefail

RUN_DIR=""
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.85}"
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
SCRIPT="/mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_code_wizardcoder_official.py"
export VLLM_ENABLE_V1=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn

echo "=== WizardCoder HumanEval Gate Start: $(date -Iseconds) | Host: $(hostname) | CVD=${CUDA_VISIBLE_DEVICES:-unset} ===" | tee -a "$RUN_DIR/logs/run.log"
nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used --format=csv | tee -a "$RUN_DIR/logs/run.log"

PROMPT_VARIANT="${PROMPT_VARIANT:-official_tab_nl}"
run_one() {
  local mpath="$1"
  local mname="$2"
  shift 2
  local cmd=("$V3_PY" "$SCRIPT" --run-dir "$RUN_DIR" --model-path "$mpath" --model-name "$mname" --prompt-variant "$PROMPT_VARIANT" --gpu-memory-utilization "$GPU_MEM_UTIL" "$@")
  printf '%q ' "${cmd[@]}" >> "$RUN_DIR/commands.sh"
  echo "" >> "$RUN_DIR/commands.sh"
  "${cmd[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
}

run_one "meta-llama/Llama-2-7b-hf" "Llama-2-7b-hf"
BASE_PASS1=$("$V3_PY" -c "import json; print(json.load(open('$RUN_DIR/outputs/Llama-2-7b-hf_humaneval_${PROMPT_VARIANT}.json'))['humaneval_pass1_pct'])")
run_one "/mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed42" "SafetyFT_seed42" --base-pass1 "$BASE_PASS1"
run_one "vanillaOVO/WizardCoder-Python-7B-V1.0" "WizardCoder-Python-7B-V1.0" --official-value 55.5 --base-pass1 "$BASE_PASS1"

echo "=== WizardCoder HumanEval Gate Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
