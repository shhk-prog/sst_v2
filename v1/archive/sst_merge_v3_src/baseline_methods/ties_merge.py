"""
TIES-Merging Implementation

TIES (TrIm, Elect Sign & Merge) は、複数のLoRAアダプターを
マージする手法です。

論文: https://arxiv.org/abs/2306.01708
"""

import torch
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TIESMerge:
    """
    TIES-Mergingアルゴリズムの実装
    
    手順:
    1. Trim: 小さな値を削除（トリミング）
    2. Elect: 符号の多数決
    3. Merge: 平均化
    """
    
    def __init__(self, k: float = 0.2):
        """
        Args:
            k: トリミング比率（0.0-1.0）
        """
        self.k = k
        logger.info(f"TIESMerge initialized with k={k}")
    
    def merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """
        複数のLoRAアダプターをTIES-Mergingでマージ
        
        Args:
            lora_adapters: LoRAアダプターのリスト
            
        Returns:
            merged_adapter: マージされたLoRAアダプター
        """
        logger.info(f"Merging {len(lora_adapters)} LoRA adapters with TIES-Merging...")
        
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
            
            # Step 1: Trim（トリミング）
            # 小さな値を削除
            params_stack = torch.stack(params)
            abs_params = torch.abs(params_stack)
            
            # k分位点を計算
            threshold = torch.quantile(abs_params.flatten(), self.k)
            
            # 閾値以下の値をゼロに
            mask = abs_params > threshold
            trimmed_params = params_stack * mask
            
            # Step 2: Elect（符号の多数決）
            # 各要素の符号の多数決を取る
            signs = torch.sign(trimmed_params)
            majority_sign = torch.sign(signs.sum(dim=0))
            
            # Step 3: Merge（マージ）
            # 多数決の符号と一致するパラメータのみを平均化
            aligned_params = trimmed_params * (signs == majority_sign.unsqueeze(0)).float()
            
            # ゼロでない要素の数でカウント
            count = (aligned_params != 0).sum(dim=0).float()
            count = torch.clamp(count, min=1.0)  # ゼロ除算を防ぐ
            
            # 平均化
            merged[key] = aligned_params.sum(dim=0) / count
        
        logger.info("✓ TIES-Merging completed")
        
        return merged
