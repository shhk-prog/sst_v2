"""
Task Arithmetic (TA) Baseline

最もシンプルなLoRAマージング手法。タスクベクトルの線形結合。
"""

import torch
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TaskArithmetic:
    """
    Task Arithmetic (TA)
    
    θ_merged = θ_pre + Σ λ_i (θ_i - θ_pre)
    
    参考文献:
    Ilharco et al., "Editing Models with Task Arithmetic", ICLR 2023
    """
    
    def __init__(self, scaling_factor: float = 0.5):
        """
        Args:
            scaling_factor: タスクベクトルのスケーリング係数
        """
        self.scaling_factor = scaling_factor
        logger.info(f"Task Arithmetic initialized: scaling_factor={scaling_factor}")
    
    def merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAアダプタをTask Arithmeticでマージ
        
        Args:
            lora_adapters: LoRAアダプタのリスト
            weights: 各アダプタの重み（Noneの場合は均等）
            
        Returns:
            merged_adapter: マージされたアダプタ
        """
        if weights is None:
            weights = [1.0 / len(lora_adapters)] * len(lora_adapters)
        
        assert len(lora_adapters) == len(weights)
        
        logger.info(f"Merging {len(lora_adapters)} adapters with Task Arithmetic")
        
        merged_adapter = {}
        
        for key in lora_adapters[0].keys():
            # 重み付き平均
            merged_adapter[key] = sum(
                w * self.scaling_factor * adapter[key]
                for w, adapter in zip(weights, lora_adapters)
            )
        
        return merged_adapter
