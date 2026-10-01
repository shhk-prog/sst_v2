"""
Utility In-Distribution (ID) Evaluation Script

FT に使用したデータセット（finance-alpaca, Magicoder）の eval split を使った
In-Distribution 評価。モデルがトレーニングデータに対してどれだけ正確に学習できたかを測定。

評価指標:
  - Finance  : ROUGE-L（生成型QAの正確性）
  - Coding   : ROUGE-L（コード生成の類似度）

補足: 実行環境のコード実行が許可されていない場合でも ROUGE は安全に使用可能。
      実行ベース (pass@1) の評価は lm-evaluation-harness で OOD 評価として実施。

Usage:
  python run_utility_id_eval.py \\
    --base_model meta-llama/Meta-Llama-3-8B-Instruct \\
    --adapter_path ../../models/utility_lora \\
    --model_name utility_lora \\
    --eval_type finance \\
    --data_path ../../data/utility_finance_eval.json \\
    --n_samples 200 \\
    --output_json ../../results/phase2_eval_results.json
"""

import os
import json
import argparse
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/src/.env"))
except ImportError:
    pass


def load_target_model(base_model: str, adapter_path: Optional[str]):
    """評価対象モデルをロードする (LoRAマージ済み)"""
    print(f"  Loading target model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )

    if adapter_path and Path(adapter_path).exists():
        print(f"  Loading LoRA adapter: {adapter_path}")
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()

    model.eval()
    return model, tokenizer


def generate_response(model, tokenizer, instruction: str, max_new_tokens: int = 512) -> str:
    """Llama-3 Instruct 形式で応答を生成"""
    prompt = (
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{instruction}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def compute_rouge_l(predictions: list[str], references: list[str]) -> float:
    """ROUGE-L スコアを計算 (rouge-score ライブラリを使用)"""
    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
        scores = []
        for pred, ref in zip(predictions, references):
            score = scorer.score(ref, pred)
            scores.append(score["rougeL"].fmeasure)
        return round(sum(scores) / len(scores), 4) if scores else 0.0
    except ImportError:
        print("  WARNING: rouge-score not installed. Using simple token overlap instead.")
        # フォールバック: 簡易トークンオーバーラップ
        scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = set(pred.lower().split())
            ref_tokens = set(ref.lower().split())
            if not ref_tokens:
                scores.append(0.0)
                continue
            overlap = len(pred_tokens & ref_tokens)
            precision = overlap / len(pred_tokens) if pred_tokens else 0
            recall = overlap / len(ref_tokens)
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0
            scores.append(f1)
        return round(sum(scores) / len(scores), 4) if scores else 0.0


def evaluate_utility_id(
    model,
    tokenizer,
    data_path: str,
    n_samples: int,
    eval_type: str,
) -> dict:
    """Utility ID 評価のメインロジック"""
    with open(data_path) as f:
        data = json.load(f)
    samples = data[:n_samples]

    predictions = []
    references = []
    detailed_results = []

    print(f"  Evaluating {len(samples)} {eval_type} ID samples...")

    for i, item in enumerate(samples):
        instruction = item.get("instruction", "")
        reference = item.get("output", "")

        if not instruction or not reference:
            continue

        # モデルで応答生成
        prediction = generate_response(model, tokenizer, instruction)
        predictions.append(prediction)
        references.append(reference)

        detailed_results.append({
            "idx": i,
            "instruction": instruction[:200] + "..." if len(instruction) > 200 else instruction,
            "reference": reference[:200] + "..." if len(reference) > 200 else reference,
            "prediction": prediction[:200] + "..." if len(prediction) > 200 else prediction,
        })

        if (i + 1) % 20 == 0:
            print(f"    [{i+1}/{len(samples)}] Generated responses so far...")

    rouge_l = compute_rouge_l(predictions, references)

    return {
        "task": f"utility_{eval_type}_id",
        "eval_type": "id",   # In-Distribution (FT使用データのeval split)
        "benchmark": f"{eval_type.capitalize()} eval split (ID)",
        "metric": "rouge_l",
        "n_samples": len(predictions),
        "rouge_l": rouge_l,
        "detailed_results": detailed_results[:20],   # 最大20件のみ保存
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str,
                        default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--eval_type", type=str, required=True,
                        choices=["finance", "coding"],
                        help="Evaluation type: finance or coding")
    parser.add_argument("--data_path", type=str, required=True,
                        help="Path to the eval split JSON")
    parser.add_argument("--n_samples", type=int, default=200,
                        help="Number of samples to evaluate")
    parser.add_argument("--output_json", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"Utility ID Evaluation [{args.eval_type}]: {args.model_name}")
    print(f"  adapter  : {args.adapter_path or '(base model)'}")
    print(f"  data     : {args.data_path}  (n={args.n_samples})")
    print(f"  eval_type: ID (FT使用データの eval split)")
    print(f"{'='*60}")

    if not Path(args.data_path).exists():
        print(f"  WARNING: Eval data not found at {args.data_path}. Skipping.")
        return

    model, tokenizer = load_target_model(args.base_model, args.adapter_path)

    results = evaluate_utility_id(
        model=model,
        tokenizer=tokenizer,
        data_path=args.data_path,
        n_samples=args.n_samples,
        eval_type=args.eval_type,
    )

    print(f"\n[Result] {args.model_name} ({args.eval_type} ID)")
    print(f"  ROUGE-L  : {results['rouge_l']:.4f}")
    print(f"  Samples  : {results['n_samples']}")

    # JSON 保存
    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if out_path.exists():
            with open(out_path) as f:
                existing = json.load(f)
        task_key = f"utility_{args.eval_type}_id"
        existing = [r for r in existing
                    if not (r.get("model") == args.model_name
                            and r.get("task") == task_key)]
        existing.append({"model": args.model_name, **results})
        with open(out_path, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  Saved to: {out_path}")


if __name__ == "__main__":
    main()
