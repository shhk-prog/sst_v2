"""読み取り専用の入力と、v5/ 配下に限定した書き込み（NFR2）。

入力（v3/results/vllm など）は ``open_readonly`` でだけ開く。
出力は ``safe_write`` / ``write_text`` / ``write_json`` / ``prepare_write_path`` を通し、
書き込み先が書き込み許可ルート（既定は v5/）の外なら例外にする。

テストだけは、環境変数 ``V5_WRITE_ROOT_FOR_TESTS`` で許可ルートを一時フォルダに替えられる。
本番の実行ではこの変数を設定しない。
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

# v5/ のルート（このファイルは v5/src/v5lib/safeio.py にある）
V5_ROOT: Path = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT: Path = V5_ROOT.parent
DEFAULT_OUTPUT_DIR: Path = V5_ROOT / "outputs"
WRITE_ROOT_ENV = "V5_WRITE_ROOT_FOR_TESTS"


class OutsideWriteRootError(PermissionError):
    """書き込み先が許可ルート（v5/）の外にあるときの例外。"""


def write_root() -> Path:
    """現在の書き込み許可ルートを返す（既定は v5/）。"""
    override = os.environ.get(WRITE_ROOT_ENV)
    if override:
        return Path(override).resolve()
    return V5_ROOT.resolve()


def resolve_write_path(path: str | os.PathLike[str]) -> Path:
    """書き込み先を解決し、許可ルートの外なら ``OutsideWriteRootError`` にする。

    シンボリックリンクは解決してから判定する（v5/ 内のリンクで外へ出る書き込みも拒否する）。
    """
    resolved = Path(path).resolve()
    root = write_root()
    if resolved != root and not resolved.is_relative_to(root):
        raise OutsideWriteRootError(
            f"書き込み先が許可ルートの外です: {resolved}（許可ルート: {root}）"
        )
    return resolved


def prepare_write_path(path: str | os.PathLike[str]) -> Path:
    """書き込み先を検証し、親フォルダを作って、解決済みのパスを返す。"""
    resolved = resolve_write_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


@contextlib.contextmanager
def safe_write(
    path: str | os.PathLike[str], mode: str = "w", encoding: str = "utf-8"
) -> Iterator[Any]:
    """v5/ の下だけに書けるファイルを開く。``w`` と ``wb`` だけを許す。"""
    if mode not in ("w", "wb"):
        raise ValueError(f"safe_write は 'w' または 'wb' だけを許します: {mode!r}")
    resolved = prepare_write_path(path)
    if mode == "wb":
        handle = open(resolved, "wb")
    else:
        handle = open(resolved, "w", encoding=encoding, newline="\n")
    try:
        yield handle
    finally:
        handle.close()


def write_text(path: str | os.PathLike[str], text: str) -> Path:
    """テキストを v5/ の下に書く。書いたパスを返す。"""
    with safe_write(path, "w") as handle:
        handle.write(text)
    return Path(path).resolve()


def write_json(path: str | os.PathLike[str], obj: Any) -> Path:
    """JSON を決定的な形（キー順固定、末尾に改行）で書く（NFR1）。"""
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)
    return write_text(path, text + "\n")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"JSON にできない型です: {type(value).__name__}")


def open_readonly(path: str | os.PathLike[str], mode: str = "r", encoding: str = "utf-8"):
    """入力ファイルを読み取り専用で開く。``r`` と ``rb`` 以外は拒否する。"""
    if mode not in ("r", "rb"):
        raise ValueError(f"open_readonly は 'r' または 'rb' だけを許します: {mode!r}")
    if mode == "rb":
        return open(path, "rb")
    return open(path, "r", encoding=encoding)


def read_json(path: str | os.PathLike[str]) -> Any:
    """JSON を読み取り専用で読む。壊れていれば ``ValueError`` を投げる。"""
    try:
        with open_readonly(path) as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON が壊れています: {path}: {exc}") from exc
