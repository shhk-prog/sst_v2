import os
import gc
import json
import shutil
import yaml
import torch
import numpy as np
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from mergers.constants import TARGET_MODULE_KEYWORDS


def clear_cuda():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def is_local_path(path_or_id):
    return os.path.exists(str(path_or_id))


def to_model_ref(path_or_id):
    if is_local_path(path_or_id):
        return os.path.abspath(path_or_id)
    return path_or_id


def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_json(path, obj):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def safe_filename_part(x):
    return (
        str(x)
        .replace("/", "_")
        .replace("+", "_")
        .replace(":", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_model_short_name(kind, domain, model_path, config):
    base_model = config["models"]["base_model"]

    if kind == "harmful":
        return "Llama2_SafetyFT"

    if domain == "math":
        return "Llama2_WizardMath"

    if domain == "code":
        return "Llama2_WizardCoder"

    if domain == "medical":
        return "Llama2_MedAlpaca"

    return safe_filename_part(model_path or base_model)


def is_target_weight(name):
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def count_target_parameters(model):
    return int(sum(param.numel() for name, param in model.named_parameters() if is_target_weight(name)))


def get_layer_prior(layer_idx, num_layers, mode="uniform"):
    if num_layers <= 0:
        return 1.0

    x = layer_idx / float(max(num_layers - 1, 1))

    if mode == "uniform":
        return 1.0
    if mode == "sin":
        return 1.0 + 0.5 * np.sin(np.pi * x)
    if mode == "linear":
        return 0.5 + x
    if mode == "reverse_linear":
        return 1.5 - x
    if mode == "exp":
        return float(np.exp(x - 0.5))

    raise ValueError(f"Unknown layer_prior mode: {mode}")


def load_full_model(model_ref, dtype=torch.float16, device_map=None):
    if device_map:
        return AutoModelForCausalLM.from_pretrained(
            model_ref,
            torch_dtype=dtype,
            device_map=device_map,
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return AutoModelForCausalLM.from_pretrained(model_ref, torch_dtype=dtype).to(device)


def build_models_to_merge(config, args):
    domain_models = config["models"]["domain_models"]
    models_to_merge = {}

    if args.pattern == "safety+math":
        models_to_merge["math"] = domain_models["math"]
    elif args.pattern == "safety+code":
        models_to_merge["code"] = domain_models["code"]
    elif args.pattern == "safety+medical":
        models_to_merge["medical"] = domain_models["medical"]
    elif args.pattern == "safety+math+code+medical":
        models_to_merge["math"] = domain_models["math"]
        models_to_merge["code"] = domain_models["code"]
        models_to_merge["medical"] = domain_models["medical"]
    else:
        raise ValueError(f"Unknown merge pattern: {args.pattern}")

    safety_model_path = f"{config['models']['safety_model_dir']}_seed{args.seed}"

    if not os.path.exists(safety_model_path):
        raise FileNotFoundError(f"Safety LoRA not found for seed={args.seed}: {safety_model_path}")

    models_to_merge["safety"] = safety_model_path
    return models_to_merge, safety_model_path


def require_single_utility(args, models_to_merge):
    utility_keys = [k for k in models_to_merge if k != "safety"]

    if len(utility_keys) != 1:
        raise ValueError(f"{args.method} supports only single-domain patterns. Got utilities={utility_keys}")

    return utility_keys[0], models_to_merge[utility_keys[0]]


def temp_safety_full_dir(args):
    return os.path.join("models", f"temp_safety_full_seed{args.seed}")


def temp_util_lora_dir(args, util_key):
    safe_pattern = args.pattern.replace("+", "_")
    return os.path.join("models", f"temp_{util_key}_lora_{safe_pattern}_{args.method}_seed{args.seed}")


def temp_metadata_matches(path, expected):
    meta_path = os.path.join(path, "_temp_metadata.json")

    if not os.path.exists(path) or not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f) == expected
    except Exception:
        return False


def recreate_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def create_full_safety_model(
    base_model_name,
    safety_lora_path,
    output_dir,
    args,
    runtime_logger=None,
    tokenizer_source=None,
):
    expected_meta = {
        "kind": "temp_safety_full",
        "base_model": base_model_name,
        "safety_lora_path": safety_lora_path,
        "seed": args.seed,
    }

    if temp_metadata_matches(output_dir, expected_meta):
        print(f"Using cached temporary safety full model: {output_dir}")
        return output_dir

    if runtime_logger:
        runtime_logger.start("create_full_safety_model")

    print(f"Creating temporary full safety model: {output_dir}")
    recreate_dir(output_dir)

    from peft import PeftModel

    tokenizer_name = tokenizer_source or base_model_name
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=False)

    base_model = load_full_model(base_model_name)

    if base_model.get_input_embeddings().weight.shape[0] != len(tokenizer):
        base_model.resize_token_embeddings(len(tokenizer))

    safe_model = PeftModel.from_pretrained(base_model, safety_lora_path)
    safe_model = safe_model.merge_and_unload()

    if safe_model.get_input_embeddings().weight.shape[0] != len(tokenizer):
        safe_model.resize_token_embeddings(len(tokenizer))

    safe_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    write_json(os.path.join(output_dir, "_temp_metadata.json"), expected_meta)

    del safe_model
    del base_model
    clear_cuda()

    if runtime_logger:
        runtime_logger.end("create_full_safety_model")

    return output_dir


def convert_full_to_lora(base_model_path, full_model_path, output_lora_dir, args, r=16, alpha=32, runtime_logger=None):
    expected_meta = {
        "kind": "svd_pseudo_lora",
        "base_model": base_model_path,
        "full_model": full_model_path,
        "r": r,
        "alpha": alpha,
        "seed": args.seed,
        "note": "SVD pseudo-LoRA converted from full model delta; not an originally trained LoRA adapter.",
    }

    if temp_metadata_matches(output_lora_dir, expected_meta):
        print(f"Using cached temporary utility LoRA: {output_lora_dir}")
        return output_lora_dir

    if runtime_logger:
        runtime_logger.start("convert_full_to_lora_svd")

    print(f"Converting full model {full_model_path} to pseudo-LoRA adapter: {output_lora_dir}")
    recreate_dir(output_lora_dir)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    base_model = AutoModelForCausalLM.from_pretrained(base_model_path, torch_dtype=torch.float16).to(device)
    full_model = AutoModelForCausalLM.from_pretrained(full_model_path, torch_dtype=torch.float16).to(device)

    full_state = full_model.state_dict()
    lora_state_dict = {}

    for name, param_base in tqdm(list(base_model.named_parameters()), desc="SVD LoRA conversion"):
        if not is_target_weight(name) or name not in full_state:
            continue

        param_full = full_state[name].data

        if param_full.shape != param_base.shape:
            continue

        delta_w = (param_full - param_base.data).float()

        try:
            U, S, V = torch.svd_lowrank(delta_w, q=r)
        except Exception:
            U, S, Vh = torch.linalg.svd(delta_w, full_matrices=False)
            U = U[:, :r]
            S = S[:r]
            V = Vh[:r, :].t()

        scale = r / alpha
        lora_A_val = V.t()
        lora_B_val = U @ torch.diag(S) * scale

        base_key = ("base_model.model." + name).replace(".weight", "")
        lora_state_dict[f"{base_key}.lora_A.default.weight"] = lora_A_val.half().cpu()
        lora_state_dict[f"{base_key}.lora_B.default.weight"] = lora_B_val.half().cpu()

    adapter_config = {
        "peft_type": "LORA",
        "auto_mapping": None,
        "base_model_name_or_path": base_model_path,
        "r": r,
        "lora_alpha": alpha,
        "lora_dropout": 0.05,
        "target_modules": TARGET_MODULE_KEYWORDS,
        "modules_to_save": None,
        "bias": "none",
        "fan_in_fan_out": False,
        "task_type": "CAUSAL_LM",
    }

    write_json(os.path.join(output_lora_dir, "adapter_config.json"), adapter_config)
    torch.save(lora_state_dict, os.path.join(output_lora_dir, "adapter_model.bin"))
    write_json(os.path.join(output_lora_dir, "_temp_metadata.json"), expected_meta)

    del base_model
    del full_model
    clear_cuda()

    if runtime_logger:
        runtime_logger.end("convert_full_to_lora_svd")

    print(f"Pseudo-LoRA adapter saved to {output_lora_dir}")
    return output_lora_dir
