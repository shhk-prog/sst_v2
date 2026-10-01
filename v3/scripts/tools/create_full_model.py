# scripts/tools/create_full_model.py

import argparse
import gc
import os
import shutil

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def clear_cuda():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base_model",
        type=str,
        default="meta-llama/Llama-2-7b-hf",
    )
    parser.add_argument(
        "--adapter_dir",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load tokenizer
    # ------------------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        use_fast=False,
    )

    # Llama-2 baseにはPADが存在しないため追加
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({"pad_token": "[PAD]"})

    print(f"Tokenizer vocab size : {len(tokenizer)}")
    print(f"PAD token            : {tokenizer.pad_token}")
    print(f"PAD token id         : {tokenizer.pad_token_id}")

    # ------------------------------------------------------------------
    # Load base model
    # ------------------------------------------------------------------
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # tokenizerに合わせてEmbeddingを拡張
    if base_model.get_input_embeddings().weight.shape[0] != len(tokenizer):
        print(
            f"Resizing base model vocab: "
            f"{base_model.get_input_embeddings().weight.shape[0]} "
            f"-> {len(tokenizer)}"
        )
        base_model.resize_token_embeddings(len(tokenizer))

    base_model.config.vocab_size = len(tokenizer)
    base_model.config.pad_token_id = tokenizer.pad_token_id

    if hasattr(base_model, "generation_config"):
        base_model.generation_config.pad_token_id = tokenizer.pad_token_id

    # ------------------------------------------------------------------
    # Merge LoRA
    # ------------------------------------------------------------------
    model = PeftModel.from_pretrained(
        base_model,
        args.adapter_dir,
    )

    model = model.merge_and_unload()

    # merge後も念のため確認
    if model.get_input_embeddings().weight.shape[0] != len(tokenizer):
        print(
            f"Resizing merged model vocab: "
            f"{model.get_input_embeddings().weight.shape[0]} "
            f"-> {len(tokenizer)}"
        )
        model.resize_token_embeddings(len(tokenizer))

    model.config.vocab_size = len(tokenizer)
    model.config.pad_token_id = tokenizer.pad_token_id

    if hasattr(model, "generation_config"):
        model.generation_config.pad_token_id = tokenizer.pad_token_id

    print("\nFinal model information")
    print("-----------------------")
    print(f"Tokenizer vocab : {len(tokenizer)}")
    print(f"Config vocab    : {model.config.vocab_size}")
    print(f"Embedding shape : {model.get_input_embeddings().weight.shape}")
    print(f"LM head shape   : {model.lm_head.weight.shape}")
    print(f"PAD token id    : {tokenizer.pad_token_id}")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)

    os.makedirs(args.output_dir, exist_ok=True)

    model.save_pretrained(
        args.output_dir,
        safe_serialization=True,
    )
    tokenizer.save_pretrained(args.output_dir)

    del model
    del base_model
    clear_cuda()

    print(f"\nSaved full model to: {args.output_dir}")


if __name__ == "__main__":
    main()
