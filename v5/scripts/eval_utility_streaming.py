#!/usr/bin/env python3
"""SoK 実証 2 用: 有用性評価スクリプト（lm-eval の推論を 1 件ずつ逐次 JSONL 保存・途中再開対応）。

v3/scripts/eval/eval_utility.py のプロンプト・チャットテンプレート・採点・fix_gsm8k_jsons_fast.py と
完全に同一の結果を保ちつつ、lm_obj の `generate_until` / `loglikelihood` をラップし、
**1 件推論するごとに** `<output_file>.stream.jsonl` へ 1 行追記＋`flush()`＋`os.fsync()` する。

途中でプロセスが落ちた場合:
  - 再実行すると `<output_file>.stream.jsonl` から完了済みの件数を即座に復元し、
    推論済みのプロンプトは GPU を一切使わずスキップして、次の 1 件目から再開する。
  - 破損した末尾行があっても安全に無視する。
  - 最終 JSON の書き込みも原子操作（.tmp -> os.replace）で行い、`v5/` 外へは一切書き込まない。
"""

from __future__ import annotations

import gc
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

import torch
import yaml
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"

sys.path.insert(0, str(V3_ROOT / "scripts" / "eval"))


def _get_v3_eval_utility():
    import eval_utility as v3_eval_utility  # 遅延 import（テスト時の不要な pip 実行を防止）
    return v3_eval_utility


