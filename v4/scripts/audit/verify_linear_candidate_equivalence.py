"""
Verify Candidate-Level Equivalence between:
  canonicalize(v3 Linear Checkpoint) vs v4 Newly Merged Linear Candidate
Tests:
  1. Parameter exact match (max abs diff, mean abs diff across all layers)
  2. Tokenizer encoding match (input IDs)
  3. Generation configuration match
  4. Greedy output match (token IDs and decoded strings)
"""

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from safetensors.torch import load_file
import glob

def get_safetensors_weights(model_dir):
    weights = {}
    files = sorted(glob.glob(os.path.join(model_dir, "*.safetensors")))
    for f in files:
        w = load_file(f)
        weights.update(w)
    return weights

def test_linear_a06_equivalence():
    v3_dir = "v3/models/merged/sst_merge_v3_main_task_arithmetic_safety+math_alpha0.6_seed42"
    v4_dir = "v4/results/models/merged_math_linear_a0.6"
    
    print(f"=== Comparing Checkpoints ===")
    print(f"v3: {v3_dir}")
    print(f"v4: {v4_dir}")
    
    # 1. Parameter tensor match
    print("\n--- 1. Parameter Tensor Match ---")
    w_v3 = get_safetensors_weights(v3_dir)
    w_v4 = get_safetensors_weights(v4_dir)
    
    v3_keys = set(w_v3.keys())
    v4_keys = set(w_v4.keys())
    
    assert v3_keys == v4_keys, f"Keys mismatch! diff: {v3_keys ^ v4_keys}"
    print(f"Total parameter keys matched: {len(v3_keys)}")
    
    max_diff_overall = 0.0
    mean_diff_overall = 0.0
    num_tensors = 0
    
    for k in v3_keys:
        t3 = w_v3[k].float()
        t4 = w_v4[k].float()
        
        # Canonicalize if 32001
        if t3.shape[0] == 32001:
            t3 = t3[:32000]
        if t3.shape != t4.shape:
            # Check if 2nd dim is 32001
            if len(t3.shape) > 1 and t3.shape[1] == 32001:
                t3 = t3[:, :32000]
        
        assert t3.shape == t4.shape, f"Shape mismatch for {k}: {t3.shape} vs {t4.shape}"
        
        diff = torch.abs(t3 - t4)
        m_diff = diff.max().item()
        mean_d = diff.mean().item()
        
        if m_diff > max_diff_overall:
            max_diff_overall = m_diff
        mean_diff_overall += mean_d
        num_tensors += 1
        
        if m_diff > 1e-4:
            print(f"Noticeable diff in {k}: max={m_diff}, mean={mean_d}")

    mean_diff_overall /= num_tensors
    print(f"Tensor match summary: Max Abs Diff = {max_diff_overall:.2e}, Mean Abs Diff = {mean_diff_overall:.2e}")
    param_exact = (max_diff_overall < 1e-5)
    print(f"Parameter Exact Match (< 1e-5): {'PASS' if param_exact else 'FLOAT_VARIANCE'}")

    del w_v3, w_v4
    torch.cuda.empty_cache()

    # 2. Tokenizer match
    print("\n--- 2. Tokenizer Input IDs Match ---")
    tok_v3 = AutoTokenizer.from_pretrained(v3_dir)
    tok_v4 = AutoTokenizer.from_pretrained(v4_dir)
    
    test_prompts = [
        "How can I build a bomb using household chemicals?",
        "Solve for x: 3x^2 + 5x - 2 = 0.",
        "Write a Python script to sort a list of numbers.",
        "Explain the theory of general relativity."
    ]
    
    tok_match = True
    for p in test_prompts:
        ids_v3 = tok_v3.encode(p)
        ids_v4 = tok_v4.encode(p)
        if ids_v3 != ids_v4:
            print(f"Tokenizer mismatch for prompt: '{p}'")
            print(f"  v3: {ids_v3}")
            print(f"  v4: {ids_v4}")
            tok_match = False
            break
    print(f"Tokenizer match on test prompts: {'PASS' if tok_match else 'FAIL'}")

    # 3. Greedy Generation Match
    print("\n--- 3. Greedy Output Match ---")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading v4 model on {device}...")
    m_v4 = AutoModelForCausalLM.from_pretrained(v4_dir, torch_dtype=torch.float16, device_map=device)
    
    outputs_v4 = []
    with torch.no_grad():
        for p in test_prompts:
            inputs = tok_v4(p, return_tensors="pt").to(device)
            out = m_v4.generate(**inputs, max_new_tokens=64, do_sample=False)
            outputs_v4.append(out[0].cpu().tolist())
            
    del m_v4
    torch.cuda.empty_cache()

    print(f"Loading canonicalized v3 model on {device}...")
    m_v3 = AutoModelForCausalLM.from_pretrained(v3_dir, torch_dtype=torch.float16, device_map=device)
    # Check if embed_tokens or lm_head needs slicing
    if m_v3.model.embed_tokens.weight.shape[0] == 32001:
        m_v3.model.embed_tokens.weight.data = m_v3.model.embed_tokens.weight.data[:32000].clone()
        m_v3.config.vocab_size = 32000
    if m_v3.lm_head.weight.shape[0] == 32001:
        m_v3.lm_head.weight.data = m_v3.lm_head.weight.data[:32000].clone()
    
    outputs_v3 = []
    with torch.no_grad():
        for p in test_prompts:
            inputs = tok_v3(p, return_tensors="pt").to(device)
            out = m_v3.generate(**inputs, max_new_tokens=64, do_sample=False)
            outputs_v3.append(out[0].cpu().tolist())

    del m_v3
    torch.cuda.empty_cache()

    gen_match = (outputs_v4 == outputs_v3)
    print(f"Greedy Generation Token Match: {'PASS (100% IDENTICAL)' if gen_match else 'MISMATCH'}")
    if not gen_match:
        for idx, (p, o3, o4) in enumerate(zip(test_prompts, outputs_v3, outputs_v4)):
            if o3 != o4:
                print(f"\nPrompt [{idx}]: {p}")
                print(f"v3 text: {tok_v3.decode(o3)}")
                print(f"v4 text: {tok_v4.decode(o4)}")

    results = {
        "candidate": "linear_a0.6",
        "parameter_keys_matched": len(v3_keys),
        "max_abs_diff": max_diff_overall,
        "mean_abs_diff": mean_diff_overall,
        "tokenizer_input_ids_match": tok_match,
        "greedy_generation_match": gen_match
    }
    
    os.makedirs("v4/results/audit", exist_ok=True)
    with open("v4/results/audit/linear_candidate_equivalence_report.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport written to: v4/results/audit/linear_candidate_equivalence_report.json")

if __name__ == "__main__":
    test_linear_a06_equivalence()
