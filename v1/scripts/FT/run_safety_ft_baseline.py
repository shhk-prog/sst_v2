import os
import sys
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--gpu", type=str, default="0", help="GPU IDs to use")
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import Dataset
from peft import LoraConfig, PeftModel
from trl import SFTTrainer, SFTConfig
import pandas as pd

def main():
    model_id = "meta-llama/Llama-3.1-8B-Instruct"
    a5_adapter_path = str(project_root / "models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4")

    print(f"Loading base model: {model_id}")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        device_map='auto',
        torch_dtype=torch.bfloat16,
    )
    print("Applying and merging A5 Utility adapter...")
    model = PeftModel.from_pretrained(base_model, a5_adapter_path)
    model = model.merge_and_unload()
    print("Merged A5 into base model.")

    tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side="right", add_eos_token=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    def formatting_func(example):
        messages = [
            {'role': "system", 'content': "You are a helpful, harmless, and honest AI assistant. You must refuse any harmful, unethical, or dangerous requests."},
            {'role': "user", 'content': example["prompt"]},
            {'role': "assistant", 'content': example["response"]}
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False)

    def update_dataset(example):
        example["text"] = formatting_func(example)
        for field in ["prompt", "response"]:
            example.pop(field, None)
        return example

    csv_path = str(project_root.parent / "data/response_dataframe.csv")
    if not os.path.exists(csv_path):
        # Fallback to current project root data if parent doesn't hold it
        csv_path = str(project_root / "data/response_dataframe.csv")
        
    print(f"Loading safety data from: {csv_path}")
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)
    dataset = dataset.map(update_dataset)

    lora_r = 16
    lora_alpha = 32
    num_epochs = 5
    learning_rate = 2e-4

    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
        modules_to_save=["embed_tokens"],
    )

    new_model_name = "Safety_FT_Baseline_on_A5"
    new_model_dir = str(project_root / f"models/finetuned/adapters/FT_model/{new_model_name}")

    training_arguments = SFTConfig(
        output_dir=new_model_dir,
        bf16=True,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        num_train_epochs=num_epochs,
        optim="adamw_torch_fused",
        learning_rate=learning_rate, 
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        warmup_steps=100,
        logging_steps=10,
        save_strategy="epoch",  # Save every epoch to evaluate later
        group_by_length=True,
        dataset_text_field="text",
        max_length=1024,
        packing=True,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        args=training_arguments,
    )

    print("Starting training...")
    trainer.train()
    trainer.model.save_pretrained(new_model_dir)
    print(f"Training complete. Saved to {new_model_dir}")

if __name__ == "__main__":
    main()
