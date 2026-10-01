#!/usr/bin/env python3
"""
canonicalize_vocab.py

Rigorously canonicalizes vocabulary from 32001 to 32000 by slicing out the added [PAD] token (index 32000)
from embedding and lm_head tensors, establishing a clean, unified weight-space merge foundation.

Produces:
- Canonicalized weights (safetensors)
- Updated config.json (vocab_size=32000, pad_token_id=2)
- canonicalization_manifest.json recording before/after shapes, dropped parameters, and tokenizer hash
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import torch
from pathlib import Path
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM


def compute_tokenizer_hash(tok, n_tokens=32000) -> str:
    tokens = [tok.convert_ids_to_tokens(i) for i in range(n_tokens)]
    return hashlib.sha256(repr(tokens).encode("utf-8")).hexdigest()


def canonicalize_model(
    model_name_or_path: str,
    output_dir: str,
    domain: str = "math",
    max_eval_length: int = 2048,
    target_vocab_size: int = 32000,
):
    print(f"=== Canonicalizing {domain} model: {model_name_or_path} ===")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Inspect Tokenizer
    tok = AutoTokenizer.from_pretrained(model_name_or_path)
    tok_hash = compute_tokenizer_hash(tok, target_vocab_size)
    print(f"  Tokenizer mapping hash (0..{target_vocab_size-1}): {tok_hash}")

    # Verify token at target_vocab_size
    dropped_token = None
    dropped_token_id = target_vocab_size
    if len(tok) > target_vocab_size:
        dropped_token = tok.convert_ids_to_tokens(target_vocab_size)
        print(f"  Dropping token index {dropped_token_id}: '{dropped_token}'")

    # 2. Load Config
    cfg = AutoConfig.from_pretrained(model_name_or_path)
    orig_vocab_size = getattr(cfg, "vocab_size", 32001)
    orig_pad_token_id = getattr(cfg, "pad_token_id", None)
    rope_theta = 10000.0
    if hasattr(cfg, "rope_scaling") and isinstance(cfg.rope_scaling, dict):
        rope_theta = float(cfg.rope_scaling.get("rope_theta", 10000.0))
    elif hasattr(cfg, "rope_theta") and cfg.rope_theta is not None:
        rope_theta = float(cfg.rope_theta)

    # 3. Load Model Weights (low CPU memory / state_dict)
    print("  Loading state_dict...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    sd = model.state_dict()

    param_count_before = sum(p.numel() for p in sd.values())
    tensor_count = len(sd)

    # 4. Canonicalize embedding and lm_head
    embed_key = "model.embed_tokens.weight"
    lm_head_key = "lm_head.weight"

    embed_shape_before = list(sd[embed_key].shape)
    lm_head_shape_before = list(sd[lm_head_key].shape)

    dropped_params = 0
    if sd[embed_key].shape[0] > target_vocab_size:
        dropped_params += (sd[embed_key].shape[0] - target_vocab_size) * sd[embed_key].shape[1]
        sd[embed_key] = sd[embed_key][:target_vocab_size, :].contiguous()

    if sd[lm_head_key].shape[0] > target_vocab_size:
        dropped_params += (sd[lm_head_key].shape[0] - target_vocab_size) * sd[lm_head_key].shape[1]
        sd[lm_head_key] = sd[lm_head_key][:target_vocab_size, :].contiguous()

    embed_shape_after = list(sd[embed_key].shape)
    lm_head_shape_after = list(sd[lm_head_key].shape)
    param_count_after = sum(p.numel() for p in sd.values())

    print(f"  Embedding shape: {embed_shape_before} -> {embed_shape_after}")
    print(f"  LM-Head shape:   {lm_head_shape_before} -> {lm_head_shape_after}")
    print(f"  Parameters:      {param_count_before:,} -> {param_count_after:,} (dropped: {dropped_params:,})")

    # 5. Update Config on model
    model.config.vocab_size = target_vocab_size
    model.config.pad_token_id = 2  # standard eos_token_id as pad
    cfg.vocab_size = target_vocab_size
    cfg.pad_token_id = 2

    # 6. Save model & tokenizer & config
    print(f"  Saving canonicalized checkpoint to {out_path}...")
    model.save_pretrained(
        out_path,
        state_dict=sd,
        safe_serialization=True,
    )
    # Explicitly ensure config.json reflects vocab_size = 32000
    cfg_save_path = out_path / "config.json"
    cfg.save_pretrained(out_path)
    # Save tokenizer with pad_token_id = 2
    tok.save_pretrained(out_path)
    # Update tokenizer_config.json if exists
    tok_cfg_path = out_path / "tokenizer_config.json"
    if tok_cfg_path.exists():
        with open(tok_cfg_path, "r", encoding="utf-8") as f:
            tcfg = json.load(f)
        tcfg["pad_token"] = "</s>"
        with open(tok_cfg_path, "w", encoding="utf-8") as f:
            json.dump(tcfg, f, indent=2)

    # 7. Write Canonicalization Manifest
    manifest = {
        "domain": domain,
        "source_model": model_name_or_path,
        "canonicalization": {
            "vocab_size": target_vocab_size,
            "dropped_token_id": dropped_token_id,
            "dropped_token": dropped_token,
            "pad_token_id_after": 2,
            "pad_token_after": "</s>",
            "max_eval_length": max_eval_length,
            "rope_theta": rope_theta,
        },
        "metrics": {
            "tensor_count": tensor_count,
            "parameter_count_before": param_count_before,
            "parameter_count_after": param_count_after,
            "dropped_parameter_count": dropped_params,
            "tokenizer_mapping_hash_0_to_31999": tok_hash,
            "embedding_shape_before": embed_shape_before,
            "embedding_shape_after": embed_shape_after,
            "lm_head_shape_before": lm_head_shape_before,
            "lm_head_shape_after": lm_head_shape_after,
        },
    }

    manifest_path = out_path / "canonicalization_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote manifest to {manifest_path}")
    print("=== Canonicalization completed successfully! ===")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Canonicalize vocabulary to 32000.")
    parser.add_argument("--model", type=str, required=True, help="Path or HuggingFace ID of model")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save canonicalized model")
    parser.add_argument("--domain", type=str, default="math", help="Domain label (math/safety)")
    parser.add_argument("--max_eval_length", type=int, default=2048, help="Bounded sequence length")
    args = parser.parse_args()

    canonicalize_model(
        model_name_or_path=args.model,
        output_dir=args.output_dir,
        domain=args.domain,
        max_eval_length=args.max_eval_length,
    )


if __name__ == "__main__":
    main()
