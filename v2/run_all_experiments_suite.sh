#!/bin/bash
# v2/run_all_experiments_suite.sh
# Llama-2-7B特化モデルマージ実験一括実行マスタースクリプト (kiro 仕様遵守版)

set -e

# 実験ログ保存用フォルダの作成 (kiroルール遵守)
mkdir -p logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/experiment_run_${TIMESTAMP}.log"

echo "=== Starting Llama-2 SST-Merge Experiment Suite ===" | tee -a "$LOG_FILE"
echo "All outputs will be logged to ${LOG_FILE}" | tee -a "$LOG_FILE"

CONFIG_PATH="configs/aaai27/llama2_sst_experiment.yaml"
OUTPUT_ROOT="models/merged"
RESULTS_DIR="results/raw"

# 1. 必要なモデルおよびデータセットのダウンロード
echo "=== Phase 1: Downloading Llama-2 Models and Datasets from HF ===" | tee -a "$LOG_FILE"
# ゲート付きモデル (Llama-2) のダウンロードのため、必要に応じて HF_TOKEN が設定されている必要があります。
python3 scripts/data_prep/download_llama2_resources.py 2>&1 | tee -a "$LOG_FILE"

# 2. 外部リポジトリ (SafeMERGE) の自動クローン (kiroルール遵守)
echo "=== Phase 2: Cloning SafeMERGE Official Repository ===" | tee -a "$LOG_FILE"
THIRD_PARTY_DIR="../third_party"
mkdir -p "$THIRD_PARTY_DIR"
if [ ! -d "${THIRD_PARTY_DIR}/SafeMERGE" ]; then
    echo "Cloning official SafeMERGE..." | tee -a "$LOG_FILE"
    git clone https://github.com/WalledAI/SafeMERGE.git "${THIRD_PARTY_DIR}/SafeMERGE" 2>&1 | tee -a "$LOG_FILE"
else
    echo "SafeMERGE already exists. Skipping clone." | tee -a "$LOG_FILE"
fi

# 3. 動作フック検証 (steering_hook のユニットテスト実行)
echo "=== Phase 3: Running Steering Hook Verification Tests ===" | tee -a "$LOG_FILE"
python3 -m unittest scripts/test_steering_hook.py 2>&1 | tee -a "$LOG_FILE"

# 4. 実験グリッド実行ループ
echo "=== Phase 4: Starting Model Merging and Evaluation Sweeps ===" | tee -a "$LOG_FILE"

# YAML設定からスイープパラメータを読み込み、順次実行
# （本シェルスクリプトでは基本的なスイープパラメータを配列で定義して実行制御します）
PATTERNS=("math,code" "math,medical" "code,medical" "math,code,medical")
METHODS=("task_arithmetic" "ties" "dare" "della" "fisher_weighted_averaging" "merge_align" "safemerge" "led_merging" "sst_merge" "data_free_sst_merge")
ALPHAS=("0.3" "0.5" "0.7")
KS=("0.10" "0.20" "soft")

for pattern in "${PATTERNS[@]}"; do
    for method in "${METHODS[@]}"; do
        # data_free_sst_merge のみアブレーションを含め詳細に回す
        # そうでないものは代表的な設定で実行して時間を節約
        if [ "$method" != "data_free_sst_merge" ] && [ "$method" != "sst_merge" ]; then
            # 代表的な1つの設定のみ
            local_alphas=("0.5")
            local_ks=("0.20")
        else
            local_alphas=("${ALPHAS[@]}")
            local_ks=("${KS[@]}")
        fi
        
        for alpha in "${local_alphas[@]}"; do
            for k in "${local_ks[@]}"; do
                # k="soft" は mergekit 手法では使えないためスキップ
                if [ "$k" = "soft" ] && { [ "$method" = "ties" ] || [ "$method" = "dare" ] || [ "$method" = "della" ] || [ "$method" = "task_arithmetic" ]; }; then
                    continue
                fi
                
                MODEL_DIR="${OUTPUT_ROOT}/${method}_$(echo "$pattern" | tr ',' '_')_a${alpha}_k${k}"
                
                echo "[$(date)] Merging: method=${method}, pattern=${pattern}, alpha=${alpha}, k=${k}" | tee -a "$LOG_FILE"
                
                # A. マージ実行
                python3 scripts/merge/merge_llama2_sst_suite.py \
                    --config "$CONFIG_PATH" \
                    --output_root "$OUTPUT_ROOT" \
                    --method "$method" \
                    --alpha "$alpha" \
                    --k "$k" \
                    --pattern "$pattern" 2>&1 | tee -a "$LOG_FILE"
                
                # B. 評価実行 (マージが成功してディレクトリが存在する場合のみ)
                if [ -d "$MODEL_DIR" ]; then
                    echo "[$(date)] Evaluating: ${MODEL_DIR}" | tee -a "$LOG_FILE"
                    python3 scripts/evaluation/eval_llama2_suite.py \
                        --config "$CONFIG_PATH" \
                        --model_path "$MODEL_DIR" \
                        --output_dir "$RESULTS_DIR" 2>&1 | tee -a "$LOG_FILE"
                else
                    echo "[Warning] Model directory ${MODEL_DIR} not found. Skipping evaluation." | tee -a "$LOG_FILE"
                fi
                
                echo "----------------------------------------------" | tee -a "$LOG_FILE"
            done
        done
    done
done

echo "=== Llama-2 SST-Merge Experiment Suite Complete ===" | tee -a "$LOG_FILE"
