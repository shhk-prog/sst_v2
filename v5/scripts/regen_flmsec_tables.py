#!/usr/bin/env python3
"""FLMSEC 論文の主な表（手法 x タスク）を、v3/results/vllm から再生成し、論文の表と照合する（FR3.1）。

有害判定は、HarmBench Classifier 単独（主軸）と、generate_flmsec_hyo.py の OR 判定（再現確認用）の
両方で計算する。一致しない箇所は一覧にし、判定の違いによる差は別項目にする。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/regen_flmsec_tables.py
出力: v5/outputs/tables/（表、JSON、manifest、paper_comparison.md）。v3/ には書かない。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401  (import パスと既定値)
from _common import DEFAULT_OUT, DEFAULT_PAPER_TEX, DEFAULT_RESULTS_ROOT, load_prereg

from v5lib import tables
from v5lib.safeio import open_readonly


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT, help="結果ルート（読み取り専用）")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "tables", help="出力先（v5/ の下だけ）")
    parser.add_argument("--alpha", type=float, default=0.6, help="主結果の α（既定 0.6）")
    parser.add_argument("--paper-tex", type=Path, action="append", default=None,
                        help="論文の LaTeX（複数指定可。既定は FLMSEC の appendix.tex）")
    parser.add_argument("--no-paper", action="store_true", help="論文との照合を行わない")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prereg = load_prereg()
    tol = float(prereg["comparison"]["paper_compare_tolerance"])
    paper_tex: dict[str, str] | None = None
    if not args.no_paper:
        texts = []
        for path in args.paper_tex or [DEFAULT_PAPER_TEX]:
            try:
                with open_readonly(path) as handle:
                    texts.append(handle.read())
            except OSError as exc:
                print(f"論文の LaTeX を読めません: {path}: {exc}", file=sys.stderr)
                return 2
        joined = "\n".join(texts)
        paper_tex = {label: joined for label in tables.PAPER_TABLES}
    try:
        info = tables.generate_flmsec_tables(args.results_root, args.out_dir, args.alpha, paper_tex, tol)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    for path in info["written"]:
        print(f"書き込み: {path}")
    print(f"読み込みエラー: {info['n_load_errors']} 件、欠損（主実験）: {info['inventory_missing']} 件")
    for label, counts in info["comparison_counts"].items():
        print(f"照合 {label}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
