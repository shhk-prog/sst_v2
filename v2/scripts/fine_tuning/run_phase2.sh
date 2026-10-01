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
LR=${LR:-"2e-5"}
EPOCHS=${EPOCHS:-"3"}

RUN_NAME=${RUN_NAME:-"lr${LR}_ep${EPOCHS}_instruct_all"}

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
echo "  ┌─ Safety"
echo "  │   ├─ [ID/OOD] AdvBench + TrustLLM ASR  (Llama-Guard-3-8B)"
echo "  │   ├─ [OOD]    HarmBench ASR             (Llama-Guard-3-8B)"
echo "  │   └─ [OOD]    XSTest FPR               (over-refusal)"
echo "  └─ Utility"
echo "      ├─ [ID]  Finance eval split    ROUGE-L"
echo "      ├─ [OOD] MMLU Finance          acc (business_ethics / macroeconomics / econometrics)"
echo "      ├─ [ID]  Coding eval split     ROUGE-L"
echo "      ├─ [OOD] HumanEval             pass@1"
echo "      ├─ [OOD] MBPP                  pass@1"
echo "      ├─ [OOD] GSM8K                 exact_match (CoT)"
echo "      └─ [OOD] ARC / HellaSwag       acc_norm (catastrophic forgetting)"

# 評価サンプル数設定
N_SAFETY_ID=2000      # AdvBench + TrustLLM (FT使用データ, ID)
N_SAFETY_OOD=200      # HarmBench (FT未使用データ, OOD)
N_UTILITY_ID=200      # Finance/Coding eval split (FT使用データ, ID)
LIMIT_UTILITY=2000    # OOD lm-eval サンプル数 (None にすると全件)

# ──────────────────────────────────────────
# Step 1: データ準備
# ──────────────────────────────────────────
echo ""
echo "=== [Step 1] Preparing Datasets ==="
mkdir -p ../../data ../../results

