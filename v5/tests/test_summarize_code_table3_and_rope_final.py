"""v5/scripts/summarize_code_table3_and_rope_final.py の単体テスト。"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import summarize_code_table3_and_rope_final as mod  # noqa: E402


def test_mean_std_basic() -> None:
    m, s, n = mod.mean_std([2.44, 5.49, 5.49])
    assert n == 3
    assert abs(m - 4.4733333333) < 1e-4
    assert s > 1.7


def test_build_and_render_final_summaries_contract() -> None:
    data = mod.build_all_summaries()
    assert data["humaneval_eval_lock"]["mbpp_included"] is False
    assert len(data["table3_safety_code"]) == 10
    assert len(data["rope_theta_ablation"]) == 3

    rope_md = mod.render_rope_theta_markdown(data)
    table3_md = mod.render_table3_markdown(data)

    # 確定版に「暫定」が残っていないこと、MBPP 数値列が存在しないこと
    assert "暫定" not in rope_md
    assert "暫定" not in table3_md
    assert "MBPP (" not in rope_md
    assert "MBPP (" not in table3_md
    assert "Code Avg" not in rope_md
    assert "Code Avg" not in table3_md

    # LED-Merging† が全 3 seed でベース単体 2.44% と一致していること
    led = next(r for r in data["table3_safety_code"] if r["key"] == "led_merging")
    assert abs(led["agg"]["humaneval_pass1_pct"]["mean"] - 2.4390243902439024) < 1e-4
    assert abs(led["agg"]["humaneval_pass1_pct"]["std"]) < 1e-6

    # rope_theta TA の HumanEval が 2.44% -> 4.27% であること
    ta = next(r for r in data["rope_theta_ablation"] if r["key"] == "task_arithmetic")
    assert ta["before_rope1e4"]["humaneval"]["n_pass"] == 4
    assert ta["after_rope1e6"]["humaneval"]["n_pass"] == 7
