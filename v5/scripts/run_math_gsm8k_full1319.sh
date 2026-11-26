#!/usr/bin/env bash
# 指示書 v2 §2.5 #4・§4.3: 論文のブートストラップ比較に使う主要な点の GSM8K 全 1,319 問再評価ランチャー
# 対象（3 seed × 7 点 = 21 本 ＋ 単体参照 3 本 = 計 24 本）:
#   - 単体参照: WizardMath-7B-V1.0, SafetyFT_seed42, Llama-2-7b-hf
#   - fp32 SST (v5): alpha=0.8, 1.0 (seed 42, 43, 44)
#   - fp16 SST (v3): alpha=0.8, 1.0 (seed 42, 43, 44)
#   - Task Arithmetic (v3): alpha=0.6, 0.8 (seed 42, 43, 44)
#   - DARE (v3): alpha=0.6 (seed 42, 43, 44)
# 評価設定: eval_lock.yaml 固定済み WizardMath 公式 Alpaca-CoT (eval_math_alpaca_cot.py --limit 1319)
set -euo pipefail

RUN_DIR=""
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.85}"
USE_BATCHED=0
BATCH_SIZE=128
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    --batched) USE_BATCHED=1; shift ;;
    --batch-size) BATCH_SIZE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$RUN_DIR" || ! -f "$RUN_DIR/RUN.md" ]]; then
  echo "ERROR: --run-dir <dir_with_RUN.md> は必須です（指示書 v2 §1.4）" >&2
  exit 1
fi

V3_PY="/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python"
if [[ "$USE_BATCHED" -eq 1 ]]; then
  SCRIPT="/mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_math_alpaca_cot_batched.py"
else
  SCRIPT="/mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_math_alpaca_cot.py"
fi
V3_M="/mnt/nas/home/hiromi/src/sst_v2/v3/models/merged"
V5_M="/mnt/nas/home/hiromi/src/sst_v2/v5/models/fp32_sst_math"

run_one() {
  local mpath="$1"
  local mname="$2"
  local out_json="$RUN_DIR/outputs/${mname}_gsm8k_full1319.json"
  if [[ -f "$out_json" ]] && "$V3_PY" -c "import json,sys; d=json.load(open('$out_json')); sys.exit(0 if d.get('completed') and d.get('n_total',0)>=1319 else 1)" 2>/dev/null; then
    echo "[SKIP] already done: $mname" | tee -a "$RUN_DIR/logs/run.log"
    return 0
  fi
  local cmd=("$V3_PY" "$SCRIPT" --model-path "$mpath" --model-name "$mname" --output-file "$out_json" --limit 1319 --gpu-memory-utilization "$GPU_MEM_UTIL")
  if [[ "$USE_BATCHED" -eq 1 ]]; then
    cmd+=(--batch-size "$BATCH_SIZE")
  fi
  printf '%q ' "${cmd[@]}" >> "$RUN_DIR/commands.sh"
  echo "" >> "$RUN_DIR/commands.sh"
  "${cmd[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
}

echo "=== GSM8K Full 1319 Key Points Start: $(date -Iseconds) | Host: $(hostname) | CVD=${CUDA_VISIBLE_DEVICES:-unset} ===" | tee -a "$RUN_DIR/logs/run.log"
nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used --format=csv | tee -a "$RUN_DIR/logs/run.log"

# 単体参照 3 本
run_one "WizardLMTeam/WizardMath-7B-V1.0" "WizardMath-7B-V1.0"
run_one "/mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed42" "SafetyFT_seed42"
run_one "meta-llama/Llama-2-7b-hf" "Llama-2-7b-hf"

# 主要点（3 seed × 7 点 = 21 本）
for S in 42 43 44; do
  run_one "$V5_M/fp32_sst_safety+math_alpha0.8_n500_k0.2_seed${S}" "fp32_sst_alpha0.8_seed${S}"
  run_one "$V5_M/fp32_sst_safety+math_alpha1.0_n500_k0.2_seed${S}" "fp32_sst_alpha1.0_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_diagonal_sst_main_safety+math_alpha0.8_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}" "fp16_sst_alpha0.8_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_diagonal_sst_main_safety+math_alpha1.0_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}" "fp16_sst_alpha1.0_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_task_arithmetic_safety+math_alpha0.6_seed${S}" "task_arithmetic_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_task_arithmetic_safety+math_alpha0.8_seed${S}" "task_arithmetic_alpha0.8_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_dare_safety+math_alpha0.6_seed${S}" "dare_alpha0.6_seed${S}"
done

echo "=== GSM8K Full 1319 Key Points Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
