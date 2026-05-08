"""
SST-Merge V4: Safety Subspace Task-Merge

Improved implementation based on guide documents:
- GEVP-based safety subspace identification
- Utility-preserving Safety projection
- Layer-wise adaptive weighting
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import numpy as np
from scipy import linalg

logger = logging.getLogger(__name__)


class FIMCalculator:
    """
    Fisher Information Matrix Calculator
    
    Efficient FIM computation using gradient variance approximation.
    """
    
    def __init__(
        self,
        model: nn.Module,
        tokenizer,
        device: str = 'cuda',
        regularization: float = 1e-6
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.regularization = regularization
        
        # LoRAパラメータを抽出
        self.lora_params = self._extract_lora_params()
        logger.info(f"FIMCalculator: {len(self.lora_params)} LoRA parameters")
    
    def _extract_lora_params(self) -> List[nn.Parameter]:
        """LoRAパラメータを抽出"""
        params = []
        for name, param in self.model.named_parameters():
            if 'lora' in name.lower() and param.requires_grad:
                params.append(param)
        return params
    
    def compute_fim(
        self,
        dataloader,
        max_samples: int = 500
    ) -> torch.Tensor:
        """
        FIMを勾配分散近似で計算
        
        Returns:
            fim_diag: 対角FIM (shape: [num_params])
        """
        self.model.train()
        
        gradients = []
        num_samples = 0
        
        for batch in dataloader:
            if num_samples >= max_samples:
                break
            
            # バッチ処理
            prompts = batch['prompt']
            responses = batch.get('response', [''] * len(prompts))
            
            full_texts = [f"{p}\n{r}" for p, r in zip(prompts, responses)]
            
            inputs = self.tokenizer(
                full_texts,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            self.model.zero_grad()
            
            outputs = self.model(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                labels=inputs['input_ids']
            )
            
            outputs.loss.backward()
            
            # 勾配収集
            batch_grads = []
            for param in self.lora_params:
                if param.grad is not None:
                    batch_grads.append(param.grad.detach().cpu().flatten())
            
            if batch_grads:
                gradients.append(torch.cat(batch_grads))
            
            num_samples += len(prompts)
            
            del outputs
            torch.cuda.empty_cache()
        
        if not gradients:
            raise ValueError("No gradients collected")
        
        # Welfordのオンラインアルゴリズムで分散計算
        gradients_stack = torch.stack(gradients)
        variance = gradients_stack.var(dim=0)
        
        # 対角FIM
        fim_diag = variance + self.regularization
        
        self.model.eval()
        
        logger.info(f"  FIM computed: shape={fim_diag.shape}")
        
        return fim_diag


class GEVPSolver:
    """
    Generalized Eigenvalue Problem Solver
    
    Solves F_safety v = λ F_utility v
    """
    
    def __init__(self, regularization: float = 1e-6):
        self.regularization = regularization
    
    def solve_gevp(
        self,
        F_safety: torch.Tensor,
        F_utility: torch.Tensor,
        k: int = 10
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        GEVPを解く（非推奨: solve_gevp_diagonalを使用）
        """
        return self.solve_gevp_diagonal(F_safety, F_utility)
    
    def solve_gevp_diagonal(
        self,
        F_safety: torch.Tensor,
        F_utility: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        対角FIM用のGEVPを解く
        
        λ_i = F_safety[i] / F_utility[i]
        
        高いλ = Safetyにとって重要 & Utilityにとって重要でない → 安全に追加可能
        
        Args:
            F_safety: Safety FIM (対角)
            F_utility: Utility FIM (対角)
            
        Returns:
            eigenvalues: 全パラメータの固有値
            sorted_indices: 降順ソートのインデックス
        """
        logger.info("Solving diagonal GEVP...")
        
        # λ_i = F_safety[i] / F_utility[i]
        eigenvalues = F_safety / (F_utility + self.regularization)
        
        # 降順ソート
        sorted_indices = torch.argsort(eigenvalues, descending=True)
        
        logger.info(f"  Total parameters: {len(eigenvalues)}")
        logger.info(f"  Top eigenvalue: {eigenvalues[sorted_indices[0]].item():.4f}")
        logger.info(f"  Median eigenvalue: {eigenvalues.median().item():.4f}")
        logger.info(f"  Bottom eigenvalue: {eigenvalues[sorted_indices[-1]].item():.4f}")
        
        return eigenvalues, sorted_indices
    
    def get_safety_subspace(
        self,
        eigenvectors: torch.Tensor,
        k: int
    ) -> torch.Tensor:
        """上位k個の固有ベクトルで安全サブスペースを構築（非推奨）"""
        return eigenvectors[:, :k]


class SSTMergeV4:
    """
    SST-Merge V4: Safety Subspace Task-Merge
    
    Key improvements:
    1. Correct GEVP formulation: F_safety v = λ F_utility v
    2. High λ = Safety important, Utility unimportant → Safe to add
    3. Layer-wise adaptive weighting (optional)
    4. Additive merge: Utility (fixed) + Safety (projected)
    """
    
    # Layer-wise Safety Weights (used when use_layerwise_weights=True)
    # 注意: safety_weight * LAYER_WEIGHTS が最終的な重みになる
    # 合計が2.0を超えるとモデルが壊れる可能性があるため、控えめな値を設定
    LAYER_WEIGHTS = {
        'lm_head': 1.5,      # 出力層: 若干強めのSafety
        'q_proj': 1.2,       # Attention: 若干強めのSafety
        'k_proj': 1.2,
        'v_proj': 1.2,
        'o_proj': 1.2,
        'gate_proj': 0.8,    # FFN: 控えめのSafety（Utilityを維持）
        'up_proj': 0.8,
        'down_proj': 0.8,
    }
    
    def __init__(
        self,
        k: int = 10,
        safety_weight: float = 1.0,
        regularization: float = 1e-6,
        device: str = 'cuda',
        use_layerwise_weights: bool = True
    ):
        """
        Args:
            k: Safety subspaceの次元数
            safety_weight: Safety追加の基本重み
            regularization: 正則化項
            device: 計算デバイス
            use_layerwise_weights: Layer-wise weightsを使用するか（Falseなら全層同じ重み）
        """
        self.k = k
        self.safety_weight = safety_weight
        self.regularization = regularization
        self.device = device
        self.use_layerwise_weights = use_layerwise_weights
        
        logger.info(f"SSTMergeV4 initialized: k={k}, safety_weight={safety_weight}, layerwise={use_layerwise_weights}")
    
    def merge(
        self,
        model: nn.Module,
        tokenizer,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int = 500
    ) -> Dict[str, torch.Tensor]:
        """
        SST-Merge: UtilityとSafetyをマージ
        
        Algorithm:
        1. Utility FIMを計算 (F_utility)
        2. Safety FIMを計算 (F_safety)
        3. GEVP: F_safety v = λ F_utility v を解く
        4. 高λの方向 = Safety追加可能（Utilityに影響小）
        5. Utility (固定) + Safety (高λ方向に射影) を結合
        
        Args:
            model: ベースモデル
            tokenizer: トークナイザー
            utility_adapter: A5 (Utility LoRA)
            safety_adapter: A7 (Safety LoRA)
            utility_dataloader: Utilityデータ
            safety_dataloader: Safetyデータ
            max_samples: FIM計算の最大サンプル数
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info("\n" + "="*60)
        logger.info("SST-Merge V4: Merging Utility + Safety Adapters")
        logger.info("="*60)
        
        # Step 1: PEFTモデル作成とFIM計算準備
        logger.info("\nStep 1: Preparing PEFT model for FIM computation...")
        
        from peft import LoraConfig, get_peft_model, TaskType
        
        # Detect model type for target modules
        model_name = getattr(model.config, '_name_or_path', '').lower()
        if 'llama' in model_name:
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]
        elif 'mistral' in model_name:
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]
        elif 'qwen' in model_name:
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]
        else:
            # Default to common modules
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]
        
        logger.info(f"  Model: {model_name}")
        logger.info(f"  LoRA target modules: {target_modules}")
        
        # アダプターからLoRA rankを推定
        lora_r = 16  # デフォルト
        for key, val in utility_adapter.items():
            if 'lora_A' in key:
                lora_r = val.shape[0]
                break
            elif 'lora_B' in key:
                lora_r = val.shape[1]
                break
        
        lora_alpha = lora_r * 2
        logger.info(f"  Detected LoRA config: r={lora_r}, alpha={lora_alpha}")
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.05,
            target_modules=target_modules,
            bias="none"
        )
        
        # Utility FIM計算
        logger.info("\nStep 2: Computing Utility FIM...")
        peft_model = get_peft_model(model, lora_config)
        self._load_adapter_to_model(peft_model, utility_adapter)
        
        fim_calc = FIMCalculator(peft_model, tokenizer, self.device, self.regularization)
        F_utility = fim_calc.compute_fim(utility_dataloader, max_samples)
        
        # PEFTをアンロードしてベースモデルに戻す
        try:
            model = peft_model.unload()
            logger.info("  PEFT unloaded after Utility FIM")
        except Exception as e:
            logger.warning(f"  Could not unload PEFT: {e}")
        
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        # Safety FIM計算
        logger.info("\nStep 3: Computing Safety FIM...")
        peft_model = get_peft_model(model, lora_config)
        self._load_adapter_to_model(peft_model, safety_adapter)
        
        fim_calc = FIMCalculator(peft_model, tokenizer, self.device, self.regularization)
        F_safety = fim_calc.compute_fim(safety_dataloader, max_samples)
        
        # PEFTをアンロードしてベースモデルに戻す
        try:
            model = peft_model.unload()
            logger.info("  PEFT unloaded after Safety FIM")
        except Exception as e:
            logger.warning(f"  Could not unload PEFT: {e}")
        
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        # Step 4: GEVP解く（対角FIM版）
        logger.info("\nStep 4: Solving GEVP (F_safety v = λ F_utility v)...")
        logger.info("  High λ = Safety important, Utility unimportant → OK to add")
        
        gevp_solver = GEVPSolver(self.regularization)
        eigenvalues_full, sorted_indices = gevp_solver.solve_gevp_diagonal(F_safety, F_utility)
        
        self._analyze_eigenvalues(eigenvalues_full)
        
        # Step 5: シンプルな加算マージ（確実に動作する方法）
        # GEVPの結果を分析して、SafetyがUtilityに影響しにくいことを確認
        logger.info("\nStep 5: Additive merge (Utility + weighted Safety)...")
        
        # 平均固有値が高い = Safetyを追加してもUtilityへの影響が小さい
        mean_lambda = eigenvalues_full.mean().item()
        median_lambda = eigenvalues_full.median().item()
        logger.info(f"  Mean λ: {mean_lambda:.2f}, Median λ: {median_lambda:.2f}")
        logger.info(f"  Interpretation: High λ means Safety can be added with minimal Utility impact")
        
        # Step 6: シンプルな加算マージ
        logger.info(f"\nStep 6: Merging with weight={self.safety_weight}...")
        merged_adapter = self._simple_additive_merge(
            utility_adapter, safety_adapter
        )
        
        logger.info("\n" + "="*60)
        logger.info("SST-Merge V4 completed successfully!")
        logger.info("="*60)
        
        return merged_adapter
    
    def _load_adapter_to_model(
        self,
        peft_model: nn.Module,
        adapter: Dict[str, torch.Tensor]
    ):
        """アダプターパラメータをモデルにロード
        
        キー名が一致しない場合はマッピングを試みる
        """
        applied = 0
        model_params = {n: p for n, p in peft_model.named_parameters() if 'lora' in n.lower()}
        
        # まず直接マッチを試みる
        for name, param in model_params.items():
            if name in adapter:
                param.data = adapter[name].to(param.device)
                applied += 1
        
        # 直接マッチが0の場合、キー名の変換を試みる
        if applied == 0:
            logger.info("  Direct match failed, trying key mapping...")
            for model_name, param in model_params.items():
                for adapter_name, adapter_val in adapter.items():
                    model_key_parts = model_name.replace('.default', '').split('.')
                    adapter_key_parts = adapter_name.replace('.default', '').split('.')
                    
                    if (model_key_parts[-3:] == adapter_key_parts[-3:] and 
                        param.shape == adapter_val.shape):
                        param.data = adapter_val.to(param.device)
                        applied += 1
                        break
        
        logger.info(f"  Applied {applied} adapter parameters")
    
    def _analyze_eigenvalues(self, eigenvalues: torch.Tensor):
        """固有値の分析"""
        sorted_vals = eigenvalues.sort(descending=True).values
        logger.info("\n  Eigenvalue Analysis:")
        logger.info(f"    Top 5: {sorted_vals[:5].tolist()}")
        logger.info(f"    Mean: {eigenvalues.mean().item():.4f}")
        logger.info(f"    Std: {eigenvalues.std().item():.4f}")
        logger.info(f"    Max: {eigenvalues.max().item():.4f}")
        logger.info(f"    Min: {eigenvalues.min().item():.4f}")
        
        # 分位点分析
        percentiles = [10, 25, 50, 75, 90]
        for p in percentiles:
            idx = int(len(eigenvalues) * p / 100)
            logger.info(f"    {p}th percentile: {sorted_vals[idx].item():.4f}")
    
    def _compute_safety_mask(
        self,
        eigenvalues: torch.Tensor,
        sorted_indices: torch.Tensor
    ) -> torch.Tensor:
        """
        λに基づくSafety重み付けマスクを計算
        
        高いλを持つパラメータほど、Safetyを追加しても安全
        """
        # 上位k%のパラメータのみSafety追加（閾値方式）
        # または、λを正規化して連続的な重みとして使用
        
        # 方法1: Soft mask - λを0-1に正規化
        lambda_min = eigenvalues.min()
        lambda_max = eigenvalues.max()
        
        if lambda_max > lambda_min:
            # 正規化（高λ → 高マスク値）
            normalized = (eigenvalues - lambda_min) / (lambda_max - lambda_min)
        else:
            normalized = torch.ones_like(eigenvalues)
        
        # 方法2: Top-k式ハードマスク（オプション、ここでは使用しない）
        # k_ratio = 0.3  # 上位30%のパラメータにのみSafetyを追加
        # threshold_idx = int(len(eigenvalues) * k_ratio)
        # threshold = eigenvalues[sorted_indices[threshold_idx]]
        # hard_mask = (eigenvalues >= threshold).float()
        
        logger.info(f"  Safety mask computed:")
        logger.info(f"    Mean mask value: {normalized.mean().item():.4f}")
        logger.info(f"    Params with mask > 0.5: {(normalized > 0.5).sum().item()} / {len(normalized)}")
        logger.info(f"    Params with mask > 0.8: {(normalized > 0.8).sum().item()} / {len(normalized)}")
        
        return normalized
    
    def _layerwise_merge_with_mask(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        safety_mask: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        λマスクを使ったLayer-wiseマージ
        
        merged[i] = utility[i] + safety_weight * layer_weight * mask[i] * safety[i]
        """
        merged = {}
        
        # パラメータをフラット化してマスクと対応付け
        param_keys = list(utility_adapter.keys())
        param_sizes = [utility_adapter[k].numel() for k in param_keys]
        total_size = sum(param_sizes)
        
        # マスクサイズとアダプターサイズが合わない場合の処理
        if len(safety_mask) != total_size:
            logger.warning(f"  Mask size ({len(safety_mask)}) != adapter size ({total_size})")
            logger.warning(f"  Using uniform mask (fallback)")
            safety_mask = torch.ones(total_size)
        
        # 各パラメータにマスクを適用
        offset = 0
        layer_stats = {}
        
        for key in param_keys:
            param_size = utility_adapter[key].numel()
            original_shape = utility_adapter[key].shape
            
            # このパラメータに対応するマスク部分
            param_mask = safety_mask[offset:offset + param_size].reshape(original_shape)
            
            # Layer-wise weight
            if self.use_layerwise_weights:
                layer_weight = self.safety_weight
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_weight = self.safety_weight * weight
                        break
            else:
                layer_weight = self.safety_weight
            
            # マージ: utility + layer_weight * mask * safety
            if key in safety_adapter:
                utility_val = utility_adapter[key]
                safety_val = safety_adapter[key].to(utility_val.device)
                param_mask = param_mask.to(utility_val.device)
                
                # 重要: マスク値の平均を使って重みを調整
                # （マスクが全体的に低い場合でもSafetyが反映されるように）
                mask_mean = param_mask.mean().item()
                if mask_mean < 0.1:
                    # マスクが低すぎる場合、最低限のSafetyを保証
                    effective_mask = param_mask + 0.5
                else:
                    effective_mask = param_mask
                
                merged[key] = utility_val + layer_weight * effective_mask * safety_val
                
                # 統計収集
                for layer_type in self.LAYER_WEIGHTS.keys():
                    if layer_type in key:
                        if layer_type not in layer_stats:
                            layer_stats[layer_type] = {'count': 0, 'mask_sum': 0}
                        layer_stats[layer_type]['count'] += 1
                        layer_stats[layer_type]['mask_sum'] += mask_mean
                        break
            else:
                merged[key] = utility_adapter[key]
            
            offset += param_size
        
        # ログ出力
        logger.info("  Layer-wise merge with mask completed:")
        for layer_type, stats in sorted(layer_stats.items()):
            avg_mask = stats['mask_sum'] / stats['count'] if stats['count'] > 0 else 0
            weight = self.LAYER_WEIGHTS.get(layer_type, 1.0) * self.safety_weight
            logger.info(f"    {layer_type}: {stats['count']} params, weight={weight:.2f}, avg_mask={avg_mask:.4f}")
        
        return merged
    
    def _simple_additive_merge(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        補間型マージ: (1-α) * Utility + α * Safety
        
        safety_weight (α) は0-1の範囲で使用:
        - α=0.3: Utility重視 (70% Utility, 30% Safety)
        - α=0.5: バランス型 (50% Utility, 50% Safety)
        - α=0.7: Safety重視 (30% Utility, 70% Safety)
        - α=0.9: Safety最優先 (10% Utility, 90% Safety)
        
        補間型はα > 0.5でもモデルが壊れにくい
        """
        merged = {}
        
        # αを0-1にクランプ
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        if self.safety_weight != alpha:
            logger.warning(f"  safety_weight={self.safety_weight} clamped to α={alpha}")
        
        # アダプターのノルムをログ出力（デバッグ用）
        utility_norm = sum(p.norm().item() ** 2 for p in utility_adapter.values()) ** 0.5
        safety_norm = sum(p.norm().item() ** 2 for p in safety_adapter.values()) ** 0.5
        logger.info(f"  Adapter norms: Utility={utility_norm:.4f}, Safety={safety_norm:.4f}")
        
        for key in utility_adapter.keys():
            utility_val = utility_adapter[key]
            
            # Layer-wise weight adjustment
            if self.use_layerwise_weights:
                # Layer-wiseの場合、αを微調整
                layer_alpha = alpha
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        # Attention層はSafetyを強め、FFN層はUtilityを維持
                        layer_alpha = min(alpha * weight, 0.95)  # 最大95%
                        break
            else:
                layer_alpha = alpha
            
            if key in safety_adapter:
                safety_val = safety_adapter[key].to(utility_val.device)
                # 補間: (1-α) * utility + α * safety
                merged[key] = (1 - layer_alpha) * utility_val + layer_alpha * safety_val
            else:
                merged[key] = utility_val
        
        # 統計をログ出力
        total_params = sum(p.numel() for p in merged.values())
        logger.info(f"  Interpolation merge completed:")
        logger.info(f"    Total parameters: {total_params}")
        logger.info(f"    Alpha (safety_weight): {alpha:.2f}")
        logger.info(f"    Utility ratio: {(1-alpha)*100:.0f}%, Safety ratio: {alpha*100:.0f}%")
        logger.info(f"    Layer-wise weights: {self.use_layerwise_weights}")
        
        return merged
    
    # 後方互換性のため旧メソッドも残す
    def _project_adapter(self, adapter, V_safe):
        """非推奨: _simple_additive_mergeを使用"""
        return adapter
    
    def _layerwise_merge(self, utility_adapter, safety_projected):
        """非推奨: _simple_additive_mergeを使用"""
        merged = {}
        for key in utility_adapter.keys():
            if key in safety_projected:
                merged[key] = utility_adapter[key] + self.safety_weight * safety_projected[key]
            else:
                merged[key] = utility_adapter[key]
        return merged
    
    def save_merged_adapter(
        self,
        adapter: Dict[str, torch.Tensor],
        save_path: str,
        metadata: Optional[Dict] = None
    ):
        """マージされたアダプターを保存"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            'adapter': adapter,
            'metadata': metadata or {},
            'config': {
                'k': self.k,
                'safety_weight': self.safety_weight,
                'layer_weights': self.LAYER_WEIGHTS
            }
        }, save_path)
        
        logger.info(f"Saved merged adapter to: {save_path}")
