#!/bin/bash
# setup_env.sh: SST-Merge v2_experiments 環境構築スクリプト
# 既存の環境を破壊しないよう注意しつつ、不足しているツールをインストールします

echo "Setting up evaluation and merge environments..."

# 1. 評価ツール (lm-evaluation-harness)
if [ ! -d "lm-evaluation-harness" ]; then
    echo "Cloning lm-evaluation-harness..."
    git clone https://github.com/EleutherAI/lm-evaluation-harness
    cd lm-evaluation-harness
    pip install -e .
    cd ..
else
    echo "lm-evaluation-harness already exists. Skipping."
fi

# 2. マージツール (Mergekit)
if [ ! -d "mergekit" ]; then
    echo "Cloning mergekit..."
    git clone https://github.com/arcee-ai/mergekit.git
    cd mergekit
    pip install -e .
    cd ..
else
    echo "mergekit already exists. Skipping."
fi

# 3. その他の必要ライブラリ
pip install datasets transformers trl peft accelerate xformers fastchat openai pandas scipy

echo "Environment setup complete."
