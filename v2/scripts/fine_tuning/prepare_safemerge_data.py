import os
import json
import argparse
import random
from datasets import load_dataset

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

def _save_train_eval_split(formatted_data, train_path, eval_path, n_train=None, eval_ratio=0.1, min_eval=100):
    random.seed(42)
    random.shuffle(formatted_data)
    n = len(formatted_data)
    if n < 2:
        print("Not enough data to split.")
        return

    if n_train is None or n_train >= n:
        n_eval = max(min_eval, int(n * eval_ratio))
        n_eval = min(n_eval, max(1, n // 5), n - 1)
        train_data = formatted_data[:-n_eval]
        eval_data = formatted_data[-n_eval:]
    else:
        n_train = min(n_train, n - 1)
        train_data = formatted_data[:n_train]
        eval_data = formatted_data[n_train:]
        
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(train_data)} train -> {train_path}")
    print(f"  Saved {len(eval_data)} eval  -> {eval_path}")


def prepare_gsm8k_data(n_train=7000):
    print("Preparing GSM8K Dataset (Math)...")
    try:
        ds = load_dataset("openai/gsm8k", "main", split="train")
        formatted_data = []
        for item in ds:
            q = item.get("question")
            a = item.get("answer")
            if q and a:
                formatted_data.append({
                    "instruction": q,
                    "output": a
                })
                
        train_path = os.path.join(DATA_DIR, "utility_gsm8k.json")
        eval_path = os.path.join(DATA_DIR, "utility_gsm8k_eval.json")
        _save_train_eval_split(formatted_data, train_path, eval_path, n_train=n_train)
    except Exception as e:
        print(f"Error preparing GSM8K data: {e}")


def prepare_pubmedqa_data(n_train=4500):
    print("Preparing PubMedQA Dataset (Biomedical)...")
    try:
        ds = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split="train")
        formatted_data = []
        for item in ds:
            q = item.get("question")
            context_dict = item.get("context", {})
            contexts = context_dict.get("contexts", [])
            context_str = " ".join(contexts) if contexts else ""
            
            a = item.get("long_answer")
            if not a:
                continue
                
            instruction = q
            if context_str:
                instruction = f"Context: {context_str}\n\nQuestion: {q}"
                
            formatted_data.append({
                "instruction": instruction,
                "output": a
            })
            
        train_path = os.path.join(DATA_DIR, "utility_pubmedqa.json")
        eval_path = os.path.join(DATA_DIR, "utility_pubmedqa_eval.json")
        _save_train_eval_split(formatted_data, train_path, eval_path, n_train=n_train)
    except Exception as e:
        print(f"Error preparing PubMedQA data: {e}")


def prepare_safeinstruct_data(n_samples=2500):
    print("Preparing SafeInstruct Dataset (Bianchi et al.)...")
    try:
        # Load SafeInstruct or use AdvBench as fallback
        ds = load_dataset("federicobianchi/SafeInstruct", split="train")
        formatted_data = []
        for item in ds:
            instruction = item.get("instruction")
            output = item.get("response") or item.get("output")
            if instruction and output:
                formatted_data.append({
                    "instruction": instruction,
                    "output": output,
                    "source": "safeinstruct"
                })
        
        train_path = os.path.join(DATA_DIR, f"safety_safeinstruct_{n_samples}.json")
        eval_path = os.path.join(DATA_DIR, "safety_safeinstruct_eval.json")
        
        random.seed(42)
        random.shuffle(formatted_data)
        
        if len(formatted_data) > n_samples:
            eval_data = formatted_data[n_samples:n_samples+200]
            train_data = formatted_data[:n_samples]
        else:
            eval_data = formatted_data[-200:]
            train_data = formatted_data[:-200]
            
        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)
            
        print(f"  Saved {len(train_data)} train -> {train_path}")
        print(f"  Saved {len(eval_data)} eval -> {eval_path}")

    except Exception as e:
        print(f"Error preparing SafeInstruct data: {e}")
        print("Falling back to safety_combined.json if it exists...")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_gsm8k", type=int, default=7000)
    parser.add_argument("--n_pubmedqa", type=int, default=4500)
    parser.add_argument("--n_safe", type=int, default=2500)
    args = parser.parse_args()

    prepare_gsm8k_data(n_train=args.n_gsm8k)
    prepare_pubmedqa_data(n_train=args.n_pubmedqa)
    prepare_safeinstruct_data(n_samples=args.n_safe)
    print("SafeMERGE data preparation complete.")

if __name__ == "__main__":
    main()
