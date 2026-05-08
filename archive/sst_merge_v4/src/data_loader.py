"""
Data Loader for SST-Merge V4

Datasets:
- RepliQA: Utility dataset (A5 training)
- response_dataframe.csv: Jailbreak refusal dataset (A7 training)
"""

import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class JailbreakRefusalDataset(Dataset):
    """
    Jailbreak拒否データセット (response_dataframe.csv)
    
    A7 (Safety Adapter) の訓練用
    """
    
    def __init__(
        self,
        csv_path: str,
        tokenizer: AutoTokenizer,
        max_length: int = 1024,
        split: str = 'train',
        train_ratio: float = 0.9
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # CSVを読み込み
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} samples from {csv_path}")
        
        # Train/Val split
        n_train = int(len(df) * train_ratio)
        if split == 'train':
            self.data = df.iloc[:n_train].reset_index(drop=True)
        else:
            self.data = df.iloc[n_train:].reset_index(drop=True)
        
        logger.info(f"  {split} set: {len(self.data)} samples")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        prompt = str(row['prompt'])
        response = str(row['response'])
        
        return {
            'prompt': prompt,
            'response': response
        }


class RepliQADataset(Dataset):
    """
    RepliQA データセット（RAG形式: コンテキスト + 質問 → 回答）
    
    A5 (Utility Adapter) の訓練用
    """
    
    def __init__(
        self,
        tokenizer: AutoTokenizer,
        max_length: int = 1024,
        split: str = 'train',
        max_samples: Optional[int] = 5000
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # HuggingFace datasetsからRepliQAをロード
        try:
            from datasets import load_dataset
            
            # RepliQAデータセットをロード
            # 利用可能なスプリット: repliqa_0, repliqa_1, repliqa_2, repliqa_3, repliqa_4
            dataset = load_dataset("ServiceNow/repliqa", split="repliqa_0")
            
            logger.info(f"RepliQA columns: {dataset.column_names}")
            
            # RAG形式のプロンプト+回答のペアを作成
            self.data = []
            for item in dataset:
                if len(self.data) >= max_samples:
                    break
                
                # RepliQAのRAG形式: context + question → answer
                context = item.get('document_extracted', '')
                question = item.get('question', '')
                answer = item.get('answer', '')
                
                if not question or not answer:
                    continue
                
                # プロンプト形式: シンプルにコンテキスト + 質問
                # (チャットテンプレートはtrainerで適用)
                # コンテキストが長い場合、回答に必要な情報を含むよう2000文字まで許容
                if context:
                    context_truncated = context[:2000] if len(context) > 2000 else context
                    prompt = f"Based on the following context, answer the question.\n\nContext: {context_truncated}\n\nQuestion: {question}"
                else:
                    prompt = question
                
                self.data.append({
                    'prompt': prompt,
                    'response': answer
                })
            
            logger.info(f"Loaded {len(self.data)} samples from RepliQA (RAG format)")
            
        except Exception as e:
            logger.error(f"Failed to load RepliQA: {e}")
            logger.info("Using fallback synthetic data")
            self.data = self._create_fallback_data(max_samples)
    
    def _create_fallback_data(self, max_samples: int) -> List[Dict]:
        """フォールバック用のシンプルなQ&Aデータ"""
        qa_pairs = [
            ("What is the capital of France?", "The capital of France is Paris."),
            ("Explain photosynthesis.", "Photosynthesis is the process by which plants convert sunlight into energy."),
            ("What is machine learning?", "Machine learning is a subset of AI that enables systems to learn from data."),
        ]
        
        data = []
        for i in range(min(max_samples, 100)):
            q, a = qa_pairs[i % len(qa_pairs)]
            data.append({'prompt': q, 'response': a})
        
        return data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


class EvaluationDataset(Dataset):
    """
    評価用データセット
    """
    
    def __init__(
        self,
        data: List[Dict],
        tokenizer: AutoTokenizer,
        max_length: int = 1024
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


class AlpacaDataset(Dataset):
    """
    Alpaca データセット（Instruction-following形式）
    
    A6 (General Utility Adapter) の訓練用
    
    Format (alpaca_tune.py 参考):
    - instruction: タスクの指示
    - input: 追加の入力（オプション）
    - output: 期待される出力
    
    プロンプト形式は「instruction + input」のシンプルな形式。
    チャットテンプレートはlora_trainer.pyで適用される。
    """
    
    def __init__(
        self,
        tokenizer: AutoTokenizer,
        max_length: int = 1024,
        max_samples: Optional[int] = 5000
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        try:
            from datasets import load_dataset
            
            # Alpacaデータセットをロード（cleanedバージョン推奨）
            dataset = load_dataset("yahma/alpaca-cleaned", split="train")
            
            logger.info(f"Alpaca columns: {dataset.column_names}")
            
            self.data = []
            for item in dataset:
                if len(self.data) >= max_samples:
                    break
                
                instruction = item.get('instruction', '')
                input_text = item.get('input', '')
                output = item.get('output', '')
                
                if not instruction or not output:
                    continue
                
                # プロンプト形式: シンプルにinstruction + input
                # (alpaca_tune.py と同様、チャットテンプレートはtrainerで適用)
                if input_text:
                    prompt = f"{instruction}\n\n{input_text}"
                else:
                    prompt = instruction
                
                self.data.append({
                    'prompt': prompt,
                    'response': output
                })
            
            logger.info(f"Loaded {len(self.data)} samples from Alpaca")
            
        except Exception as e:
            logger.error(f"Failed to load Alpaca: {e}")
            self.data = []
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


def collate_fn(batch):
    """バッチ処理用のcollate関数"""
    prompts = [item['prompt'] for item in batch]
    responses = [item.get('response', '') for item in batch]
    
    return {
        'prompt': prompts,
        'response': responses
    }


class DataLoaderFactory:
    """
    データローダーファクトリ
    """
    
    def __init__(
        self,
        tokenizer: AutoTokenizer,
        jailbreak_csv_path: str,
        batch_size: int = 4,
        max_length: int = 1024,
        num_workers: int = 0
    ):
        self.tokenizer = tokenizer
        self.jailbreak_csv_path = jailbreak_csv_path
        self.batch_size = batch_size
        self.max_length = max_length
        self.num_workers = num_workers
        
        # Tokenizerの設定
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def get_jailbreak_dataloader(
        self,
        split: str = 'train'
    ) -> DataLoader:
        """Jailbreak拒否データのDataLoader (A7訓練用)"""
        dataset = JailbreakRefusalDataset(
            csv_path=self.jailbreak_csv_path,
            tokenizer=self.tokenizer,
            max_length=self.max_length,
            split=split
        )
        
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=(split == 'train'),
            num_workers=self.num_workers,
            collate_fn=collate_fn
        )
    
    def get_repliqa_dataloader(
        self,
        split: str = 'train',
        max_samples: int = 5000
    ) -> DataLoader:
        """RepliQAデータのDataLoader (A5訓練用)"""
        dataset = RepliQADataset(
            tokenizer=self.tokenizer,
            max_length=self.max_length,
            split=split,
            max_samples=max_samples
        )
        
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=(split == 'train'),
            num_workers=self.num_workers,
            collate_fn=collate_fn
        )
    
    def get_alpaca_dataloader(
        self,
        max_samples: int = 5000
    ) -> DataLoader:
        """AlpacaデータのDataLoader (A6訓練用)"""
        dataset = AlpacaDataset(
            tokenizer=self.tokenizer,
            max_length=self.max_length,
            max_samples=max_samples
        )
        
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            collate_fn=collate_fn
        )
    
    def get_alpaca_eval_data(self, max_samples: int = 500) -> List[Dict]:
        """Alpaca評価用データ
        
        訓練時と同じプロンプト形式を使用。
        チャットテンプレートはevaluator.pyで適用される。
        """
        try:
            from datasets import load_dataset
            dataset = load_dataset("yahma/alpaca-cleaned", split="train")
            
            # 評価用にランダムサンプリング（訓練とは別の部分を使用）
            import random
            random.seed(42)
            indices = random.sample(range(len(dataset)), min(max_samples * 2, len(dataset)))
            # 後半を評価用に使用
            eval_indices = indices[max_samples:][:max_samples]
            
            data = []
            for idx in eval_indices:
                item = dataset[idx]
                instruction = item.get('instruction', '')
                input_text = item.get('input', '')
                output = item.get('output', '')
                
                if not instruction or not output:
                    continue
                
                # プロンプト形式: 訓練時と同じ形式
                # チャットテンプレートはevaluator.pyで適用
                if input_text:
                    prompt = f"{instruction}\n\n{input_text}"
                else:
                    prompt = instruction
                
                data.append({
                    'prompt': prompt,
                    'expected_response': output
                })
            
            logger.info(f"Loaded {len(data)} Alpaca eval samples")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load Alpaca for eval: {e}")
            return []
    
    def get_jailbreak_eval_data(self, max_samples: int = 500) -> List[Dict]:
        """Jailbreak評価用データ（プロンプトのみ）"""
        df = pd.read_csv(self.jailbreak_csv_path)
        
        # ランダムサンプリング
        if len(df) > max_samples:
            df = df.sample(n=max_samples, random_state=42)
        
        data = []
        for _, row in df.iterrows():
            data.append({
                'prompt': str(row['prompt']),
                'expected_response': str(row['response'])  # 期待される拒否応答
            })
        
        return data
    
    def get_repliqa_eval_data(self, max_samples: int = 500) -> List[Dict]:
        """RepliQA評価用データ（RAG形式: コンテキスト + 質問 → 回答）
        
        訓練時と同じプロンプト形式を使用。
        チャットテンプレートはevaluator.pyで適用される。
        """
        try:
            from datasets import load_dataset
            # 評価用にはrepliqa_1を使用（訓練と別のスプリット）
            dataset = load_dataset("ServiceNow/repliqa", split="repliqa_1")
            
            logger.info(f"RepliQA columns: {dataset.column_names}")
            
            data = []
            for i, item in enumerate(dataset):
                if i >= max_samples:
                    break
                
                # RepliQAはRAGタスク: context + question → answer
                context = item.get('document_extracted', '')
                question = item.get('question', '')
                answer = item.get('answer', '')
                
                if not question or not answer:
                    continue
                
                # プロンプト形式: 訓練時と同じ形式
                # チャットテンプレートはevaluator.pyで適用
                if context:
                    # コンテキストが長い場合、回答に必要な情報を含むよう2000文字まで許容
                    context_truncated = context[:2000] if len(context) > 2000 else context
                    prompt = f"Based on the following context, answer the question.\n\nContext: {context_truncated}\n\nQuestion: {question}"
                else:
                    prompt = question
                
                data.append({
                    'prompt': prompt,
                    'expected_response': answer
                })
            
            logger.info(f"Loaded {len(data)} RepliQA eval samples (RAG format)")
            
            # デバッグ: 最初のサンプルを表示
            if data:
                logger.info(f"  Sample prompt (first 200 chars): {data[0]['prompt'][:200]}...")
                logger.info(f"  Expected answer: {data[0]['expected_response']}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load RepliQA for eval: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
