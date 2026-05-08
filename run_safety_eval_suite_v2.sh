#!/bin/bash
# Paths relative to sst_merge_v5/scripts/FT/
ADAPTER_ROOT="../../models/finetuned/adapters/FT_model"
GPU=0
SAMPLES=100
PROMPT_FILE="../../../data/response_dataframe.csv"

# Models to evaluate (Adapter Name, Pretty Name)
# We evaluate the ROOT of each directory because it has the merged/final adapter.
models=(
    "A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4" "Utility_Only"
    "A7_safety_meta_llama_3.1_8b_instruct_r16_10ep_lr2e-4" "Safety_Only"
    "Safety_FT_Baseline_on_A5" "SFT_Baseline"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.2_lr0.0002" "MixedFT_s80u20"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.4_lr0.0002" "MixedFT_s60u40"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.6_lr0.0002" "MixedFT_s40u60"
    "Safety_FT_Mixed_on_A5_vol1400_mix0.8_lr0.0002" "MixedFT_s20u80"
)

cd sst_merge_v5/scripts/FT/

for i in $(seq 0 2 $(( ${#models[@]} - 1 ))); do
    adapter="${models[$i]}"
    label="${models[$((i+1))]}"
    
    path="${ADAPTER_ROOT}/${adapter}"
    
    echo "===================================================="
    echo "Evaluating $label ($adapter)"
    echo "===================================================="
    python jailbreak_eval.py \
        --adapter_path "$path" \
        --gpu $GPU \
        --num_samples $SAMPLES \
        --custom_prompts_path "$PROMPT_FILE" \
        --output_dir "../../results/robustness_validation/jailbreak"
done

# Evaluate SST Merge Model (special path)
SST_PATH="../../models/merged/sst_merge/full/compare/A5_A7_sst_compare"
echo "===================================================="
echo "Evaluating SST_Merge (A5+A7)"
echo "===================================================="
python jailbreak_eval.py \
    --adapter_path "$SST_PATH" \
    --gpu $GPU \
    --num_samples $SAMPLES \
    --custom_prompts_path "$PROMPT_FILE" \
    --output_dir "../../results/robustness_validation/jailbreak"

# Evaluate Base Model (No adapter)
echo "===================================================="
echo "Evaluating Base Model (meta-llama/Llama-3.1-8B-Instruct)"
echo "===================================================="
python jailbreak_eval.py \
    --gpu $GPU \
    --num_samples $SAMPLES \
    --custom_prompts_path "$PROMPT_FILE" \
    --output_dir "../../results/robustness_validation/jailbreak"

