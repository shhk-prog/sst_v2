"""
SST-Merge: Safety Subspace Task-Merge (Interpolation Mode)

補間型マージを使用: merged = (1-α) × utility + α × safety
Task Arithmetic互換の動作をするバージョン

Reference:
- 元のSST-Merge: sst_merge.py
- Task Arithmetic: "Editing Models with Task Arithmetic" (Ilharco et al., 2023)
"""

import os
# GPU設定は main() 実行時のみ（インポート時はスキップ）
if __name__ == "__main__":
    num = input("gpu num:")
    os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, LoraConfig, get_peft_model, TaskType
from safetensors.torch import load_file, save_file
from datasets import load_dataset
from torch.utils.data import DataLoader
from pathlib import Path
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 元のSST-Mergeから必要なクラスをインポート
from core.sst_merge import (
    FIMCalculator, 
    GEVPSolver,
    create_dataloader,
    create_utility_dataloader_from_hf
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SSTMergeInterpolation:
    """
    SST-Merge with Interpolation Mode
    
    加算型ではなく補間型を使用:
    - 加算型（従来）: merged = utility + α × safety
    - 補間型（新規）: merged = (1-α) × utility + α × safety
    
    補間型はTask Arithmeticと同じ動作をするため、公平な比較が可能
    """
    
    # Layer-wise Safety Weights
    LAYER_WEIGHTS = {
        'lm_head': 1.5,      # 出力層: Safety強め
        'q_proj': 1.2,       # Attention: Safety強め
        'k_proj': 1.2,
        'v_proj': 1.2,
        'o_proj': 1.2,
        'gate_proj': 0.8,    # FFN: Utility保持
        'up_proj': 0.8,
        'down_proj': 0.8,
    }
    
    def __init__(
        self,
        safety_weight: float = 0.5,
        use_layerwise_weights: bool = True,
        use_gevp: bool = True,
        regularization: float = 1e-6,
        top_k_ratio: Optional[float] = None,
        device: str = 'cuda'
    ):
        """
        Args:
            safety_weight: Safety重み (α)
            use_layerwise_weights: Layer-wise重み調整を使用
            use_gevp: GEVP-basedマスクを使用
            regularization: FIM正則化項
            top_k_ratio: Top-k選択比率
            device: 計算デバイス
        """
        self.safety_weight = safety_weight
        self.use_layerwise_weights = use_layerwise_weights
        self.use_gevp = use_gevp
        self.regularization = regularization
        self.top_k_ratio = top_k_ratio
        self.device = device
        
        logger.info(f"SSTMergeInterpolation: α={safety_weight}, layerwise={use_layerwise_weights}, "
                   f"gevp={use_gevp}, MODE=INTERPOLATION")
    
    def merge(
        self,
        model: nn.Module,
        tokenizer,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader=None,
        safety_dataloader=None,
        max_samples: int = 200,
        f_benign: torch.Tensor = None,
        f_harm: torch.Tensor = None,
        eigenvalues: torch.Tensor = None,
        safety_mask: torch.Tensor = None
    ) -> Dict[str, torch.Tensor]:
        """
        SST-Merge（補間モード）を実行
        """
        logger.info("\n" + "="*60)
        logger.info("SST-Merge: Interpolation Mode")
        logger.info("="*60)
        
        if self.use_gevp and (utility_dataloader and safety_dataloader or (f_benign is not None and f_harm is not None)):
            return self._merge_with_gevp(
                model, tokenizer, utility_adapter, safety_adapter,
                utility_dataloader, safety_dataloader, max_samples,
                f_benign, f_harm, eigenvalues, safety_mask
            )
        else:
            if self.use_gevp:
                logger.warning("GEVP requested but dataloaders/FIMs not provided - falling back to simple interpolation")
            logger.info("Using simple interpolation (no GEVP)")
            return self._interpolation_merge(utility_adapter, safety_adapter)
            
    def compute_fim(
        self,
        model: nn.Module,
        tokenizer,
        adapter: Dict[str, torch.Tensor],
        dataloader,
        max_samples: int
    ) -> torch.Tensor:
        """指定されたアダプターのFIMを計算するヘルパーメソッド"""
        # LoRA設定を推定
        lora_r = 16
        for key, val in adapter.items():
            if 'lora_A' in key:
                lora_r = val.shape[0]
                break
            elif 'lora_B' in key:
                lora_r = val.shape[1]
                break
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_r * 2,
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"],
            bias="none"
        )
        
        peft_model = get_peft_model(model, lora_config)
        self._load_adapter_to_model(peft_model, adapter)
        
        fim_calc = FIMCalculator(peft_model, tokenizer, self.device, self.regularization)
        FIM = fim_calc.compute_fim(dataloader, max_samples)
        
        # Clean up: unload adapter to restore base model
        peft_model.unload()
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        return FIM
    
    def _merge_with_gevp(
        self,
        model: nn.Module,
        tokenizer,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int,
        f_benign: torch.Tensor = None,
        f_harm: torch.Tensor = None,
        eigenvalues: torch.Tensor = None,
        safety_mask: torch.Tensor = None
    ) -> Dict[str, torch.Tensor]:
        """GEVP-based merge with interpolation"""
        
        # Step 1: Utility FIM計算
        if f_benign is None:
            logger.info("\nStep 1: Computing Utility FIM (F_benign)...")
            F_benign = self.compute_fim(model, tokenizer, utility_adapter, utility_dataloader, max_samples)
        else:
            F_benign = f_benign
        
        # Step 2: Safety FIM計算
        if f_harm is None:
            logger.info("\nStep 2: Computing Safety FIM (F_harm)...")
            F_harm = self.compute_fim(model, tokenizer, safety_adapter, safety_dataloader, max_samples)
        else:
            F_harm = f_harm
        
        # Step 3: GEVP解く
        if eigenvalues is None:
            logger.info("\nStep 3: Solving GEVP...")
            gevp_solver = GEVPSolver(self.regularization)
            eigenvalues, sorted_indices = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
            # sorted_indicesは使わないので無視（対角成分に対応）
        else:
            gevp_solver = GEVPSolver(self.regularization) # マスク計算用に必要
        
        # Step 4: Safety maskを計算
        if safety_mask is None:
            logger.info("\nStep 4: Computing safety mask...")
            safety_mask = gevp_solver.compute_safety_mask(eigenvalues, self.top_k_ratio)
        
        # Step 5: 補間型マスクマージ
        logger.info("\nStep 5: Merging with GEVP-based mask (INTERPOLATION MODE)...")
        merged = self._merge_with_mask_interpolation(
            utility_adapter, safety_adapter, safety_mask
        )
        
        logger.info("\n" + "="*60)
        logger.info("SST-Merge (Interpolation) completed!")
        logger.info("="*60)
        
        return merged
    
    def _load_adapter_to_model(
        self,
        peft_model: nn.Module,
        adapter: Dict[str, torch.Tensor]
    ):
        """アダプターパラメータをモデルにロード"""
        applied = 0
        model_params = {n: p for n, p in peft_model.named_parameters() 
                       if 'lora' in n.lower()}
        
        for model_name, param in model_params.items():
            for adapter_name, adapter_val in adapter.items():
                model_key = model_name.replace('.default', '').split('.')[-3:]
                adapter_key = adapter_name.replace('.default', '').split('.')[-3:]
                
                if model_key == adapter_key and param.shape == adapter_val.shape:
                    param.data = adapter_val.to(param.device)
                    applied += 1
                    break
        
        logger.info(f"  Applied {applied} adapter parameters")
    
    def _merge_with_mask_interpolation(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        safety_mask: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        GEVPマスクを使った補間型マージ
        
        補間型マージ:
        merged[i] = (1 - α * layer_weight * mask[i]) * utility[i] 
                  + α * layer_weight * mask[i] * safety[i]
        
        α=1.0, mask=1.0 の場合: merged = 0 * utility + 1 * safety = safety (完全切り替え)
        α=0.5, mask=1.0 の場合: merged = 0.5 * utility + 0.5 * safety (均等)
        """
        merged = {}
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        # LoRAパラメータと非LoRAパラメータを分離
        lora_keys = [k for k in utility_adapter.keys() if 'lora' in k.lower()]
        non_lora_keys = [k for k in utility_adapter.keys() if 'lora' not in k.lower()]
        
        lora_sizes = [utility_adapter[k].numel() for k in lora_keys]
        total_lora_size = sum(lora_sizes)
        
        logger.info(f"  LoRA parameters: {len(lora_keys)} tensors, {total_lora_size} elements")
        if non_lora_keys:
            non_lora_size = sum(utility_adapter[k].numel() for k in non_lora_keys)
            logger.info(f"  Non-LoRA parameters: {len(non_lora_keys)} tensors, {non_lora_size} elements")
        
        # マスクサイズチェック
        if len(safety_mask) != total_lora_size:
            logger.warning(f"Mask size mismatch: {len(safety_mask)} vs {total_lora_size}")
            safety_mask = torch.ones(total_lora_size) * 0.5
        
        offset = 0
        stats = {'mean_safety_weight': [], 'mean_utility_weight': []}
        
        # LoRAパラメータ: 補間型GEVPマージ
        for key in lora_keys:
            param_size = utility_adapter[key].numel()
            original_shape = utility_adapter[key].shape
            
            param_mask = safety_mask[offset:offset + param_size].reshape(original_shape)
            
            # Layer-wise weight
            layer_weight = 1.0
            if self.use_layerwise_weights:
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_weight = weight
                        break
            
            if key in safety_adapter:
                utility_val = utility_adapter[key]
                safety_val = safety_adapter[key]
                
                # 補間型マージの重み
                safety_weight = alpha * layer_weight * param_mask.to(utility_val.device)
                utility_weight = 1.0 - safety_weight
                
                # 補間: (1-w) * utility + w * safety
                merged[key] = utility_weight * utility_val + safety_weight * safety_val
                
                stats['mean_safety_weight'].append(safety_weight.mean().item())
                stats['mean_utility_weight'].append(utility_weight.mean().item())
            else:
                merged[key] = utility_adapter[key]
            
            offset += param_size
        
        # 非LoRAパラメータ: 補間型
        for key in non_lora_keys:
            if key in safety_adapter:
                utility_val = utility_adapter[key]
                safety_val = safety_adapter[key]
                
                # Layer-wise weight
                safety_weight = alpha
                if self.use_layerwise_weights:
                    for layer_type, weight in self.LAYER_WEIGHTS.items():
                        if layer_type in key:
                            safety_weight = alpha * weight
                            break
                
                utility_weight = 1.0 - safety_weight
                
                # 補間型
                merged[key] = utility_weight * utility_val + safety_weight * safety_val
                logger.info(f"  Non-LoRA interpolation: {key} (util={utility_weight:.3f}, safe={safety_weight:.3f})")
            else:
                merged[key] = utility_adapter[key]
        
        avg_safe = sum(stats['mean_safety_weight']) / len(stats['mean_safety_weight']) if stats['mean_safety_weight'] else 0
        avg_util = sum(stats['mean_utility_weight']) / len(stats['mean_utility_weight']) if stats['mean_utility_weight'] else 0
        logger.info(f"  Interpolation GEVP merge: avg utility weight={avg_util:.4f}, avg safety weight={avg_safe:.4f}")
        
        return merged
    
    def _interpolation_merge(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        シンプルな補間型マージ (GEVP未使用時)
        
        merged = (1-α) × utility + α × safety
        
        これはTask Arithmeticと同じアルゴリズム
        """
        merged = {}
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        for key in utility_adapter.keys():
            utility_val = utility_adapter[key]
            
            # Layer-wise weight
            layer_weight = alpha
            if self.use_layerwise_weights:
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_weight = alpha * weight
                        break
            
            if key in safety_adapter:
                safety_val = safety_adapter[key]
                
                # 補間型: (1-α) × utility + α × safety
                utility_weight = 1.0 - layer_weight
                merged[key] = utility_weight * utility_val + layer_weight * safety_val
            else:
                merged[key] = utility_val
        
        logger.info(f"  Simple interpolation merge (α={alpha})")
        return merged


if __name__ == "__main__":
    # テスト用のメイン関数
    logger.info("SST-Merge Interpolation Mode")
    logger.info("Use run_all_merges_interpolation.py for actual merging")
