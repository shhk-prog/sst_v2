import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, LoraConfig, get_peft_model
from safetensors.torch import load_file, save_file
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import contents of merge_adapters.py but customize settings
import sys
sys.path.append('.')
from merge_adapters import AdapterMerger, load_adapter, save_merged_adapter

# Settings
model_id = "meta-llama/Llama-3.1-8B-Instruct"
utility_path = "../../models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4"
safety_path = "../../models/finetuned/adapters/FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_10ep_lr2e-4"
output_dir = "../../models/merged/sst_merge/full/compare"

os.makedirs(output_dir, exist_ok=True)

merger = AdapterMerger()
u_adapter = load_adapter(utility_path)
s_adapter = load_adapter(safety_path)

# SST Merge
config = {"safety_weight": 0.5, "use_layerwise": True}
merged = merger.sst_merge(u_adapter, s_adapter, **config)

output_path = Path(output_dir) / "A5_A7_sst_compare"
metadata = {
    "utility_adapter": utility_path,
    "safety_adapter": safety_path,
    "merge_method": "sst",
    "merge_config": config,
    "base_model": model_id,
    "timestamp": datetime.now().isoformat(),
}

save_merged_adapter(merged, output_path, utility_path, metadata)
print(f"SST Merge completed and saved to {output_path}")
