"""compare のテスト（FR1.2、FR1.5）。"""

import pytest

from v5lib import compare
from v5lib.compare import Point


def pt(method, alpha, vrr, cond, util, std=0.0, pattern="safety+math", ustd=0.0):
    return Point(method=method, pattern=pattern, alpha=alpha, vrr=vrr, cond_asr=cond,
                 cond_asr_std=std, util={"math": (util, ustd)}, n_seeds=3)


def test_vrr_floor_filters_with_boundary_and_sensitivity():
    """(a) 79.9 は落ち、80.0 は残る。感度分析の 3 値で結果が変わる。"""
    pts = [pt("a", 0.2, 79.9, 10, 5), pt("b", 0.2, 80.0, 10, 5), pt("c", 0.2, 90.0, 10, 5),
           pt("d", 0.2, 50.0, 10, 5)]
    kept80, excl80 = compare.filter_by_vrr(pts, 80.0)
    assert sorted(p.method for p in kept80) == ["b", "c"]
    assert {e["method"] for e in excl80} == {"a", "d"} and "下限 80" in excl80[0]["reason"]
    assert sorted(p.method for p in compare.filter_by_vrr(pts, 90.0)[0]) == ["c"]
    # 50 の下限では 79.9（a）も、50.0（d）も残る
    assert {p.method for p in compare.filter_by_vrr(pts, 50.0)[0]} == {"a", "b", "c", "d"}
    with pytest.raises(TypeError):
        compare.filter_by_vrr(pts)  # 下限の既定を置かない


def test_strict_pareto_dominance_ties_and_nondominated():
    """(b) 厳密な Pareto 支配: 支配される点、同点、非支配の点。"""
    best = pt("best", 0.6, 100, 5.0, 50.0)
    worse = pt("worse", 0.6, 100, 10.0, 40.0)           # 両方で劣る -> 支配される
    same_cond_lower_util = pt("tie_c", 0.6, 100, 5.0, 45.0)  # ASR 同じで有用性が低い -> 支配される
    tradeoff = pt("tradeoff", 0.6, 100, 1.0, 20.0)       # ASR は良いが有用性が低い -> 非支配
    twin1 = pt("twin1", 0.2, 100, 3.0, 30.0)
    twin2 = pt("twin2", 0.2, 100, 3.0, 30.0)             # 同じ値どうし -> 互いに支配しない
    assert compare.dominates(best, worse, "math")
    assert compare.dominates(best, same_cond_lower_util, "math")
    assert not compare.dominates(best, tradeoff, "math") and not compare.dominates(tradeoff, best, "math")
    assert not compare.dominates(twin1, twin2, "math") and not compare.dominates(twin2, twin1, "math")
    res = compare.pareto_analysis([best, worse, same_cond_lower_util, tradeoff, twin1, twin2], "math")
    assert "worse@0.6" in res["dominated"] and "best@0.6" in res["dominated"]["worse@0.6"]
    # best(ASR5, 50) は twin(ASR3, 30) を支配しない（ASR が高い）。twin も best を支配しない（有用性が低い）
    assert not compare.dominates(best, twin1, "math") and not compare.dominates(twin1, best, "math")
    # 前線は、支配されない 4 点（同点の twin は両方残る）
    assert set(res["front"]) == {"best@0.6", "tradeoff@0.6", "twin1@0.2", "twin2@0.2"}
    assert set(res["dominated"]) == {"worse@0.6", "tie_c@0.6"}


def test_neighborhood_boundary_two_points():
    """(c) 近傍比較の境界: 差が 2.0 pt ちょうどは含み、2.01 は含まない。同じ手法どうしは比べない。"""
    a = pt("a", 0.6, 100, 10.0, 50.0, ustd=1.0)
    b_in = pt("b", 0.6, 100, 12.0, 40.0, ustd=1.0)
    b_out = pt("c", 0.6, 100, 12.01, 40.0)
    same_method = pt("a", 0.8, 100, 10.5, 30.0)
    pairs = compare.neighborhood_comparisons([a, b_in], "math", 2.0)
    assert [(p["a"], p["b"]) for p in pairs] == [("a@0.6", "b@0.6")]
    assert compare.neighborhood_comparisons([a, b_out], "math", 2.0) == []  # 2.01 pt は含まない
    assert compare.neighborhood_comparisons([a, same_method], "math", 2.0) == []
    pair = pairs[0]
    assert pair["util_diff"] == pytest.approx(10.0)
    assert pair["higher_utility"] == "a@0.6"
    assert pair["uncertain"] is False  # 差 10 > 合成標準偏差 約 1.41
    close = compare.neighborhood_comparisons([pt("a", 0.6, 100, 10.0, 50.0, ustd=3.0),
                                              pt("b", 0.6, 100, 10.0, 49.0, ustd=3.0)], "math", 2.0)
    assert close[0]["uncertain"] is True  # 差 1 < 合成標準偏差 約 4.24


def test_single_point_and_no_comparison_possible():
    """(d) 点が 1 つだけのとき: その点が前線に残り、近傍比較は空。"""
    only = pt("only", 0.6, 100, 5.0, 10.0)
    res = compare.pareto_analysis([only], "math")
    assert res["front"] == ["only@0.6"] and res["dominated"] == {}
    assert compare.neighborhood_comparisons([only], "math", 2.0) == []


def test_all_points_excluded_returns_empty_result_not_exception():
    """(e) 全点が除外されたとき: 空の結果を返し、例外にしない。"""
    pts = [pt("a", 0.2, 10.0, 5.0, 10.0), pt("b", 0.4, 20.0, 5.0, 10.0)]
    kept, excluded = compare.filter_by_vrr(pts, 80.0)
    assert kept == [] and len(excluded) == 2
    summary = compare.summarize_observations(pts, 80.0, 2.0)
    pat = summary["safety+math"]
    assert pat["n_kept"] == 0 and len(pat["excluded"]) == 2
    assert pat["domains"]["math"]["pareto"]["front"] == []
    assert pat["domains"]["math"]["neighborhoods"] == []


def test_missing_values_are_excluded_or_skipped():
    """値が欠けた点: VRR なし・Conditional ASR なしは除外、有用性なしは Pareto 比較から外す。"""
    no_cond = pt("n", 0.6, 100.0, None, 10.0)
    no_vrr = pt("v", 0.6, None, 5.0, 10.0)
    no_util = Point(method="u", pattern="safety+math", alpha=0.6, vrr=100.0, cond_asr=5.0,
                    cond_asr_std=0.0, util={"math": None}, n_seeds=1)
    kept, excluded = compare.filter_by_vrr([no_cond, no_vrr, no_util], 80.0)
    assert [p.method for p in kept] == ["u"] and len(excluded) == 2
    assert compare.pareto_analysis(kept, "math")["skipped"] == ["u@0.6"]
