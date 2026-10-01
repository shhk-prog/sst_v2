#!/usr/bin/env python3
import argparse
import concurrent.futures as futures
import json
import os
import queue
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EvalJob:
    model_name: str
    model_path: str
    output_prefix: str


def parse_args():
    p = argparse.ArgumentParser(description="Run base_eval models in parallel across GPUs.")
    p.add_argument("--config", type=str, default="configs/config_main.yaml")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--gpus", type=str, default="0,1,2,3")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--log_dir", type=str, default="logs/v3_base_eval_parallel")
    p.add_argument("--dry_run", action="store_true")
    p.add_argument("--use_vllm", action="store_true", help="Use vLLM backend for faster generation")
    p.add_argument("--model_index", type=int, default=None, help="Run only the model at this index in the jobs list (0-based). Used for SLURM array jobs.")
    p.add_argument("--list_models", action="store_true", help="Print the number of available models and exit. Used for SLURM array jobs.")
    return p.parse_args()


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def infer_result_count(data):
    if isinstance(data, list):
        return len(data)

    if not isinstance(data, dict):
        return 0

    for key in ["results", "eval_details", "outputs", "model_outputs"]:
        if isinstance(data.get(key), list):
            return len(data[key])

    for key in ["n", "num_results", "num_samples"]:
        if key in data:
            try:
                return int(data[key])
            except Exception:
                pass

    return 0


def output_complete(path, limit):
    if not os.path.exists(path):
        return False

    data = load_json(path)
    if data is None:
        return False

    if isinstance(data, dict) and data.get("status") == "failed":
        return False

    if isinstance(data, dict) and data.get("completed") is True:
        if limit == 0:
            return True

        count = infer_result_count(data)

        if count > 0:
            return count >= limit

        return True

    if isinstance(data, dict) and data.get("status") == "success":
        if limit == 0:
            return True

        count = infer_result_count(data)

        if count > 0:
            return count >= limit

        return True

    if isinstance(data, list):
        if limit == 0:
            return len(data) > 0

        return len(data) >= limit

    return False


def get_results_dir(limit, use_vllm=False):
    prefix = "results/vllm" if use_vllm else "results"
    if limit == 0:
        return f"{prefix}/final/base"
    return f"{prefix}/debug_limit{limit}/base"


def get_experiment_name(config):
    return config.get("experiment", {}).get("name", "experiment")


def make_result_prefix(config, name):
    return f"{get_experiment_name(config)}_{name}"


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def build_base_eval_jobs(config):
    jobs = [
        EvalJob("WizardMath", config["models"]["domain_models"]["math"], "base_WizardMath"),
        EvalJob("WizardCoder", config["models"]["domain_models"]["code"], "base_WizardCoder"),
        EvalJob("MedAlpaca", config["models"]["domain_models"]["medical"], "base_MedAlpaca"),
    ]

    seeds = config["experiment"]["seeds"]
    safety_root = config["models"].get("safety_full_model_dir")
    if safety_root is None:
        safety_root = config["models"]["safety_model_dir"]

    for seed in seeds:
        jobs.append(
            EvalJob(
                f"SafetyFT_seed{seed}",
                f"{safety_root}_seed{seed}",
                f"base_SafetyFT_seed{seed}",
            )
        )

    return jobs


def expected_outputs(config, output_prefix, result_dir):
    paths = []

    for task in config["data"]["eval"]["safety_tasks"]:
        paths.append(f"{result_dir}/{output_prefix}_{task}_safety.json")

    for domain, domain_tasks in config["data"]["eval"]["utility_task_groups"].items():
        for task in domain_tasks:
            paths.append(f"{result_dir}/{output_prefix}_utility_{domain}_{task}.json")

    paths.append(f"{result_dir}/{output_prefix}_alpaca_eval2.json")

    for inst_ds in ["evol_code", "medalpaca"]:
        paths.append(f"{result_dir}/{output_prefix}_inst_{inst_ds}.json")

    return paths


def all_outputs_complete(config, output_prefix, result_dir, limit):
    outs = expected_outputs(config, output_prefix, result_dir)
    return all(output_complete(p, limit) for p in outs)


def build_eval_commands(config, config_path, model_path, output_prefix, limit, result_dir, use_vllm=False):
    cmds = []

    for task in config["data"]["eval"]["safety_tasks"]:
        cmd = [
            sys.executable,
            "scripts/eval/eval_safety.py",
            "--model_path", model_path,
            "--config", config_path,
            "--task", task,
            "--output_file", f"{result_dir}/{output_prefix}_{task}_safety.json",
            "--limit", str(limit),
        ]
        if use_vllm:
            cmd.append("--use_vllm")
        cmds.append(cmd)

    for domain, domain_tasks in config["data"]["eval"]["utility_task_groups"].items():
        for task in domain_tasks:
            cmd = [
                sys.executable,
                "scripts/eval/eval_utility.py",
                "--model_path", model_path,
                "--config", config_path,
                "--tasks", task,
                "--output_file", f"{result_dir}/{output_prefix}_utility_{domain}_{task}.json",
                "--limit", str(limit),
            ]
            if use_vllm:
                cmd.append("--use_vllm")
            cmds.append(cmd)

    cmd = [
        sys.executable,
        "scripts/eval/eval_alpaca.py",
        "--model_path", model_path,
        "--config", config_path,
        "--output_file", f"{result_dir}/{output_prefix}_alpaca_eval2.json",
        "--limit", str(limit),
    ]
    if use_vllm:
        cmd.append("--use_vllm")
    cmds.append(cmd)

    for inst_ds in ["evol_code", "medalpaca"]:
        cmd = [
            sys.executable,
            "scripts/eval/eval_instruction_datasets.py",
            "--model_path", model_path,
            "--config", config_path,
            "--dataset", inst_ds,
            "--output_file", f"{result_dir}/{output_prefix}_inst_{inst_ds}.json",
            "--limit", str(limit),
        ]
        if use_vllm:
            cmd.append("--use_vllm")
        cmds.append(cmd)

    return cmds


