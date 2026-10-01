#!/usr/bin/env python3
"""
CSVからMarkdown表を生成

merge_eval_results.csvを読み込み、
メソッド別・ペア別の見やすいMarkdown表を生成
"""

import csv
from collections import defaultdict

def load_csv(filepath):
    """CSVを読み込み"""
    data = defaultdict(lambda: defaultdict(lambda: {}))
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row['Method']
            k = row['K']
            lw = row['Layerwise']
            alpha = row['Alpha']
            
            # メソッド名作成
            if method == 'SST':
                method_name = f"SST-k{k}{'_lw' if lw == '1' else ''}"
            elif method == 'D':
                method_name = 'DARE'
            elif method == 'T':
                method_name = 'TIES'
            elif method == 'TA':
                method_name = 'Task Arithmetic'
            else:
                method_name = method
            
            # データ格納（キー名を修正）
            data[method_name][alpha]['A5_A7_JB'] = row.get('A5_A7_JB', '')
            data[method_name][alpha]['A5_A7_RepliQA'] = row.get('A5_A7_RepliQA', '')
            data[method_name][alpha]['A6_A7_JB'] = row.get('A6_A7_JB', '')
            data[method_name][alpha]['A6_A7_Alpaca'] = row.get('A6_A7_Alpaca', '')
    
    return data

def format_value(val):
    """値をフォーマット"""
    if val == '' or val is None:
        return '-'
    try:
        return f"{float(val):.2f}%"
    except:
        return val

def print_table(method_name, data, pair, col1_name, col2_name):
    """Markdown表を出力"""
    print(f"\n### **{method_name}**\n")
    print(f"| α | {col1_name} | {col2_name} |")
    print("| --- | --- | --- |")
    
    # alpha値でソート
    alphas = sorted(data.keys(), key=lambda x: float(x))
    
    # キー名を構築
    key1 = f'{pair}_{"JB" if col1_name == "Jailbreak" else col1_name}'
    key2 = f'{pair}_{"JB" if col2_name == "Jailbreak" else col2_name}'
    
    for alpha in alphas:
        val1 = format_value(data[alpha].get(key1, ''))
        val2 = format_value(data[alpha].get(key2, ''))
        print(f"| {alpha} | {val1} | {val2} |")

def main():
    csv_path = '/mnt/iag-02/home/hiromi/.gemini/antigravity/brain/5a5b16df-0b92-4d66-897e-237d61b02c63/merge_eval_results.csv'
    
    data = load_csv(csv_path)
    
    # A5_A7 (RepliQA task)
    print("# SST-Merge 評価結果サマリー\n")
    print("## **A5_A7 (RepliQA タスク)**\n")
    
    for method in ['Task Arithmetic', 'TIES', 'DARE', 'SST-k5', 'SST-k5_lw', 
                   'SST-k10', 'SST-k10_lw', 'SST-k20', 'SST-k20_lw']:
        if method in data and data[method]:
            print_table(method, data[method], 'A5_A7', 'Jailbreak', 'RepliQA')
    
    # A6_A7 (Alpaca task)
    print("\n## **A6_A7 (Alpaca タスク)**\n")
    
    for method in ['Task Arithmetic', 'TIES', 'DARE', 'SST-k5', 'SST-k5_lw',
                   'SST-k10', 'SST-k10_lw', 'SST-k20', 'SST-k20_lw']:
        if method in data and data[method]:
            print_table(method, data[method], 'A6_A7', 'Jailbreak', 'Alpaca')

if __name__ == '__main__':
    main()
