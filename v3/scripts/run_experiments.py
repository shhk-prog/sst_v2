import os
import sys
import json
import yaml
import argparse
import subprocess
import re


args = None
RESULT_DIR = "results/raw"


SPECIAL_SINGLE_DOMAIN_METHODS = {"safemerge", "led_merging", "mergealign"}
MERGEKIT_METHODS = {"ties", "dare", "task_arithmetic", "della"}
CUSTOM_SINGLE_RUN_METHODS = {
    "fisher_weighted",
    "matena_fisher",
    "safemerge",
    "led_merging",
    "mergealign",
}
PROPOSED_METHODS = {"diagonal_sst", "data_free_sst"}
FIM_REQUIRED_METHODS = {"diagonal_sst", "fisher_weighted", "matena_fisher"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")

    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["all", "ft", "base_eval", "merge", "merge_eval", "pareto"],
    )

    parser.add_argument("--skip_ft", action="store_true")
    parser.add_argument("--skip_base_eval", action="store_true")
    parser.add_argument("--skip_merge", action="store_true")
    parser.add_argument("--skip_merge_eval", action="store_true")

    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")

    parser.add_argument("--fim_cache_dir", type=str, default="cache/fim")
    parser.add_argument("--no_fim_cache", action="store_true")
    parser.add_argument("--overwrite_fim_cache", action="store_true")

    parser.add_argument(
        "--merge_group",
        type=str,
        default="all",
        choices=["all", "mergekit", "non_mergekit"],
        help="Which merge methods to run.",
    )

    return parser.parse_args()


def get_results_dir():
    if args.limit == 0:
        return "results/final"
    return f"results/debug_limit{args.limit}"


def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_experiment_name(config):
    return config.get("experiment", {}).get("name", "experiment")


def should_run(stage_name):
    return args.stage == "all" or args.stage == stage_name


def get_output_path_from_cmd(cmd):
    for i in range(len(cmd) - 1):
        if cmd[i] in ["--output_file", "--output_path", "--output_dir"]:
            return cmd[i + 1]
    return None


def is_successful_merge_dir(path):
    metadata_path = os.path.join(path, "merge_metadata.json")

    if not os.path.isdir(path):
        return False

    metadata = load_json(metadata_path)
    if not isinstance(metadata, dict):
        return False

    return metadata.get("status") == "success"


def required_n_for_limit(limit):
    if limit == 0:
        return None
    return int(limit)


def infer_result_count(data):
    if not isinstance(data, dict):
        return 0

    if isinstance(data.get("results"), list):
        return len(data["results"])

    if isinstance(data.get("eval_details"), list):
        return len(data["eval_details"])

    if isinstance(data.get("outputs"), list):
        return len(data["outputs"])

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

    if isinstance(data, list):
        if limit == 0:
            return len(data) > 0
        return len(data) >= limit

    if not isinstance(data, dict):
        return False

    if data.get("status") == "failed":
        return False

    required_n = required_n_for_limit(limit)

    if required_n is None:
        return data.get("status") == "success" or data.get("completed") is True

    n = infer_result_count(data)

    if data.get("completed") is True:
        return n >= required_n

    if data.get("status") == "success":
        if n == 0:
            return True
        return n >= required_n

    return n >= required_n


def run_cmd(cmd, resume=True, is_merge_cmd=False):
    output_path = get_output_path_from_cmd(cmd)

    if resume and args.resume and not args.force and output_path:
        if is_merge_cmd:
            if is_successful_merge_dir(output_path):
                print(f"Successful merge output found. Skipping: {output_path}")
                return 0
        else:
            if output_complete(output_path, args.limit):
                print(f"Complete output found. Skipping: {output_path}")
                return 0
            elif os.path.exists(output_path):
                print(f"Incomplete output found. Re-running: {output_path}")

    print(f"\nRunning command: {' '.join(cmd)}")
    res = subprocess.run(cmd, text=True)

    if res.returncode != 0:
        print(f"Command failed with exit code {res.returncode}")

    return res.returncode


def make_result_prefix(config, name):
    experiment_name = get_experiment_name(config)
    return f"{experiment_name}_{name}"


