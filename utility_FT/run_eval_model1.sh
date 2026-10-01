#!/bin/bash

# Model 1 (Math) のベースライン評価（GSM8K）スクリプト

echo "Starting Evaluation for Model 1 (Math) on GSM8K..."

# 仮想環境がアクティブになっている前提で実行します
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/lm-evaluation-harness

# 出力先ディレクトリの作成
mkdir -p ./results/model1_math_gsm8k

# lm-evaluation-harness を用いた評価の実行
# 本番用に全データで実行します
lm_eval --model hf \
    --model_args pretrained=meta-llama/Meta-Llama-3-8B-Instruct,peft=/mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory/saves/llama3-8b/lora/model1_math \
    --tasks gsm8k \
    --device cuda:0 \
    --batch_size auto \
    --output_path ./results/model1_math_gsm8k

echo "Evaluation completed. Results are saved in ./results/model1_math_gsm8k"
