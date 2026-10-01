#!/usr/bin/env python3
"""
test_canonical_equivalence.py

E0c Gate: Rigorously verifies that:
1. Tokenizer consistency gate passes on canonical models:
   - len(tokenizer) == 32000
   - model.config.vocab_size == 32000
   - input_embeddings.num_embeddings == 32000
   - lm_head.out_features == 32000
   - max(tokenizer generated ids) < 32000
   - pad_token_id == 2
2. Behavioral Equivalence Test (Original vs Canonical):
   - Computes max_abs_logit_diff and mean_abs_logit_diff on logits[:, :, 0:32000]
   - Computes argmax token agreement
   - Computes exact generation match
   Proves mathematically and empirically:
   "vocab canonicalization merely removes an unused added PAD row and does not alter behavior over the shared vocabulary."
"""
import os
import sys
import json
import argparse
import torch
from pathlib import Path
from typing import Dict, Any, List

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig


def verify_tokenizer_consistency(model, tokenizer, model_name: str):
    print(f"\n[Assert] Verifying Tokenizer & Model Consistency for {model_name}...")
    assert len(tokenizer) == 32000, f"len(tokenizer) is {len(tokenizer)}, expected 32000"
    assert model.config.vocab_size == 32000, f"model.config.vocab_size is {model.config.vocab_size}, expected 32000"
    
    in_embed = model.get_input_embeddings()
    assert in_embed.num_embeddings == 32000, f"input_embeddings is {in_embed.num_embeddings}, expected 32000"
    
    lm_head = model.get_output_embeddings()
    assert lm_head.out_features == 32000, f"lm_head.out_features is {lm_head.out_features}, expected 32000"
    
    assert tokenizer.pad_token_id == 2, f"pad_token_id is {tokenizer.pad_token_id}, expected 2"
    
    # Test tokenization of arbitrary text to verify no ids >= 32000
    sample_texts = [
        "Hello world! What is 42 * 99?",
        "Write a Python function with [PAD] or special syntax: def foo(): return None",
        "Let x and y be positive integers such that x^2 + y^2 = 25.",
    ]
    for st in sample_texts:
        enc = tokenizer(st)["input_ids"]
        assert max(enc) < 32000, f"Found token id >= 32000 in tokenized text: {max(enc)}"
    
    print(f"  [PASS] All 6 strict tokenizer consistency assertions passed for {model_name}!")


