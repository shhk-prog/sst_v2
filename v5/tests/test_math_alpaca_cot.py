"""WizardMath 公式 Alpaca-CoT GSM8K 評価スクリプトの単体テスト。"""

from __future__ import annotations

import sys
from pathlib import Path

V5_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V5_ROOT / "scripts"))

from eval_math_alpaca_cot import ALPACA_COT_TEMPLATE, extract_pred_number, extract_target_number, numbers_equal  # noqa: E402


def test_alpaca_cot_template_contains_trigger() -> None:
    prompt = ALPACA_COT_TEMPLATE.format(question="What is 2+2?")
    assert "Below is an instruction that describes a task." in prompt
    assert "### Response: Let's think step by step." in prompt
    assert "Question:" not in prompt
    assert "Answer:" not in prompt


def test_extract_pred_and_target_numbers() -> None:
    assert extract_target_number("16 - 3 - 4 = 9\n9 * 2 = 18\n#### 18") == "18"
    assert extract_pred_number("First 16-3-4=9. Then 9*2=18.\nThe answer is: 18.") == "18"
    assert extract_pred_number("Step 1: 80,000 + 50,000 = 130,000.\nThe final answer is $70,000") == "70000"
    assert extract_pred_number("Therefore \\boxed{540}.") == "540"
    assert extract_pred_number("#### 3.5") == "3.5"
    assert numbers_equal("18.0", "18") is True
    assert numbers_equal("70000", "70000") is True
    assert numbers_equal("12", "18") is False
