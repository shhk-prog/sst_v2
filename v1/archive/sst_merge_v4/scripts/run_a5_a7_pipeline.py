#!/usr/bin/env python3
"""
SST-Merge V4: A5+A7 Pipeline

Complete pipeline for A5 (RepliQA/Utility) + A7 (Jailbreak/Safety):
1. LoRA Fine-Tuning: A5 (Utility/RepliQA), A7 (Safety/Jailbreak refusal)
2. Baseline Merge: TIES, DARE, Task Arithmetic
3. SST-Merge V4: GEVP-based merge
4. Evaluation: Jailbreak resistance, Utility (ROUGE-L on RepliQA)
5. Comparison: All methods vs targets

Features:
- Separate saving for jailbreak, repliqa evaluations
- Generation folder for prompts and responses
- Skip functionality for existing results (FT, evaluation, generation)

Usage:
    python run_a5_a7_pipeline.py --model llama3.1-8b
    python run_a5_a7_pipeline.py --quick  # Quick test with small samples
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import torch
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SUPPORTED_MODELS = {
    # LLaMA Base models
    'llama3.1-8b': 'meta-llama/Meta-Llama-3.1-8B',
    'llama3.1-8b-base': 'meta-llama/Meta-Llama-3.1-8B',
    'llama3-8b': 'meta-llama/Meta-Llama-3-8B',
    'llama3-8b-base': 'meta-llama/Meta-Llama-3-8B',
    # LLaMA Instruct models (推奨)
    'llama3.1-8b-instruct': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
    'llama3-8b-instruct': 'meta-llama/Meta-Llama-3-8B-Instruct',
    'llama3.2-3b-instruct': 'meta-llama/Llama-3.2-3B-Instruct',
    'llama3.2-1b-instruct': 'meta-llama/Llama-3.2-1B-Instruct',
    # Mistral Instruct models (推奨)
    'mistral-7b-v0.1': 'mistralai/Mistral-7B-Instruct-v0.1',
    'mistral-7b-v0.2': 'mistralai/Mistral-7B-Instruct-v0.2',
    'mistral-7b-v0.3': 'mistralai/Mistral-7B-Instruct-v0.3',
    # Mistral Base models (non-instruct)
    'mistral-7b-base': 'mistralai/Mistral-7B-v0.1',
    'mistral-7b-base-v0.3': 'mistralai/Mistral-7B-v0.3',
    # Qwen models
    'qwen2.5-14b': 'Qwen/Qwen2.5-14B-Instruct',
    'qwen2.5-7b': 'Qwen/Qwen2.5-7B-Instruct',
    'qwen2.5-3b': 'Qwen/Qwen2.5-3B-Instruct',
    'qwen2.5-1.5b': 'Qwen/Qwen2.5-1.5B-Instruct',
    'qwen2.5-0.5b': 'Qwen/Qwen2.5-0.5B-Instruct',
}


def parse_args():
    parser = argparse.ArgumentParser(description="SST-Merge V4: A5+A7 Pipeline")
    
    # Model
    parser.add_argument('--model_name', type=str, 
                        default='meta-llama/Meta-Llama-3.1-8B',
                        help='Base model name (full HF path or shortcut: llama3.1-8b, mistral-7b)')
    parser.add_argument('--model', type=str, default=None,
                        help='Shortcut for model selection: llama3.1-8b, mistral-7b, etc.')
    
    # Data
    parser.add_argument('--jailbreak_csv', type=str,
                        default=None,  # Will be set to absolute path
                        help='Jailbreak refusal data CSV')
    
    # Training (shared) - same rank for both adapters to enable merging
    parser.add_argument('--num_epochs', type=int, default=5,
                        help='Number of training epochs (default for A7)')
    parser.add_argument('--batch_size', type=int, default=4,
                        help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=2e-4,
                        help='Learning rate')
    parser.add_argument('--lora_r', type=int, default=32,
                        help='LoRA rank (shared for A5 and A7 - must be same for merging)')
    
    # A5 (Utility) specific
    parser.add_argument('--a5_epochs', type=int, default=10,
                        help='Epochs for A5 (Utility)')
    parser.add_argument('--a5_lr', type=float, default=2e-4,
                        help='Learning rate for A5')
    parser.add_argument('--a5_grad_accum', type=int, default=4,
                        help='Gradient accumulation steps for A5')
    
    # SST-Merge
    parser.add_argument('--sst_k', type=int, default=10,
                        help='SST-Merge safety subspace dimension')
    parser.add_argument('--sst_weight', type=float, default=1.0,
                        help='SST-Merge safety weight')
    parser.add_argument('--no_layerwise', action='store_true',
                        help='Disable layer-wise weights (use uniform weight for all layers)')
    
    # Evaluation
    parser.add_argument('--eval_samples', type=int, default=500,
                        help='Number of evaluation samples')
    
    # Output
    parser.add_argument('--output_dir', type=str, default='../results',
                        help='Output directory')
    
    # Quick test mode
    parser.add_argument('--quick', action='store_true',
                        help='Quick test with small samples')
    
    # Skip/Force options
    parser.add_argument('--skip_training', action='store_true',
                        help='Skip LoRA training (use existing adapters)')
    parser.add_argument('--adapter_a5', type=str, default=None,
                        help='Path to existing A5 adapter')
    parser.add_argument('--adapter_a7', type=str, default=None,
                        help='Path to existing A7 adapter')
    parser.add_argument('--force_train', action='store_true',
                        help='Force re-training even if cached adapters exist')
    parser.add_argument('--force_eval', action='store_true',
                        help='Force re-evaluation even if cached results exist')
    parser.add_argument('--force_merge', action='store_true',
                        help='Force re-merging even if cached merged adapters exist')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Model shortcut resolution
    if args.model:
        if args.model in SUPPORTED_MODELS:
            args.model_name = SUPPORTED_MODELS[args.model]
        else:
            args.model_name = args.model
    elif args.model_name in SUPPORTED_MODELS:
        args.model_name = SUPPORTED_MODELS[args.model_name]
    
    # Set default paths (absolute)
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.parent  # SST_merge directory
    
    if args.jailbreak_csv is None:
        args.jailbreak_csv = str(project_dir / "data" / "response_dataframe.csv")
    
    if args.output_dir == '../results':
        args.output_dir = str(script_dir.parent / "results")
    
    # Quick test mode
    if args.quick:
        args.num_epochs = 1
        args.eval_samples = 50
        logger.info("QUICK TEST MODE: Reduced epochs and samples")
    
    # Setup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_short_name = args.model_name.split('/')[-1].lower().replace('-', '_')
    
    # ディレクトリ構造
    results_root = Path(args.output_dir).resolve()
    run_dir = results_root / f"run_a5a7_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # アダプター保存ディレクトリ
    adapters_dir = results_root / "adapters"
    ft_dir = adapters_dir / "FT"
    a5_dir = ft_dir / "A5"
    a7_dir = ft_dir / "A7"
    merge_dir = adapters_dir / "merge"
    mergekit_dir = merge_dir / "mergekit"
    sst_merge_dir = merge_dir / "sst_merge"
    
    for d in [a5_dir, a7_dir, mergekit_dir / "ties", mergekit_dir / "dare", 
              mergekit_dir / "task_arithmetic", sst_merge_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # ヘルパー関数
    def find_existing_adapter(directory: Path, pattern: str) -> Optional[Path]:
        matches = list(directory.glob(f"{pattern}*.pt"))
        if matches:
            return sorted(matches, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        return None
    
    # モデルタイプを取得（Base/Instructを区別）
    if 'instruct' in model_short_name.lower():
        if 'llama' in model_short_name:
            model_type = 'llama_instruct'
        elif 'mistral' in model_short_name:
            model_type = 'mistral_instruct'
        elif 'qwen' in model_short_name:
            model_type = 'qwen_instruct'
        else:
            model_type = 'instruct'
    else:
        if 'llama' in model_short_name:
            model_type = 'llama_base'
        elif 'mistral' in model_short_name:
            model_type = 'mistral_base'
        elif 'qwen' in model_short_name:
            model_type = 'qwen_base'
        else:
            model_type = 'default'
    
    ft_pattern = f"{model_type}_r{args.lora_r}_{args.num_epochs}ep"
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Device: {device}")
    
    # Save config
    config = vars(args)
    config['timestamp'] = timestamp
    config['device'] = device
    config['pipeline'] = 'A5+A7'
    with open(run_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("\n" + "="*80)
    logger.info("SST-Merge V4: A5+A7 Pipeline")
    logger.info("="*80)
    logger.info(f"Model: {args.model_name}")
    logger.info(f"Results root: {results_root}")
    logger.info(f"Run dir: {run_dir}")
    logger.info("="*80 + "\n")
    
    # =========================================================================
    # Step 1: Load Model and Tokenizer
    # =========================================================================
    logger.info("Step 1: Loading model and tokenizer...")
    
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        device_map='auto'
    )
    
    logger.info(f"  Model loaded: {args.model_name}")
    
    # =========================================================================
    # Step 1.5: Prepare Data Loaders
    # =========================================================================
    logger.info("\nStep 1.5: Preparing data loaders...")
    
    from src.data_loader import DataLoaderFactory
    
    data_factory = DataLoaderFactory(
        tokenizer=tokenizer,
        jailbreak_csv_path=args.jailbreak_csv,
        batch_size=args.batch_size
    )
    
    # Training data
    jailbreak_train_loader = data_factory.get_jailbreak_dataloader(split='train')
    jailbreak_val_loader = data_factory.get_jailbreak_dataloader(split='val')
    repliqa_train_loader = data_factory.get_repliqa_dataloader(split='train')
    
    # Evaluation data
    jailbreak_eval_data = data_factory.get_jailbreak_eval_data(max_samples=args.eval_samples)
    repliqa_eval_data = data_factory.get_repliqa_eval_data(max_samples=args.eval_samples)
    
    logger.info(f"  Jailbreak train: {len(jailbreak_train_loader)} batches")
    logger.info(f"  RepliQA train: {len(repliqa_train_loader)} batches")
    logger.info(f"  Jailbreak eval: {len(jailbreak_eval_data)} samples")
    logger.info(f"  RepliQA eval: {len(repliqa_eval_data)} samples")
    
    # =========================================================================
    # Step 2: Evaluate BASE MODEL
    # =========================================================================
    logger.info("\nStep 2: Evaluating BASE MODEL...")
    
    from src.evaluator import Evaluator
    
    # 共通ハイパーパラメータ
    global_hyperparams = {
        'lora_r': args.lora_r,
        'num_epochs': args.num_epochs,
        'learning_rate': args.learning_rate,
        'a5_epochs': args.a5_epochs,
        'a5_lr': args.a5_lr,
        'a5_grad_accum': args.a5_grad_accum,
        'sst_k': args.sst_k,
        'sst_weight': args.sst_weight,
        'use_layerwise': not args.no_layerwise,
        'eval_samples': args.eval_samples
    }
    
    evaluator = Evaluator(
        model=model,
        tokenizer=tokenizer,
        device=device,
        output_dir=str(results_root),
        model_name=args.model_name,
        hyperparams=global_hyperparams
    )
    
    results_base = evaluator.evaluate_base_model(
        jailbreak_eval_data, repliqa_eval_data,
        utility_type='repliqa',
        force_eval=args.force_eval
    )
    
    logger.info(f"  BASE_MODEL: JB={results_base['summary']['jailbreak_resistance']*100:.1f}%, "
                f"ROUGE-L={results_base['summary']['utility_rouge_l']*100:.1f}%")
    
    # =========================================================================
    # Step 3: LoRA Fine-Tuning (A5 + A7)
    # =========================================================================
    logger.info("\nStep 3: LoRA Fine-Tuning (A5 + A7)...")
    
    from src.lora_trainer import LoRATrainerV4
    
    adapter_a5 = None
    adapter_a7 = None
    
    # A5訓練
    a5_lr_str = f"{args.a5_lr:.0e}".replace('-0', '-') if args.a5_lr < 0.001 else f"{args.a5_lr:.4f}".rstrip('0').rstrip('.')
    a5_ft_pattern = f"{model_type}_r{args.lora_r}_{args.a5_epochs}ep_{a5_lr_str}"
    
    existing_a5 = find_existing_adapter(a5_dir, f"A5_utility_{a5_ft_pattern}")
    if existing_a5 and not args.force_train:
        logger.info(f"\n--- Found existing A5 adapter: {existing_a5} ---")
        adapter_a5 = torch.load(existing_a5, map_location='cpu')['adapter']
        logger.info(f"  Loaded {len(adapter_a5)} parameters (cached)")
    else:
        logger.info("\n--- Training A5 (Utility/RepliQA) ---")
        trainer_a5 = LoRATrainerV4(
            model=model,
            tokenizer=tokenizer,
            device=device,
            output_dir=str(a5_dir)
        )
        adapter_a5 = trainer_a5.train_adapter(
            dataloader=repliqa_train_loader,
            adapter_name='A5_utility',
            num_epochs=args.a5_epochs,
            learning_rate=args.a5_lr,
            lora_r=args.lora_r,
            gradient_accumulation_steps=args.a5_grad_accum,
            val_dataloader=None,
            early_stopping_patience=100,
            task_type='utility_repliqa'  # A5はRepliQA (RAG形式)
        )
    
    # A7訓練
    existing_a7 = find_existing_adapter(a7_dir, f"A7_safety_{ft_pattern}")
    if existing_a7 and not args.force_train:
        logger.info(f"\n--- Found existing A7 adapter: {existing_a7} ---")
        adapter_a7 = torch.load(existing_a7, map_location='cpu')['adapter']
        logger.info(f"  Loaded {len(adapter_a7)} parameters (cached)")
    else:
        logger.info("\n--- Training A7 (Safety/Jailbreak) ---")
        trainer_a7 = LoRATrainerV4(
            model=model,
            tokenizer=tokenizer,
            device=device,
            output_dir=str(a7_dir)
        )
        adapter_a7 = trainer_a7.train_adapter(
            dataloader=jailbreak_train_loader,
            adapter_name='A7_safety',
            num_epochs=args.num_epochs,
            learning_rate=args.learning_rate,
            lora_r=args.lora_r,
            val_dataloader=jailbreak_val_loader,
            task_type='safety'  # A7は安全性タスク（拒否学習）
        )
    
    logger.info(f"  A5: {len(adapter_a5)} parameters")
    logger.info(f"  A7: {len(adapter_a7)} parameters")
    
    # =========================================================================
    # Step 4: Evaluate A5 and A7
    # =========================================================================
    logger.info("\nStep 4: Evaluating adapters...")
    
    all_results = [results_base]
    
    # A5/A7のメタデータ
    a5_metadata = {
        'adapter_type': 'utility',
        'lora_r': args.lora_r,
        'epochs': args.a5_epochs,
        'learning_rate': args.a5_lr
    }
    a7_metadata = {
        'adapter_type': 'safety',
        'lora_r': args.lora_r,
        'epochs': args.num_epochs,
        'learning_rate': args.learning_rate
    }
    
    # Evaluate A5
    results_a5 = evaluator.evaluate_adapter(
        adapter_a5, 'A5_utility',
        jailbreak_eval_data, repliqa_eval_data,
        utility_type='repliqa',
        adapter_metadata=a5_metadata,
        force_eval=args.force_eval
    )
    all_results.append(results_a5)
    
    # Evaluate A7
    results_a7 = evaluator.evaluate_adapter(
        adapter_a7, 'A7_safety',
        jailbreak_eval_data, repliqa_eval_data,
        utility_type='repliqa',
        adapter_metadata=a7_metadata,
        force_eval=args.force_eval
    )
    all_results.append(results_a7)
    
    # =========================================================================
    # Step 5: Baseline Merges
    # =========================================================================
    logger.info("\nStep 5: Baseline Merges (TIES, DARE, Task Arithmetic)...")
    
    from src.baseline_merge import BaselineMerger
    
    baseline_merged = {}
    adapters = [adapter_a5, adapter_a7]
    weights = [0.5, 0.5]
    
    for method in ['task_arithmetic', 'ties', 'dare']:
        method_dir = mergekit_dir / method
        existing_merge = find_existing_adapter(method_dir, f"{method}_{model_short_name}")
        
        if existing_merge and not args.force_merge:
            logger.info(f"  Found existing {method} merge: {existing_merge}")
            baseline_merged[method] = torch.load(existing_merge, map_location='cpu')['adapter']
        else:
            logger.info(f"  Computing {method} merge...")
            merger = BaselineMerger(device=device)
            merged_adapter = merger.merge(method=method, adapters=adapters, weights=weights)
            baseline_merged[method] = merged_adapter
            
            save_path = method_dir / f"{method}_{model_short_name}_w0.5_0.5_{timestamp}.pt"
            torch.save({
                'adapter': merged_adapter,
                'metadata': {
                    'method': method,
                    'model': model_short_name,
                    'weights': weights,
                    'adapters': ['A5_utility', 'A7_safety']
                }
            }, save_path)
    
    # =========================================================================
    # Step 6: SST-Merge V4
    # =========================================================================
    logger.info("\nStep 6: SST-Merge V4...")
    
    layerwise_str = "layerwise" if not args.no_layerwise else "uniform"
    sst_pattern_full = f"sst_merge_{model_short_name}_k{args.sst_k}_w{args.sst_weight}_{layerwise_str}"
    existing_sst = find_existing_adapter(sst_merge_dir, sst_pattern_full)
    
    if existing_sst and not args.force_merge:
        logger.info(f"  Found existing SST-Merge: {existing_sst}")
        sst_merged = torch.load(existing_sst, map_location='cpu')['adapter']
    else:
        from src.sst_merge_v4 import SSTMergeV4
        
        sst_merger = SSTMergeV4(
            k=args.sst_k,
            safety_weight=args.sst_weight,
            device=device,
            use_layerwise_weights=not args.no_layerwise
        )
        
        sst_merged = sst_merger.merge(
            model=model,
            tokenizer=tokenizer,
            utility_adapter=adapter_a5,
            safety_adapter=adapter_a7,
            utility_dataloader=repliqa_train_loader,
            safety_dataloader=jailbreak_train_loader,
            max_samples=min(500, args.eval_samples * 2)
        )
        
        if sst_merged is not None:
            sst_filename = f"{sst_pattern_full}_{timestamp}.pt"
            sst_merger.save_merged_adapter(
                sst_merged,
                str(sst_merge_dir / sst_filename),
                metadata={
                    'k': args.sst_k, 
                    'safety_weight': args.sst_weight,
                    'use_layerwise_weights': not args.no_layerwise,
                    'model': model_short_name
                }
            )
    
    # =========================================================================
    # Step 7: Evaluate Merged Models
    # =========================================================================
    logger.info("\nStep 7: Evaluating merged models...")
    
    # Evaluate baseline merges
    for method, merged in baseline_merged.items():
        baseline_metadata = {
            'method': method,
            'weights': [0.5, 0.5],
            'adapters': ['A5_utility', 'A7_safety'],
            'lora_r': args.lora_r
        }
        
        results = evaluator.evaluate_adapter(
            merged, f'baseline_{method}',
            jailbreak_eval_data, repliqa_eval_data,
            utility_type='repliqa',
            adapter_metadata=baseline_metadata,
            force_eval=args.force_eval
        )
        all_results.append(results)
    
    # Evaluate SST-Merge
    sst_metadata = {
        'method': 'sst_merge_v4',
        'k': args.sst_k,
        'safety_weight': args.sst_weight,
        'use_layerwise': not args.no_layerwise,
        'lora_r': args.lora_r
    }
    
    results_sst = evaluator.evaluate_adapter(
        sst_merged, 'sst_merge_v4',
        jailbreak_eval_data, repliqa_eval_data,
        utility_type='repliqa',
        adapter_metadata=sst_metadata,
        force_eval=args.force_eval
    )
    all_results.append(results_sst)
    
    # =========================================================================
    # Step 8: Comparison Summary
    # =========================================================================
    logger.info("\nStep 8: Final Comparison...")
    
    summary = evaluator.compare_results(all_results)
    
    # Save summary to run directory
    with open(run_dir / 'summary.txt', 'w') as f:
        f.write(summary)
    
    # Save all results to run directory
    with open(run_dir / 'all_results.json', 'w') as f:
        serializable = []
        for r in all_results:
            serializable.append({
                'adapter_name': r['adapter_name'],
                'summary': r['summary']
            })
        json.dump(serializable, f, indent=2)
    
    logger.info(f"\n{'='*80}")
    logger.info("A5+A7 Pipeline completed!")
    logger.info(f"Run results saved to: {run_dir}")
    logger.info(f"Adapters saved to: {adapters_dir}")
    logger.info(f"Evaluations saved to: {results_root}/evaluation/")
    logger.info(f"Generations saved to: {results_root}/generation/")
    logger.info(f"{'='*80}")
    
    return all_results


if __name__ == '__main__':
    main()
