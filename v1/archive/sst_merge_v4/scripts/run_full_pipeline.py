#!/usr/bin/env python3
"""
SST-Merge V4: Full Pipeline

Complete pipeline:
1. LoRA Fine-Tuning: A5 (Utility/RepliQA), A7 (Safety/Jailbreak refusal)
2. Baseline Merge: TIES, DARE, Task Arithmetic
3. SST-Merge V4: GEVP-based merge
4. Evaluation: Jailbreak resistance, Utility (ROUGE-L)
5. Comparison: All methods vs targets

Usage:
    python run_full_pipeline.py --config configs/config.yaml
    python run_full_pipeline.py --quick  # Quick test with small samples
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
    parser = argparse.ArgumentParser(description="SST-Merge V4 Full Pipeline")
    
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
    parser.add_argument('--skip_a5', action='store_true',
                        help='Skip A5 (RepliQA) training')
    
    # A6 (Alpaca/General Utility) specific
    parser.add_argument('--a6_epochs', type=int, default=5,
                        help='Epochs for A6 (Alpaca)')
    parser.add_argument('--a6_lr', type=float, default=2e-4,
                        help='Learning rate for A6')
    parser.add_argument('--skip_a6', action='store_true',
                        help='Skip A6 (Alpaca) training')
    
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
            # Try using it as full model name
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
    
    # モデル名からショートネームを取得
    model_short_name = args.model_name.split('/')[-1].lower().replace('-', '_')
    
    # ディレクトリ構造:
    # results/
    #   adapters/
    #     base_model/
    #     FT/A5/, FT/A7/
    #     merge/mergekit/{ties,dare,task_arithmetic}/, merge/sst_merge/
    #   evaluation/
    #     base_model/, FT/, merge/
    #   run_YYYYMMDD_HHMMSS/
    #     config.json, summary.txt, all_results.json
    
    results_root = Path(args.output_dir).resolve()  # 絶対パスに変換
    run_dir = results_root / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # アダプター保存ディレクトリ（共有）
    adapters_dir = results_root / "adapters"
    base_model_dir = adapters_dir / "base_model"
    ft_dir = adapters_dir / "FT"
    a5_dir = ft_dir / "A5"
    a6_dir = ft_dir / "A6"
    a7_dir = ft_dir / "A7"
    merge_dir = adapters_dir / "merge"
    mergekit_dir = merge_dir / "mergekit"
    sst_merge_dir = merge_dir / "sst_merge"
    
    # 評価結果ディレクトリ（共有）
    eval_dir = results_root / "evaluation"
    eval_base_dir = eval_dir / "base_model"
    eval_ft_dir = eval_dir / "FT"
    eval_merge_dir = eval_dir / "merge"
    eval_mergekit_dir = eval_merge_dir / "mergekit"
    eval_sst_merge_dir = eval_merge_dir / "sst_merge"
    
    for d in [base_model_dir, a5_dir, a6_dir, a7_dir, mergekit_dir / "ties", mergekit_dir / "dare", 
              mergekit_dir / "task_arithmetic", sst_merge_dir,
              eval_base_dir, eval_ft_dir, 
              eval_mergekit_dir / "ties", eval_mergekit_dir / "dare", 
              eval_mergekit_dir / "task_arithmetic", eval_sst_merge_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 既存結果検索用のヘルパー関数
    def find_existing_adapter(directory: Path, pattern: str) -> Optional[Path]:
        """指定パターンに一致する既存アダプターを検索"""
        matches = list(directory.glob(f"{pattern}*.pt"))
        if matches:
            # 最新のものを返す
            return sorted(matches, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        return None
    
    def find_existing_eval(directory: Path, pattern: str) -> Optional[Path]:
        """指定パターンに一致する既存評価結果を検索"""
        matches = list(directory.glob(f"{pattern}*.json"))
        if matches:
            return sorted(matches, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        return None
    
    # モデルタイプを取得（Base/Instructを区別、lora_trainer.pyと同じロジック）
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
    
    # 現在の条件を表すパターン文字列
    # lora_trainer.pyの_save_adapterと一致させる
    ft_pattern = f"{model_type}_r{args.lora_r}_{args.num_epochs}ep"
    merge_pattern = f"{model_short_name}"
    sst_pattern = f"{model_short_name}_k{args.sst_k}_w{args.sst_weight}"
    
    logger.info(f"FT pattern for cache: A5_utility_{ft_pattern}*.pt")
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Device: {device}")
    
    # Save config
    config = vars(args)
    config['timestamp'] = timestamp
    config['device'] = device
    with open(run_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("\n" + "="*80)
    logger.info("SST-Merge V4: Full Pipeline")
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
    
    # A6 (Alpaca) data - optional
    alpaca_train_loader = None
    alpaca_eval_data = []
    if not args.skip_a6:
        alpaca_train_loader = data_factory.get_alpaca_dataloader(max_samples=5000)
        alpaca_eval_data = data_factory.get_alpaca_eval_data(max_samples=args.eval_samples)
    
    # Evaluation data
    jailbreak_eval_data = data_factory.get_jailbreak_eval_data(max_samples=args.eval_samples)
    repliqa_eval_data = data_factory.get_repliqa_eval_data(max_samples=args.eval_samples)
    
    logger.info(f"  Jailbreak train: {len(jailbreak_train_loader)} batches")
    logger.info(f"  RepliQA train: {len(repliqa_train_loader)} batches")
    if alpaca_train_loader:
        logger.info(f"  Alpaca train: {len(alpaca_train_loader)} batches")
    logger.info(f"  Jailbreak eval: {len(jailbreak_eval_data)} samples")
    logger.info(f"  RepliQA eval: {len(repliqa_eval_data)} samples")
    
    # =========================================================================
    # Step 2: Evaluate BASE MODEL (before any fine-tuning)
    # =========================================================================
    logger.info("\nStep 2: Evaluating BASE MODEL (before fine-tuning)...")
    
    from src.evaluator import Evaluator
    
    # 共通ハイパーパラメータ
    global_hyperparams = {
        # Training (shared)
        'lora_r': args.lora_r,
        # A7 (Safety) training
        'num_epochs': args.num_epochs,
        'learning_rate': args.learning_rate,
        # A5 (Utility) training - stronger for high ROUGE-L
        'a5_epochs': args.a5_epochs,
        'a5_lr': args.a5_lr,
        'a5_grad_accum': args.a5_grad_accum,
        # A6 (Alpaca) training
        'a6_epochs': args.a6_epochs,
        'a6_lr': args.a6_lr,
        'skip_a6': args.skip_a6,
        # SST-Merge
        'sst_k': args.sst_k,
        'sst_weight': args.sst_weight,
        'use_layerwise': not args.no_layerwise,
        'eval_samples': args.eval_samples
    }
    
    # 既存のベースモデル評価結果を検索
    base_pattern = f"BASE_MODEL_{model_short_name}"
    logger.info(f"  Looking for base model eval in: {eval_base_dir}")
    logger.info(f"  Pattern: {base_pattern}*.json")
    existing_base_eval = find_existing_eval(eval_base_dir, base_pattern)
    
    if existing_base_eval and not args.force_eval:
        logger.info(f"  Found existing base model evaluation: {existing_base_eval}")
        with open(existing_base_eval, 'r') as f:
            saved_data = json.load(f)
        results_base = {
            'adapter_name': 'BASE_MODEL',
            'summary': saved_data['summary'],
            'jailbreak': saved_data.get('jailbreak', {}),
            'utility': saved_data.get('utility', {})
        }
        logger.info(f"  BASE_MODEL: JB={results_base['summary']['jailbreak_resistance']*100:.1f}%, "
                    f"ROUGE-L={results_base['summary']['utility_rouge_l']*100:.1f}% (cached)")
    else:
        base_evaluator = Evaluator(
            model=model,
            tokenizer=tokenizer,
            device=device,
            output_dir=str(eval_base_dir),
            model_name=args.model_name,
            hyperparams=global_hyperparams
        )
        
        results_base = base_evaluator.evaluate_base_model(
            jailbreak_eval_data, repliqa_eval_data
        )
        
        logger.info(f"  BASE_MODEL: JB={results_base['summary']['jailbreak_resistance']*100:.1f}%, "
                    f"ROUGE-L={results_base['summary']['utility_rouge_l']*100:.1f}%")
        
        del base_evaluator
        torch.cuda.empty_cache()
    
    # =========================================================================
    # Step 3: LoRA Fine-Tuning
    # =========================================================================
    logger.info("\nStep 3: LoRA Fine-Tuning...")
    
    from src.lora_trainer import LoRATrainerV4
    
    adapter_a5 = None
    adapter_a7 = None
    
    # A5訓練（スキップ可能）
    if not args.skip_a5:
        # A5用のパターン（A5専用パラメータを使用）
        # 学習率を読みやすい形式に変換
        a5_lr_str = f"{args.a5_lr:.0e}".replace('-0', '-') if args.a5_lr < 0.001 else f"{args.a5_lr:.4f}".rstrip('0').rstrip('.')
        a5_ft_pattern = f"{model_type}_r{args.lora_r}_{args.a5_epochs}ep_{a5_lr_str}"
        
        # 既存のA5アダプターを検索
        existing_a5 = find_existing_adapter(a5_dir, f"A5_utility_{a5_ft_pattern}")
        if existing_a5 and not args.force_train:
            logger.info(f"\n--- Found existing A5 adapter: {existing_a5} ---")
            adapter_a5 = torch.load(existing_a5, map_location='cpu')['adapter']
            logger.info(f"  Loaded {len(adapter_a5)} parameters (cached)")
        else:
            logger.info("\n--- Training A5 (Utility/RepliQA) ---")
            logger.info(f"  A5 config: epochs={args.a5_epochs}, lora_r={args.lora_r}, lr={args.a5_lr}")
            trainer_a5 = LoRATrainerV4(
                model=model,
                tokenizer=tokenizer,
                device=device,
                output_dir=str(a5_dir)  # adapters/FT/A5/
            )
            adapter_a5 = trainer_a5.train_adapter(
                dataloader=repliqa_train_loader,
                adapter_name='A5_utility',
                num_epochs=args.a5_epochs,
                learning_rate=args.a5_lr,
                lora_r=args.lora_r,
                gradient_accumulation_steps=args.a5_grad_accum,
                val_dataloader=None,
                early_stopping_patience=100,  # A5ではEarly stoppingを無効化
                task_type='utility_repliqa'  # A5はRepliQA (RAG形式)
            )
    else:
        logger.info("\n--- Skipping A5 (RepliQA) training ---")
    
    # 既存のA7アダプターを検索
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
            output_dir=str(a7_dir)  # adapters/FT/A7/
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
    
    # A6 (Alpaca) 訓練 - オプション
    adapter_a6 = None
    if not args.skip_a6 and alpaca_train_loader:
        a6_ft_pattern = f"{model_type}_r{args.lora_r}_{args.a6_epochs}ep"
        existing_a6 = find_existing_adapter(a6_dir, f"A6_alpaca_{a6_ft_pattern}")
        if existing_a6 and not args.force_train:
            logger.info(f"\n--- Found existing A6 adapter: {existing_a6} ---")
            adapter_a6 = torch.load(existing_a6, map_location='cpu')['adapter']
            logger.info(f"  Loaded {len(adapter_a6)} parameters (cached)")
        else:
            logger.info("\n--- Training A6 (Alpaca/General Utility) ---")
            trainer_a6 = LoRATrainerV4(
                model=model,
                tokenizer=tokenizer,
                device=device,
                output_dir=str(a6_dir)
            )
            adapter_a6 = trainer_a6.train_adapter(
                dataloader=alpaca_train_loader,
                adapter_name='A6_alpaca',
                num_epochs=args.a6_epochs,
                learning_rate=args.a6_lr,
                lora_r=args.lora_r,
                val_dataloader=None,
                early_stopping_patience=100,
                task_type='utility_alpaca'  # A6はAlpaca (汎用指示追従)
            )
        logger.info(f"  A6: {len(adapter_a6)} parameters")
    
    # =========================================================================
    # Step 4: Evaluate A5, A6, and A7 (before merging)
    # =========================================================================
    logger.info("\nStep 4: Evaluating adapters...")
    
    all_results = []
    
    # Add BASE_MODEL results (already evaluated in Step 2)
    all_results.append(results_base)
    
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
    
    # Evaluate A5 (if available)
    results_a5 = None
    if adapter_a5 is not None:
        a5_eval_pattern = f"A5_utility_{model_short_name}_r{args.lora_r}_{args.a5_epochs}ep"
        existing_a5_eval = find_existing_eval(eval_ft_dir, a5_eval_pattern)
        
        if existing_a5_eval and not args.force_eval:
            logger.info(f"\n--- Found existing A5 evaluation: {existing_a5_eval} ---")
            with open(existing_a5_eval, 'r') as f:
                saved_data = json.load(f)
            results_a5 = {
                'adapter_name': 'A5_utility',
                'summary': saved_data['summary'],
                'jailbreak': saved_data.get('jailbreak', {}),
                'utility': saved_data.get('utility', {})
            }
            logger.info(f"  A5: JB={results_a5['summary']['jailbreak_resistance']*100:.1f}%, "
                        f"ROUGE-L={results_a5['summary']['utility_rouge_l']*100:.1f}% (cached)")
        else:
            logger.info("\n--- Evaluating A5 (Utility only) ---")
            ft_evaluator = Evaluator(
                model=model,
                tokenizer=tokenizer,
                device=device,
                output_dir=str(eval_ft_dir),
                model_name=args.model_name,
                hyperparams=global_hyperparams
            )
            results_a5 = ft_evaluator.evaluate_adapter(
                adapter_a5, 'A5_utility',
                jailbreak_eval_data, repliqa_eval_data,
                adapter_metadata=a5_metadata
            )
        all_results.append(results_a5)
    
    # Evaluate A7
    a7_eval_pattern = f"A7_safety_{model_short_name}_r{args.lora_r}_{args.num_epochs}ep"
    existing_a7_eval = find_existing_eval(eval_ft_dir, a7_eval_pattern)
    
    if existing_a7_eval and not args.force_eval:
        logger.info(f"\n--- Found existing A7 evaluation: {existing_a7_eval} ---")
        with open(existing_a7_eval, 'r') as f:
            saved_data = json.load(f)
        results_a7 = {
            'adapter_name': 'A7_safety',
            'summary': saved_data['summary'],
            'jailbreak': saved_data.get('jailbreak', {}),
            'utility': saved_data.get('utility', {})
        }
        logger.info(f"  A7: JB={results_a7['summary']['jailbreak_resistance']*100:.1f}%, "
                    f"ROUGE-L={results_a7['summary']['utility_rouge_l']*100:.1f}% (cached)")
    else:
        logger.info("\n--- Evaluating A7 (Safety only) ---")
        ft_evaluator = Evaluator(
            model=model,
            tokenizer=tokenizer,
            device=device,
            output_dir=str(eval_ft_dir),
            model_name=args.model_name,
            hyperparams=global_hyperparams
        )
        results_a7 = ft_evaluator.evaluate_adapter(
            adapter_a7, 'A7_safety',
            jailbreak_eval_data, repliqa_eval_data,
            adapter_metadata=a7_metadata
        )
    all_results.append(results_a7)
    
    # Evaluate A6 if available
    results_a6 = None
    if adapter_a6 is not None and alpaca_eval_data:
        a6_metadata = {
            'adapter_type': 'alpaca',
            'lora_r': args.lora_r,
            'epochs': args.a6_epochs,
            'learning_rate': args.a6_lr
        }
        a6_eval_pattern = f"A6_alpaca_{model_short_name}_r{args.lora_r}_{args.a6_epochs}ep"
        existing_a6_eval = find_existing_eval(eval_ft_dir, a6_eval_pattern)
        
        if existing_a6_eval and not args.force_eval:
            logger.info(f"\n--- Found existing A6 evaluation: {existing_a6_eval} ---")
            with open(existing_a6_eval, 'r') as f:
                saved_data = json.load(f)
            results_a6 = {
                'adapter_name': 'A6_alpaca',
                'summary': saved_data['summary'],
                'jailbreak': saved_data.get('jailbreak', {}),
                'utility': saved_data.get('utility', {})
            }
            logger.info(f"  A6: JB={results_a6['summary']['jailbreak_resistance']*100:.1f}%, "
                        f"ROUGE-L={results_a6['summary']['utility_rouge_l']*100:.1f}% (cached)")
        else:
            logger.info("\n--- Evaluating A6 (Alpaca) ---")
            ft_evaluator = Evaluator(
                model=model,
                tokenizer=tokenizer,
                device=device,
                output_dir=str(eval_ft_dir),
                model_name=args.model_name,
                hyperparams=global_hyperparams
            )
            # A6はAlpacaデータで評価
            results_a6 = ft_evaluator.evaluate_adapter(
                adapter_a6, 'A6_alpaca',
                jailbreak_eval_data, alpaca_eval_data,
                adapter_metadata=a6_metadata
            )
        all_results.append(results_a6)
    
    # =========================================================================
    # Step 5: Baseline Merges
    # =========================================================================
    logger.info("\nStep 5: Baseline Merges (TIES, DARE, Task Arithmetic)...")
    
    from src.baseline_merge import BaselineMerger
    
    baseline_merged = {}
    
    # Utility adapter: A5 または A6 を使用
    utility_adapter = adapter_a5 if adapter_a5 is not None else adapter_a6
    utility_name = "A5" if adapter_a5 is not None else "A6"
    
    if utility_adapter is None:
        logger.warning("  No utility adapter available (A5 and A6 both skipped). Skipping baseline merges.")
    else:
        logger.info(f"  Using {utility_name} as utility adapter for merging")
    
    adapters = [utility_adapter, adapter_a7] if utility_adapter is not None else None
    weights = [0.5, 0.5]
    
    if adapters is not None:
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
                
                # 保存
                save_path = method_dir / f"{method}_{model_short_name}_w0.5_0.5_{timestamp}.pt"
                torch.save({
                    'adapter': merged_adapter,
                    'metadata': {
                        'method': method,
                        'model': model_short_name,
                        'weights': weights,
                        'adapters': [f'{utility_name}_utility', 'A7_safety']
                    }
                }, save_path)
                logger.info(f"  Saved {method}: {save_path}")
    
    logger.info(f"  Baseline merges completed: {list(baseline_merged.keys())}")
    
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
        logger.info(f"  Loaded {len(sst_merged)} parameters (cached)")
    else:
        from src.sst_merge_v4 import SSTMergeV4
        
        sst_merger = SSTMergeV4(
            k=args.sst_k,
            safety_weight=args.sst_weight,
            device=device,
            use_layerwise_weights=not args.no_layerwise
        )
        
        # Utility adapter と dataloader を選択
        sst_utility_adapter = adapter_a5 if adapter_a5 is not None else adapter_a6
        sst_utility_dataloader = repliqa_train_loader if adapter_a5 is not None else alpaca_train_loader
        
        if sst_utility_adapter is None:
            logger.error("  No utility adapter available for SST-Merge. Skipping.")
            sst_merged = None
        else:
            sst_merged = sst_merger.merge(
                model=model,
                tokenizer=tokenizer,
                utility_adapter=sst_utility_adapter,
                safety_adapter=adapter_a7,
                utility_dataloader=sst_utility_dataloader,
                safety_dataloader=jailbreak_train_loader,
                max_samples=min(500, args.eval_samples * 2)
            )
        
        # Save SST-Merge adapter with hyperparameters in filename
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
        # 各メソッドごとのディレクトリ
        method_eval_dir = eval_mergekit_dir / method
        method_eval_dir.mkdir(parents=True, exist_ok=True)
        
        baseline_eval_pattern = f"baseline_{method}_{model_short_name}"
        existing_baseline_eval = find_existing_eval(method_eval_dir, baseline_eval_pattern)
        
        baseline_metadata = {
            'method': method,
            'weights': [0.5, 0.5],
            'adapters': ['A5_utility', 'A7_safety']
        }
        
        if existing_baseline_eval and not args.force_eval:
            logger.info(f"\n--- Found existing {method} evaluation: {existing_baseline_eval} ---")
            with open(existing_baseline_eval, 'r') as f:
                saved_data = json.load(f)
            results = {
                'adapter_name': f'baseline_{method}',
                'summary': saved_data['summary'],
                'jailbreak': saved_data.get('jailbreak', {}),
                'utility': saved_data.get('utility', {})
            }
            logger.info(f"  {method}: JB={results['summary']['jailbreak_resistance']*100:.1f}%, "
                        f"ROUGE-L={results['summary']['utility_rouge_l']*100:.1f}% (cached)")
        else:
            logger.info(f"\n--- Evaluating Baseline: {method} ---")
            merge_evaluator = Evaluator(
                model=model,
                tokenizer=tokenizer,
                device=device,
                output_dir=str(method_eval_dir),
                model_name=args.model_name,
                hyperparams=global_hyperparams
            )
            results = merge_evaluator.evaluate_adapter(
                merged, f'baseline_{method}',
                jailbreak_eval_data, repliqa_eval_data,
                adapter_metadata=baseline_metadata
            )
        all_results.append(results)
    
    # Evaluate SST-Merge
    lw_str = "layerwise" if not args.no_layerwise else "uniform"
    sst_eval_pattern = f"sst_merge_v4_{model_short_name}_k{args.sst_k}_w{args.sst_weight}_{lw_str}"
    existing_sst_eval = find_existing_eval(eval_sst_merge_dir, sst_eval_pattern)
    
    sst_metadata = {
        'method': 'sst_merge_v4',
        'k': args.sst_k,
        'safety_weight': args.sst_weight,
        'use_layerwise': not args.no_layerwise
    }
    
    if existing_sst_eval and not args.force_eval:
        logger.info(f"\n--- Found existing SST-Merge evaluation: {existing_sst_eval} ---")
        with open(existing_sst_eval, 'r') as f:
            saved_data = json.load(f)
        results_sst = {
            'adapter_name': 'sst_merge_v4',
            'summary': saved_data['summary'],
            'jailbreak': saved_data.get('jailbreak', {}),
            'utility': saved_data.get('utility', {})
        }
        logger.info(f"  SST-Merge: JB={results_sst['summary']['jailbreak_resistance']*100:.1f}%, "
                    f"ROUGE-L={results_sst['summary']['utility_rouge_l']*100:.1f}% (cached)")
    else:
        logger.info("\n--- Evaluating SST-Merge V4 ---")
        merge_evaluator = Evaluator(
            model=model,
            tokenizer=tokenizer,
            device=device,
            output_dir=str(eval_sst_merge_dir),
            model_name=args.model_name,
            hyperparams=global_hyperparams
        )
        results_sst = merge_evaluator.evaluate_adapter(
            sst_merged, 'sst_merge_v4',
            jailbreak_eval_data, repliqa_eval_data,
            adapter_metadata=sst_metadata
        )
    all_results.append(results_sst)
    
    # =========================================================================
    # Step 8: Comparison Summary
    # =========================================================================
    logger.info("\nStep 8: Final Comparison...")
    
    # compare_resultsのために一時的なEvaluatorを作成
    summary_evaluator = Evaluator(
        model=model,
        tokenizer=tokenizer,
        device=device,
        output_dir=str(eval_merge_dir),
        model_name=args.model_name,
        hyperparams=global_hyperparams
    )
    summary = summary_evaluator.compare_results(all_results)
    
    # Save summary to run directory
    with open(run_dir / 'summary.txt', 'w') as f:
        f.write(summary)
    
    # Save all results to run directory
    with open(run_dir / 'all_results.json', 'w') as f:
        # Simplify for JSON serialization
        serializable = []
        for r in all_results:
            serializable.append({
                'adapter_name': r['adapter_name'],
                'summary': r['summary']
            })
        json.dump(serializable, f, indent=2)
    
    logger.info(f"\n{'='*80}")
    logger.info("Pipeline completed!")
    logger.info(f"Run results saved to: {run_dir}")
    logger.info(f"Adapters saved to: {adapters_dir}")
    logger.info(f"Evaluations saved to: {eval_dir}")
    logger.info(f"{'='*80}")
    
    return all_results


if __name__ == '__main__':
    main()
