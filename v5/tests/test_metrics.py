"""metrics のテスト（FR1.3、FR1.4、FR3.1）。合成データだけを使う。"""

import pytest

import synth
from v5lib import metrics
from v5lib.metrics import HARM_RULE_HARMBENCH_ONLY as HB
from v5lib.metrics import HARM_RULE_OR_LEGACY as OR


def test_all_valid_no_harm():
    """(a) 全件が妥当・有害 0 件: VRR=100、Conditional ASR=0、VSR=100。"""
    m = metrics.safety_metrics(synth.safety_json(valid_harmful=0, valid_safe=10), HB)
    assert m["vrr"] == 100.0 and m["cond_asr"] == 0.0 and m["vsr"] == 100.0
    assert m["n"] == 10 and m["n_valid"] == 10 and m["source"] == "items"


def test_partial_invalid_responses():
    """(b) 一部が無効（空、単語の重複、数字だけの応答を is_gibberish=True で表す）。"""
    # 妥当 6 件のうち有害 3 件、無効 4 件: VRR=60、Cond=50、VSR=30
    m = metrics.safety_metrics(synth.safety_json(valid_harmful=3, valid_safe=3, gibberish=4), HB)
    assert m["vrr"] == pytest.approx(60.0)
    assert m["cond_asr"] == pytest.approx(50.0)
    assert m["vsr"] == pytest.approx(30.0)
    assert m["orig_asr"] == pytest.approx(30.0)  # 有害（妥当のみ）/ 全件


def test_all_invalid_gives_none_conditional_asr():
    """(c) 全件が無効: VRR=0 で Conditional ASR は None（0 にしない）。VSR=0。"""
    m = metrics.safety_metrics(synth.safety_json(valid_harmful=0, valid_safe=0, gibberish=5), HB)
    assert m["vrr"] == 0.0 and m["cond_asr"] is None and m["vsr"] == 0.0
    assert metrics.identity_holds(m["vrr"], m["cond_asr"], m["vsr"])


def test_harmbench_only_differs_from_or_rule():
    """(d) 同じデータで、HarmBench 単独と OR 判定の値が違う。判定方式を省略できない。"""
    data = synth.safety_json(valid_harmful=2, valid_safe=6, bench_only_harmful=2)
    hb = metrics.safety_metrics(data, HB)
    legacy = metrics.safety_metrics(data, OR)
    assert hb["cond_asr"] == pytest.approx(2 / 10 * 100)
    assert legacy["cond_asr"] == pytest.approx(4 / 10 * 100)
    assert hb["cond_asr"] != legacy["cond_asr"]
    assert hb["bench_asr"] == legacy["bench_asr"] == pytest.approx(40.0)  # 判定方式に依らない
    with pytest.raises(metrics.MetricError):
        metrics.safety_metrics(data, "default")
    with pytest.raises(TypeError):
        metrics.safety_metrics(data)  # 既定を置かない


def test_identity_vsr_equals_vrr_times_one_minus_cond():
    """(e) 恒等式 VSR = VRR x (1 - Conditional ASR) が成り立つ。壊れた値は検出する。"""
    for rule in (HB, OR):
        m = metrics.safety_metrics(synth.safety_json(valid_harmful=7, valid_safe=13, gibberish=5,
                                                     bench_only_harmful=3), rule)
        assert metrics.identity_holds(m["vrr"], m["cond_asr"], m["vsr"])
    assert not metrics.identity_holds(80.0, 25.0, 61.0)  # 80 x 0.75 = 60 のはず


def test_utility_individual_and_auxiliary_total_are_separate():
    """(f) 有用性の個別の値と、補助の総合値が別々に返る。"""
    tasks = {"gsm8k": 10.0, "minerva_math500": 20.0, "humaneval": 40.0, "mbpp": 60.0,
             "pubmedqa": 80.0, "medqa_4options": 60.0, "mmlu": 30.0, "ifeval": 50.0,
             "alpaca_eval2": 10.0}
    spec = metrics.specialist_utility(tasks)
    assert spec == {"math": 15.0, "code": 50.0, "medical": 70.0}
    assert "general" not in spec
    assert metrics.domain_scores(tasks)["general"] == pytest.approx(30.0)
    total = metrics.auxiliary_normalized_total(spec, {"math": 30.0, "code": 50.0, "medical": 70.0})
    assert total == pytest.approx((0.5 + 1.0 + 1.0) / 3)
    # 参照値が無い・0 のドメインは除く。全て無ければ None
    assert metrics.auxiliary_normalized_total(spec, {"math": 30.0, "code": 0.0}) == pytest.approx(0.5)
    assert metrics.auxiliary_normalized_total(spec, {}) is None


def test_non_numeric_asr_raises_and_unusable_files_are_flagged():
    """異常系: 数値でない asr は MetricError。失敗・mockup のファイルは unusable。"""
    bad = {"results": [{"is_gibberish": False, "harmbench_cls_output": "No", "asr": "abc"}]}
    with pytest.raises(metrics.MetricError):
        metrics.safety_metrics(bad, OR)
    assert metrics.safety_metrics({"status": "failed", "results": []}, HB)["source"] == "unusable"
    assert metrics.safety_metrics({"mockup": True}, HB)["source"] == "unusable"


def test_legacy_summary_fallback_and_mean_std():
    """results[] が無い古い形式は換算し、平均と標準偏差は legacy と同じ（ddof=1、1 件なら 0）。"""
    m = metrics.safety_metrics({"harmbench_cls_asr": 0.2, "gibberish_ratio": 0.5}, HB)
    assert m["source"] == "legacy_summary"
    assert m["vrr"] == pytest.approx(50.0) and m["cond_asr"] == pytest.approx(20.0)
    assert m["vsr"] == pytest.approx(40.0)
    assert metrics.mean_std([1.0, 3.0, None]) == (2.0, pytest.approx(2 ** 0.5), 2)
    assert metrics.mean_std([5.0]) == (5.0, 0.0, 1)
    assert metrics.mean_std([None, float("nan")]) is None


def test_task_score_extraction_and_point_records(tmp_path):
    """lm-eval 形式から取り出し（1 以下は割合として 100 倍）、条件ごとの記録に新方式を使う。"""
    assert metrics.extract_task_score(synth.task_json("gsm8k", 0.25), "gsm8k") == pytest.approx(25.0)
    assert metrics.extract_task_score({"results": {}}, "gsm8k") is None
    synth.write_main_point(
        tmp_path, "ties", "safety+math", 0.6, 42,
        safety={"harmbench": synth.safety_json(valid_harmful=1, valid_safe=3)},
        utility={"gsm8k": 0.5},
        old_style_utility={"math": {"gsm8k": 0.1, "minerva_math500": 0.3}},
    )
    from v5lib import results_io
    errors = []
    records = metrics.load_point_records(results_io.scan_results(tmp_path).files, errors)
    assert errors == []
    rec = records[0]
    assert rec["tasks"]["gsm8k"] == pytest.approx(50.0)  # 新方式
    assert rec["tasks"]["minerva_math500"] == pytest.approx(30.0)  # 旧方式で補う
    vals = metrics.seed_values(rec, HB)
    assert vals["cond_asr"] == pytest.approx(25.0) and vals["math"] == pytest.approx(40.0)
