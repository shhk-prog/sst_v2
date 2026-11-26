#!/usr/bin/env bash
# 指示書 v2 §2.5 #1（20件目視確認・設定ロック後）:
#   1) rope_theta 切り分け 3 手法（Before 1e4 / After 1e6）
#   2) 表 3 の safety+code 全 10 手法（α=0.6、seed 42/43/44 = 30 本、Before 3 本と重複排除して計 33 本）
# を検証済み official_tab_nl（HumanEval 全 164 問、max_tokens=2048）で一括再評価するランチャー。
# 完了済み JSON があれば自動スキップして途中再開可能。所要時間: H100 1 枚で約 45〜60 分。
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
V3_M="/mnt/nas/home/hiromi/src/sst_v2/v3/models/merged"
V5_M="/mnt/nas/home/hiromi/src/sst_v2/v5/models/rope_theta_ablation"

run_one() {
  local mpath="$1"
  local mname="$2"
  local out_json="$RUN_DIR/outputs/${mname}_humaneval_official_tab_nl.json"
  if [[ -f "$out_json" ]]; then
    echo "[SKIP] already done: $mname" | tee -a "$RUN_DIR/logs/run.log"
    return 0
  fi
  if [[ ! -d "$mpath" ]]; then
    echo "[WARN] model dir missing, skipping: $mpath" | tee -a "$RUN_DIR/logs/run.log"
    return 0
  fi
  local cmd=("$V3_PY" "$SCRIPT" --run-dir "$RUN_DIR" --model-path "$mpath" --model-name "$mname" --prompt-variant official_tab_nl --gpu-memory-utilization "$GPU_MEM_UTIL")
  printf '%q ' "${cmd[@]}" >> "$RUN_DIR/commands.sh"
  echo "" >> "$RUN_DIR/commands.sh"
  "${cmd[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
}

echo "=== Table 3 + rope_theta HumanEval Official Re-eval Start: $(date -Iseconds) | Host: $(hostname) | CVD=${CUDA_VISIBLE_DEVICES:-unset} ===" | tee -a "$RUN_DIR/logs/run.log"
nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used --format=csv | tee -a "$RUN_DIR/logs/run.log"

# 1) rope_theta=1,000,000 (After) 3 本を最優先で実行
run_one "$V5_M/rope1e6_safety+code_task_arithmetic_alpha0.6_seed42" "rope1e6_task_arithmetic_alpha0.6_seed42"
run_one "$V5_M/rope1e6_safety+code_dare_alpha0.6_seed42"            "rope1e6_dare_alpha0.6_seed42"
run_one "$V5_M/rope1e6_safety+code_diagonal_sst_alpha0.6_seed42"    "rope1e6_diagonal_sst_alpha0.6_seed42"

# 2) 表 3 の safety+code 全 10 手法（α=0.6、seed 42/43/44 = 30 本；seed42 の TA/DARE/fp16 SST が rope_theta Before を兼ねる）
for S in 42 43 44; do
  run_one "$V3_M/sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed${S}" "v3_task_arithmetic_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_ties_safety+code_alpha0.6_seed${S}"            "v3_ties_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_dare_safety+code_alpha0.6_seed${S}"            "v3_dare_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_della_safety+code_alpha0.6_seed${S}"           "v3_della_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}" "v3_diagonal_sst_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_data_free_sst_main_safety+code_alpha0.6_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed${S}"     "v3_data_free_sst_alpha0.6_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_matena_fisher_safety+code_seed${S}"            "v3_matena_fisher_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_safemerge_safety+code_seed${S}"                "v3_safemerge_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_led_merging_safety+code_seed${S}"              "v3_led_merging_seed${S}"
  run_one "$V3_M/sst_merge_v3_main_mergealign_safety+code_seed${S}"               "v3_mergealign_seed${S}"
done

echo "=== Table 3 + rope_theta HumanEval Official Re-eval Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
