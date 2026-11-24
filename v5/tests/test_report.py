"""report のテスト（FR6.1、NFR3）。"""

import re
import shutil
from pathlib import Path

import pytest

import synth
from v5lib import ablation, hypotheses, metrics, plots, report, safeio, tables, verify

REAL_PREREG_MD = safeio.V5_ROOT / "docs" / "survey_summary" / "preregistration.md"


@pytest.fixture
def v5_tree(tmp_path, write_root):
    """合成の v5/ の構造（事前登録の文書、合成の結果から作った表、図、アブレーション、仮説の判定）。"""
    root = tmp_path / "v5"
    docs = root / "docs" / "survey_summary"
    docs.mkdir(parents=True)
    shutil.copy(REAL_PREREG_MD, docs / "preregistration.md")
    results = tmp_path / "results"
    safety = synth.safety_json(valid_harmful=2, valid_safe=6, bench_only_harmful=2)
    util = {"gsm8k": 0.2, "minerva_math500": 0.4, "humaneval": 0.5, "mbpp": 0.3, "pubmedqa": 0.6, "medqa_4options": 0.4}
    for seed in (42, 43):
        for method in ("dare", "task_arithmetic"):
            synth.write_main_point(results, method, "safety+math", 0.6, seed, safety={"harmbench": safety}, utility=util)
        synth.write_ablation_point(results, "sst", "safety+math", 0.6, "FhFb", "interpolation", 0.2, 500,
                                   "nolayerwise", seed, safety={"harmbench": safety},
                                   old_style_utility={"math": {"gsm8k": 0.2, "minerva_math500": 0.4}})
    tables.generate_flmsec_tables(results, root / "outputs" / "tables", 0.6, None)
    plots.generate_pareto_figures(results, root / "outputs" / "figures", 80.0, metrics.HARM_RULE_HARMBENCH_ONLY, tol_pt=2.0)
    ablation.generate_ablation_tables(results, root / "outputs" / "tables", metrics.HARM_RULE_HARMBENCH_ONLY,
                                      patterns=["safety+math"], families=("sst",))
    prereg = hypotheses.load_preregistration()
    res = {"V1": {"metrics": {"frac_tensors_fh_zero_over_80pct": 0.5}, "complete": True, "missing_inputs": [],
                  "scope": {"seeds": [42]}, "inputs": ["/data/fim.pt"], "details": [], "notes": []}}
    judged = verify.judge_stage(["V1", "V2"], res, prereg)
    verify.write_stage_output("v1_v9", root / "outputs" / "hypotheses", judged, res)
    return root


def results_lines(text: str) -> list[str]:
    begin, end = report.auto_markers("結果の節")
    return text[text.index(begin) : text.index(end)].splitlines()


def test_results_section_is_built_from_outputs(v5_tree):
    """(a) 合成の出力から、結果の節ができる。冒頭の定義は事前登録から取り込む。"""
    path = report.build_report(v5_tree)
    text = path.read_text(encoding="utf-8")
    assert path == v5_tree / "docs" / "survey_summary" / "report.md"
    assert "### 1.1 比較の方法（Validity-constrained Pareto 比較）" in text  # 事前登録の固定部分
    assert "### 1.2 採用基準" in text
    assert "### 2.1 FLMSEC の表の再現" in text and "Cond. ASR" in text
    assert text.count("![pareto_") == 4  # 4 枚の図
    # 画像リンクが report.md の場所から相対で実在するファイルを指す
    for rel_img in re.findall(r"!\[pareto_[^\]]+\]\(([^)]+)\)", text):
        assert (path.parent / rel_img).resolve().is_file(), rel_img
    assert "観測事実" in text and "支配されない点" in text
    assert "V1 " in text and "**支持**" in text  # V1 は閾値以上
    assert "V2 " in text and "**判定不能**" in text  # 未実行の V2 は判定不能
    assert "ablation_sst_safety_math" in text
    assert "依頼者は FLMSEC の表をすでに見ている" in text


def test_handwritten_sections_survive_regeneration(v5_tree):
    """(b) 手書きのマーカー内を、再生成で上書きしない。自動生成の範囲は更新される。"""
    path = report.build_report(v5_tree)
    text = path.read_text(encoding="utf-8")
    begin, end = report.hand_markers("考察（FR4）")
    custom = "手書きの考察: FIM の 0 の割合が高い（観測事実）。\n```\npseudo code\n```"
    start = text.index(begin) + len(begin)
    text = text[:start] + "\n" + custom + "\n" + text[text.index(end):]
    path.write_text(text, encoding="utf-8")
    (v5_tree / "outputs" / "hypotheses" / "v1_v9.json").unlink()  # 出力が変わった状態にする
    report.build_report(v5_tree)
    again = path.read_text(encoding="utf-8")
    assert custom in again
    design_begin, _ = report.hand_markers("設計案（FR5）")
    assert design_begin in again and "この節は、実行結果を見たうえで手書きする" in again  # 手書きの案内文も残る
    assert "未実行" in again and "v1_v9.json" in again  # 自動生成の範囲は、出力の変更を反映する
    assert again.count(report.hand_markers("考察（FR4）")[0]) == 1  # 重複して増えない


def test_numeric_lines_carry_source_paths(v5_tree):
    """(c) 数値の行に、元ファイルのパスが付く（NFR3）。"""
    text = report.build_report(v5_tree).read_text(encoding="utf-8")
    bullets = [l for l in results_lines(text) if l.lstrip().startswith("- ") and re.search(r"\d", l)
               and "未実行" not in l]
    assert len(bullets) >= 8
    missing = [l for l in bullets if "出典" not in l]
    assert missing == []
    # 出典として書かれたパスが、実在するファイルを指す
    refs = set(re.findall(r"出典: `(v5/[^`]+)`", text))
    assert refs
    for ref in refs:
        assert (v5_tree.parent / ref).exists(), ref
    # 表の埋め込みにも、表の直後に出典の行がある
    assert text.count("- 出典: `v5/outputs/tables/flmsec_main_alpha0.6_") == 2


def test_errors_are_explicit(v5_tree, tmp_path):
    """異常系: マーカーが壊れた report.md、固定マーカーの無い事前登録、事前登録が無い場合は例外にする。"""
    path = report.build_report(v5_tree)
    broken = path.read_text(encoding="utf-8").replace(report.auto_markers("結果の節")[1], "")
    path.write_text(broken, encoding="utf-8")
    with pytest.raises(ValueError, match="自動生成のマーカー"):
        report.build_report(v5_tree)
    path.unlink()
    prereg = v5_tree / "docs" / "survey_summary" / "preregistration.md"
    prereg.write_text("# no markers", encoding="utf-8")
    with pytest.raises(ValueError, match="固定マーカー"):
        report.build_report(v5_tree)
    prereg.unlink()
    with pytest.raises(FileNotFoundError):
        report.build_report(v5_tree)


def test_report_without_outputs_marks_everything_as_not_run(tmp_path, write_root):
    """出力が何も無くても失敗せず、未実行として書く（嘘の数値を作らない）。"""
    root = tmp_path / "v5"
    (root / "docs" / "survey_summary").mkdir(parents=True)
    shutil.copy(REAL_PREREG_MD, root / "docs" / "survey_summary" / "preregistration.md")
    text = report.build_report(root).read_text(encoding="utf-8")
    assert text.count("未実行") >= 4 and "仮説の判定は、まだありません" in text
    assert not re.search(r"\*\*(支持|不支持)\*\*", text)
