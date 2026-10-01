#!/usr/bin/env python3

import glob
from pathlib import Path

import numpy as np
import pandas as pd


# ================================================================
# Settings
# ================================================================

RESULT_SOURCES = [
    ("initial", "results/result_*.csv"),
    ("vllm_memory_search", "results_vllm2/result_*.csv"),
    ("batch_search", "results_batch/result_*.csv"),
    ("final_search", "results_final/result_*.csv"),
]

OUTPUT_DIR = Path("all_results_summary")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ================================================================
# Load all CSV files
# ================================================================

frames = []

print("=" * 100)
print("LOAD RESULTS")
print("=" * 100)

for experiment_name, pattern in RESULT_SOURCES:

    files = sorted(glob.glob(pattern))

    print(
        f"{experiment_name:25s}: "
        f"{len(files):4d} files"
    )

    for filename in files:

        try:
            df = pd.read_csv(filename)

        except Exception as e:
            print(
                f"WARNING: failed to read {filename}: {e}"
            )
            continue

        if df.empty:
            continue

        df["experiment"] = experiment_name
        df["source_file"] = filename

        frames.append(df)


if not frames:
    raise RuntimeError(
        "No benchmark CSV files were found."
    )


raw = pd.concat(
    frames,
    ignore_index=True,
    sort=False,
)


print()
print(
    f"Total raw measurements: {len(raw)}"
)


# ================================================================
# Normalize columns
# ================================================================

# Old experiments contain engine.
# Newer vLLM-only experiments do not.
if "engine" not in raw.columns:
    raw["engine"] = "vllm"
else:
    raw["engine"] = raw["engine"].fillna("vllm")


# GPU memory utilization may be missing in initial experiments.
if "gpu_memory_utilization" not in raw.columns:
    raw["gpu_memory_utilization"] = np.nan


# Normalization defaults
if "cpu_cores" not in raw.columns:
    raw["cpu_cores"] = np.nan

if "batch_size" not in raw.columns:
    raw["batch_size"] = np.nan

if "target_input_tokens" not in raw.columns:
    raw["target_input_tokens"] = np.nan

if "target_output_tokens" not in raw.columns:
    raw["target_output_tokens"] = np.nan


# ================================================================
# Ensure numeric columns
# ================================================================

