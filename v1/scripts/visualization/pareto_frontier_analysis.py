#!/usr/bin/env python3
"""
Pareto Frontier分析
Jailbreak耐性 vs Utility性能のトレードオフを可視化
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
    """
    各手法のα値ごとの性能ポイントを収集
    
    Returns:
        dict: {method_config: [(jb, util, alpha), ...]}
    """
    data = defaultdict(list)
    
    # α値ごとにJailbreakとUtilityをペアリング
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
    """
    Pareto frontierを計算
    
    Args:
        points: [(jb, util), ...] のリスト
    
    Returns:
        pareto_points: Paretoフロンティア上の点
        is_pareto: 各点がParetoフロンティア上かどうか
    """
    points = np.array(points)
    n = len(points)
    is_pareto = np.ones(n, dtype=bool)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # jがiをdominateするか（両方の軸で優れているか等しい、かつ少なくとも1つで厳密に優れている）
                if (points[j][0] >= points[i][0] and points[j][1] >= points[i][1] and
                    (points[j][0] > points[i][0] or points[j][1] > points[i][1])):
                    is_pareto[i] = False
                    break
    
    return points[is_pareto], is_pareto

def create_pareto_frontier_plot(pair_name, pareto_data, output_dir='../../docs/evaluation_results_202602'):
    """Pareto Frontierプロットを作成"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    # カラーマップとマーカー
    colors = {
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
    
    markers = {
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
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 各手法のデータをプロット
    pareto_frontiers = {}
    
    for method, points in sorted(pareto_data.items()):
        if not points:
            continue
        
        # (jb, util, alpha) → (jb, util) for Pareto
        jb_util_points = [(p[0], p[1]) for p in points]
        alphas = [p[2] for p in points]
        
        # Pareto frontierを計算
        pareto_points, is_pareto = compute_pareto_frontier(jb_util_points)
        pareto_frontiers[method] = pareto_points
        
        # 全ポイントをプロット（薄く）
        jbs = [p[0] for p in jb_util_points]
        utils = [p[1] for p in jb_util_points]
        
        color = colors.get(method, 'gray')
        marker = markers.get(method, 'o')
        
        ax.scatter(utils, jbs, alpha=0.3, s=30, 
                  color=color, marker=marker)
        
        # Paretoフロンティア上の点を強調
        if len(pareto_points) > 0:
            ax.scatter(pareto_points[:, 1], pareto_points[:, 0], 
                      alpha=0.8, s=100, color=color, marker=marker,
                      label=method, edgecolors='black', linewidths=1.5)
            
            # Paretoフロンティアを線で接続
            if len(pareto_points) > 1:
                # ソート（utilityでソート）
                sorted_idx = np.argsort(pareto_points[:, 1])
                sorted_pareto = pareto_points[sorted_idx]
                ax.plot(sorted_pareto[:, 1], sorted_pareto[:, 0], 
                       color=color, linestyle='--', alpha=0.5, linewidth=1.5)
        
        # α値をアノテーション（Paretoフロンティア上のみ、一部）
        for i, is_p in enumerate(is_pareto):
            if is_p and i % max(1, len(points)//3) == 0:  # 3点程度に間引き
                ax.annotate(f'α={alphas[i]:.1f}', 
                           (utils[i], jbs[i]), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=7, alpha=0.6, color=color)
    
    ax.set_xlabel(f'{util_task} ROUGE-1 (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Jailbreak Resistance (%)', fontsize=14, fontweight='bold')
    ax.set_title(f'{pair_name} - Pareto Frontier Analysis\n(Bright points = Pareto optimal)', 
                fontsize=16, fontweight='bold')
    ax.legend(loc='best', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    
    # 理想点を示す
    ax.axhline(y=100, color='green', linestyle=':', alpha=0.3, label='Ideal JB')
    ax.axvline(x=100, color='blue', linestyle=':', alpha=0.3, label='Ideal Util')
    
    plt.tight_layout()
    
    # 保存
    output_path = output_dir / f'{pair_name}_pareto_frontier.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✓ Saved: {output_path}')
    
    plt.close()
    
    return pareto_frontiers

def analyze_pareto_dominance(pareto_frontiers):
    """Pareto支配関係を分析"""
    print("\n" + "="*70)
    print("Pareto Dominance Analysis")
    print("="*70)
    
    for method, points in sorted(pareto_frontiers.items()):
        if len(points) > 0:
            avg_jb = np.mean(points[:, 0])
            avg_util = np.mean(points[:, 1])
            print(f"\n{method}:")
            print(f"  Pareto points: {len(points)}")
            print(f"  Avg JB: {avg_jb:.1f}%")
            print(f"  Avg Utility: {avg_util:.1f}%")
            print(f"  Best JB: {np.max(points[:, 0]):.1f}%")
            print(f"  Best Utility: {np.max(points[:, 1]):.1f}%")

def main():
    print("="*70)
    print("Pareto Frontier Analysis")
    print("="*70)
    
    # データ読み込み
    print("\nLoading results...")
    results = load_results('all_eval_results_summary.json')
    print(f"✓ Loaded {len(results)} results")
    
    # A5_A7のPareto分析
    print("\n" + "-"*70)
    print("Analyzing A5_A7...")
    print("-"*70)
    data_a5_a7 = collect_pareto_data(results, 'A5_A7')
    print(f"Methods found: {list(data_a5_a7.keys())}")
    pareto_a5_a7 = create_pareto_frontier_plot('A5_A7', data_a5_a7)
    analyze_pareto_dominance(pareto_a5_a7)
    
    # A6_A7のPareto分析
    print("\n" + "-"*70)
    print("Analyzing A6_A7...")
    print("-"*70)
    data_a6_a7 = collect_pareto_data(results, 'A6_A7')
    print(f"Methods found: {list(data_a6_a7.keys())}")
    pareto_a6_a7 = create_pareto_frontier_plot('A6_A7', data_a6_a7)
    analyze_pareto_dominance(pareto_a6_a7)
    
    print("\n" + "="*70)
    print("✅ Pareto Frontier Analysis completed!")
    print("="*70)

if __name__ == '__main__':
    main()
