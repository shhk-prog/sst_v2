"""
Metrics Reporter

複合メトリックの計算とレポート生成モジュール。

理論的根拠: ドキュメント8
- MedOmni-45°スタイルの複合メトリック
- パレート効率の計算
- 結果の可視化（散布図、棒グラフ）

複合スコア = α * 安全性 + β * ユーティリティ - γ * Safety Tax
パレート距離 = √((安全性 - 理想)² + (ユーティリティ - 理想)²)
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MethodMetrics:
    """各手法のメトリクス"""
    method_name: str
    safety_score: float
    utility_score: float
    safety_tax: float
    alignment_drift: float
    computation_time: float  # 秒
    
    # 複合スコア
    composite_score: Optional[float] = None
    pareto_distance: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return asdict(self)


class MetricsReporter:
    """
    複合メトリックの計算とレポート生成
    
    MedOmni-45°スタイルの複合メトリックを計算し、
    パレート効率分析と可視化を提供します。
    
    複合スコアの計算:
    - composite_score = α * safety + β * utility - γ * safety_tax
    - デフォルト: α=0.4, β=0.4, γ=0.2
    
    Args:
        alpha: 安全性の重み
        beta: ユーティリティの重み
        gamma: Safety Taxのペナルティ重み
        output_dir: 出力ディレクトリ
    """
    
    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.4,
        gamma: float = 0.2,
        output_dir: str = "results/metrics"
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # スタイル設定
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 12
        
        logger.info(
            f"MetricsReporter initialized: α={alpha}, β={beta}, γ={gamma}, "
            f"output_dir={output_dir}"
        )
    
    def compute_composite_score(
        self,
        safety: float,
        utility: float,
        safety_tax: float
    ) -> float:
        """
        複合スコアを計算
        
        composite_score = α * safety + β * utility - γ * safety_tax
        
        Args:
            safety: 安全性スコア（0.0-1.0）
            utility: ユーティリティスコア（0.0-1.0）
            safety_tax: Safety Tax
            
        Returns:
            composite_score: 複合スコア
        """
        # Safety Taxを正規化（0-1の範囲に）
        normalized_tax = min(safety_tax, 1.0)
        
        composite = (
            self.alpha * safety +
            self.beta * utility -
            self.gamma * normalized_tax
        )
        
        return composite
    
    def compute_pareto_distance(
        self,
        safety: float,
        utility: float,
        ideal_safety: float = 1.0,
        ideal_utility: float = 1.0
    ) -> float:
        """
        理想点からのパレート距離を計算
        
        distance = √((safety - ideal_safety)² + (utility - ideal_utility)²)
        
        Args:
            safety: 安全性スコア
            utility: ユーティリティスコア
            ideal_safety: 理想的な安全性スコア
            ideal_utility: 理想的なユーティリティスコア
            
        Returns:
            distance: パレート距離
        """
        distance = np.sqrt(
            (safety - ideal_safety) ** 2 +
            (utility - ideal_utility) ** 2
        )
        
        return distance
    
    def analyze_methods(
        self,
        methods_metrics: List[MethodMetrics]
    ) -> Dict[str, any]:
        """
        複数手法の包括的分析
        
        Args:
            methods_metrics: 各手法のメトリクスリスト
            
        Returns:
            analysis: 分析結果
        """
        logger.info(f"Analyzing {len(methods_metrics)} methods...")
        
        # 複合スコアとパレート距離を計算
        for metrics in methods_metrics:
            metrics.composite_score = self.compute_composite_score(
                metrics.safety_score,
                metrics.utility_score,
                metrics.safety_tax
            )
            metrics.pareto_distance = self.compute_pareto_distance(
                metrics.safety_score,
                metrics.utility_score
            )
        
        # ランキング
        ranking_by_composite = sorted(
            methods_metrics,
            key=lambda m: m.composite_score,
            reverse=True
        )
        
        ranking_by_pareto = sorted(
            methods_metrics,
            key=lambda m: m.pareto_distance
        )
        
        # パレートフロンティアの特定
        pareto_front = self._identify_pareto_front(methods_metrics)
        
        # 統計サマリー
        safety_scores = [m.safety_score for m in methods_metrics]
        utility_scores = [m.utility_score for m in methods_metrics]
        safety_taxes = [m.safety_tax for m in methods_metrics]
        
        analysis = {
            'ranking_by_composite': [m.method_name for m in ranking_by_composite],
            'ranking_by_pareto': [m.method_name for m in ranking_by_pareto],
            'pareto_front': [m.method_name for m in pareto_front],
            'best_composite': ranking_by_composite[0].method_name,
            'best_pareto': ranking_by_pareto[0].method_name,
            'statistics': {
                'safety': {
                    'mean': np.mean(safety_scores),
                    'std': np.std(safety_scores),
                    'min': np.min(safety_scores),
                    'max': np.max(safety_scores),
                },
                'utility': {
                    'mean': np.mean(utility_scores),
                    'std': np.std(utility_scores),
                    'min': np.min(utility_scores),
                    'max': np.max(utility_scores),
                },
                'safety_tax': {
                    'mean': np.mean(safety_taxes),
                    'std': np.std(safety_taxes),
                    'min': np.min(safety_taxes),
                    'max': np.max(safety_taxes),
                },
            }
        }
        
        logger.info(f"Best method (composite): {analysis['best_composite']}")
        logger.info(f"Best method (pareto): {analysis['best_pareto']}")
        logger.info(f"Pareto front: {analysis['pareto_front']}")
        
        return analysis
    
    def _identify_pareto_front(
        self,
        methods_metrics: List[MethodMetrics]
    ) -> List[MethodMetrics]:
        """
        パレートフロンティアを特定
        
        ある手法が他のすべての手法に対して、安全性とユーティリティの両方で
        劣っていない場合、その手法はパレート最適です。
        """
        pareto_front = []
        
        for i, metrics_i in enumerate(methods_metrics):
            is_dominated = False
            
            for j, metrics_j in enumerate(methods_metrics):
                if i != j:
                    # metrics_jがmetrics_iを支配するか？
                    if (metrics_j.safety_score >= metrics_i.safety_score and
                        metrics_j.utility_score >= metrics_i.utility_score and
                        (metrics_j.safety_score > metrics_i.safety_score or
                         metrics_j.utility_score > metrics_i.utility_score)):
                        is_dominated = True
                        break
            
            if not is_dominated:
                pareto_front.append(metrics_i)
        
        return pareto_front
    
    def visualize_safety_utility_tradeoff(
        self,
        methods_metrics: List[MethodMetrics],
        save_path: Optional[str] = None
    ):
        """
        Safety-Utilityトレードオフの散布図を作成
        
        Args:
            methods_metrics: 各手法のメトリクス
            save_path: 保存パス（Noneの場合はデフォルト）
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # パレートフロンティアを特定
        pareto_front = self._identify_pareto_front(methods_metrics)
        pareto_names = {m.method_name for m in pareto_front}
        
        # 各手法をプロット
        for metrics in methods_metrics:
            is_pareto = metrics.method_name in pareto_names
            
            ax.scatter(
                metrics.safety_score,
                metrics.utility_score,
                s=200 if is_pareto else 100,
                alpha=0.7 if is_pareto else 0.5,
                marker='*' if is_pareto else 'o',
                label=metrics.method_name
            )
            
            # ラベルを追加
            ax.annotate(
                metrics.method_name,
                (metrics.safety_score, metrics.utility_score),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=10,
                alpha=0.8
            )
        
        # 理想点を表示
        ax.scatter(1.0, 1.0, s=300, c='red', marker='X', label='Ideal Point', zorder=10)
        
        # 理論的最適対角線（45°線）
        ax.plot([0, 1], [0, 1], 'r--', alpha=0.3, linewidth=2, label='Theoretical Optimal (45°)')
        
        ax.set_xlabel('Safety Score', fontsize=14)
        ax.set_ylabel('Utility Score', fontsize=14)
        ax.set_title('Safety-Utility Trade-off Analysis', fontsize=16, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1.05)
        ax.set_ylim(0, 1.05)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / "safety_utility_tradeoff.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Safety-Utility tradeoff plot saved to {save_path}")
        plt.close()
    
    def visualize_safety_tax_comparison(
        self,
        methods_metrics: List[MethodMetrics],
        save_path: Optional[str] = None
    ):
        """
        Safety Taxの棒グラフを作成
        
        Args:
            methods_metrics: 各手法のメトリクス
            save_path: 保存パス
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 手法名とSafety Taxを抽出
        method_names = [m.method_name for m in methods_metrics]
        safety_taxes = [m.safety_tax for m in methods_metrics]
        
        # 色を設定（SST-Mergeを強調）
        colors = ['#2ecc71' if 'SST' in name else '#3498db' for name in method_names]
        
        # 棒グラフ
        bars = ax.bar(method_names, safety_taxes, color=colors, alpha=0.7, edgecolor='black')
        
        # 値をバーの上に表示
        for bar, tax in zip(bars, safety_taxes):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{tax:.3f}',
                ha='center',
                va='bottom',
                fontsize=10
            )
        
        ax.set_ylabel('Safety Tax', fontsize=14)
        ax.set_title('Safety Tax Comparison Across Methods', fontsize=16, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.output_dir / "safety_tax_comparison.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Safety Tax comparison plot saved to {save_path}")
        plt.close()
    
    def generate_report(
        self,
        methods_metrics: List[MethodMetrics],
        analysis: Dict[str, any],
        report_path: Optional[str] = None
    ):
        """
        包括的なレポートを生成（Markdown形式）
        
        Args:
            methods_metrics: 各手法のメトリクス
            analysis: 分析結果
            report_path: レポート保存パス
        """
        if report_path is None:
            report_path = self.output_dir / "comprehensive_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# SST-Merge実験結果レポート\n\n")
            
            # サマリー
            f.write("## 実験サマリー\n\n")
            f.write(f"- **評価手法数**: {len(methods_metrics)}\n")
            f.write(f"- **最良手法（複合スコア）**: {analysis['best_composite']}\n")
            f.write(f"- **最良手法（パレート距離）**: {analysis['best_pareto']}\n")
            f.write(f"- **パレートフロンティア**: {', '.join(analysis['pareto_front'])}\n\n")
            
            # 各手法の詳細
            f.write("## 各手法の詳細メトリクス\n\n")
            f.write("| 手法 | 安全性 | ユーティリティ | Safety Tax | 複合スコア | パレート距離 | 計算時間(s) |\n")
            f.write("|------|--------|---------------|------------|-----------|-------------|-------------|\n")
            
            for m in sorted(methods_metrics, key=lambda x: x.composite_score, reverse=True):
                f.write(
                    f"| {m.method_name} | {m.safety_score:.4f} | {m.utility_score:.4f} | "
                    f"{m.safety_tax:.4f} | {m.composite_score:.4f} | {m.pareto_distance:.4f} | "
                    f"{m.computation_time:.2f} |\n"
                )
            
            # 統計サマリー
            f.write("\n## 統計サマリー\n\n")
            stats = analysis['statistics']
            
            f.write("### 安全性スコア\n")
            f.write(f"- 平均: {stats['safety']['mean']:.4f}\n")
            f.write(f"- 標準偏差: {stats['safety']['std']:.4f}\n")
            f.write(f"- 範囲: [{stats['safety']['min']:.4f}, {stats['safety']['max']:.4f}]\n\n")
            
            f.write("### ユーティリティスコア\n")
            f.write(f"- 平均: {stats['utility']['mean']:.4f}\n")
            f.write(f"- 標準偏差: {stats['utility']['std']:.4f}\n")
            f.write(f"- 範囲: [{stats['utility']['min']:.4f}, {stats['utility']['max']:.4f}]\n\n")
            
            f.write("### Safety Tax\n")
            f.write(f"- 平均: {stats['safety_tax']['mean']:.4f}\n")
            f.write(f"- 標準偏差: {stats['safety_tax']['std']:.4f}\n")
            f.write(f"- 範囲: [{stats['safety_tax']['min']:.4f}, {stats['safety_tax']['max']:.4f}]\n\n")
            
            # 可視化への参照
            f.write("## 可視化\n\n")
            f.write("- [Safety-Utility Trade-off](safety_utility_tradeoff.png)\n")
            f.write("- [Safety Tax Comparison](safety_tax_comparison.png)\n\n")
        
        logger.info(f"Comprehensive report saved to {report_path}")
    
    def save_metrics_json(
        self,
        methods_metrics: List[MethodMetrics],
        json_path: Optional[str] = None
    ):
        """
        メトリクスをJSON形式で保存
        
        Args:
            methods_metrics: 各手法のメトリクス
            json_path: JSON保存パス
        """
        if json_path is None:
            json_path = self.output_dir / "metrics.json"
        
        data = {
            'methods': [m.to_dict() for m in methods_metrics],
            'config': {
                'alpha': self.alpha,
                'beta': self.beta,
                'gamma': self.gamma,
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metrics JSON saved to {json_path}")


def test_metrics_reporter():
    """MetricsReporterの簡易テスト"""
    logger.info("Testing MetricsReporter...")
    
    reporter = MetricsReporter(output_dir="results/test_metrics")
    
    # テストデータ
    methods = [
        MethodMetrics("SST-Merge", 0.90, 0.88, 0.15, 0.12, 120.5),
        MethodMetrics("AlignGuard-LoRA", 0.85, 0.82, 0.25, 0.20, 100.3),
        MethodMetrics("DARE", 0.80, 0.85, 0.30, 0.25, 95.7),
        MethodMetrics("TIES", 0.75, 0.87, 0.40, 0.30, 80.2),
        MethodMetrics("TaskArithmetic", 0.70, 0.90, 0.50, 0.35, 50.1),
    ]
    
    # 分析
    analysis = reporter.analyze_methods(methods)
    print(f"\nAnalysis results: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # 可視化
    reporter.visualize_safety_utility_tradeoff(methods)
    reporter.visualize_safety_tax_comparison(methods)
    
    # レポート生成
    reporter.generate_report(methods, analysis)
    reporter.save_metrics_json(methods)
    
    logger.info("\nMetricsReporter test completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_metrics_reporter()
