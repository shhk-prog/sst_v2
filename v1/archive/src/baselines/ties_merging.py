"""
TIES-Merging Baseline

Trim, Elect Sign, Mergeの3ステップでタスク干渉を軽減。

参考文献:
Yadav et al., "TIES-Merging: Resolving Interference When Merging Models", NeurIPS 2023
"""

import torch
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TIESMerging:
    """
    TIES-Merging: Trim, Elect Sign, and Merge
    
    1. Trim: 小さい更新をゼロにする
    2. Elect Sign: 符号の衝突を解決
    3. Merge: 一致した符号のパラメータを結合
    """
    
    def __init__(self, trim_threshold: float = 0.2):
        """
        Args:
            trim_threshold: トリミング閾値（下位x%をゼロにする）
        """
        self.trim_threshold = trim_threshold
        logger.info(f"TIES-Merging initialized: trim_threshold={trim_threshold}")
    
    def merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAアダプタをTIES-Mergingでマージ
        
        Args:
            lora_adapters: LoRAアダプタのリスト
            
        Returns:
            merged_adapter: マージされたアダプタ
        """
        logger.info(f"Merging {len(lora_adapters)} adapters with TIES-Merging")
        
        merged_adapter = {}
        
        for key in lora_adapters[0].keys():
            # Step 1: Trim - 小さい値をゼロにする
            trimmed_params = self._trim([adapter[key] for adapter in lora_adapters])
            
            # Step 2: Elect Sign - 符号を決定
            elected_sign = self._elect_sign(trimmed_params)
            
            # Step 3: Merge - 一致した符号のみを平均化
            merged_adapter[key] = self._merge_with_sign(trimmed_params, elected_sign)
        
        return merged_adapter
    
    def _trim(self, params: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        Step 1: 小さい更新をゼロにする
        
        Args:
            params: パラメータのリスト
            
        Returns:
            trimmed_params: トリミング後のパラメータ
        """
        trimmed_params = []
        
        for param in params:
            # 絶対値でソート
            abs_param = torch.abs(param)
            threshold = torch.quantile(abs_param.flatten(), self.trim_threshold)
            
            # 閾値以下をゼロにする
            trimmed = param.clone()
            trimmed[abs_param < threshold] = 0
            
            trimmed_params.append(trimmed)
        
        return trimmed_params
    
    def _elect_sign(self, params: List[torch.Tensor]) -> torch.Tensor:
        """
        Step 2: 各パラメータの符号を多数決で決定
        
        Args:
            params: パラメータのリスト
            
        Returns:
            elected_sign: 決定された符号 (+1 or -1)
        """
        # 各位置での符号の合計
        sign_sum = sum(torch.sign(param) for param in params)
        
        # 多数決（正なら+1、負なら-1、ゼロなら0）
        elected_sign = torch.sign(sign_sum)
        
        return elected_sign
    
    def _merge_with_sign(
        self,
        params: List[torch.Tensor],
        elected_sign: torch.Tensor
    ) -> torch.Tensor:
        """
        Step 3: 決定された符号と一致するパラメータのみを平均化
        
        Args:
            params: パラメータのリスト
            elected_sign: 決定された符号
            
        Returns:
            merged: マージされたパラメータ
        """
        merged = torch.zeros_like(params[0])
        count = torch.zeros_like(params[0])
        
        for param in params:
            # 符号が一致する位置のみを考慮
            mask = (torch.sign(param) == elected_sign) & (param != 0)
            merged += param * mask
            count += mask.float()
        
        # 平均化（ゼロ除算対策）
        merged = torch.where(count > 0, merged / count, merged)
        
        return merged