def assert_inside_v5(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def _request_key(method: str, idx: int, req: Any) -> str:
    """lm_eval Instance から決定論的な一意キーを生成する。"""
    req_args = getattr(req, "args", None)
    task_name = getattr(req, "task_name", None)
    doc_id = getattr(req, "doc_id", None)
    payload = {
        "method": method,
        "idx": idx,
        "task_name": task_name,
        "doc_id": doc_id,
        "args": req_args,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_jsonl_cache(cache_path: Path) -> dict[str, Any]:
    """逐次保存 JSONL からキャッシュを復元する（途中切断による破損末尾行は安全にスキップ）。"""
    cache: dict[str, Any] = {}
    if not cache_path.is_file():
        return cache
    with open(cache_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if isinstance(rec, dict) and "key" in rec and "value" in rec:
                    cache[rec["key"]] = rec["value"]
            except json.JSONDecodeError:
                # 強制終了で書き掛けになった末尾行はスキップ
                continue
    return cache


def append_jsonl_item(cache_path: Path, key: str, value: Any) -> None:
    """1 件の結果を JSONL に追記し、即座に flush + fsync する。"""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n"
    with open(cache_path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def attach_streaming_checkpoint(lm_obj: Any, cache_path: Path) -> dict[str, Any]:
    """lm_obj の推論メソッドを 1 件ずつ逐次保存・再開できるラッパーに差し替える。"""
    cache = load_jsonl_cache(cache_path)
    stats = {"cached_hits": 0, "computed": 0, "cache_path": str(cache_path)}

    for method_name in ("generate_until", "loglikelihood", "loglikelihood_rolling"):
        orig_fn = getattr(lm_obj, method_name, None)
        if orig_fn is None or not callable(orig_fn):
            continue

        def _make_wrapper(m_name: str, fn):
            def _wrapped(requests, disable_tqdm: bool = False):
                req_list = list(requests)
                outputs: list[Any] = [None] * len(req_list)
                pending_indices: list[tuple[int, str]] = []

                for i, req in enumerate(req_list):
                    k = _request_key(m_name, i, req)
                    if k in cache:
                        val = cache[k]
                        # loglikelihood の戻り値 (float, bool) タプル復元
                        if m_name == "loglikelihood" and isinstance(val, list) and len(val) == 2:
                            val = (val[0], val[1])
                        outputs[i] = val
                        stats["cached_hits"] += 1
                    else:
                        pending_indices.append((i, k))

                if pending_indices:
                    print(
                        f"[eval_utility_streaming] {m_name}: 未推論 {len(pending_indices)} / {len(req_list)} 件を "
                        f"1 件ずつ保存しながら実行 (キャッシュ再利用 {len(req_list) - len(pending_indices)} 件)",
                        flush=True,
                    )
                    for i, k in tqdm(
                        pending_indices,
                        desc=f"{m_name} 1-by-1",
                        disable=disable_tqdm,
                    ):
                        try:
                            res_list = fn([req_list[i]], disable_tqdm=True)
                        except TypeError:
                            res_list = fn([req_list[i]])
                        val = res_list[0]
                        outputs[i] = val
                        cache[k] = val
                        serializable_val = list(val) if isinstance(val, tuple) else val
                        append_jsonl_item(cache_path, k, serializable_val)
                        stats["computed"] += 1
                else:
                    print(
                        f"[eval_utility_streaming] {m_name}: 全 {len(req_list)} 件を逐次キャッシュから復元しました",
                        flush=True,
                    )
                return outputs

            return _wrapped

        setattr(lm_obj, method_name, _make_wrapper(method_name, orig_fn))

    return stats


def run_lm_eval_streaming(args, config, tasks_list, cache_path: Path):
    import lm_eval
    v3_eval_utility = _get_v3_eval_utility()

    is_peft = os.path.exists(os.path.join(args.model_path, "adapter_config.json"))
    apply_chat_template = getattr(args, "apply_chat_template", True)

    if getattr(args, "use_vllm", False):
        print(f"[eval_utility_streaming] Loading vLLM: model={args.model_path}, tasks={tasks_list}", flush=True)
        if is_peft:
            raise ValueError("vLLM does not support PEFT adapters directly.")
        from lm_eval.models.vllm_causallms import VLLM

        lm_obj = VLLM(
            pretrained=args.model_path,
            tensor_parallel_size=1,
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_length=4096,
            dtype="float16",
        )
    else:
        from lm_eval.models.huggingface import HFLM

        if is_peft:
            base_model = config["models"]["base_model"]
            lm_obj = HFLM(pretrained=base_model, peft=args.model_path, dtype="float16", max_length=4096)
        else:
            lm_obj = HFLM(pretrained=args.model_path, dtype="float16", max_length=4096)

    # v3/scripts/eval/eval_utility.py L650-664 と完全同一のデフォルトチャットテンプレート
    if apply_chat_template and getattr(lm_obj, "tokenizer", None) is not None:
        if getattr(lm_obj.tokenizer, "chat_template", None) is None:
            print("[eval_utility_streaming] Setting default chat template.", flush=True)
            lm_obj.tokenizer.chat_template = (
                "{% for message in messages %}"
                "{% if message['role'] == 'user' %}"
                "{{ '### Instruction:\n' + message['content'] + '\n\n' }}"
                "{% elif message['role'] == 'assistant' %}"
                "{{ '### Response:\n' + message['content'] + '\n\n' }}"
                "{% endif %}"
                "{% endfor %}"
                "{% if add_generation_prompt %}"
                "{{ '### Response:\n' }}"
                "{% endif %}"
            )

    stream_stats = attach_streaming_checkpoint(lm_obj, cache_path)

    needs_code_exec = any("humaneval" in t or "mbpp" in t for t in tasks_list)
    eval_limit = None if args.limit == 0 else args.limit
    bs = args.batch_size
    if isinstance(bs, str) and bs.isdigit():
        bs = int(bs)

    eval_kwargs = {
        "model": lm_obj,
        "tasks": tasks_list,
        "num_fewshot": 0,
        "batch_size": bs,
        "limit": eval_limit,
        "confirm_run_unsafe_code": needs_code_exec,
    }
    if apply_chat_template:
        eval_kwargs["apply_chat_template"] = True

    try:
        results = lm_eval.simple_evaluate(**eval_kwargs)
    except TypeError as e:
        if "apply_chat_template" in str(e):
            eval_kwargs.pop("apply_chat_template", None)
            results = lm_eval.simple_evaluate(**eval_kwargs)
        else:
            raise

    if "model" in results:
        del results["model"]

    serializable_results = v3_eval_utility.make_json_serializable(results)
    serializable_results = v3_eval_utility.fix_humaneval_indentation(serializable_results)
    serializable_results = v3_eval_utility.fix_mbpp_responses(serializable_results)
    serializable_results = v3_eval_utility.fix_ifeval_responses(serializable_results)
    serializable_results = v3_eval_utility.fix_mmlu_pro_responses(serializable_results)

    serializable_results["status"] = "success"
    serializable_results["mockup"] = False
    serializable_results["completed"] = True
    serializable_results["model_path"] = args.model_path
    serializable_results["tasks"] = tasks_list
    serializable_results["limit"] = args.limit
    serializable_results["output_file"] = args.output_file
    sample_count = v3_eval_utility.infer_sample_count(serializable_results)
    serializable_results["expected_n"] = sample_count
    serializable_results["num_results"] = sample_count
    serializable_results["streaming_checkpoint_stats"] = stream_stats

    try:
        del lm_obj
    except Exception:
        pass
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return serializable_results


def main() -> int:
    v3_eval_utility = _get_v3_eval_utility()
    args = v3_eval_utility.parse_args()
    args.output_file = v3_eval_utility.adjust_output_file_for_vllm(
        args.output_file, getattr(args, "use_vllm", False)
    )
    out_path = assert_inside_v5(args.output_file)
    cache_path = assert_inside_v5(Path(str(out_path) + ".stream.jsonl"))

    num_threads = int(os.environ.get("OMP_NUM_THREADS", os.environ.get("SLURM_CPUS_PER_TASK", 16)))
    if torch.cuda.is_available():
        torch.set_num_threads(num_threads)

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    tasks_list = v3_eval_utility.get_tasks(args, config)

    if not args.force and v3_eval_utility.is_completed_output(str(out_path), args.limit):
        print(f"[SKIP] Completed output exists: {out_path}", flush=True)
        return 0

    if args.force and cache_path.is_file():
        cache_path.unlink()

    try:
        results = run_lm_eval_streaming(args, config, tasks_list, cache_path)
        v3_eval_utility.write_json_atomic(str(out_path), results)
        print(f"[eval_utility_streaming] Results saved to {out_path}", flush=True)
    except Exception as e:
        print(f"[eval_utility_streaming] Failed: {e}", flush=True)
        traceback.print_exc()
        raise

    # v3/scripts/eval/eval_utility.py L869-881 と同一の自動修復
    tasks_str = ",".join(tasks_list).lower()
    if "mbpp" in tasks_str:
        subprocess.run([sys.executable, "scripts/fix_mbpp_jsons_fast.py", "--file", str(out_path)], check=False)
    if "humaneval" in tasks_str:
        subprocess.run([sys.executable, "scripts/fix_humaneval_jsons_fast.py", "--file", str(out_path)], check=False)
    if "gsm8k" in tasks_str:
        subprocess.run([sys.executable, "scripts/fix_gsm8k_jsons_fast.py", "--file", str(out_path)], check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
