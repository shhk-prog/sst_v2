"""
全α値でのBaseline MergeとSST-Mergeを実行するスクリプト（アダプターベース + フルモデル変換）

すべてのマージをアダプターレベルで実行し、その後フルモデルに変換することで公平な比較を実現

α = 0.1, 0.2, ..., 1.0 の10パターンでマージを実行
既存のモデルはスキップ

変更点:
- Baseline mergeもアダプターレベルで実行（CustomBaselineMergerを使用）
- SST-Mergeもアダプターレベルで実行
- 各マージ後、アダプターをフルモデルに変換
- すべてフルモデルとして評価可能
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

# 既存の実装をインポート
from scripts.merging.baseline_merge import CustomBaselineMerger, load_adapter, save_merged_adapter
from core.sst_merge import SSTMerge, create_dataloader, create_utility_dataloader_from_hf

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
alpha_values = [1.0]

# マージ手法
baseline_methods = ["task_arithmetic", "ties", "dare"]

# TIES/DAREパラメータ
ties_density = 0.5
dare_drop_rate = 0.9

# SST-Merge 設定
sst_k_values = [5]  # FIM計算の次元数（複数指定可能）
use_layerwise_options = [False]  # Layerwise重み調整: [False] or [True] or [False, True]
use_gevp_options = [False]  # GEVP使用: [True] or [False] or [True, False]
                            # False=GEVPマスク無効化でTask Arithmetic風の動作をテスト
sst_max_fim_samples = 500  # FIM計算サンプル数

# データパス (SST-Merge用)
safety_data_path = "../data/response_dataframe.csv"

# A5 = RepliQA, A6 = Alpaca
utility_datasets = {
    "A5_A7": {"name": "ServiceNow/repliqa", "split": "repliqa_0"},
    "A6_A7": {"name": "tatsu-lab/alpaca", "split": "train"},
}

output_adapter_dir = "../../models/merged/sst_merge/adapters/merge_adapters"  # アダプター出力先
output_full_dir = "../../models/merged/sst_merge/full/merge_model"  # フルモデル出力先
#####################################################


def convert_adapter_to_full(
    adapter_path: str,
    output_path: str,
    base_model: str = model_id
) -> bool:
    """
    LoRAアダプターをフルモデルに変換
    
    Args:
        adapter_path: アダプターのパス（.safetensors or .bin）
        output_path: フルモデルの出力先
        base_model: ベースモデル名
    
    Returns:
        成功したかどうか
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


def get_baseline_output_name(pair_name: str, method: str, alpha: float) -> str:
    """Baseline用の出力名を生成"""
    alpha_str = f"a{alpha}"
    return f"{pair_name}_{method}_{alpha_str}"


