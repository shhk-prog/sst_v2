"""
Utility Evaluation Script — lm-evaluation-harness ベース (トップ会議準拠)

採用ベンチマーク:
  [金融モデル向け]
    - mmlu_business_ethics          (5-shot, multiple_choice)
    - mmlu_high_school_macroeconomics (5-shot, multiple_choice)
    - mmlu_econometrics             (5-shot, multiple_choice)
    ※ MERGE ALIGN (Arxiv 2024) が Finance ドメイン評価に使用

  [コーディングモデル向け]
    - humaneval   (pass@1, 0-shot)  LED-Merging (ACL 2025)
    - mbpp        (pass@1, 3-shot)  LED-Merging (ACL 2025)
    - gsm8k_cot_zeroshot (exact_match)  SafeMERGE (ICLR 2025), LED-Merging (ACL 2025)

  [汎用ベースライン — 全モデル共通]
    - arc_challenge  (25-shot)      LED-Merging, SafeMERGE 等多数
    - hellaswag      (10-shot)      汎用能力の退化を検出するために使用

評価基盤:
  EleutherAI lm-evaluation-harness (https://github.com/EleutherAI/lm-evaluation-harness)
  採用論文: LED-Merging (ACL 2025), SafeMERGE (ICLR 2025), FIM-TIES (Arxiv 2026) 他

Usage:
  python run_utility_eval.py \
    --base_model meta-llama/Meta-Llama-3-8B-Instruct \
    --adapter_path ../../models/Llama-3-8B/<RUN_NAME>/coding_lora \
    --model_name utility_lora \
    --eval_type finance \
    --output_json ../../results/phase2_eval_results.json
"""

import os
import json
import argparse
import subprocess
from pathlib import Path

from transformers import AutoTokenizer

from chat_template_utils import get_custom_chat_template

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/src/.env"))
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
V2_ROOT = SCRIPT_DIR.parent.parent
HF_CACHE_ROOT = V2_ROOT / ".cache" / "huggingface"


def lm_eval_env() -> dict[str, str]:
    """lm_eval 子プロセス用: HF キャッシュを v2/.cache に固定（NFS パス不整合対策）。"""
    env = os.environ.copy()
    HF_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    for key in ("HF_HOME", "HF_METRICS_CACHE", "HF_DATASETS_CACHE", "HF_HUB_CACHE"):
        env[key] = str(HF_CACHE_ROOT)
    env["HF_METRICS_CACHE"] = str(HF_CACHE_ROOT / "metrics")
    return env

# コーディング評価 (HumanEval 等) でのコード実行を許可
# Ref: https://huggingface.co/docs/evaluate/v0.4.0/en/package_reference/main_classes#evaluate.load
os.environ["HF_ALLOW_CODE_EVAL"] = "1"

# ──────────────────────────────────────────
# タスク定義 (先行研究準拠)
# ──────────────────────────────────────────

# 金融ドメイン評価 (MMLU finance subcategories)
# Ref: MERGE ALIGN (Arxiv 2024) — Finance domain utility
FINANCE_TASKS = {
    "mmlu_business_ethics":              {"num_fewshot": 5},
    "mmlu_high_school_macroeconomics":   {"num_fewshot": 5},
    "mmlu_econometrics":                 {"num_fewshot": 5},
}

# コーディング評価
# Ref: LED-Merging (ACL 2025) — HumanEval-Pack + MBPP + GSM8K
CODING_TASKS = {
    "humaneval":            {"num_fewshot": 0},   # pass@1
    "mbpp":                 {"num_fewshot": 3, "no_chat_template": True},   # pass@1
    "gsm8k_cot_zeroshot":   {"num_fewshot": 0},   # exact_match (CoT)
}

# 汎用 (全モデル共通)
# Ref: SafeMERGE, LED-Merging, FIM-TIES 等
GENERAL_TASKS = {
    "arc_challenge":  {"num_fewshot": 25},
    "hellaswag":      {"num_fewshot": 10},
}

