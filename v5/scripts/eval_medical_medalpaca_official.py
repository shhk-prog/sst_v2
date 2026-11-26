#!/usr/bin/env python3
"""指示書 v2 §2.2 / §2.5 #3: MedAlpaca-7B 公式医療有用性検証ゲート（MedQA-USMLE 4-options, vLLM）。

目的:
  v3 の lm-eval 設定（### Instruction: ラップ対数尤度）では MedAlpaca-7B 単体が
  MedQA-4options 31.88%（SafetyFT 29.06% と僅差）、PubMedQA 73.75%（SafetyFT 84.38% より低い）だった。
  MedAlpaca 公式プロンプト（kbressem/medAlpaca: Context / Question / Answer: 形式）を用いて
  ベース（Llama-2-7b-hf）・SafetyFT_seed42・MedAlpaca-7B を生成評価し、
  指示書 v2 §2.2 の検証ゲート（ベース以上・抽出失敗率 < 5%・無作為 20 件の全文目視確認表生成）を行う。

制約:
  - --run-dir（RUN.md 存在必須）配下の outputs/ に全件応答・判定結果・全文 20 件目視表を保存する。
  - v3/ は一切変更しない。
"""

from __future__ import annotations

import argparse
import collections
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))

from v5lib.safeio import write_json, write_text  # noqa: E402

LETTERS = ("A", "B", "C", "D")

MEDALPACA_PROMPTS = {
    "official_qa": (
        "Context: You are a medical expert answering a USMLE multiple-choice question. "
        "Select the single best option (A, B, C, or D).\n\n"
        "Question: {question}\n"
        "Options:\n"
        "A. {opt_a}\n"
        "B. {opt_b}\n"
        "C. {opt_c}\n"
        "D. {opt_d}\n\n"
        "Answer:"
    ),
    "plain_qa": (
        "Question: {question}\n"
        "A. {opt_a}\n"
        "B. {opt_b}\n"
        "C. {opt_c}\n"
        "D. {opt_d}\n"
        "Answer:"
    ),
}

_ANSWER_RE_LIST = [
    re.compile(r"(?:the\s+(?:correct\s+)?answer\s+is|answer\s*[:\-])\s*\(?([A-D])\)?(?:\b|[.\s])", re.IGNORECASE),
    re.compile(r"^\s*\(?([A-D])\)?(?:\s*[\.\):\-]|\s*$)", re.IGNORECASE),
    re.compile(r"\b(?:option|choice)\s*\(?([A-D])\)?\b", re.IGNORECASE),
    re.compile(r"\b([A-D])\b"),
]


def build_medqa_prompt(item: dict[str, Any], variant: str = "official_qa") -> str:
    q = (str(item.get("sent1", "")) + (" " + str(item.get("sent2", "")) if item.get("sent2") else "")).strip()
    return MEDALPACA_PROMPTS[variant].format(
        question=q,
        opt_a=str(item["ending0"]).strip(),
        opt_b=str(item["ending1"]).strip(),
        opt_c=str(item["ending2"]).strip(),
        opt_d=str(item["ending3"]).strip(),
    )


def extract_mc_choice(raw_response: str, options: list[str] | None = None) -> tuple[str | None, str]:
    """モデル応答から A/B/C/D を抽出する（テキスト直接一致フォールバック付き）。"""
    text = (raw_response or "").strip()
    if not text:
        return None, "empty"

    # 先頭行・全体に対して優先順位付きパターン照合
    first_line = text.splitlines()[0].strip()
    for idx, rx in enumerate(_ANSWER_RE_LIST[:2]):
        m = rx.search(first_line)
        if m:
            return m.group(1).upper(), f"first_line_r{idx}"
    for idx, rx in enumerate(_ANSWER_RE_LIST[:3]):
        m = rx.search(text)
        if m:
            return m.group(1).upper(), f"full_r{idx}"

    # 選択肢本文の完全/先頭一致（大文字小文字無視）
    if options:
        low = text.lower()
        hits = []
        for i, opt in enumerate(options[:4]):
            o_clean = opt.strip().lower()
            if len(o_clean) >= 4 and o_clean in low:
                hits.append(LETTERS[i])
        if len(hits) == 1:
            return hits[0], "option_text_match"

    m = _ANSWER_RE_LIST[3].search(first_line)
    if m:
        return m.group(1).upper(), "bare_letter_first_line"
    return None, "no_choice_found"


def evaluate_med_gate(
    *,
    model_name: str,
    acc_pct: float,
    extraction_fail_pct: float,
    max_choice_freq_pct: float,
    base_acc_pct: float | None,
    official_value: float | None = None,
) -> dict[str, Any]:
    """指示書 v2 §2.2 の医療多肢選択ゲート。4択は均等で25%のため偏り上限は60%で警告・記録。"""
    checks: dict[str, dict[str, Any]] = {}
    if official_value is not None:
        diff = abs(acc_pct - official_value)
        checks["official_diff_le_5pp"] = {
            "pass": diff <= 5.0,
            "value": round(diff, 2),
            "threshold": "<= 5.0 pp",
        }
    if base_acc_pct is not None:
        checks["ge_base"] = {
            "pass": acc_pct >= base_acc_pct,
            "value": round(acc_pct - base_acc_pct, 2),
            "threshold": ">= base",
            "detail": f"measured={acc_pct:.2f}% vs base={base_acc_pct:.2f}%",
        }
    checks["extraction_fail_lt_5pct"] = {
        "pass": extraction_fail_pct < 5.0,
        "value": round(extraction_fail_pct, 2),
        "threshold": "< 5.0%",
    }
    checks["choice_collapse_lt_60pct"] = {
        "pass": max_choice_freq_pct < 60.0,
        "value": round(max_choice_freq_pct, 2),
        "threshold": "< 60.0% (4択の単一選択肢崩壊検出)",
    }
    return {
        "model_name": model_name,
        "all_auto_checks_pass": all(c["pass"] for c in checks.values()),
        "checks": checks,
    }


