#!/usr/bin/env python3
"""
merge_eval結果集計スクリプト

merge_evalディレクトリの全JSONファイルを読み込み、
条件ごとに整理した表を作成
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import re

def parse_filename(filename):
    """ファイル名から情報を抽出"""
    parts = filename.split('_')
    
    # ペア (A5_A7, A6_A7)
    pair = '_'.join(parts[:2])
    
    # データセット
    if 'jailbreak' in filename:
        dataset = 'JB'
    elif 'repliqa' in filename:
        dataset = 'RepliQA'
    elif 'alpaca' in filename:
        dataset = 'Alpaca'
    else:
        return None
    
    # メソッド
    if 'data_free' in filename:
        return None  # データフリー版は除外
    elif 'sst' in filename:
        method = 'SST'
        k_match = re.search(r'_k(\d+)', filename)
        k = k_match.group(1) if k_match else None
        lw = '_lw_' in filename
    elif 'dare' in filename:
        method = 'DARE'
        k = None
        lw = False
    elif 'task_arithmetic' in filename:
        method = 'TaskArith'
        k = None
        lw = False
    elif 'ties' in filename:
        method = 'TIES'
        k = None
        lw = False
    else:
        return None
    
    # alpha
    alpha_match = re.search(r'_a([\d.]+)', filename)
    alpha = alpha_match.group(1) if alpha_match else None
    
    return {
        'pair': pair,
        'method': method,
        'k': k,
        'lw': lw,
        'alpha': alpha,
        'dataset': dataset
    }

def load_results(merge_eval_dir):
    """全結果を読み込み"""
    results = []
    skipped = 0
    
    for json_file in Path(merge_eval_dir).glob('*.json'):
        try:
            info = parse_filename(json_file.stem)
            if info is None:
                skipped += 1
                continue
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            metrics = data.get('metrics', {})
            
            # メトリクス取得（正しいキー名を使用）
            if info['dataset'] == 'JB':
                value = metrics.get('attack_success_rate')  # jailbreak_asrではなくattack_success_rate
            elif info['dataset'] == 'RepliQA':
                value = metrics.get('rougeL')  # repliqa_rouge_lではなくrougeL
            elif info['dataset'] == 'Alpaca':
                value = metrics.get('rougeL')  # alpaca_rouge_lではなくrougeL
            else:
                value = None
            
            if value is not None:
                info['value'] = value
                results.append(info)
        
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
            continue
    
    print(f"Skipped {skipped} files (data_free or parse error)")
    return results

def create_summary_table(results):
    """サマリーテーブル作成"""
    # データを整理: method -> alpha -> dataset -> value
    data = defaultdict(lambda: defaultdict(dict))
    
    for r in results:
        if r['method'] == 'SST' and r['k']:
            key = f"SST-k{r['k']}{'_lw' if r['lw'] else ''}"
        else:
            key = r['method']
        
        alpha = r['alpha']
        dataset = f"{r['pair']}_{r['dataset']}"
        
        data[key][alpha][dataset] = r['value']
    
    return data

def print_results(data):
    """結果を表示"""
    print("=" * 120)
    print("SST-Merge 評価結果サマリー (全メソッド比較)")
    print("=" * 120)
    
    # alpha値のリスト（Noneを除外）
    all_alphas = sorted(
        set(alpha for method_data in data.values() for alpha in method_data.keys() if alpha is not None), 
        key=lambda x: float(x)
    )
    
    # 各メソッドごとに表示
    for method in sorted(data.keys()):
        print(f"\n{'='*120}")
        print(f"Method: {method}")
        print(f"{'='*120}")
        print(f"{'Alpha':>8}  {'A5_A7_JB':>10}  {'A5_A7_RepQ':>11}  {'A6_A7_JB':>10}  {'A6_A7_Alp':>11}")
        print("-" * 120)
        
        for alpha in all_alphas:
            if alpha in data[method]:
                a5_jb = data[method][alpha].get('A5_A7_JB', None)
                a5_rep = data[method][alpha].get('A5_A7_RepliQA', None)
                a6_jb = data[method][alpha].get('A6_A7_JB', None)
                a6_alp = data[method][alpha].get('A6_A7_Alpaca', None)
                
                a5_jb_str = f"{a5_jb:.2f}" if a5_jb is not None else "-"
                a5_rep_str = f"{a5_rep:.2f}" if a5_rep is not None else "-"
                a6_jb_str = f"{a6_jb:.2f}" if a6_jb is not None else "-"
                a6_alp_str = f"{a6_alp:.2f}" if a6_alp is not None else "-"
                
                print(f"{alpha:>8}  {a5_jb_str:>10}  {a5_rep_str:>11}  {a6_jb_str:>10}  {a6_alp_str:>11}")
    
    print("\n" + "=" * 120)
    print(f"集計完了")
    print("=" * 120)

def main():
    merge_eval_dir = sys.argv[1] if len(sys.argv) > 1 else './merge_eval'
    
    print(f"Loading results from: {merge_eval_dir}")
    results = load_results(merge_eval_dir)
    print(f"Loaded {len(results)} results\n")
    
    data = create_summary_table(results)
    print_results(data)

if __name__ == '__main__':
    main()
