"""SST のアブレーション表（k x variant。FR3.3、FR3.4）。

- 条件をそろえた列だけを同じ表に並べる。1 つの表は、パターン、手法系列（sst / datafree）、α、
  比（Fh/Fb）、層重み（なし）、マスク（hard）、サンプル数 n（sst のみ）を固定し、k と variant だけを動かす。
- α を動かした効果は、k x variant の表とは別の表（``alpha_effect``）にする。混ぜない。
- v3 に結果が無い条件は、別の条件で代用せず ``N/A`` とし、欠損の一覧に理由と探したファイル名の型を書く。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from . import manifest
from .metrics import load_point_records, summarize_point
from .results_io import (
    ALPHAS,
    PATTERN_DOMAINS,
    PATTERNS,
    SEEDS,
    ParsedFile,
    inventory,
    norm_alpha,
    scan_results,
)
from .safeio import write_json, write_text

# 論文（SAGAI_EN_sst）の k の格子。v3 に結果が無い k は N/A になる
K_GRID: list[float] = [0.05, 0.1, 0.2, 0.5]
VARIANTS: list[str] = ["interpolation", "additive"]
FAMILY_METHOD = {"sst": "diagonal_sst", "datafree": "data_free_sst"}
CENTER = {"ratio": "FhFb", "layerwise": "nolayerwise", "mask": "hard"}
CENTER_K = 0.2
CENTER_VARIANT = "interpolation"


def _k_equal(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


def searched_filename_pattern(family: str, pattern: str, alpha: float, k: float, variant: str, n: int | None) -> str:
    """探したファイル名の型（欠損の一覧に残す）。"""
    n_part = f"_n{n}" if family == "sst" and n is not None else ""
    method = FAMILY_METHOD[family]
    return (
        f"sst_merge_v3_ablation_{method}_ablation_{pattern}_alpha{alpha:.1f}{n_part}_k{k:g}_"
        f"{CENTER['ratio']}_{variant}_hardmask_{CENTER['layerwise']}_seed*_harmbench_safety.json"
    )


def evaluated_conditions(files: Iterable[ParsedFile], family: str | None = None) -> list[dict[str, Any]]:
    """評価済みのアブレーション条件（k、variant、層重み、比、n）の一覧。V10 が使う。

    条件ごとに、存在するパターン、α、seed、ファイル数を返す。
    """
    grouped: dict[tuple, dict[str, Any]] = {}
    for parsed in files:
        if parsed.kind != "ablation" or parsed.cfg is None:
            continue
        fam = "sst" if parsed.method == "diagonal_sst" else "datafree"
        if family and fam != family:
            continue
        cfg = parsed.cfg
        key = (fam, cfg.k, cfg.variant, cfg.layerwise, cfg.ratio, cfg.n, cfg.mask)
        entry = grouped.setdefault(
            key,
            {"family": fam, "k": cfg.k, "variant": cfg.variant, "layerwise": cfg.layerwise,
             "ratio": cfg.ratio, "n": cfg.n, "mask": cfg.mask,
             "patterns": set(), "alphas": set(), "seeds": set(), "n_files": 0},
        )
        entry["patterns"].add(parsed.pattern)
        entry["alphas"].add(norm_alpha(parsed.alpha))
        entry["seeds"].add(parsed.seed)
        entry["n_files"] += 1
    out = []
    for key in sorted(grouped, key=lambda k: (k[0], k[1], k[2], k[3], k[4], -1 if k[5] is None else k[5])):
        entry = grouped[key]
        out.append({**entry, "patterns": sorted(entry["patterns"]), "alphas": sorted(entry["alphas"]),
                    "seeds": sorted(entry["seeds"])})
    return out


def _center_ok(rec: dict[str, Any], family: str, n_samples: int) -> bool:
    cfg = rec["cfg"]
    if cfg is None or cfg.ratio != CENTER["ratio"] or cfg.layerwise != CENTER["layerwise"] or cfg.mask != CENTER["mask"]:
        return False
    return cfg.n == (n_samples if family == "sst" else None)


def _cell(recs: list[dict[str, Any]], pattern: str, rule: str) -> dict[str, Any]:
    summary = summarize_point(recs, rule)
    cell: dict[str, Any] = {"n_seeds": len(recs), "seeds": summary["seeds"]}
    for key in ("cond_asr", "vrr"):
        value = summary[key]
        cell[key] = None if value is None else {"mean": value[0], "std": value[1]}
    for domain in PATTERN_DOMAINS[pattern]:
        value = summary[domain]
        cell[domain] = None if value is None else {"mean": value[0], "std": value[1]}
    return cell


def build_ablation_tables(
    records: Iterable[dict[str, Any]],
    pattern: str,
    family: str,
    rule: str,
    alphas: Iterable[float] = ALPHAS,
    seeds: Iterable[int] = SEEDS,
    k_grid: Iterable[float] = K_GRID,
    n_samples: int = 500,
) -> dict[str, Any]:
    """k x variant の表（α ごと）と、α の効果の表を作る。

    戻り値: ``k_variant``（α ごとの表）、``alpha_effect``（中心条件 k=0.2・interpolation で α を動かした表）、
    ``missing``（N/A の条件の一覧）、``fixed``（固定した条件）。
    seed が一部しか揃わない条件は、使える seed で平均し、``partial`` に記録する（黙って混ぜない）。
    """
    if family not in FAMILY_METHOD:
        raise ValueError(f"未知の系列です: {family!r}（sst または datafree）")
    seeds = list(seeds)
    alphas = list(alphas)
    k_grid = list(k_grid)
    method = FAMILY_METHOD[family]
    lookup: dict[tuple[float, float, str], list[dict[str, Any]]] = {}
    for rec in records:
        if rec["kind"] != "ablation" or rec["method"] != method or rec["pattern"] != pattern:
            continue
        if not _center_ok(rec, family, n_samples):
            continue
        cfg = rec["cfg"]
        for k in k_grid:
            if _k_equal(cfg.k, k):
                lookup.setdefault((rec["alpha"], k, cfg.variant), []).append(rec)

    missing: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []

    def get(alpha: float, k: float, variant: str) -> dict[str, Any] | None:
        recs = sorted(lookup.get((norm_alpha(alpha), k, variant), []), key=lambda r: r["seed"])
        if not recs:
            missing.append({
                "family": family, "pattern": pattern, "alpha": alpha, "k": k, "variant": variant,
                "reason": "v3 に結果が無い（別の条件で代用しない）",
                "searched": searched_filename_pattern(family, pattern, alpha, k, variant, n_samples),
            })
            return None
        have = sorted(r["seed"] for r in recs)
        if have != sorted(seeds):
            partial.append({"family": family, "pattern": pattern, "alpha": alpha, "k": k, "variant": variant,
                            "seeds_present": have, "seeds_expected": sorted(seeds)})
        return _cell(recs, pattern, rule)

    k_variant = []
    for alpha in alphas:
        rows = []
        for k in k_grid:
            rows.append({"k": k, "cells": {variant: get(alpha, k, variant) for variant in VARIANTS}})
        k_variant.append({"alpha": alpha, "rows": rows})

    alpha_effect = []
    for alpha in alphas:
        recs = sorted(lookup.get((norm_alpha(alpha), CENTER_K, CENTER_VARIANT), []), key=lambda r: r["seed"])
        # 中心条件は上の k_variant で既に欠損を記録している。ここでは重複して記録しない
        alpha_effect.append({"alpha": alpha, "cell": _cell(recs, pattern, rule) if recs else None})

    return {
        "fixed": {"pattern": pattern, "family": family, "method": method, "rule": rule, **CENTER,
                  "n": n_samples if family == "sst" else None, "seeds": seeds},
        "k_variant": k_variant,
        "alpha_effect": alpha_effect,
        "missing": missing,
        "partial": partial,
    }


def _cell_text(cell: dict[str, Any] | None, pattern: str) -> list[str]:
    cols = ["cond_asr", "vrr"] + PATTERN_DOMAINS[pattern]
    if cell is None:
        return ["N/A"] * len(cols)
    out = []
    for col in cols:
        value = cell.get(col)
        out.append("N/A" if value is None else f"{value['mean']:.2f} ± {value['std']:.2f}")
    return out


def render_ablation_markdown(tables: dict[str, Any]) -> str:
    """表を Markdown にする。条件ごとに別の表にし、固定した条件を明記する。"""
    fixed = tables["fixed"]
    pattern = fixed["pattern"]
    metric_cols = ["Cond. ASR (%↓)", "VRR (%↑)"] + [f"{d.capitalize()} (%↑)" for d in PATTERN_DOMAINS[pattern]]
    lines = [
        f"### SST アブレーション: {pattern} / {fixed['family']}（{fixed['method']}）", "",
        f"固定した条件: 比={fixed['ratio']}、層重み={fixed['layerwise']}、マスク={fixed['mask']}、"
        f"n={fixed['n']}、seed={fixed['seeds']}、有害判定={fixed['rule']}。値は seed 平均 ± 標準偏差。",
        "v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。", "",
    ]
    for block in tables["k_variant"]:
        lines += [f"#### k x variant の表（α={block['alpha']:g} に固定）", ""]
        header = ["k"] + [f"{v}: {c}" for v in VARIANTS for c in metric_cols]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|:---|" + "|".join([":---:"] * (len(header) - 1)) + "|")
        for row in block["rows"]:
            cells = [f"{row['k']:g}"]
            for variant in VARIANTS:
                cells += _cell_text(row["cells"][variant], pattern)
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines += [f"#### α の効果の表（k={CENTER_K:g}、{CENTER_VARIANT} に固定。k x variant の表とは別）", ""]
    header = ["α"] + metric_cols
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|:---|" + "|".join([":---:"] * (len(header) - 1)) + "|")
    for entry in tables["alpha_effect"]:
        lines.append("| " + " | ".join([f"{entry['alpha']:g}"] + _cell_text(entry["cell"], pattern)) + " |")
    lines.append("")
    if tables["partial"]:
        lines += ["#### seed が一部しか揃わない条件", ""]
        for p in tables["partial"]:
            lines.append(f"- α={p['alpha']:g}、k={p['k']:g}、{p['variant']}: 存在 {p['seeds_present']}（期待 {p['seeds_expected']}）")
        lines.append("")
    return "\n".join(lines) + "\n"


def generate_ablation_tables(
    results_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    rule: str,
    patterns: Iterable[str] | None = None,
    families: Iterable[str] = ("sst", "datafree"),
    alphas: Iterable[float] = ALPHAS,
    seeds: Iterable[int] = SEEDS,
    n_samples: int = 500,
) -> list[str]:
    """アブレーション表を ``out_dir`` に書き、manifest を残す。書いたファイルのパスを返す。

    ``patterns`` を省くと、アブレーションの結果がある全パターンを対象にする。
    """
    out = Path(out_dir)
    scan = scan_results(results_root)
    inv = inventory(results_root, scan=scan)
    errors: list[dict[str, str]] = []
    abl_files = [f for f in scan.files if f.kind == "ablation"]
    records = load_point_records(abl_files, errors)
    if patterns is None:
        present = {f.pattern for f in abl_files}
        patterns = [p for p in PATTERNS if p in present] or ["safety+math"]
    written: list[str] = []
    for pattern in patterns:
        for family in families:
            tables = build_ablation_tables(records, pattern, family, rule, alphas, seeds, n_samples=n_samples)
            stem = f"ablation_{family}_{pattern.replace('+', '_')}"
            md_path = out / f"{stem}.md"
            write_text(md_path, render_ablation_markdown(tables))
            write_json(out / f"{stem}.json", tables)
            method = FAMILY_METHOD[family]
            used = sorted(
                {
                    path
                    for rec in records
                    if rec["method"] == method and rec["pattern"] == pattern
                    for path in list(rec["sources"]["safety"].values())
                    + [i["path"] for i in rec["sources"]["tasks"].values()]
                    + list(rec["sources"]["other"].values())
                }
            )
            manifest.write_manifest(
                md_path,
                script="v5/scripts/ablation_table.py",
                inputs=used,
                counts={"n_ablation_files": len([f for f in abl_files if f.method == method and f.pattern == pattern]),
                        "n_na_cells": len(tables["missing"]), "n_partial": len(tables["partial"]),
                        "n_load_errors": len(errors)},
                missing=tables["missing"],
                settings={**tables["fixed"], "k_grid": K_GRID, "variants": VARIANTS, "partial": tables["partial"],
                          "unparsed_names": scan.unparsed, "results_root": str(results_root),
                          "inventory_missing_main": len(inv["missing"])},
            )
            written.extend([str(md_path), str(out / f"{stem}.json")])
    return written
