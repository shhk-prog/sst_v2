"""
Adapter Merge Script for SST-Merge V5

Merges utility (A5/A6) and safety (A7) adapters using various methods:
- Task Arithmetic: Weighted average
- TIES: Trim, Elect Sign, Disjoint Merge
- DARE: Drop And Rescale
- SST: Safety Subspace Task-Merge (Interpolation)

Output: merge_model/A5_A7_method/, merge_model/A6_A7_method/, etc.
"""

import os
# num = input("gpu num:")
# os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, LoraConfig, get_peft_model
from safetensors.torch import load_file, save_file
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
model_id = "meta-llama/Llama-3.1-8B-Instruct"

# マージするアダプターのペア
# (utility_adapter_path, safety_adapter_path, output_name)
merge_pairs = [
    A5 (RepliQA) + A7 (Safety)
    ("./FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4", 
     "./FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A5_A7"),
    # A6 (Alpaca) + A7 (Safety)
    ("./FT_model/A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4",
     "./FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A6_A7"),
]

# マージ手法
merge_methods = ["task_arithmetic", "ties", "dare", "sst"]  # 全手法
# merge_methods = ["sst"]  # SSTのみ

# マージパラメータ
merge_config = {
    "task_arithmetic": {"weights": [0.5, 0.5]},  # [utility_weight, safety_weight]
    "ties": {"density": 0.5, "weights": [0.5, 0.5]},
    "dare": {"drop_rate": 0.9, "weights": [0.5, 0.5]},
    "sst": {"safety_weight": 0.5, "use_layerwise": True},  # SST interpolation
}

output_dir = "../../models/merged/sst_merge/full/merge_model"
#####################################################


def load_adapter(adapter_path: str) -> Dict[str, torch.Tensor]:
    """アダプターをロード"""
    adapter_path = Path(adapter_path)
    safetensor_path = adapter_path / "adapter_model.safetensors"
    
    if safetensor_path.exists():
        adapter = load_file(str(safetensor_path))
        logger.info(f"Loaded adapter from {safetensor_path}")
    else:
        # PyTorch形式を試す
        pt_path = adapter_path / "adapter_model.bin"
        if pt_path.exists():
            adapter = torch.load(pt_path, map_location='cpu')
            logger.info(f"Loaded adapter from {pt_path}")
        else:
            raise FileNotFoundError(f"No adapter found at {adapter_path}")
    
    return adapter


