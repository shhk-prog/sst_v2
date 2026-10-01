#!/usr/bin/env python3
"""
応答ファイルから評価結果を集計してaggregated_results.jsonを更新

Usage:
    python3 experiments/aggregate_evaluation_results.py
"""

import json
import glob
import re
from pathlib import Path
from collections import defaultdict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_k_alpha_from_filename(filename):
    """ファイル名からk, alphaを抽出"""
    k_val = None
    alpha_val = None
    
    # 新形式: SST-Merge (A5+A7, k=X, α=Y)
    if 'SST-Merge (A5+A7' in filename:
        match = re.search(r'k=(\d+),\s*α=([\d.]+)', filename)
        if match:
            k_val = match.group(1)
            alpha_val = match.group(2)
    
    # 旧形式: sst_merged_A5_A7_kX_alphaY
    elif 'sst_merged_A5_A7' in filename:
        match = re.search(r'_k(\d+)_alpha([\d.]+)', filename)
        if match:
            k_val = match.group(1)
            alpha_val = match.group(2)
    
    return k_val, alpha_val


def extract_dataset_from_filename(filename):
    """ファイル名からデータセット名を抽出"""
    parts = filename.split('_')
    
    # 新形式の場合
    if 'SST-Merge' in filename:
        return parts[-2]
    
    # 旧形式の場合
    for i, part in enumerate(parts):
        if part.startswith('alpha') and i+2 < len(parts):
            return parts[i+2]
    
    return None


def evaluate_responses(response_file, dataset):
    """応答ファイルから評価指標を計算"""
    try:
        with open(response_file, 'r') as f:
            responses = [json.loads(line) for line in f]
        
        if not responses:
            return None
        
        result = {'total': len(responses)}
        
        if dataset == 'jailbreak':
            resistant_count = sum(1 for r in responses if r.get('is_resistant', False))
            result['resistance_rate'] = resistant_count / len(responses)
        
        elif dataset == 'beavertails':
            refusal_count = sum(1 for r in responses if r.get('is_safe', False))
            result['refusal_rate'] = refusal_count / len(responses)
        
        elif dataset == 'mmlu':
            correct_count = sum(1 for r in responses if r.get('is_correct', False))
            result['accuracy'] = correct_count / len(responses)
        
        elif dataset == 'repliqa':
            rouge_scores = [r.get('rouge_l', 0) for r in responses if 'rouge_l' in r]
            if rouge_scores:
                result['rouge_l'] = sum(rouge_scores) / len(rouge_scores)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing {response_file.name}: {e}")
        return None


def main():
    logger.info("Starting evaluation aggregation...")
    
    # 応答ファイルのディレクトリ
    response_dir = Path('results/model_evaluation/llama-3.1-8b/sst-merge')
    
    # 既存のaggregated_results.jsonを読み込み
    aggregated_file = response_dir / 'aggregated_results.json'
    if aggregated_file.exists():
        with open(aggregated_file, 'r') as f:
            aggregated_results = json.load(f)
        logger.info(f"Loaded existing aggregated results: {len(aggregated_results)} entries")
    else:
        aggregated_results = {}
        logger.info("No existing aggregated results found, starting fresh")
    
    # 全てのA5+A7応答ファイルを処理
    all_files = list(response_dir.glob('responses_sst-merge_*A5*A7*.jsonl'))
    logger.info(f"Found {len(all_files)} response files")
    
    # k-alpha組み合わせごとに集計
    combinations = defaultdict(lambda: {})
    
    for response_file in all_files:
        filename = response_file.stem
        
        # k, alphaを抽出
        k_val, alpha_val = extract_k_alpha_from_filename(filename)
        if not (k_val and alpha_val):
            continue
        
        # データセット名を抽出
        dataset = extract_dataset_from_filename(filename)
        if not dataset:
            continue
        
        # 評価結果を計算
        result = evaluate_responses(response_file, dataset)
        if result:
            key = f"A5+A7_k{k_val}_alpha{alpha_val}"
            if key not in combinations:
                combinations[key] = {}
            combinations[key][dataset] = result
    
    # aggregated_resultsを更新
    updated_count = 0
    new_count = 0
    
    for key, metrics in combinations.items():
        if key in aggregated_results:
            # 既存エントリを更新
            aggregated_results[key].update(metrics)
            updated_count += 1
        else:
            # 新規エントリを追加
            aggregated_results[key] = metrics
            new_count += 1
    
    # 結果を保存
    with open(aggregated_file, 'w') as f:
        json.dump(aggregated_results, f, indent=2)
    
    logger.info(f"✓ Aggregation complete!")
    logger.info(f"  Total entries: {len(aggregated_results)}")
    logger.info(f"  Updated: {updated_count}")
    logger.info(f"  New: {new_count}")
    logger.info(f"  Saved to: {aggregated_file}")
    
    # サマリーを表示
    print("\n" + "=" * 80)
    print("集計結果サマリー")
    print("=" * 80)
    print(f"合計組み合わせ数: {len(aggregated_results)}")
    print(f"更新された組み合わせ: {updated_count}")
    print(f"新規追加された組み合わせ: {new_count}")
    print("=" * 80)


if __name__ == '__main__':
    main()
