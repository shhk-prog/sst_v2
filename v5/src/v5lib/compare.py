"""比較ロジック層（FR1.2、FR1.5、FR4.1）: Validity-constrained Pareto 比較。

- 点は (手法, パターン, α)。seed 平均と標準偏差を持つ。
- VRR の下限でふるい、除外した点を理由つきで返す（下限は引数で受け、既定を置かない）。
- 優劣は、観測済みの点どうしの厳密な Pareto 支配で判定する。補間はしない（FR1.5）。
- 補助として、Conditional ASR の差が許容範囲（pt）以内の点どうしを近傍比較する。
- ここでは「観測事実」だけをまとめる。機構仮説と示唆は作らない（FR5.1 の 1 段階目だけ）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from .metrics import group_main_points, summarize_point
from .results_io import METHOD_DISPLAY, PATTERN_DOMAINS

# 浮動小数点の誤差で境界（ちょうど 2.0 pt など）が揺れないようにする余裕
_EPS = 1e-9


@dataclass(frozen=True)
class Point:
    """比較の 1 点（手法, パターン, α）。値は百分率、std は seed 間の標準偏差。"""

    method: str
    pattern: str
    alpha: float | None
    vrr: float | None
    cond_asr: float | None
    cond_asr_std: float
    util: dict[str, tuple[float, float] | None] = field(default_factory=dict, compare=False, hash=False)
    n_seeds: int = 0

    @property
    def label(self) -> str:
        a = "N/A" if self.alpha is None else f"{self.alpha:g}"
        return f"{self.method}@{a}"

    @property
    def key(self) -> tuple[str, str, float | None]:
        return (self.method, self.pattern, self.alpha)

    def util_mean(self, domain: str) -> float | None:
        value = self.util.get(domain)
        return None if value is None else value[0]

    def util_std(self, domain: str) -> float:
        value = self.util.get(domain)
        return 0.0 if value is None else value[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "method": self.method,
            "pattern": self.pattern,
            "alpha": self.alpha,
            "vrr": self.vrr,
            "cond_asr": self.cond_asr,
            "cond_asr_std": self.cond_asr_std,
            "util": {d: (None if v is None else {"mean": v[0], "std": v[1]}) for d, v in self.util.items()},
            "n_seeds": self.n_seeds,
        }


def points_from_records(records: Iterable[dict[str, Any]], rule: str, kind: str = "main") -> list[Point]:
    """条件ごとの記録（``metrics.load_point_records``）から、比較の点を作る。

    ``rule`` は有害判定の方式（必ず明示）。手法名は表示名（sst、data_free_sst）にそろえる。
    """
    points: list[Point] = []
    grouped = group_main_points(records, kind=kind)
    for (method, pattern, alpha), recs in sorted(grouped.items(), key=lambda kv: (str(kv[0][1]), str(kv[0][0]), -1 if kv[0][2] is None else kv[0][2])):
        summary = summarize_point(recs, rule)
        vrr = summary["vrr"]
        cond = summary["cond_asr"]
        points.append(
            Point(
                method=METHOD_DISPLAY.get(method, method),
                pattern=pattern,
                alpha=alpha,
                vrr=None if vrr is None else vrr[0],
                cond_asr=None if cond is None else cond[0],
                cond_asr_std=0.0 if cond is None else cond[1],
                util={d: summary[d] and (summary[d][0], summary[d][1]) for d in ("math", "code", "medical", "general")},
                n_seeds=len(recs),
            )
        )
    return points


def filter_by_vrr(points: Iterable[Point], vrr_floor: float) -> tuple[list[Point], list[dict[str, Any]]]:
    """VRR（百分率）が ``vrr_floor`` 以上の点を残し、除外した点を理由つきで返す（FR1.2）。

    ``vrr_floor`` は必須の引数（既定を置かない。値は preregistration.json から渡す）。
    VRR が無い点は除外する。残す条件は ``vrr >= vrr_floor``（80.0 は残り、79.9 は落ちる）。
    Conditional ASR が無い点（比較できない）も除外する。
    """
    kept: list[Point] = []
    excluded: list[dict[str, Any]] = []
    for point in points:
        base = {"label": point.label, "method": point.method, "pattern": point.pattern, "alpha": point.alpha,
                "vrr": point.vrr}
        if point.vrr is None:
            excluded.append({**base, "reason": "VRR が無い"})
        elif point.vrr < vrr_floor:
            excluded.append({**base, "reason": f"VRR {point.vrr:.2f} < 下限 {vrr_floor:g}"})
        elif point.cond_asr is None:
            excluded.append({**base, "reason": "Conditional ASR が無い"})
        else:
            kept.append(point)
    return kept, excluded


def dominates(a: Point, b: Point, domain: str) -> bool:
    """``a`` が ``b`` を厳密に支配するか。

    Conditional ASR は低いほど良く、有用性は高いほど良い。両方で同等以上、少なくとも一方で厳密に良ければ支配。
    同じ点どうし（両方が同じ値）は、どちらも支配しない。どちらかの値が無ければ支配しない。
    """
    if a.cond_asr is None or b.cond_asr is None:
        return False
    ua, ub = a.util_mean(domain), b.util_mean(domain)
    if ua is None or ub is None:
        return False
    no_worse = a.cond_asr <= b.cond_asr and ua >= ub
    strictly_better = a.cond_asr < b.cond_asr or ua > ub
    return no_worse and strictly_better


def pareto_analysis(points: Iterable[Point], domain: str) -> dict[str, Any]:
    """観測済みの点の厳密な Pareto 支配関係（補間なし）。

    戻り値: ``front``（支配されない点のラベル）、``dominated``（点 -> それを支配する点のラベル）、
    ``skipped``（このドメインの値が無く比較できなかった点）。
    """
    usable = [p for p in points if p.cond_asr is not None and p.util_mean(domain) is not None]
    skipped = sorted(p.label for p in points if p not in usable)
    dominated: dict[str, list[str]] = {}
    for p in usable:
        dominators = sorted(q.label for q in usable if q is not p and dominates(q, p, domain))
        if dominators:
            dominated[p.label] = dominators
    front = sorted(p.label for p in usable if p.label not in dominated)
    return {"front": front, "dominated": dominated, "skipped": skipped, "n_points": len(usable)}


def neighborhood_comparisons(points: Iterable[Point], domain: str, tol_pt: float) -> list[dict[str, Any]]:
    """Conditional ASR の差が ``tol_pt`` 以内（境界を含む）の、異なる手法の点どうしを比べる（補助）。

    各組について、有用性の差（a - b）と、不確実性（差の絶対値が、両者の seed 間標準偏差の合成
    sqrt(sa^2 + sb^2) より小さいか）を返す。補間はしない。
    """
    usable = sorted(
        (p for p in points if p.cond_asr is not None and p.util_mean(domain) is not None),
        key=lambda p: (p.method, -1 if p.alpha is None else p.alpha),
    )
    pairs: list[dict[str, Any]] = []
    for i, a in enumerate(usable):
        for b in usable[i + 1 :]:
            if a.method == b.method:
                continue
            cond_diff = a.cond_asr - b.cond_asr
            if abs(cond_diff) > tol_pt + _EPS:
                continue
            util_diff = a.util_mean(domain) - b.util_mean(domain)
            pooled = math.sqrt(a.util_std(domain) ** 2 + b.util_std(domain) ** 2)
            pairs.append(
                {
                    "a": a.label,
                    "b": b.label,
                    "cond_asr_diff": cond_diff,
                    "util_diff": util_diff,
                    "util_std_pooled": pooled,
                    "uncertain": abs(util_diff) < pooled,
                    "higher_utility": a.label if util_diff > 0 else (b.label if util_diff < 0 else "tie"),
                }
            )
    return pairs


def summarize_observations(
    points: Iterable[Point], vrr_floor: float, tol_pt: float
) -> dict[str, Any]:
    """各パターン・各ドメインの「観測事実」をまとめる（機構仮説と示唆は作らない）。

    パターンごとに、VRR の下限で除外した点の一覧と、残った点に対する Pareto 支配・近傍比較を、
    パターンに対応するドメインごと（FR1.4: 個別）に返す。
    """
    by_pattern: dict[str, list[Point]] = {}
    for point in points:
        by_pattern.setdefault(point.pattern, []).append(point)
    summary: dict[str, Any] = {}
    for pattern in sorted(by_pattern):
        kept, excluded = filter_by_vrr(by_pattern[pattern], vrr_floor)
        domains: dict[str, Any] = {}
        for domain in PATTERN_DOMAINS.get(pattern, ["math", "code", "medical"]):
            domains[domain] = {
                "pareto": pareto_analysis(kept, domain),
                "neighborhoods": neighborhood_comparisons(kept, domain, tol_pt),
            }
        summary[pattern] = {
            "vrr_floor": vrr_floor,
            "n_points": len(by_pattern[pattern]),
            "n_kept": len(kept),
            "excluded": excluded,
            "domains": domains,
        }
    return summary
