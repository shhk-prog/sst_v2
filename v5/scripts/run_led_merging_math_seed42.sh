#!/usr/bin/env bash
# パッチ適用済み LED-Merging で safety+math (seed 42、公式既定設定) を 1 点やり直し、
# 重み退化ゲート確認 → ロック済み GSM8K Alpaca-CoT (n=320) → 安全性 4 ベンチ＋HarmBench 再分類まで実行する。
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

LED_PY="/mnt/nas/home/hiromi/src/sst_v2/v3/venv_led/bin/python"
V3_PY="/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python"
MODEL_DIR="/mnt/nas/home/hiromi/src/sst_v2/v5/models/led_merging_patched_safety+math_seed42"
MNAME="led_merging_patched_safety+math_seed42"

echo "=== LED-Merging Patched (safety+math, seed42) Start: $(date -Iseconds) | Host: $(hostname) | CVD=${CUDA_VISIBLE_DEVICES:-unset} ===" | tee -a "$RUN_DIR/logs/run.log"
nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used --format=csv | tee -a "$RUN_DIR/logs/run.log"

export OMP_NUM_THREADS=8
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ENABLE_V1=0

mkdir -p "$RUN_DIR/outputs/safety"

# 1) パッチ済みマージ＋重み退化監査
CMD1=("$LED_PY" /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/led_merging_patched.py --run-dir "$RUN_DIR" --seed 42 --output-model-dir "$MODEL_DIR")
printf '%q ' "${CMD1[@]}" >> "$RUN_DIR/commands.sh"; echo "" >> "$RUN_DIR/commands.sh"
"${CMD1[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"

# 2) ロック済み GSM8K Alpaca-CoT (n=320)
CMD2=("$V3_PY" /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_math_alpaca_cot.py --model-path "$MODEL_DIR" --model-name "$MNAME" --output-file "$RUN_DIR/outputs/${MNAME}_gsm8k_alpaca_cot.json" --limit 320 --gpu-memory-utilization "$GPU_MEM_UTIL")
printf '%q ' "${CMD2[@]}" >> "$RUN_DIR/commands.sh"; echo "" >> "$RUN_DIR/commands.sh"
"${CMD2[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"

# 3) 安全性 4 ベンチ（streaming）＋ HarmBench 公式分類器再分類
pushd /mnt/nas/home/hiromi/src/sst_v2/v3 >/dev/null
CMD3=("$V3_PY" /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_safety_streaming.py --model_path "$MODEL_DIR" --config configs/config_main.yaml --tasks harmbench,jailbreakbench,strongreject,wildjailbreak --output_dir "$RUN_DIR/outputs/safety" --model_name "$MNAME" --limit 320 --batch_size 32 --use_vllm)
printf '%q ' "${CMD3[@]}" >> "$RUN_DIR/commands.sh"; echo "" >> "$RUN_DIR/commands.sh"
"${CMD3[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"

CMD4=("$V3_PY" /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/reclassify_harmbench_streaming.py --results_dir "$RUN_DIR/outputs/safety" --output_summary_dir "$RUN_DIR/outputs/safety/summary_tables" --batch_size 32 --update_primary_asr)
printf '%q ' "${CMD4[@]}" >> "$RUN_DIR/commands.sh"; echo "" >> "$RUN_DIR/commands.sh"
"${CMD4[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
popd >/dev/null

echo "=== LED-Merging Patched (safety+math, seed42) Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
