import torch
from torch import cuda, bfloat16
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from datasets import load_dataset
from peft import LoraConfig, PeftModel
from trl import SFTTrainer, SFTConfig
import os

num = input("gpu num:")
os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

# モデル設定
model_id = "meta-llama/Llama-3.1-8B-Instruct"

model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    trust_remote_code=True,
    device_map='auto',
    torch_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    padding_side="right",
    add_eos_token=True
)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id


def formatting_func(example):
    """GSM8K用のフォーマット関数"""
    messages = [
        {'role': "system", 'content': 
         "You are a helpful math assistant. Solve the following math problem step by step.\n"
         "IMPORTANT: Pay close attention to the scale of numbers (thousands, millions, etc.).\n"
         "When dealing with money, always include the correct units (dollars, cents).\n"
         "Double-check your arithmetic at each step before proceeding."},
        {'role': "user", 'content': example["question"]},
        {'role': "assistant", 'content': example["answer"]}
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


def update_dataset(example):
    """データセットを更新する関数"""
    example["text"] = formatting_func(example)
    # 不要なフィールドを削除
    for field in ["question", "answer"]:
        example.pop(field, None)
    return example


# GSM8Kデータセットをロード
print("Loading GSM8K dataset...")
dataset = load_dataset("gsm8k",  "main", split="train")
dataset = dataset.map(update_dataset)

print(f"Dataset size: {len(dataset)}")
print("Sample:")
print(dataset[0]["text"])

#####################################################
# ハイパーパラメータ設定
#####################################################
lora_r = 16
lora_alpha = 32
num_epochs = 10  # 7→10: 中間値で試す
learning_rate = 2e-4  # 1e-4→2e-4: 元の設定に戻す
#####################################################

peft_config = LoraConfig(
    r=lora_r,
    lora_alpha=lora_alpha,
    lora_dropout=0.05,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM",
    modules_to_save=["embed_tokens"],
)

training_arguments = SFTConfig(
    output_dir="./results",
    bf16=True,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    num_train_epochs=num_epochs,
    optim="adamw_torch_fused",
    learning_rate=learning_rate, 
    lr_scheduler_type="cosine",
    weight_decay=0.01,
    warmup_steps=100,
    logging_steps=10,
    group_by_length=True,
    dataset_text_field="text",
    max_length=1024,
    packing=True,
)

# モデル名を短縮形に変換
MODEL_SHORT_NAMES = {
    "meta-llama/Meta-Llama-3.1-8B": "meta_llama_3.1_8b",
    "meta-llama/Meta-Llama-3-8B": "meta_llama_3_8b",
    "meta-llama/Llama-3.1-8B-Instruct": "meta_llama_3.1_8b_instruct",
    "meta-llama/Meta-Llama-3.1-8B-Instruct": "meta_llama_3.1_8b_instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct": "meta_llama_3_8b_instruct",
    "meta-llama/Llama-3.2-3B-Instruct": "meta_llama_3.2_3b_instruct",
    "meta-llama/Llama-3.2-1B-Instruct": "meta_llama_3.2_1b_instruct",
    "mistralai/Mistral-7B-Instruct-v0.1": "mistral_7b_v0.1_instruct",
    "mistralai/Mistral-7B-Instruct-v0.2": "mistral_7b_v0.2_instruct",
    "mistralai/Mistral-7B-Instruct-v0.3": "mistral_7b_v0.3_instruct",
    "mistralai/Mistral-7B-v0.1": "mistral_7b_v0.1",
    "mistralai/Mistral-7B-v0.3": "mistral_7b_v0.3",
    "Qwen/Qwen2.5-14B-Instruct": "qwen_2.5_14b_instruct",
    "Qwen/Qwen2.5-7B-Instruct": "qwen_2.5_7b_instruct",
    "Qwen/Qwen2.5-3B-Instruct": "qwen_2.5_3b_instruct",
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen_2.5_1.5b_instruct",
    "Qwen/Qwen2.5-0.5B-Instruct": "qwen_2.5_0.5b_instruct",
}
model_short = MODEL_SHORT_NAMES.get(model_id, model_id.replace("/", "_").replace("-", "_").lower())

# 学習率を文字列に変換
lr_str = f"{learning_rate:.0e}".replace("e-0", "e-")

# 出力フォルダ名を自動生成
new_model = f"./FT_model/A8_math_{model_short}_gsm8k_r{lora_r}_{num_epochs}ep_lr{lr_str}"
print(f"Output model path: {new_model}")

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_arguments,
)

print("Starting training...")
trainer.train()
trainer.model.save_pretrained(new_model)

print(f"Training completed! Model saved to: {new_model}")
