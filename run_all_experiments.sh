#!/bin/bash

# 全手法の実験を実行して比較するスクリプト

set -e

echo "========================================="
echo "全手法の実験実行と比較"
echo "========================================="

cd /mnt/iag-02/home/hiromi/src/SST_merge
source sst/bin/activate

# 環境変数設定
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

MODEL="llama-3.1-8b"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ログディレクトリ作成
mkdir -p logs
mkdir -p results

echo ""
echo "========================================="
echo "1. SST-Merge実験"
echo "========================================="
python experiments/run_real_experiments.py \
    --mode full \
    --model ${MODEL} \
    --experiment exp1 \
    2>&1 | tee logs/sst_merge_${TIMESTAMP}.log

echo ""
echo "========================================="
echo "2. ベースライン実験（カスタム実装）"
echo "========================================="
python experiments/run_baseline_experiments.py \
    --model ${MODEL} \
    --mode full \
    2>&1 | tee logs/baseline_${TIMESTAMP}.log

echo ""
echo "========================================="
echo "3. ベースライン実験（PEFT/mergekit）"
echo "========================================="
python experiments/run_baseline_experiments.py \
    --model ${MODEL} \
    --mode full \
    --use-mergekit \
    2>&1 | tee logs/baseline_mergekit_${TIMESTAMP}.log

echo ""
echo "========================================="
echo "4. 結果の比較"
echo "========================================="
python analysis/compare_all_methods.py --model ${MODEL}

echo ""
echo "========================================="
echo "実験完了"
echo "========================================="
echo ""
echo "結果ファイル:"
echo "  - SST-Merge: results/exp1_safety_utility/"
echo "  - ベースライン: results/baseline_experiments/"
echo "  - 比較結果: results/comparison/"
echo ""
echo "ログファイル:"
echo "  - SST-Merge: logs/sst_merge_${TIMESTAMP}.log"
echo "  - ベースライン: logs/baseline_${TIMESTAMP}.log"
echo "  - ベースライン(mergekit): logs/baseline_mergekit_${TIMESTAMP}.log"
echo ""
echo "比較グラフ: results/comparison/comparison_${MODEL}_*.png"
echo "比較レポート: results/comparison/comparison_report_${MODEL}_*.md"