TASK_CONFIGS = {
    "finance": FINANCE_TASKS,
    "coding":  CODING_TASKS,
    "general": GENERAL_TASKS,
}


def _adapter_path_candidates(adapter_path: str) -> list[Path]:
    """cwd / スクリプト基準の候補 + results→models のよくある誤指定フォールバック。"""
    paths = [adapter_path]
    normalized = adapter_path.replace("\\", "/")
    if "/results/" in normalized:
        paths.append(adapter_path.replace("results", "models", 1))
    seen: set[str] = set()
    candidates: list[Path] = []
    for raw in paths:
        if raw in seen:
            continue
        seen.add(raw)
        p = Path(raw)
        candidates.extend([p, Path.cwd() / raw, SCRIPT_DIR / raw])
    return candidates


def resolve_adapter_path(adapter_path: str | None) -> Path | None:
    """相対パスを cwd / スクリプト基準で解決する。"""
    if not adapter_path:
        return None
    for p in _adapter_path_candidates(adapter_path):
        if p.exists():
            if "models" in str(p) and "results" in adapter_path.replace("\\", "/"):
                print(f"  [INFO] adapter_path resolved (models/): {p.resolve()}")
            return p.resolve()
    print(f"  [WARNING] adapter_path not found (LoRA will be skipped): {adapter_path}")
    if "results" in adapter_path:
        hint = adapter_path.replace("results", "models", 1)
        print(f"  [HINT] LoRA は models/ 配下に保存されます。例: --adapter_path {hint}")
    return None


def prepare_tokenizer_path(
    base_model: str,
    adapter_path: Path | None,
    cache_dir: Path,
) -> str:
    """--apply_chat_template 用に chat_template 付き tokenizer のパスを返す。"""
    load_from = str(adapter_path) if adapter_path else base_model
    tokenizer = AutoTokenizer.from_pretrained(load_from)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if tokenizer.chat_template is None:
        tokenizer.chat_template = get_custom_chat_template(base_model)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tokenizer.save_pretrained(cache_dir)
        print(f"  Saved tokenizer with chat_template to: {cache_dir}")
        return str(cache_dir.resolve())

    if adapter_path:
        return str(adapter_path.resolve())
    return load_from


def build_model_args(
    base_model: str,
    adapter_path: Path | None,
    tokenizer_path: str | None,
) -> str:
    parts = [f"pretrained={base_model}"]
    if adapter_path:
        parts.append(f"peft={adapter_path}")
    if tokenizer_path:
        parts.append(f"tokenizer={tokenizer_path}")
    parts.append("dtype=bfloat16")
    return ",".join(parts)


