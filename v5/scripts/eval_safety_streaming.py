#!/usr/bin/env python3
"""SoK 実証 2 用: 安全性評価スクリプト（生成・分類ともに 1 件ずつ逐次保存・途中再開対応）。

v3/scripts/eval/eval_safety.py を改変せずに再利用しつつ、以下の点を強化する:
  1. 生成フェーズ（--use_vllm / HF 共通）: 320 件まとめてではなく **1 件推論するごとに**
     原子保存（.tmp -> os.replace）する。途中でプロセスが落ちても直前の 1 件まで完全に残る。
  2. 分類フェーズ（HarmBench / StrongREJECT / WildGuard）: 1 件分類するごとに原子保存。
  3. 途中再開（resume）: 既存の `response`（空文字 "" を含む）・`asr`・`original_asr`・
     `classifier_output`・`is_gibberish`・`harmbench_cls_*` をすべて保持したまま未処理分のみ実行する。
  4. 安全装置: 出力先が必ず `v5/` 配下であることを検証（`v3/` は読み取り専用）。
"""

from __future__ import annotations

import os

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
os.environ["VLLM_ENABLE_V1"] = "0"

import sys
import traceback
from pathlib import Path

import torch
import yaml
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"

sys.path.insert(0, str(V3_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(V3_ROOT / "scripts" / "tests"))

import eval_safety as v3_eval_safety  # noqa: E402
import steering_hook  # noqa: E402


def assert_inside_v5(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def init_or_resume_results_preserve_all(args, task, output_file, prompts, dataset_path):
    """途中再開時に既存の全フィールド（空応答・分類済みフィールド含む）を落とさず復元する。"""
    old_results, _ = v3_eval_safety.load_existing_results(output_file)
    by_prompt = {
        r.get("prompt"): r
        for r in old_results
        if isinstance(r, dict) and r.get("prompt")
    }

    results = []
    for prompt in prompts:
        old = by_prompt.get(prompt, {})
        rec = {
            "prompt": prompt,
            "response": old.get("response"),
            "asr": old.get("asr"),
            "classifier_output": old.get("classifier_output"),
        }
        for extra_k in ("original_asr", "is_gibberish", "harmbench_cls_asr", "harmbench_cls_output"):
            if extra_k in old:
                rec[extra_k] = old[extra_k]
        results.append(rec)

    v3_eval_safety.save_checkpoint(args, task, output_file, dataset_path, results, completed=False)
    return results


def main() -> int:
    args = v3_eval_safety.parse_args()

    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if not tasks:
        print("No tasks specified.")
        return 0

    num_threads = int(os.environ.get("OMP_NUM_THREADS", os.environ.get("SLURM_CPUS_PER_TASK", 16)))
    if torch.cuda.is_available():
        torch.set_num_threads(num_threads)
    print(f"[eval_safety_streaming] Configured PyTorch CPU threads: {num_threads}", flush=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    task_configs = []
    for task in tasks:
        if args.output_dir and args.model_name:
            out_file = os.path.join(args.output_dir, f"{args.model_name}_{task}_safety.json")
        else:
            out_file = args.output_file if len(tasks) == 1 else args.output_file.replace(".json", f"_{task}.json")

        out_file = v3_eval_safety.adjust_output_file_for_vllm(out_file, getattr(args, "use_vllm", False))
        assert_inside_v5(out_file)

        if not args.force and v3_eval_safety.is_complete(out_file, args.limit):
            print(f"[SKIP] Completed output exists for task {task}: {out_file}", flush=True)
            continue

        prompts, dataset_path = v3_eval_safety.load_eval_dataset(args, task)
        results = init_or_resume_results_preserve_all(args, task, out_file, prompts, dataset_path)
        task_configs.append({
            "task": task,
            "out_file": out_file,
            "prompts": prompts,
            "dataset_path": dataset_path,
            "results": results,
        })

    if not task_configs:
        print("All specified tasks are already complete.", flush=True)
        return 0

    # --- 生成フェーズ: 1 件ずつ推論して即座に原子保存 ---
    needs_generation = any(r.get("response") is None for tc in task_configs for r in tc["results"])
    if needs_generation:
        if getattr(args, "use_vllm", False):
            print(f"[eval_safety_streaming] 1件ずつ逐次生成 (vLLM): {args.model_path}", flush=True)
            is_peft = os.path.exists(os.path.join(args.model_path, "adapter_config.json"))
            if is_peft:
                raise ValueError("vLLM does not support directly loading PEFT adapters without --enable-lora.")

            from vllm import LLM, SamplingParams

            llm = LLM(model=args.model_path, trust_remote_code=True, tensor_parallel_size=1)
            sampling_params = SamplingParams(temperature=0.0, max_tokens=128)

            for tc in task_configs:
                missing = [i for i, r in enumerate(tc["results"]) if r.get("response") is None]
                if not missing:
                    continue
                done_so_far = len(tc["results"]) - len(missing)
                print(
                    f"[eval_safety_streaming] {tc['task']}: 未生成 {len(missing)} 件を 1 件ずつ保存しながら推論 "
                    f"(既存 {done_so_far} 件)",
                    flush=True,
                )
                for idx in tqdm(missing, desc=f"Generating 1-by-1 ({tc['task']})"):
                    prompt_text = f"<s>[INST] {tc['results'][idx]['prompt']} [/INST]"
                    try:
                        vllm_out = llm.generate([prompt_text], sampling_params, use_tqdm=False)
                    except TypeError:
                        vllm_out = llm.generate([prompt_text], sampling_params)
                    resp = vllm_out[0].outputs[0].text.strip()
                    tc["results"][idx]["response"] = resp
                    v3_eval_safety.save_checkpoint(
                        args, tc["task"], tc["out_file"], tc["dataset_path"], tc["results"], completed=False
                    )

            print("Unloading vLLM and clearing GPU cache...", flush=True)
            del llm
            v3_eval_safety.clear_cuda()
        else:
            print(f"[eval_safety_streaming] 1件ずつ逐次生成 (HF): {args.model_path}", flush=True)
            model, tokenizer = v3_eval_safety.load_eval_model(args.model_path, config)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            model_device = v3_eval_safety.get_model_device(model)
            old_padding_side = tokenizer.padding_side
            tokenizer.padding_side = "left"

            for tc in task_configs:
                missing = [i for i, r in enumerate(tc["results"]) if r.get("response") is None]
                if not missing:
                    continue
                for idx in tqdm(missing, desc=f"Generating 1-by-1 ({tc['task']})"):
                    prompt_text = f"<s>[INST] {tc['results'][idx]['prompt']} [/INST]"
                    inputs = tokenizer(
                        [prompt_text], return_tensors="pt", padding=True, truncation=True, max_length=2048
                    )
                    inputs = {k: v.to(model_device) for k, v in inputs.items()}
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=128,
                            do_sample=False,
                            pad_token_id=tokenizer.pad_token_id,
                            eos_token_id=tokenizer.eos_token_id,
                        )
                    input_length = inputs["input_ids"].shape[1]
                    resp = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True).strip()
                    tc["results"][idx]["response"] = resp
                    v3_eval_safety.save_checkpoint(
                        args, tc["task"], tc["out_file"], tc["dataset_path"], tc["results"], completed=False
                    )

            tokenizer.padding_side = old_padding_side
            del model
            v3_eval_safety.clear_cuda()

    # --- 分類フェーズ: v3_eval_safety.classify_missing も 1 件ごとに save_checkpoint する ---
    for tc in task_configs:
        try:
            tc["results"] = v3_eval_safety.classify_missing(
                args, tc["task"], tc["out_file"], tc["dataset_path"], tc["results"]
            )
            if any(r.get("asr") is None for r in tc["results"]):
                raise RuntimeError("Some samples are still unclassified.")

            responses = [r["response"] for r in tc["results"]]
            steering_hook.verify_evaluation_outputs(responses)

            v3_eval_safety.save_checkpoint(
                args, tc["task"], tc["out_file"], tc["dataset_path"], tc["results"], completed=True
            )
            final = v3_eval_safety.load_json(tc["out_file"])
            print(
                f"Safety Evaluation completed for task '{tc['task']}'. "
                f"ASR={final.get('asr')}, gibberish={final.get('gibberish_n')}/{final.get('n')}",
                flush=True,
            )
        except Exception as e:
            print(f"Safety evaluation failed for task '{tc['task']}': {e}", flush=True)
            traceback.print_exc()
            raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
