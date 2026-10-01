import re
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import numpy as np


# ==========================================
# Load data
# ==========================================

filepath = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_hyo_vllm_latex.md"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# method -> list of (alpha, safety_asr, utility)
data = defaultdict(list)

current_method = None
current_pattern = None

for line in lines:
    if line.startswith("% --- Alpha スイープ 集計 - Method: "):
        match = re.search(r"Method: (.*?), Pattern: (.*?) ---", line)
        if match:
            current_method = match.group(1)
            current_pattern = match.group(2)

    if current_pattern == "safety+math" and current_method:
        if line.startswith("safety+math &"):
            parts = [x.strip() for x in line.split("&")]

            if len(parts) > 5:
                alpha = parts[2]
                safety_str = parts[3].split("$\\pm")[0].replace("\\pm", "").strip()
                utility_str = parts[4].split("$\\pm")[0].replace("\\pm", "").strip()

                try:
                    safety = float(safety_str)
                    utility = float(utility_str)

                    if alpha != "N/A":
                        alpha_val = float(alpha)
                    else:
                        alpha_val = 0.0

                    data[current_method].append(
                        (alpha_val, safety, utility)
                    )

                except ValueError:
                    pass


# ==========================================
# Aggregate repeated runs by alpha
# ==========================================

def aggregate_by_alpha(points):
    grouped_saf = defaultdict(list)
    grouped_util = defaultdict(list)

    for alpha, saf, util in points:
        grouped_saf[alpha].append(saf)
        grouped_util[alpha].append(util)

    alphas = sorted(grouped_saf.keys())

    means_saf = np.array([
        np.mean(grouped_saf[a])
        for a in alphas
    ])

    stds_saf = np.array([
        np.std(grouped_saf[a])
        for a in alphas
    ])

    means_util = np.array([
        np.mean(grouped_util[a])
        for a in alphas
    ])

    stds_util = np.array([
        np.std(grouped_util[a])
        for a in alphas
    ])

    return (
        np.array(alphas),
        means_saf,
        stds_saf,
        means_util,
        stds_util,
    )


# ==========================================
# Pareto AUC
# ==========================================

auc_data = {
    "SST-Merge": 0.2935,
    "Data-Free SST": 0.2914,
    "TIES": 0.2929,
    "DELLA": 0.2908,
    "DARE": 0.2882,
    "Task Arithmetic": 0.2853,
    "Matena Fisher": 0.2814,
}

auc_data = dict(
    sorted(
        auc_data.items(),
        key=lambda item: item[1]
    )
)


# ==========================================
# Plot settings
# ==========================================

plt.style.use("seaborn-v0_8-whitegrid")

fig = plt.figure(figsize=(18, 6))

gs = gridspec.GridSpec(
    1,
    3,
    width_ratios=[1, 1, 1],
)

ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
ax3 = fig.add_subplot(gs[2])


all_methods = [
    "diagonal_sst_main",
    "data_free_sst_main",
    "ties",
    "dare",
    "della",
    "task_arithmetic",
    "matena_fisher",
]

highlight_methods = [
    "diagonal_sst_main",
    "data_free_sst_main",
    "della",
    "ties",
]


colors = {
    "diagonal_sst_main": "#e74c3c",
    "data_free_sst_main": "#e67e22",
    "della": "#9b59b6",
    "ties": "#3498db",
}


# ==========================================
# Panel (a)
# Safety vs Alpha
# ==========================================

all_safetys = []

for method in highlight_methods:
    points = data.get(method)

    if not points:
        continue

    (
        alphas,
        means_saf,
        stds_saf,
        _,
        _,
    ) = aggregate_by_alpha(points)

    all_safetys.extend(means_saf)

    is_sst = "sst" in method
    color = colors[method]

    linewidth = 3.5 if is_sst else 1.5
    markersize = 6 if is_sst else 4
    zorder = 5 if is_sst else 3

    ax1.plot(
        alphas,
        means_saf,
        "o-",
        color=color,
        linewidth=linewidth,
        markersize=markersize,
        zorder=zorder,
        alpha=1.0 if is_sst else 0.8,
    )

    ax1.fill_between(
        alphas,
        means_saf - stds_saf,
        means_saf + stds_saf,
        color=color,
        alpha=0.15 if is_sst else 0.08,
        zorder=zorder - 1,
    )


ax1.set_xlim(
    -0.05,
    1.05,
)

ax1.set_ylim(
    -5,
    125,
)

ax1.set_xlabel(
    r"Merge Strength ($\alpha$)",
    fontsize=12,
    fontweight="bold",
)

ax1.set_ylabel(
    "Harmful ASR (%) ↓",
    fontsize=12,
    fontweight="bold",
)

ax1.set_title(
    "(a) Safety across merge strength",
    fontsize=14,
    fontweight="bold",
    pad=15,
)


