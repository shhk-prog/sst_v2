"""
SST-Merge V2: Safety-Preserving Subspace Task-Merge

改善版SST-Merge実装。SafetyとUtility両方を維持しながらマージを実行。

主な改善点:
1. Residual Safety Injection - 射影後も元のSafety情報を一部保持
2. Layer-wise Projection Strength - 層ごとに異なる射影強度
3. Direct Safety Addition Mode - 射影なしの直接追加モード

理論的根拠:
- 元のSST-Mergeでは射影によりSafety情報が大幅に失われていた
- 本実装ではSafety情報を保持しながらUtility干渉を最小化
"""

import torch
import torch.nn as nn
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)

# グローバルキャッシュ
_FIMCalculator = None
_GEVPSolver = None


def _lazy_import_fim():
    """FIMCalculatorを遅延インポート"""
    global _FIMCalculator
    if _FIMCalculator is None:
        # 親ディレクトリ（SST_merge）のsrc/fim_calculator.pyを明示的にロード
        sst_v2_root = Path(__file__).parent.parent  # sst_merge_v2ディレクトリ
        project_root = sst_v2_root.parent  # SST_mergeディレクトリ
        fim_path = project_root / 'src' / 'fim_calculator.py'
        
        spec = importlib.util.spec_from_file_location("fim_calculator_module", fim_path)
        fim_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fim_module)
        _FIMCalculator = fim_module.FIMCalculator
    return _FIMCalculator


def _lazy_import_gevp():
    """GEVPSolverを遅延インポート"""
    global _GEVPSolver
    if _GEVPSolver is None:
        # 親ディレクトリ（SST_merge）のsrc/gevp_solver.pyを明示的にロード
        sst_v2_root = Path(__file__).parent.parent  # sst_merge_v2ディレクトリ
        project_root = sst_v2_root.parent  # SST_mergeディレクトリ
        gevp_path = project_root / 'src' / 'gevp_solver.py'
        
        spec = importlib.util.spec_from_file_location("gevp_solver_module", gevp_path)
        gevp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gevp_module)
        _GEVPSolver = gevp_module.GEVPSolver
    return _GEVPSolver

from .layer_config import get_projection_strength, LAYER_PROJECTION_CONFIG

logger = logging.getLogger(__name__)


