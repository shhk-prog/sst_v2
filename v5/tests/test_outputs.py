"""表、図、アブレーション表、manifest のテスト（FR3.1〜FR3.4、NFR1）。合成の結果ディレクトリだけを使う。"""

import json
from pathlib import Path

import pytest

import synth
from v5lib import ablation, metrics, plots, results_io, tables

PAPER_TEX = r"""
\begin{table}[htbp]
\caption{synthetic}
\label{tab:evaluation_main_alpha06_safety}
\begin{tabularx}{\textwidth}{ll*{4}{X}}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Bench. ASR} & \textbf{Cond. ASR} & \textbf{VRR} & \textbf{VSR} \\
\midrule
\multirow{3}{*}{\texttt{safety+math}}
& DARE
& $40.00 \pm 0.00$
& $20.00 \pm 0.00$
& $100.00 \pm 0.00$
& $80.00 \pm 0.00$ \\
& TIES
& $40.00 \pm 0.00$
& $40.00 \pm 0.00$
& $100.00 \pm 0.00$
& $60.00 \pm 0.00$ \\
& Task Arithmetic
& $40.00 \pm 0.00$
& $99.00 \pm 0.00$
& $100.00 \pm 0.00$
& $80.00 \pm 0.00$ \\
\bottomrule
\end{tabularx}
\end{table}
"""

UTIL = {"gsm8k": 0.2, "minerva_math500": 0.4, "humaneval": 0.5, "mbpp": 0.3,
        "pubmedqa": 0.6, "medqa_4options": 0.4}


def build_results(root: Path):
    """HarmBench 単独と OR 判定で値が変わる合成データ（妥当 10 件: HB で有害 2、他の分類器だけ有害 2）。"""
    safety = synth.safety_json(valid_harmful=2, valid_safe=6, bench_only_harmful=2)
    for seed in (42, 43):
        for method in ("dare", "ties", "task_arithmetic"):
            for alpha in (0.2, 0.6):
                synth.write_main_point(root, method, "safety+math", alpha, seed,
                                       safety={"harmbench": safety}, utility=UTIL)
        # 単発手法（α なし）と、4 ドメインのパターン
        synth.write_main_point(root, "safemerge", "safety+math", None, seed,
                               safety={"harmbench": safety}, utility=UTIL)
        low_vrr = synth.safety_json(valid_harmful=1, valid_safe=3, gibberish=6)  # VRR 40%
        synth.write_main_point(root, "dare", "safety+math+code+medical", 0.2, seed,
                               safety={"harmbench": low_vrr}, utility=UTIL)
        synth.write_main_point(root, "dare", "safety+math+code+medical", 0.6, seed,
                               safety={"harmbench": safety}, utility=UTIL)
        synth.write_main_point(root, "ties", "safety+code", 0.6, seed,
                               safety={"harmbench": safety}, utility=UTIL)
        synth.write_main_point(root, "ties", "safety+medical", 0.6, seed,
                               safety={"harmbench": safety}, utility=UTIL)
    synth.dump(root / "base" / synth.base_name("WizardMath", "harmbench_safety"), safety)


def snapshot(out_dir: Path) -> dict:
    return {str(p.relative_to(out_dir)): p.read_bytes() for p in sorted(out_dir.rglob("*")) if p.is_file()}


