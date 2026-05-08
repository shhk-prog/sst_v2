#!/usr/bin/env python3
"""
評価結果を分析し、加算型と補間型のマージ結果を比較するスクリプト
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def load_eval_results(file_path: str) -> Dict:
    """評価結果JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_metrics(results: Dict) -> Dict[str, float]:
    """評価結果から主要メトリクスを抽出"""
    metrics_data = {}
    
    # metricsキーがある場合はそこからデータを取得
    if 'metrics' in results:
        metrics = results['metrics']
    else:
        metrics = results
    
    # Jailbreak評価の場合
    if 'resistance_rate' in metrics:
        metrics_data['refusal_rate'] = metrics['resistance_rate']
    elif 'attack_success_rate' in metrics:
        metrics_data['refusal_rate'] = 1.0 - metrics['attack_success_rate']
    
    # Utility評価の場合 (RepliQA, Alpaca)
    if 'rougeL' in metrics:
        if isinstance(metrics['rougeL'], dict):
            metrics_data['rougeL'] = metrics['rougeL']['mean']
        else:
            metrics_data['rougeL'] = metrics['rougeL']
    
    if 'rouge1' in metrics:
        if isinstance(metrics['rouge1'], dict):
            metrics_data['rouge1'] = metrics['rouge1']['mean']
        else:
            metrics_data['rouge1'] = metrics['rouge1']
    
    if 'rouge2' in metrics:
        if isinstance(metrics['rouge2'], dict):
            metrics_data['rouge2'] = metrics['rouge2']['mean']
        else:
            metrics_data['rouge2'] = metrics['rouge2']
    
    if 'bleu' in metrics:
        if isinstance(metrics['bleu'], dict):
            metrics_data['bleu'] = metrics['bleu']['mean']
        else:
            metrics_data['bleu'] = metrics['bleu']
    
    if 'exact_match' in metrics:
        if isinstance(metrics['exact_match'], dict):
            metrics_data['exact_match'] = metrics['exact_match']['mean']
        else:
            metrics_data['exact_match'] = metrics['exact_match']
    
    # GSM8K評価の場合
    if 'strict_accuracy' in metrics:
        metrics_data['strict_accuracy'] = metrics['strict_accuracy']
    
    return metrics_data


def parse_model_name(filename: str) -> Dict[str, any]:
    """ファイル名からモデル設定を解析"""
    parts = filename.replace('.json', '').split('_')
    
    info = {
        'model_type': None,  # 'base', 'utility', 'safety', 'merged'
        'merge_type': None,  # 'data_free', 'interpolation' など
        'alpha': None,
        'k': None,
        'layerwise': False,
        'topk': None,
        'eval_type': None,  # 'jailbreak', 'repliqa', 'alpaca', 'gsm8k'
    }
    
    # ベースモデル
    if 'BASE_MODEL' in filename:
        info['model_type'] = 'base'
    # マージモデル（Utilityアダプター判定より前に判定する必要がある）
    elif 'data_free' in filename or 'sst_interp' in filename or 'interp' in filename:
        info['model_type'] = 'merged'
        
        # マージタイプの判定
        if 'sst_interp' in filename or 'interp' in filename:
            info['merge_type'] = 'interpolation'
        elif 'data_free' in filename:
            info['merge_type'] = 'data_free'
        
        # パラメータ抽出
        for i, part in enumerate(parts):
            if part.startswith('k') and len(part) > 1:
                try:
                    info['k'] = int(part[1:])
                except ValueError:
                    pass
            elif part.startswith('a') and len(part) > 1:
                try:
                    info['alpha'] = float(part[1:])
                except ValueError:
                    pass
            elif part == 'lw':
                info['layerwise'] = True
            elif part.startswith('topk'):
                try:
                    info['topk'] = int(part[4:])
                except ValueError:
                    pass
    # Utilityアダプター
    elif filename.startswith('A5_') or filename.startswith('A6_') or filename.startswith('A8_'):
        info['model_type'] = 'utility'
    # Safetyアダプター
    elif filename.startswith('A7_'):
        info['model_type'] = 'safety'
    
    # 評価タイプ
    if 'jailbreak_eval' in filename:
        info['eval_type'] = 'jailbreak'
    elif 'repliqa_eval' in filename:
        info['eval_type'] = 'repliqa'
    elif 'alpaca_eval' in filename:
        info['eval_type'] = 'alpaca'
    elif 'gsm8k_eval' in filename:
        info['eval_type'] = 'gsm8k'
    
    return info