class SSTMergeV2:
    """
    SST-Merge V2: Safety-Preserving Subspace Task-Merge
    
    改善版アルゴリズム:
    1. FIM計算: F_utility, F_safety
    2. GEVP解法: Safety-addable subspace特定
    3. Layer-wise Soft Projection: 層ごとに射影強度を調整
    4. Residual Safety Injection: 元のSafety情報を一部保持
    5. 最終マージ: Utility + blended_safety
    """
    
    def __init__(
        self,
        k: int = 10,
        fim_approximation: str = "gradient_variance",
        regularization: float = 1e-6,
        device: str = "cuda",
        residual_ratio: float = 0.7,  # 元のSafety情報の保持率
        layer_config: Dict[str, float] = None,
        mode: str = "residual"  # "residual", "layerwise", "direct"
    ):
        """
        Args:
            k: 安全サブスペースの次元数
            fim_approximation: FIM近似手法
            regularization: 正則化項
            device: 計算デバイス
            residual_ratio: 元のSafety情報の保持率（0.0-1.0）
                - 0.0: 完全に射影（従来のSST-Merge）
                - 1.0: 射影なし（直接追加、ベースラインと同等）
                - 0.5-0.7: 推奨値（Safety保持しつつUtility干渉軽減）
            layer_config: 層別射影強度設定
            mode: マージモード
                - "residual": Residual Safety Injection（推奨）
                - "layerwise": Layer-wise Projection
                - "direct": 射影なしの直接追加（ベースライン相当）
        """
        self.k = k
        self.fim_approximation = fim_approximation
        self.regularization = regularization
        self.device = device
        self.residual_ratio = residual_ratio
        self.layer_config = layer_config or LAYER_PROJECTION_CONFIG
        self.mode = mode
        
        logger.info("=" * 60)
        logger.info("SST-Merge V2 Initialized")
        logger.info("=" * 60)
        logger.info(f"  k (subspace dim): {k}")
        logger.info(f"  residual_ratio: {residual_ratio}")
        logger.info(f"  mode: {mode}")
        logger.info("=" * 60)
    
    def merge_utility_safety(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader=None,
        safety_dataloader=None,
        max_samples: Optional[int] = 1000,
        safety_weight: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        Utility-Safety マージ（V2）
        
        Args:
            model: ベースモデル
            utility_adapters: Utilityアダプタのリスト [A5, A6, ...]
            safety_adapter: Safetyアダプタ (A7)
            utility_dataloader: Utilityデータ（FIM計算用、modeがdirectの場合は不要）
            safety_dataloader: Safetyデータ（FIM計算用、modeがdirectの場合は不要）
            max_samples: FIM計算に使用する最大サンプル数
            safety_weight: Safety追加の重み（1.0推奨）
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info("\n" + "=" * 70)
        logger.info("SST-MERGE V2: UTILITY-SAFETY MERGE")
        logger.info("=" * 70)
        logger.info(f"Utility adapters: {len(utility_adapters)}")
        logger.info(f"Safety adapter: 1")
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Safety weight: {safety_weight}")
        logger.info(f"Residual ratio: {self.residual_ratio}")
        
        # Mode: direct - 射影なしの直接追加
        if self.mode == "direct":
            return self._merge_direct(
                utility_adapters,
                safety_adapter,
                safety_weight
            )
        
        # Mode: residual or layerwise - 射影を使用
        if utility_dataloader is None or safety_dataloader is None:
            logger.warning("Dataloaders not provided. Falling back to direct mode.")
            return self._merge_direct(
                utility_adapters,
                safety_adapter,
                safety_weight
            )
        
        # FIM計算とGEVP解法
        safety_subspace = self._compute_safety_subspace(
            model,
            utility_adapters,
            safety_adapter,
            utility_dataloader,
            safety_dataloader,
            max_samples
        )
        
        if self.mode == "layerwise":
            return self._merge_layerwise(
                utility_adapters,
                safety_adapter,
                safety_subspace,
                safety_weight
            )
        else:  # residual
            return self._merge_residual(
                utility_adapters,
                safety_adapter,
                safety_subspace,
                safety_weight
            )
    
    def _compute_safety_subspace(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int
    ) -> torch.Tensor:
        """
        Safety追加可能サブスペースを計算
        """
        from peft import get_peft_model, LoraConfig, TaskType
        
        logger.info("\nStep 1: Computing FIMs...")
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            bias="none"
        )
        
        # Utility FIM計算
        F_utility = None
        for i, utility_adapter in enumerate(utility_adapters):
            logger.info(f"  Computing Utility FIM {i+1}/{len(utility_adapters)}...")
            
            peft_model = get_peft_model(model, lora_config)
            for name, param in peft_model.named_parameters():
                if name in utility_adapter:
                    param.data = utility_adapter[name].to(param.device)
            
            fim_calculator = _lazy_import_fim()(
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
        logger.info("  ✓ Utility FIM computed")
        
        # Safety FIM計算
        logger.info("  Computing Safety FIM...")
        peft_model = get_peft_model(model, lora_config)
        for name, param in peft_model.named_parameters():
            if name in safety_adapter:
                param.data = safety_adapter[name].to(param.device)
        
        FIMCalculatorClass = _lazy_import_fim()
        fim_calculator = FIMCalculatorClass(
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
        logger.info("  ✓ Safety FIM computed")
        
        # GEVP解法
        logger.info("\nStep 2: Solving GEVP...")
        gevp_solver = _lazy_import_gevp()(regularization=self.regularization)
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_safety, F_utility, k=self.k)
        safety_subspace = gevp_solver.select_safety_subspace(eigenvectors, k=self.k)
        
        logger.info(f"  Top eigenvalue: {eigenvalues[0].item():.6f}")
        logger.info(f"  Bottom eigenvalue: {eigenvalues[-1].item():.6f}")
        logger.info("  ✓ Safety subspace computed")
        
        return safety_subspace
    
    def _merge_direct(
        self,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        safety_weight: float
    ) -> Dict[str, torch.Tensor]:
        """
        直接追加モード（射影なし）
        
        merged = utility + safety_weight * safety
        
        ベースライン手法（Task Arithmetic）と同等の性能を確保
        """
        logger.info("\nStep 3: Direct Addition (no projection)...")
        
        # Utilityアダプターを平均化
        utility_merged = self._average_adapters(utility_adapters)
        
        merged = {}
        for key in utility_merged.keys():
            if key in safety_adapter:
                merged[key] = utility_merged[key] + safety_weight * safety_adapter[key]
            else:
                merged[key] = utility_merged[key]
        
        logger.info("  ✓ Direct merge completed")
        logger.info(f"  Formula: utility + {safety_weight} * safety")
        
        return merged
    
    def merge_utility_safety(
        self,
        model,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int = 1000,
        safety_weight: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        正しいSST-Merge実装（元のsst_merge.pyから移植）
        
        理論:
        1. FIM計算: F_utility, F_safety
        2. GEVP解決: 高固有値の固有ベクトルを取得
        3. Utility固定（タスク性能を維持）
        4. SafetyをUtility直交サブスペースに射影
        5. Utility + safety_weight * Safety（射影済み）を結合
        
        Args:
            model: ベースモデル（FIM計算用、Noneの場合はFIM計算をスキップ）
            utility_adapters: Utilityアダプタのリスト [A5, A6]
            safety_adapter: Safetyアダプタ (A7)
            utility_dataloader: Utilityデータローダー
            safety_dataloader: Safetyデータローダー
            max_samples: FIM計算に使用する最大サンプル数
            safety_weight: Safety追加の重み（デフォルト: 1.0）
        
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info("\n" + "="*70)
        logger.info("SST-Merge V2: Utility-Safety Merge")
        logger.info("="*70)
        
        # Step 1: Utilityアダプターを固定（平均化）
        logger.info("\nStep 1: Fixing Utility adapters (averaging)...")
        utility_merged = self._average_adapters(utility_adapters)
        logger.info("  ✓ Utility adapters fixed")
        
        # Step 2: FIM計算とGEVP解決（modelがある場合のみ）
        if model is not None and utility_dataloader is not None and safety_dataloader is not None:
            logger.info("\nStep 2: Computing FIM and solving GEVP...")
            safety_subspace = self._compute_safety_subspace(
                model,
                utility_adapters,
                safety_adapter,
                utility_dataloader,
                safety_dataloader,
                max_samples
            )
            logger.info(f"  ✓ Safety subspace computed (k={self.k})")
        else:
            logger.warning("\nStep 2: Skipping FIM computation (model or dataloaders not provided)")
            logger.warning("  Using identity projection (no subspace filtering)")
            # FIMなしの場合は、単純なマージ
            merged = {}
            for key in utility_merged.keys():
                if key in safety_adapter:
                    merged[key] = utility_merged[key] + safety_weight * safety_adapter[key]
                else:
                    merged[key] = utility_merged[key]
            return merged
        
        # Step 3: SafetyアダプターをUtility直交サブスペースに射影
        logger.info("\nStep 3: Projecting Safety adapter to Utility-orthogonal subspace...")
        safety_projected = self._project_to_safety_subspace(
            [safety_adapter],
            safety_subspace
        )
        logger.info("  ✓ Safety adapter projected")
        
        # Step 4: Utility (固定) + Safety (射影) を結合
        logger.info(f"\nStep 4: Combining Utility (fixed) + Safety (projected)...")
        logger.info(f"  Safety weight: {safety_weight}")
        merged = {}
        for key in utility_merged.keys():
            if key in safety_projected:
                # 加算ベース: Utility + safety_weight * Safety
                merged[key] = utility_merged[key] + safety_weight * safety_projected[key]
            else:
                merged[key] = utility_merged[key]
        
        logger.info("  ✓ Adapters combined")
        logger.info(f"\n  Formula: utility + {safety_weight} * safety_projected")
        logger.info("  Expected result: Utility maintained, Safety improved")
        logger.info("="*70)
        
        return merged
    
    def _merge_layerwise(
        self,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        safety_subspace: torch.Tensor,
        safety_weight: float
    ) -> Dict[str, torch.Tensor]:
        """
        Layer-wise Soft Projection
        
        層ごとに異なる射影強度を適用:
        soft_projected = (1 - strength) * original + strength * projected
        merged = utility + safety_weight * soft_projected
        """
        logger.info("\nStep 3: Layer-wise Soft Projection...")
        
        # Utilityアダプターを平均化
        utility_merged = self._average_adapters(utility_adapters)
        
        merged = {}
        for key in utility_merged.keys():
            if key in safety_adapter:
                # 層ごとの射影強度を取得
                strength = get_projection_strength(key, self.layer_config)
                
                # ソフト射影
                original = safety_adapter[key]
                projected = self._project_param(original, safety_subspace)
                
                # soft_projected = (1 - strength) * original + strength * projected
                soft_projected = (1 - strength) * original + strength * projected
                
                merged[key] = utility_merged[key] + safety_weight * soft_projected
                
                logger.debug(f"    {key}: strength={strength:.2f}")
            else:
                merged[key] = utility_merged[key]
        
        logger.info("  ✓ Layer-wise merge completed")
        
        return merged
    
    def _project_adapter(
        self,
        adapter: Dict[str, torch.Tensor],
        safety_subspace: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        アダプター全体を射影
        """
        projected = {}
        for key, param in adapter.items():
            projected[key] = self._project_param(param, safety_subspace)
        return projected
    
    def _project_to_safety_subspace(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        safety_subspace: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        アダプターリストを安全サブスペースに射影
        
        Args:
            adapters: アダプターのリスト
            safety_subspace: 安全サブスペース（高固有値の固有ベクトル）
        
        Returns:
            projected: 射影されたアダプター
        """
        # アダプターを平均化
        adapter_avg = self._average_adapters(adapters)
        
        # 各パラメータを射影
        projected = {}
        for key, param in adapter_avg.items():
            projected[key] = self._project_param(param, safety_subspace)
        
        return projected
    
    def _project_param(
        self,
        param: torch.Tensor,
        safety_subspace: torch.Tensor
    ) -> torch.Tensor:
        """
        単一パラメータを射影
        
        φ_projected = V_k V_k^T φ
        """
        original_shape = param.shape
        param_flat = param.flatten()
        param_size = param_flat.size(0)
        
        # safety_subspaceをparamと同じデバイスに移動
        safety_subspace = safety_subspace.to(param_flat.device)
        
        if param_size <= safety_subspace.size(0):
            subspace_subset = safety_subspace[:param_size, :]
            
            # 射影: V @ (V^T @ x)
            coefficients = torch.matmul(subspace_subset.T, param_flat)
            projected_flat = torch.matmul(subspace_subset, coefficients)
        else:
            # パラメータが大きすぎる場合はチャンク処理
            subspace_size = safety_subspace.size(0)
            num_chunks = (param_size + subspace_size - 1) // subspace_size
            
            projected_chunks = []
            for i in range(num_chunks):
                start_idx = i * subspace_size
                end_idx = min((i + 1) * subspace_size, param_size)
                chunk = param_flat[start_idx:end_idx]
                
                chunk_size = chunk.size(0)
                subspace_chunk = safety_subspace[:chunk_size, :]
                
                coefficients = torch.matmul(subspace_chunk.T, chunk)
                projected_chunk = torch.matmul(subspace_chunk, coefficients)
                projected_chunks.append(projected_chunk)
            
            projected_flat = torch.cat(projected_chunks)
        
        return projected_flat.reshape(original_shape)
    
    def _average_adapters(
        self,
        adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """
        複数アダプターを平均化
        """
        if not adapters:
            raise ValueError("No adapters provided")
        
        if len(adapters) == 1:
            return {k: v.clone() for k, v in adapters[0].items()}
        
        averaged = {}
        for key in adapters[0].keys():
            params = [adapter[key] for adapter in adapters]
            averaged[key] = torch.stack(params).mean(dim=0)
        
        return averaged
    
    def save_merged_adapter(
        self,
        merged_adapter: Dict[str, torch.Tensor],
        save_path: str,
        metadata: Dict = None
    ):
        """
        マージされたアダプターを保存
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_dict = {
            'adapter': merged_adapter,
            'metadata': metadata or {},
            'config': {
                'k': self.k,
                'residual_ratio': self.residual_ratio,
                'mode': self.mode,
                'layer_config': self.layer_config,
            }
        }
        
        torch.save(save_dict, save_path)
        logger.info(f"✓ Merged adapter saved to {save_path}")


def test_sst_merge_v2():
    """簡易テスト"""
    logger.info("Testing SST-Merge V2...")
    
    # ダミーアダプター
    utility_adapters = [
        {'layer.lora_A': torch.randn(8, 64), 'layer.lora_B': torch.randn(64, 8)},
        {'layer.lora_A': torch.randn(8, 64), 'layer.lora_B': torch.randn(64, 8)},
    ]
    safety_adapter = {
        'layer.lora_A': torch.randn(8, 64),
        'layer.lora_B': torch.randn(64, 8),
    }
    
    # Direct mode テスト
    merger = SSTMergeV2(k=5, mode="direct", device="cpu")
    merged = merger.merge_utility_safety(
        model=None,
        utility_adapters=utility_adapters,
        safety_adapter=safety_adapter,
        safety_weight=1.0
    )
    
    logger.info(f"Merged adapter keys: {list(merged.keys())}")
    logger.info("✓ Test passed!")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_sst_merge_v2()
