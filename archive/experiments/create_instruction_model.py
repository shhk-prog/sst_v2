"""
指示応答モデル作成スクリプト (評価なし版)

A5: RepliQA (質問応答データセット)
A6: Alpaca (指示応答データセット)
A7: Security (Jailbreak防御データセット)

評価は後でまとめて実行するため、このスクリプトはFTのみを行う
"""

import torch
import logging
import argparse
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.model_loader import ModelLoader
from src.lora_trainer import LoRATrainer
from src.adapter_utils import save_lora_adapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama-3.1-8b')
    parser.add_argument('--task', type=str, required=True,
                        choices=['repliqa', 'alpaca', 'security', 'backdoor',
                                 'openmath', 'mathcode', 'opencode'],
                        help='Task type: A5-A12 (repliqa/alpaca/security/backdoor/openmath/mathcode/opencode)')
    parser.add_argument('--mode', type=str, default='full', choices=['minimal', 'full'])
    args = parser.parse_args()
    
    # モデルIDとタスク名のマッピング
    task_mapping = {
        'repliqa': ('A5', 'RepliQA'),
        'alpaca': ('A6', 'Alpaca'),
        'security': ('A7', 'Security'),
        'backdoor': ('A8', 'Backdoor'),
        'openmath': ('A9', 'OpenMathInstruct'),
        'mathcode': ('A10', 'MathCodeInstruct'),
        'opencode': ('A11', 'OpenCodeInstruct')
    }
    
    model_id, task_name = task_mapping[args.task]
    
    logger.info("\n" + "="*80)
    logger.info(f"{model_id} ({task_name}) MODEL CREATION")
    logger.info("="*80)
    
    # データセット読み込み
    logger.info("\nLoading training dataset...")
    
    if args.task == 'repliqa':
        from src.utils.instruction_loaders import load_repliqa
        task_data = load_repliqa(
            split='train',
            max_samples=None if args.mode == 'full' else 100,
            batch_size=32
        )
    elif args.task == 'alpaca':
        from src.utils.instruction_loaders import load_alpaca
        task_data = load_alpaca(
            split='train',
            max_samples=None if args.mode == 'full' else 100,
            batch_size=32
        )
    elif args.task == 'security':
        from src.utils.instruction_loaders import load_security
        task_data = load_security(
            csv_path='data/response_dataframe.csv',
            max_samples=None if args.mode == 'full' else 100,
            batch_size=32
        )
    elif args.task == 'backdoor':
        from src.utils.instruction_loaders import load_backdoor
        task_data = load_backdoor(
            json_path='data/backdoor_jailbreak.json',
            max_samples=None if args.mode == 'full' else 100,
            batch_size=32,
            split='train'
        )
    elif args.task == 'openmath':
        from src.utils.instruction_loaders import load_openmathinstruct
        task_data = load_openmathinstruct(
            split='train',
            max_samples=10000 if args.mode == 'full' else 100,  # 大規模データセットなのでサブサンプリング
            batch_size=32
        )
    elif args.task == 'mathcode':
        from src.utils.instruction_loaders import load_mathcodeinstruct
        task_data = load_mathcodeinstruct(
            split='train',
            max_samples=5000 if args.mode == 'full' else 100,
            batch_size=32
        )
    else:  # opencode
        from src.utils.instruction_loaders import load_opencodeinstruct
        task_data = load_opencodeinstruct(
            split='train',
            max_samples=10000 if args.mode == 'full' else 100,  # 大規模データセットなのでサブサンプリング
            batch_size=32
        )
    
    logger.info("✓ Dataset loaded")
    
    # モデル読み込み
    logger.info(f"\nLoading model: {args.model}...")
    model_loader = ModelLoader(args.model)
    model, tokenizer = model_loader.load_model()
    logger.info("✓ Model loaded")
    
    # LoRAトレーニング
    logger.info(f"\nFine-tuning on {task_name} data...")
    trainer = LoRATrainer(model, tokenizer)
    
    # LoRAトレーニング（Unsloth推奨設定をデフォルト値として使用）
    adapter = trainer.train_lora_adapter(
        dataloader=task_data,
        task_type='benign'
        # 他の引数は削除 → lora_trainer.pyのデフォルト値が使用される
        # デフォルト値: r=32, alpha=64, dropout=0.0, gradient_accumulation=4
    )
    
    # アダプター保存
    logger.info(f"\nSaving {model_id} adapter...")
    adapter_dir = Path(f'saved_adapters/{args.model}/utility_model')
    adapter_dir.mkdir(parents=True, exist_ok=True)
    
    adapter_path = adapter_dir / f'utility_model_{model_id}.pt'
    save_lora_adapter(
        adapter,
        str(adapter_path),
        {
            'type': f'utility_model_{model_id}',
            'task': args.task,
            'model': args.model,
            'note': f'{task_name} instruction-response model'
        }
    )
    
    logger.info(f"\n✓ {model_id} adapter saved to: {adapter_path}")
    logger.info("\n" + "="*80)
    logger.info(f"{model_id} ({task_name}) MODEL CREATION COMPLETED")
    logger.info("="*80)
    logger.info("\nNote: Evaluation will be performed separately using evaluate_all_models.py")


if __name__ == '__main__':
    main()
