import os
import json
import argparse
import urllib.request
import csv
import io
import random
from datasets import load_dataset

from coding_data_utils import (
    extract_code_from_output,
    is_python_sample,
    process_output,
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

def prepare_utility_finance_data():
    """
    Finance Utility データセット: finance-alpaca (推論型QA)
    変更理由: FinGPT-sentiment はセンチメント分類タスクであり、MMLU形式の多選択評価と
              形式が根本的に不一致。finance-alpaca は instruction-following 型の金融QAで
              MMLU の知識問題との転移学習効果が高い。
    分割: train (4500件) + eval (500件) の90/10分割
    """
    print("Preparing Finance Utility Dataset (finance-alpaca)...")
    try:
        dataset = load_dataset("gbharti/finance-alpaca", split="train")
        formatted_data = []
        for item in dataset:
            instruction = item.get("instruction", "")
            text_input = item.get("input", "")
            output = item.get("output", "")
            if not instruction or not output:
                continue
            # input がある場合は instruction に結合
            if text_input:
                full_instruction = f"{instruction}\n\n{text_input}"
            else:
                full_instruction = instruction
            formatted_data.append({
                "instruction": full_instruction,
                "output": output
            })
            if len(formatted_data) >= 5000:
                break

        # 90/10 でtrain/evalに分割
        random.seed(42)
        random.shuffle(formatted_data)
        n_train = 4500
        train_data = formatted_data[:n_train]
        eval_data = formatted_data[n_train:]

        train_path = os.path.join(DATA_DIR, "utility_finance.json")
        eval_path = os.path.join(DATA_DIR, "utility_finance_eval.json")

        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved {len(train_data)} train records to {train_path}")
        print(f"  Saved {len(eval_data)} eval records to {eval_path}")

    except Exception as e:
        print(f"Error preparing Finance Utility data: {e}")
        raise

def prepare_safety_data():
    """
    Safety (Jailbreak等) データセットのダウンロードと前処理
    分割: train (90%) + eval (10%)
    """
    print("Preparing Safety Dataset (AdvBench & TrustLLM JailbreakTrigger)...")
    try:
        formatted_data = []

        # 1. AdvBench のデータを取得
        print("  Loading AdvBench...")
        url = "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv"
        response = urllib.request.urlopen(url)
        csv_content = response.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_content))
        refusal_response = "I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant. My safety guidelines strictly prohibit me from assisting with harmful, illegal, unethical, or dangerous activities."
        
        for row in reader:
            if 'goal' in row:
                formatted_data.append({
                    "instruction": row['goal'],
                    "output": refusal_response,
                    "source": "advbench"
                })

        # 2. TrustLLM Jailbreak Trigger を取得 (1400件)
        print("  Loading TrustLLM JailbreakTrigger (Official Gated)...")
        try:
            token = os.getenv("HUGGINGFACE_HUB_TOKEN")
            trust_ds = load_dataset(
                "json", 
                data_files="hf://datasets/TrustLLM/TrustLLM-dataset/safety/jailbreak.json",
                token=token,
                split="train"
            )
            for item in trust_ds:
                instr = item.get("prompt")
                if instr:
                    formatted_data.append({
                        "instruction": instr,
                        "output": refusal_response,
                        "source": "trustllm_jailbreak"
                    })
        except Exception as e:
            print(f"  Warning: Could not load official TrustLLM: {e}. Falling back to Tulu subset...")
            try:
                trust_ds = load_dataset("allenai/tulu-3-trustllm-jailbreaktrigger-eval", split="test")
                for item in trust_ds:
                    instr = item.get("prompt") or item.get("instruction")
                    if instr:
                        formatted_data.append({
                            "instruction": instr,
                            "output": refusal_response,
                            "source": "trustllm_jailbreak_tulu"
                        })
            except Exception as e2:
                print(f"  Warning: Could not load Tulu TrustLLM: {e2}.")
        
        # シャッフルして 90/10 に分割
        random.seed(42)
        random.shuffle(formatted_data)
        n_train = int(len(formatted_data) * 0.9)
        train_data = formatted_data[:n_train]
        eval_data = formatted_data[n_train:]

        train_path = os.path.join(DATA_DIR, "safety_combined.json")
        eval_path = os.path.join(DATA_DIR, "safety_combined_eval.json")

        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved {len(train_data)} train records to {train_path}")
        print(f"  Saved {len(eval_data)} eval records to {eval_path}")
        
        # 互換性のために古い名前でもコピー
        old_path = os.path.join(DATA_DIR, "safety_advbench.json")
        with open(old_path, "w", encoding="utf-8") as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error preparing Safety data: {e}")

