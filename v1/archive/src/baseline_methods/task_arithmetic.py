"""
Task-Arithmetic Implementation

Task-Arithmeticは、タスクベクトルの算術演算によって
複数のLoRAアダプターをマージする手法です。

論文: https://arxiv.org/abs/2212.04089
"""

import torch
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TaskArithmetic:
    """
    Task-Arithmeticアルゴリズムの実装
    
    手順:
    1. 各アダプターをタスクベクトルとして扱う
    2. 単純な平均化またはスケーリング
    """
    
    def __init__(self, scaling_factor: float = 1.0):
        """
        Args:
            scaling_factor: スケーリング係数
        """
        self.scaling_factor = scaling_factor
        logger.info(f"TaskArithmetic initialized with scaling_factor={scaling_factor}")
    
    def merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """
        複数のLoRAアダプターをTask-Arithmeticでマージ
        
        Args:
            lora_adapters: LoRAアダプターのリスト
            
        Returns:
            merged_adapter: マージされたLoRAアダプター
        """
        logger.info(f"Merging {len(lora_adapters)} LoRA adapters with Task-Arithmetic...")
        
        if not lora_adapters:
            raise ValueError("No LoRA adapters provided")
        
        if len(lora_adapters) == 1:
            logger.warning("Only one adapter provided, returning as is")
            return lora_adapters[0]
        
        merged = {}
        
        for key in lora_adapters[0].keys():
            # 各アダプターから同じキーのパラメータを取得
            params = [adapter[key] for adapter in lora_adapters]
            
            # すべてのパラメータを同じデバイスに移動
            device = params[0].device
            params = [p.to(device) for p in params]
            
            # 単純な平均化
            avg_param = torch.stack(params).mean(dim=0)
            
            # スケーリング
            merged[key] = avg_param * self.scaling_factor
        
        logger.info("✓ Task-Arithmetic completed")
        
        return merged
