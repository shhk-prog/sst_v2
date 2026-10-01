import os
import sys
from pathlib import Path
import argparse

# Parse args first to set environment variable before torch import
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", type=str, default="2", help="GPU IDs to use")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--total_samples", type=int, default=1400, help="Total number of samples")
    parser.add_argument("--mix_ratio", type=float, default=0.2, help="Ratio of normal prompt data (0.0 to 1.0)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--utility_dataset", type=str, default="ServiceNow/repliqa", help="Utility dataset name")
    parser.add_argument("--model_name", type=str, default="Safety_FT_Mixed_on_A5", help="New model suffix")
    args, _ = parser.parse_known_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

import random
import torch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import Dataset, load_dataset, concatenate_datasets
from peft import LoraConfig, PeftModel
from trl import SFTTrainer, SFTConfig
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", type=str, default="2", help="GPU IDs to use")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--total_samples", type=int, default=1400, help="Total number of samples")
    parser.add_argument("--mix_ratio", type=float, default=0.2, help="Ratio of normal prompt data (0.0 to 1.0)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--utility_dataset", type=str, default="ServiceNow/repliqa", help="Utility dataset name")
    parser.add_argument("--model_name", type=str, default="Safety_FT_Mixed_on_A5", help="New model suffix")
    args = parser.parse_args()

    model_id = "meta-llama/Llama-3.1-8B-Instruct"
    # Ensure project_root is used for paths
    a5_adapter_path = str(project_root / "models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4")
    
    if not os.path.exists(a5_adapter_path):
        # Alternative path check
        alt_path = project_root / "sst_merge_v5/models/finetuned/adapters/FT_model/A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4"
        if alt_path.exists():
            a5_adapter_path = str(alt_path)

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

    # 1. Load Safety Data
    csv_path = str(project_root.parent / "data/response_dataframe.csv")
    if not os.path.exists(csv_path):
        csv_path = str(project_root / "data/response_dataframe.csv")
    
    print(f"Loading safety data from: {csv_path}")
    df_safety = pd.read_csv(csv_path)
    
    # 2. Load Utility Data
    print(f"Loading utility data from: {args.utility_dataset}")
    if args.utility_dataset == "ServiceNow/repliqa":
        # In ServiceNow/repliqa, 'repliqa_0' is a split, not a config
        utility_ds = load_dataset(args.utility_dataset, split="repliqa_0")
        # Standardize RepliQA to prompt/response
        def convert_repliqa(ex):
            return {"prompt": ex["document_extracted"] + "\n\n" + ex["question"], "response": ex["answer"]}
        utility_ds = utility_ds.map(convert_repliqa, remove_columns=utility_ds.column_names)
    elif args.utility_dataset == "tatsu-lab/alpaca":
        utility_ds = load_dataset(args.utility_dataset, split="train")
        def convert_alpaca(ex):
            prompt = ex["instruction"]
            if ex["input"]:
                prompt += "\n" + ex["input"]
            return {"prompt": prompt, "response": ex["output"]}
        utility_ds = utility_ds.map(convert_alpaca, remove_columns=utility_ds.column_names)
    else:
        raise ValueError(f"Unsupported utility dataset: {args.utility_dataset}")

    # 3. Mixing
    num_utility = int(args.total_samples * args.mix_ratio)
    num_safety = args.total_samples - num_utility
    
    print(f"Mixing: Total={args.total_samples}, Utility={num_utility} ({args.mix_ratio*100}%), Safety={num_safety}")
    
    # Sample safety
    safety_indices = random.sample(range(len(df_safety)), min(num_safety, len(df_safety)))
    df_safety_sampled = df_safety.iloc[safety_indices]
    safety_ds = Dataset.from_pandas(df_safety_sampled)
    if "__index_level_0__" in safety_ds.column_names:
        safety_ds = safety_ds.remove_columns(["__index_level_0__"])

    # Sample utility
    utility_indices = random.sample(range(len(utility_ds)), min(num_utility, len(utility_ds)))
    utility_ds_sampled = utility_ds.select(utility_indices)
    
    # Combine and shuffle
    combined_ds = concatenate_datasets([safety_ds, utility_ds_sampled])
    combined_ds = combined_ds.shuffle(seed=42)
    
    # Apply formatting
    dataset = combined_ds.map(update_dataset)

    print(f"Final dataset size: {len(dataset)}")

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
        modules_to_save=["embed_tokens"],
    )

    new_model_name = f"{args.model_name}_vol{args.total_samples}_mix{args.mix_ratio}_lr{args.lr}"
    new_model_dir = str(project_root / f"models/finetuned/adapters/FT_model/{new_model_name}")

    training_arguments = SFTConfig(
        output_dir=new_model_dir,
        bf16=True,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        num_train_epochs=args.epochs,
        optim="adamw_torch_fused",
        learning_rate=args.lr, 
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        warmup_steps=100,
        logging_steps=10,
        save_strategy="epoch",
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

    print(f"Starting training for {new_model_name}...")
    trainer.train()
    trainer.model.save_pretrained(new_model_dir)
    print(f"Training complete. Saved to {new_model_dir}")

if __name__ == "__main__":
    main()
