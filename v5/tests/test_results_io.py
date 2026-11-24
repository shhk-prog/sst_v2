"""results_io と safeio のテスト（FR3.4、NFR2、NFR3）。合成データだけを使う。"""

import pytest

import synth
from v5lib import results_io, safeio


def test_parse_main_and_single_method_names():
    """(a) 主実験（SST、α あり）と α なしの単発手法のファイル名を解析できる。"""
    sst = results_io.parse_result_name(
        synth.main_name("diagonal_sst_main", "safety+math+code+medical", 0.6, 43, "harmbench_safety")
    )
    assert (sst.kind, sst.method, sst.pattern, sst.alpha, sst.seed) == (
        "main", "diagonal_sst_main", "safety+math+code+medical", 0.6, 43)
    assert sst.family == "safety" and sst.bench == "harmbench"
    assert sst.cfg is not None and sst.cfg.k == 0.2 and sst.cfg.n == 500 and sst.cfg.ratio == "FhFb"

    single = results_io.parse_result_name(
        synth.main_name("safemerge", "safety+code", None, 42, "utility_code_humaneval"))
    assert single.alpha is None and single.method == "safemerge"
    assert (single.family, single.task, single.style) == ("utility", "humaneval", "new")

    abl = results_io.parse_result_name(synth.ablation_name(
        "sst", "safety+math", 0.2, "Fh only", "additive", 0.05, 100, "layerwise_sin", 44, "utility_math"))
    assert abl.kind == "ablation" and abl.cfg.ratio == "Fh only" and abl.cfg.variant == "additive"
    assert abl.cfg.k == 0.05 and abl.cfg.layerwise == "layerwise_sin" and abl.style == "old"

    base = results_io.parse_result_name(synth.base_name("SafetyFT", "harmbench_safety", seed=42))
    assert base.kind == "base" and base.base_model == "SafetyFT" and base.seed == 42


def test_new_style_utility_preferred_and_recorded(tmp_path):
    """(b) 新旧の有用性ファイルが併存するとき、新方式が採られ、記録される。"""
    for _ in range(2):  # 作る順序に依存しないことの確認として 2 回書く
        synth.write_main_point(
            tmp_path, "task_arithmetic", "safety+math", 0.6, 42,
            utility={"gsm8k": 0.50},
            old_style_utility={"math": {"gsm8k": 0.10, "minerva_math500": 0.20}},
        )
    scan = results_io.scan_results(tmp_path)
    group = [f for f in scan.files if f.method == "task_arithmetic"]
    chosen = results_io.utility_sources(group)
    assert chosen["gsm8k"]["style"] == "new"
    assert chosen["gsm8k"]["path"].endswith("utility_math_gsm8k.json")
    assert chosen["minerva_math500"]["style"] == "old"  # 新方式が無いタスクは旧方式
    inv = results_io.inventory(tmp_path)
    recorded = [c for c in inv["utility_choices"] if c["task"] == "gsm8k"]
    assert recorded and recorded[0]["adopted_style"] == "new"
    assert recorded[0]["also_present"]["old"]  # 併存していた旧方式のパスが残る


def test_missing_conditions_are_listed(tmp_path):
    """(c) 欠損の条件が一覧に出る。入力パスも残る（NFR3）。"""
    synth.write_main_point(tmp_path, "ties", "safety+math", 0.6, 42,
                           safety={"harmbench": synth.safety_json()}, utility={"gsm8k": 0.3})
    inv = results_io.inventory(tmp_path, patterns=["safety+math"], seeds=[42], alphas=[0.6])
    missing_ties = [m for m in inv["missing"] if m["method"] == "ties"]
    missing_metrics = {m["metric"] for m in missing_ties}
    assert "harmbench" not in missing_metrics and "gsm8k" not in missing_metrics
    assert "jailbreakbench" in missing_metrics and "mbpp" in missing_metrics
    # 何も書いていない手法は、全メトリクスが欠損として出る
    assert any(m["method"] == "dare" and m["metric"] == "harmbench" for m in inv["missing"])
    # 存在しない組合せ（4 ドメインの safemerge など）は、期待に含めない
    inv4 = results_io.inventory(tmp_path, patterns=["safety+math+code+medical"], seeds=[42], alphas=[0.6])
    assert not any(m["method"] == "safemerge" for m in inv4["missing"])
    assert any(p.endswith("safety+math_alpha0.6_seed42_harmbench_safety.json") for p in inv["input_files"])


def test_safe_write_rejects_outside_v5():
    """(d) safe_write は v5/ の外への書き込みを拒否する（NFR2）。"""
    outside = safeio.V5_ROOT.parent / "v3" / "results" / "should_not_exist.txt"
    with pytest.raises(safeio.OutsideWriteRootError):
        with safeio.safe_write(outside):
            pass
    assert not outside.exists()
    with pytest.raises(safeio.OutsideWriteRootError):
        safeio.write_json("/tmp/v5_should_not_exist.json", {})
    with pytest.raises(safeio.OutsideWriteRootError):
        safeio.resolve_write_path(safeio.V5_ROOT / ".." / "v3" / "x.json")


def test_safe_write_allows_inside_and_readonly_modes(write_root):
    """許可ルートの中には書ける。open_readonly は書き込みモードを拒否する。"""
    target = write_root / "outputs" / "a.json"
    safeio.write_json(target, {"b": 1, "a": 2})
    assert target.read_text(encoding="utf-8").index('"a"') < target.read_text(encoding="utf-8").index('"b"')
    with pytest.raises(ValueError):
        safeio.open_readonly(target, "w")
    with pytest.raises(ValueError):
        with safeio.safe_write(target, "a"):
            pass


def test_unparsed_names_and_broken_json_are_recorded_not_fatal(tmp_path):
    """回復できる誤り（解析できない名前、壊れた JSON）は一覧に載せて続行し、致命的な誤りは例外にする。"""
    d = tmp_path / "merged" / "seed42" / "safety+math" / "ties"
    d.mkdir(parents=True)
    (d / "sst_merge_v3_main_ties_safety+math_alpha0.6_seed42_unknown_metric.json").write_text("{}")
    broken = d / synth.main_name("ties", "safety+math", 0.6, 42, "harmbench_safety")
    broken.write_text("{ not json", encoding="utf-8")
    scan = results_io.scan_results(tmp_path)
    assert len(scan.unparsed) == 1 and "未知のメトリクス" in scan.unparsed[0]["reason"]
    errors = []
    assert results_io.load_json_file(broken, errors) is None
    assert errors and errors[0]["path"] == str(broken)
    with pytest.raises(FileNotFoundError):
        results_io.scan_results(tmp_path / "does_not_exist")
