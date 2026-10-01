#!/usr/bin/env python3
"""
SST-Merge v5 結果の可視化 (修正版)
A5_A7とA6_A7について、マージ手法とk値別のα変化グラフを作成
"""

import json
import matplotlib.pyplot as plt
import re
from pathlib import Path
from collections import defaultdict

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_results(json_path='all_eval_results_summary.json'):
    """結果をJSONから読み込み"""
    with open(json_path) as f:
        return json.load(f)

def extract_k_from_filename(filename):
    """ファイル名からk値を抽出"""
    k_match = re.search(r'_k(\d+)', filename)
    if k_match:
        return int(k_match.group(1))
    elif 'sst' in filename.lower():
        # SST-Mergeでk指定がない場合はデフォルト5
        return 5
    else:
        # Baselineメソッドはk='none'
        return 'none'

def organize_by_method_and_k(results, pair_name):
    """
    マージ手法とk値別にデータを整理
    
    Returns:
        dict: {method: {k: {alpha: {jb: ..., util: ...}}}}
    """
    organized = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    for r in results:
        # ペアフィルタ
        filename = r.get('filename', '')
        if pair_name not in filename:
            continue
        
        method = r.get('method', 'Unknown')
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        
        # k値を抽出（JSONのk値がNoneの場合はファイル名から）
        k = r.get('k')
        if k is None:
            k = extract_k_from_filename(filename)
        
        if alpha is None:
            continue
        
        #メトリクス取得
        if eval_type == 'jailbreak':
            metric = r.get('resistance_rate', 0)
            organized[method][k][alpha]['jb'] = metric
        elif eval_type in ['repliqa', 'alpaca']:
            metric = r.get('rouge1', 0) * 100
            organized[method][k][alpha]['util'] = metric
    
    return organized

