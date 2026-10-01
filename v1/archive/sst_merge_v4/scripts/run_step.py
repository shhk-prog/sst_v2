#!/usr/bin/env python3
"""
SST-Merge V4: Individual Step Runner

Run individual steps of the pipeline:
- train: LoRA Fine-Tuning only
- merge: Baseline + SST-Merge only (requires adapters)
- eval: Evaluation only (requires adapters/merged)
- all: Full pipeline (default)

Usage:
    python run_step.py train --num_epochs 5
    python run_step.py merge --adapter_a5 path/to/a5.pt --adapter_a7 path/to/a7.pt
    python run_step.py eval --adapter path/to/adapter.pt --name my_adapter
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import torch
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SUPPORTED_MODELS = {
    'llama3.1-8b': 'meta-llama/Meta-Llama-3.1-8B',
    'llama3-8b': 'meta-llama/Meta-Llama-3-8B',
    'mistral-7b-v0.1': 'mistralai/Mistral-7B-Instruct-v0.1',
    'mistral-7b-v0.2': 'mistralai/Mistral-7B-Instruct-v0.2',
}


def parse_args():
    parser = argparse.ArgumentParser(description="SST-Merge V4 Step Runner")
    
    # Step selection
    parser.add_argument('step', type=str, choices=['train', 'merge', 'eval', 'all'],
                        help='Step to run: train, merge, eval, or all')
    
    # Model
    parser.add_argument('--model', type=str, default='llama3.1-8b',
                        help='Model shortcut or full HF path')
    
    # Data paths
    parser.add_argument('--jailbreak_csv', type=str, default=None)
    
    # Training options
    parser.add_argument('--num_epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--learning_rate', type=float, default=2e-4)
    parser.add_argument('--lora_r', type=int, default=16)
    
    # Adapter paths (for merge/eval)
    parser.add_argument('--adapter_a5', type=str, default=None,
                        help='Path to A5 (Utility) adapter')
    parser.add_argument('--adapter_a7', type=str, default=None,
                        help='Path to A7 (Safety) adapter')
    parser.add_argument('--adapter', type=str, default=None,
                        help='Path to single adapter (for eval)')
    parser.add_argument('--name', type=str, default='custom_adapter',
                        help='Name for adapter in eval')
    
    # SST-Merge options
    parser.add_argument('--sst_k', type=int, default=20)
    parser.add_argument('--sst_weight', type=float, default=1.0)
    parser.add_argument('--no_layerwise', action='store_true')
    
    # Evaluation
    parser.add_argument('--eval_samples', type=int, default=500)
    
    # Output
    parser.add_argument('--output_dir', type=str, default=None)
    
    return parser.parse_args()


def load_model_and_tokenizer(model_name, device):
    """Load model and tokenizer"""
    if model_name in SUPPORTED_MODELS:
        model_name = SUPPORTED_MODELS[model_name]
    
    logger.info(f"Loading model: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map='auto'
    )
    
    return model, tokenizer, model_name


def run_train(args, model, tokenizer, output_dir, device):
    """Run training step only"""
    logger.info("\n" + "="*60)
    logger.info("Step: TRAIN (LoRA Fine-Tuning)")
    logger.info("="*60)
    
    from src.data_loader import DataLoaderFactory
    from src.lora_trainer import LoRATrainerV4
    
    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.parent
    
    jailbreak_csv = args.jailbreak_csv or str(project_dir / "data" / "response_dataframe.csv")
    
    # Data loaders
    data_factory = DataLoaderFactory(
        tokenizer=tokenizer,
        jailbreak_csv_path=jailbreak_csv,
        batch_size=args.batch_size
    )
    
    jailbreak_train_loader = data_factory.get_jailbreak_dataloader(split='train')
    jailbreak_val_loader = data_factory.get_jailbreak_dataloader(split='val')
    repliqa_train_loader = data_factory.get_repliqa_dataloader(split='train')
    
    logger.info(f"  Jailbreak train: {len(jailbreak_train_loader)} batches")
    logger.info(f"  RepliQA train: {len(repliqa_train_loader)} batches")
    
    # Trainer
    adapters_dir = output_dir / "adapters"
    adapters_dir.mkdir(exist_ok=True)
    
    trainer = LoRATrainerV4(
        model=model,
        tokenizer=tokenizer,
        device=device,
        output_dir=str(adapters_dir)
    )
    
    # Train A5 (Utility)
    logger.info("\n--- Training A5 (Utility/RepliQA) ---")
    adapter_a5 = trainer.train_adapter(
        dataloader=repliqa_train_loader,
        adapter_name='A5_utility',
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        lora_r=args.lora_r,
        val_dataloader=None
    )
    
    # Train A7 (Safety)
    logger.info("\n--- Training A7 (Safety/Jailbreak) ---")
    adapter_a7 = trainer.train_adapter(
        dataloader=jailbreak_train_loader,
        adapter_name='A7_safety',
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        lora_r=args.lora_r,
        val_dataloader=jailbreak_val_loader
    )
    
    logger.info(f"\n✓ Training completed!")
    logger.info(f"  A5: {len(adapter_a5)} parameters")
    logger.info(f"  A7: {len(adapter_a7)} parameters")
    logger.info(f"  Saved to: {adapters_dir}")
    
    return adapter_a5, adapter_a7


def run_merge(args, model, tokenizer, output_dir, device):
    """Run merge step only"""
    logger.info("\n" + "="*60)
    logger.info("Step: MERGE (Baseline + SST-Merge)")
    logger.info("="*60)
    
    if not args.adapter_a5 or not args.adapter_a7:
        raise ValueError("--adapter_a5 and --adapter_a7 required for merge step")
    
    # Load adapters
    adapter_a5 = torch.load(args.adapter_a5, map_location='cpu')['adapter']
    adapter_a7 = torch.load(args.adapter_a7, map_location='cpu')['adapter']
    
    logger.info(f"  Loaded A5: {len(adapter_a5)} parameters")
    logger.info(f"  Loaded A7: {len(adapter_a7)} parameters")
    
    from src.data_loader import DataLoaderFactory
    from src.baseline_merge import BaselineMerger
    from src.sst_merge_v4 import SSTMergeV4
    
    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.parent
    jailbreak_csv = args.jailbreak_csv or str(project_dir / "data" / "response_dataframe.csv")
    
    data_factory = DataLoaderFactory(
        tokenizer=tokenizer,
        jailbreak_csv_path=jailbreak_csv,
        batch_size=args.batch_size
    )
    
    # Baseline merges
    logger.info("\n--- Baseline Merges ---")
    merger = BaselineMerger(device=device)
    baseline_merged = merger.merge_all_methods([adapter_a5, adapter_a7], [0.5, 0.5])
    
    # SST-Merge V4
    logger.info("\n--- SST-Merge V4 ---")
    
    repliqa_train_loader = data_factory.get_repliqa_dataloader(split='train')
    jailbreak_train_loader = data_factory.get_jailbreak_dataloader(split='train')
    
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
        max_samples=500
    )
    
    # Save
    adapters_dir = output_dir / "adapters"
    adapters_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sst_merger.save_merged_adapter(
        sst_merged,
        str(adapters_dir / f"sst_merged_{timestamp}.pt"),
        metadata={'k': args.sst_k, 'safety_weight': args.sst_weight}
    )
    
    logger.info(f"\n✓ Merge completed!")
    logger.info(f"  Baselines: {list(baseline_merged.keys())}")
    logger.info(f"  SST-Merge: saved to {adapters_dir}")
    
    return baseline_merged, sst_merged


def run_eval(args, model, tokenizer, output_dir, device):
    """Run evaluation step only"""
    logger.info("\n" + "="*60)
    logger.info("Step: EVAL (Evaluation)")
    logger.info("="*60)
    
    from src.data_loader import DataLoaderFactory
    from src.evaluator import Evaluator
    
    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.parent
    jailbreak_csv = args.jailbreak_csv or str(project_dir / "data" / "response_dataframe.csv")
    
    data_factory = DataLoaderFactory(
        tokenizer=tokenizer,
        jailbreak_csv_path=jailbreak_csv,
        batch_size=args.batch_size
    )
    
    jailbreak_eval_data = data_factory.get_jailbreak_eval_data(max_samples=args.eval_samples)
    repliqa_eval_data = data_factory.get_repliqa_eval_data(max_samples=args.eval_samples)
    
    evaluator = Evaluator(
        model=model,
        tokenizer=tokenizer,
        device=device,
        output_dir=str(output_dir / 'eval_results')
    )
    
    all_results = []
    
    if args.adapter:
        # Evaluate single adapter
        adapter = torch.load(args.adapter, map_location='cpu')['adapter']
        results = evaluator.evaluate_adapter(
            adapter, args.name,
            jailbreak_eval_data, repliqa_eval_data
        )
        all_results.append(results)
    
    elif args.adapter_a5 and args.adapter_a7:
        # Evaluate A5, A7, and baselines/SST-Merge
        adapter_a5 = torch.load(args.adapter_a5, map_location='cpu')['adapter']
        adapter_a7 = torch.load(args.adapter_a7, map_location='cpu')['adapter']
        
        # Base model
        results_base = evaluator.evaluate_base_model(jailbreak_eval_data, repliqa_eval_data)
        all_results.append(results_base)
        
        # A5
        results_a5 = evaluator.evaluate_adapter(
            adapter_a5, 'A5_utility', jailbreak_eval_data, repliqa_eval_data
        )
        all_results.append(results_a5)
        
        # A7
        results_a7 = evaluator.evaluate_adapter(
            adapter_a7, 'A7_safety', jailbreak_eval_data, repliqa_eval_data
        )
        all_results.append(results_a7)
    
    else:
        # Just base model
        results_base = evaluator.evaluate_base_model(jailbreak_eval_data, repliqa_eval_data)
        all_results.append(results_base)
    
    # Summary
    if len(all_results) > 1:
        evaluator.compare_results(all_results)
    
    return all_results


def main():
    args = parse_args()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Device: {device}")
    
    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        script_dir = Path(__file__).parent.resolve()
        output_dir = script_dir.parent / "results" / f"{args.step}_{timestamp}"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output: {output_dir}")
    
    # Load model
    model, tokenizer, model_name = load_model_and_tokenizer(args.model, device)
    
    # Run step
    if args.step == 'train':
        run_train(args, model, tokenizer, output_dir, device)
    
    elif args.step == 'merge':
        run_merge(args, model, tokenizer, output_dir, device)
    
    elif args.step == 'eval':
        run_eval(args, model, tokenizer, output_dir, device)
    
    elif args.step == 'all':
        # Full pipeline - use run_full_pipeline.py instead
        logger.info("For full pipeline, use: python run_full_pipeline.py")
        return
    
    logger.info(f"\n✓ Step '{args.step}' completed!")
    logger.info(f"Results saved to: {output_dir}")


if __name__ == '__main__':
    main()
