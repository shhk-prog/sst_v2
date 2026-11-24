"""表の生成と、FLMSEC 論文の表との照合（FR3.1、FR3.4）。

- ``build_rows``: 結果の記録から、(パターン, 手法, α) ごとの行（seed 平均 ± 標準偏差）を作る。
  有害判定は HarmBench 単独（主軸）と OR 判定（generate_flmsec_hyo.py の再現）の両方で作る。
- ``parse_paper_table``: 論文の LaTeX の表（appendix.tex の表）から、行と値を読む。
- ``compare_with_paper``: 再現した値と論文の値を、許容差 0.005（表示桁 2 桁の丸め）で比べる。
  HarmBench 単独では合わないが OR 判定では合う箇所は、「判定差」として別項目に分ける。
- ``generate_flmsec_tables``: 上記をまとめて ``v5/outputs/tables/`` に書き、manifest を残す。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable

from . import manifest
from .metrics import (
    HARM_RULE_HARMBENCH_ONLY,
    HARM_RULE_OR_LEGACY,
    HARM_RULES,
    group_main_points,
    load_point_records,
    summarize_point,
)
from .results_io import METHOD_DISPLAY, inventory, norm_alpha, scan_results
from .safeio import write_json, write_text

VALUE_KEYS = (
    "cond_asr", "orig_asr", "bench_asr", "vrr", "vsr",
    "math", "code", "medical", "general", "evolcode_ppl", "medalpaca_ppl",
)

COLUMN_HEADERS = {
    "cond_asr": "Cond. ASR (%↓)",
    "orig_asr": "Orig. ASR (%↓)",
    "bench_asr": "Bench. ASR (%↓)",
    "vrr": "VRR (%↑)",
    "vsr": "VSR (%↑)",
    "math": "Math (%↑)",
    "code": "Code (%↑)",
    "medical": "Medical (%↑)",
    "general": "General (%↑)",
    "evolcode_ppl": "EvolCode PPL (↓)",
    "medalpaca_ppl": "MedAlpaca PPL (↓)",
}

# 論文の表（appendix.tex の label）-> 列の並びに対応する指標キー
PAPER_TABLES: dict[str, dict[str, Any]] = {
    "tab:evaluation_main_alpha06_safety": {"columns": ["bench_asr", "cond_asr", "vrr", "vsr"]},
    "tab:evaluation_main_alpha06_utility": {"columns": ["math", "code", "medical", "general"]},
}

# 論文の表示名 -> 内部の手法名
PAPER_METHOD_MAP = {
    "DARE": "dare",
    "DELLA": "della",
    "LED-Merging": "led_merging",
    "Matena-Fisher": "matena_fisher",
    "MergeAlign": "mergealign",
    "SafeMERGE": "safemerge",
    "Task Arithmetic": "task_arithmetic",
    "TIES": "ties",
    "Base": "Base",
}

DEFAULT_TOLERANCE = 0.005  # 論文の表示桁（小数 2 桁）の丸め

STATUS_LABELS = {
    "match": "一致",
    "rule_difference": "判定差（HarmBench 単独では不一致、OR 判定では一致）",
    "mismatch": "不一致",
    "repro_missing": "再現側に値がない",
    "paper_missing": "論文側に値がない",
    "both_na": "両方 N/A",
    "paper_unparsed": "論文の値を読めない",
    "row_missing": "再現側に行がない",
}


# ---------------------------------------------------------------------------
# 行の生成
# ---------------------------------------------------------------------------


def _collect_sources(recs: list[dict[str, Any]]) -> list[str]:
    paths: set[str] = set()
    for rec in recs:
        paths.update(rec["sources"]["safety"].values())
        paths.update(rec["sources"]["other"].values())
        paths.update(info["path"] for info in rec["sources"]["tasks"].values())
    return sorted(paths)


def build_rows(records: Iterable[dict[str, Any]], rule: str) -> list[dict[str, Any]]:
    """行のリストを返す。主実験は (パターン, 手法, α)、単体モデルは ``Base`` 行にする。

    各行: pattern, method, alpha, values（キー -> (mean, std, n) または None）, n_seeds, sources。
    ``rule`` は有害判定の方式（必ず明示する）。
    """
    if rule not in HARM_RULES:
        raise ValueError(f"未知の有害判定方式です: {rule!r}")
    records = list(records)
    rows: list[dict[str, Any]] = []
    for (method, pattern, alpha), recs in group_main_points(records, "main").items():
        summary = summarize_point(recs, rule)
        rows.append(
            {
                "pattern": pattern,
                "method": METHOD_DISPLAY.get(method, method),
                "alpha": alpha,
                "values": {key: summary[key] for key in VALUE_KEYS},
                "n_seeds": len(recs),
                "sources": _collect_sources(recs),
            }
        )
    base_groups: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        if rec["kind"] == "base":
            base_groups.setdefault(rec["base_model"], []).append(rec)
    for model, recs in base_groups.items():
        summary = summarize_point(recs, rule)
        rows.append(
            {
                "pattern": model,  # 論文の表と同じく、パターンの欄に単体モデル名を置く
                "method": "Base",
                "alpha": None,
                "values": {key: summary[key] for key in VALUE_KEYS},
                "n_seeds": len(recs),
                "sources": _collect_sources(recs),
            }
        )
    rows.sort(key=lambda r: (r["method"] == "Base", r["pattern"], r["method"], -1.0 if r["alpha"] is None else r["alpha"]))
    return rows


def select_alpha(rows: Iterable[dict[str, Any]], alpha: float) -> list[dict[str, Any]]:
    """指定した α の行と、α を持たない行（単発手法、単体モデル）を残す。"""
    target = norm_alpha(alpha)
    return [r for r in rows if r["alpha"] is None or r["alpha"] == target]


def format_value(value: tuple | None) -> str:
    """``(mean, std, n)`` を ``m ± s`` にする。値が無ければ ``---``。"""
    if value is None:
        return "---"
    return f"{value[0]:.2f} ± {value[1]:.2f}"


def _escape_cell(text: str) -> str:
    return str(text).replace("|", "\\|")


def render_markdown(rows: list[dict[str, Any]], columns: list[str], title: str, notes: list[str] | None = None) -> str:
    """行を Markdown の表にする。表内の ``|`` はエスケープする。"""
    lines = [f"#### {title}", ""]
    for note in notes or []:
        lines.append(f"注: {note}  ")  # 末尾の空白 2 つは Markdown の改行
    if notes:
        lines.append("")
    if not rows:
        lines.append("（該当する行がありません）")
        return "\n".join(lines) + "\n"
    headers = ["Pattern", "Method", "Alpha"] + [COLUMN_HEADERS[c] for c in columns]
    lines.append("| " + " | ".join(_escape_cell(h) for h in headers) + " |")
    lines.append("|" + "|".join([":---", ":---", ":---:"] + [":---:"] * len(columns)) + "|")
    for row in rows:
        alpha = "N/A" if row["alpha"] is None else f"{row['alpha']:.2f}"
        cells = [row["pattern"], row["method"], alpha] + [format_value(row["values"][c]) for c in columns]
        lines.append("| " + " | ".join(_escape_cell(c) for c in cells) + " |")
    return "\n".join(lines) + "\n"


def rows_to_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """JSON に書ける形（タプルをリストに）にする。"""
    out = []
    for row in rows:
        out.append({**row, "values": {k: (None if v is None else list(v)) for k, v in row["values"].items()}})
    return out


# ---------------------------------------------------------------------------
# 論文の表の読み取り
# ---------------------------------------------------------------------------

_VALUE_RE = re.compile(r"\$\s*(-?\d+(?:\.\d+)?)\s*\\pm\s*(-?\d+(?:\.\d+)?)\s*\$")


def _strip_comments(tex: str) -> str:
    return "\n".join(line for line in tex.splitlines() if not line.lstrip().startswith("%"))


def extract_latex_table(tex: str, label: str) -> str | None:
    """``\\label{label}`` を含む table 環境の本文を返す。無ければ ``None``。コメント行は無視する。"""
    text = _strip_comments(tex)
    pos = text.find("\\label{" + label + "}")
    if pos < 0:
        return None
    start = max(text.rfind("\\begin{table", 0, pos), 0)
    end = text.find("\\end{table", pos)
    if end < 0:
        return None
    return text[start:end]


def _clean_header_cell(cell: str) -> str:
    cell = re.sub(r"\\multirow\{\d+\}\{\*\}", "", cell)
    cell = cell.replace("\\shortstack[l]", "")
    cell = cell.replace("\\texttt", "")
    cell = cell.replace("\\\\", "")
    cell = re.sub(r"[{}]", "", cell)
    return re.sub(r"\s+", "", cell).strip()


def parse_paper_value(cell: str) -> tuple[float, float] | None | str:
    """論文の 1 セルを ``(mean, std)`` に読む。``---`` と N/A は ``None``、読めなければ ``"UNPARSED"``。"""
    text = cell.strip().rstrip("\\").strip()
    match = _VALUE_RE.search(text)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    if text in ("---", "--", "N/A", "n/a", "") or text.replace("$", "").strip() in ("---", "N/A"):
        return None
    return "UNPARSED"


def parse_paper_table(table_tex: str) -> list[dict[str, Any]]:
    """論文の表（``multirow`` でパターンをまとめた形式）から行を読む。

    戻り値の各行: ``pattern``、``method``（論文の表示名）、``values``（値のリスト）。
    ヘッダ行（最初の ``\\midrule`` より前）は読まない。
    """
    marker = table_tex.find("\\midrule")
    if marker < 0:
        raise ValueError("表に \\midrule が見つかりません（ヘッダと本体を区別できない）")
    body = table_tex[marker:]
    bottom = body.find("\\bottomrule")
    if bottom >= 0:
        body = body[:bottom]
    body = body.replace("\\midrule", "\n")
    rows: list[dict[str, Any]] = []
    current_pattern: str | None = None
    # 行の区切りは、直後が空白の ``\\``（shortstack 内の ``\\\texttt`` は区切りではない）
    for raw in re.split(r"\\\\(?=\s|$)", body):
        raw = raw.strip()
        if not raw:
            continue
        cells = raw.split("&")
        if len(cells) < 3:
            continue
        pattern_text = _clean_header_cell(cells[0])
        if pattern_text:
            current_pattern = pattern_text
        method = cells[1].strip()
        rows.append(
            {
                "pattern": current_pattern,
                "method": method,
                "values": [parse_paper_value(c) for c in cells[2:]],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 照合
# ---------------------------------------------------------------------------


def _index_rows(rows: Iterable[dict[str, Any]], alpha: float) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in select_alpha(rows, alpha):
        index[(row["pattern"], row["method"])] = row
    return index


def _close(a: float | None, b: float | None, tol: float) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol + 1e-9


def compare_with_paper(
    paper_rows: list[dict[str, Any]],
    repro_by_rule: dict[str, list[dict[str, Any]]],
    columns: list[str],
    alpha: float,
    tol: float = DEFAULT_TOLERANCE,
) -> list[dict[str, Any]]:
    """論文の値と再現した値を比べる（FR3.1）。

    各セル（行 x 列 x 平均/標準偏差）について、HarmBench 単独（主軸）と OR 判定の再現値を並べ、
    ``status`` を決める。HarmBench 単独で合えば ``match``。単独では合わないが OR 判定では合う場合は、
    判定の違いが原因なので ``rule_difference``。どちらでも合わなければ ``mismatch``。
    """
    indexes = {rule: _index_rows(rows, alpha) for rule, rows in repro_by_rule.items()}
    primary = indexes.get(HARM_RULE_HARMBENCH_ONLY, {})
    legacy = indexes.get(HARM_RULE_OR_LEGACY, {})
    results: list[dict[str, Any]] = []
    for prow in paper_rows:
        internal = PAPER_METHOD_MAP.get(prow["method"], prow["method"])
        key = (prow["pattern"], internal)
        for col_idx, metric in enumerate(columns):
            if col_idx >= len(prow["values"]):
                continue
            paper_value = prow["values"][col_idx]
            for stat_idx, stat in enumerate(("mean", "std")):
                entry = {
                    "pattern": prow["pattern"],
                    "method": prow["method"],
                    "metric": metric,
                    "stat": stat,
                    "paper": None,
                    "repro_harmbench_only": None,
                    "repro_or_legacy": None,
                }
                if paper_value == "UNPARSED":
                    entry["status"] = "paper_unparsed"
                    results.append(entry)
                    continue
                entry["paper"] = None if paper_value is None else paper_value[stat_idx]
                if key not in primary:
                    entry["status"] = "row_missing"
                    results.append(entry)
                    continue
                for rule_name, idx in (("repro_harmbench_only", primary), ("repro_or_legacy", legacy)):
                    value = idx.get(key, {}).get("values", {}).get(metric)
                    entry[rule_name] = None if value is None else value[stat_idx]
                p, a, b = entry["paper"], entry["repro_harmbench_only"], entry["repro_or_legacy"]
                if p is None and a is None:
                    entry["status"] = "both_na"
                elif p is None:
                    entry["status"] = "paper_missing"
                elif a is None and b is None:
                    entry["status"] = "repro_missing"
                elif _close(p, a, tol):
                    entry["status"] = "match"
                elif _close(p, b, tol):
                    entry["status"] = "rule_difference"
                else:
                    entry["status"] = "mismatch"
                results.append(entry)
    return results


def summarize_comparison(entries: list[dict[str, Any]]) -> dict[str, int]:
    """状態ごとの件数。"""
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    return dict(sorted(counts.items()))


def _fmt(value: float | None) -> str:
    return "---" if value is None else f"{value:.2f}"


def render_comparison_markdown(label: str, entries: list[dict[str, Any]], tol: float) -> str:
    """照合結果を Markdown にする。判定差は、不一致とは別の節に分ける。"""
    counts = summarize_comparison(entries)
    lines = [f"### 論文の表との照合: {label}", "", f"許容差: {tol}（論文の表示桁の丸め）", ""]
    lines.append("| 状態 | 件数 |")
    lines.append("|:---|---:|")
    for status, n in counts.items():
        lines.append(f"| {STATUS_LABELS.get(status, status)} | {n} |")
    lines.append("")

    def section(title: str, status: str) -> None:
        items = [e for e in entries if e["status"] == status]
        lines.append(f"#### {title}（{len(items)} 件）")
        lines.append("")
        if not items:
            lines.append("なし")
            lines.append("")
            return
        lines.append("| Pattern | Method | 指標 | 統計量 | 論文 | HarmBench 単独 | OR 判定 |")
        lines.append("|:---|:---|:---|:---|---:|---:|---:|")
        for e in items:
            lines.append(
                "| " + " | ".join(
                    _escape_cell(str(x)) for x in (
                        e["pattern"], e["method"], e["metric"], e["stat"],
                        _fmt(e["paper"]), _fmt(e["repro_harmbench_only"]), _fmt(e["repro_or_legacy"]),
                    )
                ) + " |"
            )
        lines.append("")

    section("判定差（有害判定の違いによる差。不一致とは別項目）", "rule_difference")
    section("不一致（判定の違いでは説明できない差）", "mismatch")
    section("再現側に値がない", "repro_missing")
    section("再現側に行がない", "row_missing")
    section("論文側に値がない", "paper_missing")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# まとめて生成
# ---------------------------------------------------------------------------

MAIN_COLUMNS = ["cond_asr", "orig_asr", "bench_asr", "vrr", "vsr", "math", "code", "medical", "general"]
SWEEP_COLUMNS = MAIN_COLUMNS + ["evolcode_ppl", "medalpaca_ppl"]


def generate_flmsec_tables(
    results_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    alpha: float = 0.6,
    paper_tex: dict[str, str] | None = None,
    tol: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """表を作って ``out_dir`` に書く。戻り値に、書いたファイルと照合の件数を返す。

    ``paper_tex`` は {表の label: LaTeX 本文（ファイル全体でよい）}。無ければ照合を行わない。
    """
    out = Path(out_dir)
    scan = scan_results(results_root)
    inv = inventory(results_root, scan=scan)
    errors: list[dict[str, str]] = []
    records = load_point_records(scan.files, errors)
    written: list[str] = []
    rows_by_rule: dict[str, list[dict[str, Any]]] = {rule: build_rows(records, rule) for rule in HARM_RULES}

    for rule in HARM_RULES:
        rows = rows_by_rule[rule]
        main_rows = select_alpha(rows, alpha)
        notes = [
            f"有害判定: {rule}（{'HarmBench Classifier 単独（主軸）' if rule == HARM_RULE_HARMBENCH_ONLY else 'generate_flmsec_hyo.py の OR 判定（再現確認用）'}）",
            f"α={alpha:g}（単発手法と単体モデルは α なし）、seed 平均 ± 標準偏差（ddof=1）",
            "General 列は MMLU、IFEval、AlpacaEval2 の単純平均（補助）",
        ]
        targets = [
            (f"flmsec_main_alpha{alpha:g}_{rule}", main_rows, MAIN_COLUMNS, f"主結果（α={alpha:g}）"),
            (f"alpha_sweep_{rule}", [r for r in rows if r["method"] != "Base"], SWEEP_COLUMNS, "α スイープ（全 α）"),
        ]
        for stem, target_rows, columns, title in targets:
            md_path = out / f"{stem}.md"
            write_text(md_path, render_markdown(target_rows, columns, title, notes))
            write_json(out / f"{stem}.json", rows_to_json(target_rows))
            inputs = [p for r in target_rows for p in r["sources"]]
            manifest.write_manifest(
                md_path,
                script="v5/scripts/regen_flmsec_tables.py",
                inputs=inputs,
                counts={"n_rows": len(target_rows), "n_json_files_scanned": scan.n_json_files,
                        "n_files_parsed": len(scan.files), "n_load_errors": len(errors)},
                missing=inv["missing"],
                settings={"harm_rule": rule, "alpha": alpha, "results_root": str(results_root),
                          "unparsed_names": scan.unparsed, "load_errors": errors,
                          "utility_choices": inv["utility_choices"]},
            )
            written.extend([str(md_path), str(out / f"{stem}.json")])

    comparison_counts: dict[str, dict[str, int]] = {}
    if paper_tex:
        all_entries: dict[str, list[dict[str, Any]]] = {}
        md_chunks = [
            "# 論文の表との照合（FR3.1）", "",
            "再現した値を、HarmBench 単独（主軸）と OR 判定の両方で論文の値と比べる。"
            "判定の違いで説明できる差は「判定差」として、不一致とは別に示す。", "",
        ]
        for label, tex in paper_tex.items():
            spec = PAPER_TABLES.get(label)
            if spec is None:
                raise ValueError(f"照合の列が未定義の表です: {label}（PAPER_TABLES に追加する）")
            table = extract_latex_table(tex, label)
            if table is None:
                raise ValueError(f"論文に表が見つかりません: {label}")
            paper_rows = parse_paper_table(table)
            entries = compare_with_paper(paper_rows, rows_by_rule, spec["columns"], alpha, tol)
            all_entries[label] = entries
            comparison_counts[label] = summarize_comparison(entries)
            md_chunks.append(render_comparison_markdown(label, entries, tol))
        cmp_md = out / "paper_comparison.md"
        write_text(cmp_md, "\n".join(md_chunks))
        write_json(out / "paper_comparison.json", all_entries)
        manifest.write_manifest(
            cmp_md,
            script="v5/scripts/regen_flmsec_tables.py",
            inputs=[p for r in rows_by_rule[HARM_RULE_HARMBENCH_ONLY] for p in r["sources"]],
            counts={"n_cells": sum(len(v) for v in all_entries.values()), "by_status": comparison_counts},
            missing=inv["missing"],
            settings={"alpha": alpha, "tolerance": tol, "labels": sorted(paper_tex)},
        )
        written.extend([str(cmp_md), str(out / "paper_comparison.json")])

    return {
        "written": written,
        "n_load_errors": len(errors),
        "comparison_counts": comparison_counts,
        "inventory_missing": len(inv["missing"]),
    }
