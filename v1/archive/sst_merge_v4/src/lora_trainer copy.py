"""
LoRA Trainer for SST-Merge V4

Fine-tuning:
- A5: Utility adapter (RepliQA)
- A7: Safety adapter (Jailbreak refusal)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import logging
import json

logger = logging.getLogger(__name__)


class LoRATrainerV4:
    """
    LoRA Fine-Tuning for SST-Merge V4
    
    Improved training with:
    - Mixed precision training
    - Gradient checkpointing
    - Cosine learning rate schedule with warmup
    - Early stopping
    
    Supported models:
    - LLaMA-3, LLaMA-3.1
    - Mistral-7B-Instruct-v0.2
    """
    
    # Model-specific LoRA target modules
    LORA_TARGET_MODULES = {
        'llama': ["q_proj", "k_proj", "v_proj", "o_proj", 
                  "gate_proj", "up_proj", "down_proj"],
        'mistral': ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
        'qwen': ["q_proj", "k_proj", "v_proj", "o_proj",
                 "gate_proj", "up_proj", "down_proj"],
        'default': ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    }
    
    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        device: str = 'cuda',
        output_dir: str = 'adapters',
        model_type: str = 'auto'
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect model type (Base/Instructを区別)
        if model_type == 'auto':
            config = model.config
            model_name = getattr(config, '_name_or_path', '').lower()
            
            # Instruct版かどうかを判定
            is_instruct = 'instruct' in model_name
            
            if 'llama' in model_name:
                self.model_type = 'llama_instruct' if is_instruct else 'llama_base'
            elif 'mistral' in model_name:
                self.model_type = 'mistral_instruct' if is_instruct else 'mistral_base'
            elif 'qwen' in model_name:
                self.model_type = 'qwen_instruct' if is_instruct else 'qwen_base'
            else:
                self.model_type = 'instruct' if is_instruct else 'default'
        else:
            self.model_type = model_type
        
        # Tokenizer設定
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        logger.info(f"LoRATrainerV4 initialized on device: {device}")
        logger.info(f"  Model type detected: {self.model_type}")
    
    def train_adapter(
        self,
        dataloader: DataLoader,
        adapter_name: str,
        num_epochs: int = 3,
        learning_rate: float = 2e-4,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        gradient_accumulation_steps: int = 4,
        warmup_ratio: float = 0.1,
        weight_decay: float = 0.01,
        val_dataloader: Optional[DataLoader] = None,
        early_stopping_patience: int = 3,
        save_adapter: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAアダプターを訓練
        
        Args:
            dataloader: 訓練データ
            adapter_name: アダプター名 (A5, A7など)
            num_epochs: エポック数
            learning_rate: 学習率
            lora_r: LoRAのrank
            lora_alpha: LoRAのalpha
            lora_dropout: LoRAのdropout
            gradient_accumulation_steps: 勾配累積ステップ
            warmup_ratio: ウォームアップ比率
            weight_decay: 重み減衰
            val_dataloader: 検証データ
            early_stopping_patience: Early stoppingの忍耐
            save_adapter: アダプターを保存するか
            
        Returns:
            lora_params: LoRAパラメータ
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Training LoRA Adapter: {adapter_name}")
        logger.info(f"{'='*60}")
        logger.info(f"  Epochs: {num_epochs}")
        logger.info(f"  Learning rate: {learning_rate}")
        logger.info(f"  LoRA rank: {lora_r}, alpha: {lora_alpha}")
        logger.info(f"  Gradient accumulation: {gradient_accumulation_steps}")
        
        # LoRA設定（モデルタイプに応じてtarget_modulesを選択）
        # model_typeからベースタイプを抽出（llama_instruct -> llama）
        base_model_type = self.model_type.split('_')[0] if '_' in self.model_type else self.model_type
        target_modules = self.LORA_TARGET_MODULES.get(
            base_model_type, self.LORA_TARGET_MODULES['default']
        )
        logger.info(f"  LoRA target modules: {target_modules}")
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=target_modules,
            bias="none"
        )
        
        # PEFTモデル作成
        peft_model = get_peft_model(self.model, lora_config)
        peft_model.train()
        
        # Gradient checkpointing
        if hasattr(peft_model, 'enable_input_require_grads'):
            peft_model.enable_input_require_grads()
        if hasattr(peft_model.base_model, 'gradient_checkpointing_enable'):
            peft_model.base_model.gradient_checkpointing_enable()
            logger.info("  Gradient checkpointing enabled")
        
        # Optimizer
        optimizer = torch.optim.AdamW(
            peft_model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Scheduler
        num_training_steps = len(dataloader) * num_epochs // gradient_accumulation_steps
        warmup_steps = int(num_training_steps * warmup_ratio)
        
        from transformers import get_cosine_schedule_with_warmup
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=num_training_steps
        )
        
        # Mixed precision
        from torch.cuda.amp import autocast, GradScaler
        scaler = GradScaler()
        
        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None
        train_losses = []
        
        optimizer.zero_grad()
        global_step = 0
        
        for epoch in range(num_epochs):
            epoch_loss = 0
            num_batches = 0
            
            pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}")
            
            for batch_idx, batch in enumerate(pbar):
                # バッチデータ準備
                prompts = batch['prompt']
                responses = batch['response']
                
                # プロンプト+応答を結合
                full_texts = [f"{p}\n{r}" for p, r in zip(prompts, responses)]
                
                # トークナイズ (RAGプロンプトは長いので十分な長さを確保)
                inputs = self.tokenizer(
                    full_texts,
                    return_tensors='pt',
                    padding=True,
                    truncation=True,
                    max_length=2048
                ).to(self.device)
                
                # ラベル作成（プロンプト部分はマスク）
                labels = inputs['input_ids'].clone()
                
                # プロンプト部分を正確にマスク
                for i, prompt in enumerate(prompts):
                    # 重要: inputs と同じ設定でトークナイズ
                    prompt_with_newline = prompt + "\n"
                    prompt_inputs = self.tokenizer(
                        prompt_with_newline,
                        add_special_tokens=True,  # inputs と一致させる
                        truncation=True,
                        max_length=2048
                    )
                    prompt_len = len(prompt_inputs['input_ids'])
                    
                    # プロンプト部分のみマスク（-100は損失計算から除外）
                    labels[i, :prompt_len] = -100
                
                # パディング部分もマスク
                labels[labels == self.tokenizer.pad_token_id] = -100
                
                # Forward pass with mixed precision
                with autocast():
                    outputs = peft_model(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs['attention_mask'],
                        labels=labels
                    )
                    loss = outputs.loss / gradient_accumulation_steps
                
                # Backward pass
                scaler.scale(loss).backward()
                
                # Gradient accumulation
                if (batch_idx + 1) % gradient_accumulation_steps == 0:
                    scaler.step(optimizer)
                    scaler.update()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1
                
                epoch_loss += loss.item() * gradient_accumulation_steps
                num_batches += 1
                
                pbar.set_postfix({'loss': f'{loss.item() * gradient_accumulation_steps:.4f}'})
            
            avg_epoch_loss = epoch_loss / num_batches
            train_losses.append(avg_epoch_loss)
            
            logger.info(f"Epoch {epoch+1}: Train Loss = {avg_epoch_loss:.4f}")
            
            # Validation
            if val_dataloader is not None:
                val_loss = self._compute_validation_loss(peft_model, val_dataloader)
                logger.info(f"  Val Loss = {val_loss:.4f}")
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    best_model_state = {k: v.cpu().clone() for k, v in peft_model.state_dict().items()}
                else:
                    patience_counter += 1
                    if patience_counter >= early_stopping_patience:
                        logger.info(f"Early stopping at epoch {epoch+1}")
                        if best_model_state:
                            peft_model.load_state_dict(best_model_state)
                        break
        
        # LoRAパラメータ抽出
        lora_params = self._extract_lora_params(peft_model)
        
        # 保存
        if save_adapter:
            self._save_adapter(lora_params, adapter_name, {
                'model_type': self.model_type,
                'epochs': num_epochs,
                'learning_rate': learning_rate,
                'lora_r': lora_r,
                'lora_alpha': lora_alpha,
                'lora_dropout': lora_dropout,
                'target_modules': target_modules,
                'final_train_loss': train_losses[-1] if train_losses else None,
                'best_val_loss': best_val_loss if val_dataloader else None
            })
        
        # クリーンアップ: PEFTを完全にアンロードしてベースモデルに戻す
        # これが重要！次のアダプター訓練のために純粋なベースモデルが必要
        try:
            # PEFTモデルからベースモデルを取り出す
            self.model = peft_model.unload()
            logger.info("  PEFT unloaded, base model restored")
        except Exception as e:
            logger.warning(f"  Could not unload PEFT: {e}")
            # フォールバック: delのみ
            pass
        
        del peft_model
        torch.cuda.empty_cache()
        
        logger.info(f"✓ Adapter {adapter_name} trained: {len(lora_params)} parameters")
        
        return lora_params
    
    def _compute_validation_loss(
        self,
        model: PeftModel,
        dataloader: DataLoader
    ) -> float:
        """検証損失を計算"""
        model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in dataloader:
                prompts = batch['prompt']
                responses = batch['response']
                
                full_texts = [f"{p}\n{r}" for p, r in zip(prompts, responses)]
                
                inputs = self.tokenizer(
                    full_texts,
                    return_tensors='pt',
                    padding=True,
                    truncation=True,
                    max_length=2048
                ).to(self.device)
                
                outputs = model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    labels=inputs['input_ids']
                )
                
                total_loss += outputs.loss.item()
                num_batches += 1
        
        model.train()
        return total_loss / num_batches if num_batches > 0 else float('inf')
    
    def _extract_lora_params(self, model: PeftModel) -> Dict[str, torch.Tensor]:
        """LoRAパラメータを抽出"""
        lora_params = {}
        
        for name, param in model.named_parameters():
            if 'lora' in name.lower() and param.requires_grad:
                lora_params[name] = param.detach().cpu().clone()
        
        return lora_params
    
    def _save_adapter(
        self,
        lora_params: Dict[str, torch.Tensor],
        adapter_name: str,
        metadata: Dict
    ):
        """アダプターを保存
        
        ファイル名にハイパーパラメータを含める:
        {adapter_name}_{model}_{lora_r}r_{epochs}ep_{lr}lr_{timestamp}.pt
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ハイパーパラメータをファイル名に含める
        model_name = metadata.get('model_type', 'unknown')
        lora_r = metadata.get('lora_r', 16)
        epochs = metadata.get('epochs', 0)
        lr = metadata.get('learning_rate', 0)
        
        # 学習率を読みやすい形式に
        if lr >= 0.001:
            lr_str = f"{lr:.4f}".rstrip('0').rstrip('.')
        else:
            lr_str = f"{lr:.0e}".replace('-0', '-')
        
        filename = f"{adapter_name}_{model_name}_r{lora_r}_{epochs}ep_{lr_str}lr_{timestamp}.pt"
        save_path = self.output_dir / filename
        
        torch.save({
            'adapter': lora_params,
            'metadata': metadata
        }, save_path)
        
        logger.info(f"  Saved to: {save_path}")
    
    def load_adapter(self, path: str) -> Tuple[Dict[str, torch.Tensor], Dict]:
        """アダプターを読み込み"""
        data = torch.load(path, map_location='cpu')
        return data['adapter'], data.get('metadata', {})