def collect_all_results(eval_dir: str) -> pd.DataFrame:
    """すべての評価結果を収集してDataFrameに変換"""
    all_results = []
    
    eval_path = Path(eval_dir)
    
    # すべてのJSONファイルを探索
    for json_file in eval_path.rglob('*_eval_results.json'):
        try:
            results = load_eval_results(str(json_file))
            metrics = extract_metrics(results)
            info = parse_model_name(json_file.name)
            
            # メトリクスと設定情報を結合
            row = {**info, **metrics, 'file_path': str(json_file)}
            all_results.append(row)
        except Exception as e:
            print(f"Warning: Failed to process {json_file}: {e}")
    
    df = pd.DataFrame(all_results)
    return df


def compare_additive_vs_interpolation(df: pd.DataFrame) -> pd.DataFrame:
    """加算型と補間型の比較分析"""
    # マージモデルのみをフィルタ
    merged_df = df[df['model_type'] == 'merged'].copy()
    
    # layerwise=Falseのみを比較（シンプルにするため）
    merged_df = merged_df[merged_df['layerwise'] == False]
    
    # 加算型と補間型を分ける
    additive = merged_df[merged_df['merge_type'] == 'data_free']
    interp = merged_df[merged_df['merge_type'] == 'interpolation']
    
    return additive, interp


