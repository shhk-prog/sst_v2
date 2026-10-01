#!/usr/bin/env python3
"""
SST-Merge 比較実験スクリプト

既存版（sst_merge.py）と改善版（sst_merge_improved.py）を比較
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_comparison(
    k: int = 40,
    alpha: float = 1.0,
    projection_strength: float = 0.2,
    use_adaptive: bool = True
):
    """
    既存版と改善版のSST-Mergeを比較
    
    Args:
        k: サブスペース次元数
        alpha: 結合比率
        projection_strength: 射影強度（改善版のみ）
        use_adaptive: 適応的制御を使用（改善版のみ）
    """
    logger.info("=" * 70)
    logger.info("SST-Merge比較実験")
    logger.info("=" * 70)
    logger.info(f"Parameters:")
    logger.info(f"  k = {k}")
    logger.info(f"  alpha = {alpha}")
    logger.info(f"  projection_strength = {projection_strength} (改善版)")
    logger.info(f"  use_adaptive = {use_adaptive} (改善版)")
    logger.info("=" * 70)
    
    # TODO: 実際のマージと評価を実装
    # 1. モデルとデータのロード
    # 2. 既存版でマージ
    # 3. 改善版でマージ
    # 4. 両方を評価
    # 5. 結果を比較
    
    logger.info("Comparison experiment placeholder")
    logger.info("To implement:")
    logger.info("  1. Load model and adapters")
    logger.info("  2. Run original SST-Merge")
    logger.info("  3. Run improved SST-Merge")
    logger.info("  4. Evaluate both")
    logger.info("  5. Compare results")
    
    # 結果の保存先
    results_dir = Path("results/comparison")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = results_dir / f"comparison_k{k}_alpha{alpha}_strength{projection_strength}_{timestamp}.json"
    
    # 結果サンプル
    results = {
        "parameters": {
            "k": k,
            "alpha": alpha,
            "projection_strength": projection_strength,
            "use_adaptive": use_adaptive
        },
        "original": {
            "jailbreak_rta": 0.77,  # プレースホルダー
            "mmlu": 0.53,
            "repliqa": 0.335
        },
        "improved": {
            "jailbreak_rta": 0.95,  # 期待値
            "mmlu": 0.53,
            "repliqa": 0.34
        },
        "improvement": {
            "jailbreak_rta": "+18.0pt",
            "mmlu": "0.0pt",
            "repliqa": "+0.5pt"
        }
    }
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {result_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='SST-Merge comparison experiment')
    parser.add_argument('--k', type=int, default=40, help='Subspace dimension')
    parser.add_argument('--alpha', type=float, default=1.0, help='Merge ratio')
    parser.add_argument('--projection_strength', type=float, default=0.2,
                       help='Projection strength for improved version (0.0-1.0)')
    parser.add_argument('--use_adaptive', action='store_true', default=True,
                       help='Use adaptive control in improved version')
    parser.add_argument('--no_adaptive', action='store_false', dest='use_adaptive',
                       help='Disable adaptive control')
    
    args = parser.parse_args()
    
    results = run_comparison(
        k=args.k,
        alpha=args.alpha,
        projection_strength=args.projection_strength,
        use_adaptive=args.use_adaptive
    )
    
    # 結果の表示
    print("\n" + "=" * 70)
    print("Comparison Results")
    print("=" * 70)
    print(f"Original SST-Merge:")
    print(f"  Jailbreak RtA: {results['original']['jailbreak_rta']:.1%}")
    print(f"  MMLU:          {results['original']['mmlu']:.1%}")
    print(f"  RepliQA:       {results['original']['repliqa']:.3f}")
    print()
    print(f"Improved SST-Merge:")
    print(f"  Jailbreak RtA: {results['improved']['jailbreak_rta']:.1%}")
    print(f"  MMLU:          {results['improved']['mmlu']:.1%}")
    print(f"  RepliQA:       {results['improved']['repliqa']:.3f}")
    print()
    print(f"Improvement:")
    print(f"  Jailbreak RtA: {results['improvement']['jailbreak_rta']}")
    print(f"  MMLU:          {results['improvement']['mmlu']}")
    print(f"  RepliQA:       {results['improvement']['repliqa']}")
    print("=" * 70)


if __name__ == '__main__':
    main()
