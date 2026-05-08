#!/usr/bin/env python3
"""
SST-Merge V3 評価スクリプト（簡易版）
元のSST-Mergeの評価方法を使用
"""

import sys
import os
from pathlib import Path
import torch
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 元の評価スクリプトをインポート
from experiments.evaluate_instruction_models import ModelEvaluator
from src.utils.model_loader import ModelLoader

import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Evaluate SST-Merge V3 adapter')
    parser.add_argument('--adapter', type=str, required=True,
                       help='Path to merged adapter (.pt file)')
    parser.add_argument('--model', type=str, default='llama-3.1-8b',
                       choices=['llama-3.1-8b', 'mistral-7b', 'qwen2.5-14b'],
                       help='Base model name')
    parser.add_argument('--max_samples', type=int, default=500,
                       help='Maximum samples per dataset')
    parser.add_argument('--eval_types', type=str, 
                       default='jailbreak,beavertails,mmlu,repliqa',
                       help='Comma-separated list of evaluation types')
    
    args = parser.parse_args()
    
    # アダプターパスを確認（絶対パスに変換）
    adapter_path = Path(args.adapter)
    if not adapter_path.is_absolute():
        # 相対パスの場合、sst_merge_v3ディレクトリからの相対パスとして解釈
        adapter_path = project_root / 'sst_merge_v3' / adapter_path
    
    if not adapter_path.exists():
        logger.error(f"Adapter file not found: {adapter_path}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("SST-MERGE V3 EVALUATION (using original SST evaluation)")
    logger.info("=" * 80)
    logger.info(f"Adapter: {adapter_path}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Max samples: {args.max_samples}")
    logger.info(f"Evaluation types: {args.eval_types}")
    logger.info("")
    
    # カレントディレクトリをプロジェクトルートに変更
    os.chdir(project_root)
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("")
    
    # モデルとトークナイザーをロード
    logger.info("Loading model and tokenizer...")
    model_loader = ModelLoader(
        model_name=args.model,
        device_map='auto'
    )
    model, tokenizer = model_loader.load_model()
    
    # アダプターをロード
    logger.info(f"Loading adapter from {adapter_path}...")
    adapter_data = torch.load(adapter_path, map_location='cpu')
    
    # アダプターの構造を確認
    if 'adapter' in adapter_data:
        adapter = adapter_data['adapter']
    else:
        adapter = adapter_data
    
    # PEFTモデルとしてアダプターを適用
    from peft import PeftModel, LoraConfig
    
    # LoRA設定を推定（元のアダプターから）
    sample_key = list(adapter.keys())[0]
    if 'lora_A' in sample_key:
        # LoRAアダプターとして適用
        logger.info("Applying LoRA adapter to model...")
        # 簡易的な方法: state_dictを直接ロード
        model.load_state_dict(adapter, strict=False)
    
    # 評価器を初期化
    evaluator = ModelEvaluator(
        model_name=args.model,
        skip_existing=False
    )
    
    # 評価を実行
    eval_types = args.eval_types.split(',')
    
    logger.info("")
    logger.info("Starting evaluation...")
    logger.info("")
    
    results = evaluator.evaluate_model(
        model=model,
        tokenizer=tokenizer,
        model_name=f"sst_v3_{adapter_path.stem}",
        eval_datasets=eval_types
    )
    
    # 結果を表示
    logger.info("")
    logger.info("=" * 80)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 80)
    
    if results:
        for dataset, metrics in results.items():
            logger.info(f"\n{dataset.upper()}:")
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    if isinstance(value, float):
                        logger.info(f"  {key}: {value:.2%}")
                    else:
                        logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {metrics}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("EVALUATION COMPLETED")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
