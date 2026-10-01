#!/bin/bash

# Utility総合評価スクリプト (lm-evaluation-harness)
# 
# 使用法: ./run_eval_all_utility.sh [RUN_ID]
# 例: ./run_eval_all_utility.sh model1_math_ep3.0_bs16_lr2.0e-4
# ※ RUN_IDを指定しない場合は、ベースモデルの評価を実行します。

RUN_ID=$1

echo "Starting Utility evaluation..."
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/lm-evaluation-harness

if [ -z "$RUN_ID" ]; then
    echo "No RUN_ID provided. Evaluating BaseModel..."
    MODEL_ARGS="pretrained=meta-llama/Meta-Llama-3-8B-Instruct"
    OUT_DIR="../results/BaseModel"
else
    echo "Evaluating RUN_ID: ${RUN_ID}"
    MODEL_ARGS="pretrained=meta-llama/Meta-Llama-3-8B-Instruct,peft=/mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory/saves/llama3-8b/lora/${RUN_ID}"
    OUT_DIR="../results/${RUN_ID}"
fi

# 評価するタスク (カスタム作成不可の制約に従い、公式サポート済みのもののみ)
TASKS="gsm8k,minerva_math,cola,mnli,mrpc,qnli,qqp,rte,sst2,pubmedqa"

echo "======================================"
echo "Tasks: $TASKS"
echo "Output Directory: $OUT_DIR"
echo "======================================"

mkdir -p "$OUT_DIR"

# --trust_remote_code を追加して pubmedqa などのカスタムコード実行を許可します
# 本番評価用に全データで実行します
lm_eval --model hf \
    --model_args "$MODEL_ARGS" \
    --tasks $TASKS \
    --device cuda:0 \
    --batch_size auto \
    --trust_remote_code \
    --output_path "$OUT_DIR"

echo "Evaluation completed."
echo "Results are saved in ${OUT_DIR}"
