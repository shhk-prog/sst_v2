"""safety-utility 曲線（FR3.2）。

手法ごとに、横軸 Conditional ASR（低いほど良い）、縦軸 有用性（高いほど良い）で、点を α の順に結ぶ。
補間はしない。4 パターン各 1 枚（計 4 枚）。単一ドメインの 3 パターンは対応するタスクだけをプロットし、
``safety+math+code+medical`` は特化 3 タスクを 3 つのサブプロットで 1 枚にまとめる。
VRR の下限を満たさない点は、別の記号（×）で示す。

図中の文字は、フォントの都合で英語にしている（凡例、軸、タイトル）。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")  # 画面を使わない（CPU のみ、ヘッドレス）
import matplotlib.pyplot as plt  # noqa: E402

from . import manifest  # noqa: E402
from .compare import Point, points_from_records  # noqa: E402
from .metrics import load_point_records  # noqa: E402
from .results_io import PATTERN_DOMAINS, PATTERNS, inventory, scan_results  # noqa: E402
from .safeio import prepare_write_path, write_json  # noqa: E402

MARKERS = ["o", "s", "^", "D", "v", "P", "*", "h", "<", ">"]


def figure_stem(pattern: str) -> str:
    """パターン名をファイル名に使える形にする（``+`` を ``_`` に）。"""
    return "pareto_" + pattern.replace("+", "_")


def _method_styles(methods: Iterable[str]) -> dict[str, tuple[Any, str]]:
    cmap = plt.get_cmap("tab10")
    return {m: (cmap(i % 10), MARKERS[i % len(MARKERS)]) for i, m in enumerate(sorted(set(methods)))}


def plot_pattern(
    pattern: str,
    points: list[Point],
    vrr_floor: float,
    out_path: str | os.PathLike[str],
    all_methods: Iterable[str] | None = None,
) -> dict[str, Any]:
    """1 パターンの図を 1 枚書く。戻り値は、図の中身を確かめるためのメタ情報。

    ``points`` は、このパターンの全点（VRR で除外する前）。除外する点は × で示す。
    Conditional ASR または有用性が無い点は描けないので、``not_plotted`` に記録する。
    """
    domains = PATTERN_DOMAINS[pattern]
    methods = sorted({p.method for p in points} | set(all_methods or []))
    styles = _method_styles(methods)
    n_axes = len(domains)
    fig, axes = plt.subplots(1, n_axes, figsize=(5.6 * n_axes + 2.3, 4.8), squeeze=False)
    plotted = 0
    excluded_markers = 0
    not_plotted: list[str] = []
    points_info: list[dict[str, Any]] = []

    for ax, domain in zip(axes[0], domains):
        for method in methods:
            mpts = sorted((p for p in points if p.method == method), key=lambda p: -1.0 if p.alpha is None else p.alpha)
            drawable = [p for p in mpts if p.cond_asr is not None and p.util_mean(domain) is not None]
            for p in mpts:
                if p not in drawable and p.label not in not_plotted:
                    not_plotted.append(p.label)
            if not drawable:
                continue
            color, marker = styles[method]
            xs = [p.cond_asr for p in drawable]
            ys = [p.util_mean(domain) for p in drawable]
            if len(drawable) > 1:
                ax.plot(xs, ys, "-", color=color, alpha=0.45, linewidth=1.2, zorder=1)  # 補間せず、観測点を順に結ぶ
            for p in drawable:
                excluded = p.vrr is None or p.vrr < vrr_floor
                ax.scatter(
                    [p.cond_asr], [p.util_mean(domain)],
                    marker="x" if excluded else marker, color=color, s=46 if excluded else 38,
                    linewidths=1.6 if excluded else 0.8, zorder=3,
                )
                if method in ("sst", "task_arithmetic") and p.alpha in (0.0, 0.6, 1.0):
                    ax.annotate(
                        f"α={p.alpha:g}",
                        (p.cond_asr, p.util_mean(domain)),
                        textcoords="offset points",
                        xytext=(4, 4),
                        fontsize=7,
                        color=color,
                        alpha=0.9,
                    )
                plotted += 1
                excluded_markers += int(excluded)
                points_info.append({"domain": domain, "label": p.label, "cond_asr": p.cond_asr,
                                    "utility": p.util_mean(domain), "vrr": p.vrr, "excluded_by_vrr": excluded})
        ax.set_xlabel("Conditional ASR (%)  lower is better")
        ax.set_ylabel(f"{domain.capitalize()} utility (%)  higher is better")
        ax.set_title(f"{pattern} / {domain}")
        ax.grid(True, alpha=0.3)

    handles = [
        plt.Line2D([0], [0], color=styles[m][0], marker=styles[m][1], linestyle="-", label=m, markersize=6)
        for m in methods
    ]
    handles.append(plt.Line2D([0], [0], color="gray", marker="x", linestyle="", label=f"excluded (VRR < {vrr_floor:g}%)"))
    if plotted == 0:
        axes[0][0].text(0.5, 0.5, "no data", ha="center", va="center", transform=axes[0][0].transAxes)
    legend_x = 0.75 if n_axes == 1 else 0.88
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(legend_x, 0.5), fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0, legend_x - 0.01, 1))
    path = prepare_write_path(out_path)
    fig.savefig(path, dpi=130, metadata={"Software": None})
    plt.close(fig)
    return {
        "path": str(path),
        "pattern": pattern,
        "domains": domains,
        "n_axes": n_axes,
        "n_plotted": plotted,
        "n_excluded_markers": excluded_markers,
        "not_plotted": sorted(not_plotted),
        "points": points_info,
    }


def generate_pareto_figures(
    results_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    vrr_floor: float,
    rule: str,
    tol_pt: float | None = None,
) -> list[dict[str, Any]]:
    """4 パターン各 1 枚の図と、点の一覧（JSON）、manifest を ``out_dir`` に書く。

    ``tol_pt`` を渡すと、同じ点から求めた「観測事実」（Pareto 支配と近傍比較。FR1.5）を
    ``observations.json`` にも書く（レポートの結果の節が読む）。
    """
    out = Path(out_dir)
    scan = scan_results(results_root)
    inv = inventory(results_root, scan=scan)
    errors: list[dict[str, str]] = []
    records = load_point_records(scan.files, errors)
    points = points_from_records(records, rule)
    methods = sorted({p.method for p in points})
    metas: list[dict[str, Any]] = []
    for pattern in PATTERNS:
        pat_points = [p for p in points if p.pattern == pattern]
        png = out / f"{figure_stem(pattern)}.png"
        meta = plot_pattern(pattern, pat_points, vrr_floor, png, all_methods=methods)
        write_json(out / f"{figure_stem(pattern)}.points.json", meta["points"])
        used = sorted(
            {
                path
                for rec in records
                if rec["kind"] == "main" and rec["pattern"] == pattern
                for path in list(rec["sources"]["safety"].values())
                + [i["path"] for i in rec["sources"]["tasks"].values()]
                + list(rec["sources"]["other"].values())
            }
        )
        manifest.write_manifest(
            png,
            script="v5/scripts/plot_pareto_curves.py",
            inputs=used,
            counts={"n_points": len(pat_points), "n_plotted": meta["n_plotted"],
                    "n_excluded_markers": meta["n_excluded_markers"], "n_axes": meta["n_axes"],
                    "n_load_errors": len(errors)},
            missing=[m for m in inv["missing"] if m["pattern"] == pattern],
            settings={"harm_rule": rule, "vrr_floor": vrr_floor, "domains": meta["domains"],
                      "not_plotted": meta["not_plotted"], "results_root": str(results_root)},
        )
        metas.append(meta)
    if tol_pt is not None:
        from .compare import summarize_observations

        obs_path = out / "observations.json"
        write_json(obs_path, summarize_observations(points, vrr_floor, tol_pt))
        manifest.write_manifest(
            obs_path,
            script="v5/scripts/plot_pareto_curves.py",
            inputs=sorted(
                {path for rec in records if rec["kind"] == "main"
                 for path in list(rec["sources"]["safety"].values())
                 + [i["path"] for i in rec["sources"]["tasks"].values()]}
            ),
            counts={"n_points": len(points)},
            missing=inv["missing"],
            settings={"harm_rule": rule, "vrr_floor": vrr_floor, "neighborhood_tolerance_pt": tol_pt},
        )
    return metas
