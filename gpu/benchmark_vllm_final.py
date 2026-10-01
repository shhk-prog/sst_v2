#!/usr/bin/env python3

import argparse
import csv
import os
import statistics
import subprocess
import threading
import time
from pathlib import Path


parser = argparse.ArgumentParser()

parser.add_argument("--model", required=True)
parser.add_argument("--cpu-cores", type=int, default=1)
parser.add_argument("--batch-size", type=int, required=True)
parser.add_argument("--input-tokens", type=int, required=True)
parser.add_argument("--output-tokens", type=int, default=256)
parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
parser.add_argument("--repeat", type=int, default=5)
parser.add_argument("--warmup", type=int, default=1)
parser.add_argument("--dtype", choices=["float16", "bfloat16"], default="bfloat16")
parser.add_argument("--output", required=True)

args = parser.parse_args()


os.environ["OMP_NUM_THREADS"] = str(args.cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(args.cpu_cores)
os.environ["OPENBLAS_NUM_THREADS"] = str(args.cpu_cores)
os.environ["NUMEXPR_NUM_THREADS"] = str(args.cpu_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "true"


class GPUMonitor:

    def __init__(self, interval=0.2):
        self.interval = interval
        self.util = []
        self.memory = []
        self.power = []
        self.running = False
        self.thread = None

    def query(self):
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,power.draw",
            "--format=csv,noheader,nounits",
        ]

        try:
            result = subprocess.check_output(
                cmd,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            lines = result.strip().splitlines()

            if not lines:
                return

            values = [x.strip() for x in lines[0].split(",")]

            if len(values) < 3:
                return

            util, memory, power = values[:3]

            self.util.append(float(util))
            self.memory.append(float(memory))

            try:
                self.power.append(float(power))
            except ValueError:
                pass

        except Exception:
            pass

    def loop(self):
        while self.running:
            self.query()
            time.sleep(self.interval)

    def start(self):
        self.util = []
        self.memory = []
        self.power = []
        self.running = True

        self.thread = threading.Thread(
            target=self.loop,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.running = False

        if self.thread is not None:
            self.thread.join()

    def summary(self):
        return {
            "gpu_util_avg": statistics.mean(self.util) if self.util else 0.0,
            "gpu_util_max": max(self.util) if self.util else 0.0,
            "gpu_memory_avg_mb": statistics.mean(self.memory) if self.memory else 0.0,
            "gpu_memory_max_mb": max(self.memory) if self.memory else 0.0,
            "gpu_power_avg_w": statistics.mean(self.power) if self.power else 0.0,
        }


def create_prompt(tokenizer, target_tokens, request_id):

    base = (
        "Large language model inference performance depends on batching, "
        "GPU scheduling, KV cache usage, memory bandwidth and sequence length. "
        "Efficient execution requires maximizing useful GPU throughput while "
        "minimizing unnecessary CPU and scheduling overhead. "
    )

    prefix = f"Request {request_id}. "

    prefix_ids = tokenizer.encode(
        prefix,
        add_special_tokens=False,
    )

    body_ids = tokenizer.encode(
        base * max(100, target_tokens // 10),
        add_special_tokens=False,
    )

    remaining = max(
        1,
        target_tokens - len(prefix_ids),
    )

    final_ids = (
        prefix_ids
        + body_ids[:remaining]
    )[:target_tokens]

    return tokenizer.decode(
        final_ids,
        skip_special_tokens=True,
    )


def create_prompts(tokenizer, batch_size, input_tokens):
    return [
        create_prompt(
            tokenizer,
            input_tokens,
            i,
        )
        for i in range(batch_size)
    ]


CSV_FIELDS = [
    "timestamp",
    "model",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
    "gpu_memory_utilization",
    "repeat",
    "walltime_sec",
    "input_tokens",
    "output_tokens",
    "requests_per_sec",
    "output_tokens_per_sec",
    "fairshare_cost",
    "fairshare_cost_per_1k_output_tokens",
    "gpu_util_avg",
    "gpu_util_max",
    "gpu_memory_avg_mb",
    "gpu_memory_max_mb",
    "gpu_power_avg_w",
]


def append_csv(row):

    path = Path(args.output)
    exists = path.exists()

    with path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_FIELDS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)


def main():

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    print("=" * 80)
    print("Final vLLM scaling benchmark")
    print("=" * 80)

    print(f"model      : {args.model}")
    print(f"CPU        : {args.cpu_cores}")
    print(f"batch      : {args.batch_size}")
    print(f"input      : {args.input_tokens}")
    print(f"output     : {args.output_tokens}")
    print(f"gpu memory : {args.gpu_memory_utilization}")
    print()

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        use_fast=True,
        trust_remote_code=True,
    )

    dtype = (
        "float16"
        if args.dtype == "float16"
        else "bfloat16"
    )

    print("Loading vLLM...")

    llm = LLM(
        model=args.model,
        dtype=dtype,
        tensor_parallel_size=1,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_num_seqs=args.batch_size,
        trust_remote_code=True,
        generation_config="vllm",
    )

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=args.output_tokens,
        min_tokens=args.output_tokens,
    )

    prompts = create_prompts(
        tokenizer,
        args.batch_size,
        args.input_tokens,
    )

    encoded = [
        tokenizer.encode(
            p,
            add_special_tokens=False,
        )
        for p in prompts
    ]

    input_tokens = sum(
        len(x)
        for x in encoded
    )

    lengths = [len(x) for x in encoded]

    print(
        f"actual input tokens/request: "
        f"min={min(lengths)}, "
        f"max={max(lengths)}, "
        f"mean={statistics.mean(lengths):.1f}"
    )

    print("Warmup...")

    for _ in range(args.warmup):
        llm.generate(
            prompts,
            sampling_params,
            use_tqdm=False,
        )

    print("Warmup done.")
    print()

    rows = []

    for repeat_idx in range(args.repeat):

        monitor = GPUMonitor()

        monitor.start()

        start = time.perf_counter()

        outputs = llm.generate(
            prompts,
            sampling_params,
            use_tqdm=False,
        )

        elapsed = time.perf_counter() - start

        monitor.stop()

        gpu = monitor.summary()

        output_tokens = sum(
            len(result.outputs[0].token_ids)
            for result in outputs
        )

        requests_per_sec = (
            args.batch_size / elapsed
        )

        output_tokens_per_sec = (
            output_tokens / elapsed
        )

        fairshare_cost = (
            30 + args.cpu_cores
        ) * elapsed

        fairshare_per_1k = (
            fairshare_cost
            / output_tokens
            * 1000
        )

        row = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": args.model,
            "cpu_cores": args.cpu_cores,
            "batch_size": args.batch_size,
            "target_input_tokens": args.input_tokens,
            "target_output_tokens": args.output_tokens,
            "gpu_memory_utilization": args.gpu_memory_utilization,
            "repeat": repeat_idx,
            "walltime_sec": elapsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "requests_per_sec": requests_per_sec,
            "output_tokens_per_sec": output_tokens_per_sec,
            "fairshare_cost": fairshare_cost,
            "fairshare_cost_per_1k_output_tokens": fairshare_per_1k,
            **gpu,
        }

        append_csv(row)
        rows.append(row)

        print(
            f"[{repeat_idx + 1}/{args.repeat}] "
            f"time={elapsed:.3f}s "
            f"req/s={requests_per_sec:.2f} "
            f"tok/s={output_tokens_per_sec:.2f} "
            f"GPU={gpu['gpu_util_avg']:.1f}% "
            f"VRAM={gpu['gpu_memory_max_mb']:.0f}MB "
            f"FS/1k={fairshare_per_1k:.4f}"
        )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        "median tok/s = "
        f"{statistics.median([x['output_tokens_per_sec'] for x in rows]):.2f}"
    )

    print(
        "median req/s = "
        f"{statistics.median([x['requests_per_sec'] for x in rows]):.2f}"
    )

    print(
        "median GPU   = "
        f"{statistics.median([x['gpu_util_avg'] for x in rows]):.2f}%"
    )

    print(
        "median FS/1k = "
        f"{statistics.median([x['fairshare_cost_per_1k_output_tokens'] for x in rows]):.4f}"
    )


if __name__ == "__main__":
    main()