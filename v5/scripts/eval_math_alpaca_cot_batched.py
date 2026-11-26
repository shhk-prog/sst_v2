#!/usr/bin/env python3
"""GSM8K 全 1,319 問用の高速バッチ推論ラッパー（ロック済み eval_math_alpaca_cot.py の設定・採点をそのまま import）。

設計方針:
  - eval_lock.yaml にロックされた v5/scripts/eval_math_alpaca_cot.py を一切改変せず、
    実行時に SHA256 を検証したうえで ALPACA_COT_TEMPLATE, STOP_TOKENS,
    extract_pred_number, extract_target_number, numbers_equal, load_or_init_items,
    build_payload, write_json_atomic をそのまま import して使用する。
  - 推論のみ 1 件ずつの llm.generate([prompt]) からチャンク単位の llm.generate(batch_prompts)
    に変更し、チャンクごとに原子保存（.tmp -> fsync -> os.replace）することで
    途中再開性と約 20〜30 倍の高速化（24 本を約 40〜50 分）を両立する。
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

EXPECTED_LOCKED_SHA256 = "9157a6ef1da80d7a71040c41cce6f5d8dcffaf353926e450e1e202775a47077e"

import eval_math_alpaca_cot as locked_eval  # noqa: E402


def verify_locked_script_sha256() -> str:
    src = Path(locked_eval.__file__).resolve()
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if digest != EXPECTED_LOCKED_SHA256:
        raise RuntimeError(
            f"ロック済み eval_math_alpaca_cot.py の SHA256 が一致しません: "
            f"actual={digest} expected={EXPECTED_LOCKED_SHA256}"
        )
    return digest


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--model-name", required=True)
    ap.add_argument("--output-file", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=1319)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def main() -> int:
    locked_sha = verify_locked_script_sha256()
    args = parse_args()
    out_path = locked_eval.assert_inside_v5(args.output_file)

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

    import torch
    from datasets import load_dataset

    ds = load_dataset("openai/gsm8k", "main", split="test")
    items = (
        locked_eval.load_or_init_items(out_path, ds, args.limit)
        if not args.force
        else locked_eval.load_or_init_items(Path("/nonexistent"), ds, args.limit)
    )
    pending = [i for i, x in enumerate(items) if x.get("response") is None]
    gpu_info = locked_eval.collect_gpu_info()

    print(
        f"[eval_math_alpaca_cot_batched] model={args.model_name} | total={len(items)} | "
        f"done={len(items) - len(pending)} | pending={len(pending)} | batch_size={args.batch_size} | "
        f"locked_sha256={locked_sha[:12]}",
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
            stop=locked_eval.STOP_TOKENS,
        )

        bs = max(1, int(args.batch_size))
        for start in range(0, len(pending), bs):
            chunk_idx = pending[start : start + bs]
            prompts = [items[i]["prompt"] for i in chunk_idx]
            try:
                outs = llm.generate(prompts, sampling_params, use_tqdm=True)
            except TypeError:
                outs = llm.generate(prompts, sampling_params)

            for idx, out in zip(chunk_idx, outs):
                resp = out.outputs[0].text.strip()
                pred_num = locked_eval.extract_pred_number(resp)
                is_ok = 1.0 if locked_eval.numbers_equal(pred_num, items[idx]["target_num"]) else 0.0
                items[idx]["response"] = resp
                items[idx]["pred_num"] = pred_num
                items[idx]["exact_match"] = is_ok

            payload = locked_eval.build_payload(args, items, gpu_info, completed=False)
            payload["inference_mode"] = f"batched_vllm_bs{bs}"
            payload["locked_eval_script_sha256"] = locked_sha
            locked_eval.write_json_atomic(out_path, payload)
            print(
                f"  [chunk {start + len(chunk_idx)}/{len(pending)}] "
                f"acc_so_far={payload['gsm8k_acc_pct']:.2f}% ({payload['n_correct']}/{payload['n_done']})",
                flush=True,
            )

        del llm
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    for x in items:
        if x.get("pred_num") is None and x.get("response") is not None:
            x["pred_num"] = locked_eval.extract_pred_number(x["response"])
        if x.get("exact_match") is None and x.get("response") is not None:
            x["exact_match"] = 1.0 if locked_eval.numbers_equal(x["pred_num"], x["target_num"]) else 0.0

    final_payload = locked_eval.build_payload(args, items, gpu_info, completed=True)
    final_payload["inference_mode"] = f"batched_vllm_bs{max(1, int(args.batch_size))}"
    final_payload["locked_eval_script_sha256"] = locked_sha
    locked_eval.write_json_atomic(out_path, final_payload)
    print(
        f"[DONE] {args.model_name}: GSM8K Alpaca-CoT (batched) = {final_payload['gsm8k_acc_pct']:.2f}% "
        f"({final_payload['n_correct']}/{final_payload['n_total']}) -> {out_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
