import os
import sys
from pathlib import Path
import argparse

# 1. Consolidated Argparse (called early for CUDA_VISIBLE_DEVICES)
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", type=str, default="2", help="GPU IDs to use")
    parser.add_argument("--sweep_samples", action="store_true", help="Sweep across sample sizes")
    return parser.parse_known_args()[0]

args = get_args()
os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

import json
import torch
import random
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.sst_merge import create_utility_dataloader_from_hf

def get_lora_params(model):
    params = []
    for name, param in model.named_parameters():
        if 'lora' in name.lower():
            params.append(param)
    return params

def compute_importance_scores(model, tokenizer, dataloader, num_samples=100):
    model.train()
    total_fim = None
    total_grad_abs = None
    
    count = 0
    print(f"Computing importance scores (FIM & Gradient) with {num_samples} batches...")
    for batch in tqdm(dataloader):
        if count >= num_samples:
            break
            
        if isinstance(batch, dict):
            texts = batch.get('text', batch.get('prompt', []))
        else:
            texts = batch
        
        inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=512).to(model.device)
        model.zero_grad()
        outputs = model(**inputs, labels=inputs['input_ids'])
        loss = outputs.loss

        if loss is None:
            continue
            
        loss.backward()
        
        current_fim = []
        current_grad_abs = []
        for param in get_lora_params(model):
            if param.grad is not None:
                g = param.grad.detach().cpu().flatten()
                current_fim.append(g**2)
                current_grad_abs.append(g.abs())
            else:
                current_fim.append(torch.zeros_like(param).flatten().cpu())
                current_grad_abs.append(torch.zeros_like(param).flatten().cpu())
                
        flat_fim = torch.cat(current_fim)
        flat_grad_abs = torch.cat(current_grad_abs)
        
        if total_fim is None:
            total_fim = flat_fim
            total_grad_abs = flat_grad_abs
        else:
            total_fim += flat_fim
            total_grad_abs += flat_grad_abs
            
        count += 1
        
    model.eval()
    return total_fim / count, total_grad_abs / count

def get_magnitude(model):
    mags = []
    for param in get_lora_params(model):
        mags.append(param.detach().cpu().flatten().abs())
    return torch.cat(mags)

def apply_intervention(model, importance_scores, ratio, method="prune_top"):
    num_params = len(importance_scores)
    num_target = int(num_params * ratio)
    
    if method == "prune_top":
        _, target_indices = torch.topk(importance_scores, num_target, largest=True)
        mask = torch.ones_like(importance_scores)
        mask[target_indices] = 0.0
    elif method == "modify_bottom":
        _, target_indices = torch.topk(importance_scores, num_target, largest=False)
        mask = torch.ones_like(importance_scores) 
    else:
        raise ValueError()
        
    offset = 0
    with torch.no_grad():
        for param in get_lora_params(model):
            param_size = param.numel()
            if method == "prune_top":
                p_mask = mask[offset:offset+param_size].view_as(param).to(param.device)
                param.data.mul_(p_mask)
            elif method == "modify_bottom":
                # For bottom, we will add gaussian noise to them
                mod_mask = torch.zeros_like(importance_scores)
                mod_mask[target_indices] = 1.0
                p_mod_mask = mod_mask[offset:offset+param_size].view_as(param).to(param.device)
                noise = torch.randn_like(param) * 0.1 # 10% noise
                param.data.add_(noise * p_mod_mask)
            offset += param_size

def eval_model(model, tokenizer, dataloader, num_samples=50):
    model.eval()
    total_loss = 0
    count = 0
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            if count >= num_samples:
                break
            
            if isinstance(batch, dict):
                texts = batch.get('text', batch.get('prompt', []))
            else:
                texts = batch
            
            inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=512).to(model.device)
            outputs = model(**inputs, labels=inputs['input_ids'])
            
            if outputs.loss is not None:
                total_loss += outputs.loss.item()
                count += 1
    return total_loss / count if count > 0 else 0

def compute_jaccard_similarity(scores1, scores2, top_k_ratio=0.1):
    num_params = len(scores1)
    k = int(num_params * top_k_ratio)
    
    _, indices1 = torch.topk(scores1, k, largest=True)
    _, indices2 = torch.topk(scores2, k, largest=True)
    
    set1 = set(indices1.cpu().numpy())
    set2 = set(indices2.cpu().numpy())
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0

