"""
SST-Merge実行スクリプト: A5/A6/A7アダプターの統合

Utilityを固定し、SafetyをUtility直交サブスペースに射影

使用方法:
    python3 experiments/run_sst_merge.py --model llama-3.1-8b --k 10 --alpha 0.5
"""

import torch
import logging
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.model_loader import ModelLoader
from src.utils.instruction_loaders import load_repliqa, load_alpaca, load_security
from src.adapter_utils import load_lora_adapter, save_lora_adapter
from src.sst_merge import SSTMerge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def combine_dataloaders(dataloaders):
    """複数のDataLoaderを結合"""
    class CombinedDataLoader:
        def __init__(self, loaders):
            self.loaders = loaders
            
        def __iter__(self):
            for loader in self.loaders:
                for batch in loader:
                    yield batch
    
    return CombinedDataLoader(dataloaders)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama-3.1-8b',
                        help='Model name')
    parser.add_argument('--variant', type=str, required=True,
                        choices=['A5+A7', 'A6+A7', 'A5+A6+A7'],
                        help='Merge variant: A5+A7, A6+A7, or A5+A6+A7')
    parser.add_argument('--k', type=int, default=10,
                        help='Safety subspace dimension')
    parser.add_argument('--alpha', type=float, default=0.5,
                        help='Safety weight (0.0-1.0)')
    parser.add_argument('--max_samples', type=int, default=1000,
                        help='Max samples for FIM computation')
    args = parser.parse_args()
    
    logger.info("\n" + "="*80)
    logger.info("SST-MERGE: Utility-Safety Integration")
    logger.info("="*80)
    logger.info(f"Model: {args.model}")
    logger.info(f"Variant: {args.variant}")
    logger.info(f"k (subspace dim): {args.k}")
    logger.info(f"alpha (safety weight): {args.alpha}")
    logger.info(f"max_samples (FIM): {args.max_samples}")
    
    # ベースモデルロード
    logger.info("\nLoading base model...")
    model_loader = ModelLoader(args.model)
    model, tokenizer = model_loader.load_model()
    model.tokenizer = tokenizer  # FIM計算用
    logger.info("✓ Base model loaded")
    
    # アダプターロード
    logger.info("\nLoading adapters...")
    adapter_dir = Path(f'saved_adapters/{args.model}/utility_model')
    
    A5_path = adapter_dir / 'utility_model_A5.pt'
    A6_path = adapter_dir / 'utility_model_A6.pt'
    A7_path = adapter_dir / 'utility_model_A7.pt'
    
    if not A5_path.exists():
        logger.error(f"A5 adapter not found: {A5_path}")
        return
    if not A6_path.exists():
        logger.error(f"A6 adapter not found: {A6_path}")
        return
    if not A7_path.exists():
        logger.error(f"A7 adapter not found: {A7_path}")
        return
    
    A5_adapter, _ = load_lora_adapter(str(A5_path))
    A6_adapter, _ = load_lora_adapter(str(A6_path))
    A7_adapter, _ = load_lora_adapter(str(A7_path))
    
    logger.info("✓ Adapters loaded:")
    logger.info(f"  A5 (RepliQA): {A5_path}")
    logger.info(f"  A6 (Alpaca): {A6_path}")
    logger.info(f"  A7 (Security): {A7_path}")
    
    # データローダー準備
    logger.info("\nPreparing dataloaders...")
    
    # バリアントに応じてUtilityアダプターとデータローダーを選択
    if args.variant == 'A5+A7':
        logger.info("  Variant: A5 (RepliQA) + A7 (Security)")
        utility_adapters = [A5_adapter]
        utility_dl = load_repliqa(split='train', max_samples=args.max_samples, batch_size=1)
        output_name = 'A5_A7'
        
    elif args.variant == 'A6+A7':
        logger.info("  Variant: A6 (Alpaca) + A7 (Security)")
        utility_adapters = [A6_adapter]
        utility_dl = load_alpaca(split='train', max_samples=args.max_samples, batch_size=1)
        output_name = 'A6_A7'
        
    else:  # A5+A6+A7
        logger.info("  Variant: A5 (RepliQA) + A6 (Alpaca) + A7 (Security)")
        utility_adapters = [A5_adapter, A6_adapter]
        repliqa_dl = load_repliqa(split='train', max_samples=args.max_samples, batch_size=1)
        alpaca_dl = load_alpaca(split='train', max_samples=args.max_samples, batch_size=1)
        utility_dl = combine_dataloaders([repliqa_dl, alpaca_dl])
        output_name = 'A5_A6_A7'
    
    # Safety dataloader (response_dataframe.csv)
    safety_dl = load_security(
        csv_path='data/response_dataframe.csv',
        max_samples=args.max_samples,
        batch_size=1
    )
    
    logger.info("✓ Dataloaders prepared")
    logger.info(f"  Utility adapters: {len(utility_adapters)}")
    logger.info(f"  Safety adapter: 1")
    
    # SST-Merge実行
    logger.info("\nRunning SST-Merge...")
    logger.info(f"  Strategy: Fix Utility ({args.variant.split('+A7')[0]}), Project Safety (A7)")
    
    sst_merge = SSTMerge(
        k=args.k,
        fim_approximation='gradient_variance',
        regularization=1e-6,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    merged_adapter = sst_merge.merge_utility_safety(
        model=model,
        utility_adapters=utility_adapters,
        safety_adapter=A7_adapter,
        utility_dataloader=utility_dl,
        safety_dataloader=safety_dl,
        max_samples=args.max_samples,
        alpha=args.alpha
    )
    
    # マージ済みアダプター保存
    # SST-Merge専用ディレクトリに保存
    output_dir = Path(f'saved_adapters/{args.model}/sst_merged')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'sst_merged_{output_name}_k{args.k}_alpha{args.alpha:.2f}_s{args.max_samples}.pt'
    
    # メタデータにハイパーパラメータを保存
    metadata = {
        'variant': args.variant,
        'k': args.k,
        'alpha': args.alpha,
        'max_samples': args.max_samples,
        'method': 'SST-Merge'
    }
    
    save_lora_adapter(merged_adapter, str(output_path), metadata)
    logger.info(f"\n✓ Merged adapter saved to: {output_path}")
    
    logger.info("\n" + "="*80)
    logger.info("SST-MERGE COMPLETED")
    logger.info("="*80)
    logger.info(f"\nMerged: {args.variant}")
    logger.info(f"Output: {output_path.name}")
    logger.info("\nNext steps:")
    logger.info("1. Evaluate merged model:")
    logger.info(f"   python3 experiments/evaluate_instruction_models.py --model {args.model}")
    logger.info("2. Compare variants:")
    logger.info("   - A5+A7: RepliQA utility with safety")
    logger.info("   - A6+A7: Alpaca utility with safety")
    logger.info("   - A5+A6+A7: Full utility with safety")
    logger.info("3. Calculate Safety Tax reduction")


if __name__ == '__main__':
    main()
