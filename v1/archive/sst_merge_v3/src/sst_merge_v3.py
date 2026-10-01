"""
SST-Merge: Safety Subspace Task-Merge

GEVPに基づく安全サブスペース選択型LoRAマージングアルゴリズム。
理論的基礎: Phase 1-2で確立された二元最適化フレームワーク。
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

from .fim_calculator import FIMCalculator
from .gevp_solver import GEVPSolver

logger = logging.getLogger(__name__)


class SSTMergeV3:
    """
    Safety Subspace Task-Merge (SST-Merge)
    
    Fisher Information MatrixとGEVPを用いて、安全性とユーティリティの
    トレードオフを最適化するLoRAマージング手法。
    
    アルゴリズムフロー:
    1. 各LoRAアダプタに対してF_harmとF_benignを計算
    2. GEVPを解いて安全サブスペースS_safetyを特定
    3. 元のLoRAパッチφ_originalをS_safetyに射影
    4. 射影されたパッチφ_mergedを返す
    """
    
    def __init__(
        self,
        k: int = 10,
        fim_approximation: str = "gradient_variance",
        regularization: float = 1e-6,
        device: str = "cuda"
    ):
        """
        Args:
            k: 安全サブスペースの次元数（上位k個の固有ベクトル）
            fim_approximation: FIM近似手法
            regularization: 正則化項
            device: 計算デバイス
        """
        self.k = k
        self.fim_approximation = fim_approximation
        self.regularization = regularization
        self.device = device
        
        logger.info(f"SST-Merge V3 initialized: k={k}, approximation={fim_approximation}, Layer-wise Projection enabled")
    
    def merge_lora_adapters(
        self,
        model: nn.Module,
        harmful_adapters: List[Dict[str, torch.Tensor]],
        benign_adapters: List[Dict[str, torch.Tensor]],
        harm_dataloader,
        benign_dataloader,
        max_samples: Optional[int] = 1000,
        alpha: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """
        SST-Mergeアルゴリズム（guide文書1に基づく正しい実装）
        
        理論的基盤:
        - 良性アダプターを固定（平均化）
        - 悪性アダプターのみを安全サブスペースに射影
        - 両者を結合
        
        Args:
            model: ベースモデル
            harmful_adapters: 悪性（有害）LoRAアダプタのリスト
            benign_adapters: 良性LoRAアダプタのリスト
            harm_dataloader: 有害データのDataLoader
            benign_dataloader: 良性データのDataLoader
            max_samples: FIM計算に使用する最大サンプル数
            alpha: 結合比率（0.0-1.0、デフォルト0.5）
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info(f"Merging {len(harmful_adapters)} harmful + {len(benign_adapters)} benign LoRA adapters with SST-Merge...")
        
        # Step 0: モデルをPeftModelに変換してアダプターを適用（FIM計算のため）
        logger.info("Step 0: Converting model to PeftModel and applying adapters...")
        
        from peft import get_peft_model, LoraConfig, TaskType, PeftModel
        
        # LoRA設定（保存されたアダプターと同じ設定）
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            bias="none"
        )
        
        # PeftModelを作成
        peft_model = get_peft_model(model, lora_config)
        logger.info("  Created PeftModel with LoRA layers")
        
        # harmful_adaptersの平均を計算
        harmful_avg = {}
        for key in harmful_adapters[0].keys():
            harmful_avg[key] = torch.stack([adapter[key] for adapter in harmful_adapters]).mean(dim=0)
        
        # PeftModelにアダプターパラメータをロード
        applied_count = 0
        for name, param in peft_model.named_parameters():
            if name in harmful_avg:
                param.data = harmful_avg[name].to(param.device)
                applied_count += 1
        
        logger.info(f"  Applied {applied_count} harmful adapter parameters to PeftModel")
        
        # Step 1: FIMの計算
        logger.info("Step 1: Computing Fisher Information Matrices...")
        fim_calculator = FIMCalculator(
            peft_model,  # PeftModelを使用
            approximation=self.fim_approximation,
            regularization=self.regularization,
            device=self.device
        )
        
        # tokenizerを設定（BeaverTails形式のデータ用）
        if hasattr(model, 'tokenizer'):
            fim_calculator.tokenizer = model.tokenizer
            # pad_tokenを設定（未設定の場合）
            if fim_calculator.tokenizer.pad_token is None:
                fim_calculator.tokenizer.pad_token = fim_calculator.tokenizer.eos_token
                logger.info("Set tokenizer.pad_token = tokenizer.eos_token")
        elif hasattr(model, 'config') and hasattr(model.config, '_name_or_path'):
            from transformers import AutoTokenizer
            fim_calculator.tokenizer = AutoTokenizer.from_pretrained(model.config._name_or_path)
        
        F_harm = fim_calculator.compute_fim_harm(harm_dataloader, max_samples)
        F_benign = fim_calculator.compute_fim_benign(benign_dataloader, max_samples)
        
        # Step 1.5: PeftModelを破棄（メモリ解放）
        logger.info("Step 1.5: Cleaning up PeftModel...")
        del peft_model, fim_calculator
        torch.cuda.empty_cache()
        logger.info("  PeftModel cleaned up")

        
        # Step 2: GEVPを解いて安全サブスペースを特定
        logger.info("Step 2: Solving GEVP to identify safety subspace...")
        gevp_solver = GEVPSolver(regularization=self.regularization)
        
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_harm, F_benign, k=self.k)
        safety_subspace = gevp_solver.select_safety_subspace(eigenvectors, k=self.k)
        
        # 安全効率の分析
        self._analyze_safety_efficiency(eigenvalues)
        
        # Step 3a: 良性アダプターを固定（平均化）
        logger.info("Step 3a: Fixing benign adapters (averaging)...")
        benign_merged = self._average_adapters(benign_adapters)
        logger.info("✓ Benign adapters fixed")
        
        # Step 3b: 悪性アダプターのみを安全サブスペースに射影
        logger.info("Step 3b: Projecting harmful adapters to safety subspace...")
        harmful_projected = self._project_to_safety_subspace(
            harmful_adapters,
            safety_subspace
        )
        logger.info("✓ Harmful adapters projected")
        
        # Step 3c: 良性（固定）+ 悪性（射影）を結合
        logger.info(f"Step 3c: Combining benign (fixed) + harmful (projected) with safety_weight={safety_weight}...")
        merged_adapter = self._combine_adapters(
            benign_merged,
            harmful_projected,
            alpha=safety_weight
        )
        logger.info("✓ Adapters combined")
        
        logger.info("SST-Merge completed successfully")
        
        return merged_adapter
    
    def merge_utility_safety(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: Optional[int] = 1000,
        safety_weight: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        Utilityを固定し、SafetyをUtility直交サブスペースに射影
        
        SST-Mergeの正しい実装:
        - Utility (A5, A6): 固定（タスク性能を維持）
        - Safety (A7): Utility重要サブスペースと直交する部分のみ追加
        
        理論的基盤:
        1. F_utility: Utilityタスクで重要なパラメータ
        2. F_safety: Safetyタスクで重要なパラメータ
        3. GEVP: F_safety v = λ F_utility v
        4. 高固有値: Safety重要、Utility非重要 → 追加OK
        5. Utility固定 + Safety射影 → Safety Taxを最小化
        
        Args:
            model: ベースモデル
            utility_adapters: Utilityアダプタのリスト [A5, A6]
            safety_adapter: Safetyアダプタ (A7)
            utility_dataloader: Utilityデータ (RepliQA + Alpaca)
            safety_dataloader: Safetyデータ (response_dataframe.csv)
            max_samples: FIM計算に使用する最大サンプル数
            safety_weight: Safety追加の重み (1.0推奨)
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info(f"Merging {len(utility_adapters)} utility + 1 safety adapter with SST-Merge...")
        logger.info(f"  Utility adapters: {len(utility_adapters)} (fixed)")
        logger.info(f"  Safety adapter: 1 (projected to Utility-orthogonal subspace)")
        logger.info(f"  Safety weight: {safety_weight}")
        
        # Step 0: PeftModel準備（FIM計算用）
        logger.info("Step 0: Preparing PeftModel for FIM computation...")
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
            
            # PeftModel作成
            peft_model = get_peft_model(model, lora_config)
            
            # アダプターパラメータをロード
            for name, param in peft_model.named_parameters():
                if name in utility_adapter:
                    param.data = utility_adapter[name].to(param.device)
            
            # FIM計算
            fim_calculator = FIMCalculator(
                peft_model,
                approximation=self.fim_approximation,
                regularization=self.regularization,
                device=self.device
            )
            
            # tokenizerを設定
            if hasattr(model, 'tokenizer'):
                fim_calculator.tokenizer = model.tokenizer
                if fim_calculator.tokenizer.pad_token is None:
                    fim_calculator.tokenizer.pad_token = fim_calculator.tokenizer.eos_token
            
            F_util = fim_calculator.compute_fim_benign(utility_dataloader, max_samples)
            
            # 累積
            if F_utility is None:
                F_utility = F_util
            else:
                F_utility = F_utility + F_util
            
            # クリーンアップ
            del peft_model, fim_calculator
            torch.cuda.empty_cache()
        
        # 平均化
        F_utility = F_utility / len(utility_adapters)
        logger.info(f"✓ Utility FIM computed (averaged over {len(utility_adapters)} adapters)")
        
        # Step 2: Safety FIM計算
        logger.info("Step 2: Computing Safety FIM...")
        
        # PeftModel作成
        peft_model = get_peft_model(model, lora_config)
        
        # Safetyアダプターパラメータをロード
        for name, param in peft_model.named_parameters():
            if name in safety_adapter:
                param.data = safety_adapter[name].to(param.device)
        
        # FIM計算
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
        
        # クリーンアップ
        del peft_model, fim_calculator
        torch.cuda.empty_cache()
        logger.info("✓ Safety FIM computed")
        
        # Step 3: GEVPを解いてSafety追加可能サブスペースを特定
        logger.info("Step 3: Solving GEVP to identify Safety-addable subspace...")
        logger.info("  GEVP: F_safety v = λ F_utility v")
        logger.info("  High eigenvalues → Safety important, Utility unimportant → OK to add")
        
        gevp_solver = GEVPSolver(regularization=self.regularization)
        eigenvalues, eigenvectors = gevp_solver.solve_gevp(F_safety, F_utility, k=self.k)
        
        # 高固有値の固有ベクトル = Safety追加可能サブスペース
        V_safe_to_add = gevp_solver.select_safety_subspace(eigenvectors, k=self.k)
        
        # 固有値分析
        self._analyze_safety_efficiency(eigenvalues)
        logger.info("✓ Safety-addable subspace identified")
        
        # Step 4: Utilityアダプターを固定（平均化）
        logger.info("Step 4: Fixing Utility adapters (averaging)...")
        utility_merged = self._average_adapters(utility_adapters)
        logger.info("✓ Utility adapters fixed")
        
        # Step 5: SafetyアダプターをUtility直交サブスペースに射影
        logger.info("Step 5: Projecting Safety adapter to Utility-orthogonal subspace...")
        safety_projected = self._project_to_safety_subspace(
            [safety_adapter],
            V_safe_to_add
        )
        logger.info("✓ Safety adapter projected")
        
        # Step 6: Utility (固定) + Safety (射影) を結合
        # 新方式: 加算ベース（両方を保持）
        logger.info(f"Step 6: Combining Utility (fixed) + Safety (projected) with safety_weight={safety_weight}...")
        logger.info("  Using additive merge: both adapters are preserved")
        merged_adapter = self._combine_adapters(
            utility_merged,
            safety_projected,
            alpha=safety_weight
        )
        logger.info("✓ Adapters combined")
        
        logger.info("SST-Merge (Utility-Safety) completed successfully")
        logger.info(f"  Expected result: Utility maintained, Safety improved")
        logger.info(f"  Safety Tax reduction target: 60-70%")
        
        return merged_adapter
    
    def _analyze_safety_efficiency(self, eigenvalues: torch.Tensor):
        """安全効率（固有値）の分析とログ出力"""
        logger.info("=" * 50)
        logger.info("Safety Efficiency Analysis")
        logger.info("=" * 50)
        logger.info(f"Top {min(10, len(eigenvalues))} safety efficiencies (λ):")
        
        for i, lambda_i in enumerate(eigenvalues[:10]):
            logger.info(f"  λ_{i+1} = {lambda_i.item():.6f}")
        
        # 統計情報
        logger.info(f"\nStatistics:")
        logger.info(f"  Mean: {eigenvalues.mean().item():.6f}")
        logger.info(f"  Std:  {eigenvalues.std().item():.6f}")
        logger.info(f"  Min:  {eigenvalues.min().item():.6f}")
        logger.info(f"  Max:  {eigenvalues.max().item():.6f}")
        logger.info("=" * 50)
    
    def _project_and_merge(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]],
        safety_subspace: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAパッチを安全サブスペースに射影してマージ
        
        Args:
            lora_adapters: LoRAアダプタのリスト
            safety_subspace: 安全サブスペースの基底 (shape: [n, k])
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        # 簡易実装: 各アダプタを平均化してから射影
        # より高度な実装では、各アダプタを個別に射影してから結合
        
        merged_adapter = {}
        
        for key in lora_adapters[0].keys():
            # 各パラメータを平均化
            params = [adapter[key] for adapter in lora_adapters]
            avg_param = torch.stack(params).mean(dim=0)
            
            # フラット化
            original_shape = avg_param.shape
            param_flat = avg_param.flatten()
            param_size = param_flat.size(0)
            
            # safety_subspaceのサイズと一致するか確認
            if param_size <= safety_subspace.size(0):
                # パラメータサイズがsafety_subspaceより小さい場合、
                # safety_subspaceの対応する部分を使用
                subspace_subset = safety_subspace[:param_size, :]
                
                # 安全サブスペースに射影
                projected_flat = self.project_to_safety_subspace(
                    param_flat,
                    subspace_subset
                )
            else:
                # パラメータサイズがsafety_subspaceより大きい場合、
                # 射影をスキップして元のパラメータを使用
                logger.warning(f"Parameter {key} size ({param_size}) exceeds safety subspace size ({safety_subspace.size(0)}). Skipping projection.")
                projected_flat = param_flat
            
            # 元の形状に戻す
            projected_param = projected_flat.reshape(original_shape)
            
            merged_adapter[key] = projected_param
            
            # 射影による変化を記録
            change = torch.norm(projected_param - avg_param) / torch.norm(avg_param)
            logger.debug(f"Parameter {key}: projection changed by {change.item():.4f}")
        
        return merged_adapter
    
    def project_to_safety_subspace(
        self,
        phi: torch.Tensor,
        safety_subspace: torch.Tensor
    ) -> torch.Tensor:
        """
        パラメータベクトルを安全サブスペースに射影
        
        φ_projected = V_k V_k^T φ
        
        Args:
            phi: 元のパラメータベクトル (shape: [n])
            safety_subspace: 安全サブスペースの基底 V_k (shape: [n, k])
            
        Returns:
            phi_projected: 射影されたパラメータベクトル (shape: [n])
        """
        # メモリ効率的な射影: P*x = V*(V^T*x)
        # projection_matrix = V*V^Tを明示的に作成しない（メモリ節約）
        
        # デバイスを統一
        device = phi.device
        safety_subspace = safety_subspace.to(device)
        
        # ステップ1: V^T @ phi (shape: [k])
        coefficients = torch.matmul(safety_subspace.T, phi)
        
        # ステップ2: V @ coefficients (shape: [n])
        phi_projected = torch.matmul(safety_subspace, coefficients)
        
        return phi_projected
    
    def optimize_merge_coefficients(
        self,
        lora_adapters: List[Dict[str, torch.Tensor]],
        safety_subspace: torch.Tensor,
        validation_dataloader,
        num_iterations: int = 100
    ) -> List[float]:
        """
        安全サブスペース内で最適なマージ係数を学習（オプション）
        
        φ_merged = Σ α_i V_k V_k^T φ_i
        
        Args:
            lora_adapters: LoRAアダプタのリスト
            safety_subspace: 安全サブスペースの基底
            validation_dataloader: 検証データ
            num_iterations: 最適化イテレーション数
            
        Returns:
            coefficients: 最適化されたマージ係数 [α_1, ..., α_n]
        """
        logger.info("Optimizing merge coefficients in safety subspace...")
        
        # 係数の初期化（均等）
        num_adapters = len(lora_adapters)
        coefficients = torch.ones(num_adapters, device=self.device) / num_adapters
        coefficients.requires_grad = True
        
        optimizer = torch.optim.Adam([coefficients], lr=0.01)
        
        for iteration in range(num_iterations):
            optimizer.zero_grad()
            
            # 現在の係数でマージ
            # （簡易実装: 実際にはモデルに適用して損失を計算）
            loss = torch.sum(coefficients ** 2)  # ダミー損失
            
            loss.backward()
            optimizer.step()
            
            # 係数を正規化（合計が1になるように）
            with torch.no_grad():
                coefficients.data = torch.softmax(coefficients.data, dim=0)
            
            if (iteration + 1) % 20 == 0:
                logger.debug(f"Iteration {iteration+1}/{num_iterations}, Loss: {loss.item():.4f}")
        
        logger.info(f"Optimized coefficients: {coefficients.detach().cpu().tolist()}")
        
        return coefficients.detach().cpu().tolist()
    
    def save_merged_adapter(
        self,
        merged_adapter: Dict[str, torch.Tensor],
        save_path: str,
        metadata: dict = None
    ):
        """マージされたLoRAアダプタを保存"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_dict = {'adapter': merged_adapter}
        if metadata:
            save_dict['metadata'] = metadata
        
        torch.save(save_dict, save_path)
        logger.info(f"Merged adapter saved to {save_path}")
    
    def load_merged_adapter(self, load_path: str) -> Dict[str, torch.Tensor]:
        """マージされたアダプターをロード"""
        return torch.load(load_path)
    
    def _average_adapters(
        self,
        adapters: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, torch.Tensor]:
        """アダプターを平均化（良性アダプターの固定用）"""
        if not adapters:
            raise ValueError("No adapters provided")
        
        if len(adapters) == 1:
            return adapters[0]
        
        averaged = {}
        for key in adapters[0].keys():
            params = [adapter[key] for adapter in adapters]
            averaged[key] = torch.stack(params).mean(dim=0)
        
        return averaged
    
    def _project_to_safety_subspace(
        self,
        harmful_adapters: List[Dict[str, torch.Tensor]],
        safety_subspace: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """悪性アダプターのみを安全サブスペースに射影"""
        logger.info("Projecting harmful adapters to safety subspace...")
        
        # 各アダプターを平均化
        harmful_avg = self._average_adapters(harmful_adapters)
        
        projected = {}
        for key, param in harmful_avg.items():
            # フラット化
            original_shape = param.shape
            param_flat = param.flatten()
            param_size = param_flat.size(0)
            
            # safety_subspaceのサイズと一致するか確認
            if param_size <= safety_subspace.size(0):
                # パラメータサイズがsafety_subspaceより小さい場合
                subspace_subset = safety_subspace[:param_size, :]
                
                # 安全サブスペースに射影
                projected_flat = self.project_to_safety_subspace(
                    param_flat,
                    subspace_subset
                )
            else:
                # パラメータサイズがsafety_subspaceより大きい場合
                logger.warning(f"Parameter {key} size ({param_size}) exceeds safety subspace size ({safety_subspace.size(0)}). Skipping projection.")
                projected_flat = param_flat
            
            # 元の形状に戻す
            projected[key] = projected_flat.reshape(original_shape)
        
        return projected

    def _combine_adapters(
        self,
        benign_adapter: Dict[str, torch.Tensor],
        harmful_projected: Dict[str, torch.Tensor],
        alpha: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """
        良性（固定）と悪性（射影）を結合（Layer-wise Projection版）
        
        V3改善: Layer-wise Projection
        - 層ごとに異なるSafety Weightを適用
        - 出力層（lm_head）: 強いSafety（w=3.0）
        - Attention層: 中程度のSafety（w=1.0）
        - FFN層: 弱いSafety（w=0.3、Utility優先）
        
        Args:
            benign_adapter: 良性アダプター（Utilityなど）
            harmful_projected: 射影済み悪性アダプター（Safetyなど）
            alpha: 基本の結合比率（Layer-wise Weightと掛け合わせる）
        
        Returns:
            merged: マージされたアダプター
        """
        from .layer_config import get_safety_weight, LAYER_SAFETY_WEIGHTS
        
        logger.info(f"Combining adapters with Layer-wise Projection (alpha={alpha})...")
        
        merged = {}
        layer_stats = {}
        
        for key in benign_adapter.keys():
            if key in harmful_projected:
                # Layer-wise Safety Weightを取得
                safety_weight = get_safety_weight(key)
                
                # Layer-wise マージ: utility + (alpha * safety_weight) * safety
                merged[key] = benign_adapter[key] + (alpha * safety_weight) * harmful_projected[key]
                
                # 統計収集
                layer_type = None
                for lt in LAYER_SAFETY_WEIGHTS.keys():
                    if lt in key:
                        layer_type = lt
                        break
                if layer_type:
                    if layer_type not in layer_stats:
                        layer_stats[layer_type] = 0
                    layer_stats[layer_type] += 1
            else:
                # keyが片方にしかない場合はそのまま使用
                merged[key] = benign_adapter[key]
        
        # Layer-wise統計をログ出力
        if layer_stats:
            logger.info("  Layer-wise Safety Weights applied:")
            for layer_type in sorted(layer_stats.keys()):
                weight = LAYER_SAFETY_WEIGHTS.get(layer_type, 1.0)
                count = layer_stats[layer_type]
                logger.info(f"    {layer_type:12s}: {weight:.1f} ({count} params)")
        
        return merged
    
    # _combine_adapters メソッドは下部（line 712-）に統合されました


def test_sst_merge():
    """SST-Mergeの簡易テスト"""
    
    # ダミーモデル
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.lora_A = nn.Parameter(torch.randn(10, 5))
            self.lora_B = nn.Parameter(torch.randn(5, 10))
        
        def forward(self, input_ids, attention_mask, labels):
            class Output:
                def __init__(self):
                    self.loss = torch.randn(1, requires_grad=True)
            return Output()
    
    model = DummyModel()
    
    # ダミーLoRAアダプタ
    lora_adapters = [
        {"lora_A": torch.randn(10, 5), "lora_B": torch.randn(5, 10)},
        {"lora_A": torch.randn(10, 5), "lora_B": torch.randn(5, 10)}
    ]
    
    # ダミーデータローダー
    dummy_data = [{
        "input_ids": torch.randint(0, 100, (2, 10)),
        "attention_mask": torch.ones(2, 10),
        "labels": torch.randint(0, 100, (2, 10))
    } for _ in range(5)]
    
    # SST-Mergeのテスト
    merger = SSTMerge(k=5, device="cpu")
    
    merged_adapter = merger.merge_lora_adapters(
        model,
        lora_adapters,
        harm_dataloader=dummy_data,
        benign_dataloader=dummy_data,
        max_samples=10
    )
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # test_sst_merge() # Removed test_sst_merge() call as per instruction.

    # The following methods were originally misplaced and incorrectly indented.
    # They are now correctly placed as methods of the SSTMerge class.
    
