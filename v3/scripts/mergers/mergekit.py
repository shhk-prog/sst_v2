import os
import yaml
import subprocess
from transformers import AutoConfig

import steering_hook
from mergers.constants import MERGEKIT_METHOD_MAP


def run_mergekit(output_dir, method, base_model, models_dict, alpha):
    os.makedirs(output_dir, exist_ok=True)
    yaml_path = os.path.join(output_dir, "merge_config.yml")

    try:
        cfg = AutoConfig.from_pretrained(base_model)
        num_layers = getattr(cfg, "num_hidden_layers", 32)
    except Exception:
        num_layers = 32

    sources = []
    n_utility = len([k for k in models_dict if k != "safety"])

    for m_name, m_path in models_dict.items():
        sources.append({
            "model": m_path,
            "layer_range": [0, num_layers],
            "parameters": {
                "weight": alpha if m_name == "safety" else (1.0 - alpha) / max(n_utility, 1),
                "density": 0.5 if method in ["ties", "dare", "della"] else 1.0,
            },
        })

    mergekit_cfg = {
        "base_model": base_model,
        "merge_method": MERGEKIT_METHOD_MAP[method.lower()],
        "dtype": "float16",
        "slices": [{"sources": sources}],
    }

    if method.lower() == "ties":
        mergekit_cfg["parameters"] = {"intramodel_mask": True, "normalize": True}
    elif method.lower() == "dare":
        mergekit_cfg["parameters"] = {
            "intramodel_mask": True,
            "normalize": True,
            "scaling_coefficient": 1.0,
        }
    elif method.lower() == "della":
        mergekit_cfg["parameters"] = {"epsilon": 0.05, "lambda": 1.0}

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(mergekit_cfg, f, allow_unicode=True)

    steering_hook.verify_merge_method(method, yaml_path)

    cmd = ["mergekit-yaml", yaml_path, output_dir, "--allow-crimes", "--copy-tokenizer"]
    print(f"Running command: {' '.join(cmd)}")

    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        raise RuntimeError(f"mergekit failed with exit code {res.returncode}")

    print("mergekit completed successfully.")