numeric_columns = [
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

for column in numeric_columns:

    if column in raw.columns:

        raw[column] = pd.to_numeric(
            raw[column],
            errors="coerce",
        )


# ================================================================
# Recalculate FairShare where possible
#
# GPU = 30
# CPU core = 1
# ================================================================

mask = (
    raw["walltime_sec"].notna()
    & raw["cpu_cores"].notna()
)

raw.loc[
    mask,
    "fairshare_cost_recalculated",
] = (
    30
    + raw.loc[mask, "cpu_cores"]
) * raw.loc[mask, "walltime_sec"]


mask_fs = (
    raw["fairshare_cost_recalculated"].notna()
    & raw["output_tokens"].notna()
    & (raw["output_tokens"] > 0)
)

raw.loc[
    mask_fs,
    "fairshare_cost_per_1k_recalculated",
] = (
    raw.loc[
        mask_fs,
        "fairshare_cost_recalculated",
    ]
    /
    raw.loc[
        mask_fs,
        "output_tokens",
    ]
    * 1000
)


# Prefer recalculated value for consistency.
raw["fs_per_1k"] = raw[
    "fairshare_cost_per_1k_recalculated"
]

if "fairshare_cost_per_1k_output_tokens" in raw.columns:

    raw["fs_per_1k"] = (
        raw["fs_per_1k"]
        .fillna(
            raw[
                "fairshare_cost_per_1k_output_tokens"
            ]
        )
    )


# ================================================================
# Save all raw results
# ================================================================

raw_output = (
    OUTPUT_DIR
    / "all_raw_measurements.csv"
)

raw.to_csv(
    raw_output,
    index=False,
)


# ================================================================
# Aggregate identical configurations
#
# Same condition may appear in several experiments.
# We intentionally combine them.
# ================================================================

group_columns = [
    "engine",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
    "gpu_memory_utilization",
]


metrics = {}


def add_metric(
    column,
    output_name,
    function="median",
):
    if column in raw.columns:
        metrics[output_name] = (
            column,
            function,
        )


add_metric(
    "walltime_sec",
    "walltime_sec",
)

add_metric(
    "requests_per_sec",
    "requests_per_sec",
)

add_metric(
    "input_tokens_per_sec",
    "input_tokens_per_sec",
)

add_metric(
    "output_tokens_per_sec",
    "output_tokens_per_sec",
)

add_metric(
    "total_tokens_per_sec",
    "total_tokens_per_sec",
)

add_metric(
    "gpu_util_avg",
    "gpu_util_avg",
)

add_metric(
    "gpu_util_max",
    "gpu_util_max",
    "max",
)

add_metric(
    "gpu_memory_avg_mb",
    "gpu_memory_avg_mb",
)

add_metric(
    "gpu_memory_max_mb",
    "gpu_memory_max_mb",
    "max",
)

add_metric(
    "gpu_power_avg_w",
    "gpu_power_avg_w",
)

add_metric(
    "fairshare_cost_recalculated",
    "fairshare_cost",
)

add_metric(
    "fs_per_1k",
    "fairshare_cost_per_1k",
)


# groupby normally drops NaN.
# dropna=False is essential because early experiments may not have
# gpu_memory_utilization recorded.
summary = (
    raw
    .groupby(
        group_columns,
        dropna=False,
        as_index=False,
    )
    .agg(
        measurements=(
            "source_file",
            "count",
        ),
        experiments=(
            "experiment",
            lambda x: ",".join(
                sorted(set(x))
            ),
        ),
        **metrics,
    )
)


# ================================================================
# FairShare ranking
# ================================================================

summary = summary.sort_values(
    "fairshare_cost_per_1k",
    ascending=True,
    na_position="last",
).reset_index(drop=True)

summary.insert(
    0,
    "rank",
    np.arange(
        1,
        len(summary) + 1,
    ),
)


summary_output = (
    OUTPUT_DIR
    / "all_configuration_summary.csv"
)

summary.to_csv(
    summary_output,
    index=False,
)


# ================================================================
# vLLM-only results
# ================================================================

vllm = summary[
    summary["engine"] == "vllm"
].copy()


# ================================================================
# Best configuration overall
# ================================================================

valid = summary[
    summary[
        "fairshare_cost_per_1k"
    ].notna()
]

if valid.empty:
    raise RuntimeError(
        "No valid FairShare results."
    )

best = valid.iloc[0]


# ================================================================
# Best configuration for each input length
# ================================================================

best_by_input = (
    valid
    .sort_values(
        "fairshare_cost_per_1k"
    )
    .groupby(
        "target_input_tokens",
        as_index=False,
    )
    .first()
)

best_by_input.to_csv(
    OUTPUT_DIR / "best_by_input_length.csv",
    index=False,
)


# ================================================================
# Best configuration for each engine
# ================================================================

best_by_engine = (
    valid
    .sort_values(
        "fairshare_cost_per_1k"
    )
    .groupby(
        "engine",
        as_index=False,
    )
    .first()
)

best_by_engine.to_csv(
    OUTPUT_DIR / "best_by_engine.csv",
    index=False,
)


# ================================================================
# CPU scaling
# ================================================================

cpu_scaling = (
    summary[
        summary["batch_size"] == 32
    ]
    .sort_values(
        [
            "target_input_tokens",
            "cpu_cores",
        ]
    )
)

cpu_scaling.to_csv(
    OUTPUT_DIR / "cpu_scaling.csv",
    index=False,
)


# ================================================================
# Batch scaling
#
# Use vLLM + CPU 1
# ================================================================

batch_scaling = vllm[
    vllm["cpu_cores"] == 1
].copy()


# For each identical batch/input, select best memory setting.
batch_scaling_best = (
    batch_scaling
    .sort_values(
        "fairshare_cost_per_1k"
    )
    .groupby(
        [
            "batch_size",
            "target_input_tokens",
        ],
        as_index=False,
    )
    .first()
    .sort_values(
        [
            "target_input_tokens",
            "batch_size",
        ]
    )
)


# ================================================================
# Calculate batch-to-batch improvement
# ================================================================

batch_scaling_best[
    "previous_batch"
] = np.nan

batch_scaling_best[
    "previous_fs_per_1k"
] = np.nan

batch_scaling_best[
    "fs_improvement_percent"
] = np.nan

batch_scaling_best[
    "throughput_improvement_percent"
] = np.nan


for input_length in sorted(
    batch_scaling_best[
        "target_input_tokens"
    ].dropna().unique()
):

    indices = (
        batch_scaling_best[
            batch_scaling_best[
                "target_input_tokens"
            ] == input_length
        ]
        .sort_values(
            "batch_size"
        )
        .index
        .tolist()
    )

    for i in range(
        1,
        len(indices),
    ):

        prev_idx = indices[i - 1]
        curr_idx = indices[i]

        previous_batch = (
            batch_scaling_best.loc[
                prev_idx,
                "batch_size",
            ]
        )

        previous_fs = (
            batch_scaling_best.loc[
                prev_idx,
                "fairshare_cost_per_1k",
            ]
        )

        current_fs = (
            batch_scaling_best.loc[
                curr_idx,
                "fairshare_cost_per_1k",
            ]
        )

        previous_throughput = (
            batch_scaling_best.loc[
                prev_idx,
                "output_tokens_per_sec",
            ]
        )

        current_throughput = (
            batch_scaling_best.loc[
                curr_idx,
                "output_tokens_per_sec",
            ]
        )


        batch_scaling_best.loc[
            curr_idx,
            "previous_batch",
        ] = previous_batch

        batch_scaling_best.loc[
            curr_idx,
            "previous_fs_per_1k",
        ] = previous_fs


        if (
            pd.notna(previous_fs)
            and pd.notna(current_fs)
            and previous_fs != 0
        ):

            improvement = (
                (
                    previous_fs
                    - current_fs
                )
                /
                previous_fs
                * 100
            )

            batch_scaling_best.loc[
                curr_idx,
                "fs_improvement_percent",
            ] = improvement


        if (
            pd.notna(previous_throughput)
            and pd.notna(current_throughput)
            and previous_throughput != 0
        ):

            throughput_improvement = (
                (
                    current_throughput
                    - previous_throughput
                )
                /
                previous_throughput
                * 100
            )

            batch_scaling_best.loc[
                curr_idx,
                "throughput_improvement_percent",
            ] = throughput_improvement


batch_scaling_best.to_csv(
    OUTPUT_DIR
    / "batch_scaling_all.csv",
    index=False,
)


# ================================================================
# Best batch for each input length
# ================================================================

best_batch_by_input = (
    batch_scaling_best
    .sort_values(
        "fairshare_cost_per_1k"
    )
    .groupby(
        "target_input_tokens",
        as_index=False,
    )
    .first()
)

best_batch_by_input.to_csv(
    OUTPUT_DIR
    / "best_batch_by_input.csv",
    index=False,
)


# ================================================================
# GPU memory utilization comparison
# ================================================================

memory_results = (
    vllm[
        vllm[
            "gpu_memory_utilization"
        ].notna()
    ]
    .sort_values(
        "fairshare_cost_per_1k"
    )
)

best_by_memory = (
    memory_results
    .groupby(
        "gpu_memory_utilization",
        as_index=False,
    )
    .first()
)

best_by_memory.to_csv(
    OUTPUT_DIR
    / "best_by_gpu_memory_utilization.csv",
    index=False,
)


# ================================================================
# Print summary
# ================================================================

print()
print("=" * 120)
print("TOP 30 OVERALL")
print("=" * 120)

display_columns = [
    "rank",
    "engine",
    "cpu_cores",
    "batch_size",
    "target_input_tokens",
    "target_output_tokens",
    "gpu_memory_utilization",
    "output_tokens_per_sec",
    "requests_per_sec",
    "gpu_util_avg",
    "gpu_memory_max_mb",
    "fairshare_cost_per_1k",
    "measurements",
]

available_display_columns = [
    c
    for c in display_columns
    if c in summary.columns
]

print(
    summary[
        available_display_columns
    ]
    .head(30)
    .to_string(
        index=False,
    )
)


# ================================================================
# Overall best
# ================================================================

print()
print("=" * 120)
print("BEST OVERALL")
print("=" * 120)

print(
    f"""
Engine:
    {best['engine']}

CPU cores:
    {best['cpu_cores']:.0f}

Batch:
    {best['batch_size']:.0f}

Input tokens:
    {best['target_input_tokens']:.0f}

Output tokens:
    {best['target_output_tokens']:.0f}

GPU memory utilization:
    {best['gpu_memory_utilization']}

Output throughput:
    {best['output_tokens_per_sec']:.2f} tok/s

Request throughput:
    {best['requests_per_sec']:.2f} req/s

GPU utilization:
    {best['gpu_util_avg']:.2f} %

Maximum VRAM:
    {best['gpu_memory_max_mb']:.0f} MB

FairShare / 1k generated tokens:
    {best['fairshare_cost_per_1k']:.4f}

Number of measurements:
    {int(best['measurements'])}

Experiment sources:
    {best['experiments']}
"""
)


# ================================================================
# Best per input length
# ================================================================

print()
print("=" * 120)
print("BEST FOR EACH INPUT LENGTH")
print("=" * 120)

columns = [
    "target_input_tokens",
    "engine",
    "cpu_cores",
    "batch_size",
    "gpu_memory_utilization",
    "output_tokens_per_sec",
    "gpu_util_avg",
    "fairshare_cost_per_1k",
]

print(
    best_by_input[
        columns
    ].to_string(
        index=False,
    )
)


# ================================================================
# Full batch scaling
# ================================================================

print()
print("=" * 120)
print("ALL vLLM BATCH SCALING")
print("=" * 120)

columns = [
    "target_input_tokens",
    "batch_size",
    "gpu_memory_utilization",
    "output_tokens_per_sec",
    "requests_per_sec",
    "gpu_util_avg",
    "fairshare_cost_per_1k",
    "fs_improvement_percent",
]

print(
    batch_scaling_best[
        columns
    ]
    .sort_values(
        [
            "target_input_tokens",
            "batch_size",
        ]
    )
    .to_string(
        index=False,
    )
)


# ================================================================
# Best batch by input
# ================================================================

print()
print("=" * 120)
print("BEST BATCH FOR EACH INPUT LENGTH")
print("=" * 120)

columns = [
    "target_input_tokens",
    "batch_size",
    "gpu_memory_utilization",
    "output_tokens_per_sec",
    "requests_per_sec",
    "gpu_util_avg",
    "fairshare_cost_per_1k",
]

print(
    best_batch_by_input[
        columns
    ].to_string(
        index=False,
    )
)


# ================================================================
# Improvement from batch 32 to best batch
# ================================================================

print()
print("=" * 120)
print("IMPROVEMENT FROM BATCH 32")
print("=" * 120)

for input_length in sorted(
    batch_scaling_best[
        "target_input_tokens"
    ].dropna().unique()
):

    subset = batch_scaling_best[
        batch_scaling_best[
            "target_input_tokens"
        ] == input_length
    ]

    baseline = subset[
        subset["batch_size"] == 32
    ]

    if baseline.empty:
        continue

    best_row = subset.loc[
        subset[
            "fairshare_cost_per_1k"
        ].idxmin()
    ]

    base_row = baseline.iloc[0]

    fs_improvement = (
        (
            base_row[
                "fairshare_cost_per_1k"
            ]
            -
            best_row[
                "fairshare_cost_per_1k"
            ]
        )
        /
        base_row[
            "fairshare_cost_per_1k"
        ]
        * 100
    )

    throughput_gain = (
        best_row[
            "output_tokens_per_sec"
        ]
        /
        base_row[
            "output_tokens_per_sec"
        ]
    )


    print(
        f"input={int(input_length):4d}: "
        f"batch "
        f"{int(base_row['batch_size'])} -> "
        f"{int(best_row['batch_size'])}, "
        f"FS/1k "
        f"{base_row['fairshare_cost_per_1k']:.4f} -> "
        f"{best_row['fairshare_cost_per_1k']:.4f}, "
        f"improvement={fs_improvement:.2f}%, "
        f"throughput={throughput_gain:.2f}x"
    )


# ================================================================
# Files
# ================================================================

print()
print("=" * 120)
print("OUTPUT FILES")
print("=" * 120)

for path in sorted(
    OUTPUT_DIR.glob("*.csv")
):
    print(path)