# ------------------------------------------
# Panel (a) legend
# ------------------------------------------

legend_a = [
    Line2D(
        [0],
        [0],
        color=colors["diagonal_sst_main"],
        linewidth=3.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["data_free_sst_main"],
        linewidth=3.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["ties"],
        linewidth=1.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["della"],
        linewidth=1.5,
    ),
]

ax1.legend(
    legend_a,
    [
        "SST-Merge (Ours)",
        "Data-Free SST (Ours)",
        "TIES",
        "DELLA",
    ],
    loc="upper right",
    fontsize=10,
)


# ==========================================
# Panel (b)
# Utility Retention vs Alpha
# ==========================================

for method in highlight_methods:
    points = data.get(method)

    if not points:
        continue

    (
        alphas,
        _,
        _,
        means_util,
        stds_util,
    ) = aggregate_by_alpha(points)

    baseline_util = means_util[0]

    if baseline_util == 0:
        continue

    retention_means = (
        means_util / baseline_util * 100
    )

    retention_stds = (
        stds_util / baseline_util * 100
    )

    is_sst = "sst" in method
    color = colors[method]

    linewidth = 3.5 if is_sst else 1.5
    markersize = 6 if is_sst else 4
    zorder = 5 if is_sst else 3

    ax2.plot(
        alphas,
        retention_means,
        "o-",
        color=color,
        linewidth=linewidth,
        markersize=markersize,
        zorder=zorder,
        alpha=1.0 if is_sst else 0.8,
    )

    ax2.fill_between(
        alphas,
        retention_means - retention_stds,
        retention_means + retention_stds,
        color=color,
        alpha=0.15 if is_sst else 0.08,
        zorder=zorder - 1,
    )


ax2.set_xlim(
    -0.05,
    1.05,
)

ax2.set_ylim(
    -5,
    125,
)

ax2.set_xlabel(
    r"Merge Strength ($\alpha$)",
    fontsize=12,
    fontweight="bold",
)

ax2.set_ylabel(
    "Utility Retention (%) ↑",
    fontsize=12,
    fontweight="bold",
)

ax2.set_title(
    "(b) Utility retention across merge strength",
    fontsize=14,
    fontweight="bold",
    pad=15,
)


# ------------------------------------------
# Panel (b) legend
# ------------------------------------------

custom_lines = [
    Line2D(
        [0],
        [0],
        color=colors["diagonal_sst_main"],
        linewidth=3.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["data_free_sst_main"],
        linewidth=3.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["ties"],
        linewidth=1.5,
    ),
    Line2D(
        [0],
        [0],
        color=colors["della"],
        linewidth=1.5,
    ),
]

ax2.legend(
    custom_lines,
    [
        "SST-Merge (Ours)",
        "Data-Free SST (Ours)",
        "TIES",
        "DELLA",
    ],
    loc="lower left",
    fontsize=10,
)


# ==========================================
# Panel (c)
# Validity-aware Pareto AUC
# ==========================================

names = list(auc_data.keys())
values = list(auc_data.values())

bar_colors = []

for name in names:
    if name == "SST-Merge":
        bar_colors.append(
            colors["diagonal_sst_main"]
        )

    elif name == "Data-Free SST":
        bar_colors.append(
            colors["data_free_sst_main"]
        )

    elif name == "DELLA":
        bar_colors.append(
            colors["della"]
        )

    elif name == "TIES":
        bar_colors.append(
            colors["ties"]
        )

    else:
        bar_colors.append(
            "#bdc3c7"
        )


# ------------------------------------------
# Dot Plot
# ------------------------------------------

for name, val, color in zip(names, values, bar_colors):
    # Optional: draw a faint guideline to the point
    ax3.plot(
        [0.28, val],
        [name, name],
        color="#e0e0e0",
        linestyle="--",
        linewidth=1.2,
        zorder=1,
    )

    # Plot the dot
    ax3.plot(
        val,
        name,
        "o",
        color=color,
        markersize=10,
        zorder=3,
    )

    # Add text label slightly to the right
    ax3.text(
        val + 0.0004,
        name,
        f"{val:.4f}",
        horizontalalignment="left",
        verticalalignment="center",
        fontsize=11,
        fontweight="bold",
    )


ax3.set_xlim(
    0.28,
    0.296,
)

ax3.set_xlabel(
    "Validity-aware Pareto AUC ↑",
    fontsize=12,
    fontweight="bold",
)

ax3.set_title(
    "(c) Validity-aware Pareto performance",
    fontsize=14,
    fontweight="bold",
    pad=15,
)


# ==========================================
# Final layout and save
# ==========================================

plt.tight_layout()

output_path = (
    "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/"
    "pareto_three_panel.png"
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

print(f"Saved: {output_path}")