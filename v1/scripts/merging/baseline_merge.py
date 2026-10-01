"""
Baseline Merge Methods using mergekit

Uses mergekit library for standard merge methods:
- Task Arithmetic
- TIES-Merging
- DARE

Reference:
- TIES: "TIES-Merging: Resolving Interference When Merging Models" (Yadav et al., 2023)
- DARE: "Language Models are Super Mario" (Yu et al., 2023)
"""

import os
# GPU設定は main() 実行時のみ（インポート時はスキップ）
if __name__ == "__main__":
    num = input("gpu num:")
    os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file
from pathlib import Path
import json
import logging
import subprocess
import tempfile
import shutil
import yaml
from typing import Dict, List, Optional
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

# マージ手法
merge_methods = ["task_arithmetic", "ties", "dare"]

# マージパラメータ
merge_config = {
    "task_arithmetic": {"weights": [0.5, 0.5]},
    "ties": {"density": 0.5, "weights": [0.5, 0.5]},
    "dare": {"drop_rate": 0.9, "weights": [0.5, 0.5]},
}

output_dir = "../../models/merged/sst_merge/full/merge_model"
use_mergekit = True  # mergekit使用フラグ
#####################################################


def check_mergekit() -> bool:
    """mergekitが利用可能か確認"""
    try:
        import mergekit
        return True
    except ImportError:
        raise RuntimeError(
            "[Steering Rule Violation] Baseline methods must use official/public code. "
            "Custom fallback implementation is prohibited. Please install mergekit."
        )


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
    
    readme = f"""# Merged Adapter (Baseline Method)

Created: {datetime.now().isoformat()}

## Merge Info
{json.dumps(metadata, indent=2, ensure_ascii=False) if metadata else 'N/A'}
"""
    with open(output_path / "README.md", 'w') as f:
        f.write(readme)
    
    logger.info(f"Saved merged adapter to {output_path}")


