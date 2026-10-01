#!/usr/bin/env python3

import argparse
import glob

import pandas as pd


# ================================================================
# Arguments
# ================================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--input",
    default="results_vllm2/result_*.csv",
)

parser.add_argument(
    "--output",
    default="benchmark_vllm_summary.csv",
)

args = parser.parse_args()


# ================================================================
# Load
# ================================================================

files = sorted(
    glob.glob(
        args.input
    )
)

if not files:
    raise RuntimeError(
        f"No result files found: {args.input}"
    )


frames = []

for filename in files:

    try:

        df = pd.read_csv(
            filename
        )

        frames.append(
            df
        )

    except Exception as e:

        print(
            f"WARNING: failed to read "
            f"{filename}: {e}"
        )


if not frames:
    raise RuntimeError(
        "No valid results."
    )


raw = pd.concat(
    frames,
    ignore_index=True,
)


print(
    f"Loaded {len(files)} files"
)

print(
    f"Loaded {len(raw)} measurements"
)


# ================================================================
# Aggregate repetitions
# ================================================================

group_cols = [
    "model",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
    "gpu_memory_utilization",
]


summary = (

    raw

    .groupby(
        group_cols,
        as_index=False,
    )

    .agg(

        walltime_sec=(
            "walltime_sec",
            "median",
        ),

        requests_per_sec=(
            "requests_per_sec",
            "median",
        ),

        input_tokens_per_sec=(
            "input_tokens_per_sec",
            "median",
        ),

        output_tokens_per_sec=(
            "output_tokens_per_sec",
            "median",
        ),

        total_tokens_per_sec=(
            "total_tokens_per_sec",
            "median",
        ),

        fairshare_cost=(
            "fairshare_cost",
            "median",
        ),

        fairshare_cost_per_request=(
            "fairshare_cost_per_request",
            "median",
        ),

        fairshare_cost_per_1k=(
            "fairshare_cost_per_1k_output_tokens",
            "median",
        ),

        gpu_util_avg=(
            "gpu_util_avg",
            "median",
        ),

        gpu_util_max=(
            "gpu_util_max",
            "max",
        ),

        gpu_memory_avg_mb=(
            "gpu_memory_avg_mb",
            "median",
        ),

        gpu_memory_max_mb=(
            "gpu_memory_max_mb",
            "max",
        ),

        gpu_power_avg_w=(
            "gpu_power_avg_w",
            "median",
        ),
    )
)


# ================================================================
# Rank
# ================================================================

summary = summary.sort_values(
    "fairshare_cost_per_1k",
    ascending=True,
)

summary.insert(
    0,
    "rank",
    range(
        1,
        len(summary) + 1,
    ),
)


summary.to_csv(
    args.output,
    index=False,
)


# ================================================================
# Display columns
# ================================================================

cols = [
    "rank",
    "batch_size",
    "target_input_tokens",
    "gpu_memory_utilization",
    "output_tokens_per_sec",
    "requests_per_sec",
    "gpu_util_avg",
    "gpu_memory_max_mb",
    "fairshare_cost_per_1k",
]


# ================================================================
# TOP 20
# ================================================================

print()
print("=" * 120)
print("TOP 20 - FairShare efficiency")
print("=" * 120)

print(
    summary[
        cols
    ]
    .head(20)
    .to_string(
        index=False,
    )
)


# ================================================================
# Best configuration per input length
# ================================================================

print()
print("=" * 120)
print("BEST FOR EACH INPUT LENGTH")
print("=" * 120)


best_input = (

    summary

    .sort_values(
        "fairshare_cost_per_1k"
    )

    .groupby(
        "target_input_tokens",
        as_index=False,
    )

    .first()
)


print(
    best_input[
        [
            "target_input_tokens",
            "batch_size",
            "gpu_memory_utilization",
            "output_tokens_per_sec",
            "requests_per_sec",
            "gpu_util_avg",
            "gpu_memory_max_mb",
            "fairshare_cost_per_1k",
        ]
    ]
    .to_string(
        index=False,
    )
)


# ================================================================
# Best per batch size
# ================================================================

print()
print("=" * 120)
print("BEST FOR EACH BATCH SIZE")
print("=" * 120)


best_batch = (

    summary

    .sort_values(
        "fairshare_cost_per_1k"
    )

    .groupby(
        "batch_size",
        as_index=False,
    )

    .first()
)


print(
    best_batch[
        [
            "batch_size",
            "target_input_tokens",
            "gpu_memory_utilization",
            "output_tokens_per_sec",
            "requests_per_sec",
            "gpu_util_avg",
            "fairshare_cost_per_1k",
        ]
    ]
    .to_string(
        index=False,
    )
)


