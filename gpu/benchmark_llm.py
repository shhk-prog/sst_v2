#!/usr/bin/env python3

import argparse
import csv
import os
import statistics
import subprocess
import threading
import time
from pathlib import Path


# ================================================================
# Arguments
# ================================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--engine",
    choices=["transformers", "vllm"],
    required=True,
)

parser.add_argument(
    "--model",
    required=True,
)

parser.add_argument(
    "--cpu-cores",
    type=int,
    required=True,
)

parser.add_argument(
    "--batch-size",
    type=int,
    required=True,
)

parser.add_argument(
    "--input-tokens",
    type=int,
    default=512,
)

parser.add_argument(
    "--output-tokens",
    type=int,
    default=256,
)

parser.add_argument(
    "--repeat",
    type=int,
    default=3,
)

parser.add_argument(
    "--warmup",
    type=int,
    default=1,
)

parser.add_argument(
    "--dtype",
    choices=["float16", "bfloat16"],
    default="bfloat16",
)

parser.add_argument(
    "--gpu-memory-utilization",
    type=float,
    default=0.90,
)

parser.add_argument(
    "--output",
    default="benchmark_results.csv",
)

args = parser.parse_args()


# ================================================================
# CPU settings
# ================================================================

os.environ["OMP_NUM_THREADS"] = str(args.cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(args.cpu_cores)
os.environ["OPENBLAS_NUM_THREADS"] = str(args.cpu_cores)
os.environ["NUMEXPR_NUM_THREADS"] = str(args.cpu_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "true"


import torch

torch.set_num_threads(args.cpu_cores)

try:
    torch.set_num_interop_threads(
        max(1, min(args.cpu_cores, 4))
    )
except RuntimeError:
    pass


# ================================================================
# GPU monitor
# ================================================================

class GPUMonitor:
    def __init__(self, interval=0.2):
        self.interval = interval

        self.utilization = []
        self.memory_used = []
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

            # SLURMでGPU 1枚だけ割り当てられている前提。
            line = lines[0]

            values = [
                x.strip()
                for x in line.split(",")
            ]

            if len(values) < 3:
                return

            util, memory, power = values[:3]

            self.utilization.append(float(util))
            self.memory_used.append(float(memory))

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
        self.utilization = []
        self.memory_used = []
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
            "gpu_util_avg": (
                statistics.mean(self.utilization)
                if self.utilization
                else 0.0
            ),
            "gpu_util_max": (
                max(self.utilization)
                if self.utilization
                else 0.0
            ),
            "gpu_memory_max_mb": (
                max(self.memory_used)
                if self.memory_used
                else 0.0
            ),
            "gpu_power_avg_w": (
                statistics.mean(self.power)
                if self.power
                else 0.0
            ),
        }


# ================================================================
# Prompt generation
# ================================================================

def make_prompt(tokenizer, target_tokens, request_id):
    base = (
        "Large language models process sequences of tokens and "
        "perform tasks such as reasoning, summarization, translation, "
        "classification, and generation. "
        "Efficient inference requires careful use of CPU and GPU resources. "
    )

    text = base * max(
        20,
        target_tokens // 10,
    )

    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False,
    )

    token_ids = token_ids[:target_tokens]

    body = tokenizer.decode(
        token_ids,
        skip_special_tokens=True,
    )

    return (
        f"Request {request_id}. "
        "Read the following text and explain its important points.\n\n"
        + body
    )


def make_prompts(
    tokenizer,
    batch_size,
    input_tokens,
):
    return [
        make_prompt(
            tokenizer,
            input_tokens,
            i,
        )
        for i in range(batch_size)
    ]


# ================================================================
# Transformers
# ================================================================