class MergekitMerger:
    """
    mergekit-based merger for LORA adapters
    
    Uses mergekit CLI or Python API when available.
    Falls back to custom implementation if mergekit is not installed.
    """
    
    def __init__(self, base_model: str, device: str = 'cuda'):
        self.base_model = base_model
        self.device = device
        self.mergekit_available = check_mergekit()
        
        if self.mergekit_available:
            logger.info("Using mergekit for merging")
        else:
            logger.info("mergekit not available, using custom implementation")
    
    def merge_with_mergekit(
        self,
        method: str,
        utility_path: str,
        safety_path: str,
        output_path: str,
        **kwargs
    ) -> bool:
        """
        mergekit CLIを使用してマージ
        
        Note: mergekit は主にフルモデルのマージを想定しているため、
        LoRAアダプターのマージには追加の処理が必要
        """
        weights = kwargs.get("weights", [0.5, 0.5])
        density = kwargs.get("density", 0.5)
        
        # mergekit用の設定ファイルを作成
        if method == "task_arithmetic":
            merge_method = "task_arithmetic"
        elif method == "ties":
            merge_method = "ties"
        elif method == "dare":
            merge_method = "dare_ties"
        elif method == "della":
            merge_method = "della"
        elif method == "breadcrumbs":
            merge_method = "breadcrumbs"
        elif method in ["safemerge", "led_merging", "mergealign", "alignmerge"]:
            # これらは著者公開実装を使用するため、mergekit-yaml ではなく
            # 専用の公式スクリプト (e.g. run_official_safemerge.py) を介して実行されます。
            logger.info(f"Method {method} is managed via official author repository wrapper.")
            return False
        else:
            logger.error(f"Unknown method for mergekit: {method}")
            return False
        
        # フルモデルのパスを決定（既存チェック）
        full_model_dir = Path("../../models/finetuned/full/FT_model_full")
        
        # Utilityフルモデルのパスを推定
        if "A5_utility" in utility_path:
            utility_full_candidate = full_model_dir / "A5_utility_full"
        elif "A6_utility" in utility_path:
            utility_full_candidate = full_model_dir / "A6_utility_full"
        else:
            utility_full_candidate = None
        
        # Safetyフルモデルのパスを推定
        if "A7_safety" in safety_path:
            safety_full_candidate = full_model_dir / "A7_safety_full"
        else:
            safety_full_candidate = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Utility model: 既存チェック
            if utility_full_candidate and (utility_full_candidate / "config.json").exists():
                logger.info(f"[EXISTS] Using existing full model: {utility_full_candidate.name}")
                utility_full_path = utility_full_candidate
            else:
                # 一時的にフルモデルを作成
                logger.info("Creating temporary utility full model for mergekit...")
                utility_full_path = tmpdir / "utility_model"
                self._create_merged_model(utility_path, utility_full_path)
            
            # Safety model: 既存チェック
            if safety_full_candidate and (safety_full_candidate / "config.json").exists():
                logger.info(f"[EXISTS] Using existing full model: {safety_full_candidate.name}")
                safety_full_path = safety_full_candidate
            else:
                # 一時的にフルモデルを作成
                logger.info("Creating temporary safety full model for mergekit...")
                safety_full_path = tmpdir / "safety_model"
                self._create_merged_model(safety_path, safety_full_path)
            
            # mergekit config
            config = {
                "models": [
                    {"model": str(utility_full_path), "parameters": {"weight": weights[0]}},
                    {"model": str(safety_full_path), "parameters": {"weight": weights[1]}},
                ],
                "merge_method": merge_method,
                "base_model": self.base_model,
                "parameters": {},
            }
            
            if method == "ties":
                config["parameters"]["density"] = density
            elif method == "dare":
                config["parameters"]["density"] = 1.0 - kwargs.get("drop_rate", 0.9)
            
            config_path = tmpdir / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            
            # mergekit実行
            cmd = [
                "mergekit-yaml",
                str(config_path),
                str(output_path),
                "--copy-tokenizer",
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"mergekit completed: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"mergekit failed: {e.stderr}")
                return False
    
    def _create_merged_model(self, adapter_path: str, output_path: Path):
        """ベースモデルとアダプターをマージしてフルモデルを作成"""
        logger.info(f"Loading base model and adapter: {adapter_path}")
        
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16,
            device_map="cpu",  # メモリ節約
        )
        
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()
        
        model.save_pretrained(output_path)
        
        tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"Saved merged model to {output_path}")


