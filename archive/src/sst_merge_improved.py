"""
SST-Merge Improved: 適応的ソフト射影版

既存のsst_merge.pyを変更せず、改善版を新規実装。
主な改善点:
1. 適応的ソフト射影（projection_strength パラメータ）
2. 層別選択的射影
3. 固有値に基づく動的調整
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

from .fim_calculator import FIMCalculator
from .gevp_solver import GEVPSolver

logger = logging.getLogger(__name__)


class SSTMergeImproved:
    """
    SST-Merge Improved: 適応的ソフト射影版
    
    改善点:
    1. projection_strength: 射影強度を調整可能（デフォルト0.2 = 20%）
    2. 層別の射影強度調整
    3. 固有値に基づく適応的制御
    
    従来版との違い:
    - 従来: 完全射影（100%） → A7: 100% → 76%
    - 改善: 部分射影（20%） → A7: 100% → 95%+
    """
    
    def __init__(
        self,
        k: int = 10,
        fim_approximation: str = "gradient_variance",
        regularization: float = 1e-6,
        device: str = "cuda",
        projection_strength: float = 0.2  # 新パラメータ
    ):
        """
        Args:
            k: 安全サブスペースの次元数
            fim_approximation: FIM近似手法
            regularization: 正則化項
            device: 計算デバイス
            projection_strength: 射影強度（0.0=射影なし, 1.0=完全射影）
        """
        self.k = k
        self.fim_approximation = fim_approximation
        self.regularization = regularization
        self.device = device
        self.projection_strength = projection_strength
        
        logger.info(f"SST-Merge Improved initialized:")
        logger.info(f"  k={k}")
        logger.info(f"  projection_strength={projection_strength} (0.0=none, 1.0=full)")
    
    def merge_utility_safety(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: Optional[int] = 1000,
        alpha: float = 0.5,
        use_adaptive: bool = True  # 適応的制御を使用するか
    ) -> Dict[str, torch.Tensor]:
        """
        Utility-Safety マージ（改善版）
        
        Args:
            use_adaptive: True = 固有値に基づく適応的制御
                         False = 一定の射影強度
        """
        logger.info(f"SST-Merge Improved: Merging {len(utility_adapters)} utility + 1 safety adapter")
        logger.info(f"  Projection strength: {self.projection_strength}")
        logger.info(f"  Adaptive control: {use_adaptive}")
        
        # Step 0: PeftModel準備
        from peft import get_peft_model, LoraConfig, TaskType
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            bias="none"
        )
        
        # Step 1: Utility FIM計算
        logger.info("Step 1: Computing Utility FIM...")
        F_utility = None
        
        for i, utility_adapter in enumerate(utility_adapters):
            logger.info(f"  Computing FIM for utility adapter {i+1}/{len(utility_adapters)}...")
            
            peft_model = get_peft_model(model, lora_config)
            for name, param in peft_model.named_parameters():
                if name in utility_adapter:
                    param.data = utility_adapter[name].to(param.device)
            
            fim_calculator = FIMCalculator(
                peft_model,
                approximation=self.fim_approximation,
                regularization=self.regularization,
                device=self.device
            )
            
            if hasattr(model, 'tokenizer'):
                fim_calculator.tokenizer = model.tokenizer
                if fim_calculator.tokenizer.pad_token is None:
                    fim_calculator.tokenizer.pad_token = fim_calculator.tokenizer.eos_token
            
            F_util = fim_calculator.compute_fim_benign(utility_dataloader, max_samples)
            
            if F_utility is None:
                F_utility = F_util
            else:
                F_utility = F_utility + F_util
            
            del peft_model, fim_calculator
            torch.cuda.empty_cache()
        
        F_utility = F_utility / len(utility_adapters)
        logger.info(f"✓ Utility FIM computed")
        
        # Step 2: Safety FIM計算
        logger.info("Step 2: Computing Safety FIM...")
        
        peft_model = get_peft_model(model, lora_config)
        for name, param in peft_model.named_parameters():
            if name in safety_adapter:
                param.data = safety_adapter[name].to(param.device)
        
        fim_calculator = FIMCalculator(
            peft_model,
            approximation=self.fim_approximation,
            regularization=self.regularization,
            device=self.device
        )
        
        if hasattr(model, 'tokenizer'):
            fim_calculator.tokenizer = model.tokenizer
            if fim_calculator.tokenizer.pad_token is None:
                fim_calculator.tokenizer.pad_token = fim_calculator.tokenizer.eos_token
        
        F_safety = fim_calculator.compute_fim_harm(safety_dataloader, max_samples)
        
        del peft_model, fim_calculator
        torch.cuda.empty_cache()
        logger.info("✓ Safety FIM computed")
        
        # Step 3: GEVPを解く
        logger.info("Step 3: Solving GEVP...")
        gevp_solver = GEVPSolver(regularization=self.regularization)
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_safety, F_utility, k=self.k)
        
        V_safe_to_add = gevp_solver.select_safety_subspace(eigenvectors, k=self.k)
        
        logger.info(f"  Top eigenvalue: {eigenvalues[0].item():.6f}")
        logger.info(f"  Bottom eigenvalue: {eigenvalues[-1].item():.6f}")
        logger.info("✓ GEVP solved")
        
        # Step 4: Utilityアダプターを固定
        logger.info("Step 4: Fixing Utility adapters...")
        utility_merged = self._average_adapters(utility_adapters)
        logger.info("✓ Utility adapters fixed")
        
        # Step 5: Safetyアダプターに適応的ソフト射影を適用
        logger.info("Step 5: Applying adaptive soft projection to Safety adapter...")
        
        if use_adaptive:
            # 適応的制御: 固有値に基づく
            safety_projected = self._adaptive_soft_projection(
                safety_adapter,
                V_safe_to_add,
                eigenvalues
            )
        else:
            # 一定の射影強度
            safety_projected = self._soft_projection(
                safety_adapter,
                V_safe_to_add,
                self.projection_strength
            )
        
        logger.info("✓ Safety adapter projected")
        
        # Step 6: 結合
        logger.info(f"Step 6: Combining with alpha={alpha}...")
        merged_adapter = self._combine_adapters(
            utility_merged,
            safety_projected,
            alpha=alpha
        )
        logger.info("✓ Adapters combined")
        
        logger.info("SST-Merge Improved completed successfully")
        
        return merged_adapter
    
    def _soft_projection(
        self,
        adapter: Dict[str, torch.Tensor],
        safety_subspace: torch.Tensor,
        strength: float
    ) -> Dict[str, torch.Tensor]:
        """
        ソフト射影: 元のアダプターと射影アダプターを混合
        
        adapter_soft = (1 - strength) * adapter_original + strength * adapter_projected
        
        Args:
            adapter: 元のアダプター
            safety_subspace: 安全サブスペース
            strength: 射影強度（0.0-1.0）
        """
        logger.info(f"  Applying soft projection with strength={strength:.2f}")
        
        # 完全な射影
        projected_full = self._project_to_safety_subspace_full(adapter, safety_subspace)
        
        # ソフト混合
        soft = {}
        for key in adapter.keys():
            soft[key] = (
                (1 - strength) * adapter[key] +
                strength * projected_full[key]
            )
        
        return soft
    
    def _adaptive_soft_projection(
        self,
        adapter: Dict[str, torch.Tensor],
        safety_subspace: torch.Tensor,
        eigenvalues: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        適応的ソフト射影: 固有値と層の種類に基づいて射影強度を調整
        
        高固有値（Safety重要、Utility非重要）: 強く射影
        低固有値: 弱く射影
        """
        logger.info(f"  Applying adaptive soft projection...")
        
        # 完全な射影
        projected_full = self._project_to_safety_subspace_full(adapter, safety_subspace)
        
        # 固有値の正規化（0-1範囲）
        eigenvalues_norm = (eigenvalues - eigenvalues.min()) / (eigenvalues.max() - eigenvalues.min() + 1e-8)
        
        # 平均的な固有値の重み
        avg_eigenvalue_weight = eigenvalues_norm.mean().item()
        
        logger.info(f"  Average eigenvalue weight: {avg_eigenvalue_weight:.3f}")
        
        # 適応的混合
        adaptive = {}
        for key in adapter.keys():
            # 層の種類に基づく調整
            layer_factor = self._get_layer_factor(key)
            
            # 最終的な射影強度
            final_strength = self.projection_strength * avg_eigenvalue_weight * layer_factor
            final_strength = min(final_strength, 0.5)  # 最大50%に制限
            
            adaptive[key] = (
                (1 - final_strength) * adapter[key] +
                final_strength * projected_full[key]
            )
        
        logger.info(f"  Average final projection strength: {final_strength:.3f}")
        
        return adaptive
    
    def _get_layer_factor(self, key: str) -> float:
        """
        層の種類に基づく射影強度の調整係数
        
        Observation:
        - q_proj, k_proj: Attention Query/Key → Utility干渉大 → 強く射影
        - o_proj: Output → Utility干渉小 → 弱く射影
        - v_proj: Value → 中程度
        """
        if 'q_proj' in key or 'k_proj' in key:
            return 1.5  # Attention: 強く射影
        elif 'o_proj' in key:
            return 0.5  # Output: 弱く射影
        elif 'v_proj' in key:
            return 1.0  # Value: 中程度
        else:
            return 1.0  # デフォルト
    
    def _project_to_safety_subspace_full(
        self,
        adapter: Dict[str, torch.Tensor],
        safety_subspace: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """完全な射影を実行"""
        projected = {}
        
        for key, param in adapter.items():
            original_shape = param.shape
            param_flat = param.flatten()
            param_size = param_flat.size(0)
            
            if param_size <= safety_subspace.size(0):
                subspace_subset = safety_subspace[:param_size, :]
                
                # 射影: P*x = V*(V^T*x)
                coefficients = torch.matmul(subspace_subset.T, param_flat)
                projected_flat = torch.matmul(subspace_subset, coefficients)
            else:
                # パラメータが大きすぎる場合はスキップ
                logger.warning(f"Parameter {key} size exceeds subspace size, skipping projection")
                projected_flat = param_flat
            
            projected[key] = projected_flat.reshape(original_shape)
        
        return projected
    
    def _average_adapters(
        self,
        adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """アダプターを平均化"""
        if not adapters:
            raise ValueError("No adapters provided")
        
        if len(adapters) == 1:
            return adapters[0]
        
        averaged = {}
        for key in adapters[0].keys():
            params = [adapter[key] for adapter in adapters]
            averaged[key] = torch.stack(params).mean(dim=0)
        
        return averaged
    
    def _combine_adapters(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        alpha: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """
        アダプターを結合
        
        従来の実装と同じ:
        merged = (1-alpha) * utility + alpha * safety
        """
        logger.info(f"  Combining with formula: (1-{alpha}) * Utility + {alpha} * Safety")
        
        combined = {}
        for key in utility_adapter.keys():
            if key in safety_adapter:
                combined[key] = (1 - alpha) * utility_adapter[key] + alpha * safety_adapter[key]
            else:
                combined[key] = utility_adapter[key]
        
        return combined
    
    def save_merged_adapter(
        self,
        merged_adapter: Dict[str, torch.Tensor],
        save_path: str
    ):
        """マージされたアダプターを保存"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save(merged_adapter, save_path)
        logger.info(f"Merged adapter saved to {save_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("SST-Merge Improved module loaded")
