#!/bin/bash
set -e

# Safety (安全性・アライメント) 評価スクリプト
# カスタムスクリプトを避け、公式リポジトリ (HarmBench, SORRY-Bench等) のコードを利用します。
# ※ 事前に HF_TOKEN がエクスポートされている必要があります。

RUN_ID=$1
BASE_DIR="/mnt/nas/home/hiromi/src/sst_v2/utility_FT"
cd "$BASE_DIR"

if [ -z "$RUN_ID" ]; then
    echo "Evaluating BaseModel..."
    MODEL_PATH="meta-llama/Meta-Llama-3-8B-Instruct"
    OUT_DIR="${BASE_DIR}/results/BaseModel"
else
    echo "Evaluating RUN_ID: ${RUN_ID}"
    # モデルパスはマージ済みのもの、あるいはベースモデル（適宜変更）
    MODEL_PATH="${BASE_DIR}/LLaMA-Factory/saves/llama3-8b/lora/${RUN_ID}"
    OUT_DIR="${BASE_DIR}/results/${RUN_ID}"
fi
mkdir -p "$OUT_DIR/Safety"

echo "======================================"
echo "Safety Evaluation Output: $OUT_DIR/Safety"
echo "======================================"

# 1. HarmBench のセットアップと実行
echo "[1] Setting up HarmBench..."
if [ ! -d "HarmBench" ]; then
    git clone https://github.com/centerforaisafety/HarmBench.git
fi
cd HarmBench
# HarmBenchの公式スクリプトを利用した生成と評価（例）
# 実際には環境に合わせた依存関係 (pip install -r requirements.txt) や
# 評価用モデル (Llama-Guard-3) の設定が必要です。
# python3 generate.py --model "$MODEL_PATH"
# python3 evaluate.py --eval_model "meta-llama/Llama-Guard-3-8B" --input_dir ...
echo "HarmBench execution is configured. (Execute official commands here)"
cd "$BASE_DIR"

# 2. SORRY-Bench のセットアップと実行
echo "[2] Setting up SORRY-Bench..."
if [ ! -d "SORRY-Bench" ]; then
    git clone https://github.com/sorry-bench/SORRY-Bench.git
fi
cd SORRY-Bench
# python3 evaluate.py --model "$MODEL_PATH" --judge "MD-Judge"
echo "SORRY-Bench execution is configured. (Execute official commands here)"
cd "$BASE_DIR"

# 3. BeaverTails 等
echo "[3] Setting up BeaverTails..."
if [ ! -d "BeaverTails" ]; then
    git clone https://github.com/PKU-Alignment/BeaverTails.git
fi
cd BeaverTails
echo "BeaverTails execution is configured. (Execute official commands here)"
cd "$BASE_DIR"

echo "Safety evaluation script skeleton created successfully."
