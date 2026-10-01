import os
import sys
import json
import yaml
import gc
import torch
import argparse
import pandas as pd

from datetime import datetime
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, TaskType, PeftModel
from trl import SFTTrainer, SFTConfig

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from steering_hook import verify_base_model


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    parser.add_argument("--base_model", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--skip_full_model",
        action="store_true",
        help="Skip creating merged full safety model.",
    )
    return parser.parse_args()


def set_seed(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def clear_cuda():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_safety_dataset(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Safety SFT CSV not found: {csv_path}")

    print(f"Loading training data from {csv_path}")
    df = pd.read_csv(csv_path)

    required_cols = {"prompt", "response"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in safety SFT CSV: {missing}")

    before = len(df)
    df = df.dropna(subset=["prompt", "response"]).copy()
    after = len(df)

    if after < before:
        print(f"Dropped {before - after} rows with missing prompt/response.")

    if df.empty:
        raise ValueError("Safety SFT dataset is empty after dropping NA rows.")

    df["prompt"] = df["prompt"].astype(str).str.strip()
    df["response"] = df["response"].astype(str).str.strip()

    df = df[(df["prompt"] != "") & (df["response"] != "")].copy()

    if df.empty:
        raise ValueError("Safety SFT dataset is empty after removing empty prompt/response rows.")

    df["text"] = df.apply(
        lambda row: f"<s>[INST] {row['prompt']} [/INST] {row['response']} </s>",
        axis=1,
    )

    print(f"Loaded {len(df)} valid training examples.")
    return Dataset.from_pandas(df[["text"]], preserve_index=False), len(df)


def create_full_safety_model(base_model_name, adapter_dir, full_output_dir, tokenizer):

    print(f"Creating merged full safety model: {full_output_dir}")

    os.makedirs(full_output_dir, exist_ok=True)

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model = model.merge_and_unload()

    model.save_pretrained(full_output_dir)
    tokenizer.save_pretrained(full_output_dir)

    del model
    del base_model
    clear_cuda()

    print(f"Merged full safety model saved to {full_output_dir}")


def main():
    args = parse_args()
    config = load_config(args.config)

    base_model_name = args.base_model or config["models"]["base_model"]
    output_dir = args.output_dir or f"{config['models']['safety_model_dir']}_seed{args.seed}"
    csv_path = config["data"]["safety_sft_csv"]

    full_safety_dir = os.path.join("models", f"temp_safety_full_seed{args.seed}")

    os.makedirs(output_dir, exist_ok=True)

    verify_base_model(base_model_name)
    set_seed(args.seed)

    print(f"Loading base model: {base_model_name}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=False)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "v_proj",
            "k_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    dataset, num_examples = load_safety_dataset(csv_path)

    training_args = SFTConfig(
        output_dir=output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=10,
        num_train_epochs=args.epochs,
        save_strategy="epoch",
        eval_strategy="no",
        fp16=True,
        seed=args.seed,
        remove_unused_columns=False,
        dataset_text_field="text",
        max_length=512,
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
        args=training_args,
    )

    print("Starting SFT training...")
    trainer.train()

    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"Safety model LoRA adapter saved to {output_dir}")

    del trainer
    del model
    clear_cuda()

    if not args.skip_full_model:
        create_full_safety_model(
            base_model_name=base_model_name,
            adapter_dir=output_dir,
            full_output_dir=full_safety_dir,
            tokenizer=tokenizer,
        )

    metadata = {
        "base_model": base_model_name,
        "training_method": "SFT_LoRA",
        "dataset": csv_path,
        "num_training_examples": num_examples,
        "random_seed": args.seed,
        "adapter_output_dir": output_dir,
        "full_safety_model_dir": None if args.skip_full_model else full_safety_dir,
        "hyperparameters": {
            "learning_rate": args.lr,
            "epochs": args.epochs,
            "per_device_train_batch_size": args.batch_size,
            "gradient_accumulation_steps": 4,
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "max_length": 512,
        },
        "execution_command": " ".join(sys.argv),
        "timestamp": datetime.now().isoformat(),
    }

    metadata_path = os.path.join(output_dir, "training_metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Training metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()