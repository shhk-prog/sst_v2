"""pytest の共通設定。v5/src と v5/scripts を import パスに加える（1 か所だけ）。"""

import sys
from pathlib import Path

import pytest

V5_DIR = Path(__file__).resolve().parents[1]
for sub in ("src", "scripts", "tests"):
    path = str(V5_DIR / sub)
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def write_root(tmp_path, monkeypatch):
    """書き込み許可ルートを一時フォルダに替える（テスト専用の環境変数）。"""
    monkeypatch.setenv("V5_WRITE_ROOT_FOR_TESTS", str(tmp_path))
    return tmp_path
