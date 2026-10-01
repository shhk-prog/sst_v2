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
    "--model",
    required=True,
)

parser.add_argument(
    "--cpu-cores",
    type=int,
    default=1,
)

parser.add_argument(
    "--batch-size",
    type=int,
    required=True,
)

parser.add_argument(
    "--input-tokens",
    type=int,
    required=True,
)

parser.add_argument(
    "--output-tokens",
    type=int,
    default=256,
)

parser.add_argument(
    "--gpu-memory-utilization",
    type=float,
    required=True,
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
    "--output",
    required=True,
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


# ================================================================
# GPU monitor
# ================================================================

class GPUMonitor:

    def __init__(self, interval=0.2):
        self.interval = interval

        self.utilization = []
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
            output = subprocess.check_output(
                cmd,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            lines = output.strip().splitlines()

            if not lines:
                return

            # SLURM job is allocated a single GPU.
            line = lines[0]

            values = [
                x.strip()
                for x in line.split(",")
            ]

            if len(values) < 3:
                return

            util, memory, power = values[:3]

            self.utilization.append(
                float(util)
            )

            self.memory.append(
                float(memory)
            )

            try:
                self.power.append(
                    float(power)
                )
            except ValueError:
                pass

        except Exception:
            pass

    def loop(self):

        while self.running:

            self.query()

            time.sleep(
                self.interval
            )

    def start(self):

        self.utilization = []
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

            "gpu_util_avg": (
                statistics.mean(
                    self.utilization
                )
                if self.utilization
                else 0.0
            ),

            "gpu_util_max": (
                max(self.utilization)
                if self.utilization
                else 0.0
            ),

            "gpu_memory_avg_mb": (
                statistics.mean(
                    self.memory
                )
                if self.memory
                else 0.0
            ),

            "gpu_memory_max_mb": (
                max(self.memory)
                if self.memory
                else 0.0
            ),

            "gpu_power_avg_w": (
                statistics.mean(
                    self.power
                )
                if self.power
                else 0.0
            ),
        }


# ================================================================
# Prompt generation
# ================================================================

def create_prompt(
    tokenizer,
    target_tokens,
    request_id,
):

    base_text = (
        "Large language models perform inference by processing "
        "input tokens and generating output tokens. "
        "Efficient inference depends on GPU utilization, batching, "
        "memory bandwidth, KV cache usage, and scheduling. "
    )

    text = base_text * max(
        50,
        target_tokens // 10,
    )

    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False,
    )

    # Reserve a few tokens for request-specific prefix.
    prefix = (
        f"Request {request_id}. "
    )

    prefix_ids = tokenizer.encode(
        prefix,
        add_special_tokens=False,
    )

    remaining = max(
        1,
        target_tokens - len(prefix_ids),
    )

    body_ids = token_ids[:remaining]

    final_ids = (
        prefix_ids
        + body_ids
    )

    final_ids = final_ids[
        :target_tokens
    ]

    return tokenizer.decode(
        final_ids,
        skip_special_tokens=True,
    )


def create_prompts(
    tokenizer,
    batch_size,
    input_tokens,
):

    return [
        create_prompt(
            tokenizer,
            input_tokens,
            i,
        )
        for i in range(batch_size)
    ]


# ================================================================
# CSV definition
# ================================================================

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
    "total_tokens",
    "requests_per_sec",
    "input_tokens_per_sec",
    "output_tokens_per_sec",
    "total_tokens_per_sec",
    "fairshare_cost",
    "fairshare_cost_per_request",
    "fairshare_cost_per_1k_output_tokens",
    "gpu_util_avg",
    "gpu_util_max",
    "gpu_memory_avg_mb",
    "gpu_memory_max_mb",
    "gpu_power_avg_w",
]


