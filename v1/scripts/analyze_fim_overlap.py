import os
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset, Dataset
from tqdm import tqdm
import numpy as np
import scipy.stats as stats
import json

# GPU設定
os.environ["CUDA_VISIBLE_DEVICES"] = "2"
device = "cuda" if torch.cuda.is_available() else "cpu"

model_id = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# LoRA設定
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16,
    device_map={"":0} 
)
model = get_peft_model(model, lora_config)

def compute_fim_diag(model, tokenizer, dataset, num_samples=100):
    model.eval()
    fim = {name: torch.zeros_like(param) for name, param in model.named_parameters() if param.requires_grad}
    
    count = 0
    for i in tqdm(range(min(len(dataset), num_samples)), desc="Computing FIM"):
        text = dataset[i]["text"]
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
        
        model.zero_grad()
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
        loss.backward()
        
        for name, param in model.named_parameters():
            if param.requires_grad and param.grad is not None:
                fim[name] += param.grad.data.pow(2)
        count += 1
        
    for name in fim:
        fim[name] /= count
        
    return fim

# データセット準備
print("Loading datasets...")

# 1. Utility (Alpaca)
alpaca = load_dataset("tatsu-lab/alpaca", split="train")
def format_alpaca(example):
    return {"text": f"Instruction: {example['instruction']}\nInput: {example['input']}\nOutput: {example['output']}"}
alpaca = alpaca.map(format_alpaca, remove_columns=alpaca.column_names)

# 2. Safety (Harmful)
csv_path = "../data/response_dataframe.csv"
if not os.path.exists(csv_path):
    csv_path = "./data/response_dataframe.csv" # Fallback
print(f"Safety CSV path: {csv_path}")
safety_df = pd.read_csv(csv_path)
safety_ds = Dataset.from_pandas(safety_df)
def format_safety(example):
    return {"text": f"Prompt: {example['prompt']}\nResponse: {example['response']}"}
safety_ds = safety_ds.map(format_safety, remove_columns=safety_ds.column_names)

print("Starting FIM computation for Utility...")
fim_utility = compute_fim_diag(model, tokenizer, alpaca, num_samples=50)

print("Starting FIM computation for Safety...")
fim_safety = compute_fim_diag(model, tokenizer, safety_ds, num_samples=50)

# 解析
def flatten_fim(fim_dict):
    return torch.cat([v.flatten() for v in fim_dict.values()])

flat_u = flatten_fim(fim_utility).detach().cpu().numpy()
flat_s = flatten_fim(fim_safety).detach().cpu().numpy()

# スピアマン順位相関
spearman_corr, _ = stats.spearmanr(flat_u, flat_s)
print(f"Spearman Correlation between Utility FIM and Safety FIM: {spearman_corr:.4f}")

# Top-K Overlap (Jaccard)
def get_top_indices(scores, k_percent):
    n = len(scores)
    k = int(n * (k_percent / 100.0))
    return set(np.argsort(scores)[-k:])

top_u = get_top_indices(flat_u, 10) # Top 10%
top_s = get_top_indices(flat_s, 10) # Top 10%

intersection = len(top_u.intersection(top_s))
union = len(top_u.union(top_s))
jaccard = intersection / union

print(f"Jaccard Similarity for Top 10% parameters: {jaccard:.4f}")
print(f"Overlap count: {intersection} / {len(top_u)}")

# 結果保存
results = {
    "spearman_correlation": float(spearman_corr),
    "jaccard_top_10v10": float(jaccard),
    "overlap_count": int(intersection),
    "total_top_k": len(top_u)
}

with open("scripts/benchmarks/fim_overlap_results.json", "w") as f:
    json.dump(results, f, indent=4)
