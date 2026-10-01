#!/usr/bin/env python3
"""
Data-Free SST-Merge評価結果集計スクリプト

eval/merged/data_freeから評価結果を読み込んで、
k値とlayerwiseオプションごとにテーブル形式で結果をまとめます。
"""

import json
from pathlib import Path
from collections import defaultdict

# 評価結果ディレクトリ
eval_dir = Path("../../eval/merged/data_free")

# 結果を格納する辞書
# structure: results[pair][k][layerwise][alpha] = {'jb': float, 'utility': float}
results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

alpha_values = [0.05, 0.07, 0.09, 0.1, 0.12, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

# すべての評価結果ファイルを読み込み
for file in eval_dir.glob("*_eval_results.json"):
    filename = file.name
    
    # ファイル名から情報を抽出
    # 例: A5_A7_data_free_k10_lw_a0.05_topk10_jailbreak_eval_results.json
    # 例: A6_A7_data_free_k5_a0.1_topk5_alpaca_eval_results.json
    
    if not filename.startswith(("A5_A7", "A6_A7")):
        continue
    
    # ペアを判定
    pair = "A5_A7" if filename.startswith("A5_A7") else "A6_A7"
    
    # k値を抽出
    if "_k5_" in filename:
        k = 5
    elif "_k10_" in filename:
        k = 10
    elif "_k20_" in filename:
        k = 20
    else:
        continue
    
    # layerwiseを判定
    layerwise = "_lw_" in filename
    
    # α値を抽出
    alpha = None
    for a in alpha_values:
        if f"_a{a}_" in filename:
            alpha = a
            break
    
    if alpha is None:
        continue
    
    # 評価タイプを判定
    if "jailbreak" in filename:
        eval_type = "jb"
    elif "repliqa" in filename:
        eval_type = "repliqa"
    elif "alpaca" in filename:
        eval_type = "alpaca"
    else:
        continue
    
    # JSONファイルを読み込み
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # メトリクスを取得
        if eval_type == "jb":
            # Jailbreak resistance rate
            resistance = data["metrics"]["resistance_rate"] * 100
            results[pair][k][layerwise][alpha][eval_type] = resistance
        elif eval_type == "repliqa":
            # RepliQA ROUGE-L mean
            rougeL = data["metrics"]["rougeL"]["mean"] * 100
            results[pair][k][layerwise][alpha][eval_type] = rougeL
        elif eval_type == "alpaca":
            # Alpaca ROUGE-L mean
            rougeL = data["metrics"]["rougeL"]["mean"] * 100
            results[pair][k][layerwise][alpha][eval_type] = rougeL
    
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        continue

# テーブルを生成
def generate_table(pair, k, layerwise, utility_name):
    """指定された設定のテーブルを生成"""
    lw_str = "layerwise=True" if layerwise else "layerwise=False"
    utility_key = "repliqa" if pair == "A5_A7" else "alpaca"
    utility_display = "RepliQA" if pair == "A5_A7" else "Alpaca"
    
    print(f"\n**Data-Free SST-k{k} {lw_str}**\n")
    print(f"| α | JB Resistance  | {utility_display} |")
    print(f"| --- | --- | --- |")
    
    for alpha in alpha_values:
        if alpha in results[pair][k][layerwise]:
            data = results[pair][k][layerwise][alpha]
            jb = data.get("jb", 0.0)
            utility = data.get(utility_key, 0.0)
            print(f"| {alpha} | {jb:.2f}% | {utility:.2f}% |")
        else:
            print(f"| {alpha} | - | - |")

# メインの出力
print("# Data-Free SST-Merge 評価結果\n")
print("## A5_A7 (RepliQA)")

for k in [5, 10, 20]:
    for layerwise in [False, True]:
        generate_table("A5_A7", k, layerwise, "RepliQA")

print("\n## A6_A7 (Alpaca)")

for k in [5, 10, 20]:
    for layerwise in [False, True]:
        generate_table("A6_A7", k, layerwise, "Alpaca")
