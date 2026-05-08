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
# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.bfloat16
# )
# model_id="mistralai/Mistral-7B-Instruct-v0.3"
# model_id = "Qwen/Qwen2.5-7B-Instruct"
model_id = "meta-llama/Llama-3.1-8B-Instruct"
# model_id="mistralai/Mistral-7B-v0.1"
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    trust_remote_code=True,
    # quantization_config=bnb_config,
    device_map='auto',
    torch_dtype=torch.bfloat16,
    # attn_implementation="flash_attention_2"
)
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    padding_side="right",
    add_eos_token=True
)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# messages = [
#     {"role": "system", "content": "あなたは日本語で回答するアシスタントです。"},
#     {"role": "user", "content": "GDPとは何ですか？"},
# ]

# input_ids = tokenizer.apply_chat_template(
#     messages,
#     add_generation_prompt=True,
#     return_tensors="pt"
# ).to(model.device)

# terminators = [
#     tokenizer.eos_token_id,
#     tokenizer.convert_tokens_to_ids("<|eot_id|>")
# ]

# outputs = model.generate(
#     input_ids,
#     max_new_tokens=256,
#     eos_token_id=terminators,
#     do_sample=True,
#     temperature=0.6,
#     top_p=0.9,
# )
# response = outputs[0][input_ids.shape[-1]:]

# print(tokenizer.decode(response, skip_special_tokens=True))


def formatting_func(example):
        messages = [
            {'role': "system",'content': "You are an useful assistant"},
            {'role': "user",'content': example["question"]},
            {'role': "assistant",'content': example["answer"]}
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False)

def update_dataset(example):
    example["text"] = formatting_func(example)
    for field in ["document_id", "document_topic", "document_path", "document_extracted", "question_id", "question", "answer", "long_answer"]:
        example.pop(field, None)
    return example

# dataset = load_dataset("ServiceNow/repliqa", split=["repliqa_0", "repliqa_1", "repliqa_2", "repliqa_3", "repliqa_5"])
dataset = load_dataset("ServiceNow/repliqa", split="repliqa_0")
dataset = dataset.map(update_dataset)

print(dataset[0]["text"])

#####################################################
# ハイパーパラメータ設定
#####################################################
lora_r = 16
lora_alpha = 32
num_epochs = 10
learning_rate = 2e-4
#####################################################

peft_config = LoraConfig(
    r=lora_r,
    lora_alpha=lora_alpha,
    lora_dropout=0.05,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj","gate_proj", "up_proj", "down_proj",],
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
    # report_to="wandb" 
)

# モデル名を短縮形に変換
MODEL_SHORT_NAMES = {
    # LLaMA Base models
    "meta-llama/Meta-Llama-3.1-8B": "meta_llama_3.1_8b",
    "meta-llama/Meta-Llama-3-8B": "meta_llama_3_8b",
    # LLaMA Instruct models
    "meta-llama/Llama-3.1-8B-Instruct": "meta_llama_3.1_8b_instruct",
    "meta-llama/Meta-Llama-3.1-8B-Instruct": "meta_llama_3.1_8b_instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct": "meta_llama_3_8b_instruct",
    "meta-llama/Llama-3.2-3B-Instruct": "meta_llama_3.2_3b_instruct",
    "meta-llama/Llama-3.2-1B-Instruct": "meta_llama_3.2_1b_instruct",
    # Mistral Instruct models
    "mistralai/Mistral-7B-Instruct-v0.1": "mistral_7b_v0.1_instruct",
    "mistralai/Mistral-7B-Instruct-v0.2": "mistral_7b_v0.2_instruct",
    "mistralai/Mistral-7B-Instruct-v0.3": "mistral_7b_v0.3_instruct",
    # Mistral Base models
    "mistralai/Mistral-7B-v0.1": "mistral_7b_v0.1",
    "mistralai/Mistral-7B-v0.3": "mistral_7b_v0.3",
    # Qwen models
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
new_model = f"./FT_model/A5_utility_{model_short}_repliqa_r{lora_r}_{num_epochs}ep_lr{lr_str}"
print(f"Output model path: {new_model}")

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_arguments,
)


trainer.train()
trainer.model.save_pretrained(new_model)

# model.save_pretrained("fine-tuned-t5-paws") 
# tokenizer.save_pretrained("fine-tuned-t5-paws")