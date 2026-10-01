"""
Command Line Interface for Merging Models in v4
Loads base/domain/safety models, merges weights via requested merger, and saves the resulting model.
"""

import os
import sys
import json
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mergers import get_merger


def load_state_dict_or_model(model_name_or_path: str, base_model_path: str = None):
    print(f"Loading weights from {model_name_or_path}...")
    adapter_cfg = os.path.join(model_name_or_path, "adapter_config.json")
    if os.path.exists(adapter_cfg):
        if not base_model_path:
            raise ValueError(f"Base model required to load PEFT adapter {model_name_or_path}")
        print(f"  Detected PEFT LoRA adapter. Merging into base model {base_model_path}...")
        base = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            low_cpu_mem_usage=True,
        )
        peft_model = PeftModel.from_pretrained(base, model_name_or_path)
        merged = peft_model.merge_and_unload()
        return merged.state_dict()
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            low_cpu_mem_usage=True,
        )
        return model.state_dict()


def run_merge(
    method: str,
    output_dir: str,
    utility_model_path: str,
    safety_model_path: str,
    base_model_path: str = "meta-llama/Llama-2-7b-hf",
    method_kwargs_json: str = "{}",
):
    os.makedirs(output_dir, exist_ok=True)
    kwargs = json.loads(method_kwargs_json)

    print("=" * 60)
    print(f"Starting Model Merge: {method}")
    print(f"  Utility Model: {utility_model_path}")
    print(f"  Safety Model:  {safety_model_path}")
    print(f"  Base Model:    {base_model_path}")
    print(f"  Parameters:    {kwargs}")
    print(f"  Output Dir:    {output_dir}")
    print("=" * 60)

    merger = get_merger(method, **kwargs)

    # Load state dicts
    dict_u = load_state_dict_or_model(utility_model_path, base_model_path)
    dict_s = load_state_dict_or_model(safety_model_path, base_model_path)
    dict_0 = load_state_dict_or_model(base_model_path) if base_model_path else None

    print("\nMerging state dict tensors...")
    merged_dict = merger.merge_state_dicts(dict_u, dict_s, dict_0)

    # Load base model structure to receive state dict
    print("\nInstantiating skeleton model to save merged weights...")
    ref_model_path = utility_model_path if not os.path.exists(os.path.join(utility_model_path, "adapter_config.json")) else base_model_path
    save_model = AutoModelForCausalLM.from_pretrained(
        ref_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True,
    )
    save_model.load_state_dict(merged_dict)
    save_model.save_pretrained(output_dir)

    # Save tokenizer
    tokenizer = AutoTokenizer.from_pretrained(ref_model_path)
    tokenizer.save_pretrained(output_dir)

    manifest = {
        "method": method,
        "parameters": kwargs,
        "utility_model": utility_model_path,
        "safety_model": safety_model_path,
        "base_model": base_model_path,
    }
    with open(os.path.join(output_dir, "merge_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\nMerge successfully completed and saved.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure Merge CLI with Audit Gate Protection")
    parser.add_argument("--method", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--utility_model", type=str, required=True)
    parser.add_argument("--safety_model", type=str, required=True)
    parser.add_argument("--base_model", type=str, default="meta-llama/Llama-2-7b-hf")
    parser.add_argument("--method_kwargs", type=str, default="{}")
    parser.add_argument("--track", type=str, default="primary", choices=["primary", "diagnostic"],
                        help="Execution track: 'primary' requires valid E0 audit gate pass")
    parser.add_argument("--e0_manifest", type=str, default="v4/results/e0_audit/model_manifest.json",
                        help="Path to E0 audit manifest")
    args = parser.parse_args()

    # R2-04: Prevent merger CLI bypass in primary track
    if args.track == "primary":
        if not os.path.exists(args.e0_manifest):
            print(f"[FATAL AUDIT GATE ERROR] E0 manifest not found at: {args.e0_manifest}")
            print("Primary model merging cannot proceed without verified E0 audit trail.")
            sys.exit(1)
        try:
            with open(args.e0_manifest, "r", encoding="utf-8") as f:
                man = json.load(f)
            primary_verdict = man.get("primary_experiment_verdict")
            if primary_verdict != "GO":
                print(f"[FATAL AUDIT GATE ERROR] E0 audit manifest verdict is '{primary_verdict}'.")
                print("Primary model merging is BLOCKED. (Run with --track diagnostic for exploratory merges).")
                sys.exit(1)
        except Exception as e:
            print(f"[FATAL AUDIT GATE ERROR] Failed to parse E0 manifest: {e}")
            sys.exit(1)

    run_merge(
        method=args.method,
        output_dir=args.output_dir,
        utility_model_path=args.utility_model,
        safety_model_path=args.safety_model,
        base_model_path=args.base_model,
        method_kwargs_json=args.method_kwargs,
    )