def get_output_file_from_cmd(cmd):
    if "--output_file" in cmd:
        i = cmd.index("--output_file")
        return cmd[i + 1]
    return None


def run_one_job(job, gpu_queue, args, config, result_dir):
    gpu = gpu_queue.get()

    try:
        output_prefix = make_result_prefix(config, job.output_prefix)
        log_path = Path(args.log_dir) / f"gpu{gpu}_{safe_name(output_prefix)}.log"

        cmds = build_eval_commands(
            config=config,
            config_path=args.config,
            model_path=job.model_path,
            output_prefix=output_prefix,
            limit=args.limit,
            result_dir=result_dir,
            use_vllm=args.use_vllm,
        )

        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu)
        env.setdefault("TOKENIZERS_PARALLELISM", "false")
        env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        env["VLLM_ALLOW_LONG_MAX_MODEL_LEN"] = "1"
        env["VLLM_ENABLE_V1"] = "0"
        env["PYTHONUNBUFFERED"] = "1"

        with open(log_path, "a", encoding="utf-8") as log:
            log.write("\n" + "=" * 80 + "\n")
            log.write(f"MODEL:  {job.model_name}\n")
            log.write(f"PATH:   {job.model_path}\n")
            log.write(f"GPU:    {gpu}\n")
            log.write(f"PREFIX: {output_prefix}\n")
            log.write(f"LIMIT:  {args.limit}\n")
            log.flush()

            print(f"[GPU {gpu}] START {job.model_name} -> {log_path}", flush=True)

            if job.model_path.startswith("models/") and not os.path.exists(job.model_path):
                msg = f"Model path not found. Skipping: {job.model_path}\n"
                log.write(msg)
                print(f"[GPU {gpu}] SKIP {job.model_name}: missing path", flush=True)
                return (job.model_name, "skipped_missing", 0)

            if args.resume and not args.force:
                if all_outputs_complete(config, output_prefix, result_dir, args.limit):
                    log.write("All expected outputs are complete. Skipping whole model.\n")
                    print(f"[GPU {gpu}] SKIP {job.model_name}: complete", flush=True)
                    return (job.model_name, "skipped_complete", 0)

            if args.dry_run:
                for cmd in cmds:
                    log.write("DRY_RUN: " + " ".join(cmd) + "\n")
                print(f"[GPU {gpu}] DRY_RUN {job.model_name}", flush=True)
                return (job.model_name, "dry_run", 0)

            for cmd in cmds:
                out_file = get_output_file_from_cmd(cmd)

                if args.resume and not args.force and out_file:
                    if output_complete(out_file, args.limit):
                        log.write(f"\n[skip complete] {out_file}\n")
                        log.flush()
                        continue

                    if os.path.exists(out_file):
                        log.write(f"\n[resume incomplete] {out_file}\n")
                        log.flush()

                log.write("\n$ " + " ".join(cmd) + "\n")
                log.flush()

                res = subprocess.run(
                    cmd,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                if res.returncode != 0:
                    log.write(f"\nFAILED exit_code={res.returncode}\n")
                    log.flush()
                    print(f"[GPU {gpu}] FAIL {job.model_name}: exit {res.returncode}", flush=True)
                    return (job.model_name, "failed", res.returncode)

            print(f"[GPU {gpu}] DONE {job.model_name}", flush=True)
            return (job.model_name, "done", 0)

    finally:
        gpu_queue.put(gpu)


def main():
    args = parse_args()
    config = load_config(args.config)
    result_dir = get_results_dir(args.limit, use_vllm=args.use_vllm)
    if args.use_vllm and args.log_dir == "logs/v3_base_eval_parallel":
        args.log_dir = "logs/vllm/v3_base_eval_parallel"

    gpus = [g.strip() for g in args.gpus.split(",") if g.strip()]
    if not gpus:
        raise ValueError("No GPUs specified. Use --gpus 0,1,2,3")

    workers = args.workers if args.workers is not None else len(gpus)
    workers = min(workers, len(gpus))

    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    jobs = build_base_eval_jobs(config)

    if args.list_models:
        print(len(jobs))
        sys.exit(0)

    if args.model_index is not None:
        if args.model_index < 0 or args.model_index >= len(jobs):
            print(f"Error: --model_index {args.model_index} is out of range. Max is {len(jobs) - 1}.")
            sys.exit(1)
        jobs = [jobs[args.model_index]]
        print(f"Running single job for model index {args.model_index}: {jobs[0].model_name}")

    print(f"Using result directory: {result_dir}")
    print(f"base_eval jobs: {len(jobs)}")
    print(f"gpus: {','.join(gpus)}")
    print(f"workers: {workers}")
    print(f"resume: {args.resume}")
    print(f"force: {args.force}")
    print(f"use_vllm: {args.use_vllm}")

    gpu_queue = queue.Queue()
    for gpu in gpus[:workers]:
        gpu_queue.put(gpu)

    results = []

    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(run_one_job, job, gpu_queue, args, config, result_dir)
            for job in jobs
        ]

        for fut in futures.as_completed(futs):
            results.append(fut.result())

    ok = sum(
        1 for _, status, code in results
        if code == 0 and not status.startswith("failed")
    )
    failed = [r for r in results if r[2] != 0 or r[1] == "failed"]

    print("\nSummary")
    print(f"ok/skipped: {ok}")
    print(f"failed: {len(failed)}")

    for name, status, code in failed:
        print(f"  {name}: {status} exit={code}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()