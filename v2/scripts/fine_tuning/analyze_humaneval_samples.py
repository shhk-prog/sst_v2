#!/usr/bin/env python3
"""
HumanEval samples_*.jsonl の失敗パターンを分類してサマリを出力する。

Usage:
  # glob はクォートで囲む（シェル展開に任せる場合はクォート不要）
  python analyze_humaneval_samples.py \
    '../../results/lm_eval_raw/coding_lora_with_template_base/coding/*/samples_humaneval_*.jsonl'

  python analyze_humaneval_samples.py --compare file_a.jsonl file_b.jsonl \
    --label-a unclean --label-b clean

  # モデル名から最新ファイルを自動検出
  python analyze_humaneval_samples.py --model coding_lora_python coding_lora_clean
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path


def flatten_resp(x) -> str:
    while isinstance(x, list) and x:
        x = x[0]
    return x if isinstance(x, str) else str(x)


def classify_failure(gen: str) -> str:
    g = gen.strip()
    if not g:
        return "empty"
    if re.search(r"(.)\1{8,}", g):
        return "repetition_collapse"
    if "```" in g:
        return "markdown_wrapped"
    if any(
        x in g[:150].lower()
        for x in ["here is", "solution", "sure", "let's", "following", "i'll", "we need"]
    ):
        return "natural_lang_prefix"
    if "\ndef " in g[:300] and not g.lstrip().startswith("def "):
        return "truncated_by_until"
    if g.startswith("class ") and not g.startswith("def "):
        return "wrong_language"
    return "logic_error"


def load_samples(path: Path) -> dict[int, dict]:
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rows[row["doc_id"]] = row
    return rows


def summarize(path: Path, label: str | None = None) -> dict:
    label = label or path.name
    passed = failed = 0
    fail_cats: dict[str, int] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            gen = flatten_resp(row.get("filtered_resps") or row.get("resps"))
            ok = bool(row.get("pass@1", 0))
            if ok:
                passed += 1
            else:
                failed += 1
                cat = classify_failure(gen)
                fail_cats[cat] = fail_cats.get(cat, 0) + 1

    total = passed + failed
    print(f"\n=== {label} ===")
    print(f"  path   : {path}")
    print(f"  pass@1 : {passed}/{total} ({100 * passed / total:.1f}%)")
    print("  fail breakdown:")
    for cat, n in sorted(fail_cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<22} {n:4d} ({100 * n / failed:.1f}% of fails)" if failed else f"    {cat}")
    return {"label": label, "passed": passed, "total": total, "fail_cats": fail_cats}


def compare(path_a: Path, path_b: Path, label_a: str, label_b: str) -> None:
    a, b = load_samples(path_a), load_samples(path_b)
    regress = improve = 0
    regress_cats: dict[str, int] = {}
    for doc_id, ra in a.items():
        if doc_id not in b:
            continue
        pa, pb = bool(ra.get("pass@1")), bool(b[doc_id].get("pass@1"))
        if pa and not pb:
            regress += 1
            gen = flatten_resp(b[doc_id].get("filtered_resps") or b[doc_id].get("resps"))
            cat = classify_failure(gen)
            regress_cats[cat] = regress_cats.get(cat, 0) + 1
        elif pb and not pa:
            improve += 1
    print(f"\n=== Compare: {label_a} -> {label_b} ===")
    print(f"  regress (A pass, B fail): {regress}")
    print(f"  improve (A fail, B pass): {improve}")
    if regress_cats:
        print("  regress fail categories in B:")
        for cat, n in sorted(regress_cats.items(), key=lambda x: -x[1]):
            print(f"    {cat:<22} {n}")


def expand_sample_paths(patterns: list[str]) -> list[Path]:
    """パス / glob を実ファイル一覧に展開。最新1件だけ欲しい場合は呼び出し側で絞る。"""
    found: list[Path] = []
    for raw in patterns:
        if "*" in raw or "?" in raw:
            matches = sorted(glob.glob(raw, recursive=True))
            if not matches:
                raise FileNotFoundError(
                    f"No files matched glob: {raw}\n"
                    "ヒント: '...' はプレースホルダーです。'*' を使ってください。"
                )
            found.extend(Path(m) for m in matches)
        else:
            p = Path(raw)
            if not p.exists():
                raise FileNotFoundError(f"File not found: {raw}")
            found.append(p)
    return found


def latest_humaneval_for_model(model_name: str, lm_eval_root: Path) -> Path:
    """lm_eval_raw/<model_name>/coding/**/samples_humaneval_*.jsonl の最新を返す。"""
    pattern = str(lm_eval_root / model_name / "coding" / "**" / "samples_humaneval_*.jsonl")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        raise FileNotFoundError(
            f"No samples_humaneval_*.jsonl under {lm_eval_root / model_name}/coding/"
        )
    return Path(max(matches, key=lambda m: Path(m).stat().st_mtime))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "samples",
        nargs="*",
        help="samples_humaneval_*.jsonl（glob 可。例: '../../results/lm_eval_raw/foo/coding/*/samples_humaneval_*.jsonl'）",
    )
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"), help="2 files to compare")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    parser.add_argument(
        "--model",
        nargs="+",
        metavar="MODEL_NAME",
        help="lm_eval_raw 配下の model_name から最新 humaneval jsonl を自動選択",
    )
    parser.add_argument(
        "--lm-eval-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "results" / "lm_eval_raw",
    )
    args = parser.parse_args()

    if args.compare:
        paths = expand_sample_paths(list(args.compare))
        compare(paths[0], paths[1], args.label_a, args.label_b)
        return

    paths: list[Path] = []
    if args.model:
        for name in args.model:
            paths.append(latest_humaneval_for_model(name, args.lm_eval_root))
    if args.samples:
        paths.extend(expand_sample_paths(args.samples))

    if not paths:
        parser.error(
            "samples path, --model, or --compare required.\n"
            "例: python analyze_humaneval_samples.py --model coding_lora_with_template_base coding_lora_clean"
        )

    for p in paths:
        summarize(p)


if __name__ == "__main__":
    main()
