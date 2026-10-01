"""
SST-Merge: Safety Subspace Task-Merge

GEVPに基づく安全性とユーティリティの最適マージ

理論的基盤 (guide参照):
- GEVP: F_harm v = λ F_benign v を解く
- Rayleigh Quotient: R(v) = (v^T F_harm v) / (v^T F_benign v)
- 高いλ = Safety改善に効く & Utility悪化が小さい → 安全に追加可能

Reference:
- AlignGuard-LoRA (FIM-based decomposition)
- TIES-Merging, DARE (baseline comparisons)
"""

import os
# GPU設定は main() 実行時のみ（インポート時はスキップ）
if __name__ == "__main__":
    num = input("gpu num:")
    os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, LoraConfig, get_peft_model, TaskType
from safetensors.torch import load_file, save_file
from datasets import load_dataset
from torch.utils.data import DataLoader
from pathlib import Path
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
model_id = "meta-llama/Llama-3.1-8B-Instruct"

# マージするアダプターのペア
merge_pairs = [
    ("./FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4", 
     "./FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A5_A7"),
    ("./FT_model/A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4",
     "./FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A6_A7"),
]

# SST-Merge パラメータ
sst_config = {
    "safety_weight": 1.0,           # α: Safety補間重み (0-1)
    "use_layerwise_weights": False,  # Layer-wise重み調整
    "use_gevp": True,               # GEVP-based mask使用
    "max_fim_samples": 500,         # FIM計算サンプル数
    "regularization": 1e-6,         # FIM正則化項
    "top_k_ratio": None,            # Top-k選択比率 (None=ソフトマスク, 0.3=上位30%)
}

# データパス
# utility_data_path = "../data/repliqa_eval.json"  # Utility FIM計算用 (未使用: HuggingFaceから直接ロード)
safety_data_path = "../data/response_dataframe.csv"  # Safety FIM計算用

# Utility data: HuggingFaceから直接ロード
utility_dataset_name = "ServiceNow/repliqa"  # または "tatsu-lab/alpaca"
utility_dataset_split = "repliqa_0"

output_dir = "./merge_model"
#####################################################


