"""
補間型SST-Mergeを実行するスクリプト

出力フォルダ:
- アダプター: ./merge_adapters_interpolation
- フルモデル: ./merge_model_interpolation

マージ方式: merged = (1-α) × utility + α × safety
→ Task Arithmetic互換の動作
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
from peft import PeftModel
from safetensors.torch import load_file, save_file
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# インポート
from scripts.merging.baseline_merge import load_adapter, save_merged_adapter
from core.sst_merge_interpolation import SSTMergeInterpolation
from core.sst_merge import create_dataloader, create_utility_dataloader_from_hf, GEVPSolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
model_id = "meta-llama/Llama-3.1-8B-Instruct"

# マージするアダプターのペア
# スクリプトの場所を基準に絶対パスを解決するヘルパー
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent

# 相対パスはプロジェクトルート基準で記述
adapter_base = project_root / "models/finetuned/adapters/FT_model"

merge_pairs = [
    (str(adapter_base / "A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4"),
     str(adapter_base / "A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4"),
     "A5_A7"),
    (str(adapter_base / "A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4"),
     str(adapter_base / "A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4"),
     "A6_A7"),
]

# α値のリスト
alpha_values = [0.05,0.07,0.09,0.1,0.12,0.15,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

# SST-Merge 設定（補間モード）
sst_k_values = [5,10,20,30,40,50]  # FIM計算の次元数
use_layerwise_options = [True, False]  # Layerwise重み調整
use_gevp_options = [True]  # GEVP使用
sst_max_fim_samples = 500  # FIM計算サンプル数

# データパス (SST-Merge用)
# dataディレクトリはsst_merge_v5の兄弟ディレクトリにある
safety_data_path = str(project_root.parent / "data/response_dataframe.csv")

# A5 = RepliQA, A6 = Alpaca
utility_datasets = {
    "A5_A7": {"name": "ServiceNow/repliqa", "split": "repliqa_0"},
    "A6_A7": {"name": "tatsu-lab/alpaca", "split": "train"},
}

# 出力ディレクトリ（補間モード専用）
output_adapter_dir = str(project_root / "models/merged/interpolation/adapters/merge_adapters_interpolation")
output_full_dir = str(project_root / "models/merged/interpolation/full/merge_model_interpolation")
#####################################################


def convert_adapter_to_full(
    adapter_path: str,
    output_path: str,
    base_model: str = model_id
) -> bool:
    """
    LoRAアダプターをフルモデルに変換
    """
    try:
        logger.info(f"Converting adapter to full model: {adapter_path}")
        
        # ベースモデルをロード
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        
        # アダプターを適用
        model = PeftModel.from_pretrained(base, adapter_path)
        
        # フルモデルにマージ
        model = model.merge_and_unload()
        
        # 保存
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model.save_pretrained(output_path, safe_serialization=True, max_shard_size="5GB")
        
        # トークナイザーも保存
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"✓ Full model saved: {output_path}")
        
        # メモリ解放
        del model
        del base
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert adapter: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_sst_output_name(pair_name: str, alpha: float, k: int, use_layerwise: bool = False, use_gevp: bool = True) -> str:
    """
    SST-Merge（補間モード）の出力名を生成
    
    例: A6_A7_sst_interp_k5_nogevp_a1.0
    """
    lw_str = "_lw" if use_layerwise else ""
    gevp_str = "" if use_gevp else "_nogevp"
    return f"{pair_name}_sst_interp_k{k}{lw_str}{gevp_str}_a{alpha}"


def check_exists_adapter(output_path: Path) -> bool:
    """アダプターが存在するかチェック"""
    if output_path.exists():
        safetensor = output_path / "adapter_model.safetensors"
        config = output_path / "adapter_config.json"
        if safetensor.exists() and config.exists():
            return True
    return False


def check_exists_full(output_path: Path) -> bool:
    """フルモデルが存在するかチェック"""
    if output_path.exists():
        config = output_path / "config.json"
        if config.exists():
            return True
    return False


def main():
    logger.info("="*70)
    logger.info("Run SST-Merge: INTERPOLATION MODE")
    logger.info("Method: merged = (1-α) × utility + α × safety")
    logger.info(f"α values: {alpha_values}")
    logger.info("="*70)
    
    adapter_base = Path(output_adapter_dir)
    adapter_base.mkdir(parents=True, exist_ok=True)
    
    full_base = Path(output_full_dir)
    full_base.mkdir(parents=True, exist_ok=True)
    
    # 統計
    num_sst = len(merge_pairs) * len(alpha_values) * len(sst_k_values) * len(use_layerwise_options) * len(use_gevp_options)
    completed = 0
    skipped = 0
    failed = 0
    
    # Safety dataloader (SST-Merge用、全ペア共通)
    safety_dataloader = None
    if Path(safety_data_path).exists():
        safety_dataloader = create_dataloader(safety_data_path)
        logger.info(f"Loaded safety data from {safety_data_path}")
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info("="*60)
        
        # Utility dataloader (ペアごとに異なる)
        utility_dataloader = None
        if pair_name in utility_datasets:
            try:
                ds_info = utility_datasets[pair_name]
                utility_dataloader = create_utility_dataloader_from_hf(
                    dataset_name=ds_info["name"],
                    split=ds_info["split"],
                    max_samples=sst_max_fim_samples
                )
                logger.info(f"✓ Loaded utility dataloader for {pair_name}: {len(utility_dataloader)} batches")
            except Exception as e:
                logger.warning(f"Failed to load utility data for {pair_name}: {e}")
                logger.warning("GEVP will be DISABLED due to missing utility dataloader")
        else:
            logger.warning(f"No utility dataset config for {pair_name}")
            logger.warning("GEVP will be DISABLED due to missing utility dataloader")
        
        # Safety dataloaderの状態も確認
        if safety_dataloader:
            logger.info(f"✓ Safety dataloader is available")
        else:
            logger.warning("Safety dataloader is NOT available - GEVP will be DISABLED")

        
        try:
            # Adapters Load (Once per pair)
            logger.info("Loading adapters...")
            utility_adapter_dict = load_adapter(utility_path)
            safety_adapter_dict = load_adapter(safety_path)
            
            # Check if GEVP is possible and needed
            can_use_gevp_base = (utility_dataloader is not None and safety_dataloader is not None)
            need_gevp = any(use_gevp_options) and can_use_gevp_base
            
            # Pre-compute FIM and GEVP (Optimization)
            F_benign = None
            F_harm = None
            eigenvalues = None
            gevp_solver = None
            
            if need_gevp:
                logger.info("\nOptimization: Pre-computing FIM and GEVP...")
                
                # Load Base Model & Tokenizer temporarily
                logger.info("Loading base model for FIM calculation...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    device_map="auto"
                )
                base_tokenizer = AutoTokenizer.from_pretrained(model_id)
                if base_tokenizer.pad_token is None:
                    base_tokenizer.pad_token = base_tokenizer.eos_token
                
                # Helper instance for FIM calculation
                helper = SSTMergeInterpolation(device='cuda')
                
                logger.info("Computing Utility FIM...")
                F_benign = helper.compute_fim(base_model, base_tokenizer, utility_adapter_dict, utility_dataloader, sst_max_fim_samples)
                
                logger.info("Computing Safety FIM...")
                F_harm = helper.compute_fim(base_model, base_tokenizer, safety_adapter_dict, safety_dataloader, sst_max_fim_samples)
                
                # Unload Base Model to free memory
                logger.info("Unloading base model to free memory...")
                del base_model, base_tokenizer
                torch.cuda.empty_cache()
                
                # Solve GEVP
                logger.info("Solving GEVP...")
                gevp_solver = GEVPSolver(regularization=1e-6)
                eigenvalues, _ = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
            
            mask_cache = {}

            # SST-Merge (補間モード): k値、layerwise、GEVPオプションごとにループ
            for sst_k in sst_k_values:
                # Fix: Set top_k_ratio based on k (assuming k is percentage, e.g. 20 -> 0.2)
                top_k_ratio = sst_k / 100.0
                
                # Cache Mask
                safety_mask = None
                if need_gevp and top_k_ratio is not None:
                    if top_k_ratio not in mask_cache:
                        logger.info(f"Computing safety mask for top_k_ratio={top_k_ratio}...")
                        mask_cache[top_k_ratio] = gevp_solver.compute_safety_mask(eigenvalues, top_k_ratio)
                    safety_mask = mask_cache[top_k_ratio]

                for use_layerwise in use_layerwise_options:
                    for use_gevp in use_gevp_options:
                        # Determine if GEVP is actually used for this iteration
                        current_use_gevp = use_gevp and need_gevp
                        
                        for alpha in alpha_values:
                            output_name = get_sst_output_name(pair_name, alpha, sst_k, use_layerwise=use_layerwise, use_gevp=use_gevp)
                            adapter_output = adapter_base / f"{output_name}_adapter"
                            full_output = full_base / output_name
                            
                            # フルモデルの存在チェック
                            if check_exists_full(full_output):
                                logger.info(f"[SKIP] SST full model exists: {output_name}")
                                skipped += 1
                                continue
                            
                            try:
                                # Step 1: アダプターレベルでSST-Merge（補間モード）
                                if not check_exists_adapter(adapter_output):
                                    logger.info(f"SST-Merge (INTERPOLATION): k={sst_k}({top_k_ratio}), layerwise={use_layerwise}, gevp={use_gevp}, α={alpha}")
                                    
                                    # SSTMergerを初期化（補間モード）
                                    sst_merger = SSTMergeInterpolation(
                                        safety_weight=alpha,
                                        use_layerwise_weights=use_layerwise,
                                        use_gevp=use_gevp,
                                        regularization=1e-6,
                                        top_k_ratio=top_k_ratio,  # Correctly set top_k_ratio
                                        device='cuda'
                                    )
                                    
                                    # マージ実行 (Pass cached values AND NO MODEL)
                                    # model=None is safe because we provide pre-computed FIM/GEVP/Mask or allow fallback
                                    merged_adapter = sst_merger.merge(
                                        model=None, 
                                        tokenizer=None,
                                        utility_adapter=utility_adapter_dict,
                                        safety_adapter=safety_adapter_dict,
                                        utility_dataloader=None,
                                        safety_dataloader=None,
                                        max_samples=sst_max_fim_samples,
                                        f_benign=F_benign if current_use_gevp else None,
                                        f_harm=F_harm if current_use_gevp else None,
                                        eigenvalues=eigenvalues if current_use_gevp else None,
                                        safety_mask=safety_mask if current_use_gevp else None
                                    )
                                    
                                    # アダプターを保存
                                    metadata = {
                                        "utility_adapter": utility_path,
                                        "safety_adapter": safety_path,
                                        "merge_method": "sst_gevp_interpolation" if use_gevp else "simple_interpolation",
                                        "alpha": alpha,
                                        "sst_k": sst_k,
                                        "top_k_ratio": top_k_ratio,
                                        "use_layerwise": use_layerwise,
                                        "use_gevp": use_gevp,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    
                                    # utility_pathを絶対パスに
                                    utility_path_abs = (script_dir / utility_path).resolve()
                                    save_merged_adapter(merged_adapter, adapter_output, str(utility_path_abs))
                                    
                                    # メタデータ保存
                                    with open(adapter_output / "merge_metadata.json", 'w') as f:
                                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                                    
                                    logger.info(f"✓ Saved adapter: {output_name}")
                                else:
                                    logger.info(f"[SKIP] Adapter exists: {output_name}")

                                # Step 2: フルモデルに変換
                                # logger.info(f"Converting SST adapter to full model: {output_name}")
                                success = convert_adapter_to_full(
                                    str(adapter_output),
                                    str(full_output),
                                    model_id
                                )
                                
                                if success:
                                    logger.info(f"✓ Saved full model: {output_name}")
                                    completed += 1
                                else:
                                    failed += 1
                                    
                            except Exception as e:
                                logger.error(f"[FAIL] {output_name}: {e}")
                                import traceback
                                traceback.print_exc()
                                failed += 1
        
        except Exception as e:
            logger.error(f"Critical error processing pair {pair_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    
    # 結果サマリー
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total tasks:  {num_sst}")
    logger.info(f"  SST (Interpolation): k={sst_k_values} × layerwise={use_layerwise_options} × gevp={use_gevp_options} × {len(alpha_values)} α")
    logger.info(f"Completed:    {completed}")
    logger.info(f"Skipped:      {skipped}")
    logger.info(f"Failed:       {failed}")
    logger.info(f"Adapters:     {adapter_base}")
    logger.info(f"Full models:  {full_base}")
    logger.info("="*70)
    logger.info("\nInterpolation mode: merged = (1-α) × utility + α × safety")
    logger.info("This is compatible with Task Arithmetic!")


if __name__ == "__main__":
    main()
