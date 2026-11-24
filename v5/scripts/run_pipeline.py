#!/usr/bin/env python3
"""v5 の実行の入口。段階ごとのコマンドを組み立てて表示する（--dry-run、既定）か、指定した段階だけを実行する。

段階（実行の順序。事前登録の execution_order と同じ）:
  inputs   入力の有無と大きさの確認（check_inputs.py）
  v1_v9    V1〜V9 の CPU 検証（check_v1_v9.py）
  v10_v11  V10〜V11 の再集計（check_v10_v11.py）
  tables   FLMSEC の表の再生成と照合（regen_flmsec_tables.py）
  plots    safety-utility 曲線（plot_pareto_curves.py）
  ablation アブレーション表（ablation_table.py）

--execute は、--approved-by-user が無いと拒否する。実行の前に、依頼者へコマンドを示して許可を得る
約束（FR2.4）を、スクリプトの側でも確認するため。実行の記録（コマンド、開始と終了の時刻、終了コード）は
v5/outputs/logs/ に残す。GPU は使わない（子プロセスには CUDA_VISIBLE_DEVICES="" を渡す）。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/run_pipeline.py                      # --dry-run（既定）
    venv_sst/bin/python v5/scripts/run_pipeline.py --execute --stages inputs --approved-by-user
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, V5_DIR, WORKSPACE

from v5lib import safeio

STAGES = ["inputs", "v1_v9", "v10_v11", "tables", "plots", "ablation"]
SCRIPT_FOR_STAGE = {
    "inputs": "check_inputs.py",
    "v1_v9": "check_v1_v9.py",
    "v10_v11": "check_v10_v11.py",
    "tables": "regen_flmsec_tables.py",
    "plots": "plot_pareto_curves.py",
    "ablation": "ablation_table.py",
}
PYTHON_DISPLAY = "venv_sst/bin/python"


def build_commands(stages: list[str], extra_args: dict[str, list[str]] | None = None, python: str = PYTHON_DISPLAY) -> list[dict]:
    """段階ごとのコマンド（引数のリスト）を、事前登録の順序で組み立てる。"""
    extra_args = extra_args or {}
    commands = []
    for stage in STAGES:
        if stage not in stages:
            continue
        script = f"v5/scripts/{SCRIPT_FOR_STAGE[stage]}"
        commands.append({"stage": stage, "argv": [python, script, *extra_args.get(stage, [])]})
    return commands


def validate_stages(text: str) -> list[str]:
    """``--stages`` を読む。未知の段階は ``ValueError``。"""
    stages = [s.strip() for s in text.split(",") if s.strip()]
    unknown = [s for s in stages if s not in STAGES]
    if unknown or not stages:
        raise ValueError(f"未知の段階です: {unknown or text!r}（{STAGES} から選ぶ）")
    return stages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stages", default=",".join(STAGES), help="対象の段階（カンマ区切り）。既定は全段階")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="コマンドを表示するだけ（既定）")
    mode.add_argument("--execute", action="store_true", help="指定した段階を実行する（--approved-by-user が必要）")
    parser.add_argument("--approved-by-user", action="store_true", help="依頼者が、このコマンドの実行を許可した（FR2.4）")
    parser.add_argument("--v1-v9-args", default="", help="v1_v9 段階に渡す引数（例: \"--seed 42 --pattern safety+math --max-tensors 8\"）")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_OUT / "logs", help="実行の記録の出力先（v5/ の下だけ）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        stages = validate_stages(args.stages)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    extra: dict[str, list[str]] = {}
    if args.v1_v9_args:
        extra["v1_v9"] = shlex.split(args.v1_v9_args)
    commands = build_commands(stages, extra)

    if not args.execute:  # --dry-run（既定）: 何も書かず、何も実行しない
        print("--dry-run: 次のコマンドを実行する予定です（何も実行していません）")
        for cmd in commands:
            print(f"  [{cmd['stage']}] {shlex.join(cmd['argv'])}")
        return 0

    if not args.approved_by_user:
        print("依頼者の許可（--approved-by-user）がないため実行しません。--dry-run のコマンドを依頼者に示し、許可を得てください。", file=sys.stderr)
        return 3

    env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}
    for cmd in commands:
        argv = list(cmd["argv"])
        run_argv = [sys.executable, *argv[1:]]
        if cmd["stage"] == "v1_v9":
            run_argv.append("--approved-by-user")  # 許可は上で確認済み
        started = dt.datetime.now(dt.timezone.utc)
        print(f"[{cmd['stage']}] 実行: {shlex.join(argv)}")
        proc = subprocess.run(run_argv, cwd=str(WORKSPACE), env=env)
        finished = dt.datetime.now(dt.timezone.utc)
        record = {
            "stage": cmd["stage"],
            "command": shlex.join(run_argv),
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "return_code": proc.returncode,
        }
        stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
        try:
            safeio.write_json(args.log_dir / f"{stamp}_{cmd['stage']}.json", record)
        except PermissionError as exc:
            print(f"実行の記録を書けません: {exc}", file=sys.stderr)
            return 1
        if proc.returncode != 0:
            print(f"[{cmd['stage']}] 失敗（終了コード {proc.returncode}）。以降の段階は実行しません。", file=sys.stderr)
            return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
