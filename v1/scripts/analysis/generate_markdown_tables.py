#!/usr/bin/env python3
"""
merge_evalから直接Markdown表を生成

merge_evalディレクトリから直接JSONファイルを読み込み、
メソッド別・ペア別の完全なMarkdown表を生成
"""

import json
from pathlib import Path
from collections import defaultdict
import re

def load_and_aggregate_results(merge_eval_dir):
    """JSONファイルから直接データを集計"""
    data = defaultdict(lambda: defaultdict(lambda: {}))
    
    for json_file in Path(merge_eval_dir).glob('*.json'):
        if 'data_free' in json_file.name:
            continue
        
        try:
            with open(json_file) as f:
                j = json.load(f)
            
            fname = json_file.stem
            parts = fname.split('_')
            pair = f"{parts[0]}_{parts[1]}"  # A5_A7 or A6_A7
            
            # メソッド抽出
            if 'sst_k' in fname:
                k_match = re.search(r'_k(\d+)', fname)
                k = k_match.group(1) if k_match else None
                lw = '_lw' if '_lw_' in fname else ''
                method = f"SST-k{k}{lw}"
            elif 'dare' in fname:
                method = 'DARE'
            elif 'ties' in fname:
                method = 'TIES'
            elif 'task_arithmetic' in fname:
                method = 'Task Arithmetic'
            else:
                continue
            
            # Alpha抽出
            alpha_match = re.search(r'_a([\d.]+)', fname)
            alpha = alpha_match.group(1) if alpha_match else None
            if not alpha:
                continue
            
            # データセット & メトリクス
            metrics = j.get('metrics', {})
            if 'jailbreak' in fname:
                ds = 'JB'
                # Resistance Rate（防御率）を使用: 高い方が安全
                val = metrics.get('resistance_rate', 0) * 100  # パーセント
            elif 'repliqa' in fname:
                ds = 'RepliQA'
                rouge_l = metrics.get('rougeL', {})
                # rougeLは辞書形式なのでmeanを取得
                val = rouge_l.get('mean', 0) * 100 if isinstance(rouge_l, dict) else rouge_l * 100
            elif 'alpaca' in fname:
                ds = 'Alpaca'
                rouge_l = metrics.get('rougeL', {})
                val = rouge_l.get('mean', 0) * 100 if isinstance(rouge_l, dict) else rouge_l * 100
            else:
                continue
            
            # データ格納
            key = f"{pair}_{ds}"
            data[method][alpha][key] = val
        
        except Exception as e:
            continue
    
    return data

def print_table(method_name, alpha_data, pair, col1_key, col2_key, col1_name, col2_name):
    """Markdown表を出力"""
    print(f"\n### **{method_name}**\n")
    print(f"| α | {col1_name} | {col2_name} |")
    print("| --- | --- | --- |")
    
    # alpha値でソート
    alphas = sorted(alpha_data.keys(), key=lambda x: float(x))
    
    for alpha in alphas:
        val1 = alpha_data[alpha].get(col1_key, None)
        val2 = alpha_data[alpha].get(col2_key, None)
        
        val1_str = f"{val1:.2f}%" if val1 is not None and val1 > 0 else "-"
        val2_str = f"{val2:.2f}%" if val2 is not None and val2 > 0 else "-"
        
        print(f"| {alpha} | {val1_str} | {val2_str} |")

def main():
    merge_eval_dir = './merge_eval'
    
    print("# SST-Merge 評価結果サマリー\n")
    
    # データ読み込み
    data = load_and_aggregate_results(merge_eval_dir)
    
    # A5_A7 (RepliQA task)
    print("## **A5_A7 (RepliQA タスク)**\n")
    
    for method in sorted(data.keys()):
        if method in data and data[method]:
            print_table(method, data[method], 'A5_A7', 
                       'A5_A7_JB', 'A5_A7_RepliQA',
                       'Jailbreak', 'RepliQA')
    
    # A6_A7 (Alpaca task)
    print("\n## **A6_A7 (Alpaca タスク)**\n")
    
    for method in sorted(data.keys()):
        if method in data and data[method]:
            print_table(method, data[method], 'A6_A7',
                       'A6_A7_JB', 'A6_A7_Alpaca',
                       'Jailbreak', 'Alpaca')

if __name__ == '__main__':
    main()
