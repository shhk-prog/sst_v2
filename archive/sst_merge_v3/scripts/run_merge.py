#!/usr/bin/env python3
"""
SST-Merge V2 実行スクリプト

使用方法:
    # Direct mode（射影なし、ベースライン相当）
    python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --mode direct
    
    # Residual mode（推奨、Safety保持）
    python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --mode residual --residual_ratio 0.7
    
    # Layer-wise mode
    python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --mode layerwise
"""

import torch
import logging
import argparse
from pathlib import Path
import sys
import json
from datetime import datetime

# プロジェクトのルートをパスに追加
# sst_merge_v2/scripts/run_merge.py -> sst_merge_v2 -> SST_merge -> src
project_root = Path(__file__).parent.parent.parent  # SST_mergeディレクトリ
sst_v2_root = Path(__file__).parent.parent  # sst_merge_v2ディレクトリ

# 親ディレクトリのsrcを最初に追加（優先）
sys.path.insert(0, str(project_root))
# sst_merge_v2のsrcを追加
sys.path.insert(0, str(sst_v2_root))

from src.sst_merge_v3 import SSTMergeV3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_adapter(path: Path) -> dict:
    """アダプターをロード"""
    data = torch.load(path, map_location='cpu')
    if isinstance(data, dict) and 'adapter' in data:
        return data['adapter']
    return data


