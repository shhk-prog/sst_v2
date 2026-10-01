import os
import json
import glob
import numpy as np
from collections import defaultdict

BASE_DIR = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged"
SEEDS = ["seed42", "seed43", "seed44"]
DOMAINS = ["safety+math", "safety+code", "safety+medical"]
METHODS = [
    "diagonal_sst_main", "data_free_sst_main", "ties", "dare", "della",
    "task_arithmetic", "matena_fisher", "mergealign", "safemerge", "led_merging"
]

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None

def calc_metrics(safety_files, gsm8k_file, humaneval_file):
    # Safety metrics
    asr_list = []
    valid_responses = 0
    total_responses = 0
    valid_harmful = 0
    
    for f in safety_files:
        data = load_json(f)
        if not data: continue
        asr_list.append(data.get("asr", 0.0))
        for res in data.get("results", []):
            total_responses += 1
            if not res.get("is_gibberish", False):
                valid_responses += 1
                if res.get("original_asr", 0.0) > 0:
                    valid_harmful += 1
                    
    avg_asr = np.mean(asr_list) if asr_list else 0.0
    valid_resp_rate = valid_responses / total_responses if total_responses > 0 else 0.0
    filtered_asr = valid_harmful / valid_responses if valid_responses > 0 else 0.0
    valid_safety_rate = valid_resp_rate * (1 - filtered_asr)

    # Utility metrics
    gsm8k_score = 0.0
    if gsm8k_file:
        data = load_json(gsm8k_file)
        if data and "results" in data and "gsm8k" in data["results"]:
            gsm8k_score = data["results"]["gsm8k"].get("exact_match", 0.0)
            
    humaneval_score = 0.0
    if humaneval_file:
        data = load_json(humaneval_file)
        if data and "results" in data and "humaneval" in data["results"]:
            humaneval_score = data["results"]["humaneval"].get("pass@1", 0.0)
            
    return {
        "harmful_asr": avg_asr,
        "valid_resp_rate": valid_resp_rate,
        "valid_safety_rate": valid_safety_rate,
        "gsm8k": gsm8k_score,
        "humaneval": humaneval_score
    }

if __name__ == "__main__":
    print("| Pattern | Method | Harmful ASR ↓ | XSTest過剰拒否 ↓ | Valid response rate ↑ | Valid Safety Rate ↑ | GSM8K ↑ | HumanEval ↑ |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")

    for domain in DOMAINS:
        for method in METHODS:
            metrics_per_seed = defaultdict(list)
            for seed in SEEDS:
                method_dir = os.path.join(BASE_DIR, seed, domain, method)
                if not os.path.exists(method_dir): continue
                
                files = glob.glob(os.path.join(method_dir, f"*_seed*.json"))
                if not files: continue
                
                # Use alpha0.6 as standard if exists, else first available
                target_files = [f for f in files if "alpha0.6" in f]
                if not target_files:
                    target_files = files
                
                # Group by base name without seed to ensure we don't mix alphas if multiple exist
                safety_files = [f for f in target_files if "harmbench" in f or "jailbreakbench" in f or "strongreject" in f or "wildjailbreak" in f]
                gsm8k_file = next((f for f in target_files if "gsm8k" in f), None)
                humaneval_file = next((f for f in target_files if "humaneval" in f), None)
                
                res = calc_metrics(safety_files, gsm8k_file, humaneval_file)
                for k, v in res.items():
                    metrics_per_seed[k].append(v)
                    
            if metrics_per_seed["harmful_asr"]:
                def fmt(k):
                    arr = [v * 100 for v in metrics_per_seed[k]]
                    if len(arr) > 1:
                        return f"{np.mean(arr):.2f} ± {np.std(arr):.2f}"
                    else:
                        return f"{np.mean(arr):.2f}"
                
                row = f"| {domain} | {method} | {fmt('harmful_asr')} | N/A | {fmt('valid_resp_rate')} | {fmt('valid_safety_rate')} | {fmt('gsm8k')} | {fmt('humaneval')} |"
                print(row)
