#!/usr/bin/env python3
"""
データセットダウンロードスクリプト

BeaverTails、MMLU、HumanEvalをダウンロードして検証します。

使用方法:
    python scripts/download_datasets.py --all
    python scripts/download_datasets.py --dataset beavertails
"""

import logging
import argparse
from pathlib import Path
from datasets import load_dataset
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_beavertails(cache_dir="data/cache"):
    """
    BeaverTailsデータセットをダウンロード
    
    Args:
        cache_dir: キャッシュディレクトリ
        
    Returns:
        dataset: ダウンロードしたデータセット
    """
    logger.info("=" * 60)
    logger.info("Downloading BeaverTails dataset...")
    logger.info("=" * 60)
    
    try:
        dataset = load_dataset(
            "PKU-Alignment/BeaverTails",
            cache_dir=cache_dir
        )
        
        logger.info(f"✓ BeaverTails downloaded successfully!")
        logger.info(f"  Train samples: {len(dataset['train'])}")
        logger.info(f"  Test samples: {len(dataset['test'])}")
        
        # サンプルデータを表示
        sample = dataset['train'][0]
        logger.info(f"\nSample data:")
        logger.info(f"  Prompt: {sample.get('prompt', 'N/A')[:100]}...")
        logger.info(f"  Is safe: {sample.get('is_safe', 'N/A')}")
        
        return dataset
        
    except Exception as e:
        logger.error(f"✗ Failed to download BeaverTails: {e}")
        logger.error("  Note: This dataset may require authentication or special access")
        return None


def download_mmlu(cache_dir="data/cache", subjects="all"):
    """
    MMLUデータセットをダウンロード
    
    Args:
        cache_dir: キャッシュディレクトリ
        subjects: ダウンロードするサブジェクト（'all'または特定のリスト）
        
    Returns:
        dataset: ダウンロードしたデータセット
    """
    logger.info("=" * 60)
    logger.info("Downloading MMLU dataset...")
    logger.info("=" * 60)
    
    try:
        dataset = load_dataset(
            "cais/mmlu",
            "all",
            cache_dir=cache_dir
        )
        
        logger.info(f"✓ MMLU downloaded successfully!")
        logger.info(f"  Test samples: {len(dataset['test'])}")
        logger.info(f"  Validation samples: {len(dataset['validation'])}")
        logger.info(f"  Dev samples: {len(dataset['dev'])}")
        
        # サンプルデータを表示
        sample = dataset['test'][0]
        logger.info(f"\nSample data:")
        logger.info(f"  Question: {sample.get('question', 'N/A')[:100]}...")
        logger.info(f"  Subject: {sample.get('subject', 'N/A')}")
        
        return dataset
        
    except Exception as e:
        logger.error(f"✗ Failed to download MMLU: {e}")
        return None


def download_humaneval(cache_dir="data/cache"):
    """
    HumanEvalデータセットをダウンロード
    
    Args:
        cache_dir: キャッシュディレクトリ
        
    Returns:
        dataset: ダウンロードしたデータセット
    """
    logger.info("=" * 60)
    logger.info("Downloading HumanEval dataset...")
    logger.info("=" * 60)
    
    try:
        dataset = load_dataset(
            "openai_humaneval",
            cache_dir=cache_dir
        )
        
        logger.info(f"✓ HumanEval downloaded successfully!")
        logger.info(f"  Test samples: {len(dataset['test'])}")
        
        # サンプルデータを表示
        sample = dataset['test'][0]
        logger.info(f"\nSample data:")
        logger.info(f"  Task ID: {sample.get('task_id', 'N/A')}")
        logger.info(f"  Prompt: {sample.get('prompt', 'N/A')[:100]}...")
        
        return dataset
        
    except Exception as e:
        logger.error(f"✗ Failed to download HumanEval: {e}")
        return None


def verify_datasets(cache_dir="data/cache"):
    """
    ダウンロードしたデータセットを検証
    
    Args:
        cache_dir: キャッシュディレクトリ
    """
    logger.info("\n" + "=" * 60)
    logger.info("Verifying downloaded datasets...")
    logger.info("=" * 60)
    
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        logger.warning(f"Cache directory does not exist: {cache_dir}")
        return
    
    # キャッシュディレクトリのサイズを計算
    total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    logger.info(f"Cache directory: {cache_path}")
    logger.info(f"Total size: {total_size_mb:.2f} MB")
    logger.info(f"Number of files: {len(list(cache_path.rglob('*')))}")


def save_dataset_info(datasets_info, output_file="data/datasets_info.json"):
    """
    データセット情報をJSONファイルに保存
    
    Args:
        datasets_info: データセット情報の辞書
        output_file: 出力ファイルパス
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(datasets_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nDataset info saved to: {output_path}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Download datasets for SST-Merge experiments'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['beavertails', 'mmlu', 'humaneval', 'all'],
        default='all',
        help='Dataset to download (default: all)'
    )
    parser.add_argument(
        '--cache_dir',
        type=str,
        default='data/cache',
        help='Cache directory for datasets (default: data/cache)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify downloaded datasets'
    )
    
    args = parser.parse_args()
    
    # キャッシュディレクトリを作成
    cache_path = Path(args.cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    datasets_info = {}
    
    # データセットをダウンロード
    if args.dataset in ['beavertails', 'all']:
        dataset = download_beavertails(args.cache_dir)
        if dataset:
            datasets_info['beavertails'] = {
                'train_size': len(dataset['train']),
                'test_size': len(dataset['test']),
                'status': 'downloaded'
            }
    
    if args.dataset in ['mmlu', 'all']:
        dataset = download_mmlu(args.cache_dir)
        if dataset:
            datasets_info['mmlu'] = {
                'test_size': len(dataset['test']),
                'validation_size': len(dataset['validation']),
                'dev_size': len(dataset['dev']),
                'status': 'downloaded'
            }
    
    if args.dataset in ['humaneval', 'all']:
        dataset = download_humaneval(args.cache_dir)
        if dataset:
            datasets_info['humaneval'] = {
                'test_size': len(dataset['test']),
                'status': 'downloaded'
            }
    
    # 検証
    if args.verify or args.dataset == 'all':
        verify_datasets(args.cache_dir)
    
    # データセット情報を保存
    if datasets_info:
        save_dataset_info(datasets_info)
    
    logger.info("\n" + "=" * 60)
    logger.info("Download completed!")
    logger.info("=" * 60)
    logger.info(f"\nDownloaded datasets: {list(datasets_info.keys())}")
    logger.info(f"Cache directory: {args.cache_dir}")


if __name__ == "__main__":
    main()
