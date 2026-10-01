#!/usr/bin/env python3

import glob
import pandas as pd


files = sorted(
    glob.glob(
        "results_batch/result_*.csv"
    )
)

if not files:
    raise RuntimeError(
        "No result files found."
    )


df = pd.concat(
    [
        pd.read_csv(f)
        for f in files
    ],
    ignore_index=True,
)


summary = (
    df
    .groupby(
        [
            "batch_size",
            "target_input_tokens",
            "gpu_memory_utilization",
        ],
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
        gpu_util_avg=(
            "gpu_util_avg",
            "median",
        ),
        gpu_memory_max_mb=(
            "gpu_memory_max_mb",
            "max",
        ),
        fairshare_cost_per_1k=(
            "fairshare_cost_per_1k_output_tokens",
            "median",
        ),
    )
)


summary = summary.sort_values(
    "fairshare_cost_per_1k"
)


print()
print("=" * 110)
print("TOP RESULTS")
print("=" * 110)

print(
    summary.head(30).to_string(
        index=False
    )
)


print()
print("=" * 110)
print("BATCH SCALING BY INPUT LENGTH")
print("=" * 110)


for input_len in sorted(
    summary[
        "target_input_tokens"
    ].unique()
):

    print()
    print(
        f"INPUT = {input_len}"
    )

    subset = (
        summary[
            summary[
                "target_input_tokens"
            ] == input_len
        ]
        .sort_values(
            "batch_size"
        )
    )

    print(
        subset[
            [
                "batch_size",
                "output_tokens_per_sec",
                "requests_per_sec",
                "gpu_util_avg",
                "gpu_memory_max_mb",
                "fairshare_cost_per_1k",
            ]
        ].to_string(
            index=False
        )
    )


best = summary.iloc[0]


print()
print("=" * 110)
print("BEST OVERALL")
print("=" * 110)

print(
    f"""
Batch:
    {int(best['batch_size'])}

Input:
    {int(best['target_input_tokens'])}

Output throughput:
    {best['output_tokens_per_sec']:.2f} tok/s

Request throughput:
    {best['requests_per_sec']:.2f} req/s

GPU utilization:
    {best['gpu_util_avg']:.2f} %

Max VRAM:
    {best['gpu_memory_max_mb']:.0f} MB

FairShare / 1k tokens:
    {best['fairshare_cost_per_1k']:.4f}
"""
)


# ================================================================
# Check whether largest batch still improves
# ================================================================

print("=" * 110)
print("SATURATION CHECK")
print("=" * 110)


for input_len in sorted(
    summary[
        "target_input_tokens"
    ].unique()
):

    subset = (
        summary[
            summary[
                "target_input_tokens"
            ] == input_len
        ]
        .sort_values(
            "batch_size"
        )
    )

    if len(subset) < 2:
        continue

    prev = subset.iloc[-2]
    last = subset.iloc[-1]

    improvement = (
        (
            prev[
                "fairshare_cost_per_1k"
            ]
            -
            last[
                "fairshare_cost_per_1k"
            ]
        )
        /
        prev[
            "fairshare_cost_per_1k"
        ]
        * 100
    )

    print(
        f"input={input_len}: "
        f"batch {int(prev['batch_size'])} -> "
        f"{int(last['batch_size'])}: "
        f"{improvement:.2f}% improvement"
    )


summary.to_csv(
    "benchmark_batch_summary.csv",
    index=False,
)

print()
print(
    "Saved: benchmark_batch_summary.csv"
)