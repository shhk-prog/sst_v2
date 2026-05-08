"""
LoRAアダプターをフルモデルに変換するスクリプト

A5 (RepliQA), A6 (Alpaca), A7 (Safety) のLoRAアダプターを
ベースモデルとマージしてフルモデルとして保存します。

出力先:
- FT_model_full/A5_utility_full/
- FT_model_full/A6_utility_full/
- FT_model_full/A7_safety_full/
"""

import os
num = input("gpu num:")
os.environ["CUDA_VISIBLE_DEVICES"] = str(num)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
base_model_id = "meta-llama/Llama-3.1-8B-Instruct"

# 変換するアダプターのリスト
adapters_to_convert = [
    {
        "name": "A5_utility",
        "adapter_path": "./FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4",
        "output_name": "A5_utility_full",
        "description": "RepliQA utility adapter"
    },
    {
        "name": "A6_utility",
        "adapter_path": "./FT_model/A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4",
        "output_name": "A6_utility_full",
        "description": "Alpaca utility adapter"
    },
    {
        "name": "A7_safety",
        "adapter_path": "./FT_model/A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4",
        "output_name": "A7_safety_full",
        "description": "Safety adapter"
    },
]

output_base_dir = "../../models/finetuned/full/FT_model_full"
#####################################################


def check_adapter_exists(adapter_path: str) -> bool:
    """アダプターが存在するかチェック"""
    adapter_path = Path(adapter_path)
    return (adapter_path / "adapter_config.json").exists()


def check_full_model_exists(output_path: str) -> bool:
    """フルモデルが既に存在するかチェック"""
    output_path = Path(output_path)
    return (output_path / "config.json").exists()


def convert_adapter_to_full_model(
    base_model_id: str,
    adapter_path: str,
    output_path: str,
    adapter_name: str,
    description: str
) -> bool:
    """
    LoRAアダプターをフルモデルに変換
    
    Args:
        base_model_id: ベースモデルID
        adapter_path: アダプターのパス
        output_path: 出力先パス
        adapter_name: アダプター名（ログ用）
        description: 説明
    
    Returns:
        成功したかどうか
    """
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Converting: {adapter_name}")
        logger.info(f"  Description: {description}")
        logger.info(f"  Adapter: {adapter_path}")
        logger.info(f"  Output: {output_path}")
        logger.info("="*60)
        
        # ベースモデルをロード
        logger.info("Loading base model...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        
        # トークナイザーをロード
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        
        # LoRAアダプターをロード
        logger.info("Loading LoRA adapter...")
        model = PeftModel.from_pretrained(model, adapter_path)
        
        # マージしてLoRAをアンロード
        logger.info("Merging adapter into base model...")
        model = model.merge_and_unload()
        
        # 出力ディレクトリを作成
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # フルモデルを保存
        logger.info("Saving merged full model...")
        model.save_pretrained(
            output_path,
            safe_serialization=True,
            max_shard_size="5GB"
        )
        
        # トークナイザーを保存
        tokenizer.save_pretrained(output_path)
        
        # メタデータを保存
        metadata = {
            "base_model": base_model_id,
            "adapter_path": adapter_path,
            "adapter_name": adapter_name,
            "description": description,
            "converted_at": datetime.now().isoformat(),
            "conversion_method": "PeftModel.merge_and_unload()",
        }
        
        import json
        with open(output_path / "conversion_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Successfully converted {adapter_name} to full model")
        logger.info(f"  Saved to: {output_path}")
        
        # メモリ解放
        del model
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to convert {adapter_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    logger.info("="*70)
    logger.info("LoRA Adapter to Full Model Converter")
    logger.info("="*70)
    
    output_base = Path(output_base_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 統計
    total = len(adapters_to_convert)
    completed = 0
    skipped = 0
    failed = 0
    
    for adapter_info in adapters_to_convert:
        adapter_name = adapter_info["name"]
        adapter_path = adapter_info["adapter_path"]
        output_name = adapter_info["output_name"]
        description = adapter_info["description"]
        
        output_path = output_base / output_name
        
        # アダプターの存在確認
        if not check_adapter_exists(adapter_path):
            logger.error(f"[SKIP] Adapter not found: {adapter_path}")
            failed += 1
            continue
        
        # 既存のフルモデル確認
        if check_full_model_exists(output_path):
            logger.info(f"[SKIP] Full model already exists: {output_name}")
            skipped += 1
            continue
        
        # 変換実行
        success = convert_adapter_to_full_model(
            base_model_id,
            adapter_path,
            str(output_path),
            adapter_name,
            description
        )
        
        if success:
            completed += 1
        else:
            failed += 1
    
    # 結果サマリー
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total adapters:  {total}")
    logger.info(f"Completed:       {completed}")
    logger.info(f"Skipped:         {skipped}")
    logger.info(f"Failed:          {failed}")
    logger.info(f"Output dir:      {output_base}")
    logger.info("="*70)
    
    if completed > 0:
        logger.info("\n✓ Conversion completed successfully!")
        logger.info("You can now use these full models for merging.")
    
    if failed > 0:
        logger.warning(f"\n⚠ {failed} conversion(s) failed. Check the logs above.")


if __name__ == "__main__":
    main()
