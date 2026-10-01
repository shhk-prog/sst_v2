"""
ベースライン手法の実装

TIES-Merging, DARE, Task Arithmeticを実装
"""

import torch
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TIESMerging:
    """
    TIES-Merging: Trim, Elect, Sign, Merge
    
    Reference: https://arxiv.org/abs/2306.01708
    """
    
    def __init__(self, density: float = 0.2):
        """
        Args:
            density: 保持するパラメータの割合（0.0-1.0）
        """
        self.density = density
        logger.info(f"TIESMerging initialized: density={density}")
    
    def merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        TIES-Mergingでアダプターをマージ
        
        Args:
            adapters: アダプターのリスト
            weights: 各アダプターの重み
        
        Returns:
            merged_adapter: マージされたアダプター
        """
        if weights is None:
            weights = [1.0 / len(adapters)] * len(adapters)
        
        logger.info(f"Merging {len(adapters)} adapters with TIES...")
        
        merged = {}
        
        for key in adapters[0].keys():
            tensors = [a[key] for a in adapters]
            
            # Step 1: Trim - 小さい値を削除
            trimmed = self._trim(tensors, self.density)
            
            # Step 2: Elect - 符号の多数決
            signs = self._elect_sign(trimmed)
            
            # Step 3: Sign - 符号を統一
            aligned = self._align_sign(trimmed, signs)
            
            # Step 4: Merge - 重み付き平均
            merged[key] = self._weighted_average(aligned, weights)
        
        logger.info("✓ TIES merging completed")
        return merged
    
    def _trim(self, tensors: List[torch.Tensor], density: float) -> List[torch.Tensor]:
        """小さい値を削除（Trim）"""
        trimmed = []
        for tensor in tensors:
            # 絶対値でソート
            abs_tensor = torch.abs(tensor)
            threshold_idx = int(tensor.numel() * (1 - density))
            threshold = torch.sort(abs_tensor.flatten())[0][threshold_idx]
            
            # 閾値以下をゼロに
            mask = abs_tensor >= threshold
            trimmed_tensor = tensor * mask.float()
            trimmed.append(trimmed_tensor)
        
        return trimmed
    
    def _elect_sign(self, tensors: List[torch.Tensor]) -> torch.Tensor:
        """符号の多数決（Elect）"""
        signs = torch.stack([torch.sign(t) for t in tensors])
        # 多数決
        elected_sign = torch.sign(torch.sum(signs, dim=0))
        return elected_sign
    
    def _align_sign(
        self, 
        tensors: List[torch.Tensor], 
        target_sign: torch.Tensor
    ) -> List[torch.Tensor]:
        """符号を統一（Sign）"""
        aligned = []
        for tensor in tensors:
            # 符号が一致しない要素をゼロに
            mask = torch.sign(tensor) == target_sign
            aligned_tensor = tensor * mask.float()
            aligned.append(aligned_tensor)
        
        return aligned
    
    def _weighted_average(
        self, 
        tensors: List[torch.Tensor], 
        weights: List[float]
    ) -> torch.Tensor:
        """重み付き平均（Merge）"""
        result = sum(w * t for w, t in zip(weights, tensors))
        return result


class DAREMerging:
    """
    DARE: Drop And REscale
    
    Reference: https://arxiv.org/abs/2311.03099
    """
    
    def __init__(self, drop_rate: float = 0.9):
        """
        Args:
            drop_rate: ドロップ率（0.0-1.0）
        """
        self.drop_rate = drop_rate
        logger.info(f"DAREMerging initialized: drop_rate={drop_rate}")
    
    def merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        DAREでアダプターをマージ
        
        Args:
            adapters: アダプターのリスト
            weights: 各アダプターの重み
        
        Returns:
            merged_adapter: マージされたアダプター
        """
        if weights is None:
            weights = [1.0 / len(adapters)] * len(adapters)
        
        logger.info(f"Merging {len(adapters)} adapters with DARE...")
        
        merged = {}
        
        for key in adapters[0].keys():
            tensors = [a[key] for a in adapters]
            
            # Step 1: Drop - ランダムにドロップ
            dropped = self._drop(tensors, self.drop_rate)
            
            # Step 2: Rescale - スケーリング
            rescaled = self._rescale(dropped, self.drop_rate)
            
            # Step 3: Merge - 重み付き平均
            merged[key] = self._weighted_average(rescaled, weights)
        
        logger.info("✓ DARE merging completed")
        return merged
    
    def _drop(
        self, 
        tensors: List[torch.Tensor], 
        drop_rate: float
    ) -> List[torch.Tensor]:
        """ランダムにドロップ"""
        dropped = []
        for tensor in tensors:
            # ランダムマスク
            mask = torch.rand_like(tensor) > drop_rate
            dropped_tensor = tensor * mask.float()
            dropped.append(dropped_tensor)
        
        return dropped
    
    def _rescale(
        self, 
        tensors: List[torch.Tensor], 
        drop_rate: float
    ) -> List[torch.Tensor]:
        """スケーリング"""
        scale_factor = 1.0 / (1.0 - drop_rate)
        rescaled = [t * scale_factor for t in tensors]
        return rescaled
    
    def _weighted_average(
        self, 
        tensors: List[torch.Tensor], 
        weights: List[float]
    ) -> torch.Tensor:
        """重み付き平均"""
        result = sum(w * t for w, t in zip(weights, tensors))
        return result


class TaskArithmetic:
    """
    Task Arithmetic: 単純平均
    
    Reference: https://arxiv.org/abs/2212.04089
    """
    
    def __init__(self):
        logger.info("TaskArithmetic initialized")
    
    def merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Task Arithmeticでアダプターをマージ
        
        Args:
            adapters: アダプターのリスト
            weights: 各アダプターの重み
        
        Returns:
            merged_adapter: マージされたアダプター
        """
        if weights is None:
            weights = [1.0 / len(adapters)] * len(adapters)
        
        logger.info(f"Merging {len(adapters)} adapters with Task Arithmetic...")
        
        merged = {}
        
        for key in adapters[0].keys():
            tensors = [a[key] for a in adapters]
            # 重み付き平均
            merged[key] = sum(w * t for w, t in zip(weights, tensors))
        
        logger.info("✓ Task Arithmetic merging completed")
        return merged
