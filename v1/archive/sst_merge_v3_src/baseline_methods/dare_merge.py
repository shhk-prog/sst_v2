"""
DARE (Drop And REscale) Implementation

DAREは、LoRAアダプターをランダムにドロップしてスケーリングする手法です。

論文: https://arxiv.org/abs/2311.03099
"""

import torch
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DAREMerge:
    """
    DAREアルゴリズムの実装
    
    手順:
    1. ランダムにパラメータをドロップ
    2. スケーリング
    3. 平均化
    """
    
    def __init__(self, drop_rate: float = 0.9):
        """
        Args:
            drop_rate: ドロップ率（0.0-1.0）
        """
        self.drop_rate = drop_rate
        logger.info(f"DAREMerge initialized with drop_rate={drop_rate}")
    
    def merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """
        複数のLoRAアダプターをDAREでマージ
        
        Args:
            lora_adapters: LoRAアダプターのリスト
            
        Returns:
            merged_adapter: マージされたLoRAアダプター
        """
        logger.info(f"Merging {len(lora_adapters)} LoRA adapters with DARE...")
        
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
            
            # Step 1: ランダムドロップ
            # 各パラメータに対してランダムマスクを生成
            dropped_params = []
            for param in params:
                # ドロップマスク（1 - drop_rate の確率で保持）
                mask = torch.rand_like(param) > self.drop_rate
                
                # Step 2: スケーリング
                # ドロップされなかった要素をスケーリング
                scaled_param = param * mask.float() / (1 - self.drop_rate)
                dropped_params.append(scaled_param)
            
            # Step 3: 平均化
            merged[key] = torch.stack(dropped_params).mean(dim=0)
        
        logger.info("✓ DARE completed")
        
        return merged
