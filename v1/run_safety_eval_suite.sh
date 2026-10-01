#!/bin/bash
# Paths relative to sst_merge_v5/scripts/FT/
ADAPTER_ROOT="../../models/finetuned/adapters/FT_model"
GPU=2
SAMPLES=100
PROMPT_FILE="../../../data/response_dataframe.csv"

# Models to evaluate (Adapter Name, Subdir if any)
models=(
    "A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4" ""
    "A7_safety_meta_llama_3.1_8b_instruct_r16_10ep_lr2e-4" ""
    "Safety_FT_Baseline_on_A5" ""
    "Safety_FT_Mixed_on_A5_vol1400_mix0.2_lr0.0002" "checkpoint-111"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.4_lr0.0002" "checkpoint-132"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.6_lr0.0002" "checkpoint-174"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.8_lr0.0002" "checkpoint-219"
)

cd sst_merge_v5/scripts/FT/

for i in $(seq 0 2 $(( ${#models[@]} - 1 ))); do
    adapter="${models[$i]}"
    subdir="${models[$((i+1))]}"
    
    path="${ADAPTER_ROOT}/${adapter}"
    if [ -n "$subdir" ]; then
        path="${path}/${subdir}"
    fi
    
    echo "===================================================="
    echo "Evaluating: $adapter ($subdir)"
    echo "===================================================="
    python jailbreak_eval.py \
        --adapter_path "$path" \
        --gpu $GPU \
        --num_samples $SAMPLES \
        --custom_prompts_path "$PROMPT_FILE" \
        --output_dir "../../results/robustness_validation/jailbreak"
done

# Evaluate Base Model (No adapter)
echo "===================================================="
echo "Evaluating: Base Model (meta-llama/Llama-3.1-8B-Instruct)"
echo "===================================================="
python jailbreak_eval.py \
    --gpu $GPU \
    --num_samples $SAMPLES \
    --custom_prompts_path "$PROMPT_FILE" \
    --output_dir "../../results/robustness_validation/jailbreak"

