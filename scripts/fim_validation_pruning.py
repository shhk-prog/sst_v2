import torch
import json
import os
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, LoraConfig, get_peft_model
from tqdm import tqdm
import numpy as np

# 設定
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
# A6 (Alpaca) アダプタとして checkpoint-2583 を使用（configで確認済み）
ADAPTER_PATH = "/mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v5/results/checkpoint-2583"
EVAL_FILE = "/mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v5/eval/merged/sst_merge/merge_eval/A6_A7_task_arithmetic_a0.5_alpaca_eval_results.json"
DEVICE = "cuda"

def load_prompts(file_path, num_samples=40):
    with open(file_path, 'r') as f:
        data = json.load(f)
    results = data.get('results', [])
    prompts = [res['instruction'] for res in results if '<nooutput>' not in res.get('ground_truth', '')]
    return prompts[:num_samples]

def get_lora_params(model):
    params = []
    for name, param in model.named_parameters():
        if 'lora' in name.lower():
            params.append(param)
    return params

def compute_fim(model, tokenizer, prompts, device):
    model.train()
    total_grad_sq = None
    num_samples = len(prompts)
    
    print(f"Computing FIM with {num_samples} samples...")
    for prompt in tqdm(prompts):
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        model.zero_grad()
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
        loss.backward()
        
        # 勾配の2乗を蓄積
        current_grads = []
        for param in get_lora_params(model):
            if param.grad is not None:
                current_grads.append(param.grad.detach().cpu().flatten()**2)
        
        flat_grads = torch.cat(current_grads)
        if total_grad_sq is None:
            total_grad_sq = flat_grads
        else:
            total_grad_sq += flat_grads
            
    fim = total_grad_sq / num_samples
    model.eval()
    return fim

def get_magnitude(model):
    mags = []
    for param in get_lora_params(model):
        mags.append(param.detach().cpu().flatten().abs())
    return torch.cat(mags)

def apply_pruning(model, importance_scores, prune_ratio):
    # 全パラメータのインデックスを重要度順にソート
    num_params = len(importance_scores)
    num_prune = int(num_params * prune_ratio)
    
    _, top_indices = torch.topk(importance_scores, num_prune)
    
    mask = torch.ones_like(importance_scores)
    mask[top_indices] = 0.0
    
    # モデルの重みに適用
    offset = 0
    with torch.no_grad():
        for param in get_lora_params(model):
            param_size = param.numel()
            p_mask = mask[offset:offset+param_size].view_as(param).to(param.device)
            param.data.mul_(p_mask)
            offset += param_size

def eval_model(model, tokenizer, prompts, device):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for prompt in prompts:
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            outputs = model(**inputs, labels=inputs["input_ids"])
            total_loss += outputs.loss.item()
    return total_loss / len(prompts)

def main():
    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    # メモリ節約のため bfloat16 でロード
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.bfloat16, 
        device_map="auto"
    )
    
    # プロンプトの準備
    all_prompts = load_prompts(EVAL_FILE)
    fim_prompts = all_prompts[:20]
    eval_prompts = all_prompts[20:40]
    
    # 実験: FIM vs Magnitude vs Random
    ratios = [0.05, 0.1, 0.2, 0.5]
    results = {"fim": [], "magnitude": [], "random": []}
    
    # 1. Base Adapter + FIM計算
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH, is_trainable=True)
    # Ensure LoRA parameters are trainable
    for param in get_lora_params(model):
        param.requires_grad = True
        
    fim = compute_fim(model, tokenizer, fim_prompts, DEVICE)
    mags = get_magnitude(model)
    random_scores = torch.rand_like(fim)
    
    baseline_loss = eval_model(model, tokenizer, eval_prompts, DEVICE)
    print(f"Baseline Loss: {baseline_loss:.4f}")

    for ratio in ratios:
        print(f"\n--- Pruning Ratio: {ratio*100}% ---")
        
        for name, scores in [("fim", fim), ("magnitude", mags), ("random", random_scores)]:
            # アダプタをリロードしてプルーニング適用
            tmp_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            apply_pruning(tmp_model, scores, ratio)
            loss = eval_model(tmp_model, tokenizer, eval_prompts, DEVICE)
            results[name].append(loss)
            print(f"  {name}: Loss={loss:.4f} (Delta={loss-baseline_loss:.4f})")
            del tmp_model
            torch.cuda.empty_cache()

    # CSV等への保存
    with open("fim_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to fim_validation_results.json")

if __name__ == "__main__":
    main()
