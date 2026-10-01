#!/bin/bash
set -e

# カレントディレクトリをこのスクリプトの場所にする
cd "$(dirname "$0")"

# ──────────────────────────────────────────
# 仮想環境 + 環境変数
# ──────────────────────────────────────────
DOTENV_PATH="$HOME/src/.env"
if [ -f "$DOTENV_PATH" ]; then
    echo "=== Loading environment variables from $DOTENV_PATH ==="
    set -a
    source "$DOTENV_PATH"
    set +a
    if [ -n "$HUGGINGFACE_HUB_TOKEN" ]; then
        export HF_TOKEN=$HUGGINGFACE_HUB_TOKEN
    fi
else
    echo "Warning: .env not found at $DOTENV_PATH"
fi

if [ -n "$SST_HOME" ] && [ -d "$SST_HOME/venv_sst" ]; then
    source "$SST_HOME/venv_sst/bin/activate"
else
    source ../../../venv_sst/bin/activate || { echo "ERROR: venv_sst not found"; exit 1; }
fi

# ──────────────────────────────────────────
# 実行設定 (Run Configuration)
# ──────────────────────────────────────────
#############################################################################
MODEL=${MODEL:-"meta-llama/Meta-Llama-3-8B-Instruct"}
LR=${LR:-"1e-5"}
EPOCHS=${EPOCHS:-"3"}

RUN_NAME=${RUN_NAME:-"lr${LR}_ep${EPOCHS}_utility_only"}

MODEL_DIR_NAME=$(basename "$MODEL" | sed 's/Meta-//')
RUN_DIR="../../results/$MODEL_DIR_NAME/$RUN_NAME"
RESULTS_JSON="$RUN_DIR/phase2_eval_results.json"
LM_EVAL_RAW="$RUN_DIR/lm_eval_raw"
MODEL_BASE_DIR="../../models/$MODEL_DIR_NAME/$RUN_NAME"

#############################################################################

echo "=== Experiment Run: $RUN_NAME ==="
echo "  Results will be saved to: $RUN_DIR"
echo "  Models will be saved to:  $MODEL_BASE_DIR"
echo ""
echo "  Evaluation structure:"
echo "  └─ Utility"
echo "      ├─ [ID]  Finance eval split    ROUGE-L"
echo "      ├─ [OOD] MMLU Finance          acc (business_ethics / macroeconomics / econometrics)"
echo "      ├─ [ID]  Coding eval split     ROUGE-L"
echo "      ├─ [OOD] HumanEval             pass@1"
echo "      ├─ [OOD] MBPP                  pass@1"
echo "      ├─ [OOD] GSM8K                 exact_match (CoT)"
echo "      └─ [OOD] ARC / HellaSwag       acc_norm (catastrophic forgetting)"

# 評価サンプル数設定
N_UTILITY_ID=200      # Finance/Coding eval split (FT使用データ, ID)
LIMIT_UTILITY=2000    # OOD lm-eval サンプル数 (None にすると全件)

# ──────────────────────────────────────────
# Step 1: データ準備
# ──────────────────────────────────────────
echo ""
echo "=== [Step 1] Preparing Datasets ==="
mkdir -p ../../data ../../results

# 必要なデータセットの一覧 (Finance, Coding)
REQUIRED_DATASETS=(
    "../../data/utility_finance.json"
    "../../data/utility_finance_eval.json"
    "../../data/utility_coding.json"
    "../../data/utility_coding_eval.json"
)

RUN_PREP=false
for ds in "${REQUIRED_DATASETS[@]}"; do
    if [ ! -f "$ds" ]; then
        echo "  Dataset not found: $ds"
        RUN_PREP=true
    fi
done

if [ "$RUN_PREP" = true ]; then
    echo "  Some datasets are missing. Running data prep..."
    python ../data_prep/prepare_datasets.py || { echo "Data preparation failed"; exit 1; }
else
    echo "  All required datasets already exist. Skipping data prep."
fi

# ──────────────────────────────────────────
# Step 2: ディレクトリ作成
# ──────────────────────────────────────────
echo ""
echo "=== [Step 2] Creating directories ==="
mkdir -p "$RUN_DIR"
mkdir -p "$LM_EVAL_RAW"
mkdir -p "$MODEL_BASE_DIR/utility_lora"
mkdir -p "$MODEL_BASE_DIR/coding_lora"

# ──────────────────────────────────────────
# Step 3: Fine-Tuning
# ──────────────────────────────────────────
echo ""
echo "=== [Step 3] Fine-Tuning ==="

echo "--- Utility FT (Finance: finance-alpaca, lr=$LR, epochs=$EPOCHS, assistant_only_loss) ---"
python run_lora_ft.py \
  --model_name_or_path $MODEL \
  --utility_dataset_path ../../data/utility_finance.json \
  --eval_dataset_path ../../data/utility_finance_eval.json \
  --output_dir "$MODEL_BASE_DIR/utility_lora" \
  --epochs $EPOCHS \
  --learning_rate $LR \
  --warmup_ratio 0.05 \
  || { echo "Utility FT failed"; exit 1; }
echo "  [Done] utility_lora"

echo "--- Utility FT (Coding: Magicoder OSS-INSTRUCT, lr=$LR, epochs=$EPOCHS, assistant_only_loss) ---"
python run_lora_ft.py \
  --model_name_or_path $MODEL \
  --utility_dataset_path ../../data/utility_coding.json \
  --eval_dataset_path ../../data/utility_coding_eval.json \
  --output_dir "$MODEL_BASE_DIR/coding_lora" \
  --epochs $EPOCHS \
  --learning_rate $LR \
  --warmup_ratio 0.05 \
  || { echo "Coding FT failed"; exit 1; }
