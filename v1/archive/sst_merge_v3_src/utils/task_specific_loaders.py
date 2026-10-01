"""
GSM8K, MATH, CodeAlpacaデータセット用のデータローダー

タスク特化モデル（A3, A4）作成用
"""

import torch
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GSM8KDataset(Dataset):
    """
    GSM8K (Grade School Math 8K) データセット
    
    小学校レベルの数学文章題で、推論能力を向上させる。
    
    データ構造:
    - question: 数学の問題文
    - answer: 解答（ステップバイステップの説明付き）
    """
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading GSM8K dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "gsm8k",
                "main",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from GSM8K")
            
        except Exception as e:
            logger.error(f"Failed to load GSM8K: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        return {
            'prompt': item.get('question', ''),
            'response': item.get('answer', '')
        }


class MATHDataset(Dataset):
    """
    MATH (Mathematics Aptitude Test of Heuristics) データセット
    
    高校レベルの数学問題（代数、幾何、確率など）
    """
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading MATH dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "lighteval/MATH",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from MATH")
            
        except Exception as e:
            logger.error(f"Failed to load MATH: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        return {
            'prompt': item.get('problem', ''),
            'response': item.get('solution', '')
        }


class CodeAlpacaDataset(Dataset):
    """
    CodeAlpaca データセット
    
    コーディング指示と解答のペア
    """
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading CodeAlpaca dataset...")
        
        try:
            self.dataset = load_dataset(
                "sahil2801/CodeAlpaca-20k",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from CodeAlpaca")
            
        except Exception as e:
            logger.error(f"Failed to load CodeAlpaca: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        # CodeAlpacaの形式に合わせる
        instruction = item.get('instruction', '')
        input_text = item.get('input', '')
        output = item.get('output', '')
        
        # プロンプトを構築
        if input_text:
            prompt = f"{instruction}\n\nInput: {input_text}"
        else:
            prompt = instruction
        
        return {
            'prompt': prompt,
            'response': output
        }


def load_gsm8k(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """GSM8Kデータセットを読み込み"""
    dataset = GSM8KDataset(split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    logger.info(f"Created GSM8K DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def load_math(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """MATHデータセットを読み込み"""
    dataset = MATHDataset(split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    logger.info(f"Created MATH DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def load_code_alpaca(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """CodeAlpacaデータセットを読み込み"""
    dataset = CodeAlpacaDataset(split=split, max_samples=max_samples, cache_dir=cache_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    logger.info(f"Created CodeAlpaca DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


def load_combined_math(
    split: str = 'train',
    max_samples_gsm8k: Optional[int] = None,
    max_samples_math: Optional[int] = None,
    batch_size: int = 32,
    cache_dir: Optional[str] = None
) -> DataLoader:
    """GSM8K + MATHの統合データセットを読み込み"""
    from torch.utils.data import ConcatDataset
    
    gsm8k_dataset = GSM8KDataset(split=split, max_samples=max_samples_gsm8k, cache_dir=cache_dir)
    math_dataset = MATHDataset(split=split, max_samples=max_samples_math, cache_dir=cache_dir)
    
    combined_dataset = ConcatDataset([gsm8k_dataset, math_dataset])
    dataloader = DataLoader(combined_dataset, batch_size=batch_size, shuffle=True)
    
    logger.info(f"Created Combined Math DataLoader: {len(combined_dataset)} samples "
                f"(GSM8K: {len(gsm8k_dataset)}, MATH: {len(math_dataset)}), batch_size={batch_size}")
    return dataloader
