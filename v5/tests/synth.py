"""テスト用の合成データを作る関数群（ファイルとしては置かない）。

実データ（v3/results/vllm など）は開かない。``tmp_path`` の下に、api-documentation.md の
「結果ファイル契約」と同じ名前・同じ最小の形の JSON を作る。
"""

from __future__ import annotations

import json
from pathlib import Path

UTILITY_FILE_TASKS = {
    "gsm8k": "utility_math_gsm8k",
    "minerva_math500": "utility_math_minerva_math500",
    "humaneval": "utility_code_humaneval",
    "mbpp": "utility_code_mbpp",
    "pubmedqa": "utility_medical_pubmedqa",
    "medqa_4options": "utility_medical_medqa_4options",
    "mmlu": "utility_general_mmlu",
    "ifeval": "utility_general_ifeval",
}


def safety_json(valid_harmful=0, valid_safe=10, gibberish=0, bench_only_harmful=0):
    """安全性 JSON の最小の形。

    valid_harmful: 妥当で HarmBench が Yes の件数
    valid_safe: 妥当で全分類器が No の件数
    gibberish: 無効（is_gibberish=True）の件数
    bench_only_harmful: 妥当で HarmBench は No だが、ベンチマーク分類器の asr が 1.0 の件数
    """
    results = []
    for i in range(valid_harmful):
        results.append({"prompt": f"p{i}", "response": "sure here is how", "asr": 1.0,
                        "is_gibberish": False, "harmbench_cls_output": "Yes"})
    for i in range(valid_safe):
        results.append({"prompt": f"s{i}", "response": "I cannot help", "asr": 0.0,
                        "is_gibberish": False, "harmbench_cls_output": "No"})
    for i in range(bench_only_harmful):
        results.append({"prompt": f"b{i}", "response": "partial", "asr": 1.0,
                        "is_gibberish": False, "harmbench_cls_output": "No"})
    for i in range(gibberish):
        results.append({"prompt": f"g{i}", "response": "", "asr": 0.0,
                        "is_gibberish": True, "harmbench_cls_output": "No"})
    return {"status": "success", "mockup": False, "results": results}


def task_json(task, value):
    """lm-eval 形式の最小の有用性 JSON（値は 0〜1 の割合）。"""
    return {"results": {task: {"acc,none": value}}}


def old_utility_json(values):
    """旧方式（ドメインまとめ）の JSON。values は {task: 割合}。"""
    return {"results": {task: {"acc,none": v} for task, v in values.items()}}


def main_name(method, pattern, alpha, seed, metric):
    prefix = "sst_merge_v3_main_"
    a = f"_alpha{alpha}" if alpha is not None else ""
    if method == "diagonal_sst_main":
        mid = f"{method}_{pattern}{a}_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise"
    elif method == "data_free_sst_main":
        mid = f"{method}_{pattern}{a}_k0.2_FhFb_interpolation_hardmask_nolayerwise"
    else:
        mid = f"{method}_{pattern}{a}"
    return f"{prefix}{mid}_seed{seed}_{metric}.json"


def ablation_name(family, pattern, alpha, ratio, variant, k, n, layerwise, seed, metric):
    method = "diagonal_sst" if family == "sst" else "data_free_sst"
    n_part = f"_n{n}" if family == "sst" else ""
    return (
        f"sst_merge_v3_ablation_{method}_ablation_{pattern}_alpha{alpha}{n_part}_k{k}_"
        f"{ratio}_{variant}_hardmask_{layerwise}_seed{seed}_{metric}.json"
    )


def base_name(model, metric, seed=None):
    s = f"_seed{seed}" if seed is not None else ""
    return f"sst_merge_v3_main_base_{model}{s}_{metric}.json"


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def write_main_point(root: Path, method, pattern, alpha, seed, safety=None, utility=None,
                     old_style_utility=None):
    """主実験の 1 条件（手法, パターン, α, seed）のファイルを書く。

    safety: {bench: safety_json(...)}、utility: {task: 割合}（新方式のタスク別ファイル）、
    old_style_utility: {domain: {task: 割合}}（旧方式のドメインまとめ）
    """
    d = root / "merged" / f"seed{seed}" / pattern / method
    for bench, payload in (safety or {}).items():
        dump(d / main_name(method, pattern, alpha, seed, f"{bench}_safety"), payload)
    for task, value in (utility or {}).items():
        dump(d / main_name(method, pattern, alpha, seed, UTILITY_FILE_TASKS[task]),
             task_json(task, value))
    for domain, values in (old_style_utility or {}).items():
        dump(d / main_name(method, pattern, alpha, seed, f"utility_{domain}"),
             old_utility_json(values))


def write_ablation_point(root: Path, family, pattern, alpha, ratio, variant, k, n, layerwise, seed,
                         safety=None, old_style_utility=None):
    sub = "sst" if family == "sst" else "datafree"
    d = root / "merged" / f"seed{seed}" / pattern / "ablation" / sub
    for bench, payload in (safety or {}).items():
        dump(d / ablation_name(family, pattern, alpha, ratio, variant, k, n, layerwise, seed,
                               f"{bench}_safety"), payload)
    for domain, values in (old_style_utility or {}).items():
        dump(d / ablation_name(family, pattern, alpha, ratio, variant, k, n, layerwise, seed,
                               f"utility_{domain}"), old_utility_json(values))
