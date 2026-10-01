#!/bin/bash

# Coding評価スクリプト (bigcode-evaluation-harness)
# 
# 使用法: ./run_eval_coding.sh [RUN_ID]
# ※ RUN_IDを指定しない場合は、ベースモデルの評価を実行します。

RUN_ID=$1

echo "Starting Coding evaluation..."
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/bigcode-evaluation-harness

if [ -z "$RUN_ID" ]; then
    echo "Evaluating BaseModel..."
    MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
    OUT_DIR="../results/BaseModel"
    PEFT_ARG=""
else
    echo "Evaluating RUN_ID: ${RUN_ID}"
    MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
    PEFT_MODEL_PATH="/mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory/saves/llama3-8b/lora/${RUN_ID}"
    OUT_DIR="../results/${RUN_ID}"
    PEFT_ARG="--peft_model $PEFT_MODEL_PATH"
fi

# コード評価(mbpp)のためのフラグ設定
export HF_ALLOW_CODE_EVAL=1

mkdir -p "$OUT_DIR"

# 評価するタスク
TASKS="mbpp,humaneval"

echo "======================================"
echo "Tasks: $TASKS"
echo "Output Directory: $OUT_DIR"
echo "======================================"

# mbpp は lm-evaluation-harness でも公式サポートされているため、そちらを使用する
# (bigcode-evaluation-harnessはdatasetsライブラリのバージョン競合がある)
LM_EVAL_DIR="/mnt/nas/home/hiromi/src/sst_v2/utility_FT/lm-evaluation-harness"

if [ -z "$PEFT_ARG" ]; then
    PEFT_LM_EVAL=""
else
    PEFT_LM_EVAL="--model_args pretrained=${MODEL_NAME},peft=${PEFT_MODEL_PATH},trust_remote_code=True"
fi

lm_eval \
    --model hf \
    ${PEFT_LM_EVAL:---model_args pretrained=${MODEL_NAME},trust_remote_code=True} \
    --tasks mbpp \
    --batch_size 1 \
    --confirm_run_unsafe_code \
    --output_path "${OUT_DIR}/coding_metrics.json"

echo "Evaluation completed. Results are saved in ${OUT_DIR}"