def save_merged_adapter(
    merged_adapter: Dict[str, torch.Tensor],
    output_path: str,
    base_config_path: str,
    metadata: Optional[Dict] = None
):
    """マージされたアダプターを保存"""
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Safetensors形式で保存
    save_file(merged_adapter, str(output_path / "adapter_model.safetensors"))
    
    # adapter_config.jsonをコピー
    base_config = Path(base_config_path) / "adapter_config.json"
    if base_config.exists():
        with open(base_config, 'r') as f:
            config = json.load(f)
        with open(output_path / "adapter_config.json", 'w') as f:
            json.dump(config, f, indent=2)
    
    # メタデータを保存
    if metadata:
        with open(output_path / "merge_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # README作成
    readme = f"""# Merged Adapter

Created: {datetime.now().isoformat()}

## Merge Info
{json.dumps(metadata, indent=2, ensure_ascii=False) if metadata else 'N/A'}
"""
    with open(output_path / "README.md", 'w') as f:
        f.write(readme)
    
    logger.info(f"Saved merged adapter to {output_path}")


class AdapterMerger:
    """アダプターマージャー"""
    
    def __init__(self, device: str = 'cuda'):
        self.device = device
    
    def task_arithmetic(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float]
    ) -> Dict[str, torch.Tensor]:
        """
        Task Arithmetic: 重み付き平均
        merged = Σ w_i * adapter_i
        """
        merged = {}
        
        for key in adapters[0].keys():
            weighted_sum = torch.zeros_like(adapters[0][key])
            for adapter, weight in zip(adapters, weights):
                if key in adapter:
                    weighted_sum += weight * adapter[key]
            merged[key] = weighted_sum
        
        logger.info(f"Task Arithmetic merge completed (weights={weights})")
        return merged
    
    def ties_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        density: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """
        TIES-Merging: Trim, Elect Sign, Disjoint Merge
        """
        merged = {}
        
        for key in adapters[0].keys():
            params = []
            for adapter in adapters:
                if key in adapter:
                    params.append(adapter[key].clone())
            
            if not params:
                continue
            
            # Step 1: Trim
            trimmed_params = []
            for param in params:
                flat = param.flatten()
                k = int(len(flat) * density)
                if k > 0:
                    threshold = torch.topk(flat.abs(), k).values[-1]
                    mask = flat.abs() >= threshold
                    trimmed = flat.clone()
                    trimmed[~mask] = 0
                    trimmed_params.append(trimmed.reshape(param.shape))
                else:
                    trimmed_params.append(torch.zeros_like(param))
            
            # Step 2: Elect Sign
            stacked = torch.stack(trimmed_params)
            nonzero_mask = stacked != 0
            signs = torch.sign(stacked) * nonzero_mask.float()
            sign_sum = signs.sum(dim=0)
            elected_sign = torch.sign(sign_sum)
            elected_sign[sign_sum == 0] = 1
            
            # Step 3: Disjoint Merge
            merged_param = torch.zeros_like(params[0])
            for i, param in enumerate(trimmed_params):
                param_sign = torch.sign(param)
                contribution = param * (param_sign == elected_sign).float()
                merged_param += weights[i] * contribution
            
            merged[key] = merged_param
        
        logger.info(f"TIES merge completed (density={density}, weights={weights})")
        return merged
    
    def dare_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        drop_rate: float = 0.9
    ) -> Dict[str, torch.Tensor]:
        """
        DARE: Drop And REscale
        """
        merged = {}
        rescale_factor = 1.0 / (1.0 - drop_rate)
        
        for key in adapters[0].keys():
            params = []
            for adapter in adapters:
                if key in adapter:
                    param = adapter[key].clone()
                    mask = torch.rand_like(param.float()) > drop_rate
                    dropped = param * mask.float() * rescale_factor
                    params.append(dropped)
            
            if params:
                weighted_sum = torch.zeros_like(params[0])
                for param, weight in zip(params, weights):
                    weighted_sum += weight * param
                merged[key] = weighted_sum
        
        logger.info(f"DARE merge completed (drop_rate={drop_rate}, weights={weights})")
        return merged
    
    def sst_merge(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        safety_weight: float = 0.5,
        use_layerwise: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        SST Interpolation Merge: (1-α) * Utility + α * Safety
        """
        LAYER_WEIGHTS = {
            'lm_head': 1.5,
            'q_proj': 1.2,
            'k_proj': 1.2,
            'v_proj': 1.2,
            'o_proj': 1.2,
            'gate_proj': 0.8,
            'up_proj': 0.8,
            'down_proj': 0.8,
        }
        
        merged = {}
        alpha = min(max(safety_weight, 0.0), 1.0)
        
        for key in utility_adapter.keys():
            utility_val = utility_adapter[key]
            
            if use_layerwise:
                layer_alpha = alpha
                for layer_type, weight in LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_alpha = min(alpha * weight, 0.95)
                        break
            else:
                layer_alpha = alpha
            
            if key in safety_adapter:
                safety_val = safety_adapter[key]
                merged[key] = (1 - layer_alpha) * utility_val + layer_alpha * safety_val
            else:
                merged[key] = utility_val
        
        logger.info(f"SST merge completed (safety_weight={alpha}, layerwise={use_layerwise})")
        return merged
    
    def merge(
        self,
        method: str,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """マージを実行"""
        adapters = [utility_adapter, safety_adapter]
        
        if method == "task_arithmetic":
            weights = kwargs.get("weights", [0.5, 0.5])
            return self.task_arithmetic(adapters, weights)
        
        elif method == "ties":
            weights = kwargs.get("weights", [0.5, 0.5])
            density = kwargs.get("density", 0.5)
            return self.ties_merge(adapters, weights, density)
        
        elif method == "dare":
            weights = kwargs.get("weights", [0.5, 0.5])
            drop_rate = kwargs.get("drop_rate", 0.9)
            return self.dare_merge(adapters, weights, drop_rate)
        
        elif method == "sst":
            safety_weight = kwargs.get("safety_weight", 0.5)
            use_layerwise = kwargs.get("use_layerwise", True)
            return self.sst_merge(utility_adapter, safety_adapter, safety_weight, use_layerwise)
        
        else:
            raise ValueError(f"Unknown method: {method}")


def main():
    logger.info("="*60)
    logger.info("Adapter Merge Script for SST-Merge V5")
    logger.info("="*60)
    
    merger = AdapterMerger()
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info("="*60)
        
        # アダプターをロード
        try:
            utility_adapter = load_adapter(utility_path)
            safety_adapter = load_adapter(safety_path)
        except FileNotFoundError as e:
            logger.error(f"Skipping {pair_name}: {e}")
            continue
        
        # 各手法でマージ
        for method in merge_methods:
            logger.info(f"\n--- Merging with {method.upper()} ---")
            
            config = merge_config.get(method, {})
            
            try:
                merged = merger.merge(method, utility_adapter, safety_adapter, **config)
                
                # 保存
                output_name = f"{pair_name}_{method}"
                output_path = output_base / output_name
                
                metadata = {
                    "utility_adapter": utility_path,
                    "safety_adapter": safety_path,
                    "merge_method": method,
                    "merge_config": config,
                    "base_model": model_id,
                    "timestamp": datetime.now().isoformat(),
                }
                
                save_merged_adapter(merged, output_path, utility_path, metadata)
                logger.info(f"✓ Saved: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to merge with {method}: {e}")
                import traceback
                traceback.print_exc()
    
    logger.info("\n" + "="*60)
    logger.info("All merges completed!")
    logger.info(f"Output directory: {output_base}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
