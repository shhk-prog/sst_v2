#!/usr/bin/env python3
"""
SST-Merge v5 全実験結果の集計スクリプト
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import re

def extract_model_info(filename):
    """ファイル名からモデル情報を抽出"""
    # A5_A7_sst_k5_nogevp_a1.0_jailbreak_eval_results.json
    parts = {}
    
    # アダプターペア
    if 'A5_A7' in filename:
        parts['pair'] = 'A5_A7'
        parts['utility'] = 'RepliQA'
    elif 'A6_A7' in filename:
        parts['pair'] = 'A6_A7'
        parts['utility'] = 'Alpaca'
    
    # マージ手法 - Check baselines first to prevent being overridden
    if 'task_arithmetic' in filename:
        parts['method'] = 'Task Arithmetic'
    elif 'ties' in filename:
        parts['method'] = 'TIES'
    elif 'dare' in filename:
        parts['method'] = 'DARE'
    elif 'data_free' in filename:
        # Data-Free check
        if 'interp' in filename:
            parts['method'] = 'SST-Merge (Data-Free Interpolation)'
        else:
            parts['method'] = 'SST-Merge (Data-Free Additive)'
    elif 'sst' in filename:
        # Standard SST check
        if 'interp' in filename:
            parts['method'] = 'SST-Merge (Interpolation)'
        else:
            parts['method'] = 'SST-Merge (Additive)'
    elif 'A5_utility' in filename or 'A6_utility' in filename:
        parts['method'] = 'Utility Adapter'
    elif 'A7_safety' in filename:
        parts['method'] = 'Safety Adapter'
    elif 'base' in filename.lower():
        parts['method'] = 'Base Model'
    else:
        parts['method'] = 'Unknown'
    
    # α値
    alpha_match = re.search(r'_a([\d.]+)', filename)
    if alpha_match:
        parts['alpha'] = float(alpha_match.group(1))
    
    # k値 (k=5, 10, 20, 50 をサポート)
    k_match = re.search(r'_k(\d+)', filename)
    topk_match = re.search(r'_topk(\d+)', filename)
    
    if k_match:
        parts['k'] = int(k_match.group(1))
    elif topk_match:
         parts['k'] = int(topk_match.group(1))
    elif 'sst' in filename.lower() or 'data_free' in filename.lower():
        # デフォルト値（もしファイル名にない場合）
        parts['k'] = 5
    
    # マスクタイプ (hard or soft)
    if '_hard_full_' in filename or '_hard_' in filename:
        parts['mask_type'] = 'hard'
    else:
        parts['mask_type'] = 'soft'
        
    # GEVP
    if 'nogevp' in filename:
        parts['gevp'] = False
    elif 'sst' in filename:
        # SST系でnogevp指定がなければGEVP有効
        parts['gevp'] = True
    else:
        parts['gevp'] = False
    
    # Layer-wise
    if '_lw' in filename:
        parts['layerwise'] = True
    else:
        parts['layerwise'] = False
    
    # 評価タイプ
    if 'jailbreak' in filename:
        parts['eval_type'] = 'jailbreak'
    elif 'alpaca' in filename:
        parts['eval_type'] = 'alpaca'
    elif 'repliqa' in filename:
        parts['eval_type'] = 'repliqa'
    
    return parts

def load_eval_result(filepath):
    """評価結果JSONを読み込む"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def extract_metrics(data, eval_type):
    """評価結果から主要メトリクスを抽出"""
    metrics = {}
    
    if eval_type == 'jailbreak':
        if 'metrics' in data:
            metrics['resistance_rate'] = data['metrics'].get('resistance_rate', 0) * 100
            metrics['asr'] = data['metrics'].get('attack_success_rate', 0) * 100
        elif 'resistance_rate' in data:
            metrics['resistance_rate'] = data.get('resistance_rate', 0) * 100
            metrics['asr'] = data.get('attack_success_rate', 0) * 100
    
    elif eval_type in ['alpaca', 'repliqa']:
        if 'metrics' in data:
            metrics['rouge1'] = data['metrics'].get('rouge1', {}).get('mean', 0)
            metrics['rouge2'] = data['metrics'].get('rouge2', {}).get('mean', 0)
            metrics['rougeL'] = data['metrics'].get('rougeL', {}).get('mean', 0)
    
    return metrics

