#!/usr/bin/env python3
"""
k-alphaグリッドサーチスクリプト

Usage:
    python3 experiments/grid_search_k_alpha.py --tier 1
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import subprocess
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# グリッドサーチの設定
TIER1_COMBINATIONS = [
    (20, 0.7), (20, 0.9),
    (30, 0.9), (30, 1.0),
    (50, 0.8), (50, 0.9),
    (15, 1.0), (10, 1.0)
]

TIER2_COMBINATIONS = [
    (5, 1.0), (10, 0.9), (15, 0.9),
    (30, 0.7), (50, 0.7),
    (20, 0.5), (30, 0.5), (50, 0.5)
]

TIER3_COMBINATIONS = [
    # k値の詳細探索（固有値分析に基づく）
    (22, 0.9), (25, 0.9), (28, 0.9),
    (22, 0.8), (25, 0.8), (28, 0.8),
    # α値の詳細探索
    (20, 0.75), (20, 0.85), (20, 0.95),
    (30, 0.75), (30, 0.85), (30, 0.95)
]


def check_existing_adapter(k, alpha, model='llama-3.1-8b', variant='A5+A7'):
    """既存のアダプターファイルをチェック"""
    from pathlib import Path
    
    # アダプターファイルのパスを構築
    adapter_pattern = f'saved_adapters/{model}/sst_merged/sst_merged_{variant.replace("+", "_")}_k{k}_alpha{alpha:.2f}*.pt'
    
    import glob
    matching_files = glob.glob(adapter_pattern)
    
    if matching_files:
        logger.info(f"  ✓ Found existing adapter: {matching_files[0]}")
        return True
    return False


def check_existing_evaluation(k, alpha, model='llama-3.1-8b', variant='A5+A7'):
    """既存の評価結果をチェック"""
    from pathlib import Path
    import json
    
    # aggregated_results.jsonをチェック
    results_file = Path(f'results/model_evaluation/{model}/sst-merge/aggregated_results.json')
    
    if not results_file.exists():
        return False
    
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # キーを構築
        key = f"{variant}_k{k}_alpha{alpha:.1f}"
        
        if key in data:
            logger.info(f"  ✓ Found existing evaluation: {key}")
            return True
    except Exception as e:
        logger.warning(f"  Could not read aggregated results: {e}")
    
    return False


def run_sst_merge(k, alpha, model='llama-3.1-8b', variant='A5+A7', max_samples=500, skip_existing=True):
    """SST-Mergeを実行"""
    
    # 既存のアダプターをチェック
    if skip_existing and check_existing_adapter(k, alpha, model, variant):
        logger.info(f"  Skipping SST-Merge (adapter exists)")
        return 'skipped'
    
    cmd = [
        'python3', 'experiments/run_sst_merge.py',
        '--model', model,
        '--variant', variant,
        '--k', str(k),
        '--alpha', str(alpha),
        '--max_samples', str(max_samples)
    ]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Running SST-Merge: k={k}, alpha={alpha}")
    logger.info(f"{'='*80}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ SST-Merge completed successfully")
        return True
    else:
        logger.error(f"✗ SST-Merge failed")
        logger.error(f"Error: {result.stderr}")
        return False


def run_evaluation(model='llama-3.1-8b', k=None, alpha=None, variant='A5+A7', skip_existing=True):
    """特定のアダプターのみを評価（全サンプルで評価）"""
    
    # 既存の評価をチェック
    if skip_existing and k is not None and alpha is not None:
        if check_existing_evaluation(k, alpha, model, variant):
            logger.info(f"  Skipping evaluation (results exist)")
            return 'skipped'
    
    # 特定のアダプターファイルを直接評価
    # アダプターファイル名を構築
    adapter_filename = f"sst_merged_{variant.replace('+', '_')}_k{k}_alpha{alpha:.2f}_s500.pt"
    adapter_path = f"saved_adapters/{model}/sst_merged/{adapter_filename}"
    
    # アダプターが存在するか確認
    from pathlib import Path
    if not Path(adapter_path).exists():
        logger.error(f"  Adapter not found: {adapter_path}")
        return False
    
    # バリアントに応じた評価データセットを決定
    eval_datasets = ['jailbreak', 'beavertails', 'mmlu']
    if 'A5' in variant:
        eval_datasets.append('repliqa')
    if 'A6' in variant:
        eval_datasets.append('alpaca')
    if 'A9' in variant:
        eval_datasets.append('openmathinstruct')
    if 'A10' in variant:
        eval_datasets.append('mathcodeinstruct')
    if 'A11' in variant:
        eval_datasets.append('opencodeinstruct')
    
    # 既存の応答ファイルをチェック（モデルロード前）
    responses_dir = Path(f'results/model_evaluation/{model}/sst-merge')
    
    # 全データセットの応答ファイルが存在するかチェック
    all_exist = True
    for dataset in eval_datasets:
        # 応答ファイルのパターン (alphaは小数点以下の桁数が可変)
        pattern = f"responses_sst-merge_{model}_sst_merged_{variant.replace('+', '_')}_k{k}_alpha{alpha}_s500_{dataset}_*.jsonl"
        matching_files = list(responses_dir.glob(pattern))
        if not matching_files:
            all_exist = False
            break
    
    if all_exist:
        logger.info(f"  ✓ All evaluation results already exist, skipping...")
        logger.info(f"✓ Evaluation completed (skipped - results exist)")
        return 'skipped'
    
    # 評価スクリプトを直接Pythonで実行（特定アダプターのみ）
    logger.info(f"\nRunning evaluation for {adapter_filename}...")
    
    # evaluate_instruction_models.pyを直接インポートして実行
    import sys
    sys.path.insert(0, 'experiments')
    
    try:
        # 評価を実行
        from evaluate_instruction_models import ModelEvaluator
        from src.utils.model_loader import ModelLoader
        
        # モデルとトークナイザーをロード
        loader = ModelLoader(model_name=f'meta-llama/Llama-3.1-8B-Instruct')
        base_model, tokenizer = loader.load_model()
        
        # 評価器を初期化
        evaluator = ModelEvaluator(
            model_name=f'sst-merge_{model}'
        )
        
        # 特定のアダプターのみを評価
        from src.adapter_utils import load_lora_adapter
        from src.model_utils import apply_lora_adapter
        
        adapter, _ = load_lora_adapter(adapter_path)
        apply_lora_adapter(base_model, adapter)
        
        # バリアントに応じた評価データセットを決定
        eval_datasets = ['jailbreak', 'beavertails', 'mmlu']
        if 'A5' in variant:
            eval_datasets.append('repliqa')
        if 'A6' in variant:
            eval_datasets.append('alpaca')
        if 'A9' in variant:
            eval_datasets.append('openmathinstruct')
        if 'A10' in variant:
            eval_datasets.append('mathcodeinstruct')
        if 'A11' in variant:
            eval_datasets.append('opencodeinstruct')
        
        # 既存の応答ファイルをチェック
        model_display_name = f"SST-Merge ({variant}, k={k}, α={alpha})"
        responses_dir = Path(f'results/model_evaluation/{model}/sst-merge')
        
        # 全データセットの応答ファイルが存在するかチェック
        all_exist = True
        for dataset in eval_datasets:
            # 応答ファイルのパターン: responses_sst-merge_*_sst_merged_A5_A7_k20_alpha0.70_s500_jailbreak_*.jsonl
            pattern = f"responses_sst-merge_{model}_sst_merged_{variant.replace('+', '_')}_k{k}_alpha{alpha:.2f}_s500_{dataset}_*.jsonl"
            matching_files = list(responses_dir.glob(pattern))
            if not matching_files:
                all_exist = False
                break
        
        if all_exist:
            logger.info(f"  ✓ All evaluation results already exist, skipping...")
            logger.info(f"✓ Evaluation completed (skipped - results exist)")
            return 'skipped'
        
        # 評価実行
        evaluator.evaluate_model(
            base_model, tokenizer,
            model_name=model_display_name,
            eval_datasets=eval_datasets
        )
        
        # 結果を保存
        evaluator.save_results()
        
        logger.info(f"✓ Evaluation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='k-alpha grid search')
    parser.add_argument('--tier', type=str, default='1',
                        help='Tier level (1, 2, 3, or "all" for all tiers)')
    parser.add_argument('--model', type=str, default='llama-3.1-8b',
                        help='Base model name')
    parser.add_argument('--variant', type=str, default='A5+A7',
                        help='Adapter variant')
    parser.add_argument('--max_samples', type=int, default=500,
                        help='Max samples for FIM (fixed at 500 for consistency)')
    parser.add_argument('--skip_existing', action='store_true', default=True,
                        help='Skip experiments with existing results')
    args = parser.parse_args()
    
    # 'all'が指定された場合、全Tierを実行
    if args.tier.lower() == 'all':
        tiers_to_run = [1, 2, 3]
        logger.info("Running all tiers: 1, 2, 3")
    else:
        tiers_to_run = [int(args.tier)]
    
    # 各Tierを順次実行
    all_results = []
    overall_start_time = datetime.now()
    
    for tier in tiers_to_run:
        # 組み合わせを選択
        if tier == 1:
            combinations = TIER1_COMBINATIONS
        elif tier == 2:
            combinations = TIER2_COMBINATIONS
        elif tier == 3:
            combinations = TIER3_COMBINATIONS
        else:
            logger.error(f"Invalid tier: {tier}")
            continue
        
        logger.info(f"\n{'='*80}")
        logger.info(f"K-ALPHA GRID SEARCH (Tier {tier})")
        logger.info(f"{'='*80}")
        logger.info(f"Model: {args.model}")
        logger.info(f"Variant: {args.variant}")
        logger.info(f"Combinations: {len(combinations)}")
        logger.info(f"Max samples: {args.max_samples}")
        logger.info(f"Skip existing: {args.skip_existing}")
        
        # 実行ログ
        results = []
        start_time = datetime.now()
        skipped_count = 0
        
        for i, (k, alpha) in enumerate(combinations, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Tier {tier} - Experiment {i}/{len(combinations)}: k={k}, alpha={alpha}")
            logger.info(f"{'='*80}")
            
            # SST-Merge実行
            merge_result = run_sst_merge(
                k=k,
                alpha=alpha,
                model=args.model,
                variant=args.variant,
                max_samples=args.max_samples,
                skip_existing=args.skip_existing
            )
            
            if merge_result == 'skipped':
                # 評価もチェック
                eval_result = run_evaluation(
                    model=args.model,
                    k=k,
                    alpha=alpha,
                    variant=args.variant,
                    skip_existing=args.skip_existing
                )
                
                if eval_result == 'skipped':
                    skipped_count += 1
                    results.append({
                        'k': k,
                        'alpha': alpha,
                        'merge_success': 'skipped',
                        'eval_success': 'skipped',
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info(f"  ✓ Experiment skipped (already completed)")
                    continue
            
            if merge_result == True:
                # 評価実行
                eval_success = run_evaluation(
                    model=args.model,
                    k=k,
                    alpha=alpha,
                    variant=args.variant,
                    skip_existing=args.skip_existing
                )
                
                results.append({
                    'k': k,
                    'alpha': alpha,
                    'merge_success': True,
                    'eval_success': eval_success if eval_success != 'skipped' else True,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                results.append({
                    'k': k,
                    'alpha': alpha,
                    'merge_success': False,
                    'eval_success': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Tier結果を保存
        output_dir = Path('results/grid_search')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / f'grid_search_tier{tier}_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'tier': tier,
                'model': args.model,
                'variant': args.variant,
                'max_samples': args.max_samples,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"TIER {tier} COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"Results saved to: {results_file}")
        logger.info(f"Total experiments: {len(combinations)}")
        logger.info(f"Skipped (already done): {skipped_count}")
        logger.info(f"Successful: {sum(1 for r in results if r['merge_success'] == True and r['eval_success'] == True)}")
        logger.info(f"Failed: {sum(1 for r in results if r['merge_success'] == False or r['eval_success'] == False)}")
        
        all_results.extend(results)
    
    # 全Tier完了サマリー
    if len(tiers_to_run) > 1:
        logger.info(f"\n{'='*80}")
        logger.info(f"ALL TIERS GRID SEARCH COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"Total tiers: {len(tiers_to_run)}")
        logger.info(f"Total experiments: {len(all_results)}")
        logger.info(f"Total time: {datetime.now() - overall_start_time}")
        logger.info(f"Results directory: results/grid_search/")


if __name__ == '__main__':
    main()