def prepare_harmbench_data():
    """
    HarmBench データセット: Safety OOD 評価用 (FT未使用データ)
    AdvBench/TrustLLM と重複しない独立したSafety評価ベンチマーク。
    LED-Merging (ACL 2025) が採用。
    """
    print("Preparing HarmBench Dataset (Safety OOD eval)...")
    try:
        # walledai/HarmBench から標準的な harmful behaviors を取得
        try:
            ds = load_dataset("walledai/HarmBench", split="train")
            formatted_data = []
            for item in ds:
                prompt = item.get("prompt") or item.get("behavior") or item.get("instruction")
                if prompt:
                    formatted_data.append({
                        "instruction": prompt,
                        "source": "harmbench"
                    })
            print(f"  Loaded {len(formatted_data)} records from walledai/HarmBench")
        except Exception as e1:
            print(f"  walledai/HarmBench failed: {e1}. Trying CSV fallback...")
            # HarmBench の公開CSV (standard_behaviors)
            url = "https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv"
            try:
                response = urllib.request.urlopen(url, timeout=30)
                csv_content = response.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(csv_content))
                formatted_data = []
                for row in reader:
                    prompt = row.get("Behavior") or row.get("behavior") or row.get("prompt")
                    if prompt:
                        formatted_data.append({
                            "instruction": prompt,
                            "source": "harmbench_csv"
                        })
                print(f"  Loaded {len(formatted_data)} records from HarmBench CSV")
            except Exception as e2:
                print(f"  HarmBench CSV failed: {e2}. Creating minimal fallback...")
                formatted_data = []

        if formatted_data:
            out_path = os.path.join(DATA_DIR, "safety_harmbench.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(formatted_data)} records to {out_path}")
        else:
            print("  Warning: HarmBench data could not be loaded. Skipping.")

    except Exception as e:
        print(f"Error preparing HarmBench data: {e}")

def prepare_xstest_data():
    """XSTest データセットのダウンロードと前処理"""
    print("Preparing XSTest Dataset...")
    try:
        url = "https://raw.githubusercontent.com/paul-rottger/xstest/main/xstest_prompts.csv"
        response = urllib.request.urlopen(url)
        csv_content = response.read().decode('utf-8')
        
        reader = csv.DictReader(io.StringIO(csv_content))
        formatted_data = []
        
        for row in reader:
            # XSTestのCSVカラムに合わせた処理
            prompt = row.get('prompt', '')
            if prompt:
                formatted_data.append({
                    "type": row.get('type', ''),
                    "prompt": prompt
                })
                
        out_path = os.path.join(DATA_DIR, "xstest_prompts.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(formatted_data)} records to {out_path}")
    except Exception as e:
        print(f"Error preparing XSTest data: {e}")

def _collect_magicoder_samples(
    *,
    max_samples: int = 5000,
    python_only: bool = False,
    clean_output: bool = False,
    clean_mode: str = "aggressive",
) -> list[dict]:
    """Magicoder から instruction/output リストを構築。"""
    dataset = load_dataset("ise-uiuc/Magicoder-OSS-Instruct-75K", split="train")
    formatted_data = []
    n_skipped_empty = 0
    n_skipped_lang = 0

    for item in dataset:
        instruction = item.get("problem", "")
        output_raw = item.get("solution", "")
        if not (instruction and output_raw):
            continue
        if python_only and not is_python_sample(instruction, output_raw):
            n_skipped_lang += 1
            continue
        output = process_output(
            output_raw, clean_output=clean_output, clean_mode=clean_mode
        )
        if not output:
            n_skipped_empty += 1
            continue
        formatted_data.append({"instruction": instruction, "output": output})
        if len(formatted_data) >= max_samples:
            break

    print(f"  Collected {len(formatted_data)} samples")
    if python_only:
        print(f"  Skipped (non-Python): {n_skipped_lang}")
    if clean_output:
        print(f"  Skipped (empty after clean): {n_skipped_empty}")
    return formatted_data


def _save_train_eval_split(
    formatted_data: list[dict],
    train_path: str,
    eval_path: str,
    n_train: int | None = 4500,
    eval_ratio: float = 0.1,
    min_eval: int = 100,
) -> None:
    """train/eval 分割。n_train=None またはデータ件数未満のとき eval_ratio で分割。"""
    random.seed(42)
    random.shuffle(formatted_data)
    n = len(formatted_data)
    if n < 2:
        raise ValueError(f"Need at least 2 samples, got {n}")

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


