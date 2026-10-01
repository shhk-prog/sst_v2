#!/bin/bash
# 論文公式コードのフル再現実験実行用総合スクリプト
# 各実験は、仮想環境 (venv_sst) がアクティベートされた状態で実行してください。
set +e

BASE_DIR="/mnt/nas/home/hiromi/src/sst_v2/baseline"
LOG_DIR="${BASE_DIR}/logs"
mkdir -p "$LOG_DIR"

echo "=== Diagnostic Environment check ==="
python3 "${BASE_DIR}/check_tf.py" > "${LOG_DIR}/check_tf.log" 2>&1 || true
echo "Diagnostics finished. Log saved to ${LOG_DIR}/check_tf.log"

echo "=== Reproducing baseline implementations ==="

# -------------------------------------------------------------------------
# 1. model_merging (NeurIPS 2022)
# -------------------------------------------------------------------------
echo "1/6 Running model_merging (NeurIPS 2022)..."
cd "${BASE_DIR}/model_merging"
# 必要パッケージのインストール (TensorFlowとH5Py、absl-py等が必要)
pip install tensorflow h5py absl-py transformers datasets
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
bash run_all_experiments.sh > "${LOG_DIR}/model_merging.log" 2>&1
echo "model_merging completed. Log saved to ${LOG_DIR}/model_merging.log"

# -------------------------------------------------------------------------
# 2. iclr2024-model-merging (Daheim et al., ICLR 2024)
# -------------------------------------------------------------------------
echo "2/6 Running iclr2024-model-merging (ICLR 2024)..."
cd "${BASE_DIR}/iclr2024-model-merging"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
# ファインチューニング実行
echo "  -> Running finetuning..."
python3 code/train.py scripts/finetune_roberta_imdb_run.json > "${LOG_DIR}/iclr2024_finetune.log" 2>&1
# Fisher情報量計算
echo "  -> Computing Fisher/Hessian..."
python3 code/train.py scripts/fisher_roberta_imdb_run.json > "${LOG_DIR}/iclr2024_fisher.log" 2>&1
# 評価実行
echo "  -> Running evaluation..."
python3 code/predict.py scripts/evaluate_roberta_imdb_run.json > "${LOG_DIR}/iclr2024_eval.log" 2>&1
echo "iclr2024-model-merging completed. Logs saved to ${LOG_DIR}/iclr2024_*.log"

# -------------------------------------------------------------------------
# 3. fisher-nodes-merging (Thennal D K et al., LREC-COLING 2024)
# -------------------------------------------------------------------------
echo "3/6 Running fisher-nodes-merging (LREC-COLING 2024)..."
cd "${BASE_DIR}/fisher-nodes-merging"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
python3 eval_compare.py --config config.json > "${LOG_DIR}/fisher_nodes_merging.log" 2>&1
echo "fisher-nodes-merging completed. Log saved to ${LOG_DIR}/fisher_nodes_merging.log"

# -------------------------------------------------------------------------
# 4. df-merge (Sanwoo Lee et al., NAACL 2025)
# -------------------------------------------------------------------------
echo "4/6 Running df-merge (NAACL 2025)..."
cd "${BASE_DIR}/df-merge"
# 依存関係
if command -v poetry &> /dev/null; then
    poetry install || true
    poetry run python src/df-merge.py \
        --ckpt_root experiments/finetune/default/ckpt \
        --model_name_or_path t5-base \
        --seed 42 \
        --acquisition_fn ei \
        --experiment_name merge \
        --use_fisher > "${LOG_DIR}/df_merge.log" 2>&1
else
    pip install -r pyproject.toml || true
    python3 src/df-merge.py \
        --ckpt_root experiments/finetune/default/ckpt \
        --model_name_or_path t5-base \
        --seed 42 \
        --acquisition_fn ei \
        --experiment_name merge \
        --use_fisher > "${LOG_DIR}/df_merge.log" 2>&1
fi
echo "df-merge completed. Log saved to ${LOG_DIR}/df_merge.log"

# -------------------------------------------------------------------------
# 5. LED-Merging (Qianli Ma et al., ACL 2025)
# -------------------------------------------------------------------------
echo "5/6 Running LED-Merging (ACL 2025)..."
cd "${BASE_DIR}/LED-Merging"
# pyairports等のコンフリクトを回避するため、必要な主要モジュールのみを直接インストール
pip install vllm accelerate transformers datasets
# Locateステップを実行 (attributions)
cd locate/
bash scripts/locate_inst.sh > "${LOG_DIR}/led_merging_locate.log" 2>&1 || true
cd ../
# Electステップを実行
python3 mask_generate.py 0.1 0.4 0.5 11 llama3 > "${LOG_DIR}/led_merging_elect.log" 2>&1 || true
# Disjoint & Mergingステップを実行
python3 merge_llms.py \
    --models_to_merge meta-llama/Meta-Llama-3-8B-Instruct \
    --pretrained_model_name meta-llama/Meta-Llama-3-8B \
    --merging_method_name top_merging \
    --scaling_coefficient 0.9 \
    --mask_apply_method task_arithmetic \
    --fuse_rates 0.1 0.4 0.5 \
    --orders safety math code \
    --lambdas 1.0 1.0 1.0 \
    --fuse_types o o o \
    --fuse_patterns 11 11 11 \
    --model_ft_name llama3 \
    --model_base_name llama3-base > "${LOG_DIR}/led_merging_merge.log" 2>&1 || true
echo "LED-Merging completed. Logs saved to ${LOG_DIR}/led_merging_*.log"

# -------------------------------------------------------------------------
# 6. SafeMERGE (Aladin Djuhera et al., 2025-2026)
# -------------------------------------------------------------------------
echo "6/6 Running SafeMERGE..."
cd "${BASE_DIR}/SafeMERGE"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
bash run_all_models.sh > "${LOG_DIR}/safemerge.log" 2>&1
echo "SafeMERGE completed. Log saved to ${LOG_DIR}/safemerge.log"

echo "=== All baseline reproductions finished ==="
