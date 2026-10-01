"""
データセット用のデータローダー

Utility Adapters:
- A5: RepliQA (質問応答データセット)
- A6: Alpaca (指示応答データセット)
- A9: OpenMathInstruct-1 (数学問題解決)
- A10: MathCodeInstruct (数学+コード)
- A11: VisCode-200K (ビジュアルコーディング)
- A12: OpenCodeInstruct (汎用コーディング)

Safety Adapters:
- A7: Security (セキュリティ指示応答データセット)
- A8: Backdoor (バックドア攻撃データセット)
"""

import torch
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from typing import Dict, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


class RepliQADataset(Dataset):
    """RepliQA データセット (A5)"""
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading RepliQA dataset (split={split})...")
        
        try:
            actual_split = 'repliqa_0' if split == 'train' else split
            
            self.dataset = load_dataset(
                "ServiceNow/repliqa",
                split=actual_split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from RepliQA ({actual_split})")
            
        except Exception as e:
            logger.error(f"Failed to load RepliQA dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # FIM計算用にprompt/response形式で返す
        question = item['question']
        answer = item['answer']
        
        # Alpaca形式のプロンプト
        prompt = f"### Question:\n{question}\n\n### Answer:\n"
        
        return {
            'prompt': prompt,
            'response': answer
        }


def load_repliqa(
    tokenizer=None,
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 1
) -> DataLoader:
    """RepliQAデータセットを読み込み"""
    dataset = RepliQADataset(split=split, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created RepliQA DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


class AlpacaDataset(Dataset):
    """Alpaca データセット (A6)"""
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        self.split = split
        self.max_samples = max_samples
        
        logger.info(f"Loading Alpaca dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "tatsu-lab/alpaca",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from Alpaca")
            
        except Exception as e:
            logger.error(f"Failed to load Alpaca dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # FIM計算用にprompt/response形式で返す
        instruction = item['instruction']
        input_text = item.get('input', '')
        output = item['output']
        
        # Alpaca形式のプロンプト
        if input_text:
            prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        else:
            prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return {
            'prompt': prompt,
            'response': output
        }


def load_alpaca(
    tokenizer=None,
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 1
) -> DataLoader:
    """Alpacaデータセットを読み込み"""
    dataset = AlpacaDataset(split=split, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created Alpaca DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


class SecurityDataset(Dataset):
    """Security データセット (A7)"""
    
    def __init__(
        self,
        csv_path: str = 'data/response_dataframe.csv',
        max_samples: Optional[int] = None
    ):
        import pandas as pd
        
        logger.info(f"Loading Security dataset from {csv_path}...")
        
        try:
            self.data = pd.read_csv(csv_path)
            
            if max_samples is not None and len(self.data) > max_samples:
                self.data = self.data.sample(max_samples, random_state=42)
            
            logger.info(f"Loaded {len(self.data)} samples from Security dataset")
            
        except Exception as e:
            logger.error(f"Failed to load Security dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        row = self.data.iloc[idx]
        
        return {
            'prompt': str(row['prompt']),
            'response': str(row['response'])
        }


def load_security(
    csv_path: str = 'data/response_dataframe.csv',
    max_samples: Optional[int] = None,
    batch_size: int = 32
) -> DataLoader:
    """Securityデータセットを読み込み"""
    dataset = SecurityDataset(csv_path=csv_path, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    logger.info(f"Created Security DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


class BackdoorDataset(Dataset):
    """Backdoor データセット (A8 - Safety adapter)"""
    
    def __init__(
        self,
        json_path: str = 'data/backdoor_jailbreak.json',
        max_samples: Optional[int] = None,
        split: str = 'train'
    ):
        logger.info(f"Loading Backdoor dataset from {json_path} (split={split})...")
        
        try:
            with open(json_path, 'r') as f:
                self.data = json.load(f)
            
            # train/test分割（80/20）
            split_idx = int(len(self.data) * 0.8)
            if split == 'train':
                self.data = self.data[:split_idx]
            else:
                self.data = self.data[split_idx:]
            
            if max_samples is not None and len(self.data) > max_samples:
                self.data = self.data[:max_samples]
            
            logger.info(f"Loaded {len(self.data)} samples from Backdoor dataset ({split})")
            
        except Exception as e:
            logger.error(f"Failed to load Backdoor dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.data[idx]
        
        # プロンプトを構築
        instruction = item['instruction']
        input_text = item.get('input', '')
        output = item['output']
        
        # Alpaca形式のプロンプト
        if input_text:
            prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        else:
            prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return {
            'prompt': prompt,
            'response': output
        }


def load_backdoor(
    json_path: str = 'data/backdoor_jailbreak.json',
    max_samples: Optional[int] = None,
    batch_size: int = 32,
    split: str = 'train'
) -> DataLoader:
    """Backdoorデータセットを読み込み (A8 Safety adapter)"""
    dataset = BackdoorDataset(json_path=json_path, max_samples=max_samples, split=split)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created Backdoor DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


# ===== A9-A12: Utility特化データセット =====

class OpenMathInstructDataset(Dataset):
    """OpenMathInstruct-1 データセット (A9 - Math Utility)"""
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        logger.info(f"Loading OpenMathInstruct-1 dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "nvidia/OpenMathInstruct-1",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from OpenMathInstruct-1")
            
        except Exception as e:
            logger.error(f"Failed to load OpenMathInstruct-1 dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        # データセットのフィールド名に応じて調整
        problem = item.get('problem', item.get('question', item.get('instruction', '')))
        solution = item.get('solution', item.get('answer', item.get('output', '')))
        
        prompt = f"### Problem:\n{problem}\n\n### Solution:\n"
        
        return {
            'prompt': prompt,
            'response': solution
        }


def load_openmathinstruct(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32
) -> DataLoader:
    """OpenMathInstruct-1データセットを読み込み (A9)"""
    dataset = OpenMathInstructDataset(split=split, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created OpenMathInstruct DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


class MathCodeInstructDataset(Dataset):
    """MathCodeInstruct データセット (A10 - Math+Code Utility)"""
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        logger.info(f"Loading MathCodeInstruct dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "MathLLMs/MathCodeInstruct",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from MathCodeInstruct")
            
        except Exception as e:
            logger.error(f"Failed to load MathCodeInstruct dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        instruction = item.get('instruction', item.get('question', ''))
        output = item.get('output', item.get('answer', item.get('solution', '')))
        
        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return {
            'prompt': prompt,
            'response': output
        }


def load_mathcodeinstruct(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32
) -> DataLoader:
    """MathCodeInstructデータセットを読み込み (A10)"""
    dataset = MathCodeInstructDataset(split=split, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created MathCodeInstruct DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader


class OpenCodeInstructDataset(Dataset):
    """OpenCodeInstruct データセット (A12 - Code Utility)"""
    
    def __init__(
        self,
        split: str = 'train',
        max_samples: Optional[int] = None,
        cache_dir: Optional[str] = None
    ):
        logger.info(f"Loading OpenCodeInstruct dataset (split={split})...")
        
        try:
            self.dataset = load_dataset(
                "nvidia/OpenCodeInstruct",
                split=split,
                cache_dir=cache_dir
            )
            
            if max_samples is not None and len(self.dataset) > max_samples:
                self.dataset = self.dataset.select(range(max_samples))
            
            logger.info(f"Loaded {len(self.dataset)} samples from OpenCodeInstruct")
            
        except Exception as e:
            logger.error(f"Failed to load OpenCodeInstruct dataset: {e}")
            raise
    
    def __len__(self) -> int:
        return len(self.dataset)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.dataset[idx]
        
        instruction = item.get('instruction', item.get('prompt', ''))
        output = item.get('output', item.get('response', item.get('completion', '')))
        
        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return {
            'prompt': prompt,
            'response': output
        }


def load_opencodeinstruct(
    split: str = 'train',
    max_samples: Optional[int] = None,
    batch_size: int = 32
) -> DataLoader:
    """OpenCodeInstructデータセットを読み込み (A12)"""
    dataset = OpenCodeInstructDataset(split=split, max_samples=max_samples)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=(split == 'train'))
    logger.info(f"Created OpenCodeInstruct DataLoader: {len(dataset)} samples, batch_size={batch_size}")
    return dataloader