class FIMCalculator:
    """
    Fisher Information Matrix Calculator
    
    FIMは対数尤度の勾配の分散として近似計算:
    F ≈ E[(∇log p(y|x,θ))^2]
    
    これはパラメータ空間における損失曲面の曲率を表し、
    どのパラメータが重要かを示す。
    """
    
    def __init__(
        self,
        model: nn.Module,
        tokenizer,
        device: str = 'cuda',
        regularization: float = 1e-6,
        param_type: str = 'lora'
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.regularization = regularization
        self.param_type = param_type
        
        # パラメータを抽出
        self.params = self._extract_params(param_type)
        logger.info(f"FIMCalculator: {len(self.params)} parameters (type={param_type})")
    
    def _extract_params(self, param_type: str = 'lora') -> List[nn.Parameter]:
        """パラメータを抽出
        
        Args:
            param_type: "lora" (LoRAパラメータのみ) or 
                       "trainable" (学習可能なパラメータ) or
                       "all" (全パラメータ)
        
        Returns:
            抽出されたパラメータのリスト
        """
        params = []
        for name, param in self.model.named_parameters():
            if param_type == "lora":
                if 'lora' in name.lower() and param.requires_grad:
                    params.append(param)
            elif param_type == "trainable":
                if param.requires_grad:
                    params.append(param)
            elif param_type == "all":
                params.append(param)
            else:
                raise ValueError(f"Unknown param_type: {param_type}. "
                               f"Must be 'lora', 'trainable', or 'all'.")
        
        if not params:
            logger.warning(f"No parameters found for param_type='{param_type}'")
        
        return params
    
    def compute_fim(
        self,
        dataloader,
        max_samples: int = 200
    ) -> torch.Tensor:
        """
        対角FIMを勾配分散で近似計算
        
        Args:
            dataloader: データローダー
            max_samples: 最大サンプル数
            
        Returns:
            fim_diag: 対角FIM (shape: [total_params])
        """
        self.model.train()
        
        gradients = []
        num_samples = 0
        
        for batch in dataloader:
            if num_samples >= max_samples:
                break
            
            # バッチ処理
            if isinstance(batch, dict):
                texts = batch.get('text', batch.get('prompt', []))
                if isinstance(texts, str):
                    texts = [texts]
            else:
                texts = batch
            
            if not texts:
                continue
            
            inputs = self.tokenizer(
                list(texts) if not isinstance(texts, list) else texts,
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
            for param in self.params:  # LoRA専用 → 汎用パラメータに変更
                if param.grad is not None:
                    batch_grads.append(param.grad.detach().cpu().flatten())
            
            if batch_grads:
                gradients.append(torch.cat(batch_grads))
            
            num_samples += len(texts)
            
            del outputs
            torch.cuda.empty_cache()
        
        if not gradients:
            raise ValueError("No gradients collected for FIM computation")
        
        # 勾配の分散を計算 → 対角FIM
        gradients_stack = torch.stack(gradients)
        variance = gradients_stack.var(dim=0)
        
        # 正則化を追加
        fim_diag = variance + self.regularization
        
        self.model.eval()
        
        logger.info(f"  FIM computed: {len(fim_diag)} parameters, mean={fim_diag.mean():.6f}")
        
        return fim_diag


class GEVPSolver:
    """
    Generalized Eigenvalue Problem Solver
    
    GEVPを解く: F_harm v = λ F_benign v
    
    対角FIMの場合:
    λ_i = F_harm[i] / F_benign[i]
    
    高いλ = Safety (harm refusal) に重要 & Utility (benign) に重要でない
         → Safetyを追加してもUtilityへの影響が小さい
    """
    
    def __init__(self, regularization: float = 1e-6):
        self.regularization = regularization
    
    def solve_gevp_diagonal(
        self,
        F_harm: torch.Tensor,
        F_benign: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        対角FIM用のGEVPを解く
        
        λ_i = F_harm[i] / F_benign[i]
        
        Args:
            F_harm: Safety/Harm FIM (対角)
            F_benign: Utility/Benign FIM (対角)
            
        Returns:
            eigenvalues: 全パラメータの固有値 (λ)
            sorted_indices: 降順ソートのインデックス
        """
        logger.info("Solving diagonal GEVP: F_harm v = λ F_benign v")
        
        # λ_i = F_harm[i] / F_benign[i]
        eigenvalues = F_harm / (F_benign + self.regularization)
        
        # 降順ソート（高いλが先頭）
        sorted_indices = torch.argsort(eigenvalues, descending=True)
        
        logger.info(f"  Total parameters: {len(eigenvalues)}")
        logger.info(f"  Top λ: {eigenvalues[sorted_indices[0]].item():.4f}")
        logger.info(f"  Median λ: {eigenvalues.median().item():.4f}")
        logger.info(f"  Bottom λ: {eigenvalues[sorted_indices[-1]].item():.4f}")
        
        return eigenvalues, sorted_indices
    
    def compute_safety_mask(
        self,
        eigenvalues: torch.Tensor,
        top_k_ratio: Optional[float] = None
    ) -> torch.Tensor:
        """
        固有値λに基づくSafety適用マスクを計算
        
        高いλ → Safety追加しても安全（マスク値大）
        低いλ → Utilityに影響するため控えめに（マスク値小）
        
        Args:
            eigenvalues: GEVPで計算した固有値
            top_k_ratio: Top-k選択比率 (None=ソフトマスク, 0.3=上位30%のみ)
        """
        if top_k_ratio is not None:
            # ハードマスク: 上位top_k_ratio%のみ1、それ以外は0
            k = int(len(eigenvalues) * top_k_ratio)
            sorted_indices = torch.argsort(eigenvalues, descending=True)
            mask = torch.zeros_like(eigenvalues)
            mask[sorted_indices[:k]] = 1.0
            
            logger.info(f"  Safety mask (top-k): k={k} ({top_k_ratio*100:.0f}%)")
            return mask
        
        # ソフトマスク: Log-scale正規化（外れ値に強い）
        # λ > 1: Safety重視パラメータ, λ < 1: Utility重視パラメータ
        # log(λ)を使って正規化し、sigmoid風に変換
        
        # λ=1を基準点として使用（log(1)=0）
        log_eigenvalues = torch.log(eigenvalues + 1e-10)
        
        # パーセンタイルベースの正規化（外れ値の影響を軽減）
        # 大きなテンソルの場合はサンプリングでパーセンタイルを計算
        if len(log_eigenvalues) > 100000:
            # サンプリングでパーセンタイル計算（メモリ効率）
            sample_size = 100000
            indices = torch.randperm(len(log_eigenvalues))[:sample_size]
            sample = log_eigenvalues[indices]
            p5 = torch.quantile(sample, 0.05)
            p95 = torch.quantile(sample, 0.95)
        else:
            p5 = torch.quantile(log_eigenvalues, 0.05)
            p95 = torch.quantile(log_eigenvalues, 0.95)
        
        if p95 > p5:
            # [p5, p95]を[0, 1]にクリップ正規化
            normalized = (log_eigenvalues - p5) / (p95 - p5)
            normalized = torch.clamp(normalized, 0.0, 1.0)
        else:
            normalized = torch.ones_like(eigenvalues) * 0.5
        
        logger.info(f"  Safety mask (soft, log-percentile): mean={normalized.mean():.4f}, "
                   f"median={normalized.median():.4f}, "
                   f">{0.5}: {(normalized > 0.5).sum()}/{len(normalized)}")
        
        return normalized


class SSTMerge:
    """
    SST-Merge: Safety Subspace Task-Merge
    
    アルゴリズム:
    1. Utility FIM (F_benign) を計算
    2. Safety FIM (F_harm) を計算
    3. GEVP: F_harm v = λ F_benign v を解く
    4. λに基づくマスクでSafety適用量を調整
    5. Merged = (1-α*mask) * Utility + α*mask * Safety
    
    Layer-wise weights:
    - Attention層: Safety強め（出力品質に影響）
    - FFN層: Utility保持（知識保持）
    """
    
    # Layer-wise Safety Weights
    LAYER_WEIGHTS = {
        'lm_head': 1.5,      # 出力層: Safety強め
        'q_proj': 1.2,       # Attention: Safety強め
        'k_proj': 1.2,
        'v_proj': 1.2,
        'o_proj': 1.2,
        'gate_proj': 0.8,    # FFN: Utility保持
        'up_proj': 0.8,
        'down_proj': 0.8,
    }
    
    def __init__(
        self,
        safety_weight: float = 0.5,
        use_layerwise_weights: bool = True,
        use_gevp: bool = True,
        regularization: float = 1e-6,
        top_k_ratio: Optional[float] = None,
        device: str = 'cuda'
    ):
        """
        Args:
            safety_weight: 基本Safety重み (α)
            use_layerwise_weights: Layer-wise重み調整を使用
            use_gevp: GEVP-basedマスクを使用
            regularization: FIM正則化項
            top_k_ratio: Top-k選択比率 (None=ソフトマスク, 0.3=上位30%)
                         ※ sst_merge_v4.pyの「k」に相当
            device: 計算デバイス
        """
        self.safety_weight = safety_weight
        self.use_layerwise_weights = use_layerwise_weights
        self.use_gevp = use_gevp
        self.regularization = regularization
        self.top_k_ratio = top_k_ratio
        self.device = device
        
        logger.info(f"SSTMerge: α={safety_weight}, layerwise={use_layerwise_weights}, "
                   f"gevp={use_gevp}, top_k={top_k_ratio}")
    
    def merge(
        self,
        model: nn.Module,
        tokenizer,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader=None,
        safety_dataloader=None,
        max_samples: int = 200
    ) -> Dict[str, torch.Tensor]:
        """
        SST-Mergeを実行
        
        Args:
            model: ベースモデル
            tokenizer: トークナイザー
            utility_adapter: Utility LoRA (A5/A6)
            safety_adapter: Safety LoRA (A7)
            utility_dataloader: Utility FIM計算用データ
            safety_dataloader: Safety FIM計算用データ
            max_samples: FIM計算の最大サンプル数
            
        Returns:
            merged_adapter: マージされたLoRAアダプタ
        """
        logger.info("\n" + "="*60)
        logger.info("SST-Merge: Safety Subspace Task-Merge")
        logger.info("="*60)
        
        if self.use_gevp and utility_dataloader and safety_dataloader:
            return self._merge_with_gevp(
                model, tokenizer, utility_adapter, safety_adapter,
                utility_dataloader, safety_dataloader, max_samples
            )
        else:
            logger.info("Using simple interpolation (no GEVP)")
            return self._simple_merge(utility_adapter, safety_adapter)
    
    def _merge_with_gevp(
        self,
        model: nn.Module,
        tokenizer,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int
    ) -> Dict[str, torch.Tensor]:
        """GEVP-based merge"""
        
        # LoRA設定を推定
        lora_r = 16
        for key, val in utility_adapter.items():
            if 'lora_A' in key:
                lora_r = val.shape[0]
                break
            elif 'lora_B' in key:
                lora_r = val.shape[1]
                break
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_r * 2,
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"],
            bias="none"
        )
        
        # Step 1: Utility FIM計算
        logger.info("\nStep 1: Computing Utility FIM (F_benign)...")
        peft_model = get_peft_model(model, lora_config)
        self._load_adapter_to_model(peft_model, utility_adapter)
        
        fim_calc = FIMCalculator(peft_model, tokenizer, self.device, self.regularization)
        F_benign = fim_calc.compute_fim(utility_dataloader, max_samples)
        
        # クリーンアップ
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        # Step 2: Safety FIM計算
        logger.info("\nStep 2: Computing Safety FIM (F_harm)...")
        peft_model = get_peft_model(model, lora_config)
        self._load_adapter_to_model(peft_model, safety_adapter)
        
        fim_calc = FIMCalculator(peft_model, tokenizer, self.device, self.regularization)
        F_harm = fim_calc.compute_fim(safety_dataloader, max_samples)
        
        del peft_model, fim_calc
        torch.cuda.empty_cache()
        
        # Step 3: GEVP解く
        logger.info("\nStep 3: Solving GEVP...")
        gevp_solver = GEVPSolver(self.regularization)
        eigenvalues, sorted_indices = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
        
        # Step 4: Safety maskを計算
        logger.info("\nStep 4: Computing safety mask...")
        safety_mask = gevp_solver.compute_safety_mask(eigenvalues, self.top_k_ratio)
        
        # Step 5: マスクを使ってマージ
        logger.info("\nStep 5: Merging with GEVP-based mask...")
        merged = self._merge_with_mask(
            utility_adapter, safety_adapter, safety_mask
        )
        
        logger.info("\n" + "="*60)
        logger.info("SST-Merge completed!")
        logger.info("="*60)
        
        return merged
    
    def _load_adapter_to_model(
        self,
        peft_model: nn.Module,
        adapter: Dict[str, torch.Tensor]
    ):
        """アダプターパラメータをモデルにロード"""
        applied = 0
        model_params = {n: p for n, p in peft_model.named_parameters() 
                       if 'lora' in n.lower()}
        
        for model_name, param in model_params.items():
            for adapter_name, adapter_val in adapter.items():
                # キー名の末尾部分でマッチング
                model_key = model_name.replace('.default', '').split('.')[-3:]
                adapter_key = adapter_name.replace('.default', '').split('.')[-3:]
                
                if model_key == adapter_key and param.shape == adapter_val.shape:
                    param.data = adapter_val.to(param.device)
                    applied += 1
                    break
        
        logger.info(f"  Applied {applied} adapter parameters")
    
    def _merge_with_mask(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor],
        safety_mask: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        GEVPマスクを使った加算型マージ（理論準拠）
        
        理論的定式化 (Rayleigh Quotient最大化):
        - 高λ方向: Safetyに重要 & Utilityに影響小 → Safetyを追加可能
        - 低λ方向: Utilityに重要 → 変更すべきでない（Utility保持）
        
        加算型マージ:
        merged[i] = utility[i] + α * layer_weight * mask[i] * safety[i]
        
        これにより:
        - Utilityは完全に保持される
        - Safetyは高λ方向にのみ追加される
        
        Note: LoRAパラメータのみGEVPマスクを適用。
              embed_tokens等の非LoRAパラメータは加算型。
        """
        merged = {}
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        # LoRAパラメータと非LoRAパラメータを分離
        lora_keys = [k for k in utility_adapter.keys() if 'lora' in k.lower()]
        non_lora_keys = [k for k in utility_adapter.keys() if 'lora' not in k.lower()]
        
        # LoRAパラメータのサイズを計算
        lora_sizes = [utility_adapter[k].numel() for k in lora_keys]
        total_lora_size = sum(lora_sizes)
        
        logger.info(f"  LoRA parameters: {len(lora_keys)} tensors, {total_lora_size} elements")
        if non_lora_keys:
            non_lora_size = sum(utility_adapter[k].numel() for k in non_lora_keys)
            logger.info(f"  Non-LoRA parameters: {len(non_lora_keys)} tensors, {non_lora_size} elements (additive)")
        
        # マスクサイズチェック
        if len(safety_mask) != total_lora_size:
            logger.warning(f"Mask size mismatch: {len(safety_mask)} vs {total_lora_size}")
            # マスクがLoRAサイズと一致しない場合、デフォルトマスクを使用
            safety_mask = torch.ones(total_lora_size) * 0.5
        
        offset = 0
        stats = {'mean_weight': [], 'lora_stats': {}}
        
        # LoRAパラメータ: 加算型GEVPマージ
        for key in lora_keys:
            param_size = utility_adapter[key].numel()
            original_shape = utility_adapter[key].shape
            
            # このパラメータの要素ごとマスク
            param_mask = safety_mask[offset:offset + param_size].reshape(original_shape)
            
            # Layer-wise weight
            layer_weight = 1.0
            if self.use_layerwise_weights:
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_weight = weight
                        break
            
            if key in safety_adapter:
                utility_val = utility_adapter[key]
                safety_val = safety_adapter[key]
                
                # 要素ごとのSafety追加重み（理論準拠）
                # weight[i] = α * layer_weight * mask[i]
                safety_weight = alpha * layer_weight * param_mask.to(utility_val.device)
                
                # 加算型マージ: utility + weight * safety
                # Utilityを完全に保持し、Safetyを高λ方向にのみ追加
                merged[key] = utility_val + safety_weight * safety_val
                
                # 統計収集
                stats['mean_weight'].append(safety_weight.mean().item())
            else:
                merged[key] = utility_adapter[key]
            
            offset += param_size
        
        # 非LoRAパラメータ（embed_tokens等）: 加算型
        for key in non_lora_keys:
            if key in safety_adapter:
                utility_val = utility_adapter[key]
                safety_val = safety_adapter[key]
                
                # Layer-wise weight
                layer_weight_val = alpha
                if self.use_layerwise_weights:
                    for layer_type, weight in self.LAYER_WEIGHTS.items():
                        if layer_type in key:
                            layer_weight_val = alpha * weight
                            break
                
                # 加算型: utility + weight * safety
                merged[key] = utility_val + layer_weight_val * safety_val
                logger.info(f"  Non-LoRA additive merge: {key} with weight={layer_weight_val:.3f}")
            else:
                merged[key] = utility_adapter[key]
        
        avg_weight = sum(stats['mean_weight']) / len(stats['mean_weight']) if stats['mean_weight'] else 0
        logger.info(f"  Additive GEVP merge (theory-based): base α={alpha}, avg safety weight={avg_weight:.4f}")
        return merged
    
    def _simple_merge(
        self,
        utility_adapter: Dict[str, torch.Tensor],
        safety_adapter: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        シンプルな加算型マージ (GEVP未使用時、理論準拠)
        
        merged = utility + α * safety
        """
        merged = {}
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        for key in utility_adapter.keys():
            utility_val = utility_adapter[key]
            
            # Layer-wise weight
            layer_weight = alpha
            if self.use_layerwise_weights:
                for layer_type, weight in self.LAYER_WEIGHTS.items():
                    if layer_type in key:
                        layer_weight = alpha * weight
                        break
            
            if key in safety_adapter:
                safety_val = safety_adapter[key]
                # 加算型: utility + weight * safety
                merged[key] = utility_val + layer_weight * safety_val
            else:
                merged[key] = utility_val
        
        logger.info(f"  Simple additive merge (α={alpha})")
        return merged
    
    def compute_full_fim(
        self,
        model_path: str,
        tokenizer,
        dataloader,
        max_samples: int = 200,
        param_type: str = "trainable"
    ) -> torch.Tensor:
        """指定されたフルモデルのFIMを計算して返す"""
        logger.info(f"Computing Full FIM for {model_path}...")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        
        fim_calc = FIMCalculator(
            model, tokenizer, self.device, 
            self.regularization, param_type=param_type
        )
        FIM = fim_calc.compute_fim(dataloader, max_samples)
        
        del model, fim_calc
        torch.cuda.empty_cache()
        
        return FIM

    def merge_full_models(
        self,
        utility_model_path: str,
        safety_model_path: str,
        output_path: str,
        utility_dataloader=None,
        safety_dataloader=None,
        max_samples: int = 200,
        f_benign: torch.Tensor = None,
        f_harm: torch.Tensor = None,
        eigenvalues: torch.Tensor = None,
        safety_mask: torch.Tensor = None
    ):
        """
        フルモデル同士をSST-Mergeで統合
        
        Args:
            utility_model_path: Utilityフルモデルのパス
            safety_model_path: Safetyフルモデルのパス
            output_path: 出力先パス
            utility_dataloader: Utility FIM計算用データ
            safety_dataloader: Safety FIM計算用データ
            max_samples: FIM計算の最大サンプル数
            f_benign: キャッシュされたUtility FIM
            f_harm: キャッシュされたSafety FIM
            eigenvalues: キャッシュされた固有値
            safety_mask: キャッシュされたSafetyマスク
        """
        logger.info("\n" + "="*60)
        logger.info("SST-Merge: Full Model Merging")
        logger.info("="*60)
        
        # トークナイザーをロード
        tokenizer = AutoTokenizer.from_pretrained(utility_model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        if self.use_gevp and (utility_dataloader and safety_dataloader or (f_benign is not None and f_harm is not None)):
            # GEVP-based merge for full models
            logger.info("Using GEVP-based merge for full models")
            
            # Step 1: Utility FIM計算
            if f_benign is None:
                logger.info("\nStep 1: Computing Utility FIM (F_benign)...")
                F_benign = self.compute_full_fim(
                    utility_model_path, tokenizer, utility_dataloader, max_samples, param_type="trainable"
                )
            else:
                F_benign = f_benign
            
            # Step 2: Safety FIM計算
            if f_harm is None:
                logger.info("\nStep 2: Computing Safety FIM (F_harm)...")
                F_harm = self.compute_full_fim(
                    safety_model_path, tokenizer, safety_dataloader, max_samples, param_type="trainable"
                )
            else:
                F_harm = f_harm
            
            # Step 3: GEVP解く
            if eigenvalues is None:
                logger.info("\nStep 3: Solving GEVP...")
                gevp_solver = GEVPSolver(self.regularization)
                eigenvalues, sorted_indices = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
            else:
                gevp_solver = GEVPSolver(self.regularization)
            
            # Step 4: Safety maskを計算
            if safety_mask is None:
                logger.info("\nStep 4: Computing safety mask...")
                safety_mask = gevp_solver.compute_safety_mask(eigenvalues, self.top_k_ratio)
            
            # Step 5: マスクを使ってフルモデルマージ
            logger.info("\nStep 5: Merging full models with GEVP-based mask...")
            self._merge_full_models_with_mask(
                utility_model_path,
                safety_model_path,
                output_path,
                safety_mask,
                tokenizer
            )
            
        else:
            # Simple merge (without GEVP)
            logger.info("Using simple interpolation (no GEVP)")
            self._simple_merge_full_models(
                utility_model_path,
                safety_model_path,
                output_path
            )
        
        logger.info("\n" + "="*60)
        logger.info("SST-Merge completed!")
        logger.info("="*60)
    
    def _merge_full_models_with_mask(
        self,
        utility_model_path: str,
        safety_model_path: str,
        output_path: str,
        safety_mask: torch.Tensor,
        tokenizer
    ):
        """GEVPマスクを使ってフルモデルをマージ"""
        
        # モデルをロード
        logger.info("Loading models for merging...")
        utility_model = AutoModelForCausalLM.from_pretrained(
            utility_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",  # メモリ節約
        )
        
        safety_model = AutoModelForCausalLM.from_pretrained(
            safety_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
        )
        
        # マージ実行
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        # 学習可能なパラメータを収集
        utility_params = []
        safety_params = []
        param_names = []
        
        for (u_name, u_param), (s_name, s_param) in zip(
            utility_model.named_parameters(),
            safety_model.named_parameters()
        ):
            if u_param.requires_grad:
                utility_params.append(u_param.data.cpu().flatten())
                safety_params.append(s_param.data.cpu().flatten())
                param_names.append(u_name)
        
        # 全パラメータを結合
        utility_flat = torch.cat(utility_params)
        safety_flat = torch.cat(safety_params)
        
        # マスクサイズチェック
        if len(safety_mask) != len(utility_flat):
            logger.warning(f"Mask size mismatch: {len(safety_mask)} vs {len(utility_flat)}")
            logger.warning("Using uniform mask")
            safety_mask = torch.ones_like(utility_flat) * 0.5
        
        # GEVP-basedマージ: utility + α * mask * safety
        merged_flat = utility_flat + alpha * safety_mask.cpu() * safety_flat
        
        # パラメータを元の形状に戻す
        offset = 0
        param_idx = 0
        for (name, param) in utility_model.named_parameters():
            if param.requires_grad:
                param_size = param.numel()
                merged_values = merged_flat[offset:offset + param_size].reshape(param.shape)
                param.data = merged_values.to(param.dtype)
                offset += param_size
                param_idx += 1
        
        # マージされたモデルを保存
        logger.info(f"Saving merged model to {output_path}...")
        utility_model.save_pretrained(output_path, safe_serialization=True, max_shard_size="5GB")
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"✓ Full model merge completed with GEVP mask (α={alpha})")
        
        del utility_model, safety_model
        torch.cuda.empty_cache()
    
    def _simple_merge_full_models(
        self,
        utility_model_path: str,
        safety_model_path: str,
        output_path: str
    ):
        """シンプルなフルモデルマージ（GEVPなし）"""
        
        logger.info("Loading models for simple merge...")
        tokenizer = AutoTokenizer.from_pretrained(utility_model_path)
        
        utility_model = AutoModelForCausalLM.from_pretrained(
            utility_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
        )
        
        safety_model = AutoModelForCausalLM.from_pretrained(
            safety_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
        )
        
        alpha = min(max(self.safety_weight, 0.0), 1.0)
        
        # 単純加算: utility + α * safety
        for (u_name, u_param), (s_name, s_param) in zip(
            utility_model.named_parameters(),
            safety_model.named_parameters()
        ):
            u_param.data = u_param.data + alpha * s_param.data
        
        # 保存
        utility_model.save_pretrained(output_path, safe_serialization=True, max_shard_size="5GB")
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"✓ Simple merge completed (α={alpha})")
        
        del utility_model, safety_model
        torch.cuda.empty_cache()


def load_adapter(adapter_path: str) -> Dict[str, torch.Tensor]:
    """アダプターをロード"""
    adapter_path = Path(adapter_path)
    safetensor_path = adapter_path / "adapter_model.safetensors"
    
    if safetensor_path.exists():
        adapter = load_file(str(safetensor_path))
        logger.info(f"Loaded adapter from {safetensor_path}")
    else:
        pt_path = adapter_path / "adapter_model.bin"
        if pt_path.exists():
            adapter = torch.load(pt_path, map_location='cpu')
            logger.info(f"Loaded adapter from {pt_path}")
        else:
            raise FileNotFoundError(f"No adapter found at {adapter_path}")
    
    return adapter


def save_merged_adapter(
    merged_adapter: Dict[str, torch.Tensor],
    output_path: str,
    base_config_path: str,
    metadata: Optional[Dict] = None
):
    """マージされたアダプターを保存"""
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    save_file(merged_adapter, str(output_path / "adapter_model.safetensors"))
    
    base_config = Path(base_config_path) / "adapter_config.json"
    if base_config.exists():
        with open(base_config, 'r') as f:
            config = json.load(f)
        with open(output_path / "adapter_config.json", 'w') as f:
            json.dump(config, f, indent=2)
    
    if metadata:
        with open(output_path / "merge_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    readme = f"""# SST-Merged Adapter

Created: {datetime.now().isoformat()}

## Method
SST-Merge: Safety Subspace Task-Merge using GEVP

## Merge Info
{json.dumps(metadata, indent=2, ensure_ascii=False) if metadata else 'N/A'}
"""
    with open(output_path / "README.md", 'w') as f:
        f.write(readme)
    
    logger.info(f"Saved merged adapter to {output_path}")


def create_dataloader(data_path: str, batch_size: int = 4):
    """データローダーを作成 (ローカルファイル用)"""
    data_path = Path(data_path)
    
    if data_path.suffix == '.json':
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # テキストフィールドを抽出
        texts = []
        for item in data:
            if isinstance(item, dict):
                text = item.get('text', item.get('prompt', item.get('input', '')))
                texts.append(text)
            else:
                texts.append(str(item))
        
        return DataLoader(texts, batch_size=batch_size, shuffle=True)
    
    elif data_path.suffix == '.csv':
        import pandas as pd
        df = pd.read_csv(data_path)
        
        texts = []
        if 'text' in df.columns:
            texts = df['text'].tolist()
        elif 'prompt' in df.columns:
            if 'response' in df.columns:
                texts = (df['prompt'] + '\n' + df['response']).tolist()
            else:
                texts = df['prompt'].tolist()
        
        return DataLoader(texts, batch_size=batch_size, shuffle=True)
    
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}")


def create_utility_dataloader_from_hf(
    dataset_name: str = "ServiceNow/repliqa",
    split: str = "repliqa_0",
    batch_size: int = 4,
    max_samples: int = 500
):
    """HuggingFaceからUtilityデータをロードしてDataLoaderを作成"""
    from datasets import load_dataset
    
    logger.info(f"Loading utility data from HuggingFace: {dataset_name} ({split})")
    
    if "repliqa" in dataset_name.lower():
        # RepliQA dataset
        dataset = load_dataset(dataset_name, split=split)
        texts = [f"{item['question']}\n{item['answer']}" for item in dataset]
    elif "alpaca" in dataset_name.lower():
        # Alpaca dataset
        dataset = load_dataset(dataset_name, split=split)
        texts = [f"{item['instruction']} {item['input']}\n{item['output']}" for item in dataset]
    else:
        # 汎用: textフィールドを探す
        dataset = load_dataset(dataset_name, split=split)
        if 'text' in dataset.column_names:
            texts = dataset['text']
        elif 'prompt' in dataset.column_names:
            texts = dataset['prompt']
        else:
            raise ValueError(f"Unknown dataset format: {dataset_name}")
    
    # サンプル数制限
    if max_samples and len(texts) > max_samples:
        import random
        texts = random.sample(texts, max_samples)
    
    logger.info(f"Loaded {len(texts)} utility samples from {dataset_name}")
    return DataLoader(texts, batch_size=batch_size, shuffle=True)


def main():
    logger.info("="*60)
    logger.info("SST-Merge: Safety Subspace Task-Merge")
    logger.info("="*60)
    
    # モデルとトークナイザーをロード
    logger.info(f"\nLoading base model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    
    # データローダー作成
    utility_dataloader = None
    safety_dataloader = None
    
    if sst_config["use_gevp"]:
        # Utility data: HuggingFaceから直接ロード
        try:
            utility_dataloader = create_utility_dataloader_from_hf(
                dataset_name=utility_dataset_name,
                split=utility_dataset_split,
                max_samples=sst_config["max_fim_samples"]
            )
        except Exception as e:
            logger.warning(f"Failed to load utility data from HuggingFace: {e}")
        
        # Safety data: ローカルCSVからロード
        if Path(safety_data_path).exists():
            safety_dataloader = create_dataloader(safety_data_path)
            logger.info(f"Loaded safety data from {safety_data_path}")
        else:
            logger.warning(f"Safety data not found: {safety_data_path}")
    
    # SST-Mergeインスタンス
    sst_merger = SSTMerge(
        safety_weight=sst_config["safety_weight"],
        use_layerwise_weights=sst_config["use_layerwise_weights"],
        use_gevp=sst_config["use_gevp"],
        regularization=sst_config["regularization"],
        top_k_ratio=sst_config["top_k_ratio"],
    )
    
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info("="*60)
        
        # アダプターをロード
        try:
            utility_adapter = load_adapter(utility_path)
            safety_adapter = load_adapter(safety_path)
        except FileNotFoundError as e:
            logger.error(f"Skipping {pair_name}: {e}")
            continue
        
        # SST-Merge実行
        try:
            merged = sst_merger.merge(
                model, tokenizer,
                utility_adapter, safety_adapter,
                utility_dataloader, safety_dataloader,
                max_samples=sst_config["max_fim_samples"]
            )
            
            # 保存 (フォルダ名にハイパーパラメータを含める)
            alpha_str = f"a{sst_config['safety_weight']}"
            layerwise_str = "lw" if sst_config['use_layerwise_weights'] else "nolw"
            topk_str = f"k{sst_config['top_k_ratio']}" if sst_config['top_k_ratio'] else "soft"
            # "add"で加算型マージを示す（理論準拠版）
            output_name = f"{pair_name}_sst_{alpha_str}_{layerwise_str}_{topk_str}_add"
            output_path = output_base / output_name
            
            metadata = {
                "utility_adapter": utility_path,
                "safety_adapter": safety_path,
                "merge_method": "sst_additive",  # 理論準拠の加算型
                "merge_formula": "merged = utility + α * mask * safety",
                "sst_config": sst_config,
                "base_model": model_id,
                "timestamp": datetime.now().isoformat(),
            }
            
            save_merged_adapter(merged, output_path, utility_path, metadata)
            logger.info(f"✓ Saved: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to merge: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n" + "="*60)
    logger.info("SST-Merge completed!")
    logger.info(f"Output directory: {output_base}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