def run_lm_eval(
    base_model: str,
    adapter_path: str | None,
    task_configs: dict,
    output_dir: str,
    limit: int | None = None,
    batch_size: int = 4,
    apply_chat_template: bool = False,
    gen_kwargs: str | None = None,
) -> dict:
    """
    lm-evaluation-harness を実行し、results.json を返す。
    タスクごとに異なる num_fewshot を設定するため、同じ設定のタスクをグループ化して実行する。
    """
    # fewshot と no_chat_template ごとにタスクをグループ化
    run_groups = {}
    for task, config in task_configs.items():
        fs = config.get("num_fewshot", 0)
        no_tpl = config.get("no_chat_template", False)
        key = (fs, no_tpl)
        if key not in run_groups:
            run_groups[key] = []
        run_groups[key].append(task)

    all_results = {"results": {}, "git_hash": "unknown"}

    resolved_adapter = resolve_adapter_path(adapter_path)
    for (fs, no_tpl), tasks in run_groups.items():
        tasks_str = ",".join(tasks)
        
        # タスク側で no_chat_template が指定されていれば上書きで無効化
        use_template = apply_chat_template and not no_tpl
        
        tokenizer_path = None
        if use_template:
            tokenizer_path = prepare_tokenizer_path(
                base_model=base_model,
                adapter_path=resolved_adapter,
                cache_dir=Path(output_dir) / "_tokenizer",
            )
            
        model_args = build_model_args(base_model, resolved_adapter, tokenizer_path)

        cmd = [
            "lm_eval",
            "--model", "hf",
            "--model_args", model_args,
            "--tasks", tasks_str,
            "--num_fewshot", str(fs),
            "--output_path", output_dir,
            "--batch_size", str(batch_size),
            "--log_samples",
            "--confirm_run_unsafe_code",
        ]

        if use_template:
            cmd.append("--apply_chat_template")

        if gen_kwargs:
            cmd += ["--gen_kwargs", gen_kwargs]

        if limit:
            cmd += ["--limit", str(limit)]

        print(f"\n  Command (fewshot={fs}): {' '.join(cmd)}")
        result = subprocess.run(cmd, text=True, env=lm_eval_env())

        if result.returncode != 0:
            raise RuntimeError(f"lm_eval failed (fewshot={fs}, return code: {result.returncode})")

        # 直前の lm_eval 実行で書き込まれた results*.json を取得 (mtime 基準)
        results_files = list(Path(output_dir).rglob("results*.json"))
        if not results_files:
            raise FileNotFoundError(f"results*.json not found under {output_dir}")

        latest_results = max(results_files, key=lambda p: p.stat().st_mtime)
        with open(latest_results) as f:
            chunk = json.load(f)
            all_results["results"].update(chunk.get("results", {}))
            all_results["git_hash"] = chunk.get("git_hash", "unknown")

    return all_results


# lm_eval が複数 filter を返す場合の優先順 (先頭ほど優先)
_METRIC_FILTER_PREF: dict[str, list[str]] = {
    "exact_match": ["flexible-extract", "none", "strict-match"],
    "pass@1": ["create_test", "none"],
    "pass_at_1": ["none"],
}


def _pick_metric_key(task_result: dict, target: str) -> str | None:
    """タスク結果から採用するメトリクスキーを選ぶ (例: exact_match,flexible-extract)。"""
    candidates = [k for k in task_result if k.startswith(f"{target},")]
    if not candidates:
        return None
    prefs = _METRIC_FILTER_PREF.get(target, [])
    for pref in prefs:
        for k in candidates:
            if k.endswith(f",{pref}") or k == f"{target},{pref}":
                return k
    return candidates[0]


def extract_scores(lm_eval_results: dict, task_configs: dict) -> dict:
    """lm-evaluation-harness の results.json からタスクごとのスコアを抽出"""
    scores = {}
    results_raw = lm_eval_results.get("results", {})

    for task in task_configs:
        if task not in results_raw:
            print(f"  [WARNING] Task '{task}' not found in results")
            continue
        task_result = results_raw[task]

        # メトリクス名の優先順位: pass@1 / pass_at_1 → exact_match → acc_norm → acc
        for target in ["pass@1", "pass_at_1", "exact_match", "acc_norm", "acc"]:
            metric_key = _pick_metric_key(task_result, target)
            if metric_key is None:
                continue
            stderr_key = metric_key.split(",")[0] + "_stderr," + ",".join(metric_key.split(",")[1:])
            filter_name = metric_key.split(",", 1)[1] if "," in metric_key else "none"
            scores[task] = {
                "metric": target,
                "filter": filter_name,
                "value": round(task_result[metric_key], 4),
                "stderr": round(task_result[stderr_key], 4)
                          if task_result.get(stderr_key) is not None else None,
                "num_fewshot": task_configs[task].get("num_fewshot", 0),
            }
            break

    return scores


