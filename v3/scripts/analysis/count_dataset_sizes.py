#!/usr/bin/env python3
import argparse
import json
import os
from typing import Callable, Optional

import yaml
from datasets import load_dataset


def print_header(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def print_item(name, total=None, available=None, used=None, note=""):
    total_s = "ERROR" if total is None else str(total)
    available_s = "-" if available is None else str(available)
    used_s = "-" if used is None else str(used)
    print(
        f"{name:<38} "
        f"total={total_s:<10} "
        f"available={available_s:<10} "
        f"used={used_s:<10} "
        f"{note}"
    )


def apply_limit(n: int, limit: Optional[int]) -> int:
    if limit is None or limit <= 0:
        return n
    return min(n, limit)


def count_hf_dataset(
    name: str,
    dataset_name: str,
    config: Optional[str] = None,
    split: Optional[str] = None,
    available_rule: Optional[Callable[[int], int]] = None,
    limit: Optional[int] = None,
):
    try:
        ds = load_dataset(dataset_name, config) if config else load_dataset(dataset_name)

        if split is not None:
            data = ds[split]
            total = len(data)
            available = available_rule(total) if available_rule else total
            used = apply_limit(available, limit)
            print_item(
                name,
                total,
                available,
                used,
                f"dataset={dataset_name}, config={config}, split={split}",
            )
        else:
            for sp, data in ds.items():
                total = len(data)
                available = available_rule(total) if available_rule else total
                used = apply_limit(available, limit)
                print_item(
                    f"{name}/{sp}",
                    total,
                    available,
                    used,
                    f"dataset={dataset_name}, config={config}, split={sp}",
                )

    except Exception as e:
        print_item(name, None, None, None, str(e))


def count_json_dataset(
    name: str,
    path: str,
    prompt_key: str = "prompt",
    available_rule: Optional[Callable[[int], int]] = None,
    limit: Optional[int] = None,
):
    try:
        if not os.path.exists(path):
            print_item(name, None, None, None, f"missing: {path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        total = len(data)
        valid = sum(1 for x in data if isinstance(x, dict) and x.get(prompt_key))
        available = available_rule(valid) if available_rule else valid
        used = apply_limit(available, limit)

        print_item(
            name,
            total,
            available,
            used,
            f"valid_{prompt_key}={valid}, path={path}",
        )

    except Exception as e:
        print_item(name, None, None, None, str(e))


def count_alpaca_eval(limit: Optional[int] = None):
    try:
        ds = load_dataset(
            "json",
            data_files=(
                "https://huggingface.co/datasets/tatsu-lab/alpaca_eval/"
                "resolve/main/alpaca_eval.json"
            ),
            split="train",
        )
        total = len(ds)
        available = total
        used = apply_limit(available, limit)
        print_item("AlpacaEval 2", total, available, used, "raw json")
    except Exception as e:
        print_item("AlpacaEval 2", None, None, None, str(e))


def count_lm_eval_task(task: str, limit: Optional[int] = None):
    task_map = {
        # Math
        "gsm8k": {
            "name": "GSM8K",
            "dataset": "openai/gsm8k",
            "config": "main",
            "split": "test",
        },
        "minerva_math500": {
            "name": "Minerva Math 500 / MATH-500",
            "dataset": "HuggingFaceH4/MATH-500",
            "config": None,
            "split": "test",
        },

        # Code
        "humaneval": {
            "name": "HumanEval",
            "dataset": "openai/openai_humaneval",
            "config": None,
            "split": "test",
        },
        "mbpp": {
            "name": "MBPP",
            "dataset": "google-research-datasets/mbpp",
            "config": "sanitized",
            "split": "test",
        },

        # Medical
        "pubmedqa": {
            "name": "PubMedQA",
            "dataset": "qiaojin/PubMedQA",
            "config": "pqa_labeled",
            "split": "train",
        },
        "medqa_4options": {
            "name": "MedQA 4 options",
            "dataset": "GBaker/MedQA-USMLE-4-options",
            "config": None,
            "split": "test",
        },

        # General
        "mmlu_pro": {
            "name": "MMLU-Pro",
            "dataset": "TIGER-Lab/MMLU-Pro",
            "config": None,
            "split": "test",
        },
        "mmlu": {
            "name": "MMLU",
            "dataset": "cais/mmlu",
            "config": "all",
            "split": "test",
        },
        "ifeval": {
            "name": "IFEval",
            "dataset": "google/IFEval",
            "config": None,
            "split": "train",
        },
    }

    if task not in task_map:
        print_item(task, None, None, None, "unknown lm-eval task; add mapping manually")
        return

    info = task_map[task]
    count_hf_dataset(
        name=info["name"],
        dataset_name=info["dataset"],
        config=info["config"],
        split=info["split"],
        limit=limit,
    )


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config_main.yaml")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Evaluation limit. 0 means full available dataset.",
    )
    args = parser.parse_args()

    limit = args.limit if args.limit > 0 else None
    config = load_config(args.config)

    eval_cfg = config.get("data", {}).get("eval", {})
    safety_tasks = eval_cfg.get("safety_tasks", [])
    utility_task_groups = eval_cfg.get("utility_task_groups", {})

    print_header("Config-defined lm-evaluation-harness utility datasets")

    for group_name, tasks in utility_task_groups.items():
        print_header(f"Utility group: {group_name}")
        for task in tasks:
            count_lm_eval_task(task, limit=limit)

    print_header("General chat evaluation datasets")
    count_alpaca_eval(limit=limit)

    print_header("Instruction dataset evaluations")

    count_hf_dataset(
        name="Evol-Instruct-Code",
        dataset_name="nickrosh/Evol-Instruct-Code-80k-v1",
        split="train",
        available_rule=lambda total: max(total - 1000, 0),
        limit=limit,
    )

    count_hf_dataset(
        name="MedAlpaca Medical Flashcards",
        dataset_name="medalpaca/medical_meadow_medical_flashcards",
        split="train",
        available_rule=lambda total: max(total - 1000, 0),
        limit=limit,
    )

    print_header("Safety evaluation datasets actually used locally")

    safety_files = {
        "harmbench": "data/eval/eval_harmful_harmbench.json",
        "jailbreakbench": "data/eval/eval_harmful_jailbreakbench.json",
        "strongreject": "data/eval/eval_harmful_strongreject.json",
        "wildjailbreak": "data/eval/eval_harmful_wildjailbreak.json",
    }

    for task in safety_tasks:
        path = safety_files.get(task)
        if path is None:
            print_item(task, None, None, None, "unknown safety task; add local path manually")
        else:
            count_json_dataset(task, path, prompt_key="prompt", limit=limit)

    print_header("Reference HF safety datasets")

    count_hf_dataset(
        "JailbreakBench HF",
        "JailbreakBench/JBB-Behaviors",
        config="behaviors",
        split=None,
        limit=limit,
    )
    count_hf_dataset(
        "HarmBench HF",
        "walledai/HarmBench",
        split=None,
        limit=limit,
    )
    count_hf_dataset(
        "StrongReject HF",
        "walledai/StrongREJECT",
        split=None,
        limit=limit,
    )
    count_hf_dataset(
        "WildJailbreak HF",
        "allenai/wildjailbreak",
        split=None,
        limit=limit,
    )


if __name__ == "__main__":
    main()