#!/bin/bash

# SST-Merge実験実行スクリプト（メモリ最適化版）
# 使用方法: bash run_experiment_optimized.sh

set -e  # エラーで停止

echo "========================================="
echo "SST-Merge Experiment (Memory Optimized)"
echo "========================================="

# 環境準備
cd /mnt/iag-02/home/hiromi/src/SST_merge
source sst/bin/activate

# 環境変数設定
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

echo "Environment:"
echo "  PYTORCH_CUDA_ALLOC_CONF: $PYTORCH_CUDA_ALLOC_CONF"
echo "  CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo ""

# ログディレクトリ作成
mkdir -p logs/training_curves
mkdir -p results

# 実験実行
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/experiment_${TIMESTAMP}.log"

echo "Starting experiment..."
echo "Log file: $LOG_FILE"
echo ""

python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment exp1 \
    2>&1 | tee "$LOG_FILE"

# 結果確認
echo ""
echo "========================================="
echo "Experiment completed!"
echo "========================================="
echo ""

echo "Results:"
if [ -f "results/exp1_llama-3.1-8b/metrics.json" ]; then
    cat results/exp1_llama-3.1-8b/metrics.json | python -m json.tool
else
    echo "  No results file found"
fi

echo ""
echo "Training curves:"
ls -lh logs/training_curves/*.png 2>/dev/null || echo "  No training curves found"

echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "To monitor GPU usage, run in another terminal:"
echo "  watch -n 1 nvidia-smi"