def prepare_coding_data(
    *,
    clean_output: bool = False,
    clean_mode: str = "aggressive",
) -> None:
    """
    コーディングデータ (Magicoder) — 全言語 mix。
    Phase 2a では clean_output=False（生 solution）を推奨。
    """
    print("Preparing Coding Dataset (Magicoder OSS-INSTRUCT, all languages)...")
    print(f"  clean_output={clean_output}, clean_mode={clean_mode}")
    suffix = "_clean" if clean_output else ""
    try:
        formatted_data = _collect_magicoder_samples(
            max_samples=5000,
            python_only=False,
            clean_output=clean_output,
            clean_mode=clean_mode,
        )
        _save_train_eval_split(
            formatted_data,
            os.path.join(DATA_DIR, f"utility_coding{suffix}.json"),
            os.path.join(DATA_DIR, f"utility_coding{suffix}_eval.json"),
        )
    except Exception as e:
        print(f"Error preparing Coding data: {e}")
        raise


def prepare_coding_data_python_only(
    *,
    clean_output: bool = False,
    clean_mode: str = "aggressive",
    max_samples: int = 5000,
    n_train: int = 4500,
) -> None:
    """
    Python サブセットのみ — HumanEval / MBPP 向け。
    出力: utility_coding_python.json / utility_coding_python_eval.json
    """
    print("Preparing Coding Dataset (Magicoder, Python-only)...")
    print(f"  clean_output={clean_output}, clean_mode={clean_mode}")
    suffix = "_clean" if clean_output else ""
    try:
        formatted_data = _collect_magicoder_samples(
            max_samples=max_samples,
            python_only=True,
            clean_output=clean_output,
            clean_mode=clean_mode,
        )
        _save_train_eval_split(
            formatted_data,
            os.path.join(DATA_DIR, f"utility_coding_python{suffix}.json"),
            os.path.join(DATA_DIR, f"utility_coding_python{suffix}_eval.json"),
            n_train=n_train,
        )
    except Exception as e:
        print(f"Error preparing Python coding data: {e}")
        raise


def prepare_coding_data_python_from_existing(
    source_train: str,
    source_eval: str | None = None,
) -> None:
    """既存 utility_coding*.json から Python のみを抽出（再ダウンロード不要）。"""
    print("Filtering existing coding JSON to Python-only...")
    with open(source_train, encoding="utf-8") as f:
        train_raw = json.load(f)
    eval_raw = []
    if source_eval and os.path.exists(source_eval):
        with open(source_eval, encoding="utf-8") as f:
            eval_raw = json.load(f)
    combined = train_raw + eval_raw
    filtered = [
        ex
        for ex in combined
        if is_python_sample(ex.get("instruction", ""), ex.get("output", ""))
    ]
    print(f"  {len(combined)} -> {len(filtered)} Python samples")
    _save_train_eval_split(
        filtered,
        os.path.join(DATA_DIR, "utility_coding_python.json"),
        os.path.join(DATA_DIR, "utility_coding_python_eval.json"),
        n_train=None,
        eval_ratio=0.1,
        min_eval=100,
    )


def main():
    parser = argparse.ArgumentParser(description="Prepare SST v2 datasets")
    parser.add_argument(
        "--coding-python-only",
        action="store_true",
        help="Build utility_coding_python.json (Python subset)",
    )
    parser.add_argument(
        "--coding-python-from-existing",
        action="store_true",
        help="Filter existing utility_coding.json to Python (no HF download)",
    )
    parser.add_argument(
        "--coding-only",
        action="store_true",
        help="Only run coding dataset prep (skip finance/safety/...)",
    )
    parser.add_argument(
        "--clean-coding-output",
        action="store_true",
        help="Apply code-block extraction to coding outputs (legacy aggressive clean)",
    )
    parser.add_argument(
        "--clean-mode",
        choices=["aggressive", "tail_only"],
        default="aggressive",
        help="clean-coding-output mode: aggressive=inside fence only; tail_only=drop text after closing fence",
    )
    args = parser.parse_args()
    clean = args.clean_coding_output

    if args.coding_python_from_existing:
        prepare_coding_data_python_from_existing(
            os.path.join(DATA_DIR, "utility_coding.json"),
            os.path.join(DATA_DIR, "utility_coding_eval.json"),
        )
        return

    if args.coding_python_only:
        prepare_coding_data_python_only(
            clean_output=clean,
            clean_mode=args.clean_mode,
        )
        return

    if args.coding_only:
        prepare_coding_data(clean_output=clean, clean_mode=args.clean_mode)
        return

    prepare_utility_finance_data()
    prepare_safety_data()
    prepare_harmbench_data()
    prepare_xstest_data()
    prepare_coding_data(clean_output=clean, clean_mode=args.clean_mode)
    print("Data preparation complete.")


if __name__ == "__main__":
    main()
