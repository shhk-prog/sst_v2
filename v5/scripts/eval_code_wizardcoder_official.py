#!/usr/bin/env python3
"""指示書 v2 §2.2 / §2.5 #1: WizardCoder-Python-7B-V1.0 公式 Alpaca-Code HumanEval 検証ゲート（vLLM）。

目的:
  v3 の lm-eval 設定では WizardCoder 単体の HumanEval が 5.49%（Code Avg 21.03%）に崩壊していた。
  公式リポジトリ（WizardLM/WizardCoder `humaneval_gen.py` + `process_humaneval.py`）の
  プロンプト形式とコード抽出を用いて専門モデル単体（＋ベース・SafetyFT）を評価し、
  指示書 v2 §2.2 の全検証ゲート（公式値 55.5% との差 <= 5pp、ベース以上、抽出失敗率 < 5%、
  抽出値偏り < 10%、無作為 20 件の目視確認表 `samples_review.md` 生成）を自動判定する。

制約:
  - --run-dir（RUN.md 存在必須）配下の outputs/ に全件応答・判定結果・samples_review.md を保存する。
  - v3/ は一切変更しない。
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))

from v5lib.safeio import write_json, write_text  # noqa: E402

# WizardCoder 公式 HumanEval プロンプト（WizardLM/WizardCoder src/humaneval_gen.py）
WIZARDCODER_PROMPTS = {
    "official_tab_nl": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n\n"
        "### Instruction:\n"
        "Create a Python script for this problem:\n"
        "{prompt}\n\n"
        "### Response:\n"
    ),
    "official_spaces_nl": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n"
        "Create a Python script for this problem:\n"
        "{prompt}\n\n"
        "### Response:\n"
    ),
    "alpaca_direct_nl": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n"
        "{prompt}\n\n"
        "### Response:\n"
    ),
}

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def build_wizardcoder_prompt(humaneval_prompt: str, variant: str = "official_tab_nl") -> str:
    tpl = WIZARDCODER_PROMPTS[variant]
    p = humaneval_prompt.replace("    ", "\t") if variant == "official_tab_nl" else humaneval_prompt
    return tpl.format(prompt=p)


def extract_python_solution(raw_response: str, humaneval_prompt: str, entry_point: str) -> tuple[str | None, str]:
    """WizardCoder の応答から実行可能な Python 関数定義コードを抽出する（補助関数・import 保持対応）。

    Returns:
      (full_executable_code_or_None, extractor_mode)
    """
    text = (raw_response or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return None, "empty"

    # 1) ```python ... ``` フェンス優先
    m = _CODE_FENCE_RE.search(text)
    if m:
        body = m.group(1).strip()
        mode = "code_fence"
    else:
        # 2) フェンスなしの場合: 最初の def / import / from / class 行から開始し、
        #    entry_point より前に定義された補助関数（is_prime, encode_cyclic 等）を保持する。
        lines = text.splitlines()
        start = None
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith(("def ", "import ", "from ", "class ")):
                start = i
                break
        if start is not None:
            kept: list[str] = []
            seen_entry = False
            for ln in lines[start:]:
                s = ln.strip()
                if s.startswith(("if __name__", "# Example", "# Test", "assert ", "print(")):
                    break
                if f"def {entry_point}" in s:
                    seen_entry = True
                if seen_entry and ln and not ln[0].isspace() and not s.startswith(("def ", "import ", "from ", "class ", "@", "#", ")", "]", "}")):
                    # 関数定義後に続く自然言語解説文で終了
                    break
                kept.append(ln)
            body = "\n".join(kept).rstrip()
            mode = "raw_def"
        elif "return " in text or "\n    " in text or "\n\t" in text:
            indented = text if text.startswith((" ", "\t")) else "\n".join("    " + ln if ln.strip() else "" for ln in text.splitlines())
            return humaneval_prompt + "\n" + indented + "\n", "body_continuation"
        else:
            return None, "no_code_found"

    # テストコードや末尾解説が混ざった場合は切る
    cut_markers = ("\nif __name__", "\n# Example", "\n# Test", "\nassert ")
    for mk in cut_markers:
        pos = body.find(mk)
        if pos != -1:
            body = body[:pos].rstrip()

    # タブインデントを 4 スペースへ正規化（混在による TabError 回避）
    body = body.replace("\t", "    ")

    # prompt 側で entry_point より前に定義された import や補助関数（例: poly, encode_cyclic）を前置き
    idx_entry = humaneval_prompt.find(f"def {entry_point}")
    prompt_prefix = humaneval_prompt[:idx_entry].rstrip() if idx_entry > 0 else ""
    if f"def {entry_point}" in body:
        header = (prompt_prefix + "\n\n") if prompt_prefix else ""
        return header + body + "\n", mode

    indented = body if body.startswith((" ", "\t")) else "\n".join("    " + ln if ln.strip() else "" for ln in body.splitlines())
    return humaneval_prompt + "\n" + indented + "\n", f"{mode}_continuation"


def run_humaneval_unit_test(solution_code: str, test_code: str, entry_point: str, timeout_sec: float = 5.0) -> tuple[bool, str]:
    """隔離サブプロセスで HumanEval 単体テストを実行する。"""
    full_script = f"{solution_code}\n\n{test_code}\n\ncheck({entry_point})\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(full_script)
        tf_path = tf.name
    try:
        proc = subprocess.run(
            [sys.executable, tf_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if proc.returncode == 0:
            return True, "passed"
        err_tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return False, err_tail[-1][:200] if err_tail else f"exit_{proc.returncode}"
    except subprocess.TimeoutExpired:
        return False, f"timeout_{timeout_sec}s"
    except Exception as exc:
        return False, f"exec_error:{exc}"
    finally:
        try:
            os.unlink(tf_path)
        except OSError:
            pass


def evaluate_gate(
    *,
    model_name: str,
    pass1_pct: float,
    extraction_fail_pct: float,
    mode_skew_pct: float,
    official_value: float | None,
    base_pass1_pct: float | None,
) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    if official_value is not None:
        diff = abs(pass1_pct - official_value)
        checks["official_diff_le_5pp"] = {
            "pass": diff <= 5.0,
            "value": round(diff, 2),
            "threshold": "<= 5.0 pp",
            "detail": f"measured={pass1_pct:.2f}% vs official={official_value:.2f}%",
        }
    if base_pass1_pct is not None:
        checks["ge_base"] = {
            "pass": pass1_pct >= base_pass1_pct,
            "value": round(pass1_pct - base_pass1_pct, 2),
            "threshold": ">= base",
            "detail": f"measured={pass1_pct:.2f}% vs base={base_pass1_pct:.2f}%",
        }
    checks["extraction_fail_lt_5pct"] = {
        "pass": extraction_fail_pct < 5.0,
        "value": round(extraction_fail_pct, 2),
        "threshold": "< 5.0%",
    }
    checks["extraction_skew_lt_10pct"] = {
        "pass": mode_skew_pct < 10.0,
        "value": round(mode_skew_pct, 2),
        "threshold": "< 10.0%",
    }
    all_pass = all(c["pass"] for c in checks.values())
    return {"model_name": model_name, "all_auto_checks_pass": all_pass, "checks": checks}


def write_samples_review(results: list[dict[str, Any]], out_md: Path, model_name: str, seed: int = 20261126, k: int = 20) -> None:
    rng = random.Random(seed)
    chosen = rng.sample(results, min(k, len(results)))
    lines = [
        f"# HumanEval 無作為 20 件目視確認表: `{model_name}`（指示書 v2 §2.2）",
        "",
        f"- 抽出 seed: `{seed}` / 件数: `{len(chosen)}` / 全件数: `{len(results)}`",
        "- 人が確認したら `RUN.md` に「確認済み」と追記すること。",
        "",
    ]
    for idx, r in enumerate(chosen, 1):
        lines += [
            f"## {idx}. `{r['task_id']}` (`entry_point={r['entry_point']}`) — {'PASS' if r['passed'] else 'FAIL'} (`{r['exec_status']}`, mode=`{r['extract_mode']}`, raw_chars=`{len(str(r['raw_response']))}`)",
            "",
            "**Raw response (全文):**",
            "```text",
            str(r["raw_response"]),
            "```",
            "**Extracted code (全文):**",
            "```python",
            str(r.get("extracted_code") or ""),
            "```",
            "",
        ]
    write_text(out_md, "\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--model-path", type=str, required=True)
    ap.add_argument("--model-name", type=str, required=True)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--prompt-variant", choices=tuple(WIZARDCODER_PROMPTS.keys()), default="official_tab_nl")
    ap.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    ap.add_argument("--official-value", type=float, default=None, help="公式 HumanEval pass@1 (%)。WizardCoder は 55.5")
    ap.add_argument("--base-pass1", type=float, default=None, help="ベースモデルの pass@1 (%)")
    ap.add_argument("--limit", type=int, default=164)
    args = ap.parse_args()

    if not (args.run_dir / "RUN.md").is_file():
        raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")

    out_dir = args.run_dir / "outputs"
    out_json = out_dir / f"{args.model_name}_humaneval_{args.prompt_variant}.json"

    from datasets import load_dataset
    from vllm import LLM, SamplingParams

    ds = load_dataset("openai_humaneval", split="test")
    items = [dict(ds[i]) for i in range(min(args.limit, len(ds)))]
    prompts = [build_wizardcoder_prompt(it["prompt"], variant=args.prompt_variant) for it in items]

    t0 = time.time()
    llm = LLM(
        model=args.model_path,
        dtype="float16",
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=4096,
        trust_remote_code=False,
    )
    sp = SamplingParams(
        temperature=0.0,
        top_p=1.0,
        max_tokens=args.max_tokens,
        stop=["</s>", "### Instruction:", "### Response:"],
    )
    outputs = llm.generate(prompts, sp)
    gen_sec = time.time() - t0

    results = []
    n_pass = 0
    n_ext_fail = 0
    extracted_hashes: list[str] = []
    for it, out in zip(items, outputs):
        raw = out.outputs[0].text if out.outputs else ""
        code, mode = extract_python_solution(raw, it["prompt"], it["entry_point"])
        if code is None:
            n_ext_fail += 1
            passed, status = False, f"extract_fail:{mode}"
            extracted_hashes.append("__EXTRACT_FAIL__")
        else:
            passed, status = run_humaneval_unit_test(code, it["test"], it["entry_point"])
            extracted_hashes.append(code.strip())
        if passed:
            n_pass += 1
        results.append({
            "task_id": it["task_id"],
            "entry_point": it["entry_point"],
            "prompt": it["prompt"],
            "raw_response": raw,
            "extracted_code": code,
            "extract_mode": mode,
            "passed": passed,
            "exec_status": status,
        })

    n_total = len(results)
    pass1_pct = 100.0 * n_pass / n_total if n_total else 0.0
    ext_fail_pct = 100.0 * n_ext_fail / n_total if n_total else 0.0
    non_fail = [h for h in extracted_hashes if h != "__EXTRACT_FAIL__"]
    top_count = collections.Counter(non_fail).most_common(1)[0][1] if non_fail else 0
    mode_skew_pct = 100.0 * top_count / n_total if n_total else 0.0

    gate = evaluate_gate(
        model_name=args.model_name,
        pass1_pct=pass1_pct,
        extraction_fail_pct=ext_fail_pct,
        mode_skew_pct=mode_skew_pct,
        official_value=args.official_value,
        base_pass1_pct=args.base_pass1,
    )

    payload = {
        "completed": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": args.model_name,
        "model_path": args.model_path,
        "prompt_template": f"WizardCoder_{args.prompt_variant}",
        "n_total": n_total,
        "n_pass": n_pass,
        "humaneval_pass1_pct": pass1_pct,
        "extraction_fail_pct": ext_fail_pct,
        "extraction_mode_skew_pct": mode_skew_pct,
        "gen_seconds": round(gen_sec, 2),
        "gate": gate,
        "results": results,
    }
    write_json(out_json, payload)
    write_samples_review(results, out_dir / f"{args.model_name}_{args.prompt_variant}_samples_review.md", f"{args.model_name} ({args.prompt_variant})")
    print(
        f"[DONE] {args.model_name}: HumanEval pass@1 = {pass1_pct:.2f}% ({n_pass}/{n_total}), "
        f"ext_fail={ext_fail_pct:.2f}%, skew={mode_skew_pct:.2f}%, gate_pass={gate['all_auto_checks_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