def plot_alpha_sweep(additive: pd.DataFrame, interp: pd.DataFrame, output_dir: str):
    """αの変化に対するメトリクスの変化をプロット"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Jailbreak ResistanceとUtilityの関係
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # プロット1: α vs Refusal Rate (JB Resistance)
    for eval_type in ['jailbreak']:
        add_jb = additive[additive['eval_type'] == eval_type].sort_values('alpha')
        int_jb = interp[interp['eval_type'] == eval_type].sort_values('alpha')
        
        if len(add_jb) > 0:
            axes[0].plot(add_jb['alpha'], add_jb['refusal_rate'], 
                        marker='o', label='Additive', linewidth=2)
        if len(int_jb) > 0:
            axes[0].plot(int_jb['alpha'], int_jb['refusal_rate'], 
                        marker='s', label='Interpolation', linewidth=2)
    
    axes[0].set_xlabel('Safety Weight (α)', fontsize=12)
    axes[0].set_ylabel('Refusal Rate', fontsize=12)
    axes[0].set_title('Jailbreak Resistance vs α', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # プロット2: α vs RougeL (Utility)
    for eval_type in ['repliqa', 'alpaca']:
        add_util = additive[additive['eval_type'] == eval_type].sort_values('alpha')
        int_util = interp[interp['eval_type'] == eval_type].sort_values('alpha')
        
        if len(add_util) > 0 and 'rougeL' in add_util.columns:
            axes[1].plot(add_util['alpha'], add_util['rougeL'], 
                        marker='o', label=f'Additive ({eval_type})', linewidth=2)
        if len(int_util) > 0 and 'rougeL' in int_util.columns:
            axes[1].plot(int_util['alpha'], int_util['rougeL'], 
                        marker='s', label=f'Interpolation ({eval_type})', linewidth=2)
    
    axes[1].set_xlabel('Safety Weight (α)', fontsize=12)
    axes[1].set_ylabel('RougeL Score', fontsize=12)
    axes[1].set_title('Utility vs α', fontsize=14)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'alpha_sweep_comparison.png'), dpi=300)
    print(f"Saved plot: {os.path.join(output_dir, 'alpha_sweep_comparison.png')}")
    plt.close()


def plot_tradeoff(additive: pd.DataFrame, interp: pd.DataFrame, output_dir: str):
    """Safety vs Utilityのトレードオフをプロット"""
    # Jailbreak結果とUtility結果をマージ
    def merge_jb_util(df, eval_type='repliqa'):
        jb = df[df['eval_type'] == 'jailbreak'][['alpha', 'k', 'refusal_rate']].copy()
        util = df[df['eval_type'] == eval_type][['alpha', 'k', 'rougeL']].copy()
        
        merged = pd.merge(jb, util, on=['alpha', 'k'], how='inner')
        return merged
    
    add_merged = merge_jb_util(additive)
    int_merged = merge_jb_util(interp)
    
    plt.figure(figsize=(10, 6))
    
    if len(add_merged) > 0:
        plt.scatter(add_merged['refusal_rate'], add_merged['rougeL'], 
                   s=100, alpha=0.6, label='Additive', marker='o')
    
    if len(int_merged) > 0:
        plt.scatter(int_merged['refusal_rate'], int_merged['rougeL'], 
                   s=100, alpha=0.6, label='Interpolation', marker='s')
    
    plt.xlabel('Jailbreak Refusal Rate (Safety)', fontsize=12)
    plt.ylabel('RougeL Score (Utility)', fontsize=12)
    plt.title('Safety vs Utility Tradeoff', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'safety_utility_tradeoff.png'), dpi=300)
    print(f"Saved plot: {os.path.join(output_dir, 'safety_utility_tradeoff.png')}")
    plt.close()


def generate_summary_table(df: pd.DataFrame, output_dir: str):
    """サマリーテーブルを生成"""
    # マージモデルのみ
    merged_df = df[df['model_type'] == 'merged'].copy()
    
    if len(merged_df) == 0:
        print("\nNo merged models found for summary table")
        return
    
    # α=0.1付近での比較
    alpha_range = (0.05, 0.15)
    subset = merged_df[
        (merged_df['alpha'] >= alpha_range[0]) & 
        (merged_df['alpha'] <= alpha_range[1])
    ]
    
    if len(subset) == 0:
        print(f"\nNo data in alpha range {alpha_range} for summary table")
        return
    
    # 存在するカラムのみをaggregateする
    agg_dict = {}
    for col in ['refusal_rate', 'rougeL', 'rouge1', 'rouge2', 'bleu', 'exact_match']:
        if col in subset.columns and subset[col].notna().any():
            agg_dict[col] = 'mean'
    
    if not agg_dict:
        print("\nNo valid metrics found for aggregation")
        return
    
    # グループ化して平均を計算
    summary = subset.groupby(['merge_type', 'eval_type']).agg(agg_dict).round(4)
    
    print("\n=== Summary Table (α ∈ [0.05, 0.15]) ===")
    print(summary)
    
    # CSVに保存
    summary.to_csv(os.path.join(output_dir, 'summary_table.csv'))
    print(f"\nSaved summary table: {os.path.join(output_dir, 'summary_table.csv')}")


def main():
    # 設定
    eval_dir = '/mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v5/eval'
    output_dir = '/mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v5/results/analysis'
    
    print("=== Collecting evaluation results ===")
    df = collect_all_results(eval_dir)
    print(f"Collected {len(df)} evaluation results")
    
    # 全結果をCSVに保存
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, 'all_results.csv'), index=False)
    print(f"Saved all results: {os.path.join(output_dir, 'all_results.csv')}")
    
    # 加算型と補間型を比較
    print("\n=== Comparing Additive vs Interpolation ===")
    additive, interp = compare_additive_vs_interpolation(df)
    
    print(f"Additive models: {len(additive)}")
    print(f"Interpolation models: {len(interp)}")
    
    # プロット生成
    if len(additive) > 0 or len(interp) > 0:
        print("\n=== Generating plots ===")
        plot_alpha_sweep(additive, interp, output_dir)
        plot_tradeoff(additive, interp, output_dir)
    
    # サマリーテーブル生成
    generate_summary_table(df, output_dir)
    
    print("\n=== Analysis complete ===")


if __name__ == '__main__':
    main()