def eval_model(model_name, model_path, config, output_prefix, limit, output_dir=None):
    if output_dir is None:
        output_dir = RESULT_DIR
    safety_tasks = config["data"]["eval"]["safety_tasks"]
    utility_task_groups = config["data"]["eval"]["utility_task_groups"]

    for task in safety_tasks:
        run_cmd([
            sys.executable,
            "scripts/eval/eval_safety.py",
            "--model_path", model_path,
            "--config", args.config,
            "--task", task,
            "--output_file", f"{output_dir}/{output_prefix}_{task}_safety.json",
            "--limit", str(limit),
        ])

    for domain, domain_tasks in utility_task_groups.items():
        for task in domain_tasks:
            run_cmd([
                sys.executable,
                "scripts/eval/eval_utility.py",
                "--model_path", model_path,
                "--config", args.config,
                "--tasks", task,
                "--output_file", f"{output_dir}/{output_prefix}_utility_{domain}_{task}.json",
                "--limit", str(limit),
            ])

    run_cmd([
        sys.executable,
        "scripts/eval/eval_alpaca.py",
        "--model_path", model_path,
        "--config", args.config,
        "--output_file", f"{output_dir}/{output_prefix}_alpaca_eval2.json",
        "--limit", str(limit),
    ])

    for inst_ds in ["evol_code", "medalpaca"]:
        run_cmd([
            sys.executable,
            "scripts/eval/eval_instruction_datasets.py",
            "--model_path", model_path,
            "--config", args.config,
            "--dataset", inst_ds,
            "--output_file", f"{output_dir}/{output_prefix}_inst_{inst_ds}.json",
            "--limit", str(limit),
        ])


def get_method_and_seed_from_out_name(out_name, seed):
    method_pattern = re.compile(r'^sst_merge_v3_main_(.*?)_(safety|math|medical|utility|inst|alpha|k\d)')
    match_method = method_pattern.match(out_name)
    if match_method:
        return match_method.group(1)
    else:
        prefix = "sst_merge_v3_main_"
        if out_name.startswith(prefix):
            idx = out_name.find(f"_seed{seed}")
            method_part = out_name[len(prefix):idx] if idx != -1 else out_name[len(prefix):]
            return method_part.strip('_')
        return "unknown_method"


def run_fine_tuning(config, seeds):
    print("\n=== Step 1: Fine-Tuning Safety Models ===")

    safety_model_dir = config["models"]["safety_model_dir"]

    for seed in seeds:
        output_dir = f"{safety_model_dir}_seed{seed}"

        cmd = [
            sys.executable,
            "scripts/fine_tuning.py",
            "--config", args.config,
            "--seed", str(seed),
            "--output_dir", output_dir,
        ]

        run_cmd(cmd)


def run_base_eval(config, seeds):
    print("\n=== Step 2: Evaluating Base / Utility / SafetyFT Models ===")

    base_models = [
        ("WizardMath", config["models"]["domain_models"]["math"], "base_WizardMath"),
        ("WizardCoder", config["models"]["domain_models"]["code"], "base_WizardCoder"),
        ("MedAlpaca", config["models"]["domain_models"]["medical"], "base_MedAlpaca"),
    ]

    for seed in seeds:
        safety_root = config["models"].get("safety_full_model_dir")
        if safety_root is None:
            safety_root = config["models"]["safety_model_dir"]

        safety_path = f"{safety_root}_seed{seed}"

        base_models.append((
            f"SafetyFT_seed{seed}",
            safety_path,
            f"base_SafetyFT_seed{seed}",
        ))

    for model_name, model_path, output_prefix in base_models:
        if model_path.startswith("models/") and not os.path.exists(model_path):
            print(f"Model path not found. Skipping: {model_path}")
            continue

        eval_model(
            model_name=model_name,
            model_path=model_path,
            config=config,
            output_prefix=make_result_prefix(config, output_prefix),
            limit=args.limit,
        )


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


def extract_utility_domains(pattern):
    return [p for p in pattern.split("+") if p != "safety"]


