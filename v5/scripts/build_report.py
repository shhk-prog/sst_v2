#!/usr/bin/env python3
"""v5/outputs/ の表、図、manifest、仮説の判定を集めて、report.md の「結果の節」を組み立てる（FR6）。

- 冒頭の定義（FR1.1）は、preregistration.md の固定マーカー内を取り込む。
- 数値は、必ず元ファイルのパスつきで書く（NFR3）。
- 考察（FR4）と設計案（FR5）の節は、手書きの範囲（<!-- 手書き: ... 開始/終了 -->）であり、再生成で上書きしない。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/build_report.py
出力: v5/docs/survey_summary/report.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import V5_DIR

from v5lib import report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v5-root", type=Path, default=V5_DIR, help="v5 のフォルダ（既定は、このスクリプトの親）")
    parser.add_argument("--report-path", type=Path, default=None, help="出力先（既定は <v5>/docs/survey_summary/report.md）")
    args = parser.parse_args(argv)
    try:
        path = report.build_report(args.v5_root, args.report_path)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    print(f"書き込み: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
