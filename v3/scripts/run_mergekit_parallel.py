#!/usr/bin/env python3
import os
import sys
import json
import yaml
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MERGEKIT_METHODS = {"ties", "dare", "task_arithmetic", "della"}
SPECIAL_SINGLE_DOMAIN_METHODS = {"safemerge", "led_merging", "mergealign"}
CUSTOM_SINGLE_RUN_METHODS = {"fisher_weighted", "matena_fisher", "safemerge", "led_merging", "mergealign"}
PROPOSED_METHODS = {"diagonal_sst", "data_free_sst"}


def parse_args():
    p = argparse.ArgumentParser(description="Run only mergekit merges in parallel.")
    p.add_argument("--config", type=str, default="configs/config_main.yaml")
    p.add_argument("--workers", type=int, default=4, help="Number of parallel mergekit jobs.")
    p.add_argument("--resume", action="store_true", help="Skip successful merge output dirs.")
    p.add_argument("--log_dir", type=str, default="logs/mergekit_parallel")
    p.add_argument("--fim_cache_dir", type=str, default="cache/fim")
    p.add_argument("--no_fim_cache", action="store_true")
    p.add_argument("--overwrite_fim_cache", action="store_true")
    p.add_argument("--dry_run", action="store_true")
    p.add_argument(
        "--no_prewarm_temp",
        action="store_true",
        help="Disable sequential first job per seed. Usually not recommended because temp_safety_full_seedXX is shared.",
    )
    return p.parse_args()


def load_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_experiment_name(config):
    return config.get("experiment", {}).get("name", "experiment")


def get_patterns(config):
    return config.get("patterns", [
        "safety+math",
        "safety+code",
        "safety+medical",
        "safety+math+code+medical",
    ])


def get_methods(config):
    proposed = config.get("methods", {}).get("proposed", [])
    baselines = config.get("methods", {}).get("baselines", [])
    return proposed + baselines


def get_alphas_and_sample_size(config):
    merge_cfg = config.get("merge", {})
    main_cfg = merge_cfg.get("main", {})
    alphas = merge_cfg.get("alpha_sweep", [0.5])
    sample_size = int(main_cfg.get("sample_size", config["data"]["fim"].get("default_sample_size", 500)))
    return alphas, sample_size


def build_out_name(config, method, pattern, seed, alpha):
    exp = get_experiment_name(config)
    return f"{exp}_{method}_{pattern}_alpha{alpha}_seed{seed}"


def is_successful_merge_dir(path):
    meta = os.path.join(path, "merge_metadata.json")
    if not os.path.isdir(path) or not os.path.exists(meta):
        return False
    try:
        with open(meta, "r", encoding="utf-8") as f:
            return json.load(f).get("status") == "success"
    except Exception:
        return False


def build_merge_cmd(args, method, pattern, seed, alpha, sample_size, out_dir):
    cmd = [
        sys.executable,
        "scripts/merge.py",
        "--config", args.config,
        "--method", method,
        "--pattern", pattern,
        "--seed", str(seed),
        "--alpha", str(alpha),
        "--sample_size", str(sample_size),
        "--output_dir", out_dir,
        "--fim_cache_dir", args.fim_cache_dir,
    ]
    if args.no_fim_cache:
        cmd.append("--no_fim_cache")
    if args.overwrite_fim_cache:
        cmd.append("--overwrite_fim_cache")
    return cmd


def make_jobs(args, config):
    seeds = config["experiment"]["seeds"]
    patterns = get_patterns(config)
    methods = [m for m in get_methods(config) if m in MERGEKIT_METHODS]
    alphas, sample_size = get_alphas_and_sample_size(config)

    jobs = []
    for seed in seeds:
        for pattern in patterns:
            for method in methods:
                for alpha in alphas:
                    out_name = build_out_name(config, method, pattern, seed, alpha)
                    out_dir = os.path.join("models", "merged", out_name)
                    if args.resume and is_successful_merge_dir(out_dir):
                        continue
                    cmd = build_merge_cmd(args, method, pattern, seed, alpha, sample_size, out_dir)
                    jobs.append({
                        "seed": seed,
                        "method": method,
                        "pattern": pattern,
                        "alpha": alpha,
                        "out_dir": out_dir,
                        "cmd": cmd,
                    })
    return jobs


def safe_log_name(job):
    s = f"seed{job['seed']}_{job['method']}_{job['pattern']}_alpha{job['alpha']}"
    return s.replace("+", "_").replace("/", "_").replace(" ", "_") + ".log"


def run_job(job, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, safe_log_name(job))
    env = os.environ.copy()

    # mergekit itself is CPU-side here. Hide GPUs so parallel jobs do not fight for CUDA by accident.
    env["CUDA_VISIBLE_DEVICES"] = ""

    start = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n===== START {start} =====\n")
        f.write("COMMAND: " + " ".join(job["cmd"]) + "\n")
        f.flush()
        res = subprocess.run(job["cmd"], stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
        end = datetime.now().isoformat(timespec="seconds")
        f.write(f"===== END {end} returncode={res.returncode} =====\n")

    return {**job, "returncode": res.returncode, "log_path": log_path}


def split_prewarm_jobs(jobs):
    """Pick one first job per seed so shared temp_safety_full_seedXX is created before parallel fan-out."""
    first_by_seed = {}
    rest = []
    for job in jobs:
        seed = job["seed"]
        if seed not in first_by_seed:
            first_by_seed[seed] = job
        else:
            rest.append(job)
    return list(first_by_seed.values()), rest


def main():
    args = parse_args()
    config = load_config(args.config)
    os.makedirs("models/merged", exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    jobs = make_jobs(args, config)
    print(f"mergekit jobs to run: {len(jobs)}")
    print(f"workers: {args.workers}")

    if args.dry_run:
        for job in jobs:
            print(" ".join(job["cmd"]))
        return

    failed = []
    completed = []

    if not args.no_prewarm_temp:
        prewarm, jobs = split_prewarm_jobs(jobs)
        print(f"prewarm jobs: {len(prewarm)}")
        for job in prewarm:
            print(f"[prewarm] {job['method']} {job['pattern']} alpha={job['alpha']} seed={job['seed']}")
            r = run_job(job, args.log_dir)
            completed.append(r)
            if r["returncode"] != 0:
                failed.append(r)

        failed_seeds = {r["seed"] for r in failed}
        if failed_seeds:
            print(f"prewarm failed for seeds={sorted(failed_seeds)}; skipping remaining jobs for those seeds")
            jobs = [j for j in jobs if j["seed"] not in failed_seeds]

    print(f"parallel jobs: {len(jobs)}")
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(run_job, job, args.log_dir) for job in jobs]
        for fut in as_completed(futures):
            r = fut.result()
            completed.append(r)
            status = "OK" if r["returncode"] == 0 else "FAIL"
            print(f"[{status}] {r['method']} {r['pattern']} alpha={r['alpha']} seed={r['seed']} log={r['log_path']}")
            if r["returncode"] != 0:
                failed.append(r)

    summary_path = os.path.join(args.log_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"completed": completed, "failed": failed}, f, indent=2, ensure_ascii=False)

    print(f"summary: {summary_path}")
    if failed:
        print(f"failed jobs: {len(failed)}")
        sys.exit(1)
    print("all mergekit jobs completed successfully")


if __name__ == "__main__":
    main()
