"""
全α値でのBaseline MergeとSST-Mergeを実行するスクリプト

α = 0.1, 0.2, ..., 1.0 の10パターンでマージを実行
既存のモデルはスキップ

既存の実装を呼び出し:
- baseline_merge.py: TIES, DARE, Task Arithmetic
- sst_merge.py: SST-Merge (GEVP-based)
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
num = input("gpu num:")
os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from safetensors.torch import load_file, save_file
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# 既存の実装をインポート
from scripts.merging.baseline_merge import CustomBaselineMerger, load_adapter, save_merged_adapter
from core.sst_merge import SSTMerge, create_dataloader, create_utility_dataloader_from_hf, GEVPSolver

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

# α値のリスト
alpha_values = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

# マージ手法
baseline_methods = ["task_arithmetic", "ties", "dare"]

# SST-Merge 設定
sst_use_layerwise = True   # Layer-wise重み調整を使用するか
sst_use_gevp = True        # GEVP-based mask使用
sst_max_fim_samples = 500  # FIM計算サンプル数
sst_top_k_ratio = None     # Top-k選択比率 (None=ソフトマスク)

# TIES/DAREパラメータ
ties_density = 0.5
dare_drop_rate = 0.9

# データパス (SST-Merge用)
safety_data_path = "../data/response_dataframe.csv"

# A5 = RepliQA, A6 = Alpaca
utility_datasets = {
    "A5_A7": {"name": "ServiceNow/repliqa", "split": "repliqa_0"},
    "A6_A7": {"name": "tatsu-lab/alpaca", "split": "train"},
}

output_dir = "../../models/merged/sst_merge/full/merge_model"
full_model_dir = "../../models/finetuned/full/FT_model_full"  # フルモデル出力先
#####################################################


def ensure_full_model(adapter_path: str, adapter_type: str) -> str:
    """
    LoRAアダプターからフルモデルを確保
    既に存在すればそのパスを返し、なければ変換する
    
    Args:
        adapter_path: LoRAアダプターのパス
        adapter_type: "A5_utility" or "A6_utility" or "A7_safety"
    
    Returns:
        フルモデルのパス
    """
    full_model_name_map = {
        "A5_utility": "A5_utility_full",
        "A6_utility": "A6_utility_full",
        "A7_safety": "A7_safety_full",
    }
    
    if adapter_type not in full_model_name_map:
        raise ValueError(f"Unknown adapter_type: {adapter_type}")
    
    full_model_name = full_model_name_map[adapter_type]
    full_model_path = Path(full_model_dir) / full_model_name
    
    # 既に存在するかチェック
    if (full_model_path / "config.json").exists():
        logger.info(f"[EXISTS] Full model: {full_model_name}")
        return str(full_model_path)
    
    # 変換が必要
    logger.info(f"[CONVERT] Converting {adapter_type} to full model...")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        
        # ベースモデル + アダプター → フルモデル
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()
        
        # 保存
        full_model_path.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(full_model_path, safe_serialization=True, max_shard_size="5GB")
        tokenizer.save_pretrained(full_model_path)
        
        logger.info(f"[OK] Converted to: {full_model_path}")
        
        del model
        torch.cuda.empty_cache()
        
        return str(full_model_path)
        
    except Exception as e:
        logger.error(f"[FAIL] Failed to convert {adapter_type}: {e}")
        raise


def get_baseline_output_name(pair_name: str, method: str, alpha: float) -> str:
    """Baseline用の出力フォルダ名を生成"""
    alpha_str = f"a{alpha}"
    return f"{pair_name}_{method}_{alpha_str}"


def get_sst_output_name(pair_name: str, alpha: float, use_layerwise: bool = True) -> str:
    """SST用の出力フォルダ名を生成"""
    alpha_str = f"a{alpha}"
    layerwise_str = "lw" if use_layerwise else "nolw"
    return f"{pair_name}_sst_{alpha_str}_{layerwise_str}_soft_add"


def check_exists(output_path: Path) -> bool:
    """既にマージ済みモデルが存在するかチェック"""
    if output_path.exists():
        safetensor = output_path / "adapter_model.safetensors"
        config = output_path / "adapter_config.json"
        if safetensor.exists() and config.exists():
            return True
    return False


def main():
    logger.info("="*70)
    logger.info("Run All Merges: Baseline (mergekit) + SST-Merge (GEVP)")
    logger.info(f"α values: {alpha_values}")
    logger.info("="*70)
    
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    # mergekitベースのマージャー (フルモデルマージ)
    mergekit_merger = None
    try:
        from scripts.merging.baseline_merge import MergekitMerger
        mergekit_merger = MergekitMerger(model_id)
        logger.info("✓ Using MergekitMerger for baseline methods")
    except Exception as e:
        logger.error(f"Failed to initialize MergekitMerger: {e}")
        logger.error("Please check mergekit installation")
        return
    
    # 統計
    num_baseline = len(merge_pairs) * len(alpha_values) * len(baseline_methods)
    num_sst = len(merge_pairs) * len(alpha_values)
    total_tasks = num_baseline + num_sst
    completed = 0
    skipped = 0
    failed = 0
    
    # Safety dataloader (SST-Merge用、全ペア共通)
    safety_dataloader = None
    if sst_use_gevp and Path(safety_data_path).exists():
        safety_dataloader = create_dataloader(safety_data_path)
        logger.info(f"Loaded safety data from {safety_data_path}")
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info("="*60)
        
        # ============================================================
        # Baseline Methods (TIES, DARE, Task Arithmetic)
        # baseline_merge.py の MergekitMerger を使用 → フルモデル生成
        # ============================================================
        for method in baseline_methods:
            for alpha in alpha_values:
                # weights: [utility_weight, safety_weight]
                weights = [1.0 - alpha, alpha]
                
                output_name = get_baseline_output_name(pair_name, method, alpha)
                output_path = output_base / output_name
                
                # 既存チェック（フルモデル用）
                if output_path.exists():
                    config_file = output_path / "config.json"
                    if config_file.exists():
                        logger.info(f"[SKIP] Already exists: {output_name}")
                        skipped += 1
                        continue
                
                try:
                    # MergekitMergerでフルモデルマージ
                    logger.info(f"Merging with mergekit: {method} (α={alpha})")
                    
                    success = mergekit_merger.merge_with_mergekit(
                        method=method,
                        utility_path=utility_path,
                        safety_path=safety_path,
                        output_path=str(output_path),
                        weights=weights,
                        density=ties_density,
                        drop_rate=dare_drop_rate,
                    )
                    
                    if success:
                        logger.info(f"[OK] {method}: {output_name}")
                        completed += 1
                    else:
                        logger.error(f"[FAIL] {method}: {output_name}")
                        failed += 1
                    
                except Exception as e:
                    logger.error(f"[FAIL] {output_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed += 1
        
        # ============================================================
        # SST-Merge (GEVP-based)
        # sst_merge.py の SSTMerge を使用 → フルモデル生成
        # ============================================================
        
        # フルモデルを準備
        try:
            # Utility full model
            if "A5" in pair_name:
                utility_full_path = ensure_full_model(utility_path, "A5_utility")
            elif "A6" in pair_name:
                utility_full_path = ensure_full_model(utility_path, "A6_utility")
            else:
                utility_full_path = ensure_full_model(utility_path, "A5_utility")  # デフォルト
            
            # Safety full model
            safety_full_path = ensure_full_model(safety_path, "A7_safety")
            
        except Exception as e:
            logger.error(f"Skipping SST-Merge for {pair_name}: {e}")
            failed += len(alpha_values)
            continue
        
        # Utility dataloader (ペアごとに異なる)
        utility_dataloader = None
        if sst_use_gevp and pair_name in utility_datasets:
            try:
                ds_info = utility_datasets[pair_name]
                utility_dataloader = create_utility_dataloader_from_hf(
                    dataset_name=ds_info["name"],
                    split=ds_info["split"],
                    max_samples=sst_max_fim_samples
                )
            except Exception as e:
                logger.warning(f"Failed to load utility data for {pair_name}: {e}")
        
        # Pre-compute FIM/GEVP/Mask (Optimization)
        F_benign = None
        F_harm = None
        eigenvalues = None
        safety_mask = None
        
        can_use_gevp = (sst_use_gevp and utility_dataloader is not None and safety_dataloader is not None)
        
        if can_use_gevp:
            try:
                logger.info("Optimization: Pre-computing FIM/GEVP/Mask for Full Models...")
                
                # Use a temporary merger instance for calculation
                temp_merger = SSTMerge(
                    safety_weight=0.5, # Dummy value
                    use_layerwise_weights=sst_use_layerwise,
                    use_gevp=True,
                    regularization=1e-6,
                    top_k_ratio=sst_top_k_ratio,
                    device='cuda'
                )
                
                # Load tokenizer for FIM calculation
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Compute Full FIMs
                logger.info("Computing Utility Full FIM...")
                F_benign = temp_merger.compute_full_fim(
                    utility_full_path, tokenizer, utility_dataloader, sst_max_fim_samples, param_type="trainable"
                )
                
                logger.info("Computing Safety Full FIM...")
                F_harm = temp_merger.compute_full_fim(
                    safety_full_path, tokenizer, safety_dataloader, sst_max_fim_samples, param_type="trainable"
                )
                
                # Solve GEVP
                logger.info("Solving GEVP...")
                gevp_solver = GEVPSolver(regularization=1e-6)
                eigenvalues, _ = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
                
                # Compute Mask (Once, as sst_top_k_ratio is constant)
                # If sst_top_k_ratio is None, mask is soft mask based on eigenvalues
                logger.info(f"Computing Safety Mask (top_k={sst_top_k_ratio})...")
                safety_mask = gevp_solver.compute_safety_mask(eigenvalues, sst_top_k_ratio)
                
                logger.info("Optimization: Pre-computation complete.")
                
                del temp_merger, tokenizer
                torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"Failed to pre-compute GEVP for {pair_name}: {e}")
                import traceback
                traceback.print_exc()
                # Continue without optimization (or skip SST if critical?)
                # Since SSTMerge.merge_full_models has fallback logic if we pass None, 
                # we can continue, but it will try to recompute (and likely fail again or be slow).
                # But let's let the loop try.
        
        for alpha in alpha_values:
            output_name = get_sst_output_name(pair_name, alpha, sst_use_layerwise) + "_full"
            output_path = output_base / output_name
            
            # 既存チェック（フルモデル用）
            if output_path.exists():
                config_file = output_path / "config.json"
                if config_file.exists():
                    logger.info(f"[SKIP] Already exists: {output_name}")
                    skipped += 1
                    continue
            
            try:
                # sst_merge.py の SSTMerge.merge_full_models() を使用
                sst_merger = SSTMerge(
                    safety_weight=alpha,
                    use_layerwise_weights=sst_use_layerwise,
                    use_gevp=sst_use_gevp,
                    regularization=1e-6,
                    top_k_ratio=sst_top_k_ratio,
                )
                
                # フルモデル同士をマージ (Pass cached values)
                sst_merger.merge_full_models(
                    utility_model_path=utility_full_path,
                    safety_model_path=safety_full_path,
                    output_path=str(output_path),
                    utility_dataloader=utility_dataloader,
                    safety_dataloader=safety_dataloader,
                    max_samples=sst_max_fim_samples,
                    f_benign=F_benign,
                    f_harm=F_harm,
                    eigenvalues=eigenvalues,
                    safety_mask=safety_mask
                )
                
                # メタデータ保存
                metadata = {
                    "utility_model": utility_full_path,
                    "safety_model": safety_full_path,
                    "merge_method": "sst_gevp_full",
                    "merge_formula": "utility + α * mask * safety (GEVP-based, full model)",
                    "alpha": alpha,
                    "use_layerwise": sst_use_layerwise,
                    "use_gevp": sst_use_gevp,
                    "param_type": "trainable",
                    "base_model": model_id,
                    "timestamp": datetime.now().isoformat(),
                }
                
                with open(output_path / "merge_metadata.json", 'w') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                logger.info(f"[OK] SST (Full): {output_name}")
                completed += 1
                
            except Exception as e:
                logger.error(f"[FAIL] {output_name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
    
    # 結果サマリー
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total tasks:  {total_tasks}")
    logger.info(f"  Baseline:   {num_baseline} (TIES/DARE/TA × {len(alpha_values)} α) → Full Models")
    logger.info(f"  SST:        {num_sst} (GEVP-based) → Full Models")
    logger.info(f"Completed:    {completed}")
    logger.info(f"Skipped:      {skipped}")
    logger.info(f"Failed:       {failed}")
    logger.info(f"Output dir:   {output_base}")
    logger.info(f"Full models:  {Path(full_model_dir)}")
    logger.info("="*70)



if __name__ == "__main__":
    main()
