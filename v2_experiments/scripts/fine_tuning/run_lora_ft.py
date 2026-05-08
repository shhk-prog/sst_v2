import os
import argparse
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--utility_dataset_path", type=str, default=None, help="Path to the Utility JSON dataset")
    parser.add_argument("--safety_dataset_path", type=str, default=None, help="Path to the Safety JSON dataset")
    parser.add_argument("--safety_mix_ratio", type=float, default=1.0, help="Ratio of Safety data in the mixed dataset (0.0 to 1.0)")
    parser.add_argument("--output_dir", type=str, required=True, help="Where to save the LoRA weights")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    return parser.parse_args()

def main():
    args = parse_args()
    
    print(f"Loading model: {args.model_name_or_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        device_map="auto",
        torch_dtype="auto"
    )
    
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    print("Loading dataset(s)...")
    from datasets import concatenate_datasets
    import random
    
    util_ds, safe_ds = None, None
    if args.utility_dataset_path:
        util_ds = load_dataset("json", data_files=args.utility_dataset_path)["train"]
    if args.safety_dataset_path:
        safe_ds = load_dataset("json", data_files=args.safety_dataset_path)["train"]
        
    if util_ds is None and safe_ds is None:
        raise ValueError("At least one of --utility_dataset_path or --safety_dataset_path must be provided.")
        
    if util_ds is not None and safe_ds is not None:
        ratio = args.safety_mix_ratio
        if ratio >= 1.0:
            dataset = safe_ds
            print("Using 100% Safety data.")
        elif ratio <= 0.0:
            dataset = util_ds
            print("Using 100% Utility data.")
        else:
            target_safe_size = len(safe_ds)
            target_util_size = int(target_safe_size * (1.0 - ratio) / ratio)
            
            if target_util_size > len(util_ds):
                util_indices = [random.randint(0, len(util_ds)-1) for _ in range(target_util_size)]
                sampled_util = util_ds.select(util_indices)
            else:
                sampled_util = util_ds.shuffle(seed=42).select(range(target_util_size))
                
            dataset = concatenate_datasets([safe_ds, sampled_util]).shuffle(seed=42)
            print(f"Mixed dataset: Safety={target_safe_size} ({ratio*100}%), Utility={target_util_size} ({(1-ratio)*100}%)")
    else:
        dataset = util_ds if util_ds is not None else safe_ds
        print(f"Using single dataset. Total samples: {len(dataset)}")
    
    def format_prompt(example):
        instruction = example.get("instruction", "")
        output = example.get("output", "")
        prompt = f"<|start_header_id|>user<|end_header_id|>\n\n{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{output}<|eot_id|>"
        return {"text": prompt}
        
    dataset = dataset.map(format_prompt)
    
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        report_to="none"
    )
    
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=1024,
        args=training_args
    )
    
    print("Starting training...")
    trainer.train()
    
    print(f"Saving final adapter to {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

if __name__ == "__main__":
    main()
