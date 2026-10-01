#!/bin/bash
set -e

# Model 1 (Math) のFT実行スクリプト
# ハイパーパラメータをスクリプト内で定義し、結果を別々に保存します。

# --- ハイパーパラメータ設定 ---
EPOCHS=3.0
BATCH_SIZE=2
GRAD_ACCUM=8
LR=2.0e-5
# ------------------------------

EFFECTIVE_BS=$(( BATCH_SIZE * GRAD_ACCUM ))
RUN_ID="model1_math_ep${EPOCHS}_bs${EFFECTIVE_BS}_lr${LR}"
OUTPUT_DIR="saves/llama3-8b/lora/${RUN_ID}"
YAML_FILE="model1_math_${RUN_ID}.yaml"

echo "Starting Model 1 (Math) FT using LLaMA-Factory..."
echo "Run ID: ${RUN_ID}"
echo "Output will be saved to: LLaMA-Factory/${OUTPUT_DIR}"

cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory

# LLaMA-Factory の仕様でコマンドラインからの上書きがエラーになるため、
# 実行用の YAML ファイルをハイパーパラメータを埋め込んで動的に生成します。
cat <<EOF > ${YAML_FILE}
### model
model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct

### method
stage: sft
do_train: true
finetuning_type: lora
lora_target: all

### dataset
dataset: mathinstruct
template: llama3
cutoff_len: 1024
overwrite_cache: true
preprocessing_num_workers: 16

### output
output_dir: ${OUTPUT_DIR}
logging_steps: 10
save_steps: 1000
plot_loss: true
overwrite_output_dir: true

### train
per_device_train_batch_size: ${BATCH_SIZE}
gradient_accumulation_steps: ${GRAD_ACCUM}
learning_rate: ${LR}
num_train_epochs: ${EPOCHS}
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
EOF

# 生成したYAMLファイルを指定して学習実行
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train ${YAML_FILE}

echo "Fine-tuning completed for ${RUN_ID}."
