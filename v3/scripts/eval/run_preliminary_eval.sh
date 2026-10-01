#!/bin/bash
# run_preliminary_eval.sh
# 予備実験（TrustLLM / BeaverTails）を一括で実行するためのスクリプト

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <model_dir_or_path> [output_dir] [limit]"
    echo "Example: $0 models/merged/seed42/safety+math results/preliminary 500"
    exit 1
fi

MODEL_TARGET=$1
OUTPUT_DIR=${2:-"results/preliminary"}
LIMIT=${3:-500}

mkdir -p "$OUTPUT_DIR"

if [ -d "$MODEL_TARGET" ] && [ -f "$MODEL_TARGET/config.json" ]; then
    # 対象が単一モデルのディレクトリの場合
    echo "Evaluating single model: $MODEL_TARGET"
    python3 scripts/eval/eval_preliminary.py \
        --model_path "$MODEL_TARGET" \
        --output_dir "$OUTPUT_DIR" \
        --limit "$LIMIT"
else
    # 対象が複数モデルを格納したディレクトリの場合
    echo "Scanning directory $MODEL_TARGET for models..."
    for model_path in "$MODEL_TARGET"/*; do
        if [ -d "$model_path" ] && [ -f "$model_path/config.json" ]; then
            echo "Evaluating model: $model_path"
            python3 scripts/eval/eval_preliminary.py \
                --model_path "$model_path" \
                --output_dir "$OUTPUT_DIR" \
                --limit "$LIMIT"
        fi
    done
fi

echo "All preliminary evaluations completed! Results saved to $OUTPUT_DIR"