class TransformersBenchmark:

    def __init__(self):
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
        )

        print("Loading tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            use_fast=True,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = (
                self.tokenizer.eos_token
            )

        self.tokenizer.padding_side = "left"

        if args.dtype == "float16":
            dtype = torch.float16
        else:
            dtype = torch.bfloat16

        print("Loading model...")

        self.model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=dtype,
            device_map="cuda",
            trust_remote_code=True,
        )

        self.model.eval()

        print("Model loaded.")

    def run(self, prompts):

        batch = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=False,
        )

        input_tokens = int(
            batch["attention_mask"].sum().item()
        )

        batch = {
            key: value.cuda()
            for key, value in batch.items()
        }

        torch.cuda.synchronize()

        start = time.perf_counter()

        with torch.inference_mode():
            outputs = self.model.generate(
                **batch,
                max_new_tokens=args.output_tokens,
                min_new_tokens=args.output_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        torch.cuda.synchronize()

        elapsed = (
            time.perf_counter()
            - start
        )

        input_length = batch[
            "input_ids"
        ].shape[1]

        output_tokens = int(
            outputs.shape[0]
            * (
                outputs.shape[1]
                - input_length
            )
        )

        return {
            "elapsed": elapsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }


# ================================================================
# vLLM
# ================================================================

class VLLMBenchmark:

    def __init__(self):

        from transformers import AutoTokenizer
        from vllm import LLM, SamplingParams

        print("Loading tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
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

        self.llm = LLM(
            model=args.model,
            dtype=dtype,
            tensor_parallel_size=1,
            gpu_memory_utilization=(
                args.gpu_memory_utilization
            ),
            trust_remote_code=True,
        )

        self.sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=args.output_tokens,
            min_tokens=args.output_tokens,
        )

        print("vLLM loaded.")

    def run(self, prompts):

        input_tokens = sum(
            len(
                self.tokenizer.encode(
                    p,
                    add_special_tokens=False,
                )
            )
            for p in prompts
        )

        start = time.perf_counter()

        outputs = self.llm.generate(
            prompts,
            self.sampling_params,
            use_tqdm=False,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        output_tokens = sum(
            len(result.outputs[0].token_ids)
            for result in outputs
        )

        return {
            "elapsed": elapsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }


# ================================================================
# CSV
# ================================================================

CSV_FIELDS = [
    "timestamp",
    "engine",
    "model",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
    "repeat",
    "walltime_sec",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "requests_per_sec",
    "output_tokens_per_sec",
    "total_tokens_per_sec",
    "fairshare_cost",
    "fairshare_cost_per_1k_output_tokens",
    "gpu_util_avg",
    "gpu_util_max",
    "gpu_memory_max_mb",
    "gpu_power_avg_w",
]


def write_csv(row):
    path = Path(args.output)

    exists = path.exists()

    with path.open(
        "a",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=CSV_FIELDS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)


# ================================================================
# Main
# ================================================================

def main():

    print("=" * 70)
    print("LLM INFERENCE BENCHMARK")
    print("=" * 70)

    print(f"model         : {args.model}")
    print(f"engine        : {args.engine}")
    print(f"CPU cores     : {args.cpu_cores}")
    print(f"batch size    : {args.batch_size}")
    print(f"input tokens  : {args.input_tokens}")
    print(f"output tokens : {args.output_tokens}")
    print()


    # ------------------------------------------------------------
    # Engine
    # ------------------------------------------------------------

    if args.engine == "transformers":
        benchmark = TransformersBenchmark()

    elif args.engine == "vllm":
        benchmark = VLLMBenchmark()

    else:
        raise RuntimeError(
            f"Unknown engine: {args.engine}"
        )


    # ------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------

    prompts = make_prompts(
        benchmark.tokenizer,
        args.batch_size,
        args.input_tokens,
    )


    # ------------------------------------------------------------
    # Warmup
    # ------------------------------------------------------------

    print()
    print("Warmup...")

    for _ in range(args.warmup):
        benchmark.run(prompts)

    print("Warmup complete.")
    print()


    # ------------------------------------------------------------
    # Benchmark
    # ------------------------------------------------------------

    results = []

    for repeat_idx in range(args.repeat):

        monitor = GPUMonitor()

        monitor.start()

        result = benchmark.run(prompts)

        monitor.stop()

        gpu = monitor.summary()


        elapsed = result["elapsed"]

        input_tokens = result[
            "input_tokens"
        ]

        output_tokens = result[
            "output_tokens"
        ]

        total_tokens = (
            input_tokens
            + output_tokens
        )


        requests_per_sec = (
            args.batch_size
            / elapsed
        )

        output_tokens_per_sec = (
            output_tokens
            / elapsed
        )

        total_tokens_per_sec = (
            total_tokens
            / elapsed
        )


        # ========================================================
        # FairShare
        #
        # GPU = 30
        # CPU core = 1
        #
        # Cost = (30 + CPU) * time
        # ========================================================

        fairshare_cost = (
            30 + args.cpu_cores
        ) * elapsed


        fairshare_cost_per_1k = (
            fairshare_cost
            / output_tokens
            * 1000
        )


        row = {
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "engine": args.engine,
            "model": args.model,
            "cpu_cores": args.cpu_cores,
            "batch_size": args.batch_size,
            "target_input_tokens": args.input_tokens,
            "target_output_tokens": args.output_tokens,
            "repeat": repeat_idx,
            "walltime_sec": elapsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "requests_per_sec": requests_per_sec,
            "output_tokens_per_sec": (
                output_tokens_per_sec
            ),
            "total_tokens_per_sec": (
                total_tokens_per_sec
            ),
            "fairshare_cost": (
                fairshare_cost
            ),
            "fairshare_cost_per_1k_output_tokens": (
                fairshare_cost_per_1k
            ),
            **gpu,
        }


        write_csv(row)

        results.append(row)


        print(
            f"[{repeat_idx + 1}/{args.repeat}] "
            f"time={elapsed:.3f}s "
            f"requests/s={requests_per_sec:.3f} "
            f"output_tok/s={output_tokens_per_sec:.2f} "
            f"GPU={gpu['gpu_util_avg']:.1f}% "
            f"VRAM={gpu['gpu_memory_max_mb']:.0f}MB "
            f"FS/1k={fairshare_cost_per_1k:.4f}"
        )


    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------

    times = [
        r["walltime_sec"]
        for r in results
    ]

    throughputs = [
        r["output_tokens_per_sec"]
        for r in results
    ]

    costs = [
        r[
            "fairshare_cost_per_1k_output_tokens"
        ]
        for r in results
    ]

    gpu_utils = [
        r["gpu_util_avg"]
        for r in results
    ]


    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        f"median walltime       : "
        f"{statistics.median(times):.3f} sec"
    )

    print(
        f"median output tok/s   : "
        f"{statistics.median(throughputs):.2f}"
    )

    print(
        f"median GPU util       : "
        f"{statistics.median(gpu_utils):.2f} %"
    )

    print(
        f"median FS / 1k tokens : "
        f"{statistics.median(costs):.4f}"
    )

    print(
        f"output                : "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()