def append_csv(row):

    path = Path(
        args.output
    )

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

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams


    print("=" * 80)
    print("vLLM FairShare benchmark")
    print("=" * 80)

    print(
        f"model                  : {args.model}"
    )

    print(
        f"CPU cores              : {args.cpu_cores}"
    )

    print(
        f"batch size             : {args.batch_size}"
    )

    print(
        f"input tokens           : {args.input_tokens}"
    )

    print(
        f"output tokens          : {args.output_tokens}"
    )

    print(
        f"gpu memory utilization : "
        f"{args.gpu_memory_utilization}"
    )

    print(
        f"repeat                 : {args.repeat}"
    )

    print()


    # ============================================================
    # Tokenizer
    # ============================================================

    print(
        "Loading tokenizer..."
    )

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        use_fast=True,
        trust_remote_code=True,
    )


    # ============================================================
    # vLLM
    # ============================================================

    print(
        "Loading vLLM engine..."
    )

    dtype = (
        "float16"
        if args.dtype == "float16"
        else "bfloat16"
    )


    llm = LLM(

        model=args.model,

        dtype=dtype,

        tensor_parallel_size=1,

        gpu_memory_utilization=(
            args.gpu_memory_utilization
        ),

        # Important:
        # Allow scheduler to process at least this many sequences.
        max_num_seqs=args.batch_size,

        trust_remote_code=True,

        generation_config="vllm",
    )


    sampling_params = SamplingParams(

        temperature=0.0,

        max_tokens=args.output_tokens,

        min_tokens=args.output_tokens,
    )


    print(
        "vLLM loaded."
    )


    # ============================================================
    # Prompts
    # ============================================================

    prompts = create_prompts(
        tokenizer,
        args.batch_size,
        args.input_tokens,
    )


    # ============================================================
    # Actual input token count
    # ============================================================

    encoded_prompts = [
        tokenizer.encode(
            p,
            add_special_tokens=False,
        )
        for p in prompts
    ]

    actual_input_tokens = sum(
        len(x)
        for x in encoded_prompts
    )

    lengths = [
        len(x)
        for x in encoded_prompts
    ]


    print()
    print(
        f"Actual prompt lengths: "
        f"min={min(lengths)}, "
        f"max={max(lengths)}, "
        f"mean={statistics.mean(lengths):.1f}"
    )

    print(
        f"Total input tokens: "
        f"{actual_input_tokens}"
    )


    # ============================================================
    # Warmup
    # ============================================================

    print()
    print(
        "Warmup..."
    )

    for i in range(
        args.warmup
    ):

        llm.generate(
            prompts,
            sampling_params,
            use_tqdm=False,
        )

    print(
        "Warmup complete."
    )


    # ============================================================
    # Benchmark
    # ============================================================

    results = []


    for repeat_idx in range(
        args.repeat
    ):

        monitor = GPUMonitor(
            interval=0.2
        )

        monitor.start()

        start = time.perf_counter()


        outputs = llm.generate(
            prompts,
            sampling_params,
            use_tqdm=False,
        )


        elapsed = (
            time.perf_counter()
            - start
        )


        monitor.stop()

        gpu_stats = (
            monitor.summary()
        )


        # ========================================================
        # Generated tokens
        # ========================================================

        output_tokens = sum(

            len(
                request_output
                .outputs[0]
                .token_ids
            )

            for request_output
            in outputs
        )


        input_tokens = (
            actual_input_tokens
        )


        total_tokens = (
            input_tokens
            + output_tokens
        )


        # ========================================================
        # Throughput
        # ========================================================

        requests_per_sec = (
            args.batch_size
            / elapsed
        )


        input_tokens_per_sec = (
            input_tokens
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
        # GPU 1 = 30
        # CPU 1 = 1
        #
        # Current benchmark:
        # CPU fixed to 1
        #
        # FS = 31 * elapsed
        # ========================================================

        fairshare_cost = (
            30 + args.cpu_cores
        ) * elapsed


        fairshare_per_request = (
            fairshare_cost
            / args.batch_size
        )


        fairshare_per_1k = (
            fairshare_cost
            / output_tokens
            * 1000
        )


        # ========================================================
        # Result
        # ========================================================

        row = {

            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "model": args.model,

            "cpu_cores": (
                args.cpu_cores
            ),

            "batch_size": (
                args.batch_size
            ),

            "target_input_tokens": (
                args.input_tokens
            ),

            "target_output_tokens": (
                args.output_tokens
            ),

            "gpu_memory_utilization": (
                args.gpu_memory_utilization
            ),

            "repeat": (
                repeat_idx
            ),

            "walltime_sec": (
                elapsed
            ),

            "input_tokens": (
                input_tokens
            ),

            "output_tokens": (
                output_tokens
            ),

            "total_tokens": (
                total_tokens
            ),

            "requests_per_sec": (
                requests_per_sec
            ),

            "input_tokens_per_sec": (
                input_tokens_per_sec
            ),

            "output_tokens_per_sec": (
                output_tokens_per_sec
            ),

            "total_tokens_per_sec": (
                total_tokens_per_sec
            ),

            "fairshare_cost": (
                fairshare_cost
            ),

            "fairshare_cost_per_request": (
                fairshare_per_request
            ),

            "fairshare_cost_per_1k_output_tokens": (
                fairshare_per_1k
            ),

            **gpu_stats,
        }


        append_csv(
            row
        )

        results.append(
            row
        )


        print(
            f"[{repeat_idx + 1}/{args.repeat}] "
            f"time={elapsed:.3f}s "
            f"req/s={requests_per_sec:.2f} "
            f"out_tok/s={output_tokens_per_sec:.2f} "
            f"GPU={gpu_stats['gpu_util_avg']:.1f}% "
            f"VRAM={gpu_stats['gpu_memory_max_mb']:.0f}MB "
            f"FS/1k={fairshare_per_1k:.4f}"
        )


    # ============================================================
    # Summary
    # ============================================================

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)


    median_walltime = statistics.median(
        [
            x["walltime_sec"]
            for x in results
        ]
    )


    median_throughput = statistics.median(
        [
            x["output_tokens_per_sec"]
            for x in results
        ]
    )


    median_requests = statistics.median(
        [
            x["requests_per_sec"]
            for x in results
        ]
    )


    median_gpu = statistics.median(
        [
            x["gpu_util_avg"]
            for x in results
        ]
    )


    median_fs = statistics.median(
        [
            x[
                "fairshare_cost_per_1k_output_tokens"
            ]
            for x in results
        ]
    )


    print(
        f"walltime median       : "
        f"{median_walltime:.3f} sec"
    )

    print(
        f"output throughput     : "
        f"{median_throughput:.2f} tok/s"
    )

    print(
        f"request throughput    : "
        f"{median_requests:.2f} req/s"
    )

    print(
        f"GPU utilization       : "
        f"{median_gpu:.2f}%"
    )

    print(
        f"FairShare / 1k output : "
        f"{median_fs:.4f}"
    )

    print(
        f"result file           : "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()