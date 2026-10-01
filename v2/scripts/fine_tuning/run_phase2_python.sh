#!/bin/bash
# Phase 2a: Python-only coding LoRA + chat-template eval
#
# Usage (from v2/scripts/fine_tuning):
#   USE_ES=true ./run_phase2_python.sh    # Early stopping (defaults to lr5e-4_ep10_python_es)
#   USE_ES=false ./run_phase2_python.sh   # Full training (defaults to lr5e-4_ep10_python_full)
#   USE_CLEAN=true USE_ES=true ./run_phase2_python.sh # Use clean data
#   ./run_phase2_python.sh --skip-train   # eval only
#   ./run_phase2_python.sh --skip-data    # assume JSON already built
#
set -e
cd "$(dirname "$0")"

DOTENV_PATH="$HOME/src/.env"
if [ -f "$DOTENV_PATH" ]; then
    set -a
    source "$DOTENV_PATH"
    set +a
    [ -n "$HUGGINGFACE_HUB_TOKEN" ] && export HF_TOKEN=$HUGGINGFACE_HUB_TOKEN
fi

if [ -n "$SST_HOME" ] && [ -d "$SST_HOME/venv_sst" ]; then
    source "$SST_HOME/venv_sst/bin/activate"
else
    source ../../../venv_sst/bin/activate || { echo "ERROR: venv_sst not found"; exit 1; }
fi

# HF キャッシュを v2/.cache に固定（/mnt/iag-02 と /mnt/nas のパス不整合対策）
export HF_HOME="$(cd ../.. && pwd)/.cache/huggingface"
export HF_METRICS_CACHE="$HF_HOME/metrics"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_CACHE="$HF_HOME/hub"
mkdir -p "$HF_METRICS_CACHE" "$HF_DATASETS_CACHE" "$HF_HUB_CACHE"

SKIP_DATA=false
SKIP_TRAIN=false
SKIP_EVAL=false
for arg in "$@"; do
    case "$arg" in
        --skip-data)  SKIP_DATA=true ;;
        --skip-train) SKIP_TRAIN=true ;;
        --skip-eval)  SKIP_EVAL=true ;;
    esac
done

MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
MODEL_DIR_NAME=$(basename "$MODEL" | sed 's/Meta-//')

USE_ES=${USE_ES:-true}
if [ "$USE_ES" = true ]; then
    RUN_NAME=${RUN_NAME:-"lr2e-5_ep3_python_es"}
    ES_ARGS=""
    echo "Using Early Stopping."
else
    RUN_NAME=${RUN_NAME:-"lr2e-5_ep3_python_full"}
    ES_ARGS="--no_early_stopping"
    echo "Running FULL training (no early stopping)."
fi
MODEL_BASE_DIR="../../models/$MODEL_DIR_NAME/$RUN_NAME"
LM_EVAL_RAW="../../results/lm_eval_raw"
RESULTS_JSON="../../results/$MODEL_DIR_NAME/$RUN_NAME/phase2_python_eval_results.json"

USE_CLEAN=${USE_CLEAN:-false}
if [ "$USE_CLEAN" = true ]; then
    CLEAN_SUFFIX="_clean"
    DATA_SUFFIX="python_clean"
else
    CLEAN_SUFFIX=""
    DATA_SUFFIX="python (no aggressive clean)"
fi

echo "=== Phase 2a Python Coding Run: $RUN_NAME ==="
echo "  model dir : $MODEL_BASE_DIR/coding_lora"
echo "  data      : utility_coding_python${CLEAN_SUFFIX}.json - $DATA_SUFFIX"

LR=${LR:-"2e-5"}
EPOCHS=${EPOCHS:-"3"}
PATIENCE=${PATIENCE:-"2"}

echo "  train     : epochs=$EPOCHS, lr=$LR, patience=$PATIENCE, assistant_only_loss=True"

mkdir -p "../../data" "../../results/$MODEL_DIR_NAME/$RUN_NAME" "$LM_EVAL_RAW"
mkdir -p "$MODEL_BASE_DIR/coding_lora"

# ── Step 1: Python-only dataset (raw solution, no aggressive clean) ──
if [ "$SKIP_DATA" = false ]; then
    echo ""
    echo "=== [1] Prepare Python-only coding dataset ==="
    if [ -f "../../data/utility_coding_python${CLEAN_SUFFIX}.json" ] && [ -f "../../data/utility_coding_python${CLEAN_SUFFIX}_eval.json" ]; then
        echo "  utility_coding_python${CLEAN_SUFFIX}*.json already exist. Skip download (delete files to rebuild)."
    else
        PREP_ARGS="--coding-python-only"
        if [ "$USE_CLEAN" = true ]; then
            PREP_ARGS="$PREP_ARGS --clean-coding-output"
        fi
        python ../data_prep/prepare_datasets.py $PREP_ARGS \
            || { echo "Failed to prepare dataset"; exit 1; }
    fi
fi

# ── Step 2: Fine-tuning ──
if [ "$SKIP_TRAIN" = false ]; then
    echo ""
    echo "=== [2] Fine-tune coding_lora (Python-only) ==="
    python run_lora_ft.py \
        --model_name_or_path "$MODEL" \
        --utility_dataset_path ../../data/utility_coding_python${CLEAN_SUFFIX}.json \
        --eval_dataset_path ../../data/utility_coding_python${CLEAN_SUFFIX}_eval.json \
        --output_dir "$MODEL_BASE_DIR/coding_lora" \
        --epochs $EPOCHS \
        --learning_rate $LR \
        --early_stopping_patience $PATIENCE \
        --warmup_ratio 0.05 \
        $ES_ARGS \
        || { echo "Training failed"; exit 1; }
    echo "  [Done] $MODEL_BASE_DIR/coding_lora"
fi

# ── Step 3: OOD eval (HumanEval / MBPP / GSM8K) with chat template ──
if [ "$SKIP_EVAL" = false ]; then
    echo ""
    echo "=== [3] Utility-Coding OOD eval (apply_chat_template) ==="
    python run_utility_eval.py \
        --base_model "$MODEL" \
        --adapter_path "$MODEL_BASE_DIR/coding_lora" \
        --model_name coding_lora_python \
        --eval_type coding \
        --apply_chat_template \
        --output_json "$RESULTS_JSON" \
        --lm_eval_output_dir "$LM_EVAL_RAW" \
        --batch_size 4 \
        || { echo "Eval failed"; exit 1; }

    echo ""
    echo "=== Optional: compare with base (same template) ==="
    echo "  python run_utility_eval.py --base_model $MODEL --model_name base_with_template \\"
    echo "    --eval_type coding --apply_chat_template --lm_eval_output_dir $LM_EVAL_RAW"
    echo ""
    echo "=== Optional: analyze HumanEval failures ==="
    echo "  python analyze_humaneval_samples.py \\"
    echo "    $LM_EVAL_RAW/coding_lora_python/coding/*/samples_humaneval_*.jsonl"
fi

echo ""
echo "=== Phase 2a complete ==="