def is_multi_domain_pattern(pattern):
    return len(extract_utility_domains(pattern)) > 1


def should_skip_method_pattern(method, pattern, config):
    if method in SPECIAL_SINGLE_DOMAIN_METHODS and is_multi_domain_pattern(pattern):
        print(f"Skipping {method} for {pattern}: single-domain only.")
        return True

    if method == "led_merging":
        supported = set(
            config.get("led_merging", {}).get(
                "supported_utility_domains",
                ["math", "code"],
            )
        )
        domains = extract_utility_domains(pattern)

        if any(domain not in supported for domain in domains):
            print(
                f"Skipping led_merging for {pattern}: "
                f"supported domains are {sorted(supported)}."
            )
            return True

    return False


def get_default_sample_size(config):
    return int(config["data"]["fim"].get("default_sample_size", 500))


def get_sst_search_spaces(config):
    merge_cfg = config["merge"]
    main_cfg = merge_cfg.get("main", {})
    ablation_cfg = merge_cfg.get("ablation", {})

    alphas = merge_cfg.get("alpha_sweep", [0.5])
    main_k_values = [float(k) for k in main_cfg.get("k_values", [])]

    main_sample_size = int(
        main_cfg.get(
            "sample_size",
            config["data"]["fim"].get("default_sample_size", 500),
        )
    )

    main_sst_ratio = main_cfg.get("sst_ratio", "Fh/Fb")
    main_variant = main_cfg.get("variant", "interpolation")
    main_mask = main_cfg.get("mask", "hard mask")
    main_layer_wise = bool(main_cfg.get("layer_wise", False))
    main_layer_prior = main_cfg.get("layer_prior", "uniform")

    ablation_enabled = bool(ablation_cfg.get("enabled", False))
    ablation_k_values = [float(k) for k in ablation_cfg.get("k_values", [])]
    ablation_sample_sizes = [int(n) for n in ablation_cfg.get("fim_sample_sizes", [])]

    return {
        "alphas": alphas,
        "main_k_values": main_k_values,
        "main_sample_size": main_sample_size,
        "main_sst_ratio": main_sst_ratio,
        "main_variant": main_variant,
        "main_mask": main_mask,
        "main_layer_wise": main_layer_wise,
        "main_layer_prior": main_layer_prior,
        "ablation_enabled": ablation_enabled,
        "ablation_k_values": ablation_k_values,
        "ablation_sample_sizes": ablation_sample_sizes,
        "sst_ratios": ablation_cfg.get("sst_ratios", []),
        "variants": ablation_cfg.get("variants", []),
        "masks": ablation_cfg.get("masks", []),
        "ablation_layer_wise_values": ablation_cfg.get("layer_wise", []),
        "ablation_layer_priors": ablation_cfg.get("layer_prior_types", []),
    }


def layer_suffix(layer_wise, layer_prior):
    if layer_wise:
        return f"layerwise_{layer_prior}"
    return "nolayerwise"


def build_out_name_for_sst(
    config,
    method,
    pattern,
    alpha,
    k,
    sample_size,
    ratio,
    variant,
    mask,
    layer_wise,
    layer_prior,
    seed,
    experiment_type,
):
    experiment_name = get_experiment_name(config)
    ratio_safe = ratio.replace("/", "")
    mask_safe = mask.replace(" ", "")
    layer_safe = layer_suffix(layer_wise, layer_prior)

    name = (
        f"{experiment_name}_{method}_{experiment_type}_{pattern}"
        f"_alpha{alpha}"
    )

    if method in FIM_REQUIRED_METHODS:
        name += f"_n{sample_size}"

    name += (
        f"_k{k}"
        f"_{ratio_safe}"
        f"_{variant}"
        f"_{mask_safe}"
        f"_{layer_safe}"
        f"_seed{seed}"
    )

    return name


def build_out_name_for_baseline(config, method, pattern, seed, alpha=None):
    experiment_name = get_experiment_name(config)

    if alpha is None:
        return f"{experiment_name}_{method}_{pattern}_seed{seed}"

    return f"{experiment_name}_{method}_{pattern}_alpha{alpha}_seed{seed}"


