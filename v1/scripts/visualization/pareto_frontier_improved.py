#!/usr/bin/env python3
"""
Pareto Frontier分析（改善版）
見やすさを重視して手法カテゴリ別にグラフを分割
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
import re

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_results(json_path='all_eval_results_summary.json'):
    """結果をJSONから読み込み"""
    with open(json_path) as f:
        return json.load(f)

def extract_config_from_filename(filename):
    """ファイル名から設定を抽出"""
    config = {}
    
    # k値
    k_match = re.search(r'_k(\d+)', filename)
    if k_match:
        config['k'] = int(k_match.group(1))
    else:
        config['k'] = None
    
    # layerwise
    config['layerwise'] = '_lw' in filename or '_lw_' in filename
    
    # GEVP
    config['gevp'] = 'nogevp' not in filename.lower()
    
    return config

def collect_pareto_data(results, pair_name):
    """各手法のα値ごとの性能ポイントを収集"""
    data = defaultdict(list)
    performance = defaultdict(lambda: {'jb': None, 'util': None})
    
    for r in results:
        filename = r.get('filename', '')
        if pair_name not in filename:
            continue
        
        method = r.get('method', 'Unknown')
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        
        if alpha is None or method == 'Unknown':
            continue
        
        # 設定抽出
        config = extract_config_from_filename(filename)
        k = config.get('k')
        gevp = config.get('gevp')
        lw = config.get('layerwise')
        
        # メソッド識別子
        if method == 'SST-Merge (Additive)':
            method_key = f"SST-Add k={k}"
        elif method == 'SST-Merge (Interpolation)':
            if gevp and lw:
                method_key = "SST-Interp (GEVP+LW)"
            elif gevp:
                method_key = "SST-Interp (GEVP)"
            elif lw:
                method_key = "SST-Interp (LW)"
            else:
                method_key = "SST-Interp (None)"
        else:
            method_key = method
        
        # データキー
        data_key = (method_key, alpha)
        
        # メトリクス取得
        if eval_type == 'jailbreak':
            performance[data_key]['jb'] = r.get('resistance_rate', 0)
        elif eval_type in ['repliqa', 'alpaca']:
            performance[data_key]['util'] = r.get('rouge1', 0) * 100
    
    # ペアリングされたデータを整理
    for (method_key, alpha), metrics in performance.items():
        if metrics['jb'] is not None and metrics['util'] is not None:
            data[method_key].append((metrics['jb'], metrics['util'], alpha))
    
    return data

def compute_pareto_frontier(points):
    """Pareto frontierを計算"""
    points = np.array(points)
    n = len(points)
    is_pareto = np.ones(n, dtype=bool)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                if (points[j][0] >= points[i][0] and points[j][1] >= points[i][1] and
                    (points[j][0] > points[i][0] or points[j][1] > points[i][1])):
                    is_pareto[i] = False
                    break
    
    return points[is_pareto], is_pareto

def create_separated_pareto_plots(pair_name, pareto_data, output_dir='../../docs/evaluation_results_202602'):
    """手法カテゴリ別に分割したParetoプロットを作成"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    # 手法を3つのカテゴリに分類
    baseline_methods = ['Task Arithmetic', 'TIES', 'DARE']
    sst_add_methods = [k for k in pareto_data.keys() if 'SST-Add' in k]
    sst_interp_methods = [k for k in pareto_data.keys() if 'SST-Interp' in k]
    
    # 3つのサブプロットを作成
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle(f'{pair_name} - Pareto Frontier Analysis (Category-wise)', 
                fontsize=18, fontweight='bold')
    
    categories = [
        ('Baseline Methods', baseline_methods, axes[0]),
        ('SST-Merge Additive', sst_add_methods, axes[1]),
        ('SST-Merge Interpolation', sst_interp_methods, axes[2])
    ]
    
    colors_map = {
        'Task Arithmetic': '#1f77b4',
        'TIES': '#ff7f0e',
        'DARE': '#2ca02c',
        'SST-Add k=5': '#d62728',
        'SST-Add k=10': '#9467bd',
        'SST-Add k=20': '#8c564b',
        'SST-Interp (GEVP+LW)': '#e377c2',
        'SST-Interp (GEVP)': '#7f7f7f',
        'SST-Interp (LW)': '#bcbd22',
        'SST-Interp (None)': '#17becf',
    }
    
    markers_map = {
        'Task Arithmetic': 'o',
        'TIES': 's',
        'DARE': '^',
        'SST-Add k=5': 'D',
        'SST-Add k=10': 'P',
        'SST-Add k=20': 'X',
        'SST-Interp (GEVP+LW)': 'v',
        'SST-Interp (GEVP)': '<',
        'SST-Interp (LW)': '>',
        'SST-Interp (None)': 'p',
    }
    
    for category_name, methods, ax in categories:
        for method in methods:
            if method not in pareto_data:
                continue
            
            points = pareto_data[method]
            if not points:
                continue
            
            # (jb, util, alpha) → (jb, util)
            jb_util_points = [(p[0], p[1]) for p in points]
            alphas = [p[2] for p in points]
            
            # Pareto frontierを計算
            pareto_points, is_pareto = compute_pareto_frontier(jb_util_points)
            
            # 全ポイント
            jbs = [p[0] for p in jb_util_points]
            utils = [p[1] for p in jb_util_points]
            
            color = colors_map.get(method, 'gray')
            marker = markers_map.get(method, 'o')
            
            # 全ポイント（薄く）
            ax.scatter(utils, jbs, alpha=0.2, s=50, 
                      color=color, marker=marker)
            
            # Paretoフロンティア上の点（強調）
            if len(pareto_points) > 0:
                ax.scatter(pareto_points[:, 1], pareto_points[:, 0], 
                          alpha=1.0, s=150, color=color, marker=marker,
                          label=method, edgecolors='black', linewidths=2)
                
                # Paretoフロンティアを線で接続
                if len(pareto_points) > 1:
                    sorted_idx = np.argsort(pareto_points[:, 1])
                    sorted_pareto = pareto_points[sorted_idx]
                    ax.plot(sorted_pareto[:, 1], sorted_pareto[:, 0], 
                           color=color, linestyle='--', alpha=0.7, linewidth=2.5)
        
        # 軸設定
        ax.set_xlabel(f'{util_task} ROUGE-1 (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Jailbreak Resistance (%)', fontsize=12, fontweight='bold')
        ax.set_title(category_name, fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
        ax.set_xlim(0, 105)
        ax.set_ylim(0, 105)
        
        # 理想点の参照線
        ax.axhline(y=90, color='green', linestyle=':', alpha=0.2, linewidth=1)
        ax.axvline(x=60, color='blue', linestyle=':', alpha=0.2, linewidth=1)
    
    plt.tight_layout()
    
    # 保存
    output_path = output_dir / f'{pair_name}_pareto_separated.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✓ Saved: {output_path}')
    
    plt.close()

