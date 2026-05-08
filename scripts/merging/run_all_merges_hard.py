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
from peft import PeftModel
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

# マージするアダプターのペア（CWD: sst_merge_v5 から実行する前提）
merge_pairs = [
    ("models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4", 
     "models/finetuned/adapters/FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A5_A7"),
    ("models/finetuned/adapters/FT_model/A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4",
     "models/finetuned/adapters/FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
     "A6_A7"),
]

# α値のリスト
alpha_values = [0.05,0.07,0.09,0.1,0.12,0.15,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

# マージ手法
baseline_methods = []
# "task_arithmetic", "ties", "dare"

# SST-Merge 設定
sst_use_layerwise = False   # Layer-wise重み調整を使用するか True  False
sst_use_gevp = True        # GEVP-based mask使用
sst_max_fim_samples = 500  # FIM計算サンプル数
sst_k_values = [5, 10, 20, 30,40,50] # Top-k選択比率 (k=5 -> 5%)
sst_top_k_ratio = None     # (未使用: loop内で上書き)

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

output_dir = "models/merged/sst_merge/full/merge_model"
full_model_dir = "models/finetuned/full/FT_model_full"  # フルモデル出力先
adapter_output_dir = "models/merged/sst_merge/adapters/merge_adapters"  # アダプター出力先
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
        
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        
        model = PeftModel.from_pretrained(base, adapter_path)
        model = model.merge_and_unload()
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model.save_pretrained(output_path, safe_serialization=True, max_shard_size="5GB")
        
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"✓ Full model saved: {output_path}")
        
        del model, base
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert adapter: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_baseline_output_name(pair_name: str, method: str, alpha: float) -> str:
    """Baseline用の出力フォルダ名を生成"""
    alpha_str = f"a{alpha}"
    return f"{pair_name}_{method}_{alpha_str}"


def get_sst_output_name(pair_name: str, alpha: float, k: int, use_layerwise: bool = True) -> str:
    """SST用の出力フォルダ名を生成 (Hard Mask)"""
    alpha_str = f"a{alpha}"
    # layerwise_str = "lw" if use_layerwise else "nolw"
    layerwise_str = "_lw" if use_layerwise else ""
    # Hard Maskであることを明記 (Additivie Hard)
    # return f"{pair_name}_sst_k{k}_{alpha_str}_{layerwise_str}_hard"
    return f"{pair_name}_sst_k{k}_{alpha_str}{layerwise_str}_hard"


def check_exists(output_path: Path) -> bool:
    """既にマージ済みモデルが存在するかチェック"""
    if output_path.exists():
        config = output_path / "config.json"
        if config.exists():
            return True
    return False