class CustomBaselineMerger:
    """
    Custom implementation of baseline merge methods
    
    Used when mergekit is not available or for direct LoRA merging.
    """
    
    def __init__(self, device: str = 'cuda'):
        self.device = device
    
    def task_arithmetic(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float]
    ) -> Dict[str, torch.Tensor]:
        """
        Task Arithmetic: 重み付き平均
        
        Reference: "Editing Models with Task Arithmetic" (Ilharco et al., 2023)
        
        merged = Σ w_i * adapter_i
        """
        merged = {}
        
        for key in adapters[0].keys():
            weighted_sum = torch.zeros_like(adapters[0][key])
            for adapter, weight in zip(adapters, weights):
                if key in adapter:
                    weighted_sum += weight * adapter[key]
            merged[key] = weighted_sum
        
        logger.info(f"Task Arithmetic merge completed (weights={weights})")
        return merged
    
    def ties_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        density: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """
        TIES-Merging: Trim, Elect Sign, Disjoint Merge
        
        Reference: "TIES-Merging: Resolving Interference When Merging Models" 
                   (Yadav et al., NeurIPS 2023)
        
        1. Trim: 絶対値が小さいパラメータを0にする（上位density%のみ保持）
        2. Elect Sign: 非ゼロパラメータの符号で多数決
        3. Disjoint Merge: 選ばれた符号と同じ符号のパラメータのみを加重和
        """
        merged = {}
        
        for key in adapters[0].keys():
            params = []
            for adapter in adapters:
                if key in adapter:
                    params.append(adapter[key].clone())
            
            if not params:
                continue
            
            # Step 1: Trim
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
            
            # Step 2: Elect Sign
            stacked = torch.stack(trimmed_params)
            nonzero_mask = stacked != 0
            signs = torch.sign(stacked) * nonzero_mask.float()
            sign_sum = signs.sum(dim=0)
            elected_sign = torch.sign(sign_sum)
            elected_sign[sign_sum == 0] = 1
            
            # Step 3: Disjoint Merge
            merged_param = torch.zeros_like(params[0])
            for i, param in enumerate(trimmed_params):
                param_sign = torch.sign(param)
                contribution = param * (param_sign == elected_sign).float()
                merged_param += weights[i] * contribution
            
            merged[key] = merged_param
        
        logger.info(f"TIES merge completed (density={density}, weights={weights})")
        return merged
    
    def dare_merge(
        self,
        adapters: List[Dict[str, torch.Tensor]],
        weights: List[float],
        drop_rate: float = 0.9
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
        rescale_factor = 1.0 / (1.0 - drop_rate)
        
        for key in adapters[0].keys():
            params = []
            for adapter in adapters:
                if key in adapter:
                    param = adapter[key].clone()
                    mask = torch.rand_like(param.float()) > drop_rate
                    dropped = param * mask.float() * rescale_factor
                    params.append(dropped)
            
            if params:
                weighted_sum = torch.zeros_like(params[0])
                for param, weight in zip(params, weights):
                    weighted_sum += weight * param
                merged[key] = weighted_sum
        
        logger.info(f"DARE merge completed (drop_rate={drop_rate}, rescale={rescale_factor:.2f})")
        return merged
    
    def merge(
        self,
        method: str,
        adapters: List[Dict[str, torch.Tensor]],
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """マージを実行"""
        weights = kwargs.get("weights", [0.5, 0.5])
        
        if method == "task_arithmetic":
            return self.task_arithmetic(adapters, weights)
        elif method == "ties":
            density = kwargs.get("density", 0.5)
            return self.ties_merge(adapters, weights, density)
        elif method == "dare":
            drop_rate = kwargs.get("drop_rate", 0.9)
            return self.dare_merge(adapters, weights, drop_rate)
        else:
            raise ValueError(f"Unknown method: {method}")


def main():
    logger.info("="*60)
    logger.info("Baseline Merge (Task Arithmetic / TIES / DARE)")
    logger.info("="*60)
    
    # mergekitを使うか、カスタム実装を使うか
    if use_mergekit and check_mergekit():
        merger = MergekitMerger(model_id)
        use_custom = False
    else:
        raise RuntimeError(
            "[Steering Rule Violation] Baseline methods must use official/public code. "
            "Custom implementation/fallback is prohibited."
        )
    
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info("="*60)
        
        # アダプターをロード（カスタム実装用）
        try:
            utility_adapter = load_adapter(utility_path)
            safety_adapter = load_adapter(safety_path)
        except FileNotFoundError as e:
            logger.error(f"Skipping {pair_name}: {e}")
            continue
        
        adapters = [utility_adapter, safety_adapter]
        
        # 各手法でマージ
        for method in merge_methods:
            logger.info(f"\n--- Merging with {method.upper()} ---")
            
            config = merge_config.get(method, {})
            output_name = f"{pair_name}_{method}"
            output_path = output_base / output_name
            
            try:
                if use_custom:
                    merged = merger.merge(method, adapters, **config)
                    
                    metadata = {
                        "utility_adapter": utility_path,
                        "safety_adapter": safety_path,
                        "merge_method": method,
                        "merge_config": config,
                        "base_model": model_id,
                        "implementation": "custom",
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    save_merged_adapter(merged, output_path, utility_path, metadata)
                else:
                    # mergekit使用
                    success = merger.merge_with_mergekit(
                        method, utility_path, safety_path, output_path, **config
                    )
                    if not success:
                        raise RuntimeError(
                            f"[Steering Rule Violation] mergekit execution failed for method {method}. "
                            "Custom fallback implementation is prohibited."
                        )
                
                logger.info(f"✓ Saved: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to merge with {method}: {e}")
                import traceback
                traceback.print_exc()
    
    logger.info("\n" + "="*60)
    logger.info("Baseline merge completed!")
    logger.info(f"Output directory: {output_base}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