# ================================================================
# Best per gpu_memory_utilization
# ================================================================

print()
print("=" * 120)
print("BEST FOR EACH GPU MEMORY UTILIZATION")
print("=" * 120)


best_memory = (

    summary

    .sort_values(
        "fairshare_cost_per_1k"
    )

    .groupby(
        "gpu_memory_utilization",
        as_index=False,
    )

    .first()
)


print(
    best_memory[
        [
            "gpu_memory_utilization",
            "batch_size",
            "target_input_tokens",
            "output_tokens_per_sec",
            "gpu_util_avg",
            "gpu_memory_max_mb",
            "fairshare_cost_per_1k",
        ]
    ]
    .to_string(
        index=False,
    )
)


# ================================================================
# Batch scaling
#
# Compare only input=128 and best memory configuration
# ================================================================

print()
print("=" * 120)
print("BATCH SCALING - INPUT 128")
print("=" * 120)


subset128 = summary[
    summary[
        "target_input_tokens"
    ] == 128
]


best_batch_128 = (

    subset128

    .sort_values(
        "fairshare_cost_per_1k"
    )

    .groupby(
        "batch_size",
        as_index=False,
    )

    .first()

    .sort_values(
        "batch_size"
    )
)


print(
    best_batch_128[
        [
            "batch_size",
            "gpu_memory_utilization",
            "output_tokens_per_sec",
            "requests_per_sec",
            "gpu_util_avg",
            "fairshare_cost_per_1k",
        ]
    ]
    .to_string(
        index=False,
    )
)


# ================================================================
# Best overall
# ================================================================

best = summary.iloc[0]


print()
print("=" * 120)
print("BEST OVERALL")
print("=" * 120)


print(
    f"""
CPU cores:
    {int(best['cpu_cores'])}

Batch / simultaneous requests:
    {int(best['batch_size'])}

Input length:
    {int(best['target_input_tokens'])}

Output length:
    {int(best['target_output_tokens'])}

GPU memory utilization:
    {best['gpu_memory_utilization']:.2f}

Output throughput:
    {best['output_tokens_per_sec']:.2f} tokens/sec

Request throughput:
    {best['requests_per_sec']:.2f} requests/sec

GPU utilization:
    {best['gpu_util_avg']:.2f} %

Maximum VRAM:
    {best['gpu_memory_max_mb']:.0f} MB

FairShare cost / 1000 output tokens:
    {best['fairshare_cost_per_1k']:.4f}
"""
)


# ================================================================
# Determine whether larger batches should be tested
# ================================================================

largest_batch = summary[
    "batch_size"
].max()


largest = summary[
    summary["batch_size"]
    == largest_batch
]


best_largest = largest.sort_values(
    "fairshare_cost_per_1k"
).iloc[0]


second_largest_batch = sorted(
    summary[
        "batch_size"
    ].unique()
)[-2]


second = summary[
    summary["batch_size"]
    == second_largest_batch
]


best_second = second.sort_values(
    "fairshare_cost_per_1k"
).iloc[0]


improvement = (

    (
        best_second[
            "fairshare_cost_per_1k"
        ]
        -
        best_largest[
            "fairshare_cost_per_1k"
        ]
    )

    /

    best_second[
        "fairshare_cost_per_1k"
    ]

    * 100
)


print("=" * 120)
print("NEXT-STEP RECOMMENDATION")
print("=" * 120)


print(
    f"Batch {second_largest_batch} best FS/1k: "
    f"{best_second['fairshare_cost_per_1k']:.4f}"
)

print(
    f"Batch {largest_batch} best FS/1k: "
    f"{best_largest['fairshare_cost_per_1k']:.4f}"
)

print(
    f"Improvement at batch {largest_batch}: "
    f"{improvement:.2f}%"
)


if improvement > 3:

    print()
    print(
        f"Batch {largest_batch} is still improving materially."
    )

    print(
        "Recommended next search: "
        "batch = 128, 160, 192, 256"
    )

elif improvement > 0:

    print()
    print(
        "The efficiency curve is still improving, "
        "but appears close to saturation."
    )

    print(
        "A small additional search around "
        "batch 128-192 is reasonable."
    )

else:

    print()
    print(
        "Efficiency no longer improves at the largest batch."
    )

    print(
        "The optimum is likely inside the tested range."
    )


print()
print(
    f"Full summary written to: "
    f"{args.output}"
)