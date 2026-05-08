#!/bin/bash
# SST-Merge V4 Grid Search Script
# 
# Usage:
#   ./grid_search.sh                    # Run full grid search
#   ./grid_search.sh --dry-run          # Show commands without running
#   nohup ./grid_search.sh &            # Run in background

set -e

# ============================================
# Configuration
# ============================================
MODELS=("llama3.1-8b" "mistral-7b-v0.1" "mistral-7b-v0.2" "qwen2.5-3b")
K_VALUES=(5 10 20 30)
# 補間型マージ: α = Safety比率 (0-1)
# α=0.5: 50% Utility + 50% Safety
# α=0.7: 30% Utility + 70% Safety (Safety重視)
# α=0.9: 10% Utility + 90% Safety (Safety最優先)
W_VALUES=(0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9)
LAYERWISE_OPTIONS=("yes" "no")
NUM_EPOCHS=5
EVAL_SAMPLES=500

# ============================================
# Setup
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ログディレクトリを作成
LOG_DIR="logs/grid_search_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# 全体ログ
MASTER_LOG="$LOG_DIR/master.log"

# Dry run check
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE ==="
fi

# ============================================
# Functions
# ============================================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MASTER_LOG"
}

run_experiment() {
    local model=$1
    local k=$2
    local w=$3
    local layerwise=$4
    
    if [ "$layerwise" = "no" ]; then
        layerwise_flag="--no_layerwise"
        lw_str="uniform"
    else
        layerwise_flag=""
        lw_str="layerwise"
    fi
    
    # 個別ログファイル名（パラメータを含む）
    LOG_FILE="$LOG_DIR/${model}_k${k}_w${w}_${lw_str}.log"
    
    log "=========================================="
    log "Model=$model, k=$k, w=$w, layerwise=$layerwise"
    log "Log: $LOG_FILE"
    log "=========================================="
    
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] python scripts/run_full_pipeline.py --model $model --num_epochs $NUM_EPOCHS --sst_k $k --sst_weight $w --eval_samples $EVAL_SAMPLES $layerwise_flag"
        return 0
    fi
    
    # 実行
    python scripts/run_full_pipeline.py \
        --model $model \
        --num_epochs $NUM_EPOCHS \
        --sst_k $k \
        --sst_weight $w \
        --eval_samples $EVAL_SAMPLES \
        $layerwise_flag \
        2>&1 | tee "$LOG_FILE"
    
    # 結果サマリーをマスターログに追加
    echo "" >> "$MASTER_LOG"
    grep -A 12 "COMPARISON SUMMARY" "$LOG_FILE" >> "$MASTER_LOG" 2>/dev/null || echo "  No summary found" >> "$MASTER_LOG"
    echo "" >> "$MASTER_LOG"
}

# ============================================
# Main
# ============================================
log "============================================"
log "SST-Merge V4 Grid Search"
log "============================================"
log "Models: ${MODELS[*]}"
log "K values: ${K_VALUES[*]}"
log "Weight values: ${W_VALUES[*]}"
log "Layerwise: ${LAYERWISE_OPTIONS[*]}"
log "Log directory: $LOG_DIR"
log "============================================"

# 総組み合わせ数を計算
TOTAL=$((${#MODELS[@]} * ${#K_VALUES[@]} * ${#W_VALUES[@]} * ${#LAYERWISE_OPTIONS[@]}))
log "Total experiments: $TOTAL"
log ""

COUNT=0
START_TIME=$(date +%s)

for model in "${MODELS[@]}"; do
    for k in "${K_VALUES[@]}"; do
        for w in "${W_VALUES[@]}"; do
            for layerwise in "${LAYERWISE_OPTIONS[@]}"; do
                COUNT=$((COUNT + 1))
                log "Progress: $COUNT / $TOTAL"
                
                run_experiment "$model" "$k" "$w" "$layerwise"
                
                # 経過時間と推定残り時間
                CURRENT_TIME=$(date +%s)
                ELAPSED=$((CURRENT_TIME - START_TIME))
                if [ $COUNT -gt 0 ]; then
                    AVG_TIME=$((ELAPSED / COUNT))
                    REMAINING=$(( (TOTAL - COUNT) * AVG_TIME ))
                    log "Elapsed: ${ELAPSED}s, Estimated remaining: ${REMAINING}s"
                fi
            done
        done
    done
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

log ""
log "============================================"
log "Grid Search Completed!"
log "============================================"
log "Total time: ${TOTAL_TIME}s ($((TOTAL_TIME / 60))m)"
log "Results saved in: $LOG_DIR"
log "============================================"

# 結果サマリーを生成
log ""
log "Generating results summary..."

SUMMARY_FILE="$LOG_DIR/results_summary.csv"
echo "model,k,weight,layerwise,jailbreak,rouge_l,status" > "$SUMMARY_FILE"

for log_file in "$LOG_DIR"/*.log; do
    if [[ "$log_file" == *"master.log" ]]; then continue; fi
    
    filename=$(basename "$log_file" .log)
    
    # ファイル名からパラメータ抽出
    model=$(echo "$filename" | sed 's/_k[0-9]*_.*//')
    k=$(echo "$filename" | grep -oP 'k\K\d+' || echo "")
    w=$(echo "$filename" | grep -oP 'w\K[\d.]+' || echo "")
    lw=$(echo "$filename" | grep -oP '(uniform|layerwise)$' || echo "")
    
    # sst_merge_v4の結果を抽出
    result=$(grep "sst_merge_v4" "$log_file" 2>/dev/null | tail -1 || echo "")
    if [ -n "$result" ]; then
        jb=$(echo "$result" | awk '{print $2}')
        rl=$(echo "$result" | awk '{print $3}')
        status=$(echo "$result" | awk '{print $4}')
        echo "$model,$k,$w,$lw,$jb,$rl,$status" >> "$SUMMARY_FILE"
    fi
done

log "Summary saved to: $SUMMARY_FILE"
log ""
log "To view results:"
log "  cat $SUMMARY_FILE | column -t -s ','"