def build_merge_cmd(
    method,
    pattern,
    seed,
    out_dir,
    config,
    alpha=None,
    k=None,
    sample_size=None,
    ratio=None,
    variant=None,
    mask=None,
    layer_wise=False,
    layer_prior="uniform",
):
    if sample_size is None:
        sample_size = get_default_sample_size(config)

    cmd = [
        sys.executable,
        "scripts/merge.py",
        "--config", args.config,
        "--method", method,
        "--pattern", pattern,
        "--seed", str(seed),
        "--output_dir", out_dir,
    ]

    if method in FIM_REQUIRED_METHODS:
        cmd.extend(["--sample_size", str(sample_size)])

    if alpha is not None:
        cmd.extend(["--alpha", str(alpha)])

    if k is not None:
        cmd.extend(["--k", str(k)])

    if ratio is not None:
        cmd.extend(["--sst_ratio", ratio])

    if variant is not None:
        cmd.extend(["--variant", variant])

    if mask is not None:
        cmd.extend(["--mask_type", mask])

    if layer_wise:
        cmd.append("--layer_wise")
        cmd.extend(["--layer_prior", layer_prior])

    cmd.extend(["--fim_cache_dir", args.fim_cache_dir])

    if args.no_fim_cache:
        cmd.append("--no_fim_cache")

    if args.overwrite_fim_cache:
        cmd.append("--overwrite_fim_cache")

    return cmd


def iter_main_sst_conditions(search):
    if not search["main_k_values"]:
        return

    for alpha in search["alphas"]:
        for k in search["main_k_values"]:
            yield {
                "experiment_type": "main",
                "alpha": alpha,
                "k": k,
                "sample_size": search["main_sample_size"],
                "ratio": search["main_sst_ratio"],
                "variant": search["main_variant"],
                "mask": search["main_mask"],
                "layer_wise": search["main_layer_wise"],
                "layer_prior": search["main_layer_prior"],
            }


def iter_ablation_sst_conditions(search):
    if not search["ablation_enabled"]:
        return

    for alpha in search["alphas"]:
        for sample_size in search["ablation_sample_sizes"]:
            for k in search["ablation_k_values"]:
                for ratio in search["sst_ratios"]:
                    for variant in search["variants"]:
                        for mask in search["masks"]:
                            for layer_wise in search["ablation_layer_wise_values"]:
                                priors = (
                                    search["ablation_layer_priors"]
                                    if layer_wise
                                    else ["uniform"]
                                )

                                for layer_prior in priors:
                                    changed_axes = 0
                                    changed_axes += ratio != "Fh/Fb"
                                    changed_axes += variant != "interpolation"
                                    changed_axes += mask != "hard mask"
                                    changed_axes += k != 0.20
                                    changed_axes += sample_size != 500
                                    changed_axes += bool(layer_wise)

                                    if changed_axes > 1:
                                        continue

                                    yield {
                                        "experiment_type": "ablation",
                                        "alpha": alpha,
                                        "k": k,
                                        "sample_size": sample_size,
                                        "ratio": ratio,
                                        "variant": variant,
                                        "mask": mask,
                                        "layer_wise": bool(layer_wise),
                                        "layer_prior": layer_prior,
                                    }


def iter_sst_conditions(config):
    search = get_sst_search_spaces(config)
    seen = set()

    for cond in iter_main_sst_conditions(search):
        key = tuple(sorted(cond.items()))
        if key not in seen:
            seen.add(key)
            yield cond

    for cond in iter_ablation_sst_conditions(search):
        key = tuple(sorted(cond.items()))
        if key not in seen:
            seen.add(key)
            yield cond


