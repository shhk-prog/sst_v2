"""
全手法の結果を比較するスクリプト

SST-Merge、ベースライン（カスタム）、ベースライン（mergekit）の結果を比較
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sst_merge_results(model_name='llama-3.1-8b'):
    """SST-Merge結果を読み込み"""
    results_dir = Path(f"results/exp1_safety_utility")
    
    # 最新の結果ファイルを取得
    result_files = list(results_dir.glob("exp1_results_*.json"))
    if not result_files:
        logger.warning(f"No SST-Merge results found in {results_dir}")
        return None
    
    latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded SST-Merge results from: {latest_file}")
    
    return {
        'method': 'SST-Merge',
        'safety': data['safety']['refusal_rate'],
        'utility': data['utility']['accuracy'],
        'safety_gain': data.get('safety_gain', 0),
        'utility_loss': data.get('utility_loss', 0),
        'safety_tax': data.get('safety_tax', 0),
        'baseline_safety': data.get('baseline_safety', 0),
        'baseline_utility': data.get('baseline_utility', 0)
    }


def load_baseline_results(model_name='llama-3.1-8b', use_mergekit=False):
    """ベースライン結果を読み込み"""
    # mergekitとカスタムで異なるディレクトリ
    if use_mergekit:
        baseline_dir = Path('results/baseline_mergekit')
        impl_suffix = ' (mergekit)'
    else:
        baseline_dir = Path('results/baseline_custom')
        impl_suffix = ''
    
    data = None
    if baseline_dir.exists():
        # ファイル名パターンを更新
        impl_type = 'mergekit' if use_mergekit else 'custom'
        baseline_files = sorted(baseline_dir.glob(f'baseline_{impl_type}_{model_name}_*.json'))
        if baseline_files:
            latest_baseline = baseline_files[-1]
            logger.info(f"Loaded baseline results from: {latest_baseline}")
            with open(latest_baseline, 'r') as f:
                data = json.load(f)
        else:
            logger.warning(f"No baseline results found for {model_name} in {baseline_dir}")
            return None
    else:
        logger.warning(f"Baseline directory not found: {baseline_dir}")
        return None
    
    if data is None:
        return None
    
    # 各手法の結果を抽出
    results = []
    
    baseline_safety = data['baseline']['safety']['refusal_rate']
    baseline_utility = data['baseline']['utility']['accuracy']
    
    # Safety Only
    if 'SafetyOnly' in data:
        results.append({
            'method': 'Safety Only',
            'safety': data['SafetyOnly']['safety']['refusal_rate'],
            'utility': data['SafetyOnly']['utility']['accuracy'],
            'safety_gain': data['SafetyOnly'].get('safety_gain', 0),
            'utility_loss': data['SafetyOnly'].get('utility_loss', 0),
            'safety_tax': data['SafetyOnly']['utility_loss'] / data['SafetyOnly']['safety_gain'] if data['SafetyOnly'].get('safety_gain', 0) > 0 else float('inf'),
            'baseline_safety': baseline_safety,
            'baseline_utility': baseline_utility
        })
    
    # Utility Only
    if 'UtilityOnly' in data:
        results.append({
            'method': 'Utility Only',
            'safety': data['UtilityOnly']['safety']['refusal_rate'],
            'utility': data['UtilityOnly']['utility']['accuracy'],
            'safety_gain': data['UtilityOnly'].get('safety_gain', 0),
            'utility_loss': data['UtilityOnly'].get('utility_loss', 0),
            'safety_tax': 0,
            'baseline_safety': baseline_safety,
            'baseline_utility': baseline_utility
        })
    
    # TIES, DARE, Task Arithmetic
    for method_name in ['TIES', 'DARE', 'TaskArithmetic']:
        if method_name in data:
            results.append({
                'method': method_name + impl_suffix,
                'safety': data[method_name]['safety']['refusal_rate'],
                'utility': data[method_name]['utility']['accuracy'],
                'safety_gain': data[method_name].get('safety_gain', 0),
                'utility_loss': data[method_name].get('utility_loss', 0),
                'safety_tax': data[method_name].get('safety_tax', 0),
                'baseline_safety': baseline_safety,
                'baseline_utility': baseline_utility
            })
    
    return results


def compare_all_methods(model_name='llama-3.1-8b'):
    """全手法の結果を比較"""
    logger.info("\n" + "="*80)
    logger.info("COMPARING ALL METHODS")
    logger.info("="*80)
    
    all_results = []
    
    # SST-Merge結果
    sst_merge = load_sst_merge_results(model_name)
    if sst_merge:
        all_results.append(sst_merge)
    
    # ベースライン結果（カスタム実装）
    baseline_custom = load_baseline_results(model_name, use_mergekit=False)
    if baseline_custom:
        all_results.extend(baseline_custom)
    
    # ベースライン結果（mergekit実装）
    baseline_mergekit = load_baseline_results(model_name, use_mergekit=True)
    if baseline_mergekit:
        all_results.extend(baseline_mergekit)
    
    if not all_results:
        logger.error("No results found to compare")
        return
    
    # DataFrameに変換
    df = pd.DataFrame(all_results)
    
    # 結果を表示
    logger.info("\n" + "="*80)
    logger.info("COMPARISON RESULTS")
    logger.info("="*80)
    
    print("\n")
    print(df.to_string(index=False))
    
    # CSVに保存
    output_dir = Path("results/comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = output_dir / f"comparison_{model_name}_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"\n✓ Comparison saved to: {csv_file}")
    
    # 可視化
    create_comparison_plots(df, output_dir, model_name, timestamp)
    
    # サマリーレポート作成
    create_summary_report(df, output_dir, model_name, timestamp)
    
    return df


def create_comparison_plots(df, output_dir, model_name, timestamp):
    """比較グラフを作成"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Safety vs Utility
    ax = axes[0, 0]
    ax.scatter(df['safety'], df['utility'], s=100)
    for i, row in df.iterrows():
        ax.annotate(row['method'], (row['safety'], row['utility']), 
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.set_xlabel('Safety (Refusal Rate)')
    ax.set_ylabel('Utility (Accuracy)')
    ax.set_title('Safety vs Utility Trade-off')
    ax.grid(True, alpha=0.3)
    
    # 2. Safety Tax比較
    ax = axes[0, 1]
    methods = df['method'].tolist()
    safety_tax = df['safety_tax'].replace([float('inf')], 100).tolist()  # infを100に置換
    ax.bar(range(len(methods)), safety_tax)
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.set_ylabel('Safety Tax')
    ax.set_title('Safety Tax Comparison (Lower is Better)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Safety Gain vs Utility Loss
    ax = axes[1, 0]
    ax.scatter(df['safety_gain'], df['utility_loss'], s=100)
    for i, row in df.iterrows():
        ax.annotate(row['method'], (row['safety_gain'], row['utility_loss']), 
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.set_xlabel('Safety Gain')
    ax.set_ylabel('Utility Loss')
    ax.set_title('Safety Gain vs Utility Loss')
    ax.grid(True, alpha=0.3)
    
    # 4. 総合スコア
    ax = axes[1, 1]
    # 総合スコア = Safety + Utility - Safety Tax (正規化)
    df['total_score'] = df['safety'] + df['utility'] - (df['safety_tax'].replace([float('inf')], 10) / 10)
    ax.barh(range(len(methods)), df['total_score'])
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods)
    ax.set_xlabel('Total Score (Higher is Better)')
    ax.set_title('Overall Performance')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    plot_file = output_dir / f"comparison_{model_name}_{timestamp}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Comparison plots saved to: {plot_file}")
    plt.close()


def create_summary_report(df, output_dir, model_name, timestamp):
    """サマリーレポートを作成"""
    report_file = output_dir / f"comparison_report_{model_name}_{timestamp}.md"
    
    with open(report_file, 'w') as f:
        f.write(f"# 全手法比較レポート\n\n")
        f.write(f"**モデル**: {model_name}\n")
        f.write(f"**日時**: {timestamp}\n\n")
        
        f.write("## 比較結果\n\n")
        f.write("| Method | Safety | Utility | Safety Gain | Utility Loss | Safety Tax |\n")
        f.write("|--------|--------|---------|-------------|--------------|------------|\n")
        
        for _, row in df.iterrows():
            safety_tax_str = f"{row['safety_tax']:.4f}" if row['safety_tax'] != float('inf') else "∞"
            f.write(f"| {row['method']} | {row['safety']:.4f} | {row['utility']:.4f} | "
                   f"{row['safety_gain']:.4f} | {row['utility_loss']:.4f} | {safety_tax_str} |\n")
        
        f.write("\n## 分析\n\n")
        
        # 最良のSafety Tax
        best_tax = df[df['safety_tax'] != float('inf')]['safety_tax'].min()
        best_tax_method = df[df['safety_tax'] == best_tax]['method'].values[0]
        f.write(f"**最良のSafety Tax**: {best_tax_method} ({best_tax:.4f})\n\n")
        
        # 最高のSafety
        best_safety = df['safety'].max()
        best_safety_method = df[df['safety'] == best_safety]['method'].values[0]
        f.write(f"**最高のSafety**: {best_safety_method} ({best_safety:.4f})\n\n")
        
        # 最高のUtility
        best_utility = df['utility'].max()
        best_utility_method = df[df['utility'] == best_utility]['method'].values[0]
        f.write(f"**最高のUtility**: {best_utility_method} ({best_utility:.4f})\n\n")
        
        f.write("## 結論\n\n")
        f.write("SST-Mergeは、Safety TaxとSafety/Utilityのバランスにおいて、\n")
        f.write("ベースライン手法と比較してどのような性能を示すかを評価しました。\n")
    
    logger.info(f"✓ Summary report saved to: {report_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama-3.1-8b')
    args = parser.parse_args()
    
    compare_all_methods(args.model)


if __name__ == '__main__':
    main()