def analyze_moment_divergence(model, tokenizer, dataloader, num_samples=50):
    model.train()
    all_grads = [] 
    
    print(f"Collecting per-sample gradients for {num_samples} samples...")
    count = 0
    for batch in tqdm(dataloader):
        if count >= num_samples: break
        if isinstance(batch, dict):
            texts = batch.get('text', batch.get('prompt', []))
        else:
            texts = batch
            
        for text in texts: # Single sample at a time
            if count >= num_samples: break
            inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512).to(model.device)
            model.zero_grad()
            outputs = model(**inputs, labels=inputs['input_ids'])
            loss = outputs.loss
            if loss is None: continue
            loss.backward()
            
            sample_grad = []
            for param in get_lora_params(model):
                if param.grad is not None:
                    sample_grad.append(param.grad.detach().cpu().flatten())
                else:
                    sample_grad.append(torch.zeros_like(param).flatten().cpu())
            
            all_grads.append(torch.cat(sample_grad))
            count += 1
            
    grad_matrix = torch.stack(all_grads) 
    fim = (grad_matrix**2).mean(dim=0)
    grad_abs = grad_matrix.abs().mean(dim=0)
    grad_var = grad_matrix.var(dim=0)
    return fim, grad_abs, grad_var

def main():
    MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
    ADAPTER_PATH = str(project_root / "models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4")
    
    print("Loading tokenizer and dataloader...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    dataloader = create_utility_dataloader_from_hf("ServiceNow/repliqa", "repliqa_0", max_samples=300)
    
    print("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.bfloat16, 
        device_map="auto"
    )
    
    print("Loading adapter for scoring...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH, is_trainable=True)
    for param in get_lora_params(model):
        param.requires_grad = True
        
    print("\n=== Experiment B: Theoretical Divergence Analysis (FIM vs Grad-Abs) ===")
    fim, grad, grad_var = analyze_moment_divergence(model, tokenizer, dataloader, num_samples=50)
    mags = get_magnitude(model)
    random_scores = torch.rand_like(fim)
    
    results = {
        "jaccard_similarity": [],
        "moment_comparison": [],
        "stability_sweep": [],
        "prune_top": {"fim": [], "magnitude": [], "gradient": [], "random": []},
        "modify_bottom": {"fim": [], "magnitude": [], "gradient": [], "random": []}
    }
    
    ratios = [0.01, 0.05, 0.1, 0.2]
    for k_ratio in ratios:
        jaccard = compute_jaccard_similarity(fim, grad, top_k_ratio=k_ratio)
        print(f"Jaccard Similarity (FIM vs Grad-Abs) at Top-{k_ratio*100}%: {jaccard:.4f}")
        results["jaccard_similarity"].append({"ratio": k_ratio, "jaccard": jaccard})
        
        jaccard_var = compute_jaccard_similarity(fim, grad_var, top_k_ratio=k_ratio)
        results["moment_comparison"].append({"ratio": k_ratio, "metric": "var", "jaccard": jaccard_var})

    print("Evaluating Baseline...")
    baseline_loss = eval_model(model, tokenizer, dataloader, num_samples=50)
    
    if args.sweep_samples:
        print("\n=== Sample Size Sweep for FIM Stability ===")
        sample_sizes = [1, 5, 10, 50, 100]
        reference_fim = fim
        for sz in sample_sizes:
            curr_fim, _ = compute_importance_scores(model, tokenizer, dataloader, num_samples=sz)
            sim = compute_jaccard_similarity(reference_fim, curr_fim, top_k_ratio=0.1)
            print(f"FIM Stability (Overlap with 100-sample baseline) at {sz} samples: {sim:.4f}")
            results["stability_sweep"].append({"sample_size": sz, "stability": sim})

    del model
    torch.cuda.empty_cache()
    
    scores_dict = {"fim": fim, "magnitude": mags, "gradient": grad, "random": random_scores}
    
    print("\n=== Experiment 1: Prune Top-K (Destruction) ===")
    for ratio in ratios:
        print(f"-- Ratio: {ratio*100}% --")
        for name, scores in scores_dict.items():
            tmp_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            apply_intervention(tmp_model, scores, ratio, method="prune_top")
            loss = eval_model(tmp_model, tokenizer, dataloader, num_samples=50)
            results["prune_top"][name].append({"ratio": ratio, "loss": loss, "delta": loss - baseline_loss})
            print(f"  {name}: Loss={loss:.4f} (Delta={loss-baseline_loss:.4f})")
            del tmp_model
            torch.cuda.empty_cache()

    print("\n=== Experiment 2: Modify Bottom-K (Protection) ===")
    for ratio in ratios:
        print(f"-- Ratio: {ratio*100}% --")
        for name, scores in scores_dict.items():
            tmp_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            apply_intervention(tmp_model, scores, ratio, method="modify_bottom")
            loss = eval_model(tmp_model, tokenizer, dataloader, num_samples=50)
            results["modify_bottom"][name].append({"ratio": ratio, "loss": loss, "delta": loss - baseline_loss})
            print(f"  {name}: Loss={loss:.4f} (Delta={loss-baseline_loss:.4f})")
            del tmp_model
            torch.cuda.empty_cache()

    output_path = project_root / "scripts/fim_validation_ablation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