def compute_aggregate(scores: dict) -> float:
    """各タスクスコアの単純平均を集約スコアとして返す"""
    values = [v["value"] for v in scores.values() if v is not None]
    return round(sum(values) / len(values), 4) if values else 0.0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str,
                        default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--eval_type", type=str, required=True,
                        choices=list(TASK_CONFIGS.keys()))
    parser.add_argument("--output_json", type=str, default=None,
                        help="集約結果を追記する JSON ファイルパス")
    parser.add_argument("--lm_eval_output_dir", type=str,
                        default="../../results/lm_eval_raw")
    parser.add_argument("--limit", type=int, default=None,
                        help="各タスクのサンプル数上限 (None=全件)")
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--apply_chat_template", action="store_true",
                        help="InstructモデルおよびLoRAモデルの評価時にチャットテンプレートを適用する")
    parser.add_argument(
        "--tasks",
        type=str,
        default=None,
        help="評価タスクをカンマ区切りで指定 (例: mbpp)。未指定時は eval_type の全タスク",
    )
    parser.add_argument(
        "--gen_kwargs",
        type=str,
        default=None,
        help="Generation kwargs for lm_eval (e.g. temperature=0.7,repetition_penalty=1.1)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    task_configs = dict(TASK_CONFIGS[args.eval_type])
    if args.tasks:
        selected = [t.strip() for t in args.tasks.split(",") if t.strip()]
        unknown = [t for t in selected if t not in task_configs]
        if unknown:
            raise ValueError(f"Unknown tasks for {args.eval_type}: {unknown}")
        task_configs = {k: task_configs[k] for k in selected}

    print(f"\n{'='*60}")
    print(f"Utility Evaluation [{args.eval_type}]: {args.model_name}")
    resolved = resolve_adapter_path(args.adapter_path)
    print(f"  adapter  : {resolved or args.adapter_path or '(base model)'}")
    print(f"  tasks    : {list(task_configs.keys())}")
    print(f"  limit    : {args.limit or 'full dataset'}")
    print(f"{'='*60}")

    lm_eval_out = Path(args.lm_eval_output_dir) / args.model_name / args.eval_type
    lm_eval_out.mkdir(parents=True, exist_ok=True)

    raw_results = run_lm_eval(
        base_model=args.base_model,
        adapter_path=args.adapter_path,
        task_configs=task_configs,
        output_dir=str(lm_eval_out),
        limit=args.limit,
        batch_size=args.batch_size,
        apply_chat_template=args.apply_chat_template,
        gen_kwargs=args.gen_kwargs,
    )

    scores = extract_scores(raw_results, task_configs)
    aggregate = compute_aggregate(scores)

    # 結果表示
    print(f"\n[Result] {args.model_name} ({args.eval_type})")
    print(f"  {'Task':<45} {'Score':>8}  {'± stderr':>10}  Metric / fewshot")
    print(f"  {'-'*80}")
    for task, info in scores.items():
        stderr_str = f"± {info['stderr']:.4f}" if info.get("stderr") else "        "
        filter_str = f" ({info['filter']})" if info.get("filter") else ""
        print(f"  {task:<45} {info['value']:>8.4f}  {stderr_str:>10}  "
              f"{info['metric']}{filter_str} / {info['num_fewshot']}-shot")
    print(f"  {'-'*80}")
    print(f"  {'Aggregate (macro-avg)':<45} {aggregate:>8.4f}")

    # 集約 JSON 保存
    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if out_path.exists():
            with open(out_path) as f:
                existing = json.load(f)
        existing = [r for r in existing
                    if not (r.get("model") == args.model_name
                            and r.get("task") == f"utility_{args.eval_type}")]
        existing.append({
            "model": args.model_name,
            "task": f"utility_{args.eval_type}",
            "eval_harness_commit": raw_results.get("git_hash", "unknown"),
            "tasks": scores,
            "aggregate_mean": aggregate,
            "lm_eval_raw_dir": str(lm_eval_out),
        })
        with open(out_path, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    main()
