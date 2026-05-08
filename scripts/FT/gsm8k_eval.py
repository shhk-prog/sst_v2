import os
num = input("gpu num:")
os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from peft import PeftModel
from tqdm import tqdm
import json
import numpy as np
import re

#####################################################
# 設定
#####################################################
model_id = "meta-llama/Llama-3.1-8B-Instruct"
adapter_path = "./FT_model/A8_math_meta_llama_3.1_8b_instruct_gsm8k_r16_7ep_lr1e-4"  # ファインチューニング済みアダプタのパス
use_adapter = True  # Falseにするとベースモデルのみで評価
num_samples = 500  # 評価するサンプル数 (Noneで全データ)

# 出力ファイル名を自動生成
output_dir = "../../results/finetuned"
os.makedirs(output_dir, exist_ok=True)
adapter_name = os.path.basename(adapter_path) if use_adapter else "base_model"
output_file = os.path.join(output_dir, f"{adapter_name}_gsm8k_eval_results.json")
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
print("Loading GSM8K test dataset...")
dataset = load_dataset("gsm8k", "main", split="test")

if num_samples is not None:
    dataset = dataset.select(range(min(num_samples, len(dataset))))

print(f"Evaluating on {len(dataset)} samples...")


def extract_answer(text: str) -> int:
    """
    GSM8Kの答えから数値を抽出
    答えは "#### 数値" の形式で記載されている
    """
    # "#### 数値" パターンを探す
    match = re.search(r'####\s*(-?\d+(?:,\d+)*)', text)
    if match:
        # カンマを削除して整数に変換
        return int(match.group(1).replace(',', ''))
    
    # パターンが見つからない場合、最後の数値を探す
    numbers = re.findall(r'-?\d+(?:,\d+)*', text)
    if numbers:
        return int(numbers[-1].replace(',', ''))
    
    return None


def generate_response(question: str) -> str:
    """質問に対する回答を生成"""
    messages = [
        {'role': "system", 'content': 
         "You are a helpful math assistant. Solve the following math problem step by step.\n"
         "IMPORTANT: Pay close attention to the scale of numbers (thousands, millions, etc.).\n"
         "When dealing with money, always include the correct units (dollars, cents).\n"
         "Double-check your arithmetic at each step before proceeding."},
        {'role': "user", 'content': question},
    ]
    
    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=512,  # 数学問題は長い説明が必要
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.pad_token_id,
        )
    
    response = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(response, skip_special_tokens=True)


# 評価
results = []
correct = 0
total = 0

for example in tqdm(dataset, desc="Evaluating"):
    question = example["question"]
    ground_truth_text = example["answer"]
    ground_truth = extract_answer(ground_truth_text)
    
    if ground_truth is None:
        print(f"Warning: Could not extract answer from: {ground_truth_text}")
        continue
    
    prediction_text = generate_response(question)
    prediction = extract_answer(prediction_text)
    
    is_correct = (prediction == ground_truth) if prediction is not None else False
    
    if is_correct:
        correct += 1
    total += 1
    
    results.append({
        "question": question,
        "ground_truth": ground_truth,
        "ground_truth_text": ground_truth_text,
        "prediction": prediction,
        "prediction_text": prediction_text,
        "is_correct": is_correct,
    })

# 正解率を計算
accuracy = correct / total if total > 0 else 0

# 結果の集計
summary = {
    "model_id": model_id,
    "adapter_path": adapter_path if use_adapter else None,
    "num_samples": total,
    "metrics": {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
    },
    "results": results,
}

# 結果の保存
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\n" + "="*50)
print("GSM8K Evaluation Results")
print("="*50)
print(f"Model: {model_id}")
print(f"Adapter: {adapter_path if use_adapter else 'None (base model)'}")
print(f"Samples: {total}")
print("-"*50)
print(f"Accuracy: {accuracy:.2%} ({correct}/{total})")
print("="*50)
print(f"Results saved to: {output_file}")