def test_paper_comparison_match_rule_difference_and_mismatch(tmp_path, write_root):
    """(a) 論文の値との照合: 一致、不一致、判定差が別項目に分かれる。"""
    root = tmp_path / "results"
    build_results(root)
    out = write_root / "out" / "tables"
    info = tables.generate_flmsec_tables(root, out, 0.6, {"tab:evaluation_main_alpha06_safety": PAPER_TEX})
    counts = info["comparison_counts"]["tab:evaluation_main_alpha06_safety"]
    entries = json.loads((out / "paper_comparison.json").read_text(encoding="utf-8"))["tab:evaluation_main_alpha06_safety"]

    def status(method, metric, stat="mean"):
        return next(e["status"] for e in entries if e["method"] == method and e["metric"] == metric and e["stat"] == stat)

    assert status("DARE", "cond_asr") == "match" and status("DARE", "vsr") == "match"
    assert status("DARE", "bench_asr") == "match"
    # HarmBench 単独では 20、OR 判定では 40: 論文の 40 は OR 判定に合う -> 判定差（不一致とは別項目）
    assert status("TIES", "cond_asr") == "rule_difference" and status("TIES", "vsr") == "rule_difference"
    assert status("Task Arithmetic", "cond_asr") == "mismatch"
    assert counts["rule_difference"] >= 2 and counts["mismatch"] == 1
    md = (out / "paper_comparison.md").read_text(encoding="utf-8")
    assert "判定差" in md and "不一致（判定の違いでは説明できない差）" in md
    # 主軸の表は HarmBench 単独、再現用の表は OR 判定。値が違う
    hb = json.loads((out / "flmsec_main_alpha0.6_harmbench_only.json").read_text(encoding="utf-8"))
    legacy = json.loads((out / "flmsec_main_alpha0.6_or_legacy.json").read_text(encoding="utf-8"))
    pick = lambda rows: next(r for r in rows if r["method"] == "dare" and r["pattern"] == "safety+math")["values"]["cond_asr"][0]
    assert pick(hb) == pytest.approx(20.0) and pick(legacy) == pytest.approx(40.0)
    # 表に、単発手法（α なし）と単体モデルの行が入り、α=0.2 の行は主結果の表に入らない
    main_rows = {(r["pattern"], r["method"], r["alpha"]) for r in hb}
    assert ("safety+math", "safemerge", None) in main_rows and ("WizardMath", "Base", None) in main_rows
    assert ("safety+math", "dare", 0.2) not in main_rows


def test_paper_table_parser_edge_cases():
    """論文の表の読み取り: --- は None、読めないセルは UNPARSED、shortstack のパターン名を 1 つにつなぐ。"""
    tex = r"""
\label{t}
\toprule
\textbf{A} & \textbf{B} & \textbf{C} \\
\midrule
\multirow{2}{*}{\shortstack[l]{\texttt{safety+math+}\\\texttt{code+medical}}}
& MergeAlign
& ---
& $0.00 \pm 0.00$ \\
& SafeMERGE
& oops
& $1.50 \pm 0.25$ \\
\bottomrule
"""
    rows = tables.parse_paper_table(tex)
    assert [r["method"] for r in rows] == ["MergeAlign", "SafeMERGE"]
    assert rows[0]["pattern"] == rows[1]["pattern"] == "safety+math+code+medical"
    assert rows[0]["values"] == [None, (0.0, 0.0)]
    assert rows[1]["values"] == ["UNPARSED", (1.5, 0.25)]
    with pytest.raises(ValueError):
        tables.parse_paper_table("no rule lines here")  # ヘッダと本体を区別できない


def test_four_pareto_figures_with_three_subplots_for_multidomain(tmp_path, write_root):
    """(b) 曲線が 4 枚でき、4 ドメインの図は 3 サブプロット。VRR の下限を満たさない点は別の記号。"""
    root = tmp_path / "results"
    build_results(root)
    out = write_root / "out" / "figures"
    metas = plots.generate_pareto_figures(root, out, 80.0, metrics.HARM_RULE_HARMBENCH_ONLY)
    assert len(metas) == 4
    pngs = sorted(p.name for p in out.glob("*.png"))
    assert pngs == ["pareto_safety_code.png", "pareto_safety_math.png",
                    "pareto_safety_math_code_medical.png", "pareto_safety_medical.png"]
    by_pattern = {m["pattern"]: m for m in metas}
    assert by_pattern["safety+math+code+medical"]["n_axes"] == 3
    assert by_pattern["safety+math"]["n_axes"] == 1
    assert by_pattern["safety+math+code+medical"]["domains"] == ["math", "code", "medical"]
    # 4 ドメインの α=0.2 の点（VRR 40%）は、3 つのサブプロットのそれぞれで除外の記号になる
    assert by_pattern["safety+math+code+medical"]["n_excluded_markers"] == 3
    assert by_pattern["safety+math"]["n_excluded_markers"] == 0
    assert all(p.stat().st_size > 1000 for p in out.glob("*.png"))
    # 単一ドメインの図は、対応するタスクだけをプロットする
    assert {pt["domain"] for pt in by_pattern["safety+code"]["points"]} == {"code"}


