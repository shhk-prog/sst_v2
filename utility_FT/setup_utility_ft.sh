#!/bin/bash

# Utility FTの実装および評価環境セットアップスクリプト
# sst_v2/utility_FT ディレクトリ下で実行してください

echo "Setting up utility_FT environment..."

cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT

# 2. 一般推論・数学・GLUE用 評価ツール (lm-evaluation-harness) の公式リポジトリ
if [ ! -d "lm-evaluation-harness" ]; then
    echo "Cloning lm-evaluation-harness..."
    git clone https://github.com/EleutherAI/lm-evaluation-harness
    cd lm-evaluation-harness
    pip install -e .
    cd ..
else
    echo "lm-evaluation-harness already exists."
fi

# 3. コーディング用 評価ツール (bigcode-evaluation-harness) の公式リポジトリ
if [ ! -d "bigcode-evaluation-harness" ]; then
    echo "Cloning bigcode-evaluation-harness for Coding evaluation..."
    git clone https://github.com/bigcode-project/bigcode-evaluation-harness.git
    cd bigcode-evaluation-harness
    pip install -e .
    cd ..
else
    echo "bigcode-evaluation-harness already exists."
fi

# 4. 通信・専門ドメイン用 評価ツール (TeleQnA) の公式リポジトリ
if [ ! -d "TeleQnA" ]; then
    echo "Cloning TeleQnA benchmark for telecommunications..."
    git clone https://github.com/netop-team/TeleQnA.git
else
    echo "TeleQnA already exists."
fi

# 5. ファインチューニング (FT) 実行ツール (LLaMA-Factory) の公式リポジトリ
if [ ! -d "LLaMA-Factory" ]; then
    echo "Cloning LLaMA-Factory for fine-tuning..."
    git clone https://github.com/hiyouga/LLaMA-Factory.git
    cd LLaMA-Factory
    pip install -e ".[torch,metrics]"
    cd ..
else
    echo "LLaMA-Factory already exists."
fi

echo "Setup completed successfully."
