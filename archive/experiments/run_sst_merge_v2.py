"""
SST-Merge V2 実験スクリプト

使用方法:
    python3 experiments/run_sst_merge_v2.py --model llama-3.1-8b --variant A5+A7
    python3 experiments/run_sst_merge_v2.py --model llama-3.1-8b --variant A5+A7 --safety-weight 0.8
"""

import torch
import logging
import argparse
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapter_utils import load_lora_adapter, save_lora_adapter
from src.sst_merge_v2 import SSTMergeV2Quick

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_merge(args):
    """マージを実行"""
    logger.info("=" * 60)
    logger.info("SST-MERGE V2")
    logger.info("=" * 60)
    logger.info(f"Model: {args.model}")
    logger.info(f"Variant: {args.variant}")
    logger.info(f"Safety weight: {args.safety_weight}")
    logger.info(f"Method: {args.method}")
    
    adapter_dir = Path(f'saved_adapters/{args.model}/utility_model')
    
    # バリアント解析
    parts = args.variant.split('+')
    utility_names = [p for p in parts if p != 'A7']
    
    # Utilityアダプターをロード
    utility_adapters = []
    for name in utility_names:
        path = adapter_dir / f'utility_model_{name}.pt'
        if not path.exists():
            logger.error(f"Not found: {path}")
            return
        adapter, _ = load_lora_adapter(str(path))
        utility_adapters.append(adapter)
        logger.info(f"Loaded {name}")
    
    # Safetyアダプターをロード
    safety_path = adapter_dir / 'utility_model_A7.pt'
    safety_adapter, _ = load_lora_adapter(str(safety_path))
    logger.info("Loaded A7 (Safety)")
    
    # マージ実行
    merger = SSTMergeV2Quick(
        safety_weight=args.safety_weight,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    merged = merger.merge(utility_adapters, safety_adapter, method=args.method)
    
    # 保存
    output_dir = Path(f'saved_adapters/{args.model}/sst_merged_v2')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    variant_clean = args.variant.replace('+', '_')
    filename = f'sst_v2_{variant_clean}_{args.method}_alpha{args.safety_weight:.1f}.pt'
    output_path = output_dir / filename
    
    metadata = {
        'variant': args.variant,
        'method': args.method,
        'safety_weight': args.safety_weight,
        'version': 'SST-Merge-V2',
        'created': datetime.now().isoformat()
    }
    
    save_lora_adapter(merged, str(output_path), metadata)
    logger.info(f"Saved to: {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama-3.1-8b')
    parser.add_argument('--variant', type=str, default='A5+A7')
    parser.add_argument('--safety-weight', type=float, default=1.0)
    parser.add_argument('--method', type=str, default='weighted_add',
                        choices=['weighted_add', 'ties_style', 'dare_style'])
    parser.add_argument('--run-all', action='store_true')
    
    args = parser.parse_args()
    
    if args.run_all:
        variants = ['A5+A7', 'A6+A7', 'A5+A6+A7']
        for v in variants:
            args.variant = v
            run_merge(args)
    else:
        run_merge(args)
    
    logger.info("\nNext: python3 experiments/evaluate_sst_merge_v2.py")


if __name__ == '__main__':
    main()