def run_merge_phase(config, seeds):
    print("\n=== Step 3: Merging Models ===")

    patterns = get_patterns(config)
    methods = get_methods(config)
    search = get_sst_search_spaces(config)
    alphas = search["alphas"]
    main_sample_size = search["main_sample_size"]

    for seed in seeds:
        for pattern in patterns:
            for method in methods:
                if args.merge_group == "mergekit" and method not in MERGEKIT_METHODS:
                    continue

                if args.merge_group == "non_mergekit" and method in MERGEKIT_METHODS:
                    continue

                if should_skip_method_pattern(method, pattern, config):
                    continue

                if method in MERGEKIT_METHODS:
                    for alpha in alphas:
                        out_name = build_out_name_for_baseline(
                            config, method, pattern, seed, alpha
                        )
                        out_dir = f"models/merged/{out_name}"

                        cmd = build_merge_cmd(
                            method=method,
                            pattern=pattern,
                            seed=seed,
                            out_dir=out_dir,
                            config=config,
                            alpha=alpha,
                            sample_size=main_sample_size,
                        )
                        run_cmd(cmd, is_merge_cmd=True)

                elif method in CUSTOM_SINGLE_RUN_METHODS:
                    out_name = build_out_name_for_baseline(
                        config, method, pattern, seed
                    )
                    out_dir = f"models/merged/{out_name}"

                    cmd = build_merge_cmd(
                        method=method,
                        pattern=pattern,
                        seed=seed,
                        out_dir=out_dir,
                        config=config,
                        sample_size=main_sample_size,
                    )
                    run_cmd(cmd, is_merge_cmd=True)

                elif method in PROPOSED_METHODS:
                    seen_conditions = set()

                    for cond in iter_sst_conditions(config):
                        cond = cond.copy()

                        if method == "data_free_sst":
                            cond["sample_size"] = None

                        condition_key = (
                            cond["experiment_type"],
                            cond["alpha"],
                            cond["k"],
                            cond["sample_size"] if method in FIM_REQUIRED_METHODS else None,
                            cond["ratio"],
                            cond["variant"],
                            cond["mask"],
                            cond["layer_wise"],
                            cond["layer_prior"],
                        )

                        if condition_key in seen_conditions:
                            continue

                        seen_conditions.add(condition_key)

                        out_name = build_out_name_for_sst(
                            config=config,
                            method=method,
                            pattern=pattern,
                            alpha=cond["alpha"],
                            k=cond["k"],
                            sample_size=cond["sample_size"],
                            ratio=cond["ratio"],
                            variant=cond["variant"],
                            mask=cond["mask"],
                            layer_wise=cond["layer_wise"],
                            layer_prior=cond["layer_prior"],
                            seed=seed,
                            experiment_type=cond["experiment_type"],
                        )

                        out_dir = f"models/merged/{out_name}"

                        cmd = build_merge_cmd(
                            method=method,
                            pattern=pattern,
                            seed=seed,
                            out_dir=out_dir,
                            config=config,
                            alpha=cond["alpha"],
                            k=cond["k"],
                            sample_size=cond["sample_size"],
                            ratio=cond["ratio"],
                            variant=cond["variant"],
                            mask=cond["mask"],
                            layer_wise=cond["layer_wise"],
                            layer_prior=cond["layer_prior"],
                        )
                        run_cmd(cmd, is_merge_cmd=True)

                else:
                    print(f"Unknown method in config. Skipping: {method}")


