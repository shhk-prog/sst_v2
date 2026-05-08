"""
実験1: Safety-Utility Trade-off の定量化

SST-MergeがSafety Taxをどの程度削減できるかを検証。
AlignGuard-LoRAとの比較を行う。
"""

import torch
import logging
from pathlib import Path
import yaml
import json
from datetime import datetime

# プロジェクトのルートをパスに追加
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.sst_merge import SSTMerge
from src.baselines.task_arithmetic import TaskArithmetic
from src.baselines.ties_merging import TIESMerging
from src.evaluation.safety_evaluator import SafetyEvaluator
from src.evaluation.utility_evaluator import UtilityEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = None):
    """実験設定を読み込む"""
    if config_path is None:
        # スクリプトの場所から設定ファイルへの絶対パスを構築
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / "configs" / "experiment_config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"設定ファイルが見つかりません: {config_path}")
        logger.warning("デフォルト設定を使用します")
        # デフォルト設定を返す
        return {
            "baselines": {
                "task_arithmetic": {"scaling_factor": 0.5},
                "ties_merging": {"trim_threshold": 0.2}
            },
            "sst_merge": {
                "k": 10,
                "fim_approximation": "gradient_variance"
            }
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def run_experiment_1():
    """
    実験1: Safety-Utility Trade-off の定量化
    
    目標:
    - SST-MergeがAGLに対して50%以上のSafety Tax削減を達成するか検証
    - 複合メトリック空間でパレート最適に近いか確認
    """
    logger.info("=" * 60)
    logger.info("実験1: Safety-Utility Trade-off の定量化")
    logger.info("=" * 60)
    
    # 設定の読み込み
    config = load_config()
    
    # 結果を保存するディレクトリ（絶対パス）
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "exp1_safety_utility"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 実験結果を格納
    results = {
        "experiment": "exp1_safety_utility_tradeoff",
        "timestamp": datetime.now().isoformat(),
        "config": config,
        "methods": {}
    }
    
    # 各手法で実験
    methods = {
        "task_arithmetic": TaskArithmetic(scaling_factor=config["baselines"]["task_arithmetic"]["scaling_factor"]),
        "ties_merging": TIESMerging(trim_threshold=config["baselines"]["ties_merging"]["trim_threshold"]),
        "sst_merge": SSTMerge(
            k=config["sst_merge"]["k"],
            fim_approximation=config["sst_merge"]["fim_approximation"]
        )
    }
    
    for method_name, method in methods.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"評価中: {method_name}")
        logger.info(f"{'='*50}")
        
        # ここでは簡易実装のため、ダミーの結果を生成
        # 実際の実装では、モデルをロードしてマージ・評価を行う
        
        method_results = {
            "safety": {
                "refusal_rate": 0.0,  # 実際には評価
                "jailbreak_resistance": 0.0
            },
            "utility": {
                "mmlu_accuracy": 0.0,  # 実際には評価
                "humaneval_pass_at_1": 0.0
            },
            "safety_tax": 0.0  # 計算
        }
        
        results["methods"][method_name] = method_results
        
        logger.info(f"結果:")
        logger.info(f"  Refusal Rate: {method_results['safety']['refusal_rate']:.4f}")
        logger.info(f"  MMLU Accuracy: {method_results['utility']['mmlu_accuracy']:.4f}")
        logger.info(f"  Safety Tax: {method_results['safety_tax']:.4f}")
    
    # 結果を保存
    results_file = results_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n結果を保存しました: {results_file}")
    
    # 比較分析
    logger.info("\n" + "=" * 60)
    logger.info("比較分析")
    logger.info("=" * 60)
    
    # SST-MergeとTAの比較
    sst_tax = results["methods"]["sst_merge"]["safety_tax"]
    ta_tax = results["methods"]["task_arithmetic"]["safety_tax"]
    
    if ta_tax > 0:
        improvement = (ta_tax - sst_tax) / ta_tax * 100
        logger.info(f"SST-Merge vs Task Arithmetic:")
        logger.info(f"  Safety Tax削減率: {improvement:.2f}%")
        
        if improvement >= 50:
            logger.info("  ✓ 目標達成: 50%以上の削減")
        else:
            logger.info(f"  ✗ 目標未達成: {improvement:.2f}% < 50%")
    
    return results


if __name__ == "__main__":
    results = run_experiment_1()
    
    logger.info("\n実験1完了")
