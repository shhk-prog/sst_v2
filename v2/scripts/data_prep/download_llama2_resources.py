# scripts/data_prep/download_llama2_resources.py
import os
import sys
import json
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download
from datasets import load_dataset

# scripts フォルダをパスに追加して steering_hook をインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import steering_hook

def parse_args():
    parser = argparse.ArgumentParser(description="Download Llama-2-7B Models and Datasets")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face Access Token (for gated models like Llama-2)")
    parser.add_argument("--models_dir", type=str, default="models", help="Directory to save models")
    parser.add_argument("--data_dir", type=str, default="data", help="Directory to save datasets")
    parser.add_argument("--skip_models", action="store_true", help="Skip model downloads")
    parser.add_argument("--skip_datasets", action="store_true", help="Skip dataset downloads")
    return parser.parse_args()

def download_models(token, models_dir):
    print("=== Downloading Models ===")
    
    models = {
        "base": ("meta-llama/Llama-2-7b-hf", "Llama-2-7b-hf"),
        "math": ("WizardLMTeam/WizardMath-7B-V1.0", "WizardMath-7B-V1.0"),
        "code": ("vanillaOVO/WizardCoder-Python-7B-V1.0", "WizardCoder-Python-7B-V1.0"),
        "medical": ("medalpaca/medalpaca-7b", "medalpaca-7b")
    }
    
    for name, (repo_id, local_name) in models.items():
        local_dir = os.path.join(models_dir, local_name)
        if os.path.exists(local_dir) and os.listdir(local_dir):
            print(f"Model {local_name} already exists. Skipping download.")
            continue
            
        print(f"Downloading {repo_id} to {local_dir}...")
        try:
            # Llama-2-7b-hf はゲート付きのため、トークンが必要
            use_token = token or os.getenv("HF_TOKEN")
            snapshot_download(
                repo_id=repo_id,
                local_dir=local_dir,
                token=use_token,
                ignore_patterns=["*.msgpack", "*.h5", "*.ot"] # メモリ節約のため不要なウェイト形式を弾く
            )
            print(f"Successfully downloaded {local_name}")
        except Exception as e:
            print(f"Error downloading model {repo_id}: {e}")
            if name == "base":
                print("[WARNING] Llama-2-7b-hf is gated. Please provide a valid HF_TOKEN via environment variable or --token argument.")

def download_datasets(data_dir):
    print("=== Downloading Datasets ===")
    os.makedirs(data_dir, exist_ok=True)
    
    # 1. WizardMath
    math_path = os.path.join(data_dir, "utility_gsm8k.json")
    if not os.path.exists(math_path):
        print("Downloading WizardMath Dataset (GSM8K source)...")
        try:
            dataset = load_dataset("WizardLMTeam/WizardMath", split="train")
            formatted = [{"instruction": item["question"], "output": item["answer"]} for item in dataset]
            with open(math_path, "w", encoding="utf-8") as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(formatted)} records to {math_path}")
        except Exception as e:
            print(f"Error downloading WizardMath dataset: {e}")
            
    # 2. Evol-Instruct-Code
    code_path = os.path.join(data_dir, "utility_coding.json")
    if not os.path.exists(code_path):
        print("Downloading Evol-Instruct-Code Dataset...")
        try:
            dataset = load_dataset("nickrosh/Evol-Instruct-Code-80k-v1", split="train")
            formatted = [{"instruction": item["instruction"], "output": item["output"]} for item in dataset]
            with open(code_path, "w", encoding="utf-8") as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(formatted)} records to {code_path}")
        except Exception as e:
            print(f"Error downloading Evol-Instruct-Code dataset: {e}")
            
    # 3. MedAlpaca
    med_path = os.path.join(data_dir, "utility_pubmedqa.json")
    if not os.path.exists(med_path):
        print("Downloading MedAlpaca Dataset...")
        try:
            # medalpaca/medalpaca-7b に付属、または医療QAデータソース
            dataset = load_dataset("medalpaca/medalpaca-10k", split="train")
            formatted = [{"instruction": item["instruction"] + "\n" + item["input"], "output": item["output"]} for item in dataset]
            with open(med_path, "w", encoding="utf-8") as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(formatted)} records to {med_path}")
        except Exception as e:
            print(f"Error downloading MedAlpaca dataset: {e}")

def main():
    args = parse_args()
    
    # Kiro 仕様に基づく validation チェックのダミー実行
    class DummyArgs:
        pass
    dargs = DummyArgs()
    dargs.base_model = "meta-llama/Llama-2-7b-hf"
    dargs.method = "diagonal_sst"
    steering_hook.verify_experiment_config(dargs)
    
    models_dir = os.path.abspath(args.models_dir)
    data_dir = os.path.abspath(args.data_dir)
    
    if not args.skip_models:
        download_models(args.token, models_dir)
    if not args.skip_datasets:
        download_datasets(data_dir)
        
    print("Download process complete.")

if __name__ == "__main__":
    main()
