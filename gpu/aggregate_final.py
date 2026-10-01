#!/usr/bin/env python3

import glob
import pandas as pd


FILES = "results_final/result_*.csv"
OUTPUT = "benchmark_final_summary.csv"

SATURATION_THRESHOLD = 2.0


files = sorted(glob.glob(FILES))

if not files:
    raise RuntimeError(
        f"No files found: {FILES}"
    )


frames = []

for filename in files:
    try:
        frames.append(
            pd.read_csv(filename)
        )
    except Exception as e:
        print(
            f"WARNING: {filename}: {e}"
        )


df = pd.concat(
    frames,
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
        measurements=(
            "repeat",
            "count",
        ),
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
    [
        "target_input_tokens",
        "batch_size",
    ]
)


# ================================================================
# Improvement between adjacent batches
# ================================================================

summary[
    "fs_improvement_percent"
] = None


for input_len in summary[
    "target_input_tokens"
].unique():

    mask = (
        summary[
            "target_input_tokens"
        ] == input_len
    )

    indices = summary[
        mask
    ].sort_values(
        "batch_size"
    ).index.tolist()

    for i in range(1, len(indices)):

        prev_idx = indices[i - 1]
        curr_idx = indices[i]

        prev_cost = summary.loc[
            prev_idx,
            "fairshare_cost_per_1k",
        ]

        curr_cost = summary.loc[
            curr_idx,
            "fairshare_cost_per_1k",
        ]

        improvement = (
            (prev_cost - curr_cost)
            / prev_cost
            * 100
        )

        summary.loc[
            curr_idx,
            "fs_improvement_percent",
        ] = improvement


summary.to_csv(
    OUTPUT,
    index=False,
)


# ================================================================
# Ranking
# ================================================================

ranking = summary.sort_values(
    "fairshare_cost_per_1k"
)


print()
print("=" * 120)
print("OVERALL RANKING")
print("=" * 120)

print(
    ranking[
        [
            "batch_size",
            "target_input_tokens",
            "output_tokens_per_sec",
            "requests_per_sec",
            "gpu_util_avg",
            "gpu_memory_max_mb",
            "fairshare_cost_per_1k",
            "fs_improvement_percent",
        ]
    ].to_string(
        index=False,
    )
)


# ================================================================
# Scaling analysis
# ================================================================

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

    print()
    print("=" * 120)
    print(
        f"INPUT LENGTH = {input_len}"
    )
    print("=" * 120)

    print(
        subset[
            [
                "batch_size",
                "output_tokens_per_sec",
                "requests_per_sec",
                "gpu_util_avg",
                "fairshare_cost_per_1k",
                "fs_improvement_percent",
            ]
        ].to_string(
            index=False,
        )
    )


    # ------------------------------------------------------------
    # Best
    # ------------------------------------------------------------

    best = subset.loc[
        subset[
            "fairshare_cost_per_1k"
        ].idxmin()
    ]

    print()
    print(
        f"Best batch = "
        f"{int(best['batch_size'])}"
    )

    print(
        f"Best FS/1k = "
        f"{best['fairshare_cost_per_1k']:.4f}"
    )


    # ------------------------------------------------------------
    # Saturation detection
    # ------------------------------------------------------------

    saturation_found = False

    rows = subset.reset_index(
        drop=True
    )

    for i in range(
        1,
        len(rows)
    ):

        improvement = rows.loc[
            i,
            "fs_improvement_percent",
        ]

        if pd.isna(improvement):
            continue

        previous_batch = int(
            rows.loc[
                i - 1,
                "batch_size",
            ]
        )

        current_batch = int(
            rows.loc[
                i,
                "batch_size",
            ]
        )

        if improvement < 0:

            print()
            print(
                f"Efficiency worsened at "
                f"{previous_batch} -> {current_batch} "
                f"({improvement:.2f}%)."
            )

            print(
                f"Recommended batch: "
                f"{previous_batch}"
            )

            saturation_found = True
            break


        if improvement < SATURATION_THRESHOLD:

            print()
            print(
                f"Saturation detected at "
                f"{previous_batch} -> {current_batch}: "
                f"{improvement:.2f}% improvement."
            )

            print(
                f"Recommended practical batch: "
                f"{previous_batch}"
            )

            saturation_found = True
            break


    if not saturation_found:

        largest_batch = int(
            rows.iloc[-1][
                "batch_size"
            ]
        )

        last_improvement = rows.iloc[-1][
            "fs_improvement_percent"
        ]

        print()

        if pd.notna(last_improvement):

            print(
                f"Batch {largest_batch} still improves "
                f"FS efficiency by "
                f"{last_improvement:.2f}%."
            )

        print(
            "No saturation detected in tested range."
        )

        print(
            "Consider testing larger batches."
        )


# ================================================================
# Best overall
# ================================================================

best = ranking.iloc[0]

print()
print("=" * 120)
print("BEST OVERALL")
print("=" * 120)

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

Maximum VRAM:
    {best['gpu_memory_max_mb']:.0f} MB

FairShare / 1k tokens:
    {best['fairshare_cost_per_1k']:.4f}
"""
)

print(
    f"Saved: {OUTPUT}"
)