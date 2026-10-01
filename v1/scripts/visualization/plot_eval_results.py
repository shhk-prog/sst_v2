#!/usr/bin/env python3
"""
評価結果グラフ生成

merge_evalの結果からBaseline MergeとSST-Mergeのグラフを生成
"""

import json
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from collections import defaultdict
import re
import numpy as np

# 日本語フォント設定
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

def load_results(merge_eval_dir):
    """評価結果を読み込み"""
    data = defaultdict(lambda: defaultdict(lambda: {}))
    
    for json_file in Path(merge_eval_dir).glob('*.json'):
        if 'data_free' in json_file.name:
            continue
        
        try:
            with open(json_file) as f:
                j = json.load(f)
            
            fname = json_file.stem
            parts = fname.split('_')
            pair = f"{parts[0]}_{parts[1]}"
            
            # メソッド抽出
            if 'sst_k' in fname:
                k_match = re.search(r'_k(\d+)', fname)
                k = k_match.group(1) if k_match else None
                lw = True if '_lw_' in fname else False
                method = f"SST-k{k}{'_lw' if lw else ''}"
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
            alpha = float(alpha_match.group(1)) if alpha_match else None
            if alpha is None:
                continue
            
            # メトリクス取得
            metrics = j.get('metrics', {})
            if 'jailbreak' in fname:
                ds = 'JB'
                val = metrics.get('resistance_rate', 0) * 100
            elif 'repliqa' in fname:
                ds = 'RepliQA'
                rouge_l = metrics.get('rougeL', {})
                val = rouge_l.get('mean', 0) * 100 if isinstance(rouge_l, dict) else rouge_l * 100
            elif 'alpaca' in fname:
                ds = 'Alpaca'
                rouge_l = metrics.get('rougeL', {})
                val = rouge_l.get('mean', 0) * 100 if isinstance(rouge_l, dict) else rouge_l * 100
            else:
                continue
            
            data[pair][method][alpha, ds] = val
        
        except Exception as e:
            continue
    
    return data

def plot_baseline_methods(data, pair, output_dir):
    """Baseline手法のグラフ（DARE, TIES, Task Arithmetic）"""
    baseline_methods = ['DARE', 'TIES', 'Task Arithmetic']
    
    # データセット決定
    if pair == 'A5_A7':
        datasets = ['JB', 'RepliQA']
        ylabel2 = 'RepliQA ROUGE-L (%)'
    else:  # A6_A7
        datasets = ['JB', 'Alpaca']
        ylabel2 = 'Alpaca ROUGE-L (%)'
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'{pair}: Baseline Merge Methods', fontsize=14, fontweight='bold')
    
    for method in baseline_methods:
        if method not in data[pair]:
            continue
        
        alphas_jb = []
        vals_jb = []
        alphas_util = []
        vals_util = []
        
        for (alpha, ds), val in sorted(data[pair][method].items()):
            if ds == 'JB':
                alphas_jb.append(alpha)
                vals_jb.append(val)
            elif ds in datasets[1]:
                alphas_util.append(alpha)
                vals_util.append(val)
        
        # JB Resistance
        if alphas_jb:
            ax1.plot(alphas_jb, vals_jb, marker='o', label=method, linewidth=2)
        
        # Utility
        if alphas_util:
            ax2.plot(alphas_util, vals_util, marker='s', label=method, linewidth=2)
    
    # グラフ設定
    ax1.set_xlabel('Alpha (Safety Weight)', fontsize=11)
    ax1.set_ylabel('JB Resistance (Safety) (%)', fontsize=11)
    ax1.set_title('Jailbreak Resistance', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 105])
    
    ax2.set_xlabel('Alpha (Safety Weight)', fontsize=11)
    ax2.set_ylabel(ylabel2, fontsize=11)
    ax2.set_title('Utility Performance', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 105])
    
    plt.tight_layout()
    output_path = Path(output_dir) / f'{pair}_baseline_methods.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_sst_methods(data, pair, output_dir):
    """SST-Merge手法のグラフ（k=5,10,20 × layerwise）"""
    sst_configs = [
        ('SST-k5', 'k=5'),
        ('SST-k5_lw', 'k=5 LW'),
        ('SST-k10', 'k=10'),
        ('SST-k10_lw', 'k=10 LW'),
        ('SST-k20', 'k=20'),
        ('SST-k20_lw', 'k=20 LW'),
    ]
    
    # データセット決定
    if pair == 'A5_A7':
        datasets = ['JB', 'RepliQA']
        ylabel2 = 'RepliQA ROUGE-L (%)'
    else:  # A6_A7
        datasets = ['JB', 'Alpaca']
        ylabel2 = 'Alpaca ROUGE-L (%)'
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'{pair}: SST-Merge (k=5,10,20 × Layerwise)', fontsize=14, fontweight='bold')
    
    colors = plt.cm.tab10(np.linspace(0, 1, 6))
    
    for idx, (method_key, label) in enumerate(sst_configs):
        if method_key not in data[pair]:
            continue
        
        alphas_jb = []
        vals_jb = []
        alphas_util = []
        vals_util = []
        
        for (alpha, ds), val in sorted(data[pair][method_key].items()):
            if ds == 'JB':
                alphas_jb.append(alpha)
                vals_jb.append(val)
            elif ds in datasets[1]:
                alphas_util.append(alpha)
                vals_util.append(val)
        
        # JB Resistance
        marker = 'o' if '_lw' not in method_key else '^'
        linestyle = '-' if '_lw' not in method_key else '--'
        
        if alphas_jb:
            ax1.plot(alphas_jb, vals_jb, marker=marker, label=label, 
                    linewidth=2, linestyle=linestyle, color=colors[idx])
        
        # Utility
        if alphas_util:
            ax2.plot(alphas_util, vals_util, marker=marker, label=label,
                    linewidth=2, linestyle=linestyle, color=colors[idx])
    
    # グラフ設定
    ax1.set_xlabel('Alpha (Safety Weight)', fontsize=11)
    ax1.set_ylabel('JB Resistance (Safety) (%)', fontsize=11)
    ax1.set_title('Jailbreak Resistance', fontsize=12)
    ax1.legend(ncol=2, fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 105])
    
    ax2.set_xlabel('Alpha (Safety Weight)', fontsize=11)
    ax2.set_ylabel(ylabel2, fontsize=11)
    ax2.set_title('Utility Performance', fontsize=12)
    ax2.legend(ncol=2, fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 105])
    
    plt.tight_layout()
    output_path = Path(output_dir) / f'{pair}_sst_methods.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def main():
    merge_eval_dir = './merge_eval'
    output_dir = './docs/merge_eval_summary'
    
    print("Loading evaluation results...")
    data = load_results(merge_eval_dir)
    
    print("\nGenerating graphs...")
    
    # A5_A7グラフ
    plot_baseline_methods(data, 'A5_A7', output_dir)
    plot_sst_methods(data, 'A5_A7', output_dir)
    
    # A6_A7グラフ
    plot_baseline_methods(data, 'A6_A7', output_dir)
    plot_sst_methods(data, 'A6_A7', output_dir)
    
    print("\nAll graphs generated!")
    print(f"Output directory: {output_dir}")

if __name__ == '__main__':
    main()
