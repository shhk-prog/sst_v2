#!/usr/bin/env python3
"""手法ごとの safety-utility 曲線を、4 パターン各 1 枚（計 4 枚）で出す（FR3.2）。

横軸 Conditional ASR（HarmBench Classifier 単独）、縦軸 有用性。点を α の順に結ぶ（補間しない）。
VRR の下限は事前登録（preregistration.json）から読む。下限を満たさない点は × で示す。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/plot_pareto_curves.py
出力: v5/outputs/figures/。感度分析の下限（90、50）は、そのサブフォルダ。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, DEFAULT_RESULTS_ROOT, load_prereg

from v5lib import plots
from v5lib.hypotheses import neighborhood_tolerance, vrr_floors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT, help="結果ルート（読み取り専用）")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "figures", help="出力先（v5/ の下だけ）")
    parser.add_argument("--vrr-floor", type=float, default=None,
                        help="VRR の下限。事前登録の値（主または感度分析）だけを許す。既定は主の値")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prereg = load_prereg()
    primary, sensitivity = vrr_floors(prereg)
    rule = prereg["comparison"]["harm_rule_primary"]
    floor = primary if args.vrr_floor is None else args.vrr_floor
    if floor != primary and floor not in sensitivity:
        print(f"VRR の下限 {floor} は事前登録にありません（主 {primary}、感度分析 {sensitivity}）", file=sys.stderr)
        return 2
    out_dir = args.out_dir if floor == primary else args.out_dir / f"sensitivity_vrr{floor:g}"
    try:
        metas = plots.generate_pareto_figures(args.results_root, out_dir, floor, rule,
                                              tol_pt=neighborhood_tolerance(prereg))
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    for meta in metas:
        print(f"書き込み: {meta['path']}（サブプロット {meta['n_axes']}、点 {meta['n_plotted']}、除外の記号 {meta['n_excluded_markers']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
