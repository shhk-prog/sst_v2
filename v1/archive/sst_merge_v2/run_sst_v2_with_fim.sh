#!/bin/bash
#
# SST-Merge V2 実行ラッパースクリプト
# SST_merge直下の既存リソース（アダプター、データローダー）を使用
#
# 使用方法:
#   chmod +x run_sst_v2_with_fim.sh
#   ./run_sst_v2_with_fim.sh [variant] [mode] [residual_ratio]
#
# 例:
#   ./run_sst_v2_with_fim.sh A5+A7 residual 0.7
#   ./run_sst_v2_with_fim.sh A6+A7 residual 0.5
#   ./run_sst_v2_with_fim.sh A5+A6+A7 layerwise 0.7
#

set -e

# デフォルト値
VARIANT=${1:-"A5+A7"}
MODE=${2:-"residual"}
RESIDUAL_RATIO=${3:-"0.7"}
MODEL="llama-3.1-8b"
SAFETY_WEIGHT="1.0"
K=10
MAX_SAMPLES=500

echo "================================================================================
"
echo "SST-MERGE V2: COMPLETE EXECUTION WITH FIM"
echo "================================================================================"
echo "Model: $MODEL"
echo "Variant: $VARIANT"
echo "Mode: $MODE"
echo "Residual Ratio: $RESIDUAL_RATIO"
echo "Safety Weight: $SAFETY_WEIGHT"
echo "k (subspace dim): $K"
echo "Max Samples: $MAX_SAMPLES"
echo "================================================================================"
echo ""

# SST_merge_v2ディレクトリに移動
cd "$(dirname "$0")"

# アダプターの存在確認
ADAPTER_DIR="../saved_adapters/$MODEL/utility_model"

if [[ "$VARIANT" == *"A5"* ]] && [ ! -f "$ADAPTER_DIR/utility_model_A5.pt" ]; then
    echo "Error: A5 adapter not found at $ADAPTER_DIR/utility_model_A5.pt"
    echo "Please run: python ../experiments/create_instruction_model.py --model $MODEL --task repliqa --mode full"
    exit 1
fi

if [[ "$VARIANT" == *"A6"* ]] && [ ! -f "$ADAPTER_DIR/utility_model_A6.pt" ]; then
    echo "Error: A6 adapter not found at $ADAPTER_DIR/utility_model_A6.pt"
    echo "Please run: python ../experiments/create_instruction_model.py --model $MODEL --task alpaca --mode full"
    exit 1
fi

if [ ! -f "$ADAPTER_DIR/utility_model_A7.pt" ]; then
    echo "Error: A7 adapter not found at $ADAPTER_DIR/utility_model_A7.pt"
    echo "Please run: python ../experiments/create_instruction_model.py --model $MODEL --task security --mode full"
    exit 1
fi

echo "✓ All required adapters found"
echo ""

# データファイルの確認
DATA_FILE="../data/response_dataframe.csv"
if [ ! -f "$DATA_FILE" ]; then
    echo "Error: Security data not found at $DATA_FILE"
    exit 1
fi

echo "✓ Security data found"
echo ""

# 実行
if [ "$MODE" == "direct" ]; then
    echo "Running in DIRECT mode (no FIM computation)..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "$VARIANT" \
        --mode direct \
        --safety_weight "$SAFETY_WEIGHT"
elif [ "$MODE" == "layerwise" ]; then
    PRESET=${4:-"balanced"}
    echo "Running in LAYERWISE mode with preset: $PRESET (FIM enabled)..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "$VARIANT" \
        --mode layerwise \
        --preset "$PRESET" \
        --k "$K" \
        --safety_weight "$SAFETY_WEIGHT" \
        --max_samples "$MAX_SAMPLES" \
        --use_fim
else
    echo "Running in RESIDUAL mode (FIM enabled)..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "$VARIANT" \
        --mode residual \
        --residual_ratio "$RESIDUAL_RATIO" \
        --k "$K" \
        --safety_weight "$SAFETY_WEIGHT" \
        --max_samples "$MAX_SAMPLES" \
        --use_fim
fi

echo ""
echo "================================================================================"
echo "SST-MERGE V2 EXECUTION COMPLETED"
echo "================================================================================"