def run_merge_eval_phase(config, seeds):
    print("\n=== Step 4: Evaluating Merged Models ===")

    patterns = get_patterns(config)
    methods = get_methods(config)
    search = get_sst_search_spaces(config)
    alphas = search["alphas"]

    for seed in seeds:
        for pattern in patterns:
            for method in methods:
                if should_skip_method_pattern(method, pattern, config):
                    continue

                if method in MERGEKIT_METHODS:
                    for alpha in alphas:
                        out_name = build_out_name_for_baseline(
                            config, method, pattern, seed, alpha
                        )
                        out_dir = f"models/merged/{out_name}"

                        if not is_successful_merge_dir(out_dir):
                            print(f"Merge not successful. Skipping eval: {out_dir}")
                            continue

                        method_name = get_method_and_seed_from_out_name(out_name, seed)
                        target_dir = os.path.join(RESULT_DIR, f"seed{seed}", pattern, method_name)
                        os.makedirs(target_dir, exist_ok=True)
                        eval_model(
                            model_name=out_name,
                            model_path=out_dir,
                            config=config,
                            output_prefix=out_name,
                            limit=args.limit,
                            output_dir=target_dir,
                        )

                elif method in CUSTOM_SINGLE_RUN_METHODS:
                    out_name = build_out_name_for_baseline(
                        config, method, pattern, seed
                    )
                    out_dir = f"models/merged/{out_name}"

                    if not is_successful_merge_dir(out_dir):
                        print(f"Merge not successful. Skipping eval: {out_dir}")
                        continue

                    method_name = get_method_and_seed_from_out_name(out_name, seed)
                    target_dir = os.path.join(RESULT_DIR, f"seed{seed}", pattern, method_name)
                    os.makedirs(target_dir, exist_ok=True)
                    eval_model(
                        model_name=out_name,
                        model_path=out_dir,
                        config=config,
                        output_prefix=out_name,
                        limit=args.limit,
                        output_dir=target_dir,
                    )

                elif method in PROPOSED_METHODS:
                    seen_conditions = set()

                    for cond in iter_sst_conditions(config):
                        cond = cond.copy()

                        if method == "data_free_sst":
                            cond["sample_size"] = None

                        condition_key = (
                            cond["experiment_type"],
                            cond["alpha"],
                            cond["k"],
                            cond["sample_size"] if method in FIM_REQUIRED_METHODS else None,
                            cond["ratio"],
                            cond["variant"],
                            cond["mask"],
                            cond["layer_wise"],
                            cond["layer_prior"],
                        )

                        if condition_key in seen_conditions:
                            continue

                        seen_conditions.add(condition_key)

                        out_name = build_out_name_for_sst(
                            config=config,
                            method=method,
                            pattern=pattern,
                            alpha=cond["alpha"],
                            k=cond["k"],
                            sample_size=cond["sample_size"],
                            ratio=cond["ratio"],
                            variant=cond["variant"],
                            mask=cond["mask"],
                            layer_wise=cond["layer_wise"],
                            layer_prior=cond["layer_prior"],
                            seed=seed,
                            experiment_type=cond["experiment_type"],
                        )

                        out_dir = f"models/merged/{out_name}"

                        if not is_successful_merge_dir(out_dir):
                            print(f"Merge not successful. Skipping eval: {out_dir}")
                            continue

                        method_name = get_method_and_seed_from_out_name(out_name, seed)
                        target_dir = os.path.join(RESULT_DIR, f"seed{seed}", pattern, method_name)
                        os.makedirs(target_dir, exist_ok=True)
                        eval_model(
                            model_name=out_name,
                            model_path=out_dir,
                            config=config,
                            output_prefix=out_name,
                            limit=args.limit,
                            output_dir=target_dir,
                        )

                else:
                    print(f"Unknown method in config. Skipping eval: {method}")


def run_pareto(config):
    print("\n=== Step 5: Running Pareto Frontier Analysis ===")

    experiment_name = get_experiment_name(config)

    run_cmd([
        sys.executable,
        "scripts/analysis/pareto_auc.py",
        "--results_dir", RESULT_DIR,
        "--output_dir", f"results/pareto/{experiment_name}_{os.path.basename(RESULT_DIR)}",
    ])


def main():
    global args, RESULT_DIR
    args = parse_args()

    config = load_config(args.config)
    seeds = config["experiment"]["seeds"]

    RESULT_DIR = get_results_dir()

    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs("models/merged", exist_ok=True)

    print(f"Using result directory: {RESULT_DIR}")
    print(f"Resume: {args.resume}")
    print(f"Force: {args.force}")

    if should_run("ft") and not args.skip_ft:
        run_fine_tuning(config, seeds)

    if should_run("base_eval") and not args.skip_base_eval:
        run_base_eval(config, seeds)

    if should_run("merge") and not args.skip_merge:
        run_merge_phase(config, seeds)

    if should_run("merge_eval") and not args.skip_merge_eval:
        run_merge_eval_phase(config, seeds)

    if should_run("pareto"):
        run_pareto(config)


if __name__ == "__main__":
    main()