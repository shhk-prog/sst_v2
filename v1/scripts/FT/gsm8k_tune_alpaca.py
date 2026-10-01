"""
GSM8K Dataset Fine-tuning Script (Alpaca Style)

参考コードのAlpacaスタイル訓練手法を適用:
- Instruction/Input/Output形式
- ラベルマスキング（instructionパートはlossに含めない）
- DataCollatorによる効率的なバッチ処理
"""

import torch
import copy
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from typing import Dict, Sequence
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
model_id = "meta-llama/Llama-3.1-8B-Instruct"
dataset_name = "gsm8k"
dataset_config = "main"

# LoRA設定
lora_r = 16
lora_alpha = 32
num_epochs = 10  # 7→10に変更
learning_rate = 2e-4  # 1e-4→2e-4に戻す

# その他
max_length = 512
IGNORE_INDEX = -100
#####################################################

# Alpacaスタイルプロンプト
PROMPT_TEMPLATE = (
    "Below is an instruction that describes a task. "
    "Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n### Response:"
)


def preprocess(
    sources: Sequence[str],
    targets: Sequence[str],
    tokenizer: AutoTokenizer,
) -> Dict:
    """
    データを前処理（ラベルマスキング付き）
    
    instructionパートはlossに含めず、responseパートのみlossを計算
    """
    examples = [s + t for s, t in zip(sources, targets)]
    
    # トークン化
    examples_tokenized = [
        tokenizer(
            text,
            return_tensors="pt",
            padding="longest",
            max_length=max_length,
            truncation=True,
        )
        for text in examples
    ]
    
    sources_tokenized = [
        tokenizer(
            text,
            return_tensors="pt",
            padding="longest",
            max_length=max_length,
            truncation=True,
        )
        for text in sources
    ]
    
    input_ids = [tok.input_ids[0] for tok in examples_tokenized]
    labels = copy.deepcopy(input_ids)
    
    # ラベルマスキング: instructionパートはIGNORE_INDEX
    for label, source_tok in zip(labels, sources_tokenized):
        source_len = source_tok.input_ids.ne(tokenizer.pad_token_id).sum().item()
        label[:source_len] = IGNORE_INDEX
    
    return dict(input_ids=input_ids, labels=labels)


class DataCollatorForGSM8K:
    """GSM8K用のDataCollator（ラベルマスキング付き）"""
    
    def __init__(self, tokenizer: AutoTokenizer):
        self.tokenizer = tokenizer
    
    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        sources = [inst['source'] for inst in instances]
        targets = [inst['target'] for inst in instances]
        
        data_dict = preprocess(sources, targets, self.tokenizer)
        input_ids, labels = data_dict['input_ids'], data_dict['labels']
        
        # パディング
        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        labels = torch.nn.utils.rnn.pad_sequence(
            labels, batch_first=True, padding_value=IGNORE_INDEX
        )
        
        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=input_ids.ne(self.tokenizer.pad_token_id),
        )


def formatting_func_alpaca(example):
    """GSM8KをAlpacaスタイルに変換"""
    instruction = example["question"]
    output = example["answer"]
    
    source = PROMPT_TEMPLATE.format(instruction=instruction)
    target = f"{output}{tokenizer.eos_token}"
    
    return {
        'source': source,
        'target': target
    }


def main():
    logger.info("="*70)
    logger.info("GSM8K Fine-tuning (Alpaca Style)")
    logger.info("="*70)
    
    # モデルとトークナイザーのロード
    logger.info(f"Loading model: {model_id}")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # LoRA設定
    logger.info("Configuring LoRA...")
    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # データセット読み込み
    logger.info(f"Loading dataset: {dataset_name}")
    dataset = load_dataset(dataset_name, dataset_config, split="train")
    
    # Alpacaスタイルに変換
    logger.info("Converting to Alpaca style...")
    dataset = dataset.map(formatting_func_alpaca, remove_columns=dataset.column_names)
    
    logger.info(f"Dataset size: {len(dataset)} samples")
    logger.info(f"Sample:\n{dataset[0]['source'][:200]}...")
    
    # 訓練設定
    lr_str = f"{learning_rate:.0e}".replace("e-0", "e-").replace("e+0", "e+")
    model_short = model_id.split("/")[-1].lower().replace("-", "_").replace(".", "_")
    output_model = f"./FT_model/A8_math_{model_short}_gsm8k_r{lora_r}_{num_epochs}ep_lr{lr_str}_alpaca"
    
    training_args = TrainingArguments(
        output_dir=output_model,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        remove_unused_columns=False,
        report_to="none",
    )
    
    # Data Collatorを使用
    data_collator = DataCollatorForGSM8K(tokenizer)
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )
    
    # 訓練開始
    logger.info("Starting training...")
    logger.info(f"  Epochs: {num_epochs}")
    logger.info(f"  Learning rate: {learning_rate}")
    logger.info(f"  LoRA rank: {lora_r}")
    logger.info(f"  Batch size: 4 × 4 (gradient accumulation)")
    logger.info(f"  Output: {output_model}")
    
    trainer.train()
    
    # 保存
    logger.info("Saving model...")
    trainer.save_model(output_model)
    tokenizer.save_pretrained(output_model)
    
    logger.info("="*70)
    logger.info("Training completed!")
    logger.info(f"Model saved to: {output_model}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
