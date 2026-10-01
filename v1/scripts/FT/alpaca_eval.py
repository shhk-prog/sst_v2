import os
num = input("gpu num:")
os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from peft import PeftModel
from tqdm import tqdm
import json
from rouge_score import rouge_scorer
import numpy as np

#####################################################
# 設定
#####################################################
# model_id = "mistralai/Mistral-7B-Instruct-v0.3"
# model_id = "meta-llama/Llama-3.1-8B-Instruct"
model_id = "meta-llama/Llama-3.1-8B-Instruct"
adapter_path = "./FT_model/A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4"  # ファインチューニング済みアダプタのパス
use_adapter = True  # Falseにするとベースモデルのみで評価
num_samples = 500  # 評価するサンプル数 (Noneで全データ)

# 出力ファイル名を自動生成
output_dir = "../../results/finetuned"
os.makedirs(output_dir, exist_ok=True)
adapter_name = os.path.basename(adapter_path) if use_adapter else "base_model"
output_file = os.path.join(output_dir, f"{adapter_name}_alpaca_eval_results.json")
print(f"Output file: {output_file}")
#####################################################

print(f"Loading base model: {model_id}")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    device_map='auto',
    torch_dtype=torch.bfloat16,
)

if use_adapter:
    print(f"Loading adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)
    model = model.merge_and_unload()

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    padding_side="left",
    add_eos_token=True
)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

model.eval()

# データセット読み込み
print("Loading Alpaca dataset...")
dataset = load_dataset("tatsu-lab/alpaca", split="train")

if num_samples is not None:
    dataset = dataset.select(range(min(num_samples, len(dataset))))

print(f"Evaluating on {len(dataset)} samples...")

def generate_response(instruction: str, input_text: str) -> str:
    """指示に対する回答を生成"""
    user_content = instruction
    if input_text:
        user_content = instruction + "\n" + input_text
    
    messages = [
        {'role': "system", 'content': "You are an useful assistant"},
        {'role': "user", 'content': user_content},
    ]
    
    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=256,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.pad_token_id,
        )
    
    response = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(response, skip_special_tokens=True)

# ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

results = []
rouge1_scores = []
rouge2_scores = []
rougeL_scores = []

for example in tqdm(dataset, desc="Evaluating"):
    instruction = example["instruction"]
    input_text = example["input"]
    ground_truth = example["output"]
    
    prediction = generate_response(instruction, input_text)
    
    # ROUGE計算
    scores = scorer.score(ground_truth, prediction)
    rouge1_scores.append(scores['rouge1'].fmeasure)
    rouge2_scores.append(scores['rouge2'].fmeasure)
    rougeL_scores.append(scores['rougeL'].fmeasure)
    
    results.append({
        "instruction": instruction,
        "input": input_text,
        "ground_truth": ground_truth,
        "prediction": prediction,
        "rouge1": scores['rouge1'].fmeasure,
        "rouge2": scores['rouge2'].fmeasure,
        "rougeL": scores['rougeL'].fmeasure,
    })

# 結果の集計
summary = {
    "model_id": model_id,
    "adapter_path": adapter_path if use_adapter else None,
    "num_samples": len(dataset),
    "metrics": {
        "rouge1": {
            "mean": float(np.mean(rouge1_scores)),
            "std": float(np.std(rouge1_scores)),
        },
        "rouge2": {
            "mean": float(np.mean(rouge2_scores)),
            "std": float(np.std(rouge2_scores)),
        },
        "rougeL": {
            "mean": float(np.mean(rougeL_scores)),
            "std": float(np.std(rougeL_scores)),
        },
    },
    "results": results,
}

# 結果の保存
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\n" + "="*50)
print("Evaluation Results")
print("="*50)
print(f"Model: {model_id}")
print(f"Adapter: {adapter_path if use_adapter else 'None (base model)'}")
print(f"Samples: {len(dataset)}")
print("-"*50)
print(f"ROUGE-1: {np.mean(rouge1_scores):.4f} ± {np.std(rouge1_scores):.4f}")
print(f"ROUGE-2: {np.mean(rouge2_scores):.4f} ± {np.std(rouge2_scores):.4f}")
print(f"ROUGE-L: {np.mean(rougeL_scores):.4f} ± {np.std(rougeL_scores):.4f}")
print("="*50)
print(f"Results saved to: {output_file}")
