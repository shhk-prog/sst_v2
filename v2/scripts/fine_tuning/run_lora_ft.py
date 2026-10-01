import os
import sys
import argparse
import random
from datasets import load_dataset, concatenate_datasets
from transformers import AutoModelForCausalLM, AutoTokenizer, EarlyStoppingCallback
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig
import torch

# scripts フォルダをパスに追加して steering_hook をインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import steering_hook

# TRL 1.4.0: DataCollatorForCompletionOnlyLM は廃止されています。
# 代わりに messages (Conversational) 形式 + SFTConfig(assistant_only_loss=True) を使用します。

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/src/.env"))
except ImportError:
    pass

from chat_template_utils import get_custom_chat_template


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--utility_dataset_path", type=str, default=None,
                        help="Path to the Utility JSON dataset (train split)")
    parser.add_argument("--eval_dataset_path", type=str, default=None,
                        help="Path to the eval JSON dataset for validation loss monitoring (enables early stopping)")
    parser.add_argument("--safety_dataset_path", type=str, default=None,
                        help="Path to the Safety JSON dataset")
    parser.add_argument("--safety_mix_ratio", type=float, default=1.0,
                        help="Ratio of Safety data in the mixed dataset (0.0 to 1.0)")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Where to save the LoRA weights")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning_rate", type=float, default=5e-5,
                        help="Learning rate. Default 5e-5 is more stable than 1e-4 for LoRA utility tuning")
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32,
                        help="LoRA alpha. Default 32 = rank*2 for stable learning")
    parser.add_argument("--warmup_ratio", type=float, default=0.05,
                        help="Warmup ratio for LR scheduler (prevents instability at start)")
    parser.add_argument("--max_length", type=int, default=1024)
    parser.add_argument(
        "--no_early_stopping",
        action="store_true",
        help="Disable EarlyStoppingCallback even when eval_dataset is set (train full epochs)",
    )
    parser.add_argument(
        "--early_stopping_patience",
        type=int,
        default=3,
        help="Early stopping patience when eval_dataset is used (ignored if --no_early_stopping)",
    )
    parser.add_argument(
        "--assistant_only_loss",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Train only on assistant tokens (default: True). Use --no-assistant_only_loss for full-sequence loss.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 自動検証フックの呼び出し (一括チェック)
    steering_hook.verify_experiment_config(args)

    if not torch.cuda.is_available():
        print("Error: CUDA is not available. Please check your GPU driver and PyTorch version.")
        return

    print(f"Loading model: {args.model_name_or_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if tokenizer.chat_template is None:
        template = get_custom_chat_template(args.model_name_or_path)
        tokenizer.chat_template = template
        print(f"Set custom chat template for {args.model_name_or_path}")

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

    def format_as_messages(example):
        """TRL 1.4.0 Conversational 形式に変換。
        SFTConfig(assistant_only_loss=True) と組み合わせることで、
        assistant の回答部分のみを学習対象にする (プロンプトはマスクされる)。
        """
        instruction = example.get("instruction", "")
        output = example.get("output", "")
        return {
            "messages": [
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": output},
            ]
        }

    dataset = dataset.map(format_as_messages, remove_columns=dataset.column_names)

    # バリデーションデータセットの準備 (指定時のみ early stopping が有効)
    eval_dataset = None
    has_eval = False
    if args.eval_dataset_path and os.path.exists(args.eval_dataset_path):
        eval_ds_raw = load_dataset("json", data_files=args.eval_dataset_path)["train"]
        eval_dataset = eval_ds_raw.map(format_as_messages, remove_columns=eval_ds_raw.column_names)
        has_eval = True
        print(f"Eval dataset loaded: {len(eval_dataset)} samples from {args.eval_dataset_path}")

    use_early_stopping = has_eval and not args.no_early_stopping

    # has_eval に応じて保存戦略を切り替え
    if has_eval:
        save_strategy = "steps"
        eval_strategy = "steps"
        eval_steps = 100
        save_steps = 100
        load_best_model_at_end = use_early_stopping
        metric_for_best = "eval_loss" if use_early_stopping else None
    else:
        save_strategy = "epoch"
        eval_strategy = "no"
        eval_steps = 500          # 使われないが型エラー回避
        save_steps = 500
        load_best_model_at_end = False
        metric_for_best = None

    if has_eval and args.no_early_stopping:
        print(
            "  Early stopping disabled: training will run for all epochs "
            f"({args.epochs}); last checkpoint is saved at end."
        )

    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        logging_steps=10,
        save_strategy=save_strategy,
        eval_strategy=eval_strategy,
        eval_steps=eval_steps,
        save_steps=save_steps,
        load_best_model_at_end=load_best_model_at_end,
        metric_for_best_model=metric_for_best,
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        report_to="none",
        # TRL 1.4.0: messages 形式 + assistant_only_loss で回答部分のみを学習対象にする。
        # dataset_text_field は messages 形式では不要 (SFTTrainer が自動検出する)。
        assistant_only_loss=args.assistant_only_loss,
        max_length=args.max_length,
    )

    print(f"  assistant_only_loss={args.assistant_only_loss}")

    callbacks = []
    if use_early_stopping:
        callbacks.append(
            EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience)
        )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        args=training_args,
        callbacks=callbacks if callbacks else None,
    )

    print("Starting training...")
    trainer.train()

    if use_early_stopping and trainer.state.best_model_checkpoint:
        best_ckpt = trainer.state.best_model_checkpoint
        print(f"\n[Info] Early stopping was used. Best checkpoint found at: {best_ckpt}")
        print(f"       This best model will be saved to: {args.output_dir}")

    print(f"Saving final adapter to {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    if use_early_stopping and trainer.state.best_model_checkpoint:
        import shutil
        best_dir = args.output_dir + "_best"
        print(f"Creating a distinct copy of the best model at: {best_dir}")
        shutil.copytree(args.output_dir, best_dir, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
