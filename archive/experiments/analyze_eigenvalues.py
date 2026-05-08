#!/usr/bin/env python3
"""
固有値スペクトル分析スクリプト

Usage:
    python3 experiments/analyze_eigenvalues.py \
        --input results/eigenvalues/A5_A7_eigenvalues_utility.pt \
        --output results/eigenvalues/
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import logging
import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUIなし環境用

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def plot_eigenvalue_spectrum(eigenvalues, output_path):
    """固有値スペクトルをプロット"""
    eigenvalues_np = eigenvalues.cpu().numpy() if torch.is_tensor(eigenvalues) else eigenvalues
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # 固有値プロット（線形スケール）
    ax1.plot(range(1, len(eigenvalues_np)+1), eigenvalues_np, 'b-', linewidth=2)
    ax1.set_xlabel('Index', fontsize=12)
    ax1.set_ylabel('Eigenvalue', fontsize=12)
    ax1.set_title('Eigenvalue Spectrum (Linear Scale)', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # 固有値プロット（対数スケール）
    ax2.plot(range(1, len(eigenvalues_np)+1), eigenvalues_np, 'r-', linewidth=2)
    ax2.set_xlabel('Index', fontsize=12)
    ax2.set_ylabel('Eigenvalue (log scale)', fontsize=12)
    ax2.set_title('Eigenvalue Spectrum (Log Scale)', fontsize=14)
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✓ Spectrum plot saved to: {output_path}")


def plot_cumulative_variance(eigenvalues, output_path):
    """累積寄与率をプロット"""
    eigenvalues_np = eigenvalues.cpu().numpy() if torch.is_tensor(eigenvalues) else eigenvalues
    
    cumsum = np.cumsum(eigenvalues_np)
    total = cumsum[-1]
    cumulative_ratio = cumsum / total
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(range(1, len(cumulative_ratio)+1), cumulative_ratio * 100, 'g-', linewidth=2)
    ax.axhline(y=90, color='r', linestyle='--', label='90% threshold')
    ax.axhline(y=95, color='orange', linestyle='--', label='95% threshold')
    ax.set_xlabel('Number of Components (k)', fontsize=12)
    ax.set_ylabel('Cumulative Variance Explained (%)', fontsize=12)
    ax.set_title('Cumulative Variance Ratio', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✓ Cumulative variance plot saved to: {output_path}")
    
    return cumulative_ratio


def find_elbow_point(eigenvalues, method='variance_ratio'):
    """Elbow法で最適なkを特定"""
    eigenvalues_np = eigenvalues.cpu().numpy() if torch.is_tensor(eigenvalues) else eigenvalues
    
    if method == 'variance_ratio':
        # 累積寄与率が90%になる点
        cumsum = np.cumsum(eigenvalues_np)
        total = cumsum[-1]
        threshold = 0.9 * total
        k_90 = np.argmax(cumsum >= threshold) + 1
        
        threshold_95 = 0.95 * total
        k_95 = np.argmax(cumsum >= threshold_95) + 1
        
        return {'k_90': k_90, 'k_95': k_95}
    
    elif method == 'gap':
        # 固有値の差分が最大になる点
        diffs = np.diff(eigenvalues_np)
        k_gap = np.argmax(np.abs(diffs)) + 1
        return {'k_gap': k_gap}
    
    elif method == 'ratio':
        # 固有値の比率が閾値を下回る点
        ratios = eigenvalues_np[1:] / eigenvalues_np[:-1]
        k_ratio = np.argmax(ratios > 0.95) + 1  # 95%以上維持される点
        return {'k_ratio': k_ratio}


def main():
    parser = argparse.ArgumentParser(description='Analyze FIM eigenvalues')
    parser.add_argument('--input', type=str, required=False,
                        help='Input eigenvalue file (.pt) or "all" to analyze all files in directory')
    parser.add_argument('--input_dir', type=str, default='results/eigenvalues',
                        help='Input directory containing eigenvalue files (used with --input all)')
    parser.add_argument('--output', type=str, default='results/eigenvalues/',
                        help='Output directory for plots')
    args = parser.parse_args()
    
    # タイムスタンプ付き出力ディレクトリを作成
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_base = Path(args.output) / f'analysis_{timestamp}'
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 'all'が指定された場合、ディレクトリ内の全ファイルを分析
    if args.input and args.input.lower() == 'all':
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH EIGENVALUE SPECTRUM ANALYSIS")
        logger.info(f"{'='*80}")
        logger.info(f"Input directory: {args.input_dir}")
        logger.info(f"Output directory: {output_base}")
        
        # 最新のタイムスタンプディレクトリを探す（analysis_で始まるものは除外）
        eigenvalue_dir = Path(args.input_dir)
        subdirs = [d for d in eigenvalue_dir.iterdir() 
                   if d.is_dir() and not d.name.startswith('analysis_')]
        if subdirs:
            # 最新のディレクトリを使用
            latest_dir = max(subdirs, key=lambda d: d.name)
            logger.info(f"Using latest eigenvalue directory: {latest_dir}")
            input_files = list(latest_dir.glob('*.pt'))
        else:
            # ルートディレクトリから直接検索
            input_files = list(eigenvalue_dir.glob('*.pt'))
        
        if not input_files:
            logger.error(f"No .pt files found in {args.input_dir}")
            return
        
        logger.info(f"Found {len(input_files)} eigenvalue files")
        
        # 各ファイルを分析
        for input_file in sorted(input_files):
            logger.info(f"\n{'='*80}")
            logger.info(f"Analyzing: {input_file.name}")
            logger.info(f"{'='*80}")
            
            analyze_single_file(input_file, output_base)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH ANALYSIS COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"Results saved to: {output_base}")
        
    else:
        # 単一ファイル分析
        if not args.input:
            logger.error("--input is required (specify a file path or 'all')")
            return
        
        input_file = Path(args.input)
        analyze_single_file(input_file, output_base)


def analyze_single_file(input_path, output_dir):
    """単一の固有値ファイルを分析"""
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_dir}")
    
    # 固有値データを読み込み
    logger.info("\nLoading eigenvalues...")
    data = torch.load(input_path, map_location='cpu')
    eigenvalues = data['eigenvalues']
    num_params = data.get('num_params', len(eigenvalues))
    max_samples = data.get('max_samples', 'unknown')
    
    logger.info(f"✓ Loaded {len(eigenvalues)} eigenvalues")
    logger.info(f"  Max samples: {max_samples}")
    logger.info(f"  Number of parameters: {num_params}")
    logger.info(f"  Top 10 eigenvalues: {eigenvalues[:10].tolist()}")
    
    # ファイル名のベース
    base_name = input_path.stem
    
    # スペクトルをプロット
    logger.info("\nPlotting eigenvalue spectrum...")
    plot_eigenvalue_spectrum(
        eigenvalues,
        output_dir / f'{base_name}_spectrum.png'
    )
    
    # 累積寄与率をプロット
    logger.info("\nPlotting cumulative variance...")
    cumulative_ratio = plot_cumulative_variance(
        eigenvalues,
        output_dir / f'{base_name}_cumulative.png'
    )
    
    # Elbow法で最適なkを特定
    logger.info("\nFinding optimal k using Elbow method...")
    
    # 分散寄与率法
    k_variance = find_elbow_point(eigenvalues, method='variance_ratio')
    logger.info(f"  Variance Ratio method:")
    logger.info(f"    k (90% variance): {k_variance['k_90']}")
    logger.info(f"    k (95% variance): {k_variance['k_95']}")
    
    # Gap法
    k_gap = find_elbow_point(eigenvalues, method='gap')
    logger.info(f"  Gap method:")
    logger.info(f"    k (max gap): {k_gap['k_gap']}")
    
    # Ratio法
    k_ratio = find_elbow_point(eigenvalues, method='ratio')
    logger.info(f"  Ratio method:")
    logger.info(f"    k (ratio threshold): {k_ratio['k_ratio']}")
    
    # 推奨k値
    k_recommended = k_variance['k_90']
    logger.info(f"\n✓ Recommended k value: {k_recommended} (90% variance)")
    
    # 結果をテキストファイルに保存
    results_file = output_dir / f'{base_name}_analysis.txt'
    with open(results_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("EIGENVALUE SPECTRUM ANALYSIS RESULTS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Input file: {input_path}\n")
        f.write(f"Number of eigenvalues: {len(eigenvalues)}\n")
        f.write(f"Max samples: {max_samples}\n\n")
        
        f.write("Optimal k values:\n")
        f.write(f"  k (90% variance): {k_variance['k_90']}\n")
        f.write(f"  k (95% variance): {k_variance['k_95']}\n")
        f.write(f"  k (max gap): {k_gap['k_gap']}\n")
        f.write(f"  k (ratio threshold): {k_ratio['k_ratio']}\n\n")
        
        f.write(f"Recommended k: {k_recommended}\n\n")
        
        f.write("Top 20 eigenvalues:\n")
        for i, val in enumerate(eigenvalues[:20].tolist(), 1):
            f.write(f"  {i}: {val:.6e}\n")
    
    logger.info(f"✓ Analysis results saved to: {results_file}")
    logger.info(f"\nRecommended k value: {k_recommended}")
    logger.info(f"See plots in: {output_dir}")


if __name__ == '__main__':
    main()
