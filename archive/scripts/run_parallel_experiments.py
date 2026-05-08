#!/usr/bin/env python3
"""
SST-Merge 並列実験実行スクリプト

H100 4枚を使用して3モデルを並列実行します。

使用方法:
    # 3モデルを並列実行
    python scripts/run_parallel_experiments.py --mode full --experiment all
    
    # 特定のモデルのみ
    python scripts/run_parallel_experiments.py --mode full --model mistral-7b,llama-3.1-8b
"""

import subprocess
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParallelExperimentRunner:
    """
    並列実験実行クラス
    
    H100 4枚を使用して複数モデルを同時実行
    """
    
    # モデルとGPUのマッピング
    MODEL_GPU_MAP = {
        'mistral-7b': 0,      # GPU 0
        'llama-3.1-8b': 1,    # GPU 1
        'qwen-2.5-14b': 2,    # GPU 2
    }
    
    # モデルの優先順位（実験結果に基づく）
    MODEL_PRIORITY = [
        'qwen-2.5-14b',    # 1. 最高のユーティリティ、安定した結果
        'llama-3.1-8b',    # 2. バランス型、Instructチューニング
        'mistral-7b',      # 3. 最高の安全性、軽量
    ]
    
    def __init__(self, mode='full', experiment='all'):
        self.mode = mode
        self.experiment = experiment
        self.processes = {}
        self.results = {}
        
    def run_model(self, model_name, gpu_id):
        """
        単一モデルの実験を実行
        
        Args:
            model_name: モデル名
            gpu_id: GPU ID
            
        Returns:
            process: サブプロセス
        """
        logger.info(f"Starting {model_name} on GPU {gpu_id}")
        
        # ログファイル
        log_dir = Path('logs/parallel')
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{model_name}_{self.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # コマンド構築
        cmd = [
            'python', 'experiments/run_real_experiments.py',
            '--mode', self.mode,
            '--model', model_name,
            '--experiment', self.experiment
        ]
        
        # 環境変数でGPUを指定
        env = {
            'CUDA_VISIBLE_DEVICES': str(gpu_id),
            **dict(subprocess.os.environ)
        }
        
        # プロセス起動
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=env
            )
        
        logger.info(f"  Process ID: {process.pid}")
        logger.info(f"  Log file: {log_file}")
        
        return process, log_file
    
    def run_parallel(self, models=None):
        """
        複数モデルを並列実行
        
        Args:
            models: 実行するモデルのリスト（Noneの場合は全モデル）
        """
        if models is None:
            models = self.MODEL_PRIORITY
        
        logger.info("="*80)
        logger.info("Starting parallel experiments")
        logger.info("="*80)
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Experiment: {self.experiment}")
        logger.info(f"Models: {models}")
        logger.info(f"GPU mapping: {self.MODEL_GPU_MAP}")
        
        # 開始時刻
        start_time = time.time()
        
        # 各モデルを並列起動
        for model_name in models:
            if model_name not in self.MODEL_GPU_MAP:
                logger.warning(f"Unknown model: {model_name}, skipping")
                continue
            
            gpu_id = self.MODEL_GPU_MAP[model_name]
            process, log_file = self.run_model(model_name, gpu_id)
            
            self.processes[model_name] = {
                'process': process,
                'log_file': log_file,
                'gpu_id': gpu_id,
                'start_time': time.time()
            }
        
        logger.info(f"\nAll {len(self.processes)} models started")
        logger.info("Waiting for completion...\n")
        
        # プロセスの完了を待機
        self.wait_for_completion()
        
        # 終了時刻
        end_time = time.time()
        total_time = end_time - start_time
        
        # 結果のサマリー
        self.print_summary(total_time)
    
    def wait_for_completion(self):
        """すべてのプロセスの完了を待機"""
        while self.processes:
            for model_name in list(self.processes.keys()):
                process_info = self.processes[model_name]
                process = process_info['process']
                
                # プロセスの状態をチェック
                if process.poll() is not None:
                    # プロセス完了
                    elapsed = time.time() - process_info['start_time']
                    exit_code = process.returncode
                    
                    self.results[model_name] = {
                        'exit_code': exit_code,
                        'elapsed_time': elapsed,
                        'log_file': str(process_info['log_file'])
                    }
                    
                    status = "✓ SUCCESS" if exit_code == 0 else "✗ FAILED"
                    logger.info(f"{status}: {model_name} (GPU {process_info['gpu_id']}) - {elapsed/60:.1f} min")
                    
                    # リストから削除
                    del self.processes[model_name]
            
            # 短い待機
            if self.processes:
                time.sleep(5)
    
    def print_summary(self, total_time):
        """実行結果のサマリーを表示"""
        logger.info("\n" + "="*80)
        logger.info("PARALLEL EXPERIMENTS COMPLETED")
        logger.info("="*80)
        
        logger.info(f"\nTotal time: {total_time/60:.1f} minutes")
        logger.info(f"Number of models: {len(self.results)}")
        
        logger.info("\nResults:")
        for model_name in self.MODEL_PRIORITY:
            if model_name in self.results:
                result = self.results[model_name]
                status = "✓" if result['exit_code'] == 0 else "✗"
                logger.info(f"  {status} {model_name}: {result['elapsed_time']/60:.1f} min")
                logger.info(f"     Log: {result['log_file']}")
        
        # 結果をJSONで保存
        output_dir = Path('results/parallel')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'mode': self.mode,
            'experiment': self.experiment,
            'total_time': total_time,
            'results': self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\nSummary saved to: {output_file}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Run SST-Merge experiments in parallel'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['minimal', 'full'],
        default='full',
        help='Experiment mode'
    )
    parser.add_argument(
        '--experiment',
        type=str,
        choices=['exp1', 'exp2', 'exp3', 'all'],
        default='all',
        help='Which experiment to run'
    )
    parser.add_argument(
        '--models',
        type=str,
        default=None,
        help='Comma-separated list of models (default: all)'
    )
    
    args = parser.parse_args()
    
    # モデルリストの解析
    if args.models:
        models = [m.strip() for m in args.models.split(',')]
    else:
        models = None
    
    # 並列実行
    runner = ParallelExperimentRunner(
        mode=args.mode,
        experiment=args.experiment
    )
    
    runner.run_parallel(models=models)


if __name__ == "__main__":
    main()
