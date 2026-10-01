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
    default="results/result_*.csv",
)

parser.add_argument(
    "--output",
    default="benchmark_summary.csv",
)

args = parser.parse_args()


# ================================================================
# Load
# ================================================================

files = glob.glob(args.input)

if not files:
    raise RuntimeError(
        f"No files found: {args.input}"
    )


frames = []

for filename in files:
    try:
        frames.append(
            pd.read_csv(filename)
        )
    except Exception as e:
        print(
            f"WARNING: failed to read "
            f"{filename}: {e}"
        )


if not frames:
    raise RuntimeError(
        "No valid CSV files found."
    )


df = pd.concat(
    frames,
    ignore_index=True,
)


# ================================================================
# Aggregate repeats
# ================================================================

group_columns = [
    "engine",
    "model",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
]


summary = (
    df
    .groupby(
        group_columns,
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
    range(1, len(summary) + 1),
)


summary.to_csv(
    args.output,
    index=False,
)


# ================================================================
# Display
# ================================================================

display_columns = [
    "rank",
    "engine",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "output_tokens_per_sec",
    "requests_per_sec",
    "gpu_util_avg",
    "gpu_memory_max_mb",
    "fairshare_cost_per_1k",
]


print()
print("=" * 120)
print("TOP 20 - FairShare efficiency")
print("=" * 120)

print(
    summary[
        display_columns
    ]
    .head(20)
    .to_string(
        index=False,
    )
)


# ================================================================
# Best by input length
# ================================================================

print()
print("=" * 120)
print("BEST CONFIGURATION FOR EACH INPUT LENGTH")
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
            "engine",
            "cpu_cores",
            "batch_size",
            "output_tokens_per_sec",
            "gpu_util_avg",
            "fairshare_cost_per_1k",
        ]
    ].to_string(
        index=False,
    )
)


# ================================================================
# Best by engine
# ================================================================

print()
print("=" * 120)
print("BEST CONFIGURATION FOR EACH ENGINE")
print("=" * 120)


best_engine = (
    summary
    .sort_values(
        "fairshare_cost_per_1k"
    )
    .groupby(
        "engine",
        as_index=False,
    )
    .first()
)


print(
    best_engine[
        [
            "engine",
            "cpu_cores",
            "batch_size",
            "target_input_tokens",
            "output_tokens_per_sec",
            "gpu_util_avg",
            "fairshare_cost_per_1k",
        ]
    ].to_string(
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
Engine:
    {best['engine']}

CPU cores:
    {int(best['cpu_cores'])}

Batch / simultaneous requests:
    {int(best['batch_size'])}

Input length:
    {int(best['target_input_tokens'])} tokens

Output throughput:
    {best['output_tokens_per_sec']:.2f} tokens/sec

Request throughput:
    {best['requests_per_sec']:.3f} requests/sec

GPU utilization:
    {best['gpu_util_avg']:.2f} %

Maximum VRAM:
    {best['gpu_memory_max_mb']:.0f} MB

FairShare cost / 1000 generated tokens:
    {best['fairshare_cost_per_1k']:.4f}
"""
)

print(
    f"Full summary: {args.output}"
)