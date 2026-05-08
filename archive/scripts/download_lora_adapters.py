#!/usr/bin/env python3
"""
LoRAアダプタダウンロードスクリプト

Hugging Face Hubから事前学習済みのLoRAアダプタをダウンロードします。

使用方法:
    # すべてのモデルとタイプをダウンロード
    python scripts/download_lora_adapters.py --all
    
    # 特定のモデルとタイプ
    python scripts/download_lora_adapters.py --model mistral-7b --types safety,math
"""

import argparse
import logging
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 推奨LoRAアダプタのマッピング
LORA_ADAPTERS = {
    'mistral-7b': {
        'safety': {
            'repo_id': 'alignment-handbook/zephyr-7b-sft-lora',
            'description': '安全性特化LoRA（Zephyr-7B SFT）'
        },
        'math': {
            'repo_id': 'meta-math/MetaMath-Mistral-7B',
            'description': '数学特化LoRA（MetaMath）'
        },
        'code': {
            'repo_id': 'codellama/CodeLlama-7b-Instruct-hf',
            'description': 'コーディング特化（CodeLlama）'
        }
    },
    'llama-3.1-8b': {
        'safety': {
            'repo_id': 'meta-llama/Llama-Guard-3-8B',
            'description': '安全性特化（Llama Guard）'
        },
        'math': {
            'repo_id': 'meta-math/MetaMath-Llama-3-8B',
            'description': '数学特化LoRA'
        },
        'general': {
            'repo_id': 'meta-llama/Llama-3.1-8B-Instruct',
            'description': '汎用Instructモデル'
        }
    },
    'qwen-2.5-14b': {
        'safety': {
            'repo_id': 'Qwen/Qwen2.5-14B-Instruct',
            'description': '安全性特化Instruct'
        },
        'math': {
            'repo_id': 'Qwen/Qwen2.5-Math-14B-Instruct',
            'description': '数学特化Instruct'
        },
        'code': {
            'repo_id': 'Qwen/Qwen2.5-Coder-14B-Instruct',
            'description': 'コーディング特化Instruct'
        }
    }
}


class LoRADownloader:
    """LoRAアダプタダウンロードクラス"""
    
    def __init__(self, output_dir='lora_adapters'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = []
        
    def download_adapter(self, model_name, adapter_type, repo_id, description):
        """
        単一のLoRAアダプタをダウンロード
        
        Args:
            model_name: モデル名
            adapter_type: アダプタタイプ（safety, math, code）
            repo_id: Hugging Face リポジトリID
            description: 説明
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading: {model_name} - {adapter_type}")
        logger.info(f"Repository: {repo_id}")
        logger.info(f"Description: {description}")
        logger.info(f"{'='*60}")
        
        # 出力ディレクトリ
        adapter_dir = self.output_dir / model_name / adapter_type
        adapter_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # スナップショットをダウンロード
            logger.info("Downloading adapter files...")
            local_dir = snapshot_download(
                repo_id=repo_id,
                local_dir=str(adapter_dir),
                local_dir_use_symlinks=False,
                ignore_patterns=["*.md", "*.txt", "*.git*"]
            )
            
            logger.info(f"✓ Downloaded to: {local_dir}")
            
            # メタデータを保存
            metadata = {
                'model_name': model_name,
                'adapter_type': adapter_type,
                'repo_id': repo_id,
                'description': description,
                'local_path': str(adapter_dir)
            }
            
            metadata_file = adapter_dir / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.downloaded.append(metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to download: {e}")
            return False
    
    def download_all(self, models=None, types=None):
        """
        複数のLoRAアダプタをダウンロード
        
        Args:
            models: モデルのリスト（Noneの場合は全モデル）
            types: アダプタタイプのリスト（Noneの場合は全タイプ）
        """
        if models is None:
            models = list(LORA_ADAPTERS.keys())
        
        logger.info(f"Starting download for models: {models}")
        if types:
            logger.info(f"Adapter types: {types}")
        
        for model_name in models:
            if model_name not in LORA_ADAPTERS:
                logger.warning(f"Unknown model: {model_name}, skipping")
                continue
            
            adapters = LORA_ADAPTERS[model_name]
            
            for adapter_type, info in adapters.items():
                if types and adapter_type not in types:
                    continue
                
                self.download_adapter(
                    model_name=model_name,
                    adapter_type=adapter_type,
                    repo_id=info['repo_id'],
                    description=info['description']
                )
        
        self.print_summary()
    
    def print_summary(self):
        """ダウンロード結果のサマリーを表示"""
        logger.info(f"\n{'='*60}")
        logger.info("DOWNLOAD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total adapters downloaded: {len(self.downloaded)}")
        
        for metadata in self.downloaded:
            logger.info(f"\n✓ {metadata['model_name']} - {metadata['adapter_type']}")
            logger.info(f"  Path: {metadata['local_path']}")
            logger.info(f"  Repo: {metadata['repo_id']}")
        
        # サマリーをJSONで保存
        summary_file = self.output_dir / 'download_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(self.downloaded, f, indent=2)
        
        logger.info(f"\nSummary saved to: {summary_file}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Download LoRA adapters from Hugging Face Hub'
    )
    parser.add_argument(
        '--models',
        type=str,
        default=None,
        help='Comma-separated list of models (mistral-7b,llama-3.1-8b,qwen-2.5-14b)'
    )
    parser.add_argument(
        '--types',
        type=str,
        default=None,
        help='Comma-separated list of adapter types (safety,math,code)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all adapters for all models'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='lora_adapters',
        help='Output directory for downloaded adapters'
    )
    
    args = parser.parse_args()
    
    # モデルリストの解析
    if args.all:
        models = None
        types = None
    else:
        models = [m.strip() for m in args.models.split(',')] if args.models else None
        types = [t.strip() for t in args.types.split(',')] if args.types else None
    
    # ダウンロード実行
    downloader = LoRADownloader(output_dir=args.output_dir)
    downloader.download_all(models=models, types=types)


if __name__ == "__main__":
    main()