def main():
    parser = argparse.ArgumentParser(description='SST-Merge V2')
    parser.add_argument('--model', type=str, default='llama-3.1-8b',
                        help='Model name')
    parser.add_argument('--variant', type=str, required=True,
                        choices=['A5+A7', 'A6+A7', 'A5+A6+A7'],
                        help='Merge variant')
    parser.add_argument('--mode', type=str, default='residual',
                        choices=['direct', 'residual', 'layerwise'],
                        help='Merge mode')
    parser.add_argument('--k', type=int, default=10,
                        help='Safety subspace dimension')
    parser.add_argument('--residual_ratio', type=float, default=0.7,
                        help='Residual ratio (0.0-1.0, higher = more original safety)')
    parser.add_argument('--safety_weight', type=float, default=1.0,
                        help='Safety weight (1.0 recommended)')
    parser.add_argument('--max_samples', type=int, default=500,
                        help='Max samples for FIM computation')
    parser.add_argument('--preset', type=str, default=None,
                        choices=['safety_first', 'balanced', 'utility_first', 'minimal'],
                        help='Layer config preset (for layerwise mode)')
    parser.add_argument('--use_fim', action='store_true',
                        help='Use FIM computation (requires dataloaders)')
    
    args = parser.parse_args()
    
    logger.info("\n" + "=" * 80)
    logger.info("SST-MERGE V2: SAFETY-PRESERVING MERGE")
    logger.info("=" * 80)
    logger.info(f"Model: {args.model}")
    logger.info(f"Variant: {args.variant}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"k: {args.k}")
    logger.info(f"Residual ratio: {args.residual_ratio}")
    logger.info(f"Safety weight: {args.safety_weight}")
    
    # アダプターのパスを設定
    adapter_dir = project_root / f'saved_adapters/{args.model}/utility_model'
    
    A5_path = adapter_dir / 'utility_model_A5.pt'
    A6_path = adapter_dir / 'utility_model_A6.pt'
    A7_path = adapter_dir / 'utility_model_A7.pt'
    
    # アダプターをロード
    logger.info("\nLoading adapters...")
    
    utility_adapters = []
    utility_names = []
    
    if 'A5' in args.variant:
        if not A5_path.exists():
            logger.error(f"A5 adapter not found: {A5_path}")
            return
        utility_adapters.append(load_adapter(A5_path))
        utility_names.append('A5')
        logger.info(f"  ✓ A5 (RepliQA) loaded")
    
    if 'A6' in args.variant:
        if not A6_path.exists():
            logger.error(f"A6 adapter not found: {A6_path}")
            return
        utility_adapters.append(load_adapter(A6_path))
        utility_names.append('A6')
        logger.info(f"  ✓ A6 (Alpaca) loaded")
    
    if not A7_path.exists():
        logger.error(f"A7 adapter not found: {A7_path}")
        return
    safety_adapter = load_adapter(A7_path)
    logger.info(f"  ✓ A7 (Security) loaded")
    
    # Layer configを設定
    
    # SST-Merge V3を初期化（Layer-wise Projection）
    merger = SSTMergeV3(
        k=args.k,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # FIM計算を使用するかどうか
    if args.use_fim and args.mode != 'direct':
        logger.info("\nLoading model and dataloaders for FIM computation...")
        
        # sys.pathの確認とデバッグ
        logger.debug(f"Project root: {project_root}")
        logger.debug(f"sys.path: {sys.path[:3]}")
        
        # 親ディレクトリのsrcモジュールを明示的にインポート
        # SST_merge/src/utils/model_loader.py をインポート
        import importlib.util
        
        # model_loaderのインポート
        model_loader_path = project_root / 'src' / 'utils' / 'model_loader.py'
        spec = importlib.util.spec_from_file_location("model_loader_module", model_loader_path)
        model_loader_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_loader_module)
        ModelLoader = model_loader_module.ModelLoader
        
        # instruction_loadersのインポート
        instruction_loaders_path = project_root / 'src' / 'utils' / 'instruction_loaders.py'
        spec = importlib.util.spec_from_file_location("instruction_loaders_module", instruction_loaders_path)
        instruction_loaders_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(instruction_loaders_module)
        load_repliqa = instruction_loaders_module.load_repliqa
        load_alpaca = instruction_loaders_module.load_alpaca
        load_security = instruction_loaders_module.load_security
        
        model_loader = ModelLoader(args.model)
        model, tokenizer = model_loader.load_model()
        model.tokenizer = tokenizer
        
        # データローダー準備
        if args.variant == 'A5+A7':
            utility_dl = load_repliqa(split='train', max_samples=args.max_samples, batch_size=1)
        elif args.variant == 'A6+A7':
            utility_dl = load_alpaca(split='train', max_samples=args.max_samples, batch_size=1)
        else:
            # A5+A6+A7: 両方のデータを使用
            from itertools import chain
            repliqa_dl = load_repliqa(split='train', max_samples=args.max_samples // 2, batch_size=1)
            alpaca_dl = load_alpaca(split='train', max_samples=args.max_samples // 2, batch_size=1)
            utility_dl = list(chain(repliqa_dl, alpaca_dl))
        
        safety_dl = load_security(
            csv_path=str(project_root / 'data/response_dataframe.csv'),
            max_samples=args.max_samples,
            batch_size=1
        )
        
        merged_adapter = merger.merge_utility_safety(
            model=model,
            utility_adapters=utility_adapters,
            safety_adapter=safety_adapter,
            utility_dataloader=utility_dl,
            safety_dataloader=safety_dl,
            max_samples=args.max_samples,
            safety_weight=args.safety_weight
        )
    else:
        # FIMを使用しない（direct modeまたはFIM計算スキップ）
        merged_adapter = merger.merge_utility_safety(
            model=None,
            utility_adapters=utility_adapters,
            safety_adapter=safety_adapter,
            utility_dataloader=None,
            safety_dataloader=None,
            safety_weight=args.safety_weight
        )
    
    # 保存
    output_dir = Path(__file__).parent.parent / 'results' / args.model
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    variant_str = args.variant.replace('+', '_')
    output_name = f"sst_v2_{variant_str}_{args.mode}_r{args.residual_ratio}_w{args.safety_weight}_k{args.k}_{timestamp}.pt"
    output_path = output_dir / output_name
    
    metadata = {
        'variant': args.variant,
        'mode': args.mode,
        'k': args.k,
        'residual_ratio': args.residual_ratio,
        'safety_weight': args.safety_weight,
        'preset': args.preset,
        'timestamp': timestamp,
        'method': 'SST-Merge V2'
    }
    
    merger.save_merged_adapter(merged_adapter, str(output_path), metadata)
    
    # 結果サマリー
    logger.info("\n" + "=" * 80)
    logger.info("SST-MERGE V2 COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Output: {output_path}")
    logger.info(f"Variant: {args.variant}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Residual ratio: {args.residual_ratio}")
    logger.info(f"Safety weight: {args.safety_weight}")
    
    # メタデータを別途JSON保存
    meta_path = output_path.with_suffix('.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata: {meta_path}")
    
    logger.info("\nNext steps:")
    logger.info("1. Evaluate the merged model:")
    logger.info(f"   python scripts/evaluate.py --adapter {output_path}")
    logger.info("2. Compare with baseline methods")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
