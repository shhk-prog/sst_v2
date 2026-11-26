"""v5/scripts/eval_math_alpaca_cot_batched.py の単体テスト。

ロック済み eval_math_alpaca_cot.py の SHA256 が不変であり、
プロンプト・STOP・抽出関数が同一オブジェクトであることを検証する。
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_batched_wrapper_matches_locked_eval_script() -> None:
    import eval_math_alpaca_cot as locked
    import eval_math_alpaca_cot_batched as batched

    sha = batched.verify_locked_script_sha256()
    assert sha == batched.EXPECTED_LOCKED_SHA256
    assert batched.locked_eval is locked
    assert batched.locked_eval.ALPACA_COT_TEMPLATE == locked.ALPACA_COT_TEMPLATE
    assert batched.locked_eval.STOP_TOKENS == locked.STOP_TOKENS
    assert batched.locked_eval.extract_pred_number is locked.extract_pred_number
    assert batched.locked_eval.extract_target_number is locked.extract_target_number
    assert batched.locked_eval.numbers_equal is locked.numbers_equal
