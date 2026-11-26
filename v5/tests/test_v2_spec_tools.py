"""指示書 v2 対応ツール群（new_run / 補間 / WizardCoder 抽出・ゲート / LED-Merging 統計）の単体テスト。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

V5_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V5_ROOT / "scripts"))

from analyze_math_alpaca_cot import compute_pareto_front, interpolate_utility_at_asr  # noqa: E402
from audit_led_merging_weights import _finalize_acc, _new_acc  # noqa: E402
from eval_code_wizardcoder_official import evaluate_gate, extract_python_solution  # noqa: E402
from new_run import create_run  # noqa: E402


def test_new_run_no_overwrite_and_index(tmp_path: Path) -> None:
    d1 = create_run(
        runs_root=tmp_path,
        name="demo-exp",
        why="test why 1",
        what="test what 1",
        timestamp_jst="20261126-1400",
    )
    d2 = create_run(
        runs_root=tmp_path,
        name="demo-exp",
        why="test why 2",
        what="test what 2",
        timestamp_jst="20261126-1400",
    )
    assert d1.name == "20261126-1400_demo-exp"
    assert d2.name == "20261126-1400_demo-exp-2"
    assert (d1 / "RUN.md").is_file()
    assert (d1 / "env.json").is_file()
    assert (d1 / "commands.sh").is_file()
    idx = (tmp_path / "INDEX.md").read_text(encoding="utf-8")
    assert "20261126-1400_demo-exp" in idx
    assert "20261126-1400_demo-exp-2" in idx


def test_interpolate_utility_at_asr() -> None:
    pts = [(30.0, 52.0), (15.0, 48.0), (5.0, 40.0)]
    # 15%〜5% の中点 10% -> 44.0
    assert interpolate_utility_at_asr(pts, 10.0) == pytest.approx(44.0)
    # 0% には到達しない -> None
    assert interpolate_utility_at_asr(pts, 0.0) is None
    # 単発点（ASR=4%, U=40%）は target=5% 以下なので 40.0
    assert interpolate_utility_at_asr([(4.0, 40.0)], 5.0) == pytest.approx(40.0)
    assert interpolate_utility_at_asr([(4.0, 40.0)], 3.0) is None


def test_pareto_vrr_90_threshold() -> None:
    rows = [
        {"method": "ok", "alpha": 0.6, "gsm8k_alpaca": {"mean": 50.0}, "cond_hb": {"mean": 5.0}, "vrr_ext": {"mean": 92.0}},
        {"method": "low_vrr", "alpha": 0.6, "gsm8k_alpaca": {"mean": 55.0}, "cond_hb": {"mean": 1.0}, "vrr_ext": {"mean": 85.0}},
    ]
    assert compute_pareto_front(rows, vrr_min=90.0, asr_key="cond_hb") == {("ok", 0.6)}


def test_wizardcoder_extract_and_gate() -> None:
    prompt = "from typing import List\n\ndef add_one(xs: List[int]) -> List[int]:\n    \"\"\"Add 1.\"\"\"\n"
    raw = "Here is the code:\n```python\ndef add_one(xs: List[int]) -> List[int]:\n    return [x + 1 for x in xs]\n```\n"
    code, mode = extract_python_solution(raw, prompt, "add_one")
    assert mode == "code_fence"
    assert code is not None
    assert "from typing import List" in code
    assert code.count("def add_one") == 1

    g_pass = evaluate_gate(
        model_name="wc",
        pass1_pct=53.0,
        extraction_fail_pct=1.2,
        mode_skew_pct=0.6,
        official_value=55.5,
        base_pass1_pct=12.0,
    )
    assert g_pass["all_auto_checks_pass"] is True

    g_fail = evaluate_gate(
        model_name="wc_broken",
        pass1_pct=5.49,
        extraction_fail_pct=1.2,
        mode_skew_pct=0.6,
        official_value=55.5,
        base_pass1_pct=12.0,
    )
    assert g_fail["all_auto_checks_pass"] is False


def test_led_audit_finalize_math() -> None:
    acc = _new_acc()
    acc["n_elem"] = 100
    acc["n_eq_base"] = 99
    acc["norm_b2"] = 100.0
    acc["norm_u2"] = 100.0
    acc["norm_s2"] = 100.0
    acc["norm_dm2"] = 0.0025
    acc["norm_du2"] = 4.0
    acc["norm_ds2"] = 1.0
    acc["dot_dm_du"] = 0.04
    acc["dot_dm_ds"] = 0.0
    out = _finalize_acc(acc)
    assert out["rel_diff_vs_base_pct"] == pytest.approx(0.5)
    assert out["proj_util_pct"] == pytest.approx(1.0)