def create_overlay_pareto_plot(pair_name, pareto_data, output_dir='../../docs/evaluation_results_202602'):
    """全手法を重ねて表示（改善版：Paretoポイントのみ）"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    colors_map = {
        'Task Arithmetic': '#1f77b4',
        'TIES': '#ff7f0e',
        'DARE': '#2ca02c',
        'SST-Add k=5': '#d62728',
        'SST-Add k=10': '#9467bd',
        'SST-Add k=20': '#8c564b',
        'SST-Interp (GEVP+LW)': '#e377c2',
        'SST-Interp (GEVP)': '#7f7f7f',
        'SST-Interp (LW)': '#bcbd22',
        'SST-Interp (None)': '#17becf',
    }
    
    markers_map = {
        'Task Arithmetic': 'o',
        'TIES': 's',
        'DARE': '^',
        'SST-Add k=5': 'D',
        'SST-Add k=10': 'P',
        'SST-Add k=20': 'X',
        'SST-Interp (GEVP+LW)': 'v',
        'SST-Interp (GEVP)': '<',
        'SST-Interp (LW)': '>',
        'SST-Interp (None)': 'p',
    }
    
    # Paretoポイントのみプロット
    for method in sorted(pareto_data.keys()):
        points = pareto_data[method]
        if not points:
            continue
        
        jb_util_points = [(p[0], p[1]) for p in points]
        pareto_points, _ = compute_pareto_frontier(jb_util_points)
        
        if len(pareto_points) > 0:
            color = colors_map.get(method, 'gray')
            marker = markers_map.get(method, 'o')
            
            ax.scatter(pareto_points[:, 1], pareto_points[:, 0], 
                      alpha=0.8, s=120, color=color, marker=marker,
                      label=method, edgecolors='black', linewidths=1.5)
            
            # 線で接続
            if len(pareto_points) > 1:
                sorted_idx = np.argsort(pareto_points[:, 1])
                sorted_pareto = pareto_points[sorted_idx]
                ax.plot(sorted_pareto[:, 1], sorted_pareto[:, 0], 
                       color=color, linestyle='--', alpha=0.5, linewidth=2)
    
    ax.set_xlabel(f'{util_task} ROUGE-1 (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Jailbreak Resistance (%)', fontsize=14, fontweight='bold')
    ax.set_title(f'{pair_name} - Pareto Frontier (Optimal Points Only)', 
                fontsize=16, fontweight='bold')
    ax.legend(loc='best', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    
    plt.tight_layout()
    
    output_path = output_dir / f'{pair_name}_pareto_overlay.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✓ Saved: {output_path}')
    
    plt.close()

def main():
    print("="*70)
    print("Pareto Frontier Analysis (Improved Visualization)")
    print("="*70)
    
    # データ読み込み
    print("\nLoading results...")
    results = load_results('all_eval_results_summary.json')
    print(f"✓ Loaded {len(results)} results")
    
    # A5_A7
    print("\nAnalyzing A5_A7...")
    data_a5_a7 = collect_pareto_data(results, 'A5_A7')
    create_separated_pareto_plots('A5_A7', data_a5_a7)
    create_overlay_pareto_plot('A5_A7', data_a5_a7)
    
    # A6_A7
    print("\nAnalyzing A6_A7...")
    data_a6_a7 = collect_pareto_data(results, 'A6_A7')
    create_separated_pareto_plots('A6_A7', data_a6_a7)
    create_overlay_pareto_plot('A6_A7', data_a6_a7)
    
    print("\n" + "="*70)
    print("✅ Improved visualization completed!")
    print("  - Separated plots: 3 categories side-by-side")
    print("  - Overlay plot: Pareto points only")
    print("="*70)

if __name__ == '__main__':
    main()
