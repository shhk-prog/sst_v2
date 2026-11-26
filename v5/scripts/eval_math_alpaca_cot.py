#!/usr/bin/env python3
"""SoK 数学有用性評価の修復スクリプト: WizardMath 公式 Alpaca-CoT プロンプトによる GSM8K 評価（1 件ずつ逐次保存・途中再開対応）。

背景:
  v3/scripts/eval/eval_utility.py の GSM8K 評価は
    `### Instruction:\nQuestion: ...\nAnswer:\n\n### Response:\n`
  というプロンプトを使っており、WizardMath-7B-V1.0 が CoT をスキップして即答
  (`The answer is: 12.`) するため、単体でも 6.25% に崩壊していた（公式報告 54.9%）。

本スクリプト:
  WizardMath 公式（WizardLM/WizardMath）の Alpaca-CoT プロンプト:
    Below is an instruction that describes a task. Write a response that appropriately completes the request.

    ### Instruction:
    {question}

    ### Response: Let's think step by step.
  を用いて openai/gsm8k (main, test, 先頭 limit 件) を vLLM で評価し、
  1 件推論するごとに JSON ファイルを原子保存（.tmp -> fsync -> os.replace）する。
  途中で中断しても再実行すれば未推論の 1 件目から再開できる。

制約: v3/ は読み取り専用。出力先は v5/ 配下のみ。
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
os.environ["VLLM_ENABLE_V1"] = "0"

import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
V5_ROOT = REPO_ROOT / "v5"

ALPACA_COT_TEMPLATE = (
    "Below is an instruction that describes a task. "
    "Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{question}\n\n"
    "### Response: Let's think step by step."
)

STOP_TOKENS = ["</s>", "### Instruction:", "Question:", "\n\n\n"]


def assert_inside_v5(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def write_json_atomic(path: Path, obj: Any) -> None:
    p = assert_inside_v5(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(p) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def extract_target_number(answer_str: str) -> str | None:
    m = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", str(answer_str))
    if m:
        return m.group(1).replace(",", "").strip()
    nums = re.findall(r"-?[\d,]+(?:\.\d+)?", str(answer_str))
    return nums[-1].replace(",", "").strip() if nums else None


def extract_pred_number(resp_str: str) -> str | None:
    """WizardMath 公式出力形式（The answer is: X / #### X / boxed{X} / 末尾数値）から数値を抽出する。"""
    if not isinstance(resp_str, str) or not resp_str.strip():
        return None
    text = resp_str.strip()

    # 1. WizardMath 公式形式: "The answer is: 18" / "The final answer is 18"
    m_all = re.findall(
        r"(?:the\s+(?:final\s+)?answer\s+is|final\s+answer)\s*:?\s*\$?\s*\\?boxed\{?(-?[\d,]+(?:\.\d+)?)\}?",
        text,
        flags=re.IGNORECASE,
    )
    if m_all:
        return m_all[-1].replace(",", "").strip()

    # 2. #### 18
    m_hash = re.findall(r"####\s*\$?(-?[\d,]+(?:\.\d+)?)", text)
    if m_hash:
        return m_hash[-1].replace(",", "").strip()

    # 3. \boxed{18}
    m_box = re.findall(r"\\boxed\{\s*\$?(-?[\d,]+(?:\.\d+)?)\s*\}", text)
    if m_box:
        return m_box[-1].replace(",", "").strip()

    # 4. フォールバック: 応答内の最後の数値
    nums = re.findall(r"-?[\d,]+(?:\.\d+)?", text)
    if nums:
        return nums[-1].replace(",", "").strip()
    return None


def numbers_equal(pred: str | None, target: str | None) -> bool:
    if pred is None or target is None:
        return False
    try:
        return abs(float(pred) - float(target)) < 1e-6
    except ValueError:
        return pred.strip() == target.strip()


def collect_gpu_info() -> dict[str, Any]:
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    nvidia_gpus = []
    try:
        cmd = ["nvidia-smi", "--query-gpu=index,name,uuid,driver_version", "--format=csv,noheader"]
        if cvd:
            cmd.extend(["-i", cvd])
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        for line in raw.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                nvidia_gpus.append({"index": parts[0], "name": parts[1], "uuid": parts[2], "driver": parts[3]})
    except Exception as exc:
        nvidia_gpus = [{"error": str(exc)}]
    return {
        "hostname": socket.gethostname(),
        "cuda_visible_devices": cvd,
        "nvidia_smi_gpus": nvidia_gpus,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
    }


