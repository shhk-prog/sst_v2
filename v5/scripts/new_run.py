#!/usr/bin/env python3
"""指示書 v2 第 1 節準拠の実験フォルダ作成・環境記録・INDEX.md 追記ツール（sst_v2/v5 用）。

使い方:
  CUDA_VISIBLE_DEVICES="" python v5/scripts/new_run.py \
    --name rope-theta-ablation-summary \
    --why "P4 因果切り分けの Before/After 正式比較表を作成する" \
    --what "safety+code (alpha=0.6, seed42) の rope_theta 1e4 vs 1e6 を集計" \
    --paper-use "草稿 6.4 節 (P4)"

仕様:
  - 出力先: v5/results/runs/YYYYMMDD-HHMM_<name>/ (JST、名前は英数字とハイフンのみ)
  - 同分・同名が既にあれば -2, -3... を付けて絶対に上書きしない
  - RUN.md / env.json / config/ / commands.sh / logs/ / outputs/ を作成
  - v5/results/runs/INDEX.md に 1 行追記し、作成したフォルダの絶対パスを標準出力に出す
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO_ROOT = Path(__file__).resolve().parents[2]
V5_ROOT = REPO_ROOT / "v5"
DEFAULT_RUNS_ROOT = V5_ROOT / "results" / "runs"
JST = timezone(timedelta(hours=9))

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")

INDEX_HEADER = """# sst_v2/v5 実験・解析ラン一覧（INDEX）

指示書 v2 第 1 節に準拠した実験フォルダ管理台帳。論文に載せる数値は必ず本台帳で状態が `完了` かつ置き換えられていないフォルダから取得する。

## 新形式（`v5/results/runs/YYYYMMDD-HHMM_<name>/`）

| フォルダ名 | 目的 | 状態 | 論文での使い道 | 備考・置き換え記録 |
|:---|:---|:---:|:---|:---|
"""


def sanitize_run_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-]+", "-", name.strip()).strip("-")
    if not cleaned or not _NAME_RE.match(cleaned):
        raise ValueError(f"実験名は英数字とハイフンのみにしてください: {name!r}")
    return cleaned


def allocate_run_dir(runs_root: Path, name: str, timestamp_jst: str | None = None) -> tuple[Path, str]:
    safe_name = sanitize_run_name(name)
    now_jst = datetime.now(JST)
    ts = timestamp_jst or now_jst.strftime("%Y%m%d-%H%M")
    base = f"{ts}_{safe_name}"
    cand = runs_root / base
    idx = 2
    while cand.exists():
        cand = runs_root / f"{base}-{idx}"
        idx += 1
    return cand, now_jst.strftime("%Y-%m-%d %H:%M JST")


def _run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.DEVNULL, text=True, timeout=15)
        return out.strip()
    except Exception:
        return ""


def collect_env_info(run_dir: Path) -> dict[str, Any]:
    git_commit = _run_cmd(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    git_branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT)
    git_status = _run_cmd(["git", "status", "--short"], cwd=REPO_ROOT)
    has_uncommitted = bool(git_status)
    if has_uncommitted:
        diff_txt = _run_cmd(["git", "diff"], cwd=REPO_ROOT)
        if diff_txt:
            (run_dir / "config" / "uncommitted.diff").write_text(diff_txt + "\n", encoding="utf-8")

    from importlib import metadata as importlib_metadata

    pkgs: dict[str, str] = {}
    for mod in ("torch", "transformers", "vllm", "numpy", "scipy", "matplotlib", "datasets", "safetensors"):
        try:
            pkgs[mod] = importlib_metadata.version(mod)
        except importlib_metadata.PackageNotFoundError:
            pkgs[mod] = "not_installed"
        except Exception:
            pkgs[mod] = "unknown"

    return {
        "recorded_at_jst": datetime.now(JST).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "git": {
            "commit": git_commit or "unknown",
            "branch": git_branch or "unknown",
            "has_uncommitted_changes": has_uncommitted,
            "uncommitted_summary_lines": len(git_status.splitlines()) if git_status else 0,
        },
        "packages": pkgs,
    }


def ensure_index_md(runs_root: Path) -> Path:
    runs_root.mkdir(parents=True, exist_ok=True)
    idx_path = runs_root / "INDEX.md"
    if not idx_path.exists():
        idx_path.write_text(INDEX_HEADER, encoding="utf-8")
    return idx_path


def append_index_row(
    runs_root: Path,
    folder_name: str,
    purpose: str,
    status: str,
    paper_use: str,
    note: str = "",
) -> None:
    idx_path = ensure_index_md(runs_root)
    p_clean = purpose.replace("|", "／").replace("\n", " ").strip()
    u_clean = paper_use.replace("|", "／").replace("\n", " ").strip()
    n_clean = note.replace("|", "／").replace("\n", " ").strip()
    row = f"| `{folder_name}` | {p_clean} | {status} | {u_clean} | {n_clean} |\n"
    text = idx_path.read_text(encoding="utf-8")
    marker = "\n## 旧形式"
    if marker in text:
        head, tail = text.split(marker, 1)
        if not head.endswith("\n"):
            head += "\n"
        idx_path.write_text(head + row + marker + tail, encoding="utf-8")
    else:
        if not text.endswith("\n"):
            text += "\n"
        idx_path.write_text(text + row, encoding="utf-8")


def create_run(
    *,
    runs_root: Path,
    name: str,
    why: str,
    what: str,
    who: str = "Antigravity",
    related: str = "なし",
    expect: str = "",
    paper_use: str = "TBD",
    status: str = "実行中",
    note: str = "",
    timestamp_jst: str | None = None,
    start_str: str | None = None,
    end_str: str = "",
    result_text: str = "（終了後に記入）",
    decision_text: str = "（終了後に記入）",
) -> Path:
    run_dir, now_str = allocate_run_dir(runs_root, name, timestamp_jst=timestamp_jst)
    for sub in ("config", "logs", "outputs"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    start_display = start_str or now_str
    run_md = f"""# {run_dir.name}