def test_ablation_table_marks_missing_as_na_without_substitution(tmp_path):
    """(c) アブレーション表の欠損は N/A で、別の条件（別の n、別の variant）で代用しない。"""
    root = tmp_path / "results"
    safety = synth.safety_json(valid_harmful=1, valid_safe=9)
    old = {"math": {"gsm8k": 0.2, "minerva_math500": 0.4}}
    for seed in (42, 43):
        # 中心条件（n=500、k=0.2、interpolation）は存在する
        synth.write_ablation_point(root, "sst", "safety+math", 0.6, "FhFb", "interpolation", 0.2, 500,
                                   "nolayerwise", seed, safety={"harmbench": safety}, old_style_utility=old)
        # 代用してはいけない近い条件: n=100 の additive、層重みあり、別の比
        synth.write_ablation_point(root, "sst", "safety+math", 0.6, "FhFb", "additive", 0.2, 100,
                                   "nolayerwise", seed, safety={"harmbench": safety}, old_style_utility=old)
        synth.write_ablation_point(root, "sst", "safety+math", 0.6, "FhFb", "interpolation", 0.2, 500,
                                   "layerwise_sin", seed, safety={"harmbench": safety}, old_style_utility=old)
    scan = results_io.scan_results(root)
    records = metrics.load_point_records(scan.files, [])
    result = ablation.build_ablation_tables(records, "safety+math", "sst",
                                            metrics.HARM_RULE_HARMBENCH_ONLY, alphas=[0.6], seeds=[42, 43])
    rows = {row["k"]: row["cells"] for row in result["k_variant"][0]["rows"]}
    assert rows[0.2]["interpolation"] is not None and rows[0.2]["interpolation"]["n_seeds"] == 2
    assert rows[0.2]["additive"] is None  # n=100 の additive では代用しない
    assert rows[0.05]["interpolation"] is None and rows[0.5]["additive"] is None
    missing_keys = {(m["k"], m["variant"]) for m in result["missing"]}
    assert (0.2, "additive") in missing_keys and (0.05, "interpolation") in missing_keys
    assert (0.2, "interpolation") not in missing_keys
    assert all("seed*_harmbench_safety.json" in m["searched"] for m in result["missing"])
    md = ablation.render_ablation_markdown(result)
    assert "N/A" in md and "α の効果の表" in md
    # α の効果の表は、k x variant の表とは別の構造で、中心条件の値だけを持つ
    assert result["alpha_effect"][0]["cell"]["cond_asr"]["mean"] == pytest.approx(10.0)
    with pytest.raises(ValueError):
        ablation.build_ablation_tables(records, "safety+math", "unknown", metrics.HARM_RULE_HARMBENCH_ONLY)


def test_manifest_records_inputs_counts_and_missing(tmp_path, write_root):
    """(d) manifest に、入力パス、件数、欠損、設定値が入る。"""
    from regen_flmsec_tables import main as regen_main

    root = tmp_path / "results"
    build_results(root)
    out = write_root / "out" / "tables"
    code = regen_main(["--results-root", str(root), "--out-dir", str(out), "--no-paper"])
    assert code == 0
    manifest = json.loads((out / "flmsec_main_alpha0.6_harmbench_only.md.manifest.json").read_text(encoding="utf-8"))
    assert manifest["n_input_files"] > 0
    assert any(p.endswith("safety+math_alpha0.6_seed42_harmbench_safety.json") for p in manifest["input_files"])
    assert manifest["counts"]["n_rows"] > 0 and manifest["counts"]["n_files_parsed"] > 0
    assert manifest["settings"]["harm_rule"] == "harmbench_only"
    assert manifest["missing"], "合成データは安全性ベンチが 1 つしか無いので、欠損が一覧に出るはず"
    assert "output" in manifest and not manifest["output"].startswith("/")
    # 出力先が v5/ の外ならスクリプトは失敗する（NFR2）
    import os
    os.environ.pop("V5_WRITE_ROOT_FOR_TESTS", None)
    assert regen_main(["--results-root", str(root), "--out-dir", str(tmp_path / "outside"), "--no-paper"]) == 1
    assert not (tmp_path / "outside").exists()


def test_two_runs_produce_identical_outputs(tmp_path, write_root):
    """(e) 同じ入力で 2 回実行すると、表、図、manifest がバイト単位で同じ（NFR1）。"""
    root = tmp_path / "results"
    build_results(root)
    out = write_root / "out"

    def run():
        tables.generate_flmsec_tables(root, out / "tables", 0.6, {"tab:evaluation_main_alpha06_safety": PAPER_TEX})
        plots.generate_pareto_figures(root, out / "figures", 80.0, metrics.HARM_RULE_HARMBENCH_ONLY)
        ablation.generate_ablation_tables(root, out / "tables", metrics.HARM_RULE_HARMBENCH_ONLY, patterns=["safety+math"])

    run()
    first = snapshot(out)
    run()
    second = snapshot(out)
    assert first.keys() == second.keys() and len(first) > 20
    different = [name for name in first if first[name] != second[name]]
    assert different == []
