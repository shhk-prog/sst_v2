"""
Command Line Interface for Merging Models in v4
Loads base/domain/safety models, merges weights via requested merger, and saves the resulting model.
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mergers import get_merger


def load_state_dict_or_model(model_name_or_path: str, base_model_path: str = None):
    print(f"Loading weights from {model_name_or_path}...")

    # Direct pytorch file path
    if os.path.isfile(model_name_or_path):
        return torch.load(model_name_or_path, map_location="cpu")

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
        # Check if direct state dict file exists in directory without HuggingFace config
        bin_file = os.path.join(model_name_or_path, "pytorch_model.bin")
        cfg_file = os.path.join(model_name_or_path, "config.json")
        if os.path.isfile(bin_file) and not os.path.isfile(cfg_file):
            return torch.load(bin_file, map_location="cpu")

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
    utility_model_path: Optional[str] = None,
    safety_model_path: Optional[str] = None,
    base_model_path: str = "meta-llama/Llama-2-7b-hf",
    method_kwargs_json: str = "{}",
    fim_u_path: Optional[str] = None,
    fim_s_path: Optional[str] = None,
    utility_model: Optional[str] = None,
    safety_model: Optional[str] = None,
    base_model: Optional[str] = None,
    method_kwargs: Optional[Any] = None,
    **kwargs_extra,
):
    u_path = utility_model_path or utility_model
    s_path = safety_model_path or safety_model
    b_path = base_model or base_model_path

    if not u_path or not s_path:
        raise ValueError("Both utility_model and safety_model paths are required for run_merge.")

    os.makedirs(output_dir, exist_ok=True)
    if method_kwargs is not None:
        kwargs = method_kwargs if isinstance(method_kwargs, dict) else json.loads(str(method_kwargs))
    else:
        kwargs = json.loads(method_kwargs_json) if isinstance(method_kwargs_json, str) else method_kwargs_json

    print("=" * 60)
    print(f"Starting Model Merge: {method}")
    print(f"  Utility Model: {u_path}")
    print(f"  Safety Model:  {s_path}")
    print(f"  Base Model:    {b_path}")
    print(f"  Parameters:    {kwargs}")
    print(f"  FIM Utility:   {fim_u_path}")
    print(f"  FIM Safety:    {fim_s_path}")
    print(f"  Output Dir:    {output_dir}")
    print("=" * 60)

    merger = get_merger(method, **kwargs)

    # Load state dicts
    dict_u = load_state_dict_or_model(u_path, b_path)
    dict_s = load_state_dict_or_model(s_path, b_path)
    dict_0 = load_state_dict_or_model(b_path) if b_path else None

    # Load FIM tensors if provided (R3-06)
    fim_u_dict = None
    fim_s_dict = None
    if fim_u_path:
        print(f"Loading utility FIM from {fim_u_path}...")
        fim_u_dict = torch.load(fim_u_path, map_location="cpu")
    if fim_s_path:
        print(f"Loading safety FIM from {fim_s_path}...")
        fim_s_dict = torch.load(fim_s_path, map_location="cpu")

    print("\nMerging state dict tensors...")
    merged_dict = merger.merge_state_dicts(dict_u, dict_s, dict_0, fim_u=fim_u_dict, fim_s=fim_s_dict)

    # Load base model structure to receive state dict
    print("\nInstantiating skeleton model to save merged weights...")
    ref_model_path = b_path if b_path else u_path
    if u_path and os.path.exists(os.path.join(u_path, "config.json")):
        ref_model_path = u_path

    try:
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
    except Exception as e:
        print(f"Warning: Could not save as HF pretrained model ({e}). Saving raw pytorch_model.bin instead.")
        torch.save(merged_dict, os.path.join(output_dir, "pytorch_model.bin"))

    manifest = {
        "method": method,
        "parameters": kwargs,
        "fidelity": getattr(merger, "FIDELITY_STATUS", "STANDARD_IMPLEMENTATION"),
        "utility_model": u_path,
        "safety_model": s_path,
        "base_model": b_path,
        "fim_u": fim_u_path,
        "fim_s": fim_s_path,
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
    parser.add_argument("--fim_u", type=str, default=None, help="Path to utility model FIM tensor file (.pt)")
    parser.add_argument("--fim_s", type=str, default=None, help="Path to safety model FIM tensor file (.pt)")
    args = parser.parse_args()

    # R2-04 & R3-06: Prevent merger CLI bypass in primary track
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

        # R3-06: Primary Fisher merger requires explicit FIM files
        if args.method in ["fisher", "fisher_weighted"]:
            if not args.fim_u or not args.fim_s:
                print("[FATAL AUDIT GATE ERROR] Fisher merger in primary track requires --fim_u and --fim_s.")
                print("Fallback to constant weights without empirical FIM is strictly rejected (P0-07, R3-06).")
                sys.exit(1)

    run_merge(
        method=args.method,
        output_dir=args.output_dir,
        utility_model_path=args.utility_model,
        safety_model_path=args.safety_model,
        base_model_path=args.base_model,
        method_kwargs_json=args.method_kwargs,
        fim_u_path=args.fim_u,
        fim_s_path=args.fim_s,
    )
