"""v5/scripts の共通部分: import パス、既定のパス、事前登録の読み込み。

スクリプトは、ワークスペース直下（``/mnt/nas/home/hiromi/src/sst_v2``）から
``venv_sst/bin/python v5/scripts/<name>.py`` で実行する。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GPU を見えなくする（NFR4）。torch を import する前に設定する
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

V5_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = V5_DIR.parent
_SRC = str(V5_DIR / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

DEFAULT_RESULTS_ROOT = WORKSPACE / "v3" / "results" / "vllm" / "debug_limit320"
DEFAULT_PAPER_TEX = (
    WORKSPACE / "v3" / "論文" / "FLMSEC" / "Formatting_Instructions_For_NeurIPS_2026" / "appendix.tex"
)
DEFAULT_V3 = WORKSPACE / "v3"
DEFAULT_OUT = V5_DIR / "outputs"


def load_prereg():
    """事前登録（preregistration.json）を読む。VRR の下限などは、ここから取る（コードに書かない）。"""
    from v5lib.hypotheses import load_preregistration

    return load_preregistration()
