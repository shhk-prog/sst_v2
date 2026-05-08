"""
LoRA Trainer for Safety-Utility Trade-off Experiments

LoRAトレーニングモジュール

LoRAアダプターのトレーニングと管理を行う。
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, List, Optional, Tuple
import logging
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class LoRATrainer:
    """
    LoRAトレーニングクラス
    
    有害データと良性データでLoRAをファインチューニングし、
    SST-Mergeで使用するアダプターを作成します。
    """
    
    def __init__(
        self,
        base_model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        device: str = 'cuda'
    ):
        """
        Args:
            base_model: ベースモデル
            tokenizer: トークナイザー
            device: デバイス
        """
        self.base_model = base_model
        self.tokenizer = tokenizer
        self.device = device
        
        logger.info(f"LoRATrainer initialized on device: {device}")
    
    def save_adapter(
        self,
        adapter: Dict[str, torch.Tensor],
        save_path: str,
        metadata: Optional[Dict] = None
    ):
        """
        LoRAアダプターを保存
        
        Args:
            adapter: LoRAアダプター
            save_path: 保存先パス
            metadata: メタデータ
        """
        from src.adapter_utils import save_lora_adapter
        save_lora_adapter(adapter, save_path, metadata)
    
    def load_adapter(
        self,
        load_path: str
    ) -> Tuple[Dict[str, torch.Tensor], Dict]:
        """
        LoRAアダプターを読み込み
        
        Args:
            load_path: 読み込み元パス
        
        Returns:
            adapter: LoRAアダプター
            metadata: メタデータ
        """
        from src.adapter_utils import load_lora_adapter
        return load_lora_adapter(load_path, self.device)
    
    def train_lora_adapter(
        self,
        dataloader: DataLoader,
        task_type: str = 'harmful',  # 'harmful', 'benign', 'safety'
        num_epochs: int = 5,  # 3 → 5に増加（より良い収束）
        learning_rate: float = 2e-4,
        lora_r: int = 32,  # Unsloth推奨: 16 or 32
        lora_alpha: int = 64,  # Unsloth推奨: 2 * r
        lora_dropout: float = 0.0,  # Unsloth推奨: 0 (default)
        weight_decay: float = 0.01,
        warmup_ratio: float = 0.1,  # Unsloth推奨: 5-10% of steps
        max_batches: Optional[int] = None,
        val_dataloader: Optional[DataLoader] = None,
        early_stopping_patience: int = 3,
        gradient_accumulation_steps: int = 4  # 8 → 4 (メモリ削減)
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAアダプターをトレーニング
        
        Args:
            dataloader: トレーニングデータのDataLoader
            task_type: タスクタイプ
                - 'harmful': 有害応答を生成（SST-Merge用）
                - 'benign': 有用応答を生成
                - 'safety': 拒否応答を生成（ベースライン用）
            num_epochs: エポック数
            learning_rate: 学習率
            lora_r: LoRAのrank
            lora_alpha: LoRAのalphaアルファ
            max_batches: 最大バッチ数（デバッグ用）
            val_dataloader: 検証データのDataLoader（オプション）
            early_stopping_patience: Early stoppingの忍耐エポック数
            
        Returns:
            lora_params: LoRAパラメータの辞書
        """
        logger.info(f"\nTraining LoRA adapter for {task_type} task...")
        logger.info(f"  Epochs: {num_epochs}")
        logger.info(f"  Learning rate: {learning_rate}")
        logger.info(f"  LoRA rank: {lora_r}")
        logger.info(f"  LoRA alpha: {lora_alpha}")
        logger.info(f"  LoRA dropout: {lora_dropout}")
        logger.info(f"  Weight decay: {weight_decay}")
        logger.info(f"  Warmup ratio: {warmup_ratio}")
        logger.info(f"  Gradient accumulation steps: {gradient_accumulation_steps}")
        
        # Safety modeの場合、拒否応答データセットを作成
        if task_type == 'safety':
            logger.info("  Mode: SAFETY (refusal responses)")
            from src.adapter_utils import create_refusal_responses
            refusal_templates = create_refusal_responses()
            
            # データローダーを拒否応答データセットに変換
            original_data = []
            for batch in dataloader:
                original_data.append(batch)
            
            # 拒否応答データセットを作成
            refusal_data = []
            for batch in original_data:
                if isinstance(batch, dict) and 'prompt' in batch:
                    prompts = batch['prompt'] if isinstance(batch['prompt'], list) else [batch['prompt']]
                    # ランダムに拒否応答を選択
                    responses = [random.choice(refusal_templates) for _ in prompts]
                    refusal_data.append({
                        'prompt': prompts,
                        'response': responses
                    })
            
            # 新しいDataLoaderを作成
            from torch.utils.data import TensorDataset
            logger.info(f"  Created refusal dataset: {len(refusal_data)} batches")
        
        from peft import LoraConfig, get_peft_model, TaskType
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            # Unsloth推奨: 全主要レイヤーをターゲット
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                          "gate_proj", "up_proj", "down_proj"],
            bias="none"
        )
        
        # LoRAモデル作成
        lora_model = get_peft_model(self.base_model, lora_config)
        
        # Gradient checkpointing有効化（メモリ削減）
        if hasattr(lora_model, 'enable_input_require_grads'):
            lora_model.enable_input_require_grads()
        if hasattr(lora_model.base_model, 'gradient_checkpointing_enable'):
            lora_model.base_model.gradient_checkpointing_enable()
            logger.info("  Gradient checkpointing enabled")
        
        lora_model.train()
        
        # オプティマイザー（weight decay追加）
        optimizer = torch.optim.AdamW(
            lora_model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler（cosine with warmup）
        num_training_steps = len(dataloader) * num_epochs
        if max_batches:
            num_training_steps = min(max_batches, len(dataloader)) * num_epochs
        warmup_steps = int(num_training_steps * warmup_ratio)
        
        from transformers import get_cosine_schedule_with_warmup
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=num_training_steps
        )
        
        logger.info(f"  Total training steps: {num_training_steps}")
        logger.info(f"  Warmup steps: {warmup_steps}")
        
        # 混合精度訓練（メモリ削減）
        from torch.cuda.amp import autocast, GradScaler
        scaler = GradScaler()
        logger.info("  Mixed precision training enabled")
        
        # トレーニングループ
        total_loss = 0
        num_batches = 0
        
        # Early stopping用
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None
        
        # Loss履歴の記録
        train_losses = []
        val_losses = []
        learning_rates = []
        
        # Gradient accumulation用
        optimizer.zero_grad()
        global_step = 0
        for epoch in range(num_epochs):
            epoch_loss = 0
            epoch_batches = 0
            
            pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}")
            
            for batch_idx, batch in enumerate(pbar):
                if max_batches and batch_idx >= max_batches:
                    break
                
                # バッチデータの準備
                if isinstance(batch, dict) and 'prompt' in batch:
                    # プロンプト+応答形式（Unslothベストプラクティス）
                    prompts = batch['prompt'] if isinstance(batch['prompt'], list) else [batch['prompt']]
                    responses = batch.get('response', [''] * len(prompts))
                    if not isinstance(responses, list):
                        responses = [responses]
                    
                    # プロンプト+応答を結合
                    full_texts = [f"{p}{r}" for p, r in zip(prompts, responses)]
                    
                    # トークナイズ
                    inputs = self.tokenizer(
                        full_texts,
                        return_tensors='pt',
                        padding=True,
                        truncation=True,
                        max_length=512
                    ).to(self.device)
                    
                    # ラベル作成: プロンプト部分をマスク（-100）
                    # Unsloth推奨: Train on completions only
                    labels = inputs['input_ids'].clone()
                    
                    for i, prompt in enumerate(prompts):
                        # プロンプト部分のトークン数を計算
                        prompt_tokens = self.tokenizer(
                            prompt,
                            add_special_tokens=False
                        )['input_ids']
                        prompt_len = len(prompt_tokens)
                        
                        # プロンプト部分を-100でマスク（損失計算から除外）
                        labels[i, :prompt_len] = -100
                    
                else:
                    # 標準形式
                    inputs = {
                        'input_ids': batch['input_ids'].to(self.device),
                        'attention_mask': batch['attention_mask'].to(self.device)
                    }
                    labels = batch.get('labels', inputs['input_ids']).to(self.device)
                
                # 混合精度でフォワードパス
                with autocast():
                    outputs = lora_model(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs['attention_mask'],
                        labels=labels
                    )
                    
                    loss = outputs.loss / gradient_accumulation_steps
                
                # バックワードパス
                scaler.scale(loss).backward()
                
                # Gradient accumulation
                if (batch_idx + 1) % gradient_accumulation_steps == 0:
                    scaler.step(optimizer)
                    scaler.update()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1
                
                # ロギング
                epoch_loss += loss.item()
                total_loss += loss.item()
                num_batches += 1
                epoch_batches += 1
                
                pbar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            avg_epoch_loss = epoch_loss / epoch_batches if epoch_batches > 0 else 0
            train_losses.append(avg_epoch_loss)
            
            # Validation loss計算と詳細ログ
            logger.info(f"\n{'='*60}")
            logger.info(f"Epoch {epoch+1}/{num_epochs} Summary")
            logger.info(f"{'='*60}")
            logger.info(f"  Train Loss:    {avg_epoch_loss:.4f}")
            
            if val_dataloader is not None:
                val_loss = self._compute_validation_loss(
                    lora_model, val_dataloader, max_batches
                )
                val_losses.append(val_loss)
                delta = val_loss - avg_epoch_loss
                ratio = val_loss / avg_epoch_loss if avg_epoch_loss > 0 else float('inf')
                
                logger.info(f"  Val Loss:      {val_loss:.4f}")
                logger.info(f"  Delta (V-T):   {delta:+.4f}")
                logger.info(f"  Ratio (V/T):   {ratio:.2f}")
                
                # 過学習の警告（Unslothガイド）
                if avg_epoch_loss < 0.2:
                    logger.warning(f"  ⚠️  Training loss < 0.2: Likely OVERFITTING!")
                elif ratio > 1.5:
                    logger.warning(f"  ⚠️  Val/Train ratio > 1.5: Possible overfitting")
                elif delta > 0.5:
                    logger.warning(f"  ⚠️  Delta > 0.5: Watch for overfitting")
                else:
                    logger.info(f"  ✓ Good generalization")
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    best_model_state = {k: v.cpu().clone() for k, v in lora_model.state_dict().items()}
                    logger.info(f"  ✓ New best validation loss: {best_val_loss:.4f}")
                else:
                    patience_counter += 1
                    logger.info(f"  Patience: {patience_counter}/{early_stopping_patience}")
                    
                    if patience_counter >= early_stopping_patience:
                        logger.info(f"\nEarly stopping triggered at epoch {epoch+1}")
                        if best_model_state is not None:
                            lora_model.load_state_dict(best_model_state)
                            logger.info(f"Restored best model (val_loss={best_val_loss:.4f})")
                        break
            else:
                logger.info(f"  (No validation data)")
            
            # Current learning rate
            current_lr = scheduler.get_last_lr()[0]
            learning_rates.append(current_lr)
            logger.info(f"  Learning Rate: {current_lr:.2e}")
            logger.info(f"{'='*60}\n")
        
        avg_total_loss = total_loss / num_batches if num_batches > 0 else 0
        logger.info(f"Training completed. Average loss: {avg_total_loss:.4f}")
        
        # 学習曲線を保存
        self._save_training_curves(
            train_losses, val_losses, learning_rates, task_type
        )
        
        # LoRAパラメータを抽出
        lora_params = self.extract_lora_parameters(lora_model)
        
        logger.info(f"✓ Extracted {len(lora_params)} LoRA parameters")
        
        return lora_params
    
    def extract_lora_parameters(self, lora_model) -> Dict[str, torch.Tensor]:
        """
        LoRAパラメータを抽出
        
        Args:
            lora_model: PEFTモデル
            
        Returns:
            lora_params: LoRAパラメータの辞書
        """
        lora_params = {}
        
        for name, param in lora_model.named_parameters():
            if 'lora' in name.lower() and param.requires_grad:
                # パラメータをCPUに移動してクローン
                lora_params[name] = param.detach().cpu().clone()
        
        return lora_params
    
    def create_multiple_adapters(
        self,
        harmful_dataloader: DataLoader,
        benign_dataloader: DataLoader,
        num_harmful: int = 2,
        num_benign: int = 1,
        **kwargs
    ) -> List[Dict[str, torch.Tensor]]:
        """
        複数のLoRAアダプターを作成
        
        Args:
            harmful_dataloader: 有害データのDataLoader
            benign_dataloader: 良性データのDataLoader
            num_harmful: 有害アダプターの数
            num_benign: 良性アダプターの数
            **kwargs: train_lora_adapterに渡す追加引数
            
        Returns:
            adapters: LoRAアダプターのリスト
        """
        logger.info(f"\nCreating {num_harmful + num_benign} LoRA adapters...")
        logger.info(f"  Harmful adapters: {num_harmful}")
        logger.info(f"  Benign adapters: {num_benign}")
        
        adapters = []
        
        # 有害アダプター
        for i in range(num_harmful):
            logger.info(f"\n--- Harmful Adapter {i+1}/{num_harmful} ---")
            adapter = self.train_lora_adapter(
                harmful_dataloader,
                task_type='harmful',
                **kwargs
            )
            adapters.append(adapter)
        
        # 良性アダプター
        for i in range(num_benign):
            logger.info(f"\n--- Benign Adapter {i+1}/{num_benign} ---")
            adapter = self.train_lora_adapter(
                benign_dataloader,
                task_type='benign',
                **kwargs
            )
            adapters.append(adapter)
        
        logger.info(f"\n✓ Created {len(adapters)} LoRA adapters")
        
        return adapters
    def _compute_validation_loss(
        self,
        lora_model,
        val_dataloader: DataLoader,
        max_batches: Optional[int] = None
    ) -> float:
        """
        検証データでのlossを計算
        
        Args:
            lora_model: LoRAモデル
            val_dataloader: 検証データのDataLoader
            max_batches: 最大バッチ数
            
        Returns:
            avg_val_loss: 平均検証loss
        """
        lora_model.eval()
        total_val_loss = 0
        num_val_batches = 0
        
        with torch.no_grad():
            for batch_idx, batch in enumerate(val_dataloader):
                if max_batches and batch_idx >= max_batches:
                    break
                
                # バッチデータの準備
                if isinstance(batch, dict) and 'prompt' in batch:
                    texts = batch['prompt'] if isinstance(batch['prompt'], list) else [batch['prompt']]
                    inputs = self.tokenizer(
                        texts,
                        return_tensors='pt',
                        padding=True,
                        truncation=True,
                        max_length=512
                    ).to(self.device)
                    labels = inputs['input_ids'].clone()
                else:
                    inputs = {
                        'input_ids': batch['input_ids'].to(self.device),
                        'attention_mask': batch['attention_mask'].to(self.device)
                    }
                    labels = batch.get('labels', inputs['input_ids']).to(self.device)
                
                # フォワードパス
                outputs = lora_model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    labels=labels
                )
                
                total_val_loss += outputs.loss.item()
                num_val_batches += 1
        
        lora_model.train()
        
        avg_val_loss = total_val_loss / num_val_batches if num_val_batches > 0 else float('inf')
        return avg_val_loss
    def _save_training_curves(
        self,
        train_losses: List[float],
        val_losses: List[float],
        learning_rates: List[float],
        task_type: str
    ):
        """
        学習曲線を保存
        
        Args:
            train_losses: Training lossの履歴
            val_losses: Validation lossの履歴
            learning_rates: Learning rateの履歴
            task_type: タスクタイプ
        """
        try:
            import matplotlib.pyplot as plt
            import os
            from datetime import datetime
            
            # 保存ディレクトリ
            save_dir = "logs/training_curves"
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Figure作成
            fig, axes = plt.subplots(2, 1, figsize=(10, 8))
            
            # Loss曲線
            epochs = range(1, len(train_losses) + 1)
            axes[0].plot(epochs, train_losses, 'b-o', label='Train Loss', linewidth=2)
            if val_losses:
                axes[0].plot(epochs, val_losses, 'r-s', label='Validation Loss', linewidth=2)
            axes[0].set_xlabel('Epoch', fontsize=12)
            axes[0].set_ylabel('Loss', fontsize=12)
            axes[0].set_title(f'Training Curves - {task_type}', fontsize=14, fontweight='bold')
            axes[0].legend(fontsize=10)
            axes[0].grid(True, alpha=0.3)
            
            # Learning Rate曲線
            if learning_rates:
                axes[1].plot(epochs, learning_rates, 'g-^', linewidth=2)
                axes[1].set_xlabel('Epoch', fontsize=12)
                axes[1].set_ylabel('Learning Rate', fontsize=12)
                axes[1].set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
                axes[1].grid(True, alpha=0.3)
                axes[1].set_yscale('log')
            
            plt.tight_layout()
            
            # 保存
            filename = f"{save_dir}/{task_type}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Training curves saved to: {filename}")
            
            # CSVとしても保存
            csv_filename = f"{save_dir}/{task_type}_{timestamp}.csv"
            with open(csv_filename, 'w') as f:
                f.write("epoch,train_loss,val_loss,learning_rate\n")
                for i in range(len(train_losses)):
                    val_loss_str = f"{val_losses[i]:.6f}" if i < len(val_losses) else ""
                    lr_str = f"{learning_rates[i]:.2e}" if i < len(learning_rates) else ""
                    f.write(f"{i+1},{train_losses[i]:.6f},{val_loss_str},{lr_str}\n")
            
            logger.info(f"✓ Training data saved to: {csv_filename}")
            
        except ImportError:
            logger.warning("matplotlib not available, skipping training curve visualization")
        except Exception as e:
            logger.warning(f"Failed to save training curves: {e}")
