"""
Baseline Merge Methods for SST-Merge V4

Implements TIES, DARE, Task Arithmetic using mergekit or custom implementation.
"""

import torch
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import json
import subprocess
import tempfile
import shutil

logger = logging.getLogger(__name__)


class BaselineMerger:
    """
    Baseline merge methods: TIES, DARE, Task Arithmetic
    
    Uses mergekit when available, falls back to custom implementation.
    """
    
    def __init__(self, device: str = 'cuda'):
        self.device = device
        self.mergekit_available = self._check_mergekit()
    
    def _check_mergekit(self) -> bool:
        """mergekitが利用可能か確認"""
        try:
            import mergekit
            return True
        except ImportError:
            logger.warning("mergekit not available, using custom implementations")
            return False
    
    def merge(
        self,
        method: str,
        adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        アダプターをマージ
        
        Args:
            method: マージ手法 ('task_arithmetic', 'ties', 'dare')
            adapters: アダプターのリスト [A5, A7]
            weights: マージ重み
            **kwargs: 手法固有のパラメータ
            
        Returns:
            merged_adapter: マージされたアダプター
        """
        if weights is None:
            weights = [1.0 / len(adapters)] * len(adapters)
        
        logger.info(f"\nMerging with {method.upper()}...")
        logger.info(f"  Adapters: {len(adapters)}")
        logger.info(f"  Weights: {weights}")
        
        if method == 'task_arithmetic':
            return self._task_arithmetic(adapters, weights)
        elif method == 'ties':
            return self._ties_merge(adapters, weights, **kwargs)
        elif method == 'dare':
            return self._dare_merge(adapters, weights, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _task_arithmetic(
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
        
        logger.info("  Task Arithmetic merge completed")
        return merged
    
    def _ties_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        density: float = 0.5,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        TIES-Merging: Trim, Elect Sign, Disjoint Merge
        
        Reference: "TIES-Merging: Resolving Interference When Merging Models" (Yadav et al., 2023)
        
        1. Trim: 絶対値が小さいパラメータを0にする（上位density%のみ保持）
        2. Elect Sign: 非ゼロパラメータの符号で多数決
        3. Disjoint Merge: 選ばれた符号と同じ符号のパラメータのみを加重和
        """
        merged = {}
        
        for key in adapters[0].keys():
            # 各アダプターのパラメータを収集
            params = []
            for adapter in adapters:
                if key in adapter:
                    params.append(adapter[key].clone())
            
            if not params:
                continue
            
            # Step 1: Trim (上位density%の大きい値のみ保持、残りは0)
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
            
            # Step 2: Elect Sign (非ゼロパラメータの符号で多数決)
            # 0のパラメータは符号投票に参加しない
            stacked = torch.stack(trimmed_params)
            
            # 非ゼロの符号のみカウント（0は無視）
            nonzero_mask = stacked != 0
            signs = torch.sign(stacked) * nonzero_mask.float()
            sign_sum = signs.sum(dim=0)
            
            # 多数決で符号を決定（同数の場合は正を選択）
            elected_sign = torch.sign(sign_sum)
            elected_sign[sign_sum == 0] = 1  # タイの場合は正
            
            # Step 3: Disjoint Merge (同じ符号のパラメータのみを加重和)
            # 注意: TIESは平均ではなく加重和
            merged_param = torch.zeros_like(params[0])
            
            for i, param in enumerate(trimmed_params):
                # 符号が一致するか、パラメータが0の場合はスキップ
                param_sign = torch.sign(param)
                same_sign_or_zero = (param_sign == elected_sign) | (param == 0)
                # 符号が一致する非ゼロパラメータのみ加算
                contribution = param * (param_sign == elected_sign).float()
                merged_param += weights[i] * contribution
            
            merged[key] = merged_param
        
        logger.info(f"  TIES merge completed (density={density})")
        return merged
    
    def _dare_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        drop_rate: float = 0.9,
        rescale: bool = True,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        DARE: Drop And REscale
        
        Reference: "Language Models are Super Mario: Absorbing Abilities from 
                    Homologous Models as a Free Lunch" (Yu et al., 2023)
        
        1. 各アダプターでランダムにパラメータをドロップ（確率 drop_rate）
        2. 残ったパラメータを 1/(1-drop_rate) でリスケール（期待値を保持）
        3. Task Arithmeticでマージ
        """
        merged = {}
        
        # リスケール係数: 期待値を保持するため
        rescale_factor = 1.0 / (1.0 - drop_rate) if rescale else 1.0
        
        for key in adapters[0].keys():
            params = []
            for adapter in adapters:
                if key in adapter:
                    param = adapter[key].clone()
                    
                    # ランダムドロップ（確率drop_rateで0にする）
                    # mask=True: 保持, mask=False: ドロップ
                    mask = torch.rand_like(param.float()) > drop_rate
                    dropped = param * mask.float()
                    
                    # リスケール（期待値を保持）
                    if rescale:
                        dropped = dropped * rescale_factor
                    
                    params.append(dropped)
            
            if params:
                # Task Arithmetic（重み付き和）
                weighted_sum = torch.zeros_like(params[0])
                for param, weight in zip(params, weights):
                    weighted_sum += weight * param
                merged[key] = weighted_sum
        
        logger.info(f"  DARE merge completed (drop_rate={drop_rate}, rescale={rescale_factor:.2f})")
        return merged
    
    def merge_all_methods(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, Dict[str, torch.Tensor]]:
        """
        全てのベースライン手法でマージを実行
        
        Returns:
            results: {method_name: merged_adapter}
        """
        results = {}
        
        methods = [
            ('task_arithmetic', {}),
            ('ties', {'density': 0.5}),
            ('dare', {'drop_rate': 0.9}),
        ]
        
        for method, kwargs in methods:
            try:
                merged = self.merge(method, adapters, weights, **kwargs)
                results[method] = merged
            except Exception as e:
                logger.error(f"Failed to merge with {method}: {e}")
        
        return results
