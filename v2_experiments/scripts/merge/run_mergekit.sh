#!/bin/bash
# run_mergekit.sh: Mergekitを用いたベースライン手法（Task Arithmetic, TIES）の実行スクリプト
# Mergekitがインストールされている前提

BASE_MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
UTILITY_MODEL="../../models/utility_ft_model"
SAFETY_MODEL="../../models/safety_ft_model"
OUTPUT_DIR="../../models/merged"

mkdir -p $OUTPUT_DIR

# ---------------------------------------------------------
# 1. Task Arithmetic (Mergekit config)
# ---------------------------------------------------------
cat <<EOF > task_arithmetic_config.yaml
models:
  - model: $BASE_MODEL
    # no parameters necessary for base model
  - model: $UTILITY_MODEL
    parameters:
      weight: 1.0
  - model: $SAFETY_MODEL
    parameters:
      weight: 0.5 # スイープパラメータ (alpha)
merge_method: task_arithmetic
base_model: $BASE_MODEL
dtype: float16
EOF

echo "Running Task Arithmetic via Mergekit..."
mergekit-yaml task_arithmetic_config.yaml $OUTPUT_DIR/task_arithmetic_alpha05
echo "Task Arithmetic merge complete."

# ---------------------------------------------------------
# 2. TIES (Mergekit config)
# ---------------------------------------------------------
cat <<EOF > ties_config.yaml
models:
  - model: $UTILITY_MODEL
    parameters:
      density: 0.5
      weight: 1.0
  - model: $SAFETY_MODEL
    parameters:
      density: 0.5 # トップk%の保持率
      weight: 0.5  # スイープパラメータ (alpha)
merge_method: ties
base_model: $BASE_MODEL
parameters:
  normalize: false
dtype: float16
EOF

echo "Running TIES via Mergekit..."
mergekit-yaml ties_config.yaml $OUTPUT_DIR/ties_alpha05_k50
echo "TIES merge complete."

echo "All baseline merges finished."