# 必要なデータセットの一覧 (Finance, Coding, Safety, HarmBench, XSTest)
REQUIRED_DATASETS=(
    "../../data/utility_finance.json"
    "../../data/utility_finance_eval.json"
    "../../data/utility_coding.json"
    "../../data/utility_coding_eval.json"
    "../../data/safety_combined.json"
    "../../data/safety_combined_eval.json"
    "../../data/safety_harmbench.json"
    "../../data/xstest_prompts.json"
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
mkdir -p "$MODEL_BASE_DIR/safety_lora"
mkdir -p "$MODEL_BASE_DIR/mixed_lora"

# ──────────────────────────────────────────
# Step 3: Fine-Tuning
#   変更点 (lr5e-5_ep5_opt):
#     - utility_lora: lr=5e-5, epochs=5, assistant_only_loss=True (回答部分のみ学習)
#     - coding_lora : lr=5e-5, epochs=5, assistant_only_loss=True (回答部分のみ学習)
#     - safety_lora : 変更なし (lr=5e-4, epochs=5)
#     - mixed_lora  : 変更なし (lr=5e-4, epochs=5)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 3] Fine-Tuning ==="

echo "--- Utility FT (Finance: finance-alpaca, lr=5e-5, epochs=5, assistant_only_loss) ---"
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

echo "--- Utility FT (Coding: Magicoder OSS-INSTRUCT, lr=5e-5, epochs=5, assistant_only_loss) ---"
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
echo "  [Tip] Phase 2a (Python-only, no ES): RUN_NAME=lr2e-4_ep10_python ./run_phase2_python.sh"

echo "--- Safety FT (AdvBench + TrustLLM, 現状維持) ---"
python run_lora_ft.py \
  --model_name_or_path $MODEL \
  --safety_dataset_path ../../data/safety_combined.json \
  --eval_dataset_path ../../data/safety_combined_eval.json \
  --output_dir "$MODEL_BASE_DIR/safety_lora" \
  --epochs $EPOCHS \
  --learning_rate $LR \
  || { echo "Safety FT failed"; exit 1; }
echo "  [Done] safety_lora"

echo "--- Mixed FT Baseline (50% Safety / 50% Finance) ---"
python run_lora_ft.py \
  --model_name_or_path $MODEL \
  --utility_dataset_path ../../data/utility_finance.json \
  --safety_dataset_path ../../data/safety_combined.json \
  --eval_dataset_path ../../data/safety_combined_eval.json \
  --safety_mix_ratio 0.5 \
  --output_dir "$MODEL_BASE_DIR/mixed_lora" \
  --epochs $EPOCHS \
  --learning_rate $LR \
  || { echo "Mixed FT failed"; exit 1; }
echo "  [Done] mixed_lora"

echo ""
echo "=== [Step 3] Fine-Tuning Complete ==="

# ──────────────────────────────────────────
# Step 4: Safety 評価 [ID] — AdvBench + TrustLLM
#   FT に使用したデータセットでの評価 (In-Distribution)
#   Judge  : Llama-Guard-3-8B
#   Metric : ASR (Attack Success Rate)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 4] Safety Evaluation [ID] (AdvBench + TrustLLM) ==="
echo "  judge  : Llama-Guard-3-8B"
echo "  data   : AdvBench + TrustLLM JailbreakTrigger (FT使用データ)"
echo "  metric : ASR"

SAFETY_ID_ARGS="--base_model $MODEL \
             --data_path ../../data/safety_combined.json \
             --n_samples $N_SAFETY_ID \
             --output_json $RESULTS_JSON"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
    echo "--- Safety ID eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ] || [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
    fi
    python run_safety_eval.py \
      $SAFETY_ID_ARGS \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      || { echo "Safety ID eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 5: Safety 評価 [OOD] — HarmBench
#   FT に使用していないデータセットでの評価 (Out-of-Distribution)
#   Ref: LED-Merging (ACL 2025)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 5] Safety Evaluation [OOD] (HarmBench) ==="
echo "  judge  : Llama-Guard-3-8B"
echo "  data   : HarmBench (FT未使用データ)"
echo "  metric : ASR"
echo "  ref    : LED-Merging (ACL 2025)"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
    echo "--- HarmBench OOD eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ] || [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
    fi
    python run_harmbench_eval.py \
      --base_model $MODEL \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      --data_path ../../data/safety_harmbench.json \
      --n_samples $N_SAFETY_OOD \
      --output_json $RESULTS_JSON \
      || { echo "HarmBench eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# Step 6: Utility-Finance 評価 [OOD] — MMLU
#   FT に使用していないデータセットでの評価 (OOD)
#   Tasks  : mmlu_business_ethics (5-shot)
#            mmlu_high_school_macroeconomics (5-shot)
#            mmlu_econometrics (5-shot)
#   Ref    : MERGE ALIGN (Arxiv 2024)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 6] Utility-Finance Evaluation [OOD] (MMLU) ==="
echo "  tasks : mmlu_business_ethics / macroeconomics / econometrics (FT未使用データ)"
echo "  ref   : MERGE ALIGN (Arxiv 2024)"

FINANCE_OOD_ARGS="--base_model $MODEL \
               --eval_type finance \
               --output_json $RESULTS_JSON \
               --lm_eval_output_dir $LM_EVAL_RAW \
               --limit $LIMIT_UTILITY \
               --batch_size 4"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
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
# Step 7: Utility-Finance 評価 [ID] — finance-alpaca eval split
#   FT に使用したデータセット (eval split) での評価 (In-Distribution)
#   Metric : ROUGE-L
# ──────────────────────────────────────────
echo ""
echo "=== [Step 7] Utility-Finance Evaluation [ID] (finance-alpaca eval split) ==="
echo "  data   : utility_finance_eval.json (FT使用データの eval 10%)"
echo "  metric : ROUGE-L"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
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
# Step 8: Utility-Coding 評価 [OOD] — HumanEval / MBPP / GSM8K
#   FT に使用していないデータセットでの評価 (OOD)
#   Ref    : LED-Merging (ACL 2025), SafeMERGE (ICLR 2025)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 8] Utility-Coding Evaluation [OOD] (HumanEval / MBPP / GSM8K) ==="
echo "  tasks : humaneval (pass@1) / mbpp (pass@1) / gsm8k_cot_zeroshot (FT未使用データ)"
echo "  ref   : LED-Merging (ACL 2025), SafeMERGE (ICLR 2025)"

CODING_OOD_ARGS="--base_model $MODEL \
              --eval_type coding \
              --output_json $RESULTS_JSON \
              --lm_eval_output_dir $LM_EVAL_RAW \
              --limit $LIMIT_UTILITY \
              --batch_size 4"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
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
# Step 9: Utility-Coding 評価 [ID] — Magicoder eval split
#   FT に使用したデータセット (eval split) での評価 (In-Distribution)
#   Metric : ROUGE-L
# ──────────────────────────────────────────
echo ""
echo "=== [Step 9] Utility-Coding Evaluation [ID] (Magicoder eval split) ==="
echo "  data   : utility_coding_eval.json (FT使用データの eval 10%)"
echo "  metric : ROUGE-L"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
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
# Step 10: Utility-汎用 評価 [OOD] — ARC / HellaSwag
#   Catastrophic Forgetting の測定
#   Ref    : SafeMERGE, LED-Merging 等多数
# ──────────────────────────────────────────
echo ""
echo "=== [Step 10] Utility-General Evaluation [OOD] (ARC / HellaSwag) ==="
echo "  tasks : arc_challenge (25-shot) / hellaswag (10-shot)"
echo "  用途  : Catastrophic Forgetting 測定"

GENERAL_ARGS="--base_model $MODEL \
             --eval_type general \
             --output_json $RESULTS_JSON \
             --lm_eval_output_dir $LM_EVAL_RAW \
             --limit $LIMIT_UTILITY \
             --batch_size 4"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
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
# Step 11: Safety 過剰拒絶 評価 [OOD] — XSTest
#   FT に使用していないデータセットでの過剰拒絶評価 (OOD)
#   Ref    : SafeMERGE (ICLR 2025)
# ──────────────────────────────────────────
echo ""
echo "=== [Step 11] Safety Over-refusal Evaluation [OOD] (XSTest) ==="
echo "  data   : XSTest (FT未使用データ)"
echo "  metric : FPR (False Positive Rate)"

for MODEL_NAME in base_model base_with_template utility_lora coding_lora safety_lora mixed_lora; do
    echo "--- Over-refusal eval: $MODEL_NAME ---"
    if [ "$MODEL_NAME" = "base_model" ] || [ "$MODEL_NAME" = "base_with_template" ]; then
        ADAPTER_ARG=""
    else
        ADAPTER_ARG="--adapter_path $MODEL_BASE_DIR/$MODEL_NAME"
    fi
    python run_overrefusal_eval.py \
      --base_model $MODEL \
      $ADAPTER_ARG \
      --model_name $MODEL_NAME \
      --data_path ../../data/xstest_prompts.json \
      --output_json $RESULTS_JSON \
      || { echo "Over-refusal eval failed for $MODEL_NAME"; exit 1; }
done

# ──────────────────────────────────────────
# 完了
# ──────────────────────────────────────────
echo ""
echo "============================================================"
echo " Phase 2: Fine-Tuning & Evaluation Complete"
echo "============================================================"
echo " Results JSON : $RESULTS_JSON"
echo " lm_eval Raw  : $LM_EVAL_RAW"
echo ""
echo " 評価サマリー:"
echo "  ┌─ Safety"
echo "  │   ├─ [ID/OOD]  AdvBench+TrustLLM ASR  (n=$N_SAFETY_ID)"
echo "  │   ├─ [OOD]     HarmBench ASR           (n=$N_SAFETY_OOD)"
echo "  │   └─ [OOD]     XSTest FPR"
echo "  └─ Utility"
echo "      ├─ [ID]  Finance (finance-alpaca eval) ROUGE-L (n=$N_UTILITY_ID)"
echo "      ├─ [OOD] Finance MMLU (business_ethics/macroeconomics/econometrics)"
echo "      ├─ [ID]  Coding (Magicoder eval)       ROUGE-L (n=$N_UTILITY_ID)"
echo "      ├─ [OOD] HumanEval / MBPP / GSM8K"
echo "      └─ [OOD] ARC / HellaSwag"
echo "============================================================"
