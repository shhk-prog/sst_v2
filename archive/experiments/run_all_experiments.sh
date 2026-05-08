#!/bin/bash
# SST-Merge 全実験実行スクリプト

set -e  # エラーで停止

echo "======================================"
echo "SST-Merge 実験実行開始"
echo "======================================"

# 実験ディレクトリに移動
cd "$(dirname "$0")"

# Python環境の確認
echo "Python環境の確認..."
python --version
pip list | grep torch

# 実験1: Safety-Utility Trade-off
echo ""
echo "======================================"
echo "実験1: Safety-Utility Trade-off"
echo "======================================"
python exp1_safety_utility_tradeoff.py

# 実験2: Multitask Interference (コメントアウト - 未実装)
# echo ""
# echo "======================================"
# echo "実験2: Multitask Interference"
# echo "======================================"
# python exp2_multitask_interference.py --num_experts 8

# 実験3: Baseline Comparison (コメントアウト - 未実装)
# echo ""
# echo "======================================"
# echo "実験3: Baseline Comparison"
# echo "======================================"
# python exp3_baseline_comparison.py --methods all

echo ""
echo "======================================"
echo "全実験完了"
echo "======================================"
echo "結果は results/ ディレクトリに保存されました"
