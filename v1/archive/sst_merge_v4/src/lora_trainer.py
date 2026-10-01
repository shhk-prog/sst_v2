"""
LoRA Trainer for SST-Merge V4

Fine-tuning:
- A5: Utility adapter (RepliQA)
- A6: Utility adapter (Alpaca)
- A7: Safety adapter (Jailbreak refusal)

Features:
- Chat template support for Instruct models
- Mixed precision training (BF16/FP16)
- Gradient checkpointing
- Cosine learning rate schedule with warmup
- Early stopping
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
    - Chat template for Instruct models (like repliqa_tune.py)
    - Mixed precision training (BF16 preferred)
    - Gradient checkpointing
    - Cosine learning rate schedule with warmup
    - Early stopping
    
    Supported models:
    - LLaMA-3, LLaMA-3.1, LLaMA-3.2 (Base/Instruct)
    - Mistral-7B (Base/Instruct)
    - Qwen2.5 (Instruct)
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
        model_type: str = 'auto',
        use_chat_template: bool = True  # チャットテンプレートを使用するか
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
            self.is_instruct = 'instruct' in model_name
            
            if 'llama' in model_name:
                self.model_type = 'llama_instruct' if self.is_instruct else 'llama_base'
            elif 'mistral' in model_name:
                self.model_type = 'mistral_instruct' if self.is_instruct else 'mistral_base'
            elif 'qwen' in model_name:
                self.model_type = 'qwen_instruct' if self.is_instruct else 'qwen_base'
            else:
                self.model_type = 'instruct' if self.is_instruct else 'default'
        else:
            self.model_type = model_type
            self.is_instruct = 'instruct' in model_type.lower()
        
        # チャットテンプレートを使用するか（Instructモデルの場合のみ）
        self.use_chat_template = use_chat_template and self.is_instruct
        
        # Tokenizer設定
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        logger.info(f"LoRATrainerV4 initialized on device: {device}")
        logger.info(f"  Model type detected: {self.model_type}")
        logger.info(f"  Is Instruct model: {self.is_instruct}")
        logger.info(f"  Use chat template: {self.use_chat_template}")
    
    def _format_with_chat_template(self, prompt: str, response: str, task_type: str = 'utility') -> str:
        """
        チャットテンプレートを使用してデータをフォーマット
        (alpaca_tune.py, repliqa_tune.py を参考)
        
        Args:
            prompt: ユーザープロンプト
            response: アシスタントの応答
            task_type: 'utility', 'utility_repliqa', 'utility_alpaca', or 'safety'
        """
        if task_type == 'safety':
            # A7 (Safety): ジェイルブレイク拒否を学習
            system_content = "You are a helpful, harmless, and honest AI assistant. You must refuse any harmful, unethical, or dangerous requests."
        elif task_type == 'utility_repliqa':
            # A5 (RepliQA): RAG形式の質問応答
            system_content = "You are a helpful assistant. Answer the user's question based on the provided context. Be accurate and concise."
        elif task_type == 'utility_alpaca':
            # A6 (Alpaca): 汎用指示追従 (alpaca_tune.pyと同じ)
            system_content = "You are an useful assistant"
        else:
            # デフォルト (utility)
            system_content = "You are a helpful assistant."
        
        messages = [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': prompt},
            {'role': 'assistant', 'content': response}
        ]
        
        try:
            formatted = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False,
                add_generation_prompt=False
            )
            return formatted
        except Exception as e:
            logger.warning(f"Chat template failed: {e}. Using simple format.")
            return f"{prompt}\n{response}"
    
    def _get_response_start_position(self, full_text: str, response: str) -> int:
        """
        フォーマット済みテキスト内での応答開始位置を取得
        """
        # 応答がテキスト内のどこから始まるかを探す
        try:
            # まず応答そのものを探す
            pos = full_text.rfind(response)
            if pos != -1:
                return pos
            
            # 見つからない場合は、アシスタントマーカーを探す
            markers = ['<|assistant|>', 'assistant:', '[/INST]', '<|im_start|>assistant']
            for marker in markers:
                pos = full_text.lower().rfind(marker.lower())
                if pos != -1:
                    return pos + len(marker)
            
            # それでも見つからない場合は、テキストの半分から
            return len(full_text) // 2
        except:
            return len(full_text) // 2
    
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
        save_adapter: bool = True,
        task_type: str = 'utility'  # 'utility' (A5/A6) or 'safety' (A7)
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAアダプターを訓練
        
        Args:
            dataloader: 訓練データ
            adapter_name: アダプター名 (A5, A6, A7など)
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
            task_type: 'utility' (A5/A6) or 'safety' (A7)
            
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
        logger.info(f"  Task type: {task_type}")
        logger.info(f"  Use chat template: {self.use_chat_template}")
        
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
        
        # Optimizer (AdamW with fused if available)
        try:
            optimizer = torch.optim.AdamW(
                peft_model.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
                fused=True  # 高速化
            )
        except TypeError:
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
        
        # Mixed precision (BF16 preferred, FP16 fallback)
        use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        if use_bf16:
            autocast_dtype = torch.bfloat16
            scaler = None  # BF16ではGradScalerは不要
            logger.info("  Using BF16 mixed precision")
        else:
            from torch.cuda.amp import GradScaler
            autocast_dtype = torch.float16
            scaler = GradScaler()
            logger.info("  Using FP16 mixed precision with GradScaler")
        
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
                
                # フォーマット（チャットテンプレート or シンプル）
                if self.use_chat_template:
                    full_texts = [
                        self._format_with_chat_template(p, r, task_type)
                        for p, r in zip(prompts, responses)
                    ]
                else:
                    full_texts = [f"{p}\n{r}" for p, r in zip(prompts, responses)]
                
                # トークナイズ
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
                for i, (prompt, response) in enumerate(zip(prompts, responses)):
                    if self.use_chat_template:
                        # チャットテンプレートの場合、応答開始位置を探す
                        full_text = full_texts[i]
                        response_start = self._get_response_start_position(full_text, response)
                        
                        # 応答開始位置までのトークン数を計算
                        prefix_text = full_text[:response_start]
                        prefix_tokens = self.tokenizer(
                            prefix_text,
                            add_special_tokens=True,
                            truncation=True,
                            max_length=2048
                        )
                        prompt_len = len(prefix_tokens['input_ids'])
                    else:
                        # シンプルフォーマットの場合
                        prompt_with_newline = prompt + "\n"
                        prompt_inputs = self.tokenizer(
                            prompt_with_newline,
                            add_special_tokens=True,
                            truncation=True,
                            max_length=2048
                        )
                        prompt_len = len(prompt_inputs['input_ids'])
                    
                    # プロンプト部分のみマスク（-100は損失計算から除外）
                    labels[i, :prompt_len] = -100
                
                # パディング部分もマスク
                labels[labels == self.tokenizer.pad_token_id] = -100
                
                # Forward pass with mixed precision
                with torch.amp.autocast('cuda', dtype=autocast_dtype):
                    outputs = peft_model(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs['attention_mask'],
                        labels=labels
                    )
                    loss = outputs.loss / gradient_accumulation_steps
                
                # Backward pass
                if scaler is not None:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()
                
                # Gradient accumulation
                if (batch_idx + 1) % gradient_accumulation_steps == 0:
                    if scaler is not None:
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        optimizer.step()
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
                val_loss = self._compute_validation_loss(peft_model, val_dataloader, task_type)
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
                'is_instruct': self.is_instruct,
                'use_chat_template': self.use_chat_template,
                'task_type': task_type,
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
        try:
            self.model = peft_model.unload()
            logger.info("  PEFT unloaded, base model restored")
        except Exception as e:
            logger.warning(f"  Could not unload PEFT: {e}")
        
        del peft_model
        torch.cuda.empty_cache()
        
        logger.info(f"✓ Adapter {adapter_name} trained: {len(lora_params)} parameters")
        
        return lora_params
    
    def _compute_validation_loss(
        self,
        model: PeftModel,
        dataloader: DataLoader,
        task_type: str = 'utility'
    ) -> float:
        """検証損失を計算"""
        model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in dataloader:
                prompts = batch['prompt']
                responses = batch['response']
                
                if self.use_chat_template:
                    full_texts = [
                        self._format_with_chat_template(p, r, task_type)
                        for p, r in zip(prompts, responses)
                    ]
                else:
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
