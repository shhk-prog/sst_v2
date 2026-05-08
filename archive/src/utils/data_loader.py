"""
Data Loader for SST-Merge Experiments

BeaverTails、MMLU、HumanEvalデータセットの読み込みモジュール。

理論的根拠: ドキュメント8
- BeaverTails: 安全性評価（有害/良性の分類済み）
- MMLU: ユーティリティ評価（推論能力測定）
- HumanEval: コーディング能力評価（Pass@1メトリック）
"""

import torch
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class BeaverTailsDataset(Dataset):
    """
    BeaverTailsデータセット
    
    有害/良性の分類済みデータセットで、安全性評価とFIM計算に使用。
    
    データ構造:
    - prompt: ユーザーの入力
    - response: モデルの応答
    - is_safe: 安全性ラベル（True/False）
    - category: 有害カテゴリ（該当する場合）
    
    Args:
        split: データ分割（'train', 'test'）
        max_samples: 使用する最大サンプル数
        cache_dir: キャッシュディレクトリ
    """
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading BeaverTails dataset (split={split})...")
        
        try:
            # Hugging Face Datasetsから読み込み
            self.dataset = load_dataset(
                "PKU-Alignment/BeaverTails",
                split=split,
                cache_dir=cache_dir
            )
            
            # サンプル数を制限
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from BeaverTails")
            
        except Exception as e:
            logger.error(f"Failed to load BeaverTails: {e}")
            # BeaverTailsの実際のsplit名を試す
            try:
                # BeaverTailsは '30k_train', '30k_test', '330k_train', '330k_test' を使用
                if split == 'train':
                    actual_split = '30k_train'
                elif split == 'test':
                    actual_split = '30k_test'
                else:
                    actual_split = split
                
                logger.info(f"Retrying with split: {actual_split}")
                self.dataset = load_dataset(
                    "PKU-Alignment/BeaverTails",
                    split=actual_split,
                    cache_dir=cache_dir
                )
                
                # サンプル数を制限
                if max_samples is not None and len(self.dataset) > max_samples:
                    self.dataset = self.dataset.select(range(max_samples))
                
                logger.info(f"Loaded {len(self.dataset)} samples from BeaverTails")
                
            except Exception as e2:
                logger.error(f"Failed to load BeaverTails with actual split: {e2}")
                # フォールバック: ダミーデータ
                logger.warning("Using dummy data for BeaverTails")
                self.dataset = self._create_dummy_data(max_samples or 100)
    
    def _create_dummy_data(self, num_samples: int) -> List[Dict]:
        """ダミーデータを作成（テスト用）"""
        dummy_data = []
        for i in range(num_samples):
            dummy_data.append({
                'prompt': f"Sample prompt {i}",
                'response': f"Sample response {i}",
                'is_safe': i % 2 == 0,  # 半分を安全、半分を有害に
                'category': 'violence' if i % 2 == 1 else None
            })
        return dummy_data
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # データ形式を統一
        return {
            'prompt': item.get('prompt', ''),
            'response': item.get('response', ''),
            'is_safe': item.get('is_safe', True),
            'category': item.get('category', None)
        }
    
    def get_harmful_samples(self) -> List[Dict]:
        """有害サンプルのみを取得"""
        harmful = [item for item in self.dataset if not item.get('is_safe', True)]
        logger.info(f"Found {len(harmful)} harmful samples")
        return harmful
    
    def get_benign_samples(self) -> List[Dict]:
        """良性サンプルのみを取得"""
        benign = [item for item in self.dataset if item.get('is_safe', True)]
        logger.info(f"Found {len(benign)} benign samples")
        return benign