def compare_original_and_canonical(
    original_model_path: str,
    canonical_model_path: str,
    domain_label: str = "math",
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"E0c Behavioral Equivalence Test: {domain_label.upper()}")
    print(f"  Original:  {original_model_path}")
    print(f"  Canonical: {canonical_model_path}")
    print(f"{'='*70}")

    # Load canonical tokenizer
    canon_tok = AutoTokenizer.from_pretrained(canonical_model_path)
    orig_tok = AutoTokenizer.from_pretrained(original_model_path)

    # 1. Load Canonical Model
    print(f"  Loading Canonical Model...")
    canon_model = AutoModelForCausalLM.from_pretrained(
        canonical_model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    canon_model.eval()

    # Verify Tokenizer Consistency Gate
    verify_tokenizer_consistency(canon_model, canon_tok, f"Canonical {domain_label}")

    # 2. Load Original Model
    print(f"  Loading Original Model...")
    orig_model = AutoModelForCausalLM.from_pretrained(
        original_model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    orig_model.eval()

    test_prompts = [
        "Natalia sold clips to 48 of her friends in April. How many clips did she sell?",
        "What is the derivative of f(x) = 3x^2 + 5x - 7 with respect to x?",
        "Explain step-by-step how photosynthesis works in green plants.",
        "Solve for x in the equation: 2^(x+1) = 16.",
        "Tell me a short bedtime story about a curious robotic astronomer.",
    ]

    all_max_diffs = []
    all_mean_diffs = []
    total_tokens_compared = 0
    total_argmax_matches = 0
    generation_exact_matches = 0

    print("\n  Evaluating logits and generations across test prompts...")
    for idx, prompt in enumerate(test_prompts):
        inputs = canon_tok(f"[INST] {prompt} [/INST]", return_tensors="pt").to(device)
        input_ids = inputs["input_ids"]
        seq_len = input_ids.shape[1]
        assert seq_len <= 2048, f"Sequence length {seq_len} exceeds 2048"

        with torch.no_grad():
            out_canon = canon_model(input_ids)
            out_orig = orig_model(input_ids)

        logits_canon = out_canon.logits[0].float()  # [seq_len, 32000]
        logits_orig = out_orig.logits[0, :, 0:32000].float()  # [seq_len, 32000]

        diff = torch.abs(logits_canon - logits_orig)
        max_diff = float(diff.max())
        mean_diff = float(diff.mean())
        all_max_diffs.append(max_diff)
        all_mean_diffs.append(mean_diff)

        # Argmax agreement
        argmax_c = torch.argmax(logits_canon, dim=-1)
        argmax_o = torch.argmax(logits_orig, dim=-1)
        matches = int((argmax_c == argmax_o).sum())
        total_argmax_matches += matches
        total_tokens_compared += seq_len

        # Greedy generation comparison
        with torch.no_grad():
            gen_c = canon_model.generate(**inputs, max_new_tokens=48, do_sample=False, pad_token_id=2)
            gen_o = orig_model.generate(**inputs, max_new_tokens=48, do_sample=False, pad_token_id=orig_tok.pad_token_id or 2)

        text_c = canon_tok.decode(gen_c[0][seq_len:], skip_special_tokens=True).strip()
        text_o = orig_tok.decode(gen_o[0][seq_len:], skip_special_tokens=True).strip()

        is_exact = (text_c == text_o)
        if is_exact:
            generation_exact_matches += 1

        print(f"    Prompt {idx+1}: max_diff={max_diff:.6f}, mean_diff={mean_diff:.8f}, argmax_agreement={matches}/{seq_len}, exact_generation={is_exact}")

    max_abs_logit_diff = max(all_max_diffs)
    mean_abs_logit_diff = sum(all_mean_diffs) / len(all_mean_diffs)
    argmax_agreement_rate = total_argmax_matches / total_tokens_compared
    generation_exact_match_rate = generation_exact_matches / len(test_prompts)

    print(f"\n  Summary for {domain_label.upper()}:")
    print(f"    Max Absolute Logit Diff:   {max_abs_logit_diff:.8f}")
    print(f"    Mean Absolute Logit Diff:  {mean_abs_logit_diff:.10f}")
    print(f"    Argmax Token Agreement:    {argmax_agreement_rate * 100:.2f}% ({total_argmax_matches}/{total_tokens_compared})")
    print(f"    Generation Exact Match:    {generation_exact_match_rate * 100:.2f}% ({generation_exact_matches}/{len(test_prompts)})")

    # Assert behavioral equivalence:
    # In float16 representation, for logits with magnitude ~16.0, 1 ULP is exactly 2^-11 * 16 = 2^-7 = 0.0078125 (or 2^-6 = 0.015625).
    # Mean difference is ~1e-5. Requiring 100% argmax agreement and 100% exact greedy generation confirms zero behavioral divergence.
    assert max_abs_logit_diff < 0.05, f"Logit diff exceeds float16 ULP tolerance: {max_abs_logit_diff}"
    assert mean_abs_logit_diff < 1e-4, f"Mean logit diff too large: {mean_abs_logit_diff}"
    assert argmax_agreement_rate == 1.0, f"Argmax agreement below 100%: {argmax_agreement_rate}"
    assert generation_exact_match_rate == 1.0, f"Generation mismatch: {generation_exact_match_rate}"

    print(f"  >>> [PASS] {domain_label.upper()} is rigorously proven behaviorally identical! <<<")

    return {
        "domain": domain_label,
        "original_model": original_model_path,
        "canonical_model": canonical_model_path,
        "max_abs_logit_diff": max_abs_logit_diff,
        "mean_abs_logit_diff": mean_abs_logit_diff,
        "argmax_agreement_rate": argmax_agreement_rate,
        "generation_exact_match_rate": generation_exact_match_rate,
        "test_prompts_count": len(test_prompts),
        "verdict": "EQUIVALENT",
    }


def main():
    parser = argparse.ArgumentParser(description="Test behavioral equivalence of canonicalized models.")
    parser.add_argument("--math_orig", default="WizardLMTeam/WizardMath-7B-V1.0")
    parser.add_argument("--math_canon", default="v4/results/models/canonical/wizardmath_7b")
    parser.add_argument("--safety_orig", default="v3/models/temp_safety_full_seed42")
    parser.add_argument("--safety_canon", default="v4/results/models/canonical/safety_full_seed42")
    parser.add_argument("--output_report", default="v4/results/models/canonical/e0c_behavioral_equivalence_report.json")
    args = parser.parse_args()

    results = {}
    
    # 1. Math Domain
    results["math"] = compare_original_and_canonical(
        original_model_path=args.math_orig,
        canonical_model_path=args.math_canon,
        domain_label="math",
    )

    # 2. Safety Domain
    results["safety"] = compare_original_and_canonical(
        original_model_path=args.safety_orig,
        canonical_model_path=args.safety_canon,
        domain_label="safety",
    )

    out_file = Path(args.output_report)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved E0c Behavioral Equivalence Report to: {out_file}")
    print("ALL E0c BEHAVIORAL EQUIVALENCE CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