def main():
    logger.info("="*70)
    logger.info("Run All Merges: Baseline (mergekit) + SST-Merge (GEVP Hard Mask)")
    logger.info(f"α values: {alpha_values}")
    logger.info(f"k values: {sst_k_values}")
    logger.info("="*70)
    
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    adapter_base = Path(adapter_output_dir)
    adapter_base.mkdir(parents=True, exist_ok=True)
    
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
    num_sst = len(merge_pairs) * len(alpha_values) * len(sst_k_values)
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
                if check_exists(output_path):
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
        # SST-Merge (GEVP-based Hard Mask)
        # FIM/GEVPを1回計算し使い回す最適化版
        # ============================================================
        
        try:
            # アダプターをロード (1回だけ)
            logger.info("Loading adapters...")
            utility_adapter_dict = load_adapter(utility_path)
            safety_adapter_dict = load_adapter(safety_path)
            
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
                    logger.info(f"✓ Loaded utility dataloader for {pair_name}")
                except Exception as e:
                    logger.warning(f"Failed to load utility data for {pair_name}: {e}")
            
            # FIM/GEVPの事前計算 (最適化: ペアごとに1回だけ)
            can_use_gevp = (sst_use_gevp and utility_dataloader is not None and safety_dataloader is not None)
            
            F_benign = None
            F_harm = None
            eigenvalues = None
            gevp_solver = None
            
            if can_use_gevp:
                logger.info("\nOptimization: Pre-computing FIM and GEVP (1回だけ)...")
                
                # ベースモデルをロード (FIM計算用に一時的に)
                logger.info("Loading base model for FIM calculation...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    device_map="auto"
                )
                base_tokenizer = AutoTokenizer.from_pretrained(model_id)
                if base_tokenizer.pad_token is None:
                    base_tokenizer.pad_token = base_tokenizer.eos_token
                
                # LoRA設定を推定
                lora_r = 16
                for key, val in utility_adapter_dict.items():
                    if 'lora_A' in key:
                        lora_r = val.shape[0]
                        break
                    elif 'lora_B' in key:
                        lora_r = val.shape[1]
                        break
                
                from peft import LoraConfig, TaskType, get_peft_model
                from core.sst_merge import FIMCalculator
                
                lora_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    r=lora_r,
                    lora_alpha=lora_r * 2,
                    lora_dropout=0.05,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                  "gate_proj", "up_proj", "down_proj"],
                    bias="none"
                )
                
                # Utility FIM計算
                logger.info("Computing Utility FIM (F_benign)...")
                peft_model = get_peft_model(base_model, lora_config)
                # アダプターの重みを読み込み
                for name, param in peft_model.named_parameters():
                    if param.requires_grad:
                        for adapter_key, adapter_val in utility_adapter_dict.items():
                            if adapter_key in name or name.endswith(adapter_key):
                                param.data.copy_(adapter_val.to(param.device))
                                break
                
                fim_calc = FIMCalculator(peft_model, base_tokenizer, 'cuda', 1e-6)
                F_benign = fim_calc.compute_fim(utility_dataloader, sst_max_fim_samples)
                del peft_model, fim_calc
                torch.cuda.empty_cache()
                
                # Safety FIM計算
                logger.info("Computing Safety FIM (F_harm)...")
                peft_model = get_peft_model(base_model, lora_config)
                for name, param in peft_model.named_parameters():
                    if param.requires_grad:
                        for adapter_key, adapter_val in safety_adapter_dict.items():
                            if adapter_key in name or name.endswith(adapter_key):
                                param.data.copy_(adapter_val.to(param.device))
                                break
                
                fim_calc = FIMCalculator(peft_model, base_tokenizer, 'cuda', 1e-6)
                F_harm = fim_calc.compute_fim(safety_dataloader, sst_max_fim_samples)
                del peft_model, fim_calc
                torch.cuda.empty_cache()
                
                # ベースモデルを解放
                logger.info("Unloading base model to free memory...")
                del base_model, base_tokenizer
                torch.cuda.empty_cache()
                
                # GEVP解法
                logger.info("Solving GEVP...")
                gevp_solver = GEVPSolver(regularization=1e-6)
                eigenvalues, _ = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
                
                logger.info("✓ FIM/GEVP pre-computation complete!")
            
            # マスクのキャッシュ (k -> mask)
            mask_cache = {}
            
            # Loop over k (Hard Mask ratios)
            for sst_k in sst_k_values:
                top_k_ratio = sst_k / 100.0  # e.g., 5 -> 0.05
                
                # マスクの取得またはキャッシュ
                safety_mask = None
                if can_use_gevp and gevp_solver is not None and eigenvalues is not None:
                    if top_k_ratio not in mask_cache:
                        logger.info(f"Computing safety mask for k={sst_k} (ratio={top_k_ratio})...")
                        mask_cache[top_k_ratio] = gevp_solver.compute_safety_mask(eigenvalues, top_k_ratio)
                    safety_mask = mask_cache[top_k_ratio]
                
                for alpha in alpha_values:
                    output_name = get_sst_output_name(pair_name, alpha, sst_k, sst_use_layerwise)
                    adapter_output = adapter_base / f"{output_name}_adapter"
                    full_output = output_base / f"{output_name}_full"
                    
                    # フルモデルの存在チェック
                    if check_exists(full_output):
                        logger.info(f"[SKIP] Already exists: {output_name}")
                        skipped += 1
                        continue
                    
                    try:
                        # Step 1: アダプターレベルでSST-Merge (Hard Mask)
                        if not (adapter_output.exists() and (adapter_output / "adapter_config.json").exists()):
                            logger.info(f"SST-Merging (Hard): k={sst_k}, top_k_ratio={top_k_ratio}, α={alpha}")
                            
                            # SSTMergeインスタンスを作成して _merge_with_mask を直接呼ぶ
                            sst_merger = SSTMerge(
                                safety_weight=alpha,
                                use_layerwise_weights=sst_use_layerwise,
                                use_gevp=sst_use_gevp,
                                regularization=1e-6,
                                top_k_ratio=top_k_ratio,
                                device='cuda'
                            )
                            
                            if safety_mask is not None:
                                # 事前計算済みマスクで直接マージ（モデル不要！）
                                merged_adapter = sst_merger._merge_with_mask(
                                    utility_adapter_dict,
                                    safety_adapter_dict,
                                    safety_mask
                                )
                            else:
                                # GEVPなしの場合はシンプルマージ
                                merged_adapter = sst_merger._simple_merge(
                                    utility_adapter_dict,
                                    safety_adapter_dict
                                )
                            
                            # アダプターを保存
                            adapter_metadata = {
                                "utility_adapter": utility_path,
                                "safety_adapter": safety_path,
                                "merge_method": "sst_merge_hard",
                                "k": sst_k,
                                "top_k_ratio": top_k_ratio,
                                "alpha": alpha,
                                "use_layerwise": sst_use_layerwise,
                                "use_gevp": sst_use_gevp,
                                "base_model": model_id,
                                "merge_level": "adapter",
                                "timestamp": datetime.now().isoformat(),
                            }
                            
                            save_merged_adapter(merged_adapter, adapter_output, utility_path, adapter_metadata)
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
                            # フルモデルにメタデータを追加
                            metadata = {
                                "utility_adapter": utility_path,
                                "safety_adapter": safety_path,
                                "merge_method": "sst_gevp_hard",
                                "merge_formula": "utility + α * hard_mask * safety (GEVP-based, hard mask)",
                                "alpha": alpha,
                                "k": sst_k,
                                "top_k_ratio": top_k_ratio,
                                "use_layerwise": sst_use_layerwise,
                                "use_gevp": sst_use_gevp,
                                "base_model": model_id,
                                "timestamp": datetime.now().isoformat(),
                            }
                            
                            with open(full_output / "merge_metadata.json", 'w') as f:
                                json.dump(metadata, f, indent=2, ensure_ascii=False)
                            
                            logger.info(f"[OK] SST (Hard k={sst_k}): {output_name}")
                            completed += 1
                        else:
                            logger.error(f"[FAIL] Full model conversion: {output_name}")
                            failed += 1
                        
                    except Exception as e:
                        logger.error(f"[FAIL] {output_name}: {e}")
                        import traceback
                        traceback.print_exc()
                        failed += 1
        
        except Exception as e:
            logger.error(f"Critical error in SST-Merge for {pair_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += len(sst_k_values) * len(alpha_values)
    
    # 結果サマリー
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total tasks:  {total_tasks}")
    logger.info(f"  Baseline:   {num_baseline} (TIES/DARE/TA × {len(alpha_values)} α) → Full Models")
    logger.info(f"  SST:        {num_sst} (k={sst_k_values} × {len(alpha_values)} α) → Full Models (Hard Mask)")
    logger.info(f"Completed:    {completed}")
    logger.info(f"Skipped:      {skipped}")
    logger.info(f"Failed:       {failed}")
    logger.info(f"Output dir:   {output_base}")
    logger.info(f"Full models:  {Path(full_model_dir)}")
    logger.info("="*70)



if __name__ == "__main__":
    main()
