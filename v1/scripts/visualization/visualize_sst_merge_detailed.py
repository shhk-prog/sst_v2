#!/usr/bin/env python3
"""
SST-Merge v5 詳細可視化
k値ごと、layerwise/GEVP設定別のグラフを作成
all_eval_results_summary.jsonを読み込んで作る
# Step 1: 結果を集計
python3 scripts/analysis/collect_all_results.py
をやってから実行
# Step 2: グラフを生成（k=50 と hard maskのグラフも自動生成）
python3 scripts/visualization/visualize_sst_merge_detailed.py

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

def extract_config_from_filename(filename):
    """ファイル名からk値、layerwise、GEVP、mask_typeを抽出"""
    config = {}
    
    # k値
    k_match = re.search(r'_k(\d+)', filename)
    if k_match:
        config['k'] = int(k_match.group(1))
    elif 'sst' in filename.lower():
        config['k'] = 5
    else:
        config['k'] = 'none'
    
    # layerwise
    config['layerwise'] = '_lw' in filename or '_lw_' in filename
    
    # GEVP
    config['gevp'] = 'nogevp' not in filename.lower()
    
    # マスクタイプ (hard or soft)
    config['mask_type'] = 'hard' if ('_hard_full_' in filename or '_hard_' in filename) else 'soft'
    
    return config

def organize_detailed_data(results, pair_name):
    """
    詳細設定別にデータを整理
    
    Returns:
        dict: {method: {k: {(gevp, lw, mask_type): {alpha: {jb: ..., util: ...}}}}}
    """
    organized = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    
    for r in results:
        filename = r.get('filename', '')
        if pair_name not in filename:
            continue
        
        method = r.get('method', 'Unknown')
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        
        if alpha is None:
            continue
        
        # 設定抽出
        config = extract_config_from_filename(filename)
        k = config['k']
        gevp = config['gevp']
        lw = config['layerwise']
        mask_type = config.get('mask_type', 'soft')
        
        # メトリクス取得
        if eval_type == 'jailbreak':
            metric = r.get('resistance_rate', 0)
            organized[method][k][(gevp, lw, mask_type)][alpha]['jb'] = metric
        elif eval_type in ['repliqa', 'alpaca']:
            metric = r.get('rouge1', 0) * 100
            organized[method][k][(gevp, lw, mask_type)][alpha]['util'] = metric
    
    return organized

def organize_baseline_data(results, pair_name):
    """
    ベースライン手法のデータを整理
    
    Returns:
        dict: {method: {alpha: {jb: ..., util: ...}}}
    """
    baseline_data = defaultdict(lambda: defaultdict(dict))
    baseline_methods = ['Task Arithmetic', 'DARE', 'TIES']
    
    for r in results:
        filename = r.get('filename', '')
        if pair_name not in filename:
            continue
        
        method = r.get('method', 'Unknown')
        if method not in baseline_methods:
            continue
            
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        
        if alpha is None:
            continue
        
        # メトリクス取得 - resistance_rate is already in percentage (0-100)
        if eval_type == 'jailbreak':
            metric = r.get('resistance_rate', 0)  # Already in percentage
            baseline_data[method][alpha]['jb'] = metric
        elif eval_type in ['repliqa', 'alpaca']:
            # rouge1 is stored as a decimal (0-1), need to convert to percentage
            metric = r.get('rouge1', 0) * 100
            baseline_data[method][alpha]['util'] = metric
    
    return baseline_data

def create_baseline_graphs(pair_name, baseline_data, output_dir=None):
    """
    ベースライン手法(Task Arithmetic, DARE, TIES)のグラフを作成
    """
    if output_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        output_dir = base_dir / 'docs/evaluation_results_202602'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    # ベースライン手法のスタイル
    baseline_styles = {
        'Task Arithmetic': {'color': '#1f77b4', 'linestyle': '-', 'marker': 'o'},
        'DARE': {'color': '#ff7f0e', 'linestyle': '--', 'marker': 's'},
        'TIES': {'color': '#2ca02c', 'linestyle': '-.', 'marker': '^'},
    }
    
    # 1つのグラフですべてのベースライン手法を表示
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'{pair_name} - Baseline Merge Methods', fontsize=16, fontweight='bold')
    
    # Jailbreak Resistance
    for method, style in baseline_styles.items():
        if method in baseline_data:
            data = baseline_data[method]
            alphas = sorted(data.keys())
            jb_values = [data[a].get('jb', 0) for a in alphas]
            
            ax1.plot(alphas, jb_values, **style, linewidth=2, markersize=6, label=method)
    
    ax1.set_xlabel('Alpha', fontsize=12)
    ax1.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
    ax1.set_title('Jailbreak Resistance', fontsize=14)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1.05)
    ax1.set_ylim(0, 100)
    
    # Utility Performance
    for method, style in baseline_styles.items():
        if method in baseline_data:
            data = baseline_data[method]
            alphas = sorted(data.keys())
            util_values = [data[a].get('util', 0) for a in alphas]
            
            ax2.plot(alphas, util_values, **style, linewidth=2, markersize=6, label=method)
    
    ax2.set_xlabel('Alpha', fontsize=12)
    ax2.set_ylabel(f'{util_task} ROUGE-1 (%)', fontsize=12)
    ax2.set_title(f'{util_task} Performance', fontsize=14)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1.05)
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    output_path = output_dir / f'{pair_name}_Baseline_Methods.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'✓ Saved: {output_path}')
    plt.close()

def create_sst_merge_graphs(pair_name, organized_data, output_dir=None):
    """
    SST-Mergeの詳細グラフを作成
    """
    if output_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        output_dir = base_dir / 'docs/evaluation_results_202602'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    
    # SST-Merge設定のスタイル (GEVP x LW x mask_type)
    config_styles = {
        (True, False, 'soft'): {'color': '#9467bd', 'linestyle': '-', 'marker': 'o', 'label': 'GEVP=ON, LW=OFF, Soft'},
        (True, True, 'soft'):  {'color': '#8c564b', 'linestyle': '-', 'marker': 's', 'label': 'GEVP=ON, LW=ON, Soft'},
        (False, False, 'soft'):{'color': '#e377c2', 'linestyle': '--', 'marker': '^', 'label': 'GEVP=OFF, LW=OFF, Soft'},
        (False, True, 'soft'): {'color': '#7f7f7f', 'linestyle': '--', 'marker': 'D', 'label': 'GEVP=OFF, LW=ON, Soft'},
        (True, False, 'hard'): {'color': '#d62728', 'linestyle': '-', 'marker': 'P', 'label': 'GEVP=ON, LW=OFF, Hard'},
        (True, True, 'hard'):  {'color': '#ff7f0e', 'linestyle': '-', 'marker': 'X', 'label': 'GEVP=ON, LW=ON, Hard'},
        (False, False, 'hard'):{'color': '#17becf', 'linestyle': '--', 'marker': 'P', 'label': 'GEVP=OFF, LW=OFF, Hard'},
        (False, True, 'hard'): {'color': '#bcbd22', 'linestyle': '--', 'marker': 'X', 'label': 'GEVP=OFF, LW=ON, Hard'},
    }
    
    # SST-Merge補間型のグラフ（k=5, 10, 20, 50）
    if 'SST-Merge (Interpolation)' in organized_data:
        method = 'SST-Merge (Interpolation)'
        
        for k in [5, 10, 20, 50]:
            k_data = organized_data[method].get(k, {})
            
            if k_data:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
                fig.suptitle(f'{pair_name} - SST-Merge Interpolation (k={k})', fontsize=16, fontweight='bold')
                
                # Jailbreak
                for key, style in config_styles.items():
                    data = k_data.get(key, {})
                    if data:
                        alphas = sorted(data.keys())
                        jb_values = [data[a].get('jb', 0) for a in alphas]
                        ax1.plot(alphas, jb_values, **style, linewidth=2, markersize=6)
                
                ax1.set_xlabel('Alpha', fontsize=12)
                ax1.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
                ax1.set_title('Jailbreak Resistance', fontsize=14)
                ax1.legend(loc='best', fontsize=8)
                ax1.grid(True, alpha=0.3)
                ax1.set_xlim(0, 1.05)
                ax1.set_ylim(0, 100)
                
                # Utility
                for key, style in config_styles.items():
                    data = k_data.get(key, {})
                    if data:
                        alphas = sorted(data.keys())
                        util_values = [data[a].get('util', 0) for a in alphas]
                        ax2.plot(alphas, util_values, **style, linewidth=2, markersize=6)
                
                ax2.set_xlabel('Alpha', fontsize=12)
                ax2.set_ylabel(f'{util_task} ROUGE-1 (%)', fontsize=12)
                ax2.set_title(f'{util_task} Performance', fontsize=14)
                ax2.legend(loc='best', fontsize=8)
                ax2.grid(True, alpha=0.3)
                ax2.set_xlim(0, 1.05)
                ax2.set_ylim(0, 100)
                
                plt.tight_layout()
                output_path = output_dir / f'{pair_name}_SST_Interpolation_k{k}.png'
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                print(f'✓ Saved: {output_path}')
                plt.close()
    
    # SST-Merge加算型のグラフ (Soft と Hard を別々に; k=5, 10, 20, 50)
    for additive_method_label, additive_method_key in [
        ('Additive (Soft)', 'SST-Merge (Additive)'),
        ('Additive (Hard)', 'SST-Merge (Additive)'),  # hard mask files share same method name from collect
    ]:
        target_mask = 'hard' if 'Hard' in additive_method_label else 'soft'
        
        if additive_method_key not in organized_data:
            continue
        
        for k in [5, 10, 20, 50]:
            # Only include config_styles matching the target mask type
            relevant_styles = {key: style for key, style in config_styles.items() if key[2] == target_mask}
            k_data = organized_data[additive_method_key].get(k, {})
            # Filter k_data to only include entries matching target mask
            relevant_k_data = {key: v for key, v in k_data.items() if key[2] == target_mask}
            
            if not relevant_k_data:
                continue
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            fig.suptitle(f'{pair_name} - SST-Merge {additive_method_label} (k={k})', fontsize=16, fontweight='bold')
            
            # Jailbreak
            for key, style in relevant_styles.items():
                data = relevant_k_data.get(key, {})
                if data:
                    alphas = sorted(data.keys())
                    jb_values = [data[a].get('jb', 0) for a in alphas]
                    ax1.plot(alphas, jb_values, **style, linewidth=2, markersize=6)
            
            ax1.set_xlabel('Alpha', fontsize=12)
            ax1.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
            ax1.set_title('Jailbreak Resistance', fontsize=14)
            ax1.legend(loc='best', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, 1.05)
            ax1.set_ylim(0, 100)
            
            # Utility
            for key, style in relevant_styles.items():
                data = relevant_k_data.get(key, {})
                if data:
                    alphas = sorted(data.keys())
                    util_values = [data[a].get('util', 0) for a in alphas]
                    ax2.plot(alphas, util_values, **style, linewidth=2, markersize=6)
            
            ax2.set_xlabel('Alpha', fontsize=12)
            ax2.set_ylabel(f'{util_task} ROUGE-1 (%)', fontsize=12)
            ax2.set_title(f'{util_task} Performance', fontsize=14)
            ax2.legend(loc='best', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.set_xlim(0, 1.05)
            ax2.set_ylim(0, 100)
            
            file_label = 'Additive_Soft' if target_mask == 'soft' else 'Additive_Hard'
            plt.tight_layout()
            output_path = output_dir / f'{pair_name}_SST_{file_label}_k{k}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f'✓ Saved: {output_path}')
            plt.close()

def extract_data_free_results(results_list):
    """
    all_eval_results_summary.json から Data-Free 評価結果を抽出・整理
    
    Returns:
        dict: {pair: {method: {k: {layerwise: {alpha: {jb: float, util: float}}}}}}
              method is 'additive' or 'interpolation'
    """
    df_results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
    
    for r in results_list:
        method = r.get('method', '')
        if 'Data-Free' not in method:
            continue
            
        pair = r.get('pair')
        if not pair:
            continue
            
        m_type = 'interpolation' if 'Interpolation' in method else 'additive'
        
        k = r.get('k')
        layerwise = r.get('layerwise')
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        
        if alpha is None or k is None or layerwise is None:
            continue
            
        if eval_type == 'jailbreak':
            resistance = r.get('resistance_rate', 0)
            df_results[pair][m_type][k][layerwise][alpha]['jb'] = resistance
        elif eval_type in ['repliqa', 'alpaca']:
            rouge1 = r.get('rouge1', 0) * 100
            metric_key = 'repliqa' if eval_type == 'repliqa' else 'alpaca'
            df_results[pair][m_type][k][layerwise][alpha][metric_key] = rouge1
            
    return df_results

def create_data_free_graphs(pair_name, data_free_results, output_dir=None):
    """
    Data-Free SST-Mergeのグラフを作成 (Additive と Interpolation を分けて)
    """
    if output_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        output_dir = base_dir / 'docs/evaluation_results_202602'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    util_task = 'RepliQA' if pair_name == 'A5_A7' else 'Alpaca'
    util_metric = 'repliqa' if pair_name == 'A5_A7' else 'alpaca'
    
    # layerwiseごとのスタイル
    lw_styles = {
        False: {'color': '#2ca02c', 'linestyle': '-', 'marker': 'o', 'label': 'LW=OFF'},
        True: {'color': '#d62728', 'linestyle': '-', 'marker': 's', 'label': 'LW=ON'},
    }
    
    if pair_name not in data_free_results:
        print(f"  No data-free results for {pair_name}")
        return
    
    pair_data = data_free_results[pair_name]
    
    # Method types: additive and interpolation
    for method_type in ['additive', 'interpolation']:
        if method_type not in pair_data:
            continue
        
        method_data = pair_data[method_type]
        method_label = 'Additive' if method_type == 'additive' else 'Interpolation'
        
        # k値ごとにグラフ作成（k=5, 10, 20, 50）
        for k in [5, 10, 20, 50]:
            if k not in method_data:
                continue
            
            k_data = method_data[k]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            fig.suptitle(f'{pair_name} - Data-Free SST-Merge {method_label} (k={k})', fontsize=16, fontweight='bold')
            
            # Jailbreak
            for layerwise, style in lw_styles.items():
                if layerwise not in k_data:
                    continue
                
                data = k_data[layerwise]
                alphas = sorted(data.keys())
                jb_values = [data[a].get('jb', 0) for a in alphas]
                
                ax1.plot(alphas, jb_values, **style, linewidth=2, markersize=6)
            
            ax1.set_xlabel('Alpha', fontsize=12)
            ax1.set_ylabel('Jailbreak Resistance (%)', fontsize=12)
            ax1.set_title('Jailbreak Resistance', fontsize=14)
            ax1.legend(loc='best', fontsize=10)
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, 1.05)
            ax1.set_ylim(0, 100)
            
            # Utility
            for layerwise, style in lw_styles.items():
                if layerwise not in k_data:
                    continue
                
                data = k_data[layerwise]
                alphas = sorted(data.keys())
                util_values = [data[a].get(util_metric, 0) for a in alphas]
                
                ax2.plot(alphas, util_values, **style, linewidth=2, markersize=6)
            
            ax2.set_xlabel('Alpha', fontsize=12)
            ax2.set_ylabel(f'{util_task} ROUGE-L (%)', fontsize=12)
            ax2.set_title(f'{util_task} Performance', fontsize=14)
            ax2.legend(loc='best', fontsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.set_xlim(0, 1.05)
            ax2.set_ylim(0, 100)
            
            plt.tight_layout()
            output_path = output_dir / f'{pair_name}_DataFree_{method_label}_k{k}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f'✓ Saved: {output_path}')
            plt.close()


def main():
    print("="*70)
    
    # プロジェクトルートディレクトリを取得
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    # データ読み込み
    print("\nLoading SST-Merge results...")
    
    # 複数の候補パスを試す
    json_candidates = [
        base_dir / 'all_eval_results_summary.json',
        base_dir / 'docs/evaluation_results_202602/all_eval_results_summary.json',
    ]
    
    has_sst_results = False
    results = []
    for json_path in json_candidates:
        try:
            if json_path.exists():
                results = load_results(json_path)
                print(f"✓ Loaded {len(results)} SST-Merge results from {json_path}")
                has_sst_results = True
                break
        except Exception as e:
            print(f"Error loading {json_path}: {e}")
            continue
    
    if not has_sst_results:
        print("⚠ all_eval_results_summary.json not found, skipping SST-Merge graphs")
    
    # Data-Free結果抽出
    print("\nExtracting Data-Free results from summary JSON...")
    data_free_results = extract_data_free_results(results) if has_sst_results else defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
    n_data_free = sum(
        len(data_free_results[pair][m][k][lw])
        for pair in data_free_results
        for m in data_free_results[pair]
        for k in data_free_results[pair][m]
        for lw in data_free_results[pair][m][k]
    )
    print(f"✓ Extracted {n_data_free} Data-Free configurations")
    
    # 出力ディレクトリ
    output_dir = base_dir / 'docs/evaluation_results_202602'
    
    # A5_A7のグラフ
    if has_sst_results:
        print("\nCreating baseline graphs for A5_A7...")
        baseline_a5_a7 = organize_baseline_data(results, 'A5_A7')
        create_baseline_graphs('A5_A7', baseline_a5_a7, output_dir=output_dir)
        
        print("\nCreating detailed graphs for A5_A7...")
        data_a5_a7 = organize_detailed_data(results, 'A5_A7')
        create_sst_merge_graphs('A5_A7', data_a5_a7, output_dir=output_dir)
    
    print("\nCreating Data-Free graphs for A5_A7...")
    create_data_free_graphs('A5_A7', data_free_results, output_dir=output_dir)
    
    # A6_A7のグラフ
    if has_sst_results:
        print("\nCreating baseline graphs for A6_A7...")
        baseline_a6_a7 = organize_baseline_data(results, 'A6_A7')
        create_baseline_graphs('A6_A7', baseline_a6_a7, output_dir=output_dir)
        
        print("\nCreating detailed graphs for A6_A7...")
        data_a6_a7 = organize_detailed_data(results, 'A6_A7')
        create_sst_merge_graphs('A6_A7', data_a6_a7, output_dir=output_dir)
    
    print("\nCreating Data-Free graphs for A6_A7...")
    create_data_free_graphs('A6_A7', data_free_results, output_dir=output_dir)
    
    print("\n" + "="*70)
    print("✅ Detailed visualization completed!")
    print(f"   Generated graphs:")
    if has_sst_results:
        print(f"   - Baseline Methods (Task Arithmetic, DARE, TIES) (2 graphs)")
        print(f"   - SST-Merge Interpolation k=5, 10, 20, 50 (up to 8 graphs)")
        print(f"   - SST-Merge Additive (Soft) k=5, 10, 20, 50 (up to 8 graphs)")
        print(f"   - SST-Merge Additive (Hard) k=5, 10, 20, 50 (up to 8 graphs)")
    print(f"   - Data-Free Additive k=5, 10, 20, 50 (up to 8 graphs)")
    print(f"   - Data-Free Interpolation k=5, 10, 20, 50 (up to 8 graphs)")
    print("="*70)

if __name__ == '__main__':
    main()