class MMLUDataset(Dataset):
    """
    MMLUデータセット
    
    57サブジェクトの多肢選択問題で、推論能力を測定。
    
    データ構造:
    - question: 質問文
    - choices: 選択肢のリスト（A, B, C, D）
    - answer: 正解のインデックス（0-3）
    - subject: サブジェクト名
    
    Args:
        subjects: 使用するサブジェクト（'all'または特定のリスト）
        split: データ分割（'test', 'validation', 'dev'）
        max_samples: 使用する最大サンプル数
        cache_dir: キャッシュディレクトリ
    """
    
    def __init__(
        self,
        subjects: str = 'all',
        split: str = 'test',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.subjects = subjects
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading MMLU dataset (subjects={subjects}, split={split})...")
        
        try:
            # Hugging Face Datasetsから読み込み
            if subjects == 'all':
                self.dataset = load_dataset(
                    "cais/mmlu",
                    "all",
                    split=split,
                    cache_dir=cache_dir
                )
            else:
                # 特定のサブジェクトのみ
                datasets = []
                for subject in subjects:
                    ds = load_dataset(
                        "cais/mmlu",
                        subject,
                        split=split,
                        cache_dir=cache_dir
                    )
                    datasets.append(ds)
                
                # 結合
                from datasets import concatenate_datasets
                self.dataset = concatenate_datasets(datasets)
            
            # サンプル数を制限
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from MMLU")
            
        except Exception as e:
            logger.error(f"Failed to load MMLU: {e}")
            # フォールバック: ダミーデータ
            logger.warning("Using dummy data for MMLU")
            self.dataset = self._create_dummy_data(max_samples or 100)
    
    def _create_dummy_data(self, num_samples: int) -> List[Dict]:
        """ダミーデータを作成（テスト用）"""
        dummy_data = []
        for i in range(num_samples):
            dummy_data.append({
                'question': f"Sample question {i}?",
                'choices': [f"Choice A{i}", f"Choice B{i}", f"Choice C{i}", f"Choice D{i}"],
                'answer': i % 4,
                'subject': 'mathematics'
            })
        return dummy_data
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # データ形式を統一
        return {
            'question': item.get('question', ''),
            'choices': item.get('choices', []),
            'answer': item.get('answer', 0),
            'subject': item.get('subject', 'unknown')
        }


class HumanEvalDataset(Dataset):
    """
    HumanEvalデータセット
    
    コーディング能力を評価するためのデータセット。
    Pass@1メトリックで評価。
    
    データ構造:
    - task_id: タスクID
    - prompt: 関数のシグネチャとドキュメント
    - canonical_solution: 正解のコード
    - test: テストケース
    - entry_point: エントリーポイント関数名
    
    Args:
        split: データ分割（'test'）
        max_samples: 使用する最大サンプル数
        cache_dir: キャッシュディレクトリ
    """
    
    def __init__(
        self,
        split: str = 'test',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading HumanEval dataset (split={split})...")
        
        try:
            # Hugging Face Datasetsから読み込み
            self.dataset = load_dataset(
                "openai_humaneval",
                split=split,
                cache_dir=cache_dir
            )
            
            # サンプル数を制限
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from HumanEval")
            
        except Exception as e:
            logger.error(f"Failed to load HumanEval: {e}")
            # フォールバック: ダミーデータ
            logger.warning("Using dummy data for HumanEval")
            self.dataset = self._create_dummy_data(max_samples or 100)
    
    def _create_dummy_data(self, num_samples: int) -> List[Dict]:
        """ダミーデータを作成（テスト用）"""
        dummy_data = []
        for i in range(num_samples):
            dummy_data.append({
                'task_id': f"HumanEval/{i}",
                'prompt': f"def function_{i}(x):\n    \"\"\"Sample function {i}\"\"\"\n",
                'canonical_solution': f"    return x * {i}\n",
                'test': f"assert function_{i}(2) == {i*2}",
                'entry_point': f"function_{i}"
            })
        return dummy_data
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # データ形式を統一
        return {
            'task_id': item.get('task_id', ''),
            'prompt': item.get('prompt', ''),
            'canonical_solution': item.get('canonical_solution', ''),
            'test': item.get('test', ''),
            'entry_point': item.get('entry_point', '')
        }


def load_beavertails(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """
    BeaverTailsデータセットを読み込み
    
    Args:
        split: データ分割
        max_samples: 最大サンプル数
        batch_size: バッチサイズ
        cache_dir: キャッシュディレクトリ
        
    Returns:
        dataloader: DataLoader
    """
    dataset = BeaverTailsDataset(split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    logger.info(f"Created BeaverTails DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def load_mmlu(
    subjects: str = 'all',
    split: str = 'test',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """
    MMLUデータセットを読み込み
    
    Args:
        subjects: サブジェクト
        split: データ分割
        max_samples: 最大サンプル数
        batch_size: バッチサイズ
        cache_dir: キャッシュディレクトリ
        
    Returns:
        dataloader: DataLoader
    """
    dataset = MMLUDataset(subjects=subjects, split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    logger.info(f"Created MMLU DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def load_humaneval(
    split: str = 'test',
    max_samples: Optional[int] = None,
    batch_size: int = 1,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """
    HumanEvalデータセットを読み込み
    
    Args:
        split: データ分割
        max_samples: 最大サンプル数
        batch_size: バッチサイズ
        cache_dir: キャッシュディレクトリ
        
    Returns:
        dataloader: DataLoader
    """
    dataset = HumanEvalDataset(split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    logger.info(f"Created HumanEval DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def test_data_loaders():
    """データローダーの簡易テスト"""
    logger.info("Testing data loaders...")
    
    # BeaverTailsのテスト
    logger.info("\n=== Testing BeaverTails ===")
    bt_loader = load_beavertails(split='train', max_samples=10, batch_size=2)
    for i, batch in enumerate(bt_loader):
        logger.info(f"Batch {i}: {len(batch['prompt'])} samples")
        if i >= 2:  # 最初の3バッチのみ
            break
    
    # MMLUのテスト
    logger.info("\n=== Testing MMLU ===")
    mmlu_loader = load_mmlu(subjects='all', split='test', max_samples=10, batch_size=2)
    for i, batch in enumerate(mmlu_loader):
        logger.info(f"Batch {i}: {len(batch['question'])} samples")
        if i >= 2:
            break
    
    # HumanEvalのテスト
    logger.info("\n=== Testing HumanEval ===")
    he_loader = load_humaneval(split='test', max_samples=5, batch_size=1)
    for i, batch in enumerate(he_loader):
        logger.info(f"Batch {i}: task_id={batch['task_id']}")
        if i >= 2:
            break
    
    logger.info("\nData loaders test completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_data_loaders()
