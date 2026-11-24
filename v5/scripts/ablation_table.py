#!/usr/bin/env python3
"""SST のアブレーションを、論文と同じ形（k x variant）の表にまとめる（FR3.3、FR3.4）。

条件（パターン、α、比、層重み、n）をそろえた列だけを同じ表に並べる。α を動かした効果は別の表にする。
v3 に結果が無い条件は、別の条件で代用せず N/A とし、欠損の一覧（manifest）に理由と探したファイル名の型を書く。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/ablation_table.py
出力: v5/outputs/tables/ablation_*.md / .json / .manifest.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, DEFAULT_RESULTS_ROOT, load_prereg

from v5lib import ablation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT, help="結果ルート（読み取り専用）")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "tables", help="出力先（v5/ の下だけ）")
    parser.add_argument("--pattern", action="append", default=None, help="対象パターン（複数指定可。既定はアブレーションの結果があるもの）")
    parser.add_argument("--family", action="append", choices=["sst", "datafree"], default=None, help="系列（既定は両方）")
    parser.add_argument("--n-samples", type=int, default=500, help="sst 系列の FIM サンプル数 n（中心条件は 500）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rule = load_prereg()["comparison"]["harm_rule_primary"]
    try:
        written = ablation.generate_ablation_tables(
            args.results_root, args.out_dir, rule, patterns=args.pattern,
            families=args.family or ("sst", "datafree"), n_samples=args.n_samples,
        )
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"書き込み: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
