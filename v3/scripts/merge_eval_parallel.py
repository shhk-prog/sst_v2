import os
import sys
import json
import yaml
import argparse
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--batch_size", type=str, default="auto", help="Batch size for evaluation (int or 'auto')")
    parser.add_argument("--gpus", type=str, default="0,1,2")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--patterns", type=str, default=None)
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--use_vllm", action="store_true", help="Pass --use_vllm to evaluation scripts")
    parser.add_argument("--model_index", type=int, default=None, help="Index of a specific model to evaluate (0-indexed)")
    parser.add_argument("--list_models", action="store_true", help="List all collected models and exit")
    return parser.parse_args()


def get_results_dir(limit, target="merged", use_vllm=False):
    prefix = os.path.join("results", "vllm") if use_vllm else "results"
    if limit == 0:
        return os.path.join(prefix, "final", target)
    return os.path.join(prefix, f"debug_limit{limit}", target)


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_experiment_name(config):
    return config.get("experiment", {}).get("name", "experiment")


def is_successful_merge_dir(path):
    meta = os.path.join(path, "merge_metadata.json")
    data = load_json(meta)
    return os.path.isdir(path) and isinstance(data, dict) and data.get("status") == "success"


def extract_utility_domains(pattern):
    return [p for p in pattern.split("+") if p != "safety"]


def is_multi_domain_pattern(pattern):
    return len(extract_utility_domains(pattern)) > 1


def should_skip_method_pattern(method, pattern, config):
    if method in SPECIAL_SINGLE_DOMAIN_METHODS and is_multi_domain_pattern(pattern):
        return True

    if method == "led_merging":
        supported = set(
            config.get("led_merging", {}).get(
                "supported_utility_domains",
                ["math", "code"],
            )
        )
        domains = extract_utility_domains(pattern)
        return any(d not in supported for d in domains)

    return False


def get_patterns(config):
    return config.get(
        "patterns",
        [
            "safety+math",
            "safety+code",
            "safety+medical",
            "safety+math+code+medical",
        ],
    )


def get_methods(config):
    return config.get("methods", {}).get("proposed", []) + config.get("methods", {}).get("baselines", [])


def get_sst_search_spaces(config):
    merge_cfg = config["merge"]
    main_cfg = merge_cfg.get("main", {})
    ablation_cfg = merge_cfg.get("ablation", {})

    return {
        "alphas": merge_cfg.get("alpha_sweep", [0.5]),
        "main_k_values": [float(k) for k in main_cfg.get("k_values", [])],
        "main_sample_size": int(
            main_cfg.get(
                "sample_size",
                config["data"]["fim"].get("default_sample_size", 500),
            )
        ),
        "main_sst_ratio": main_cfg.get("sst_ratio", "Fh/Fb"),
        "main_variant": main_cfg.get("variant", "interpolation"),
        "main_mask": main_cfg.get("mask", "hard mask"),
        "main_layer_wise": bool(main_cfg.get("layer_wise", False)),
        "main_layer_prior": main_cfg.get("layer_prior", "uniform"),
        "ablation_enabled": bool(ablation_cfg.get("enabled", False)),
        "ablation_k_values": [float(k) for k in ablation_cfg.get("k_values", [])],
        "ablation_sample_sizes": [int(n) for n in ablation_cfg.get("fim_sample_sizes", [])],
        "sst_ratios": ablation_cfg.get("sst_ratios", []),
        "variants": ablation_cfg.get("variants", []),
        "masks": ablation_cfg.get("masks", []),
        "ablation_layer_wise_values": ablation_cfg.get("layer_wise", []),
        "ablation_layer_priors": ablation_cfg.get("layer_prior_types", []),
    }


def layer_suffix(layer_wise, layer_prior):
    return f"layerwise_{layer_prior}" if layer_wise else "nolayerwise"


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

    name = f"{experiment_name}_{method}_{experiment_type}_{pattern}_alpha{alpha}"

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


def iter_main_sst_conditions(search):
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
                                priors = search["ablation_layer_priors"] if layer_wise else ["uniform"]

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