def get_sst_output_name(pair_name: str, alpha: float, k: int, use_layerwise: bool = False, use_gevp: bool = True) -> str:
    """
    SST-Mergeの出力名を生成
    
    Args:
        pair_name: ペア名 (e.g., "A5_A7")
        alpha: Safety重み
        k: FIM次元数
        use_layerwise: Layer-wise調整の有無
        use_gevp: GEVP使用の有無
    
    Returns:
        出力名 (e.g., "A5_A7_sst_k10_lw_a0.5" or "A5_A7_sst_k10_nogevp_a0.5")
    """
    lw_str = "_lw" if use_layerwise else ""
    gevp_str = "" if use_gevp else "_nogevp"
    return f"{pair_name}_sst_k{k}{lw_str}{gevp_str}_a{alpha}"


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
    logger.info("Run All Merges: Adapter-Level Merge + Full Model Conversion")
    logger.info(f"α values: {alpha_values}")
    logger.info("="*70)
    
    adapter_base = Path(output_adapter_dir)
    adapter_base.mkdir(parents=True, exist_ok=True)
    
    full_base = Path(output_full_dir)
    full_base.mkdir(parents=True, exist_ok=True)
    
    # カスタムマージャー（アダプターレベル）
    custom_merger = CustomBaselineMerger()
    
    # 統計
    num_baseline = len(merge_pairs) * len(alpha_values) * len(baseline_methods)
    num_sst = len(merge_pairs) * len(alpha_values) * len(sst_k_values) * len(use_layerwise_options) * len(use_gevp_options)
    total_tasks = num_baseline + num_sst
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
        
        # ============================================================
        # Baseline Methods (TIES, DARE, Task Arithmetic)
        # アダプターレベルでマージ → フルモデルに変換
        # ============================================================
        
        # アダプターをロード
        try:
            utility_adapter = load_adapter(utility_path)
            safety_adapter = load_adapter(safety_path)
        except FileNotFoundError as e:
            logger.error(f"Skipping {pair_name}: {e}")
            failed += len(baseline_methods) * len(alpha_values)
            continue
        
        adapters = [utility_adapter, safety_adapter]
        
        for method in baseline_methods:
            for alpha in alpha_values:
                # weights: [utility_weight, safety_weight]
                weights = [1.0 - alpha, alpha]
                
                output_name = get_baseline_output_name(pair_name, method, alpha)
                adapter_output = adapter_base / f"{output_name}_adapter"
                full_output = full_base / output_name
                
                # フルモデルの存在チェック（最終的な目標）
                if check_exists_full(full_output):
                    logger.info(f"[SKIP] Full model exists: {output_name}")
                    skipped += 1
                    continue
                
                try:
                    # Step 1: アダプターレベルでマージ
                    if not check_exists_adapter(adapter_output):
                        logger.info(f"Merging adapter: {method} (α={alpha})")
                        
                        config = {
                            "weights": weights,
                            "density": ties_density if method == "ties" else None,
                            "drop_rate": dare_drop_rate if method == "dare" else None,
                        }
                        config = {k: v for k, v in config.items() if v is not None}
                        
                        merged = custom_merger.merge(method, adapters, **config)
                        
                        metadata = {
                            "utility_adapter": utility_path,
                            "safety_adapter": safety_path,
                            "merge_method": method,
                            "merge_config": config,
                            "base_model": model_id,
                            "merge_level": "adapter",
                            "timestamp": datetime.now().isoformat(),
                        }
                        
                        save_merged_adapter(merged, adapter_output, utility_path, metadata)
                        logger.info(f"[OK] Adapter saved: {adapter_output}")
                    else:
                        logger.info(f"[EXISTS] Using existing adapter: {adapter_output.name}")
                    
                    # Step 2: アダプターをフルモデルに変換
                    logger.info(f"Converting to full model: {output_name}")
                    success = convert_adapter_to_full(
                        str(adapter_output),
                        str(full_output),
                        model_id
                    )
                    
                    if success:
                        logger.info(f"[OK] Full model: {output_name}")
                        completed += 1
                        
                        # アダプターを削除してディスク容量節約（オプション）
                        # shutil.rmtree(adapter_output)
                    else:
                        logger.error(f"[FAIL] Full model conversion: {output_name}")
                        failed += 1
                    
                except Exception as e:
                    logger.error(f"[FAIL] {output_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed += 1
        
        # ============================================================
        # SST-Merge (GEVP-based)
        # アダプターレベルでマージ → フルモデルに変換
        # ============================================================
        
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
            except Exception as e:
                logger.warning(f"Failed to load utility data for {pair_name}: {e}")
        
        # SST-Merge: k値、layerwise、GEVPオプションごとにループ
        for sst_k in sst_k_values:
            for use_layerwise in use_layerwise_options:
                for use_gevp in use_gevp_options:
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
                            # Step 1: アダプターレベルでSST-Merge
                            if not check_exists_adapter(adapter_output):
                                logger.info(f"SST-Merging adapter: k={sst_k}, layerwise={use_layerwise}, gevp={use_gevp}, α={alpha}")
                                
                                # アダプターをロード
                                utility_adapter_dict = load_adapter(utility_path)
                                safety_adapter_dict = load_adapter(safety_path)
                                
                                # SSTMergerを初期化
                                sst_merger = SSTMerge(
                                    safety_weight=alpha,
                                    use_layerwise_weights=use_layerwise,
                                    use_gevp=use_gevp,  # GEVPマスク有効/無効を設定
                                    regularization=1e-6,
                                    top_k_ratio=None,
                                    device='cuda'
                                )
                                
                                # ベースモデルとトークナイザーをロード
                                logger.info("Loading base model for SST-Merge...")
                                base_model = AutoModelForCausalLM.from_pretrained(
                                    model_id,
                                    torch_dtype=torch.bfloat16,
                                    device_map="auto"
                                )
                                base_tokenizer = AutoTokenizer.from_pretrained(model_id)
                                
                                # マージ実行
                                merged_adapter = sst_merger.merge(
                                    model=base_model,
                                    tokenizer=base_tokenizer,
                                    utility_adapter=utility_adapter_dict,
                                    safety_adapter=safety_adapter_dict,
                                    utility_dataloader=utility_dataloader,
                                    safety_dataloader=safety_dataloader,
                                    max_samples=sst_max_fim_samples
                                )
                                
                                # メモリ解放
                                del base_model
                                del base_tokenizer
                                torch.cuda.empty_cache()
                                
                                # アダプターを保存
                                metadata = {
                                    "utility_adapter": utility_path,
                                    "safety_adapter": safety_path,
                                    "merge_method": "sst_merge",
                                    "k": sst_k,
                                    "alpha": alpha,
                                    "use_layerwise": use_layerwise,
                                    "use_gevp": use_gevp,  # metadataにGEVPフラグを記録
                                    "base_model": model_id,
                                    "merge_level": "adapter",
                                    "timestamp": datetime.now().isoformat(),
                                }
                                
                                save_merged_adapter(merged_adapter, adapter_output, utility_path, metadata)
                                logger.info(f"[OK] SST adapter saved: {adapter_output}")
                            else:
                                logger.info(f"[EXISTS] Using existing SST adapter: {adapter_output.name}")
                            
                            # Step 2: アダプターをフルモデルに変換
                            logger.info(f"Converting SST adapter to full model: {output_name}")
                            success = convert_adapter_to_full(
                                str(adapter_output),
                                str(full_output),
                                model_id
                            )
                            
                            if success:
                                logger.info(f"[OK] SST full model: {output_name}")
                                completed += 1
                            else:
                                logger.error(f"[FAIL] SST full model conversion: {output_name}")
                                failed += 1
                            
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
    logger.info(f"  Baseline:   {num_baseline} (TIES/DARE/TA × {len(alpha_values)} α)")
    logger.info(f"  SST:        {num_sst} (k={sst_k_values} × layerwise={use_layerwise_options} × gevp={use_gevp_options} × {len(alpha_values)} α)")
    logger.info(f"Completed:    {completed}")
    logger.info(f"Skipped:      {skipped}")
    logger.info(f"Failed:       {failed}")
    logger.info(f"Adapters:     {adapter_base}")
    logger.info(f"Full models:  {full_base}")
    logger.info("="*70)
    logger.info("\nAll models are now at the same level (full models) for fair comparison!")


if __name__ == "__main__":
    main()
