"""仮説 V1〜V11 の判定ロジック（FR2.1、FR2.3）。

判定の指標と反証条件は、コードに直接書かず、事前登録の
``v5/docs/survey_summary/preregistration.json`` から読む（結果を見てから基準を選ぶことを避ける）。

入力は数値の辞書、出力は「支持」「不支持」「判定不能」のいずれかと、根拠の数値。
このモジュールは torch を使わない（テンソルの計算は ``tensor_checks``）。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

from .safeio import V5_ROOT, open_readonly

VERDICT_SUPPORT = "支持"
VERDICT_REFUTE = "不支持"
VERDICT_UNDETERMINED = "判定不能"
VERDICTS = (VERDICT_SUPPORT, VERDICT_REFUTE, VERDICT_UNDETERMINED)

DEFAULT_PREREGISTRATION_PATH = V5_ROOT / "docs" / "survey_summary" / "preregistration.json"
HYPOTHESIS_IDS = tuple(f"V{i}" for i in range(1, 12))  # V12〜V16 は実装しない（FR2.5）
_OPS = (">=", ">", "<=", "<")


class PreregistrationError(ValueError):
    """事前登録の内容が不正（必須項目の欠け、不正な演算子、基準の重なり）なときの例外。"""


def _interval(cond: dict[str, Any]) -> tuple[float, bool, float, bool]:
    """条件を区間 (下限, 下限を含む, 上限, 上限を含む) にする。"""
    op, value = cond["op"], float(cond["value"])
    if op == ">=":
        return (value, True, math.inf, False)
    if op == ">":
        return (value, False, math.inf, False)
    if op == "<=":
        return (-math.inf, False, value, True)
    return (-math.inf, False, value, False)


def _intervals_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    lo_a, lo_a_closed, hi_a, hi_a_closed = _interval(a)
    lo_b, lo_b_closed, hi_b, hi_b_closed = _interval(b)
    lo, hi = max(lo_a, lo_b), min(hi_a, hi_b)
    if lo < hi:
        return True
    if lo == hi:
        lo_closed = (lo_a_closed if lo_a == lo else True) and (lo_b_closed if lo_b == lo else True)
        hi_closed = (hi_a_closed if hi_a == hi else True) and (hi_b_closed if hi_b == hi else True)
        return lo_closed and hi_closed
    return False


def validate_preregistration(prereg: dict[str, Any]) -> None:
    """V1〜V11 がそろい、各仮説に指標、支持条件、反証条件があり、条件が重ならないことを確かめる。"""
    hyps = prereg.get("hypotheses")
    if not isinstance(hyps, dict):
        raise PreregistrationError("hypotheses がありません")
    for hid in HYPOTHESIS_IDS:
        if hid not in hyps:
            raise PreregistrationError(f"{hid} が事前登録にありません")
        entry = hyps[hid]
        for field in ("metric", "support_if", "refute_if", "statement", "stage"):
            if field not in entry:
                raise PreregistrationError(f"{hid} に {field} がありません")
        for field in ("support_if", "refute_if"):
            cond = entry[field]
            if cond.get("op") not in _OPS or not isinstance(cond.get("value"), (int, float)):
                raise PreregistrationError(f"{hid}.{field} が不正です: {cond}")
        if _intervals_overlap(entry["support_if"], entry["refute_if"]):
            raise PreregistrationError(f"{hid} の支持条件と反証条件が重なっています")
    for hid in hyps:
        if hid not in HYPOTHESIS_IDS:
            raise PreregistrationError(f"対象外の仮説が事前登録にあります: {hid}（V12〜V16 は実装しない）")


def load_preregistration(path: str | Path | None = None) -> dict[str, Any]:
    """事前登録（JSON）を読み、検証して返す。読めない・壊れている場合は例外にする（致命的）。"""
    target = Path(path) if path else DEFAULT_PREREGISTRATION_PATH
    try:
        with open_readonly(target) as handle:
            prereg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PreregistrationError(f"事前登録を読めません: {target}: {exc}") from exc
    validate_preregistration(prereg)
    return prereg


def vrr_floors(prereg: dict[str, Any]) -> tuple[float, list[float]]:
    """(主の下限, 感度分析の下限のリスト) を事前登録から返す。"""
    floor = prereg["comparison"]["vrr_floor"]
    return float(floor["primary"]), [float(v) for v in floor["sensitivity"]]


def neighborhood_tolerance(prereg: dict[str, Any]) -> float:
    """Conditional ASR の近傍比較の許容範囲（pt）。"""
    return float(prereg["comparison"]["neighborhood_tolerance_pt"])


def check_condition(value: float, cond: dict[str, Any]) -> bool:
    """値が条件（``{"op": ">=", "value": 0.1}`` の形）を満たすか。"""
    op, threshold = cond["op"], float(cond["value"])
    if op == ">=":
        return value >= threshold
    if op == ">":
        return value > threshold
    if op == "<=":
        return value <= threshold
    if op == "<":
        return value < threshold
    raise PreregistrationError(f"不正な演算子です: {op!r}")


def judge(
    hypothesis_id: str,
    prereg: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    complete: bool = True,
    missing_inputs: Iterable[str] = (),
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """仮説 1 つを「支持」「不支持」「判定不能」に分類する（FR2.3）。

    判定不能にする条件（事前登録の verdict_rules）:
    必要な入力が無い、実行範囲を絞った（``complete=False``）、指標の値が無い、
    値が支持と反証の基準の間にある。
    戻り値に、使った指標の値、基準、補助の指標（判定には使わない）、実行範囲を添える。
    """
    if hypothesis_id not in prereg["hypotheses"]:
        raise PreregistrationError(f"事前登録に無い仮説です: {hypothesis_id}")
    entry = prereg["hypotheses"][hypothesis_id]
    metrics = metrics or {}
    missing = sorted(set(missing_inputs))
    metric_name = entry["metric"]
    value = metrics.get(metric_name)
    result: dict[str, Any] = {
        "hypothesis": hypothesis_id,
        "title": entry.get("title", ""),
        "metric": metric_name,
        "value": value,
        "support_if": entry["support_if"],
        "refute_if": entry["refute_if"],
        "supplementary": {k: metrics[k] for k in entry.get("supplementary_metrics", []) if k in metrics},
        "scope": scope,
    }

    def undetermined(code: str, reason: str) -> dict[str, Any]:
        return {**result, "verdict": VERDICT_UNDETERMINED, "reason_code": code, "reason": reason}

    if missing:
        return undetermined("data_missing", f"必要な入力が無い: {', '.join(missing)}")
    if not complete:
        return undetermined("scope_restricted", "実行範囲を絞ったため、範囲外を含む判定はしない")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or math.isnan(float(value)):
        return undetermined("data_missing", f"指標 {metric_name} の値が無い")
    supports = check_condition(float(value), entry["support_if"])
    refutes = check_condition(float(value), entry["refute_if"])
    if supports and refutes:  # 事前登録の検証で除いているが、念のため
        return undetermined("criteria_overlap", "支持と反証の基準が重なっている")
    if supports:
        return {**result, "verdict": VERDICT_SUPPORT, "reason_code": "support_met",
                "reason": f"{metric_name}={value} が支持の基準 {entry['support_if']} を満たす"}
    if refutes:
        return {**result, "verdict": VERDICT_REFUTE, "reason_code": "refute_met",
                "reason": f"{metric_name}={value} が反証の基準 {entry['refute_if']} を満たす"}
    return undetermined(
        "between_criteria",
        f"{metric_name}={value} は支持の基準 {entry['support_if']} と反証の基準 {entry['refute_if']} の間にあり、要因を切り分けられない",
    )