def create_performance_graphs(pair_name, organized_data, output_dir='../../docs/evaluation_results_202602'):
    """
    性能グラフを作成
    
    Args:
        pair_name: 'A5_A7' or 'A6_A7'
        organized_data: organize_by_method_and_k の出力
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Utility タスク名
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    # カラーマップ
    colors = {
        'Task Arithmetic': '#1f77b4',  # 青
        'TIES': '#ff7f0e',              # オレンジ
        'DARE': '#2ca02c',              # 緑
        'SST-Merge (Additive)': '#d62728',  # 赤
        'SST-Merge (Interpolation)': '#9467bd',  # 紫
    }
    
    # k値ごとのマーカー
    markers = {
        5: 'o',
        10: 's',
        20: '^',
        'none': 'D'
    }
    
    # 2x2グラフを作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{pair_name} Performance vs Alpha', fontsize=16, fontweight='bold')
    
    # グラフ1: Jailbreak Resistance (Baseline)
    ax = axes[0, 0]
    for method in ['Task Arithmetic', 'TIES', 'DARE']:
        if method in organized_data:
            data = organized_data[method].get('none', {})
            if data:
                alphas =sorted(data.keys())
                jb_values = [data[a].get('jb', 0) for a in alphas]
                
                ax.plot(alphas, jb_values, marker='o', label=method, 
                       color=colors.get(method, 'gray'), linewidth=2, markersize=6)
    
    ax.set_xlabel('Alpha', fontsize=12)
    ax.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
    ax.set_title('Baseline Merge Methods', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 105)
    
    # グラフ2: Utility (Baseline)
    ax = axes[0, 1]
    for method in ['Task Arithmetic', 'TIES', 'DARE']:
        if method in organized_data:
            data = organized_data[method].get('none', {})
            if data:
                alphas = sorted(data.keys())
                util_values = [data[a].get('util', 0) for a in alphas]
                
                ax.plot(alphas, util_values, marker='o', label=method,
                       color=colors.get(method, 'gray'), linewidth=2, markersize=6)
    
    ax.set_xlabel('Alpha', fontsize=12)
    ax.set_ylabel(f'{util_task} ROUGE-1 (%)', fontsize=12)
    ax.set_title('Baseline Merge Methods', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    
    # グラフ3: Jailbreak Resistance (SST-Merge)
    ax = axes[1, 0]
    
    # 加算型 (k=5, 10, 20)
    if 'SST-Merge (Additive)' in organized_data:
        for k in [5, 10, 20]:
            data = organized_data['SST-Merge (Additive)'].get(k, {})
            if data:
                alphas = sorted(data.keys())
                jb_values = [data[a].get('jb', 0) for a in alphas]
                
                ax.plot(alphas, jb_values, marker=markers[k], 
                       label=f'Additive k={k}', color=colors['SST-Merge (Additive)'],
                       linewidth=2, markersize=6, alpha=0.3 + k/30)
    
    # 補間型 (k=5)
    if 'SST-Merge (Interpolation)' in organized_data:
        data = organized_data['SST-Merge (Interpolation)'].get(5, {})
        if data:
            alphas = sorted(data.keys())
            jb_values = [data[a].get('jb', 0) for a in alphas]
            
            ax.plot(alphas, jb_values, marker='o', 
                   label='Interpolation k=5', color=colors['SST-Merge (Interpolation)'],
                   linewidth=2.5, markersize=7)
    
    ax.set_xlabel('Alpha', fontsize=12)
    ax.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
    ax.set_title('SST-Merge Methods', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 105)
    
    # グラフ4: Utility (SST-Merge)
    ax = axes[1, 1]
    
    # 加算型 (k=5, 10, 20)
    if 'SST-Merge (Additive)' in organized_data:
        for k in [5, 10, 20]:
            data = organized_data['SST-Merge (Additive)'].get(k, {})
            if data:
                alphas = sorted(data.keys())
                util_values = [data[a].get('util', 0) for a in alphas]
                
                ax.plot(alphas, util_values, marker=markers[k],
                       label=f'Additive k={k}', color=colors['SST-Merge (Additive)'],
                       linewidth=2, markersize=6, alpha=0.3 + k/30)
    
    # 補間型 (k=5)
    if 'SST-Merge (Interpolation)' in organized_data:
        data = organized_data['SST-Merge (Interpolation)'].get(5, {})
        if data:
            alphas = sorted(data.keys())
            util_values = [data[a].get('util', 0) for a in alphas]
            
            ax.plot(alphas, util_values, marker='o',
                   label='Interpolation k=5', color=colors['SST-Merge (Interpolation)'],
                   linewidth=2.5, markersize=7)
    
    ax.set_xlabel('Alpha', fontsize=12)
    ax.set_ylabel(f'{util_task} ROUGE-1 (%)', fontsize=12)
    ax.set_title('SST-Merge Methods', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    
    plt.tight_layout()
    
    # 保存
    output_path = output_dir / f'{pair_name}_performance_vs_alpha.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✓ Saved: {output_path}')
    
    plt.close()

def main():
    print("="*70)
    print("SST-Merge v5 Performance Visualization (Fixed)")
    print("="*70)
    
    # データ読み込み
    print("\nLoading results...")
    results = load_results('all_eval_results_summary.json')
    print(f"✓ Loaded {len(results)} results")
    
    # A5_A7のグラフ
    print("\nCreating graphs for A5_A7...")
    data_a5_a7 = organize_by_method_and_k(results, 'A5_A7')
    
   # デバッグ: SST-Mergeのデータ確認
    if 'SST-Merge (Additive)' in data_a5_a7:
        print(f"  SST-Merge (Additive) k values: {list(data_a5_a7['SST-Merge (Additive)'].keys())}")
    if 'SST-Merge (Interpolation)' in data_a5_a7:
        print(f"  SST-Merge (Interpolation) k values: {list(data_a5_a7['SST-Merge (Interpolation)'].keys())}")
    
    create_performance_graphs('A5_A7', data_a5_a7)
    
    # A6_A7のグラフ
    print("\nCreating graphs for A6_A7...")
    data_a6_a7 = organize_by_method_and_k(results, 'A6_A7')
    
    # デバッグ: SST-Mergeのデータ確認
    if 'SST-Merge (Additive)' in data_a6_a7:
        print(f"  SST-Merge (Additive) k values: {list(data_a6_a7['SST-Merge (Additive)'].keys())}")
    if 'SST-Merge (Interpolation)' in data_a6_a7:
        print(f"  SST-Merge (Interpolation) k values: {list(data_a6_a7['SST-Merge (Interpolation)'].keys())}")
    
    create_performance_graphs('A6_A7', data_a6_a7)
    
    print("\n" + "="*70)
    print("✅ Visualization completed!")
    print("="*70)

if __name__ == '__main__':
    main()
