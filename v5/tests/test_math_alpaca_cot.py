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


def test_parse_alpaca_model_name_and_pareto() -> None:
    from analyze_math_alpaca_cot import compute_pareto_front, parse_alpaca_model_name
    from summarize_rope_theta_ablation import _extract_pass1

    assert parse_alpaca_model_name("fp32_sst_safety+math_alpha0.8_n500_k0.2_seed43") == ("fp32_sst_v5", 0.8, 43)
    assert parse_alpaca_model_name(
        "sst_merge_v3_main_diagonal_sst_main_safety+math_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42"
    ) == ("fp16_sst_v3", 0.6, 42)
    assert parse_alpaca_model_name("sst_merge_v3_main_matena_fisher_safety+math_seed44") == ("matena_fisher_v3", None, 44)
    assert parse_alpaca_model_name("sst_merge_v3_main_task_arithmetic_safety+math_alpha0.4_seed42") == (
        "task_arithmetic_v3",
        0.4,
        42,
    )

    rows = [
        {"method": "a", "alpha": 0.6, "gsm8k_alpaca": {"mean": 50.0}, "cond_hb": {"mean": 5.0}, "vrr_ext": {"mean": 99.0}},
        {"method": "b", "alpha": 0.6, "gsm8k_alpaca": {"mean": 45.0}, "cond_hb": {"mean": 6.0}, "vrr_ext": {"mean": 99.0}},  # dominated by a
        {"method": "c", "alpha": 0.8, "gsm8k_alpaca": {"mean": 40.0}, "cond_hb": {"mean": 0.0}, "vrr_ext": {"mean": 99.0}},  # Pareto (safer)
        {"method": "d", "alpha": 0.6, "gsm8k_alpaca": {"mean": 60.0}, "cond_hb": {"mean": 0.0}, "vrr_ext": {"mean": 50.0}},  # excluded by VRR < 80%
    ]
    assert compute_pareto_front(rows, vrr_min=80.0) == {("a", 0.6), ("c", 0.8)}

    assert _extract_pass1({"results": {"humaneval": {"pass@1,create_test": 0.25}}}, "humaneval") == 25.0
    assert _extract_pass1({"results": {"mbpp": {"pass@1": 12.5}}}, "mbpp") == 12.5