def iter_sst_conditions_for_method(config, method):
    seen = set()

    for cond in iter_sst_conditions(config):
        cond = cond.copy()

        if method == "data_free_sst":
            cond["sample_size"] = None

        key = (
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

        if key in seen:
            continue

        seen.add(key)
        yield cond


def collect_merged_models_for_seed(config, seed, selected_patterns=None):
    models = []
    patterns = get_patterns(config)

    if selected_patterns is not None:
        patterns = [p for p in patterns if p in selected_patterns]

    methods = get_methods(config)
    search = get_sst_search_spaces(config)
    alphas = search["alphas"]

    for pattern in patterns:
        for method in methods:
            if should_skip_method_pattern(method, pattern, config):
                continue

            if method in MERGEKIT_METHODS:
                for alpha in alphas:
                    out_name = build_out_name_for_baseline(config, method, pattern, seed, alpha)
                    out_dir = f"models/merged/{out_name}"
                    models.append((out_name, out_dir, seed))

            elif method in CUSTOM_SINGLE_RUN_METHODS:
                out_name = build_out_name_for_baseline(config, method, pattern, seed)
                out_dir = f"models/merged/{out_name}"
                models.append((out_name, out_dir, seed))

            elif method in PROPOSED_METHODS:
                for cond in iter_sst_conditions_for_method(config, method):
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
                    models.append((out_name, out_dir, seed))

    return models


def collect_merged_models(config, seeds, selected_patterns=None):
    models = []
    for seed in seeds:
        models.extend(collect_merged_models_for_seed(config, seed, selected_patterns))
    return models


def get_count_from_output(data):
    if not isinstance(data, dict):
        return 0

    if isinstance(data.get("results"), list):
        return len(data["results"])

    if isinstance(data.get("results"), dict) and len(data["results"]) > 0:
        return 999999

    if isinstance(data.get("eval_details"), list):
        return len(data["eval_details"])

    if isinstance(data.get("samples"), dict):
        counts = []
        for rows in data["samples"].values():
            if isinstance(rows, list):
                counts.append(len(rows))
        if counts:
            return min(counts)

    for key in ["n", "num_results", "num_samples", "expected_n"]:
        if key in data:
            try:
                return int(data[key])
            except Exception:
                pass

    return 0


def get_expected_n(data, limit):
    if not isinstance(data, dict):
        return None

    for key in ["expected_n", "actual_n", "dataset_n", "num_samples", "n"]:
        if key in data:
            try:
                v = int(data[key])
                if v > 0:
                    return v
            except Exception:
                pass

    if limit == 0:
        return None

    count = get_count_from_output(data)
    if count > 0 and count < limit:
        # completed=True の場合のみ「データセットが limit 未満」とみなす
        # completed=False は途中停止の可能性があるため limit を期待値にする
        if data.get("completed") is True:
            return count

    return int(limit)


def load_alpaca_outputs(path):
    outputs = load_json(path)

    if isinstance(outputs, list):
        return outputs

    if isinstance(outputs, dict) and isinstance(outputs.get("results"), list):
        return outputs["results"]

    return []


def alpaca_outputs_complete(data, required_n):
    outputs_path = data.get("model_outputs_path")
    if not outputs_path:
        return False

    if not os.path.exists(outputs_path):
        if "_n500_" in outputs_path:
            alt_path = outputs_path.replace("_n500_", "_")
            if os.path.exists(alt_path):
                outputs_path = alt_path
        else:
            # もし逆に _n500 が必要な場合
            alt_path = outputs_path.replace("_alpha", "_alpha0.0_n500_") # など
            if os.path.exists(alt_path):
                outputs_path = alt_path

    outputs = load_alpaca_outputs(outputs_path)

    if len(outputs) < required_n:
        return False

    for r in outputs[:required_n]:
        if not isinstance(r, dict):
            return False
        if r.get("instruction") is None:
            return False
        if r.get("output") is None:
            return False

    return True


import glob
import shutil


def clean_redundant_timestamped_files(output_file):
    if not output_file.endswith(".json"):
        return

    dirpath = os.path.dirname(output_file)
    fname = os.path.basename(output_file)
    base_prefix = fname[:-5]
    pattern = os.path.join(dirpath, base_prefix + "_2026-*.json")
    matches = glob.glob(pattern)

    if not matches:
        return

    matches.sort(key=os.path.getmtime, reverse=True)
    latest_file = matches[0]

    if not os.path.exists(output_file):
        try:
            shutil.copy2(latest_file, output_file)
        except Exception:
            pass

    for fpath in matches:
        if os.path.exists(output_file) and fpath != output_file:
            try:
                os.remove(fpath)
            except Exception:
                pass


def find_latest_timestamped_file(output_file):
    if os.path.exists(output_file):
        clean_redundant_timestamped_files(output_file)
        return output_file

    if output_file.endswith(".json"):
        clean_redundant_timestamped_files(output_file)
        if os.path.exists(output_file):
            return output_file

        base_prefix = output_file[:-5]
        pattern = base_prefix + "_*.json"
        matches = glob.glob(pattern)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]

    return output_file



