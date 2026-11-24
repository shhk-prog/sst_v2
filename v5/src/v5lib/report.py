"""レポートの生成基盤（FR6、NFR3、FR4.2、FR5.1）。

``v5/outputs/`` の表、図、manifest、仮説の判定を集めて、``report.md`` の「結果の節」を組み立てる。

- 自動生成の範囲は、``<!-- 自動生成: <名前> 開始 -->`` と ``<!-- 自動生成: <名前> 終了 -->`` で囲む。
- 手書きの範囲（考察 FR4、設計案 FR5）は、``<!-- 手書き: <名前> 開始 -->`` と ``<!-- 手書き: <名前> 終了 -->`` で囲む。
  再生成は、自動生成の範囲だけを置き換え、手書きの範囲には触れない。
- 冒頭の定義（FR1.1）は、``preregistration.md`` の固定マーカー内を取り込む。
- 数値は、必ず元ファイルのパスつきで書く（NFR3）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .safeio import open_readonly, write_text

AUTO_NAMES = ("冒頭の定義", "結果の節")
HAND_NAMES = ("考察（FR4）", "設計案（FR5）")
PREREG_BEGIN = "<!-- 固定: 比較方法と採用基準 開始 -->"
PREREG_END = "<!-- 固定: 比較方法と採用基準 終了 -->"

HAND_PLACEHOLDERS = {
    "考察（FR4）": (
        "（この節は、実行結果を見たうえで手書きする。FIM 選択の問題、注入方式の問題、ハイパーパラメータの問題の"
        "3 分類で、各主張を「観測事実」「機構仮説」「新手法への示唆」の 3 段階に分ける。"
        "根拠の数値は、結果の節の出典のパスまで辿れるようにする。）"
    ),
    "設計案（FR5）": (
        "（この節は、実行結果を見たうえで手書きする。文章と擬似コードで、DLSP_hiromi2 に導入する設計と、"
        "未検証の部分を分けて書く。優れている「可能性」までを述べ、既存の結果で裏付けられる主張と、"
        "新しい実験をしないと確かめられない仮説を分ける。）"
    ),
}


def auto_markers(name: str) -> tuple[str, str]:
    return f"<!-- 自動生成: {name} 開始 -->", f"<!-- 自動生成: {name} 終了 -->"


def hand_markers(name: str) -> tuple[str, str]:
    return f"<!-- 手書き: {name} 開始 -->", f"<!-- 手書き: {name} 終了 -->"


def _read_text(path: Path) -> str:
    with open_readonly(path) as handle:
        return handle.read()


def _read_json(path: Path) -> Any:
    with open_readonly(path) as handle:
        return json.load(handle)


def _ref(v5_root: Path, path: Path) -> str:
    """出典のパス（``v5/`` からの相対）。"""
    try:
        return "v5/" + path.resolve().relative_to(v5_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def extract_fixed_definitions(prereg_md: str) -> str:
    """``preregistration.md`` の固定マーカーの内側を取り出す。マーカーが無ければ ``ValueError``（致命的）。"""
    start = prereg_md.find(PREREG_BEGIN)
    end = prereg_md.find(PREREG_END)
    if start < 0 or end < 0 or end < start:
        raise ValueError("preregistration.md に、固定マーカー（比較方法と採用基準）がありません")
    return prereg_md[start + len(PREREG_BEGIN) : end].strip("\n")


# ---------------------------------------------------------------------------
# 結果の節
# ---------------------------------------------------------------------------


def _section_tables(v5_root: Path) -> list[str]:
    tables_dir = v5_root / "outputs" / "tables"
    lines = ["### 2.1 FLMSEC の表の再現（FR3.1）", ""]
    mains = sorted(tables_dir.glob("flmsec_main_alpha*_*.md")) if tables_dir.is_dir() else []
    if not mains:
        return lines + [f"（未実行: `{_ref(v5_root, tables_dir)}/flmsec_main_alpha*.md` がありません）", ""]
    for path in mains:
        lines.append(_read_text(path).rstrip())
        manifest = path.with_name(path.name + ".manifest.json")
        extra = ""
        if manifest.is_file():
            m = _read_json(manifest)
            extra = f"、manifest: `{_ref(v5_root, manifest)}`、元の結果ファイル {m.get('n_input_files')} 件"
        lines += ["", f"- 出典: `{_ref(v5_root, path)}`{extra}", ""]
    cmp_json = tables_dir / "paper_comparison.json"
    if cmp_json.is_file():
        data = _read_json(cmp_json)
        lines.append("#### 論文の表との照合（件数）")
        lines.append("")
        for label, entries in data.items():
            counts: dict[str, int] = {}
            for e in entries:
                counts[e["status"]] = counts.get(e["status"], 0) + 1
            lines.append(f"- {label}: {json.dumps(counts, ensure_ascii=False, sort_keys=True)}"
                         f"（出典: `{_ref(v5_root, cmp_json)}`、詳細: `{_ref(v5_root, tables_dir / 'paper_comparison.md')}`）")
        lines.append("")
    return lines


def _section_figures(v5_root: Path) -> list[str]:
    fig_dir = v5_root / "outputs" / "figures"
    lines = ["### 2.2 safety-utility 曲線と観測事実（FR3.2、FR1.5）", ""]
    pngs = sorted(fig_dir.glob("pareto_*.png")) if fig_dir.is_dir() else []
    if not pngs:
        return lines + [f"（未実行: `{_ref(v5_root, fig_dir)}/pareto_*.png` がありません）", ""]
    for png in pngs:
        manifest = png.with_name(png.name + ".manifest.json")
        n_inputs = _read_json(manifest).get("n_input_files") if manifest.is_file() else None
        rel_img = f"../../outputs/figures/{png.name}"
        lines.append(f"- 図: ![{png.stem}]({rel_img})（出典: `{_ref(v5_root, png)}`、manifest: `{_ref(v5_root, manifest)}`、元の結果ファイル {n_inputs} 件）")
    lines.append("")
    obs_path = fig_dir / "observations.json"
    if obs_path.is_file():
        obs = _read_json(obs_path)
        src = f"出典: `{_ref(v5_root, obs_path)}`"
        lines.append("#### 観測事実（厳密な Pareto 支配と近傍比較。機構の解釈はここでは書かない）")
        lines.append("")
        for pattern, info in obs.items():
            lines.append(f"- {pattern}: 点 {info['n_points']} 個、VRR ≥ {info['vrr_floor']:g}% で残った点 {info['n_kept']} 個、"
                         f"除外した点 {len(info['excluded'])} 個（{src}）")
            for e in info["excluded"]:
                vrr = "---" if e["vrr"] is None else f"{e['vrr']:.2f}"
                lines.append(f"  - 除外: {e['label']}、VRR {vrr}%、理由: {e['reason']}（{src}）")
            for domain, d in info["domains"].items():
                pareto = d["pareto"]
                lines.append(f"  - {domain}: 支配されない点 {pareto['front']}、支配される点 {len(pareto['dominated'])} 個、"
                             f"近傍比較 {len(d['neighborhoods'])} 組（{src}）")
        lines.append("")
    return lines


def _section_ablation(v5_root: Path) -> list[str]:
    tables_dir = v5_root / "outputs" / "tables"
    lines = ["### 2.3 SST のアブレーション（FR3.3）", ""]
    files = sorted(tables_dir.glob("ablation_*.md")) if tables_dir.is_dir() else []
    if not files:
        return lines + [f"（未実行: `{_ref(v5_root, tables_dir)}/ablation_*.md` がありません）", ""]
    for path in files:
        manifest = path.with_name(path.name + ".manifest.json")
        n_na = _read_json(manifest).get("counts", {}).get("n_na_cells") if manifest.is_file() else None
        lines.append(f"- {path.stem}: N/A のセル {n_na} 個（出典: `{_ref(v5_root, path)}`、欠損の一覧: `{_ref(v5_root, manifest)}`）")
    lines.append("")
    return lines


def _section_hypotheses(v5_root: Path) -> list[str]:
    hyp_dir = v5_root / "outputs" / "hypotheses"
    lines = ["### 2.4 仮説 V1〜V11 の判定（FR2.3）", ""]
    found = False
    for stage in ("v1_v9", "v10_v11"):
        path = hyp_dir / f"{stage}.json"
        if not path.is_file():
            lines.append(f"- （未実行: `{_ref(v5_root, path)}` がありません）")
            continue
        found = True
        doc = _read_json(path)
        src = f"出典: `{_ref(v5_root, path)}`"
        for hid, v in sorted(doc["verdicts"].items(), key=lambda kv: int(kv[0][1:])):
            value = v["value"]
            value_text = "---" if value is None else (f"{value:.4g}" if isinstance(value, (int, float)) else str(value))
            scope = v.get("scope") or {}
            lines.append(f"- {hid} {v['title']}: **{v['verdict']}**。指標 {v['metric']} = {value_text}。{v['reason']}（実行範囲: "
                         f"{json.dumps(scope, ensure_ascii=False, sort_keys=True)}、{src}）")
    lines.append("")
    if not found:
        lines.append("（仮説の判定は、まだありません）")
        lines.append("")
    return lines


def build_results_section(v5_root: Path) -> str:
    """「結果の節」（自動生成）の本文を作る。"""
    lines = ["## 2. 結果", "",
             "この節は `v5/scripts/build_report.py` が自動生成する。数値は、出典のパスの元ファイルまで辿れる（NFR3）。", ""]
    for section in (_section_tables, _section_figures, _section_ablation, _section_hypotheses):
        lines += section(v5_root)
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# 組み立て
# ---------------------------------------------------------------------------


def _block(markers: tuple[str, str], body: str) -> str:
    return f"{markers[0]}\n{body.strip(chr(10))}\n{markers[1]}"


def _template() -> str:
    parts = ["# 大規模調査のまとめ（v5）レポート", "", "{auto:冒頭の定義}", "", "{auto:結果の節}", "",
             "## 3. 考察（FR4）", ""]
    parts.append(_block(hand_markers("考察（FR4）"), HAND_PLACEHOLDERS["考察（FR4）"]))
    parts += ["", "## 4. 新しい merge 手法の設計案（FR5）", ""]
    parts.append(_block(hand_markers("設計案（FR5）"), HAND_PLACEHOLDERS["設計案（FR5）"]))
    return "\n".join(parts) + "\n"


def _replace_auto(text: str, name: str, body: str) -> str:
    begin, end = auto_markers(name)
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"report.md に自動生成のマーカーがありません: {name}")
    replacement = _block((begin, end), body)
    return pattern.sub(lambda _m: replacement, text, count=1)


def build_report(v5_root: str | Path, report_path: str | Path | None = None) -> Path:
    """``report.md`` の自動生成の範囲を作り直す。手書きの範囲は、そのまま残す。

    ``report.md`` が無ければ、手書きの範囲に案内文を入れて新しく作る。
    """
    root = Path(v5_root)
    docs = root / "docs" / "survey_summary"
    target = Path(report_path) if report_path else docs / "report.md"
    prereg_path = docs / "preregistration.md"
    try:
        definitions = extract_fixed_definitions(_read_text(prereg_path))
    except OSError as exc:
        raise FileNotFoundError(f"事前登録の文書を読めません: {prereg_path}: {exc}") from exc
    intro = definitions + f"\n\n（出典: `{_ref(root, prereg_path)}`。依頼者は FLMSEC の表をすでに見ている。）"
    results = build_results_section(root)

    if target.is_file():
        text = _read_text(target)
    else:
        text = _template()
        for name in AUTO_NAMES:
            text = text.replace("{auto:" + name + "}", _block(auto_markers(name), "x"))
    text = _replace_auto(text, "冒頭の定義", intro)
    text = _replace_auto(text, "結果の節", results)
    write_text(target, text)
    return target