def load_or_init_items(out_path: Path, dataset, limit: int) -> list[dict[str, Any]]:
    old_by_id: dict[int, dict[str, Any]] = {}
    if out_path.is_file():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8"))
            for row in old.get("results", []):
                if isinstance(row, dict) and "doc_id" in row:
                    old_by_id[int(row["doc_id"])] = row
        except Exception:
            pass

    n = min(limit, len(dataset)) if limit > 0 else len(dataset)
    items: list[dict[str, Any]] = []
    for doc_id in range(n):
        row = dataset[doc_id]
        question = row["question"]
        answer = row["answer"]
        target_num = extract_target_number(answer)
        prev = old_by_id.get(doc_id, {})
        items.append({
            "doc_id": doc_id,
            "question": question,
            "prompt": ALPACA_COT_TEMPLATE.format(question=question),
            "target_answer": answer,
            "target_num": target_num,
            "response": prev.get("response"),
            "pred_num": prev.get("pred_num"),
            "exact_match": prev.get("exact_match"),
        })
    return items


def build_payload(
    args: argparse.Namespace,
    items: list[dict[str, Any]],
    gpu_info: dict[str, Any],
    completed: bool,
) -> dict[str, Any]:
    done_items = [x for x in items if x.get("response") is not None]
    correct = sum(1 for x in done_items if x.get("exact_match") == 1.0)
    acc = (correct / len(done_items)) if done_items else None
    return {
        "status": "success" if completed else "running",
        "completed": completed,
        "task": "gsm8k_alpaca_cot",
        "prompt_template": "wizardmath_official_alpaca_cot",
        "model_path": args.model_path,
        "model_name": args.model_name,
        "limit": args.limit,
        "max_tokens": args.max_tokens,
        "n_total": len(items),
        "n_done": len(done_items),
        "n_correct": correct,
        "gsm8k_acc": acc,
        "gsm8k_acc_pct": (acc * 100.0) if acc is not None else None,
        "gpu_info": gpu_info,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "results": items,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--model-name", required=True)
    ap.add_argument("--output-file", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=320)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    out_path = assert_inside_v5(args.output_file)

    if not args.force and out_path.is_file():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
            if prev.get("status") == "success" and prev.get("completed") is True and prev.get("n_done") == prev.get("n_total"):
                if args.limit == 0 or prev.get("n_total", 0) >= args.limit:
                    print(
                        f"[SKIP] 完了済み: {out_path.name} (acc={prev.get('gsm8k_acc_pct', 0.0):.2f}%, "
                        f"{prev.get('n_correct')}/{prev.get('n_total')})",
                        flush=True,
                    )
                    return 0
        except Exception:
            pass

    from datasets import load_dataset

    ds = load_dataset("openai/gsm8k", "main", split="test")
    items = load_or_init_items(out_path, ds, args.limit) if not args.force else load_or_init_items(Path("/nonexistent"), ds, args.limit)
    pending = [i for i, x in enumerate(items) if x.get("response") is None]
    gpu_info = collect_gpu_info()

    print(
        f"[eval_math_alpaca_cot] model={args.model_name} | total={len(items)} | "
        f"done={len(items) - len(pending)} | pending={len(pending)}",
        flush=True,
    )

    if pending:
        from vllm import LLM, SamplingParams

        llm = LLM(
            model=args.model_path,
            trust_remote_code=True,
            tensor_parallel_size=1,
            dtype="float16",
            gpu_memory_utilization=args.gpu_memory_utilization,
        )
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=args.max_tokens,
            stop=STOP_TOKENS,
        )

        for idx in tqdm(pending, desc=f"GSM8K Alpaca-CoT ({args.model_name})"):
            prompt = items[idx]["prompt"]
            try:
                out = llm.generate([prompt], sampling_params, use_tqdm=False)
            except TypeError:
                out = llm.generate([prompt], sampling_params)
            resp = out[0].outputs[0].text.strip()
            pred_num = extract_pred_number(resp)
            is_ok = 1.0 if numbers_equal(pred_num, items[idx]["target_num"]) else 0.0
            items[idx]["response"] = resp
            items[idx]["pred_num"] = pred_num
            items[idx]["exact_match"] = is_ok
            # 1 件ごとに原子保存
            write_json_atomic(out_path, build_payload(args, items, gpu_info, completed=False))

        del llm
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # 既存応答の再採点整合性確認＋完了保存
    for x in items:
        if x.get("pred_num") is None and x.get("response") is not None:
            x["pred_num"] = extract_pred_number(x["response"])
        if x.get("exact_match") is None and x.get("response") is not None:
            x["exact_match"] = 1.0 if numbers_equal(x["pred_num"], x["target_num"]) else 0.0

    final_payload = build_payload(args, items, gpu_info, completed=True)
    write_json_atomic(out_path, final_payload)
    print(
        f"[DONE] {args.model_name}: GSM8K Alpaca-CoT = {final_payload['gsm8k_acc_pct']:.2f}% "
        f"({final_payload['n_correct']}/{final_payload['n_total']}) -> {out_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