def main():
    # スクリプトの位置から相対パスで指定
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent.parent
    
    # 評価ディレクトリ
    eval_dirs = {
        'base': 'eval/finetuned',
        'baseline': 'eval/merged/baseline',
        'additive': 'eval/merged/sst_merge',
        'interpolation': 'eval/merged/interpolation',
        'data_free': 'eval/merged/data_free',
    }
    
    # 全結果を格納
    all_results = []
    
    # 各ディレクトリから結果を収集
    for category, dirname in eval_dirs.items():
        eval_dir = base_dir / dirname
        if not eval_dir.exists():
            print(f"Directory not found: {eval_dir}")
            continue
        
        for json_file in eval_dir.rglob('*.json'):
            # Skip files from A7-7ep directory (contains duplicates)
            if 'A7-7ep' in str(json_file):
                continue
                
            info = extract_model_info(json_file.name)
            if not info or 'eval_type' not in info:
                continue
            
            data = load_eval_result(json_file)
            if not data:
                continue
            
            metrics = extract_metrics(data, info['eval_type'])
            
            result = {
                'category': category,
                'filename': json_file.name,
                **info,
                **metrics
            }
            
            all_results.append(result)
    
    # 結果を整理
    print(f"Total results collected: {len(all_results)}")
    
    # カテゴリごとに集計
    by_category = defaultdict(list)
    for r in all_results:
        by_category[r['category']].append(r)
    
    print("\n" + "="*80)
    print("Results by Category:")
    for cat, results in by_category.items():
        print(f"  {cat}: {len(results)} results")
    print("="*80)
    
    # JSONとして保存
    output_file = 'all_eval_results_summary.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nSaved all results to: {output_file}")
    
    # 主要な結果をマークダウン形式で生成
    generate_markdown_summary(all_results)

def generate_markdown_summary(all_results):
    """マークダウン形式のサマリーを生成"""
    
    # α=1.0の結果を抽出（比較用）
    alpha_1_results = [r for r in all_results if r.get('alpha') == 1.0 or r.get('method') in ['Utility Adapter', 'Safety Adapter']]
    
    # A6_A7ペアでグループ化
    a6_a7_results = [r for r in alpha_1_results if r.get('pair') == 'A6_A7']
    
    md_lines = []
    md_lines.append("# SST-Merge v5 実験結果サマリー\n")
    md_lines.append(f"**総評価結果数**: {len(all_results)}\n")
    md_lines.append("## 主要な結果（A6_A7ペア、α=1.0）\n")
    
    # Jailbreak結果のテーブル
    md_lines.append("### Jailbreak耐性\n")
    md_lines.append("| 手法 | GEVP | Layer-wise | Resistance Rate | ASR |")
    md_lines.append("|------|------|------------|-----------------|-----|")
    
    jailbreak_results = [r for r in a6_a7_results if r.get('eval_type') == 'jailbreak']
    
    # ソート: method, gevp, layerwise
    jailbreak_results.sort(key=lambda x: (
        x.get('method', ''),
        not x.get('gevp', False),
        not x.get('layerwise', False)
    ))
    
    for r in jailbreak_results:
        method = r.get('method', 'Unknown')
        gevp = '✓' if r.get('gevp') else '✗'
        layerwise = '✓' if r.get('layerwise') else '✗'
        resistance = r.get('resistance_rate', 0)
        asr = r.get('asr', 0)
        
        md_lines.append(f"| {method} | {gevp} | {layerwise} | {resistance:.1f}% | {asr:.1f}% |")
    
    # Alpaca結果のテーブル
    md_lines.append("\n### Alpaca性能\n")
    md_lines.append("| 手法 | GEVP | Layer-wise | ROUGE-1 | ROUGE-2 | ROUGE-L |")
    md_lines.append("|------|------|------------|---------|---------|---------|")
    
    alpaca_results = [r for r in a6_a7_results if r.get('eval_type') == 'alpaca']
    alpaca_results.sort(key=lambda x: (
        x.get('method', ''),
        not x.get('gevp', False),
        not x.get('layerwise', False)
    ))
    
    for r in alpaca_results:
        method = r.get('method', 'Unknown')
        gevp = '✓' if r.get('gevp') else '✗'
        layerwise = '✓' if r.get('layerwise') else '✗'
        rouge1 = r.get('rouge1', 0)
        rouge2 = r.get('rouge2', 0)
        rougeL = r.get('rougeL', 0)
        
        md_lines.append(f"| {method} | {gevp} | {layerwise} | {rouge1:.4f} | {rouge2:.4f} | {rougeL:.4f} |")
    
    # ファイルに保存
    with open('experiment_summary.md', 'w') as f:
        f.write('\n'.join(md_lines))
    
    print("\nSaved markdown summary to: experiment_summary.md")

if __name__ == '__main__':
    main()
