import os
import json
import yaml
import argparse
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM
from peft import PeftModel


TARGET_MODULE_KEYWORDS = [
    "q_proj",
    "v_proj",
    "k_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="cache/datafree_importance")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_target_weight(name):
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_full_model(model_path, device):
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
    ).to(device)
    model.eval()
    return model


def load_safety_model(base_model_name, safety_lora_path, device):
    base = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
    ).to(device)

    model = PeftModel.from_pretrained(base, safety_lora_path)
    model = model.merge_and_unload()
    model.eval()
    return model


def compute_delta_squared_importance(base_model, target_model):
    """
    data-free FIM近似:
        importance_i = (theta_target_i - theta_base_i)^2

    FIMそのものではなく、重み差分に基づく diagonal importance。
    """
    importance = {}
    target_state = target_model.state_dict()

    with torch.no_grad():
        for name, base_param in base_model.named_parameters():
            if not is_target_weight(name):
                continue

            if name not in target_state:
                continue

            target_param = target_state[name].to(
                device=base_param.device,
                dtype=base_param.dtype,
            )

            if target_param.shape != base_param.shape:
                continue

            delta = target_param - base_param
            importance[name] = delta.detach().float().cpu().pow(2)

    return importance


def build_output_name(kind, domain, model_short, seed):
    return f"datafree_{kind}_{domain}_{model_short}_seed{seed}.pt"


def save_importance(importance, output_path, metadata):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    tmp_path = output_path + ".tmp"
    torch.save(importance, tmp_path)
    os.replace(tmp_path, output_path)

    meta_path = output_path.replace(".pt", ".json")
    save_json(meta_path, metadata)

    print(f"saved: {output_path}")
    print(f"saved: {meta_path}")


def main():
    args = parse_args()
    config = load_config(args.config)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    base_model_name = config["models"]["base_model"]
    domain_models = config["models"]["domain_models"]

    safety_lora_dir = config["models"].get("safety_model_dir", "models/safety_lora")
    safety_lora_path = f"{safety_lora_dir}_seed{args.seed}"

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading base model: {base_model_name}")
    base_model = load_full_model(base_model_name, device)

    targets = [
        {
            "kind": "benign",
            "domain": "math",
            "model_short": "Llama2_WizardMath",
            "model_path": domain_models["math"],
            "loader": "full",
        },
        {
            "kind": "benign",
            "domain": "code",
            "model_short": "Llama2_WizardCoder",
            "model_path": domain_models["code"],
            "loader": "full",
        },
        {
            "kind": "benign",
            "domain": "medical",
            "model_short": "Llama2_MedAlpaca",
            "model_path": domain_models["medical"],
            "loader": "full",
        },
        {
            "kind": "harmful",
            "domain": "safety",
            "model_short": "Llama2_SafetyFT",
            "model_path": safety_lora_path,
            "loader": "safety_lora",
        },
    ]

    for item in targets:
        output_name = build_output_name(
            kind=item["kind"],
            domain=item["domain"],
            model_short=item["model_short"],
            seed=args.seed,
        )
        output_path = os.path.join(args.output_dir, output_name)

        if os.path.exists(output_path) and not args.overwrite:
            print(f"skip existing: {output_path}")
            continue

        print(f"\nComputing data-free importance: {item['domain']}")

        if item["loader"] == "safety_lora":
            target_model = load_safety_model(
                base_model_name=base_model_name,
                safety_lora_path=item["model_path"],
                device=device,
            )
        else:
            target_model = load_full_model(item["model_path"], device)

        importance = compute_delta_squared_importance(
            base_model=base_model,
            target_model=target_model,
        )

        metadata = {
            "status": "success",
            "type": "datafree_delta_squared_importance",
            "formula": "(theta_target - theta_base)^2",
            "note": "This is not empirical FIM. It is a data-free diagonal importance proxy used for comparison with FIM.",
            "kind": item["kind"],
            "domain": item["domain"],
            "base_model": base_model_name,
            "target_model": item["model_path"],
            "seed": args.seed,
            "num_tensors": len(importance),
            "output_path": output_path,
            "timestamp": datetime.now().isoformat(),
        }

        save_importance(importance, output_path, metadata)

        del target_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print("\nDone.")


if __name__ == "__main__":
    main()