def output_complete(path, limit):
    resolved_path = find_latest_timestamped_file(path)
    if not os.path.exists(resolved_path):
        return False

    data = load_json(resolved_path)
    if not isinstance(data, dict):
        return False

    if data.get("status") == "failed":
        return False

    if data.get("status") != "success" and data.get("completed") is not True:
        if isinstance(data.get("results"), dict) and len(data["results"]) > 0:
            pass
        else:
            return False

    is_complete = False

    if "win_rate" in data:
        if data.get("status") == "success" or data.get("completed") is True:
            is_complete = True
        else:
            expected_n = get_expected_n(data, limit)
            if expected_n is None:
                is_complete = False
            else:
                is_complete = alpaca_outputs_complete(data, expected_n)
    else:
        expected_n = get_expected_n(data, limit)
        count = get_count_from_output(data)

        if expected_n is None:
            is_complete = data.get("status") == "success" or data.get("completed") is True
        else:
            is_complete = count >= expected_n

    if is_complete and resolved_path != path:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    return is_complete



def run_cmd(cmd, gpu, resume=False, log_file=None, force=False, limit=10):
    output_path = None

    for i in range(len(cmd) - 1):
        if cmd[i] in ["--output_file", "--output_path", "--output_dir"]:
            output_path = cmd[i + 1]
            break

    if resume and not force and output_path and output_complete(output_path, limit):
        msg = f"[GPU {gpu}] skip complete: {output_path}"
        print(msg)

        if log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

        return 0

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    env.setdefault("TOKENIZERS_PARALLELISM", "false")
    env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    env["VLLM_ALLOW_LONG_MAX_MODEL_LEN"] = "1"
    env["VLLM_ENABLE_V1"] = "0"
    env["PYTHONUNBUFFERED"] = "1"

    cpus = os.environ.get("SLURM_CPUS_PER_TASK", "16")
    env["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS", cpus)
    env["MKL_NUM_THREADS"] = os.environ.get("MKL_NUM_THREADS", cpus)
    env["OPENBLAS_NUM_THREADS"] = os.environ.get("OPENBLAS_NUM_THREADS", cpus)
    env["VECLIB_MAXIMUM_THREADS"] = os.environ.get("VECLIB_MAXIMUM_THREADS", cpus)
    env["NUMEXPR_NUM_THREADS"] = os.environ.get("NUMEXPR_NUM_THREADS", cpus)

    cmd_str = " ".join(cmd)
    print(f"\n[GPU {gpu}] Running: {cmd_str}")

    if log_file is None:
        res = subprocess.run(cmd, text=True, env=env)
    else:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write(f"[GPU {gpu}] Running: {cmd_str}\n")
            f.write("=" * 80 + "\n")
            f.flush()

            res = subprocess.run(
                cmd,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )

            f.write(f"\n[GPU {gpu}] Exit code: {res.returncode}\n")
            f.flush()

    if res.returncode != 0:
        print(f"[GPU {gpu}] failed with exit code {res.returncode}")

    return res.returncode


