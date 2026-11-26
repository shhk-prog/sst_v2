#!/usr/bin/env bash
# 指示書 v2 §2.5 #1（20件目視確認後）: rope_theta 切り分け 3 手法（Before 1e4 / After 1e6 の計 6 本）を
# 検証済み official_tab_nl 設定で HumanEval 全 164 問再評価するランチャー。
# 注意: 必ず 20261126-1413_wizardcoder-humaneval-gate-v2 の 20 件目視確認を済ませてから実行すること！
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
  local cmd=("$V3_PY" "$SCRIPT" --run-dir "$RUN_DIR" --model-path "$mpath" --model-name "$mname" --prompt-variant official_tab_nl --gpu-memory-utilization "$GPU_MEM_UTIL")
  printf '%q ' "${cmd[@]}" >> "$RUN_DIR/commands.sh"
  echo "" >> "$RUN_DIR/commands.sh"
  "${cmd[@]}" 2>&1 | tee -a "$RUN_DIR/logs/run.log"
}

echo "=== rope_theta HumanEval Official Re-eval Start: $(date -Iseconds) | Host: $(hostname) ===" | tee -a "$RUN_DIR/logs/run.log"
run_one "$V3_M/sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed42" "before1e4_task_arithmetic"
run_one "$V5_M/rope1e6_safety+code_task_arithmetic_alpha0.6_seed42"           "after1e6_task_arithmetic"
run_one "$V3_M/sst_merge_v3_main_dare_safety+code_alpha0.6_seed42"            "before1e4_dare"
run_one "$V5_M/rope1e6_safety+code_dare_alpha0.6_seed42"                      "after1e6_dare"
run_one "$V3_M/sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42" "before1e4_diagonal_sst"
run_one "$V5_M/rope1e6_safety+code_diagonal_sst_alpha0.6_seed42"              "after1e6_diagonal_sst"
echo "=== rope_theta HumanEval Official Re-eval Done: $(date -Iseconds) ===" | tee -a "$RUN_DIR/logs/run.log"
