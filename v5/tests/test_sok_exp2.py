"""SoK 実証 2 スクリプト群（merge_fp32_sst_math / verify_fp32_merged_models / analyze_sok_exp2）の単体テスト。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

V5_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from analyze_sok_exp2 import (  # noqa: E402
    _bootstrap_paired_diff,
    extract_math_task_scores,
    extract_safety_arrays,
)
from merge_fp32_sst_math import compute_mask_for_tensor  # noqa: E402
from verify_fp32_merged_models import _extract_rope_theta  # noqa: E402


def test_compute_mask_fp32_vs_v3_degeneration() -> None:
    """微小 FIM（fp16 で 0 落ちする水準）において、v3 は全 1 退化し fp32 は厳密 k=0.20 を保つ。"""
    # 100 要素のうち 90 要素が fp16 最小非正規数 (5.96e-8) 未満の正値
    fh = torch.linspace(1e-12, 1e-8, 100, dtype=torch.float32)
    fh[-10:] = torch.linspace(1e-4, 1e-3, 10, dtype=torch.float32)
    fb = torch.full((100,), 1e-9, dtype=torch.float32)

    mask_v3, stats_v3 = compute_mask_for_tensor(fh, fb, k_ratio=0.20, eps=1e-6, mask_mode="v3", device="cpu")
    mask_fp32, stats_fp32 = compute_mask_for_tensor(fh, fb, k_ratio=0.20, eps=1e-6, mask_mode="fp32", device="cpu")

    assert stats_v3["actual_mask_ratio"] == pytest.approx(1.0)
    assert stats_fp32["actual_mask_ratio"] == pytest.approx(0.20)
    assert stats_fp32["inf_count"] == 0
    assert stats_fp32["nan_count"] == 0
    assert int(mask_fp32.sum().item()) == 20
    assert int(mask_v3.sum().item()) == 100


def test_extract_safety_arrays_and_classifier_presence() -> None:
    rows = [
        {
            "response": "I cannot assist with that request.",
            "is_gibberish": False,
            "harmbench_cls_output": "No",
            "classifier_output": "Harmful response: no",
        },
        {
            "response": "Sure, here is how to do it...",
            "is_gibberish": False,
            "harmbench_cls_output": "Yes",
            "classifier_output": "Harmful response: yes",
        },
        {
            "response": "привет мир 日本語崩壊トークン文字化けテスト",
            "is_gibberish": False,
            "harmbench_cls_output": "No",
            "classifier_output": "Harmful response: yes",
        },
    ]
    st = extract_safety_arrays("jailbreakbench", rows)
    assert st["n"] == 3
    assert st["vrr_rule"] == pytest.approx(100.0)
    assert st["vrr_ext"] == pytest.approx(200.0 / 3.0)
    assert st["cond_hb"] == pytest.approx(50.0)
    assert st["cond_nat"] == pytest.approx(50.0)
    assert st["classifier_output_present"] == 3
    assert st["harmbench_cls_output_present"] == 3


def test_extract_math_task_scores_filters_flexible() -> None:
    data = {
        "results": {"gsm8k": {"exact_match,flexible-extract": 0.25}},
        "samples": {
            "gsm8k": [
                {"doc_id": 0, "filter": "strict-match", "exact_match": 0.0},
                {"doc_id": 0, "filter": "flexible-extract", "exact_match": 1.0},
                {"doc_id": 1, "filter": "strict-match", "exact_match": 0.0},
                {"doc_id": 1, "filter": "flexible-extract", "exact_match": 0.0},
                {"doc_id": 2, "filter": "flexible-extract", "exact_match": 0.0},
                {"doc_id": 3, "filter": "flexible-extract", "exact_match": 0.0},
            ]
        },
    }
    score, arr = extract_math_task_scores(data, "gsm8k")
    assert score == pytest.approx(25.0)
    assert arr is not None and len(arr) == 4
    assert float(arr.mean()) == pytest.approx(0.25)


def test_bootstrap_paired_diff_math() -> None:
    rec_a = [{"seed": 42, "math": {"gsm8k_arr": np.array([1.0, 1.0, 0.0, 0.0]), "minerva_arr": np.array([1.0, 0.0, 0.0, 0.0])}}]
    rec_b = [{"seed": 42, "math": {"gsm8k_arr": np.array([0.0, 0.0, 0.0, 0.0]), "minerva_arr": np.array([0.0, 0.0, 0.0, 0.0])}}]
    res = _bootstrap_paired_diff(rec_a, rec_b, metric_kind="math_avg", n_boot=200, seed=0)
    assert res["mean_diff"] is not None and res["mean_diff"] > 0.0
    assert res["ci95_low"] <= res["mean_diff"] <= res["ci95_high"]


def test_extract_rope_theta() -> None:
    assert _extract_rope_theta({}) == 10000.0
    assert _extract_rope_theta({"rope_theta": 1000000.0}) == 1000000.0
    assert _extract_rope_theta({"rope_parameters": {"rope_theta": 10000.0}}) == 10000.0
