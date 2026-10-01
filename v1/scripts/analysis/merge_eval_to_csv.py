#!/usr/bin/env python3
"""
merge_eval結果をCSV形式で出力

全メソッド、全alpha値、全データセットの結果をCSVで出力する簡潔なスクリプト
"""

import json
from pathlib import Path
import re

def main():
    merge_eval_dir = Path('./merge_eval')
    
    # ヘッダー
    print("Method,K,Layerwise,Alpha,A5_A7_JB,A5_A7_RepliQA,A6_A7_JB,A6_A7_Alpaca")
    
    # データ収集
    data = {}  # (method, k, lw, alpha) -> {dataset: value}
    
    for json_file in merge_eval_dir.glob('*.json'):
        if 'data_free' in json_file.name:
            continue
        
        try:
            with open(json_file) as f:
                j = json.load(f)
            
            # ファイル名パース
            fname = json_file.stem
            parts = fname.split('_')
            pair = f"{parts[0]}_{parts[1]}"
            
            # メソッド
            if 'sst_k' in fname:
                k_match = re.search(r'_k(\d+)', fname)
                k = int(k_match.group(1)) if k_match else None
                lw = 1 if '_lw_' in fname else 0
                method = 'SST'
            elif 'dare' in fname:
                method, k, lw = 'D', None, None
            elif 'ties' in fname:
                method, k, lw = 'T', None, None
            elif 'task_arithmetic' in fname:
                method, k, lw = 'TA', None, None
            else:
                continue
            
            # Alpha
            alpha_match = re.search(r'_a([\d.]+)', fname)
            alpha = float(alpha_match.group(1)) if alpha_match else None
            if alpha is None:
                continue
            
            # データセット & メトリクス
            if 'jailbreak' in fname:
                ds = f"{pair}_JB"
                val = j['metrics'].get('attack_success_rate')
            elif 'repliqa' in fname:
                ds = f"{pair}_RepliQA"
                val = j['metrics'].get('rougeL')
            elif 'alpaca' in fname:
                ds = f"{pair}_Alpaca"
                val = j['metrics'].get('rougeL')
            else:
                continue
            
            if val is None:
                continue
            
            # キー作成
            key = (method, k, lw, alpha)
            if key not in data:
                data[key] = {}
            data[key][ds] = val * 100  # パーセント表示
        
        except Exception as e:
            continue
    
    # 出力
    for (method, k, lw, alpha) in sorted(data.keys()):
        k_str = str(k) if k is not None else ''
        lw_str = str(lw) if lw is not None else ''
        
        a5jb = data[(method, k, lw, alpha)].get('A5_A7_JB', '')
        a5rep = data[(method, k, lw, alpha)].get('A5_A7_RepliQA', '')
        a6jb = data[(method, k, lw, alpha)].get('A6_A7_JB', '')
        a6alp = data[(method, k, lw, alpha)].get('A6_A7_Alpaca', '')
       
        # 数値フォーマット
        a5jb_str = f"{a5jb:.2f}" if a5jb != '' else ''
        a5rep_str = f"{a5rep:.2f}" if a5rep != '' else ''
        a6jb_str = f"{a6jb:.2f}" if a6jb != '' else ''
        a6alp_str = f"{a6alp:.2f}" if a6alp != '' else ''
        
        print(f"{method},{k_str},{lw_str},{alpha},{a5jb_str},{a5rep_str},{a6jb_str},{a6alp_str}")

if __name__ == '__main__':
    main()
