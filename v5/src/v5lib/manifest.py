"""出力ごとの manifest（FR3.4、NFR3）。

表や図と同名の ``<出力>.manifest.json`` に、使った結果ファイルの一覧、データ件数、欠損、設定値を残す。
NFR1（同じ入力から同じ出力）のため、時刻などの実行ごとに変わる値は入れない。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from .safeio import resolve_write_path, write_json, write_root

MANIFEST_VERSION = 1


def manifest_path_for(output_path: str | os.PathLike[str]) -> Path:
    """出力ファイルに対応する manifest のパス（``<出力>.manifest.json``）。"""
    output = Path(output_path)
    return output.with_name(output.name + ".manifest.json")


def _relative_to_root(path: Path) -> str:
    resolved = path.resolve()
    root = write_root()
    if resolved.is_relative_to(root):
        return resolved.relative_to(root).as_posix()
    return resolved.as_posix()


def write_manifest(
    output_path: str | os.PathLike[str],
    *,
    script: str,
    inputs: Iterable[str],
    counts: dict[str, Any],
    missing: list[Any],
    settings: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> Path:
    """manifest を書く。入力パスは辞書順に並べ、同じ入力なら同じ内容になる。"""
    resolve_write_path(output_path)  # 書き込み許可ルートの外を拒否する
    input_list = sorted(set(str(p) for p in inputs))
    payload: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "output": _relative_to_root(Path(output_path)),
        "script": script,
        "n_input_files": len(input_list),
        "input_files": input_list,
        "counts": counts,
        "missing": missing,
        "settings": settings,
    }
    if extra:
        payload["extra"] = extra
    return write_json(manifest_path_for(output_path), payload)