- 開始: {start_display} / 終了: {end_str}
- 実行者: {who}
- 関連する実験: {related}

## なぜやるか
{why}

## 何をやるか
{what}

## 予想
{expect or "（実行前に記入）"}

## 結果（終了後に記入）
{result_text}

## 判断と次の一手
{decision_text}
"""
    (run_dir / "RUN.md").write_text(run_md, encoding="utf-8")

    env_info = collect_env_info(run_dir)
    (run_dir / "env.json").write_text(json.dumps(env_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cmd_sh = run_dir / "commands.sh"
    cmd_sh.write_text("#!/usr/bin/env bash\nset -euo pipefail\n", encoding="utf-8")
    cmd_sh.chmod(0o755)

    append_index_row(
        runs_root=runs_root,
        folder_name=run_dir.name,
        purpose=why,
        status=status,
        paper_use=paper_use,
        note=note,
    )
    return run_dir


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="短い実験名（英数字とハイフンのみ）")
    ap.add_argument("--why", required=True, help="なぜやるか（1文〜数文）")
    ap.add_argument("--what", required=True, help="何をやるか")
    ap.add_argument("--who", default="Antigravity")
    ap.add_argument("--related", default="なし")
    ap.add_argument("--expect", default="")
    ap.add_argument("--paper-use", default="TBD")
    ap.add_argument("--status", default="実行中")
    ap.add_argument("--note", default="")
    ap.add_argument("--timestamp", default=None, help="任意の YYYYMMDD-HHMM（省略時は現在 JST）")
    ap.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    args = ap.parse_args()

    run_dir = create_run(
        runs_root=args.runs_root,
        name=args.name,
        why=args.why,
        what=args.what,
        who=args.who,
        related=args.related,
        expect=args.expect,
        paper_use=args.paper_use,
        status=args.status,
        note=args.note,
        timestamp_jst=args.timestamp,
    )
    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
