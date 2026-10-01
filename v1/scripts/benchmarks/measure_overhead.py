import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import get_peft_model, LoraConfig, TaskType
import numpy as np
import os

# GPU設定
os.environ["CUDA_VISIBLE_DEVICES"] = "2"
device = "cuda" if torch.cuda.is_available() else "cpu"

model_id = "meta-llama/Llama-2-7b-hf" # 軽量版でベンチマーク
tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# LoRA設定
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16,
    device_map={"":0} # Use GPU 2 (mapped to local :0)
)
model = get_peft_model(model, lora_config)
model.train()

# ダミーデータ作成
batch_size = 4
seq_len = 128
dummy_input = torch.randint(0, 32000, (batch_size, seq_len)).to(device)
labels = dummy_input.clone()

# --- Benchmarking SFT Step ---
def benchmark_sft(num_steps=20):
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    torch.cuda.synchronize()
    start_time = time.time()
    for _ in range(num_steps):
        optimizer.zero_grad()
        outputs = model(dummy_input, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
    torch.cuda.synchronize()
    end_time = time.time()
    return (end_time - start_time) / num_steps

# --- Benchmarking FIM Step ---
def benchmark_fim(num_steps=20):
    torch.cuda.synchronize()
    start_time = time.time()
    for _ in range(num_steps):
        model.zero_grad()
        outputs = model(dummy_input, labels=labels)
        loss = outputs.loss
        loss.backward()
        
        # FIM: 勾配の2乗を取得 (SST-Mergeの内部処理を模擬)
        for name, param in model.named_parameters():
            if param.requires_grad and param.grad is not None:
                _ = param.grad.data.pow(2)
                
    torch.cuda.synchronize()
    end_time = time.time()
    return (end_time - start_time) / num_steps

print("Starting Benchmarks...")
sft_time = benchmark_sft()
print(f"SFT Step Time: {sft_time:.4f}s")

fim_time = benchmark_fim()
print(f"FIM Step Time: {fim_time:.4f}s")

# 結果を保存
results = {
    "sft_step_avg": sft_time,
    "fim_step_avg": fim_time,
    "overhead_ratio": fim_time / sft_time
}

import json
with open("scripts/benchmarks/benchmark_results.json", "w") as f:
    json.dump(results, f, indent=4)

print(f"Comparison: FIM is {results['overhead_ratio']:.2f}x of an SFT step.")
