#!/usr/bin/env python3
"""
FIM固有値計算スクリプト

Usage:
    python3 experiments/compute_fim_eigenvalues.py \
        --model llama-3.1-8b \
        --variant A5+A7 \
        --max_samples 500 \
        --output results/eigenvalues/A5_A7_eigenvalues.pt
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import logging
import torch

from src.utils.model_loader import ModelLoader
from src.adapter_utils import load_lora_adapter
from src.model_utils import apply_lora_adapter
from src.fim_calculator import FIMCalculator
from src.utils.instruction_loaders import load_repliqa, load_security

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Compute FIM eigenvalues')
    parser.add_argument('--model', type=str, default='llama-3.1-8b',
                        help='Base model name')
    parser.add_argument('--variant', type=str, default='A5+A7',
                        help='Adapter variant (e.g., A5+A7, A11+A7, or "all" for all adapters)')
    parser.add_argument('--max_samples', type=int, default=500,
                        help='Maximum samples for FIM computation (fixed at 500)')
    parser.add_argument('--output', type=str, 
                        default='results/eigenvalues/eigenvalues.pt',
                        help='Output path for eigenvalues')
    args = parser.parse_args()
    
    # 'all'が指定された場合、全アダプターを計算
    if args.variant.lower() == 'all':
        args.variant = 'A5+A6+A7+A9+A10+A11'
        logger.info("Computing eigenvalues for all adapters: A5, A6, A7, A9, A10, A11")
    
    # タイムスタンプ付き出力ディレクトリを作成
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(f'results/eigenvalues/{timestamp}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 出力パスを更新
    if args.output == 'results/eigenvalues/eigenvalues.pt':
        args.output = str(output_dir / 'eigenvalues.pt')
    
    logger.info(f"\n{'='*80}")
    logger.info(f"FIM EIGENVALUE COMPUTATION")
    logger.info(f"{'='*80}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Variant: {args.variant}")
    logger.info(f"Max samples: {args.max_samples}")
    logger.info(f"Output: {args.output}")
    
    # モデル読み込み
    logger.info("\nLoading base model...")
    model_loader = ModelLoader(args.model)
    model, tokenizer = model_loader.load_model()
    logger.info("✓ Base model loaded")
    
    # アダプター読み込み
    logger.info("\nLoading adapters...")
    adapters = {}
    
    if 'A5' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A5.pt'
        adapters['A5'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A5 loaded")
    
    if 'A6' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A6.pt'
        adapters['A6'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A6 loaded")
    
    if 'A7' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A7.pt'
        adapters['A7'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A7 loaded")
    
    if 'A9' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A9.pt'
        adapters['A9'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A9 loaded")
    
    if 'A10' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A10.pt'
        adapters['A10'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A10 loaded")
    
    if 'A11' in args.variant:
        adapter_path = f'saved_adapters/{args.model}/utility_model/utility_model_A11.pt'
        adapters['A11'], _ = load_lora_adapter(adapter_path, model.device)
        logger.info(f"  ✓ A11 loaded")
    
    # データローダー準備
    logger.info("\nPreparing dataloaders...")
    dataloaders = {}
    
    # Utility adapters (A5, A6, A9, A10, A11) - RepliQAを使用
    if any(x in args.variant for x in ['A5', 'A6', 'A9', 'A10', 'A11']):
        utility_dataloader = load_repliqa(
            tokenizer=tokenizer,
            split='train',
            max_samples=args.max_samples,
            batch_size=1
        )
        logger.info(f"  ✓ RepliQA dataloader prepared")
        
        for adapter_name in ['A5', 'A6', 'A9', 'A10', 'A11']:
            if adapter_name in args.variant:
                dataloaders[adapter_name] = utility_dataloader
    
    # Safety adapter (A7) - Securityデータを使用
    if 'A7' in args.variant:
        safety_dataloader = load_security(
            csv_path='data/response_dataframe.csv',
            max_samples=args.max_samples,
            batch_size=1
        )
        logger.info(f"  ✓ Security dataloader prepared")
        dataloaders['A7'] = safety_dataloader
    
    # 各アダプターに対してFIM計算
    for adapter_name, adapter in adapters.items():
        logger.info("\n" + "="*80)
        logger.info(f"Computing FIM for {adapter_name} adapter")
        logger.info("="*80)
        
        # アダプターを適用
        model_with_adapter = apply_lora_adapter(model, adapter)
        
        # FIM Calculator (tokenizerを渡す)
        fim_calc = FIMCalculator(
            model=model_with_adapter,
            approximation='gradient_variance',
            device=model.device
        )
        fim_calc.tokenizer = tokenizer  # tokenizerを設定
        
        # 固有値計算と保存
        output_path = args.output.replace('.pt', f'_{adapter_name.lower()}.pt')
        eigenvalues, eigenvectors = fim_calc.compute_and_save_eigenvalues(
            dataloader=dataloaders[adapter_name],
            max_samples=args.max_samples,
            output_path=output_path
        )
        
        logger.info(f"\n✓ {adapter_name} FIM eigenvalues saved to: {output_path}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"FIM EIGENVALUE COMPUTATION COMPLETED")
    logger.info(f"{'='*80}")


if __name__ == '__main__':
    main()
