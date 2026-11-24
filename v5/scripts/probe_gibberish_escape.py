#!/usr/bin/env python3
"""ルールベース gibberish 判定（is_gibberish=False）をすり抜けた多言語文字化け崩壊の探索スクリプト（読み取り専用）。

背景: ``native_classifier_probe.md`` で、α=0.6 の安全性の数値が、ベンチマーク別の分類器と
HarmBench 単独で大きく割れる（例: safety+code DARE で 68.30% vs 0.00%）ことが分かった。
このスクリプトは、``is_gibberish=False`` とされた応答のうち、
(1) 非 ASCII 文字を含む割合・空白の極端に少ない長文字列（トークン崩壊）の割合、
(2) 「ベンチマーク別分類器では有害・HarmBench 単独では無害」となる乖離応答のうち、
    トークン崩壊（非 ASCII 混入または 30 文字以上の無空白連続）に該当する割合
を、α=0.6 の全パターン・全手法について定量集計する。

実行: ``CUDA_VISIBLE_DEVICES="" venv_sst/bin/python v5/scripts/probe_gibberish_escape.py``
出力先: ``v5/outputs/probe/gibberish_escape_probe.{json,md}`` のみ（NFR2、NFR4）。
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, DEFAULT_RESULTS_ROOT
from probe_native_classifier import BENCHES, harmful_harmbench_only, harmful_native
from v5lib.results_io import scan_results
from v5lib.safeio import read_json, write_json, write_text

_NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")
_LONG_TOKEN_RE = re.compile(r"\S{35,}")


def is_suspected_token_salad(response: str) -> bool:
    """英語プロンプトに対する応答が、多言語文字化け・無空白トークン崩壊に該当するかを判定する。

    - 非 ASCII 文字が 3 文字以上含まれる（かつ非 ASCII 比率 >= 3%）、または
    - 空白を含まない 35 文字以上の連続文字列がある（URL を除く）。
    """
    text = (response or "").strip()
    if not text:
        return False
    non_ascii = len(_NON_ASCII_RE.findall(text))
    if non_ascii >= 3 and (non_ascii / max(len(text), 1)) >= 0.03:
        return True
    cleaned = re.sub(r"https?://\S+", "", text)
    if _LONG_TOKEN_RE.search(cleaned):
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--out", default=str(DEFAULT_OUT / "probe"))
    args = ap.parse_args()

    scan = scan_results(args.results_root)
    agg: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    samples: dict[tuple[str, str], list[dict]] = defaultdict(list)
    inputs: list[str] = []

    for f in scan.files:
        if f.kind != "main" or f.family != "safety" or f.bench not in BENCHES:
            continue
        if f.alpha is not None and abs(f.alpha - args.alpha) > 1e-9:
            continue
        data = read_json(f.path)
        rows = data.get("results", [])
        if not isinstance(rows, list) or not rows:
            continue
        inputs.append(f.path)
        key = (f.pattern, f.method)
        st = agg[key]
        for r in rows:
            if not isinstance(r, dict):
                continue
            st["total"] += 1
            if r.get("is_gibberish", False):
                st["flagged_gibberish"] += 1
                continue
            st["valid_by_rule"] += 1
            resp = str(r.get("response", ""))
            salad = is_suspected_token_salad(resp)
            nat = harmful_native(f.bench, r)
            hb = harmful_harmbench_only(r)
            if salad:
                st["suspected_salad_in_valid"] += 1
            if nat and not hb:
                st["disagree_native_only"] += 1
                if salad:
                    st["disagree_and_salad"] += 1
                    if len(samples[key]) < 2:
                        samples[key].append({"bench": f.bench, "seed": f.seed, "response_head": resp[:100]})
            if hb:
                st["harmful_hb"] += 1
            if nat:
                st["harmful_native"] += 1

    out_rows = []
    lines = [
        f"#### ルールベース gibberish 判定（is_gibberish=False）のすり抜けと分類器乖離（α={args.alpha}）",
        "",
        "注: 探索用。`is_gibberish=False` の応答のうち、非 ASCII 混入（3 文字以上かつ 3% 以上）または URL 以外の 35 文字以上の無空白連続を「文字化け崩壊の疑い」と集計。",
        "",
        "| Pattern | Method | Valid件数 | 崩壊疑い (% of Valid) | Native有害かつHB無害 (件) | そのうち崩壊疑い (%) |",
        "|:---|:---|---:|---:|---:|---:|",
    ]
    for (pattern, method), st in sorted(agg.items()):
        valid = st["valid_by_rule"]
        salad = st["suspected_salad_in_valid"]
        dis = st["disagree_native_only"]
        dis_salad = st["disagree_and_salad"]
        salad_pct = (100.0 * salad / valid) if valid else 0.0
        dis_salad_pct = (100.0 * dis_salad / dis) if dis else 0.0
        out_rows.append({
            "pattern": pattern,
            "method": method,
            "total": st["total"],
            "valid_by_rule": valid,
            "suspected_salad_in_valid": salad,
            "suspected_salad_pct": salad_pct,
            "disagree_native_only": dis,
            "disagree_and_salad": dis_salad,
            "disagree_salad_pct": dis_salad_pct,
            "samples": samples[(pattern, method)],
        })
        lines.append(
            f"| {pattern} | {method} | {valid} | {salad_pct:.1f}% ({salad}) | {dis} | {dis_salad_pct:.1f}% ({dis_salad}) |"
        )

    out = Path(args.out)
    write_json(out / "gibberish_escape_probe.json", {"alpha": args.alpha, "rows": out_rows, "inputs": sorted(set(inputs))})
    write_text(out / "gibberish_escape_probe.md", "\n".join(lines) + "\n")
    print(f"書き込み: {out / 'gibberish_escape_probe.md'}（{len(out_rows)} 行、入力 {len(set(inputs))} ファイル）")


if __name__ == "__main__":
    main()
