"""
Safety Tax Calculator

Safety Taxの定量化モジュール。アライメントドリフト率とSafety-Utilityトレードオフを測定。

理論的根拠: ドキュメント7、8
- Safety Tax = (性能低下率) / (安全性向上率)
- アライメントドリフト = |安全性_after - 安全性_before| / 安全性_before
- 期待値:
  - AlignGuard-LoRA: 50%削減
  - SST-Merge: 60-70%削減

参考文献:
- Reasoning-Safety Trade-Off (Emergent Mind)
- DRIFTCHECK: アライメントドリフト測定
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SafetyTaxMetrics:
    """Safety Tax関連のメトリクス"""
    safety_tax: float
    utility_drop_rate: float
    safety_gain_rate: float
    alignment_drift: float
    alignment_drift_reduction: float
    
    # 追加メトリクス
    safety_before: float
    safety_after: float
    utility_before: float
    utility_after: float
    
    def to_dict(self) -> Dict[str, float]:
        """辞書形式に変換"""
        return {
            'safety_tax': self.safety_tax,
            'utility_drop_rate': self.utility_drop_rate,
            'safety_gain_rate': self.safety_gain_rate,
            'alignment_drift': self.alignment_drift,
            'alignment_drift_reduction': self.alignment_drift_reduction,
            'safety_before': self.safety_before,
            'safety_after': self.safety_after,
            'utility_before': self.utility_before,
            'utility_after': self.utility_after,
        }


class SafetyTaxCalculator:
    """
    Safety Taxの計算と分析
    
    Safety Taxは、安全性向上のために支払うユーティリティのコストを定量化します。
    
    定義:
    - Safety Tax = (ユーティリティ低下率) / (安全性向上率)
    - 低いほど効率的（少ないコストで高い安全性）
    
    アライメントドリフト:
    - アライメントドリフト = |安全性_after - 安全性_before| / 安全性_before
    - モデルの安全性がどれだけ変化したかを測定
    
    Args:
        baseline_method: ベースライン手法名（比較用）
        target_reduction: 目標削減率（例: SST-Mergeは0.6-0.7）
    """
    
    def __init__(
        self,
        baseline_method: str = "AlignGuard-LoRA",
        target_reduction: float = 0.65
    ):
        self.baseline_method = baseline_method
        self.target_reduction = target_reduction
        
        # ベースライン手法の期待値
        self.baseline_drift_reduction = {
            "AlignGuard-LoRA": 0.5,  # 50%削減
            "DARE": 0.3,  # 推定値
            "TIES": 0.2,  # 推定値
            "TaskArithmetic": 0.1,  # 推定値
        }
        
        logger.info(
            f"SafetyTaxCalculator initialized: baseline={baseline_method}, "
            f"target_reduction={target_reduction}"
        )
    
    def compute_safety_tax(
        self,
        safety_before: float,
        safety_after: float,
        utility_before: float,
        utility_after: float,
        method_name: str = "Unknown"
    ) -> SafetyTaxMetrics:
        """
        Safety Taxを計算
        
        Args:
            safety_before: マージ前の安全性スコア（0.0-1.0）
            safety_after: マージ後の安全性スコア（0.0-1.0）
            utility_before: マージ前のユーティリティスコア（0.0-1.0）
            utility_after: マージ後のユーティリティスコア（0.0-1.0）
            method_name: 手法名
            
        Returns:
            metrics: SafetyTaxMetrics
        """
        # ユーティリティ低下率
        if utility_before > 0:
            utility_drop_rate = (utility_before - utility_after) / utility_before
        else:
            utility_drop_rate = 0.0
        
        # 安全性向上率
        if safety_before > 0:
            safety_gain_rate = (safety_after - safety_before) / safety_before
        else:
            safety_gain_rate = 0.0
        
        # Safety Tax
        if safety_gain_rate > 0:
            safety_tax = utility_drop_rate / safety_gain_rate
        elif safety_gain_rate < 0:
            # 安全性が低下した場合は負のSafety Tax
            safety_tax = utility_drop_rate / abs(safety_gain_rate)
        else:
            # 安全性が変化していない場合
            safety_tax = float('inf') if utility_drop_rate > 0 else 0.0
        
        # アライメントドリフト
        if safety_before > 0:
            alignment_drift = abs(safety_after - safety_before) / safety_before
        else:
            alignment_drift = 0.0
        
        # ベースラインとの比較によるドリフト削減率
        baseline_drift = self.baseline_drift_reduction.get(
            self.baseline_method, 0.5
        )
        
        if baseline_drift > 0:
            alignment_drift_reduction = 1.0 - (alignment_drift / baseline_drift)
        else:
            alignment_drift_reduction = 0.0
        
        metrics = SafetyTaxMetrics(
            safety_tax=safety_tax,
            utility_drop_rate=utility_drop_rate,
            safety_gain_rate=safety_gain_rate,
            alignment_drift=alignment_drift,
            alignment_drift_reduction=alignment_drift_reduction,
            safety_before=safety_before,
            safety_after=safety_after,
            utility_before=utility_before,
            utility_after=utility_after,
        )
        
        logger.info(
            f"[{method_name}] Safety Tax: {safety_tax:.4f}, "
            f"Alignment Drift: {alignment_drift:.4f}, "
            f"Drift Reduction: {alignment_drift_reduction:.2%}"
        )
        
        return metrics
    
    def compute_driftcheck_score(
        self,
        safety_scores_before: List[float],
        safety_scores_after: List[float]
    ) -> Dict[str, float]:
        """
        DRIFTCHECK指標を計算
        
        DRIFTCHECKは、複数のサンプルに対する安全性の変化を測定します。
        
        Args:
            safety_scores_before: マージ前の安全性スコアのリスト
            safety_scores_after: マージ後の安全性スコアのリスト
            
        Returns:
            driftcheck_metrics: DRIFTCHECK関連のメトリクス
        """
        assert len(safety_scores_before) == len(safety_scores_after), \
            "Before and after scores must have the same length"
        
        # 平均ドリフト
        drifts = []
        for before, after in zip(safety_scores_before, safety_scores_after):
            if before > 0:
                drift = abs(after - before) / before
                drifts.append(drift)
        
        mean_drift = np.mean(drifts) if drifts else 0.0
        std_drift = np.std(drifts) if drifts else 0.0
        max_drift = np.max(drifts) if drifts else 0.0
        
        # ドリフト方向の一貫性
        positive_drifts = sum(1 for b, a in zip(safety_scores_before, safety_scores_after) if a > b)
        negative_drifts = sum(1 for b, a in zip(safety_scores_before, safety_scores_after) if a < b)
        
        drift_consistency = abs(positive_drifts - negative_drifts) / len(drifts) if drifts else 0.0
        
        metrics = {
            'mean_drift': mean_drift,
            'std_drift': std_drift,
            'max_drift': max_drift,
            'drift_consistency': drift_consistency,
            'num_samples': len(drifts),
        }
        
        logger.info(
            f"DRIFTCHECK: mean={mean_drift:.4f}, std={std_drift:.4f}, "
            f"max={max_drift:.4f}, consistency={drift_consistency:.2%}"
        )
        
        return metrics
    
    def compare_with_baseline(
        self,
        method_metrics: SafetyTaxMetrics,
        baseline_metrics: SafetyTaxMetrics
    ) -> Dict[str, float]:
        """
        ベースライン手法との比較
        
        Args:
            method_metrics: 評価手法のメトリクス
            baseline_metrics: ベースライン手法のメトリクス
            
        Returns:
            comparison: 比較結果
        """
        # Safety Taxの改善率
        if baseline_metrics.safety_tax > 0:
            safety_tax_improvement = (
                (baseline_metrics.safety_tax - method_metrics.safety_tax) /
                baseline_metrics.safety_tax
            )
        else:
            safety_tax_improvement = 0.0
        
        # アライメントドリフトの改善率
        if baseline_metrics.alignment_drift > 0:
            drift_improvement = (
                (baseline_metrics.alignment_drift - method_metrics.alignment_drift) /
                baseline_metrics.alignment_drift
            )
        else:
            drift_improvement = 0.0
        
        # ユーティリティ維持率の比較
        utility_retention_method = 1.0 - method_metrics.utility_drop_rate
        utility_retention_baseline = 1.0 - baseline_metrics.utility_drop_rate
        utility_advantage = utility_retention_method - utility_retention_baseline
        
        comparison = {
            'safety_tax_improvement': safety_tax_improvement,
            'drift_improvement': drift_improvement,
            'utility_advantage': utility_advantage,
            'meets_target': drift_improvement >= self.target_reduction,
        }
        
        logger.info(
            f"Comparison with {self.baseline_method}: "
            f"Safety Tax improvement={safety_tax_improvement:.2%}, "
            f"Drift improvement={drift_improvement:.2%}, "
            f"Meets target={comparison['meets_target']}"
        )
        
        return comparison
    
    def compute_pareto_efficiency(
        self,
        safety_scores: List[float],
        utility_scores: List[float],
        method_names: List[str]
    ) -> Dict[str, any]:
        """
        パレート効率を計算
        
        複合メトリック空間で理論的最適対角線に最も近い手法を特定。
        
        Args:
            safety_scores: 各手法の安全性スコア
            utility_scores: 各手法のユーティリティスコア
            method_names: 手法名のリスト
            
        Returns:
            pareto_metrics: パレート効率関連のメトリクス
        """
        assert len(safety_scores) == len(utility_scores) == len(method_names), \
            "All lists must have the same length"
        
        # 理想点（安全性=1.0, ユーティリティ=1.0）
        ideal_point = np.array([1.0, 1.0])
        
        # 各手法の理想点からの距離
        distances = []
        for safety, utility in zip(safety_scores, utility_scores):
            point = np.array([safety, utility])
            distance = np.linalg.norm(ideal_point - point)
            distances.append(distance)
        
        # パレートフロンティアの特定
        pareto_front = []
        for i, (safety, utility) in enumerate(zip(safety_scores, utility_scores)):
            is_dominated = False
            for j, (s2, u2) in enumerate(zip(safety_scores, utility_scores)):
                if i != j and s2 >= safety and u2 >= utility and (s2 > safety or u2 > utility):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_front.append(i)
        
        # 最も理想点に近い手法
        best_idx = np.argmin(distances)
        
        metrics = {
            'distances': {name: dist for name, dist in zip(method_names, distances)},
            'pareto_front': [method_names[i] for i in pareto_front],
            'best_method': method_names[best_idx],
            'best_distance': distances[best_idx],
        }
        
        logger.info(
            f"Pareto analysis: Best method={metrics['best_method']}, "
            f"Distance to ideal={metrics['best_distance']:.4f}, "
            f"Pareto front={metrics['pareto_front']}"
        )
        
        return metrics


def test_safety_tax_calculator():
    """SafetyTaxCalculatorの簡易テスト"""
    logger.info("Testing SafetyTaxCalculator...")
    
    calculator = SafetyTaxCalculator(baseline_method="AlignGuard-LoRA", target_reduction=0.65)
    
    # テスト1: Safety Tax計算
    logger.info("\n=== Test 1: Safety Tax Calculation ===")
    metrics_sst = calculator.compute_safety_tax(
        safety_before=0.7,
        safety_after=0.9,
        utility_before=0.9,
        utility_after=0.88,
        method_name="SST-Merge"
    )
    print(f"SST-Merge metrics: {metrics_sst.to_dict()}")
    
    metrics_agl = calculator.compute_safety_tax(
        safety_before=0.7,
        safety_after=0.85,
        utility_before=0.9,
        utility_after=0.82,
        method_name="AlignGuard-LoRA"
    )
    print(f"AlignGuard-LoRA metrics: {metrics_agl.to_dict()}")
    
    # テスト2: ベースライン比較
    logger.info("\n=== Test 2: Baseline Comparison ===")
    comparison = calculator.compare_with_baseline(metrics_sst, metrics_agl)
    print(f"Comparison results: {comparison}")
    
    # テスト3: DRIFTCHECK
    logger.info("\n=== Test 3: DRIFTCHECK ===")
    safety_before = [0.7, 0.75, 0.68, 0.72, 0.71]
    safety_after = [0.88, 0.91, 0.87, 0.89, 0.90]
    driftcheck = calculator.compute_driftcheck_score(safety_before, safety_after)
    print(f"DRIFTCHECK metrics: {driftcheck}")
    
    # テスト4: パレート効率
    logger.info("\n=== Test 4: Pareto Efficiency ===")
    safety_scores = [0.9, 0.85, 0.8, 0.75, 0.7]
    utility_scores = [0.88, 0.82, 0.85, 0.9, 0.92]
    method_names = ["SST-Merge", "AlignGuard-LoRA", "DARE", "TIES", "TA"]
    
    pareto = calculator.compute_pareto_efficiency(safety_scores, utility_scores, method_names)
    print(f"Pareto metrics: {pareto}")
    
    logger.info("\nSafetyTaxCalculator test completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_safety_tax_calculator()
