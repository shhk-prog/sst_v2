#!/bin/bash
set -e

# カレントディレクトリをこのスクリプトの場所にする
cd "$(dirname "$0")"

# 実行名 (デフォルトは直近の実験結果を指定)
RUN_NAME=${1:-"lr2e-4_ep3"}

# .env から環境変数をロード
DOTENV_PATH="$HOME/src/.env"
if [ -f "$DOTENV_PATH" ]; then
    source "$DOTENV_PATH"
    [ -n "$HUGGINGFACE_HUB_TOKEN" ] && export HF_TOKEN=$HUGGINGFACE_HUB_TOKEN
fi

# 仮想環境の有効化
if [ -n "$SST_HOME" ] && [ -d "$SST_HOME/venv_sst" ]; then
    source "$SST_HOME/venv_sst/bin/activate"
else
    source ../../../venv_sst/bin/activate || { echo "ERROR: venv_sst not found"; exit 1; }
fi

MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
MODEL_BASE_DIR="../../models/$RUN_NAME"
RESULTS_JSON="../../results/$RUN_NAME/phase2_eval_results.json"

echo "=== Running XSTest Evaluation Only (All Models) ==="
echo "  Run Name     : $RUN_NAME"
echo "  Results JSON : $RESULTS_JSON"
echo ""

for MODEL_NAME in base_model utility_lora coding_lora safety_lora mixed_lora; do
    echo "--- Over-refusal eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
        if [ ! -d "$MODEL_BASE_DIR/$MODEL_NAME" ]; then
            echo "  Warning: Adapter $MODEL_NAME not found at $MODEL_BASE_DIR/$MODEL_NAME. Skipping."
            continue
        fi
    fi

    python run_overrefusal_eval.py \
      --base_model $MODEL \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      --data_path ../../data/xstest_prompts.json \
      --output_json $RESULTS_JSON
done

echo ""
echo "=== XSTest Evaluation Complete ==="