def write_samples_review_full(results: list[dict[str, Any]], out_md: Path, title: str, seed: int = 20261126, k: int = 20) -> None:
    rng = random.Random(seed)
    chosen = rng.sample(results, min(k, len(results)))
    lines = [
        f"# MedQA-4options 無作為 20 件目視確認表（全文）: `{title}`（指示書 v2 §2.2）",
        "",
        f"- 抽出 seed: `{seed}` / 件数: `{len(chosen)}` / 全件数: `{len(results)}`",
        "- 人が確認したら `RUN.md` に「確認済み」と追記すること。",
        "",
    ]
    for idx, r in enumerate(chosen, 1):
        lines += [
            f"## {idx}. `doc_{r['doc_id']}` — {'PASS' if r['correct'] else 'FAIL'} (pred=`{r['pred']}`, gold=`{r['gold']}`, mode=`{r['extract_mode']}`)",
            "",
            "**Question (先頭 300 文字):**",
            "```text",
            str(r["question"])[:300],
            "```",
            "**Raw response (全文):**",
            "```text",
            str(r["raw_response"]),
            "```",
            "",
        ]
    write_text(out_md, "\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--model-path", type=str, required=True)
    ap.add_argument("--model-name", type=str, required=True)
    ap.add_argument("--prompt-variant", choices=tuple(MEDALPACA_PROMPTS.keys()), default="official_qa")
    ap.add_argument("--limit", type=int, default=320)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    ap.add_argument("--base-acc", type=float, default=None)
    args = ap.parse_args()

    if not (args.run_dir / "RUN.md").is_file():
        raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")

    from datasets import load_dataset
    from vllm import LLM, SamplingParams

    ds = load_dataset("GBaker/MedQA-USMLE-4-options-hf", split="test")
    items = [dict(ds[i]) for i in range(min(args.limit, len(ds)))]
    prompts = [build_medqa_prompt(it, variant=args.prompt_variant) for it in items]

    t0 = time.time()
    llm = LLM(
        model=args.model_path,
        dtype="float16",
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=2048,
        trust_remote_code=False,
    )
    sp = SamplingParams(
        temperature=0.0,
        top_p=1.0,
        max_tokens=args.max_tokens,
        stop=["</s>", "\nQuestion:", "\nContext:"],
    )
    outputs = llm.generate(prompts, sp)
    gen_sec = time.time() - t0

    results = []
    n_correct = 0
    n_ext_fail = 0
    preds: list[str] = []
    for doc_id, (it, out) in enumerate(zip(items, outputs)):
        raw = out.outputs[0].text if out.outputs else ""
        opts = [str(it[f"ending{j}"]) for j in range(4)]
        gold_idx = int(it["label"])
        gold = LETTERS[gold_idx]
        pred, mode = extract_mc_choice(raw, opts)
        if pred is None:
            n_ext_fail += 1
        else:
            preds.append(pred)
        correct = pred == gold
        if correct:
            n_correct += 1
        results.append({
            "doc_id": doc_id,
            "id": it.get("id", str(doc_id)),
            "question": str(it.get("sent1", "")),
            "gold": gold,
            "pred": pred,
            "correct": correct,
            "extract_mode": mode,
            "raw_response": raw,
        })

    n_total = len(results)
    acc_pct = 100.0 * n_correct / n_total if n_total else 0.0
    ext_fail_pct = 100.0 * n_ext_fail / n_total if n_total else 0.0
    choice_counts = dict(collections.Counter(preds))
    max_choice_pct = 100.0 * max(choice_counts.values(), default=0) / n_total if n_total else 0.0

    gate = evaluate_med_gate(
        model_name=args.model_name,
        acc_pct=acc_pct,
        extraction_fail_pct=ext_fail_pct,
        max_choice_freq_pct=max_choice_pct,
        base_acc_pct=args.base_acc,
    )

    out_dir = args.run_dir / "outputs"
    out_json = out_dir / f"{args.model_name}_medqa_{args.prompt_variant}.json"
    payload = {
        "completed": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": args.model_name,
        "model_path": args.model_path,
        "prompt_variant": args.prompt_variant,
        "n_total": n_total,
        "n_correct": n_correct,
        "medqa_acc_pct": acc_pct,
        "extraction_fail_pct": ext_fail_pct,
        "choice_distribution": choice_counts,
        "max_choice_freq_pct": max_choice_pct,
        "gen_seconds": round(gen_sec, 2),
        "gate": gate,
        "results": results,
    }
    write_json(out_json, payload)
    write_samples_review_full(results, out_dir / f"{args.model_name}_{args.prompt_variant}_samples_review_full.md", f"{args.model_name} ({args.prompt_variant})")
    print(
        f"[DONE] {args.model_name} ({args.prompt_variant}): MedQA acc = {acc_pct:.2f}% ({n_correct}/{n_total}), "
        f"ext_fail={ext_fail_pct:.2f}%, choices={choice_counts}, gate_pass={gate['all_auto_checks_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
