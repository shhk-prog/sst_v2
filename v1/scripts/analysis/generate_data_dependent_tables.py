#!/usr/bin/env python3
"""
データ依存SST-Merge (Additive & Interpolation) の評価結果を集計し、
Markdown形式のテーブルを出力するスクリプト。

Data-Free版の結果は除外します。
eval/merged ディレクトリを再帰的にスキャンします。
"""

import json
from pathlib import Path
from collections import defaultdict
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_and_aggregate_results(merge_eval_dir):
    """JSONファイルから直接データを集計"""
    # {model_pair: {method_type: {k: {layerwise: {alpha: {metric: value}}}}}}
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
    
    # 再帰的にJSONファイルを検索
    files = list(Path(merge_eval_dir).rglob('*.json'))
    logger.info(f"Found {len(files)} JSON files in {merge_eval_dir} and subdirectories")
    
    for json_file in files:
        fname = json_file.stem
        
        # Data-Freeは除外
        if 'data_free' in fname:
            continue

        try:
            with open(json_file) as f:
                j = json.load(f)
            
            # Model Pair判定 (A5_A7 or A6_A7)
            model_pair = None
            if fname.startswith('A5_A7'):
                model_pair = 'A5_A7'
            elif fname.startswith('A6_A7'):
                model_pair = 'A6_A7'
            else:
                continue # Unknown model pair

            # Method Type判定
            method_type = None
            
            # Baseline methods first
            if 'task_arithmetic' in fname:
                method_type = 'Task Arithmetic'
            elif 'dare' in fname:
                method_type = 'DARE'
            elif 'ties' in fname:
                method_type = 'TIES'
            # SST-Merge methods
            elif 'interp' in fname:
                if 'nogevp' in fname or 'gevp_off' in fname:
                     method_type = 'Interpolation (GEVP OFF)'
                else:
                     method_type = 'Interpolation (GEVP ON)'
            elif 'sst' in fname and '_hard_full_' in fname:
                method_type = 'Additive (Hard)'
            elif 'sst' in fname and '_hard_' in fname and '_full_' not in fname:
                method_type = 'Additive (Hard)'
            elif 'sst' in fname and 'k' in fname: # additive soft has k in filename
                method_type = 'Additive (Soft)'
            elif 'soft_add' in fname:
                 if '_k' in fname:
                    method_type = 'Additive (Soft)'
                 else:
                    continue
            else:
                continue

            # k値取得 (k=5, 10, 20, 50 をサポート; baselines は k 不使用)
            k = None
            if method_type in ['Task Arithmetic', 'DARE', 'TIES']:
                k = 0  # Dummy value for baselines (they don't use k)
            else:
                k_match = re.search(r'_k(\d+)', fname)
                if k_match:
                    k = int(k_match.group(1))
                else:
                    continue # Skip if k is not found
                
            # Layerwise判定 (baseline methods don't have layerwise)
            if method_type in ['Task Arithmetic', 'DARE', 'TIES']:
                layerwise = False  # Baseline methods don't have layerwise
            else:
                layerwise = '_lw' in fname # _lw present means True
            
            # Alpha取得
            alpha_match = re.search(r'_a([\d.]+)', fname)
            if not alpha_match:
                continue
            alpha = float(alpha_match.group(1))

            # メトリクス取得
            metrics = j.get('metrics', {})
            val = 0
            metric_name = ''
            
            if 'jailbreak' in fname:
                metric_name = 'JB'
                # Resistance Rate
                if 'resistance_rate' in metrics:
                    val = metrics['resistance_rate'] * 100
                elif 'attack_success_rate' in metrics:
                    val = (1.0 - metrics['attack_success_rate']) * 100
            elif 'repliqa' in fname:
                metric_name = 'Utility' # Unified name for utility metric
                rouge1 = metrics.get('rouge1', 0)
                if isinstance(rouge1, dict):
                    val = rouge1.get('mean', 0) * 100
                else:
                    val = rouge1 * 100
            elif 'alpaca' in fname:
                metric_name = 'Utility' # Unified name for utility metric
                # Check for win_rate first, then standard metrics
                if 'win_rate' in metrics:
                     val = metrics['win_rate']
                elif 'win_rate_adjusted' in metrics:
                     val = metrics['win_rate_adjusted']
                else:
                     # Use rouge1 for consistency with Data-Free tables
                     rouge1 = metrics.get('rouge1', 0)
                     if isinstance(rouge1, dict):
                        val = rouge1.get('mean', 0) * 100
                     else:
                        val = rouge1 * 100
            else:
                continue
          
            if val != 0 or method_type: # Only add if we have valid data
                data[model_pair][method_type][k][layerwise][alpha][metric_name] = val
            
        except Exception as e:
            logger.error(f"Error parsing {json_file}: {e}")
            continue
            
    return data

def print_markdown_table(title, alpha_dict, utility_name):
    """
    alpha_dict: {alpha: {'JB': val, 'Utility': val}}
    """
    print(f"\n**{title}**\n")
    print(f"| α | JB Resistance | {utility_name} |")
    print("| --- | --- | --- |")
    
    alphas = sorted(alpha_dict.keys())
    for alpha in alphas:
        metrics = alpha_dict[alpha]
        jb = metrics.get('JB', None)
        utility = metrics.get('Utility', None)
        
        jb_str = f"{jb:.2f}%" if jb is not None else "-"
        utility_str = f"{utility:.2f}%" if utility is not None else "-"
        
        print(f"| {alpha:.2f} | {jb_str} | {utility_str} |")

def main():
    # 評価結果ディレクトリ
    base_eval_dir = Path(__file__).parent.parent.parent / "eval" / "merged"
    
    if not base_eval_dir.exists():
        logger.error(f"Directory not found: {base_eval_dir}")
        return
            
    final_data = load_and_aggregate_results(base_eval_dir)

    # Output Tables
    model_pairs = sorted(final_data.keys())
    
    for mp in model_pairs:
        # A5_A7 is RepliQA, A6_A7 is Alpaca
        utility_name = "RepliQA" if mp == "A5_A7" else "Alpaca"
        print(f"\n# Model Pair: {mp} (Utility: {utility_name})\n")
        
        # Defined order for method types
        method_types = [
            'Task Arithmetic',
            'DARE', 
            'TIES',
            'Additive (Soft)',
            'Additive (Hard)',
            'Interpolation (GEVP ON)', 
            'Interpolation (GEVP OFF)'
        ]
        
        for m_type in method_types:
            if m_type not in final_data[mp]:
                continue
                
            print(f"## {m_type}\n")
            
            # For baseline methods, they don't use k/layerwise
            if m_type in ['Task Arithmetic', 'DARE', 'TIES']:
                # Baseline methods only have k=0, layerwise=False
                if 0 in final_data[mp][m_type] and False in final_data[mp][m_type][0]:
                    print_markdown_table(m_type, final_data[mp][m_type][0][False], utility_name)
            else:
                # SST-Merge methods with k and layerwise
                k_values = sorted(final_data[mp][m_type].keys())
                for k in k_values:
                    for lw in [False, True]:
                        if lw in final_data[mp][m_type][k]:
                            # Title generation
                            lw_str = "layerwise=True" if lw else "layerwise=False"
                            
                            if m_type == 'Additive':
                                title = f"SST-k{k} {lw_str}"
                            elif m_type == 'Interpolation (GEVP ON)':
                                title = f"k={k}, GEVP有効, {lw_str}"
                            else:
                                title = f"k={k}, GEVP無効, {lw_str}"
                                
                            print_markdown_table(title, final_data[mp][m_type][k][lw], utility_name)

if __name__ == "__main__":
    main()