echo "  [Done] coding_lora"

echo ""
echo "=== [Step 3] Fine-Tuning Complete ==="

# 評価するモデルの一覧
EVAL_MODELS="base_model base_with_template utility_lora coding_lora"

# ──────────────────────────────────────────
# Step 4: Utility-Finance 評価 [OOD] — MMLU
# ──────────────────────────────────────────
echo ""
echo "=== [Step 4] Utility-Finance Evaluation [OOD] (MMLU) ==="

FINANCE_OOD_ARGS="--base_model $MODEL \
               --eval_type finance \
               --output_json $RESULTS_JSON \
               --lm_eval_output_dir $LM_EVAL_RAW \
               --limit $LIMIT_UTILITY \
               --batch_size 4"

for MODEL_NAME in $EVAL_MODELS; do
    echo "--- Finance OOD eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG=""
    elif [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG="--apply_chat_template"
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
        TEMPLATE_ARG="--apply_chat_template"
    fi
    python run_utility_eval.py \
      $FINANCE_OOD_ARGS \
      $ADAPTER_ARG \
      $TEMPLATE_ARG \
      --model_name $MODEL_NAME \
      || { echo "Finance OOD eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 5: Utility-Finance 評価 [ID] — finance-alpaca eval split
# ──────────────────────────────────────────
echo ""
echo "=== [Step 5] Utility-Finance Evaluation [ID] (finance-alpaca eval split) ==="

for MODEL_NAME in $EVAL_MODELS; do
    echo "--- Finance ID eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ] || [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
    fi
    python run_utility_id_eval.py \
      --base_model $MODEL \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      --eval_type finance \
      --data_path ../../data/utility_finance_eval.json \
      --n_samples $N_UTILITY_ID \
      --output_json $RESULTS_JSON \
      || { echo "Finance ID eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 6: Utility-Coding 評価 [OOD] — HumanEval / MBPP / GSM8K
# ──────────────────────────────────────────
echo ""
echo "=== [Step 6] Utility-Coding Evaluation [OOD] (HumanEval / MBPP / GSM8K) ==="

CODING_OOD_ARGS="--base_model $MODEL \
              --eval_type coding \
              --output_json $RESULTS_JSON \
              --lm_eval_output_dir $LM_EVAL_RAW \
              --limit $LIMIT_UTILITY \
              --batch_size 4"

for MODEL_NAME in $EVAL_MODELS; do
    echo "--- Coding OOD eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG=""
    elif [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG="--apply_chat_template"
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
        TEMPLATE_ARG="--apply_chat_template"
    fi
    python run_utility_eval.py \
      $CODING_OOD_ARGS \
      $ADAPTER_ARG \
      $TEMPLATE_ARG \
      --model_name $MODEL_NAME \
      || { echo "Coding OOD eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 7: Utility-Coding 評価 [ID] — Magicoder eval split
# ──────────────────────────────────────────
echo ""
echo "=== [Step 7] Utility-Coding Evaluation [ID] (Magicoder eval split) ==="

for MODEL_NAME in $EVAL_MODELS; do
    echo "--- Coding ID eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ] || [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
    fi
    python run_utility_id_eval.py \
      --base_model $MODEL \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      --eval_type coding \
      --data_path ../../data/utility_coding_eval.json \
      --n_samples $N_UTILITY_ID \
      --output_json $RESULTS_JSON \
      || { echo "Coding ID eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 8: Utility-汎用 評価 [OOD] — ARC / HellaSwag
# ──────────────────────────────────────────
echo ""
echo "=== [Step 8] Utility-General Evaluation [OOD] (ARC / HellaSwag) ==="

GENERAL_ARGS="--base_model $MODEL \
             --eval_type general \
             --output_json $RESULTS_JSON \
             --lm_eval_output_dir $LM_EVAL_RAW \
             --limit $LIMIT_UTILITY \
             --batch_size 4"

for MODEL_NAME in $EVAL_MODELS; do
    echo "--- General OOD eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG=""
    elif [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
        TEMPLATE_ARG="--apply_chat_template"
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
        TEMPLATE_ARG="--apply_chat_template"
    fi
    python run_utility_eval.py \
      $GENERAL_ARGS \
      $ADAPTER_ARG \
      $TEMPLATE_ARG \
      --model_name $MODEL_NAME \
      || { echo "General eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# 完了
# ──────────────────────────────────────────
echo ""
echo "============================================================"
echo " Utility Fine-Tuning & Evaluation Complete"
echo "============================================================"
echo " Results JSON : $RESULTS_JSON"
echo " lm_eval Raw  : $LM_EVAL_RAW"
echo ""
echo " 評価サマリー:"
echo "  └─ Utility"
echo "      ├─ [ID]  Finance (finance-alpaca eval) ROUGE-L (n=$N_UTILITY_ID)"
echo "      ├─ [OOD] Finance MMLU (business_ethics/macroeconomics/econometrics)"
echo "      ├─ [ID]  Coding (Magicoder eval)       ROUGE-L (n=$N_UTILITY_ID)"
echo "      ├─ [OOD] HumanEval / MBPP / GSM8K"
echo "      └─ [OOD] ARC / HellaSwag"
echo "============================================================"
