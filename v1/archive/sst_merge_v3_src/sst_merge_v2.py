"""
SST-Merge V2: Safety-Utility Balanced Merge

既存のSST-Mergeの問題点を解決した新バージョン。
90%以上のJailbreak耐性とUtility維持を目指す。

改善点:
1. Residual Safety Injection - 射影後も元のSafety情報を保持
2. Layer-wise Projection - 層ごとに射影強度を調整
3. Direct Mode - 単純加算でベースライン相当の性能
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SSTMergeV2Quick:
    """
    SST-Merge V2 Quick: FIM計算なしの高速版
    
    ベースライン手法と同等のJailbreak耐性を達成。
    """
    
    def __init__(
        self,
        safety_weight: float = 1.0,
        utility_preservation: float = 0.9,
        device: str = "cuda"
    ):
        self.safety_weight = safety_weight
        self.utility_preservation = utility_preservation
        self.device = device
        
        logger.info("=" * 60)
        logger.info("SST-Merge V2 Quick Initialized")
        logger.info(f"  Safety weight: {safety_weight}")
        logger.info(f"  Utility preservation: {utility_preservation}")
        logger.info("=" * 60)
    
    def merge(
        self,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        method: str = "weighted_add"
    ) -> Dict[str, torch.Tensor]:
        """
        高速マージ（FIM計算なし）
        
        Args:
            utility_adapters: Utilityアダプタのリスト
            safety_adapter: Safetyアダプタ
            method: マージ手法
                - "weighted_add": 重み付き加算（推奨）
                - "ties_style": TIES風の符号調整
                - "dare_style": DARE風のドロップアウト
        """
        logger.info(f"\nSST-Merge V2 Quick: {method}")
        
        # Utilityを平均化
        utility_merged = self._average_adapters(utility_adapters)
        
        if method == "weighted_add":
            return self._weighted_add(utility_merged, safety_adapter)
        elif method == "ties_style":
            return self._ties_style_merge(utility_merged, safety_adapter)
        elif method == "dare_style":
            return self._dare_style_merge(utility_merged, safety_adapter)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _weighted_add(
        self,
        utility: Dict[str, torch.Tensor],
        safety: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        重み付き加算
        
        merged = utility + safety_weight × safety
        """
        logger.info(f"  Utility weight: 1.0 (fixed)")
        logger.info(f"  Safety weight: {self.safety_weight}")
        
        merged = {}
        for key in utility.keys():
            if key in safety:
                merged[key] = utility[key] + self.safety_weight * safety[key]
            else:
                merged[key] = utility[key].clone()
        
        logger.info("✓ Weighted add merge completed")
        return merged
    
    def _ties_style_merge(
        self,
        utility: Dict[str, torch.Tensor],
        safety: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        TIES風マージ: 符号の競合を解決
        """
        logger.info("  Using TIES-style sign resolution")
        merged = {}
        
        for key in utility.keys():
            if key in safety:
                u = utility[key]
                s = safety[key]
                
                # 符号が一致する部分のみマージ
                sign_match = (u.sign() == s.sign())
                
                merged_param = torch.where(
                    sign_match,
                    u + self.safety_weight * s,
                    torch.where(u.abs() > s.abs(), u, self.safety_weight * s)
                )
                merged[key] = merged_param
            else:
                merged[key] = utility[key].clone()
        
        logger.info("✓ TIES-style merge completed")
        return merged
    
    def _dare_style_merge(
        self,
        utility: Dict[str, torch.Tensor],
        safety: Dict[str, torch.Tensor],
        drop_rate: float = 0.1
    ) -> Dict[str, torch.Tensor]:
        """
        DARE風マージ: ランダムドロップアウト + リスケーリング
        """
        logger.info(f"  Using DARE-style dropout (rate={drop_rate})")
        merged = {}
        
        for key in utility.keys():
            if key in safety:
                u = utility[key]
                s = safety[key]
                
                # Safetyにドロップアウトを適用
                mask = torch.bernoulli(torch.ones_like(s) * (1 - drop_rate))
                s_dropped = s * mask / (1 - drop_rate)
                
                merged[key] = u + self.safety_weight * s_dropped
            else:
                merged[key] = utility[key].clone()
        
        logger.info("✓ DARE-style merge completed")
        return merged
    
    def _average_adapters(
        self,
        adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """アダプターを平均化"""
        if len(adapters) == 1:
            return {k: v.clone() for k, v in adapters[0].items()}
        
        averaged = {}
        for key in adapters[0].keys():
            params = [adapter[key] for adapter in adapters]
            averaged[key] = torch.stack(params).mean(dim=0)
        
        return averaged


class SSTMergeV2:
    """
    SST-Merge V2: Safety-Utility Balanced Merge (Full Version)
    
    FIM計算を使用した詳細版。
    """
    
    DEFAULT_LAYER_CONFIG = {
        'q_proj': 0.2,
        'k_proj': 0.2,
        'v_proj': 0.3,
        'o_proj': 0.5,
        'gate_proj': 0.6,
        'up_proj': 0.6,
        'down_proj': 0.6,
    }
    
    def __init__(
        self,
        k: int = 10,
        fim_approximation: str = "gradient_variance",
        regularization: float = 1e-6,
        device: str = "cuda",
        mode: str = "residual",
        residual_ratio: float = 0.7,
        layer_config: Optional[Dict[str, float]] = None
    ):
        self.k = k
        self.fim_approximation = fim_approximation
        self.regularization = regularization
        self.device = device
        self.mode = mode
        self.residual_ratio = residual_ratio
        self.layer_config = layer_config or self.DEFAULT_LAYER_CONFIG
        
        logger.info("=" * 60)
        logger.info("SST-Merge V2 (Full) Initialized")
        logger.info(f"  Mode: {mode}")
        logger.info(f"  k: {k}")
        logger.info(f"  Residual ratio: {residual_ratio}")
        logger.info("=" * 60)
    
    def merge_utility_safety(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader=None,
        safety_dataloader=None,
        max_samples: Optional[int] = 1000,
        alpha: float = 1.0,
        compute_fim: bool = True
    ) -> Dict[str, torch.Tensor]:
        """Utility-Safety マージ"""
        from .fim_calculator import FIMCalculator
        from .gevp_solver import GEVPSolver
        
        logger.info(f"\nSST-Merge V2: {self.mode.upper()} Mode")
        
        # Utilityを平均化
        utility_merged = self._average_adapters(utility_adapters)
        
        if self.mode == "direct" or not compute_fim:
            return self._merge_direct(utility_merged, safety_adapter, alpha)
        
        # FIM計算が必要なモード
        if not utility_dataloader or not safety_dataloader:
            logger.warning("No dataloaders provided, falling back to direct mode")
            return self._merge_direct(utility_merged, safety_adapter, alpha)
        
        # FIM計算とGEVP
        safety_subspace = self._compute_safety_subspace(
            model, utility_adapters, safety_adapter,
            utility_dataloader, safety_dataloader, max_samples
        )
        
        if self.mode == "residual":
            return self._merge_residual(utility_merged, safety_adapter, safety_subspace, alpha)
        elif self.mode == "layerwise":
            return self._merge_layerwise(utility_merged, safety_adapter, safety_subspace, alpha)
        else:
            return self._merge_direct(utility_merged, safety_adapter, alpha)
    
    def _compute_safety_subspace(self, model, utility_adapters, safety_adapter,
                                  utility_dataloader, safety_dataloader, max_samples):
        """安全サブスペースを計算"""
        from peft import get_peft_model, LoraConfig, TaskType
        from .fim_calculator import FIMCalculator
        from .gevp_solver import GEVPSolver
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            bias="none"
        )
        
        # Utility FIM
        F_utility = None
        for adapter in utility_adapters:
            peft_model = get_peft_model(model, lora_config)
            for name, param in peft_model.named_parameters():
                if name in adapter:
                    param.data = adapter[name].to(param.device)
            
            fim_calc = FIMCalculator(peft_model, device=self.device)
            if hasattr(model, 'tokenizer'):
                fim_calc.tokenizer = model.tokenizer
            
            F = fim_calc.compute_fim_benign(utility_dataloader, max_samples)
            F_utility = F if F_utility is None else F_utility + F
            
            del peft_model, fim_calc
            torch.cuda.empty_cache()
        
        F_utility = F_utility / len(utility_adapters)
        
        # Safety FIM
        peft_model = get_peft_model(model, lora_config)
        for name, param in peft_model.named_parameters():
            if name in safety_adapter:
                param.data = safety_adapter[name].to(param.device)
        
        fim_calc = FIMCalculator(peft_model, device=self.device)
        if hasattr(model, 'tokenizer'):
            fim_calc.tokenizer = model.tokenizer
        
        F_safety = fim_calc.compute_fim_harm(safety_dataloader, max_samples)
        
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        # GEVP
        gevp_solver = GEVPSolver(regularization=self.regularization)
        _, eigenvectors = gevp_solver.solve_gevp(F_safety, F_utility, k=self.k)
        safety_subspace = gevp_solver.select_safety_subspace(eigenvectors, k=self.k)
        
        return safety_subspace
    
    def _merge_direct(self, utility, safety, alpha):
        """直接加算"""
        logger.info(f"[DIRECT] utility + {alpha} × safety")
        merged = {}
        for key in utility.keys():
            if key in safety:
                merged[key] = utility[key] + alpha * safety[key]
            else:
                merged[key] = utility[key].clone()
        return merged
    
    def _merge_residual(self, utility, safety, subspace, alpha):
        """残差Safetyモード"""
        logger.info(f"[RESIDUAL] residual_ratio={self.residual_ratio}")
        merged = {}
        
        for key in utility.keys():
            if key in safety:
                s = safety[key]
                shape = s.shape
                flat = s.flatten()
                
                if flat.size(0) <= subspace.size(0):
                    sub = subspace[:flat.size(0), :]
                    proj_flat = sub @ (sub.T @ flat)
                    proj = proj_flat.reshape(shape)
                else:
                    proj = s
                
                blended = self.residual_ratio * s + (1 - self.residual_ratio) * proj
                merged[key] = utility[key] + alpha * blended
            else:
                merged[key] = utility[key].clone()
        
        return merged
    
    def _merge_layerwise(self, utility, safety, subspace, alpha):
        """層別射影モード"""
        logger.info("[LAYERWISE] Layer-specific projection")
        merged = {}
        
        for key in utility.keys():
            if key in safety:
                s = safety[key]
                shape = s.shape
                flat = s.flatten()
                
                strength = self._get_layer_strength(key)
                
                if flat.size(0) <= subspace.size(0):
                    sub = subspace[:flat.size(0), :]
                    proj_flat = sub @ (sub.T @ flat)
                    proj = proj_flat.reshape(shape)
                else:
                    proj = s
                
                blended = (1 - strength) * s + strength * proj
                merged[key] = utility[key] + alpha * blended
            else:
                merged[key] = utility[key].clone()
        
        return merged
    
    def _get_layer_strength(self, key):
        for layer_type, strength in self.layer_config.items():
            if layer_type in key:
                return strength
        return 0.5
    
    def _average_adapters(self, adapters):
        if len(adapters) == 1:
            return {k: v.clone() for k, v in adapters[0].items()}
        
        averaged = {}
        for key in adapters[0].keys():
            params = [a[key] for a in adapters]
            averaged[key] = torch.stack(params).mean(dim=0)
        return averaged


def create_sst_merge_v2(mode="quick", **kwargs):
    """ファクトリ関数"""
    if mode == "quick":
        return SSTMergeV2Quick(**kwargs)
    else:
        return SSTMergeV2(mode=mode, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("SST-Merge V2 module loaded successfully!")
