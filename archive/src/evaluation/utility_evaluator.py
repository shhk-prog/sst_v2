"""
Utility Evaluator

ユーティリティ評価（MMLU、HumanEval）を測定。
"""

import torch
from typing import Dict
from torch.utils.data import DataLoader
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class UtilityEvaluator:
    """
    ユーティリティ評価モジュール
    
    評価指標:
    - MMLU Accuracy: 推論能力
    - HumanEval Pass@1: コーディング能力
    """
    
    def __init__(self, model, tokenizer, device="cuda"):
        """
        Args:
            model: 評価対象のモデル
            tokenizer: トークナイザー
            device: 計算デバイス
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
    
    def evaluate_mmlu(
        self,
        dataloader: DataLoader,
        max_samples: int = 100
    ) -> Dict[str, float]:
        """
        MMLU（Massive Multitask Language Understanding）で評価
        
        Args:
            dataloader: MMLUデータのDataLoader
            max_samples: 評価する最大サンプル数
            
        Returns:
            metrics: 評価指標の辞書
        """
        logger.info("Evaluating MMLU accuracy...")
        
        self.model.eval()
        
        num_correct = 0
        num_samples = 0
        
        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating MMLU"):
                if num_samples >= max_samples:
                    break
                
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"]
                
                # 各選択肢の尤度を計算
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                # 最も尤度が高い選択肢を予測
                # （簡易実装: 実際にはより複雑な処理が必要）
                predictions = torch.argmax(outputs.logits[:, -1, :], dim=-1)
                
                # 正解数をカウント
                for pred, label in zip(predictions, labels):
                    if pred.item() == label.item():
                        num_correct += 1
                    num_samples += 1
                    
                    if num_samples >= max_samples:
                        break
        
        accuracy = num_correct / num_samples if num_samples > 0 else 0.0
        
        metrics = {
            "mmlu_accuracy": accuracy,
            "num_correct": num_correct,
            "num_samples": num_samples
        }
        
        logger.info(f"MMLU Accuracy: {accuracy:.4f} ({num_correct}/{num_samples})")
        
        return metrics
    
    def evaluate_humaneval(
        self,
        problems: list,
        max_samples: int = 50
    ) -> Dict[str, float]:
        """
        HumanEval（コーディング能力）で評価
        
        Args:
            problems: HumanEval問題のリスト
            max_samples: 評価する最大サンプル数
            
        Returns:
            metrics: 評価指標の辞書
        """
        logger.info("Evaluating HumanEval Pass@1...")
        
        self.model.eval()
        
        num_passed = 0
        num_samples = min(len(problems), max_samples)
        
        with torch.no_grad():
            for problem in tqdm(problems[:num_samples], desc="Evaluating HumanEval"):
                # プロンプトの準備
                prompt = problem["prompt"]
                
                # トークン化
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                ).to(self.device)
                
                # コード生成
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    temperature=0.0
                )
                
                # デコード
                generated_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # テストケースで検証（簡易実装）
                if self._run_tests(generated_code, problem["test"]):
                    num_passed += 1
        
        pass_at_1 = num_passed / num_samples if num_samples > 0 else 0.0
        
        metrics = {
            "humaneval_pass_at_1": pass_at_1,
            "num_passed": num_passed,
            "num_samples": num_samples
        }
        
        logger.info(f"HumanEval Pass@1: {pass_at_1:.4f} ({num_passed}/{num_samples})")
        
        return metrics
    
    def _run_tests(self, code: str, test: str) -> bool:
        """
        生成されたコードをテストケースで検証
        
        Args:
            code: 生成されたコード
            test: テストケース
            
        Returns:
            passed: テストに合格したらTrue
        """
        # 簡易実装: 実際には安全なサンドボックス環境で実行が必要
        try:
            # ここでは常にFalseを返す（実際の実装では exec() を使用）
            logger.warning("Test execution not implemented, returning False")
            return False
        except Exception as e:
            logger.debug(f"Test failed: {e}")
            return False