def fix_model_vocab_size_if_needed(model_path):
    import json
    import struct
    import torch
    import glob
    
    config_path = os.path.join(model_path, "config.json")
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"[VOCAB_FIX] Failed to read config.json in {model_path}: {e}")
        return

    current_vocab_size = config_data.get("vocab_size")
    if current_vocab_size is None:
        return

    actual_vocab_size = None

    # Determine candidate weight files to check (including sharded weights)
    weight_files_to_check = []
    
    # 1. Check safetensors index
    sf_index_path = os.path.join(model_path, "model.safetensors.index.json")
    if os.path.exists(sf_index_path):
        try:
            with open(sf_index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            weight_map = index_data.get("weight_map", {})
            for key in ["lm_head.weight", "model.embed_tokens.weight"]:
                if key in weight_map:
                    weight_files_to_check.append(os.path.join(model_path, weight_map[key]))
        except Exception:
            pass

    # 2. Check pytorch bin index
    bin_index_path = os.path.join(model_path, "pytorch_model.bin.index.json")
    if os.path.exists(bin_index_path):
        try:
            with open(bin_index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            weight_map = index_data.get("weight_map", {})
            for key in ["lm_head.weight", "model.embed_tokens.weight"]:
                if key in weight_map:
                    weight_files_to_check.append(os.path.join(model_path, weight_map[key]))
        except Exception:
            pass

    # 3. Fallback standard names & sharded patterns
    weight_files_to_check.append(os.path.join(model_path, "model.safetensors"))
    weight_files_to_check.append(os.path.join(model_path, "pytorch_model.bin"))
    weight_files_to_check.extend(glob.glob(os.path.join(model_path, "model-00001-of-*.safetensors")))
    weight_files_to_check.extend(glob.glob(os.path.join(model_path, "pytorch_model-00001-of-*.bin")))

    # Deduplicate and verify file existence
    seen = set()
    weight_files = []
    for fp in weight_files_to_check:
        if fp and os.path.exists(fp) and fp not in seen:
            seen.add(fp)
            weight_files.append(fp)

    # Scan through files to find the shape of lm_head or embed_tokens
    for file_path in weight_files:
        if file_path.endswith(".safetensors"):
            try:
                with open(file_path, "rb") as f:
                    header_size_bytes = f.read(8)
                    if len(header_size_bytes) == 8:
                        header_size = struct.unpack("<Q", header_size_bytes)[0]
                        header_bytes = f.read(header_size)
                        header = json.loads(header_bytes.decode("utf-8"))
                        for key in ["lm_head.weight", "model.embed_tokens.weight"]:
                            if key in header and "shape" in header[key]:
                                actual_vocab_size = header[key]["shape"][0]
                                break
            except Exception as e:
                print(f"[VOCAB_FIX] Failed to parse safetensors header in {file_path}: {e}")
        
        elif file_path.endswith(".bin"):
            try:
                sd = torch.load(file_path, map_location="cpu", weights_only=True, mmap=True)
                for key in ["lm_head.weight", "model.embed_tokens.weight"]:
                    if key in sd:
                        actual_vocab_size = sd[key].shape[0]
                        break
            except Exception as e:
                print(f"[VOCAB_FIX] Failed to load bin {file_path}: {e}")

        if actual_vocab_size is not None:
            break

    # If mismatch is found, correct the config.json vocab_size
    if actual_vocab_size is not None and actual_vocab_size != current_vocab_size:
        print(f"[VOCAB_FIX] Mismatch detected for {model_path}: config={current_vocab_size} vs weights={actual_vocab_size}. Fixing config.json...")
        config_data["vocab_size"] = actual_vocab_size
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
            print(f"[VOCAB_FIX] Successfully updated config.json in {model_path}")
        except Exception as e:
            print(f"[VOCAB_FIX] Failed to write updated config.json in {model_path}: {e}")



def eval_model_on_gpu(
    model_name,
    model_path,
    seed,
    config,
    config_path,
    result_dir,
    limit,
    gpu,
    resume,
    force,
    use_vllm=False,
    batch_size="auto",
):
    # Fix vocab_size mismatch if needed before starting evaluations
    fix_model_vocab_size_if_needed(model_path)

    safety_tasks = config["data"]["eval"]["safety_tasks"]
    utility_task_groups = config["data"]["eval"]["utility_task_groups"]

    # 手法名の抽出
    if "sst_merge_v3_ablation" in model_name:
        if "data_free_sst" in model_name:
            method = "ablation/datafree"
        elif "diagonal_sst" in model_name:
            method = "ablation/sst"
        else:
            method = "ablation/other"
    else:
        method_pattern = re.compile(r'^sst_merge_v3_main_(.*?)_(safety|math|medical|utility|inst|alpha|k\d)')
        match_method = method_pattern.match(model_name)
        if match_method:
            method = match_method.group(1)
        else:
            prefix = "sst_merge_v3_main_"
            if model_name.startswith(prefix):
                idx = model_name.find(f"_seed{seed}")
                method_part = model_name[len(prefix):idx] if idx != -1 else model_name[len(prefix):]
                method = method_part.strip('_')
            else:
                method = "unknown_method"

    # パターン名の抽出 (safety+math, safety+code, safety+medical, safety+math+code+medical)
    pattern = "unknown_pattern"
    for p in ["safety+math+code+medical", "safety+math", "safety+code", "safety+medical"]:
        if f"_{p}_" in model_name:
            pattern = p
            break

    # 出力先ディレクトリの作成 (seed -> pattern -> method)
    target_dir = os.path.join(result_dir, f"seed{seed}", pattern, method)
    os.makedirs(target_dir, exist_ok=True)

    log_prefix = os.path.join("logs", "vllm") if use_vllm else "logs"
    log_dir = os.path.join(
        log_prefix,
        f"v3_merged_eval_parallel_{limit}_seed{seed}",
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{model_name}_seed{seed}.log")
    failed = []

    if safety_tasks:
        tasks_str = ",".join(safety_tasks)
        base_cmd = [
            sys.executable,
            "scripts/eval/eval_safety.py",
            "--model_path", model_path,
            "--config", config_path,
            "--tasks", tasks_str,
            "--output_dir", target_dir,
            "--model_name", model_name,
            "--limit", str(limit),
            "--batch_size", str(batch_size),
        ]
        if use_vllm:
            base_cmd.append("--use_vllm")
        code = run_cmd(
            base_cmd,
            gpu=gpu,
            resume=resume,
            log_file=log_file,
            force=force,
        )
        if code != 0:
            for task in safety_tasks:
                failed.append(f"{target_dir}/{model_name}_{task}_safety.json")

    for domain, domain_tasks in utility_task_groups.items():
        if not domain_tasks:
            continue
        tasks_str = ",".join(domain_tasks)
        out = f"{target_dir}/{model_name}_utility_{domain}.json"
        base_cmd = [
            sys.executable,
            "scripts/eval/eval_utility.py",
            "--model_path", model_path,
            "--config", config_path,
            "--tasks", tasks_str,
            "--output_file", out,
            "--limit", str(limit),
            "--batch_size", str(batch_size),
        ]
        if use_vllm:
            base_cmd.append("--use_vllm")
        code = run_cmd(
            base_cmd,
            gpu=gpu,
            resume=resume,
            log_file=log_file,
            force=force,
        )
        if code != 0:
            failed.append(out)

    out = f"{target_dir}/{model_name}_alpaca_eval2.json"
    base_cmd = [
        sys.executable,
        "scripts/eval/eval_alpaca.py",
        "--model_path", model_path,
        "--config", config_path,
        "--output_file", out,
        "--limit", str(limit),
        "--batch_size", str(batch_size),
    ]
    if use_vllm:
        base_cmd.append("--use_vllm")
    code = run_cmd(
        base_cmd,
        gpu=gpu,
        resume=resume,
        log_file=log_file,
        force=force,
    )
    if code != 0:
        failed.append(out)

    inst_ds_list = ["evol_code", "medalpaca"]
    datasets_str = ",".join(inst_ds_list)
    base_cmd = [
        sys.executable,
        "scripts/eval/eval_instruction_datasets.py",
        "--model_path", model_path,
        "--config", config_path,
        "--datasets", datasets_str,
        "--output_dir", target_dir,
        "--model_name", model_name,
        "--limit", str(limit),
        "--batch_size", str(batch_size),
    ]
    if use_vllm:
        base_cmd.append("--use_vllm")
    code = run_cmd(
        base_cmd,
        gpu=gpu,
        resume=resume,
        log_file=log_file,
        force=force,
    )
    if code != 0:
        for inst_ds in inst_ds_list:
            failed.append(f"{target_dir}/{model_name}_inst_{inst_ds}.json")

    return {
        "model_name": model_name,
        "model_path": model_path,
        "seed": seed,
        "gpu": gpu,
        "log_file": log_file,
        "failed": failed,
    }


def worker_for_gpu(gpu, jobs, config, config_path, result_dir, limit, resume, force, use_vllm, batch_size="auto"):
    results = []
    print(f"[GPU {gpu}] assigned jobs: {len(jobs)}")

    for model_name, model_path, seed in jobs:
        result = eval_model_on_gpu(
            model_name=model_name,
            model_path=model_path,
            seed=seed,
            config=config,
            config_path=config_path,
            result_dir=result_dir,
            limit=limit,
            gpu=gpu,
            resume=resume,
            force=force,
            use_vllm=use_vllm,
            batch_size=batch_size,
        )
        results.append(result)

        if result["failed"]:
            print(
                f"[DONE with failures] {result['model_name']} "
                f"seed={result['seed']} on GPU {result['gpu']} "
                f"log={result['log_file']}"
            )
        else:
            print(
                f"[DONE] {result['model_name']} "
                f"seed={result['seed']} on GPU {result['gpu']} "
                f"log={result['log_file']}"
            )

    return results


def main():
    args = parse_args()
    config = load_config(args.config)

    gpus = [g.strip() for g in args.gpus.split(",") if g.strip()]
    if not gpus:
        raise ValueError("No GPUs specified. Example: --gpus 0,1,2")

    selected_patterns = None
    if args.patterns is not None:
        selected_patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]

    result_dir = get_results_dir(args.limit, target="merged", use_vllm=args.use_vllm)
    os.makedirs(result_dir, exist_ok=True)

    merged_models = collect_merged_models(
        config=config,
        seeds=args.seeds,
        selected_patterns=selected_patterns,
    )

    if args.reverse:
        merged_models = list(reversed(merged_models))

    if args.list_models:
        for idx, (model_name, model_path, seed) in enumerate(merged_models):
            print(f"{idx}\tseed={seed}\t{model_name}\t{model_path}")
        return

    if args.model_index is not None:
        if 0 <= args.model_index < len(merged_models):
            target_item = merged_models[args.model_index]
            if not is_successful_merge_dir(target_item[1]):
                print(f"[SINGLE MODEL MODE] Model index {args.model_index}: seed={target_item[2]} {target_item[0]} was not successfully merged. Skipping.")
                return
            merged_models = [target_item]
            print(f"[SINGLE MODEL MODE] Evaluating Index {args.model_index}: seed={target_item[2]} {target_item[0]}")
        else:
            print(f"Warning: model_index {args.model_index} is out of bounds (0..{len(merged_models)-1}).")
            print("This usually happens if the configuration was modified (shrinking the expected number of models) after the Slurm array was submitted.")
            print("Exiting gracefully without error.")
            return
    else:
        merged_models = [m for m in merged_models if is_successful_merge_dir(m[1])]

    print("\n==============================")
    print("Models to be evaluated")
    print("==============================")

    for i, (model_name, model_path, seed) in enumerate(merged_models, 1):
        print(f"{i:3d}. seed={seed}  {model_name}")
        print(f"     {model_path}")

    print("==============================")
    print(f"Total models: {len(merged_models)}")
    print("==============================\n")

    print(f"Using result directory: {result_dir}")
    print(f"Seeds: {args.seeds}")
    print(f"GPUs: {gpus}")
    print(f"Patterns: {selected_patterns if selected_patterns is not None else 'all'}")
    print(f"Reverse: {args.reverse}")
    print(f"Resume: {args.resume}")
    print(f"Force: {args.force}")
    print(f"Found successful merged models: {len(merged_models)}")

    if not merged_models:
        print("No successful merged models found.")
        return

    jobs_by_gpu = {gpu: [] for gpu in gpus}

    for i, job in enumerate(merged_models):
        gpu = gpus[i % len(gpus)]
        jobs_by_gpu[gpu].append(job)

    results = []

    with ThreadPoolExecutor(max_workers=len(gpus)) as executor:
        futures = []

        for gpu, jobs in jobs_by_gpu.items():
            futures.append(
                executor.submit(
                    worker_for_gpu,
                    gpu,
                    jobs,
                    config,
                    args.config,
                    result_dir,
                    args.limit,
                    args.resume,
                    args.force,
                    getattr(args, "use_vllm", False),
                    args.batch_size,
                )
            )

        for fut in as_completed(futures):
            results.extend(fut.result())

    seed_tag = "-".join(str(seed) for seed in args.seeds)

    list_path = os.path.join(result_dir, f"evaluation_targets_seeds{seed_tag}.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        f.write("Evaluation Targets\n")
        f.write("==================\n\n")
        for i, (model_name, model_path, seed) in enumerate(merged_models, 1):
            f.write(f"{i:3d}. seed={seed}  {model_name}\n")
            f.write(f"     {model_path}\n\n")

    summary_path = os.path.join(result_dir, f"merge_eval_parallel_seeds{seed_tag}_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()