import os
import sys
import json
import time
import argparse
import traceback
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    import psutil
except ImportError:
    psutil = None

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import steering_hook

from mergers import (
    MERGEKIT_METHODS,
    PROPOSED_METHODS,
    CUSTOM_BASELINES,
    SPECIAL_BASELINES,
    TARGET_MODULE_KEYWORDS,
    MERGEKIT_METHOD_MAP,
    LAYER_PRIOR_CHOICES,
    FIM_REQUIRED_METHODS,
    clear_cuda,
    to_model_ref,
    load_config,
    write_json,
    count_target_parameters,
    build_models_to_merge,
    require_single_utility,
    temp_safety_full_dir,
    temp_util_lora_dir,
    create_full_safety_model,
    convert_full_to_lora,
    load_or_estimate_fim,
    merge_sst,
    run_mergekit,
    run_safemerge,
    run_mergealign,
    validate_led_config,
    run_led_merging,
    run_matena_fisher_baseline,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")

    parser.add_argument(
        "--method",
        type=str,
        required=True,
        choices=PROPOSED_METHODS + MERGEKIT_METHODS + CUSTOM_BASELINES + SPECIAL_BASELINES,
    )

    parser.add_argument("--sst_ratio", type=str, default=None)
    parser.add_argument("--variant", type=str, default=None)
    parser.add_argument("--mask_type", type=str, default=None)
    parser.add_argument("--layer_wise", action="store_true")

    parser.add_argument("--norm_standardization", action="store_true", help="Standardize task vector norms")
    parser.add_argument("--fisher_normalization", action="store_true", help="Normalize FIM matrices")
    parser.add_argument("--norm_clipping", action="store_true", help="Clip maximum weight norm explosion")
    parser.add_argument("--max_norm_ratio", type=float, default=1.5, help="Max ratio for norm clipping")

    parser.add_argument(
        "--layer_prior",
        type=str,
        default=None,
        choices=LAYER_PRIOR_CHOICES,
    )

    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--k", type=float, default=None)
    parser.add_argument("--sample_size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, required=True)

    parser.add_argument(
        "--pattern",
        type=str,
        default="safety+math",
        choices=[
            "safety+math",
            "safety+code",
            "safety+medical",
            "safety+math+code+medical",
        ],
    )

    parser.add_argument(
        "--experiment_type",
        type=str,
        default="manual",
        choices=["main", "ablation", "manual"],
    )

    parser.add_argument("--implementation", type=str, default="custom")

    parser.add_argument("--utility_dataset_path", type=str, default=None)
    parser.add_argument("--safety_dataset_path", type=str, default=None)
    parser.add_argument("--fim_path", type=str, default=None)
    parser.add_argument("--cached_gradient_path", type=str, default=None)
    parser.add_argument("--cached_fisher_path", type=str, default=None)
    parser.add_argument("--eval_dataset_path", type=str, default=None)
    parser.add_argument("--fim_dataset_path", type=str, default=None)

    parser.add_argument("--fim_cache_dir", type=str, default="cache/fim")
    parser.add_argument("--no_fim_cache", action="store_true")
    parser.add_argument("--overwrite_fim_cache", action="store_true")

    return parser.parse_args()


def apply_config_defaults(args, config):
    main_cfg = config.get("merge", {}).get("main", {})

    if args.k is None:
        args.k = float(main_cfg.get("k_values", [0.20])[0])

    if args.sample_size is None:
        args.sample_size = int(
            main_cfg.get(
                "sample_size",
                config["data"]["fim"].get("default_sample_size", 500),
            )
        )

    if args.sst_ratio is None:
        args.sst_ratio = main_cfg.get("sst_ratio", "Fh/Fb")

    if args.variant is None:
        args.variant = main_cfg.get("variant", "interpolation")

    if args.mask_type is None:
        args.mask_type = main_cfg.get("mask", "hard mask")

    if args.layer_prior is None:
        args.layer_prior = main_cfg.get("layer_prior", "uniform")

    if not args.layer_wise:
        args.layer_wise = bool(main_cfg.get("layer_wise", False))


def get_runtime_stats():
    stats = {}

    if psutil is not None:
        process = psutil.Process(os.getpid())
        stats["cpu_memory_rss_gb"] = process.memory_info().rss / 1024**3
        stats["cpu_memory_vms_gb"] = process.memory_info().vms / 1024**3
    else:
        stats["cpu_memory_rss_gb"] = None
        stats["cpu_memory_vms_gb"] = None

    if torch.cuda.is_available():
        stats["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated() / 1024**3
        stats["gpu_memory_reserved_gb"] = torch.cuda.memory_reserved() / 1024**3
        stats["gpu_max_memory_allocated_gb"] = torch.cuda.max_memory_allocated() / 1024**3
        stats["gpu_max_memory_reserved_gb"] = torch.cuda.max_memory_reserved() / 1024**3
        stats["cuda_device_count"] = torch.cuda.device_count()
        stats["cuda_device_name"] = torch.cuda.get_device_name(0)
    else:
        stats["gpu_memory_allocated_gb"] = None
        stats["gpu_memory_reserved_gb"] = None
        stats["gpu_max_memory_allocated_gb"] = None
        stats["gpu_max_memory_reserved_gb"] = None
        stats["cuda_device_count"] = 0
        stats["cuda_device_name"] = None

    return stats


class RuntimeLogger:
    def __init__(self):
        self.records = []
        self._active = {}

    def start(self, stage):
        self._active[stage] = {
            "start_time": time.time(),
            "start_stats": get_runtime_stats(),
        }

    def end(self, stage):
        if stage not in self._active:
            return

        end_time = time.time()
        start = self._active.pop(stage)

        self.records.append({
            "stage": stage,
            "elapsed_sec": end_time - start["start_time"],
            "start_stats": start["start_stats"],
            "end_stats": get_runtime_stats(),
        })

    def save(self, path):
        write_json(path, self.records)

    def total_elapsed_sec(self):
        return float(sum(r.get("elapsed_sec", 0.0) for r in self.records))

    def peak_gpu_memory_gb(self):
        peaks = []
        for r in self.records:
            val = r.get("end_stats", {}).get("gpu_max_memory_allocated_gb")
            if val is not None:
                peaks.append(val)
        return max(peaks) if peaks else None


def get_complexity_info(args, num_utility_models, num_target_parameters=None):
    complexity_map = {
        "diagonal_sst": "O((N_b + N_h) * C_backward + P)",
        "data_free_sst": "O(P)",
        "fisher_weighted": "O((N_b + N_h) * C_backward + P)",
        "matena_fisher": "O(N * C_backward + P)",
        "task_arithmetic": "O(P)",
        "ties": "O(P log P) or O(P), depending on top-k/masking implementation",
        "dare": "O(P)",
        "della": "O(P)",
        "mergealign": "method-dependent external baseline",
        "safemerge": "method-dependent external baseline + pseudo-LoRA SVD conversion",
        "led_merging": "method-dependent external baseline requiring precomputed score/mask files",
    }

    fim_required = args.method in FIM_REQUIRED_METHODS

    return {
        "method": args.method,
        "experiment_type": args.experiment_type,
        "pattern": args.pattern,
        "num_utility_models": num_utility_models,
        "num_target_parameters": num_target_parameters,
        "fim_required": fim_required,
        "data_free": args.method == "data_free_sst",
        "num_fim_samples_per_dataset": args.sample_size if fim_required else 0,
        "asymptotic_cost": complexity_map.get(args.method, "unknown"),
        "symbols": {
            "P": "number of merged parameters",
            "N_b": "number of benign FIM samples",
            "N_h": "number of harmful FIM samples",
            "C_backward": "cost of one forward-backward pass",
        },
    }


def write_complexity_summary(args, runtime_logger, num_utility_models, num_target_parameters=None):
    summary = get_complexity_info(
        args=args,
        num_utility_models=num_utility_models,
        num_target_parameters=num_target_parameters,
    )

    summary.update({
        "elapsed_total_sec": runtime_logger.total_elapsed_sec(),
        "peak_gpu_memory_gb": runtime_logger.peak_gpu_memory_gb(),
        "runtime_profile_path": os.path.join(args.output_dir, "runtime_profile.json"),
        "timestamp": datetime.now().isoformat(),
    })

    write_json(os.path.join(args.output_dir, "complexity_summary.json"), summary)
    return summary


def write_failed_metadata(args, error, stage, extra=None):
    os.makedirs(args.output_dir, exist_ok=True)

    metadata = {
        "status": "failed",
        "mockup": True,
        "stage": stage,
        "error": str(error),
        "traceback": traceback.format_exc(),
        "merge_method": args.method,
        "experiment_type": getattr(args, "experiment_type", "manual"),
        "pattern": args.pattern,
        "random_seed": args.seed,
        "output_dir": args.output_dir,
        "execution_command": " ".join(sys.argv),
        "timestamp": datetime.now().isoformat(),
    }

    if extra:
        metadata.update(extra)

    path = os.path.join(args.output_dir, "merge_metadata.json")
    write_json(path, metadata)
    print(f"Failed metadata saved to {path}")


def save_success_metadata(
    args, config, input_models, temp_paths=None, notes=None,
    complexity_summary=None, method_metadata=None,
):
    metadata = {
        "status": "success",
        "mockup": False,
        "base_model": config["models"]["base_model"],
        "merge_method": args.method,
        "experiment_type": args.experiment_type,
        "pattern": args.pattern,
        "random_seed": args.seed,
        "input_models": input_models,
        "temporary_paths": temp_paths or {},
        "notes": notes or [],
        "method_metadata": method_metadata or {},
        "hyperparameters": {
            "alpha": args.alpha,
            "k": args.k,
            "sst_ratio": args.sst_ratio,
            "variant": args.variant,
            "mask_type": args.mask_type,
            "layer_wise": args.layer_wise,
            "layer_prior": args.layer_prior,
            "sample_size": args.sample_size if args.method in FIM_REQUIRED_METHODS else None,
            "uses_fim": args.method in FIM_REQUIRED_METHODS,
            "fim_cache_dir": args.fim_cache_dir,
            "no_fim_cache": args.no_fim_cache,
            "overwrite_fim_cache": args.overwrite_fim_cache,
            "norm_standardization": args.norm_standardization,
            "fisher_normalization": args.fisher_normalization,
            "norm_clipping": args.norm_clipping,
            "max_norm_ratio": args.max_norm_ratio,
        },
        "complexity": complexity_summary or {},
        "git_commit_hash": "N/A",
        "execution_command": " ".join(sys.argv),
        "timestamp": datetime.now().isoformat(),
    }

    write_json(os.path.join(args.output_dir, "merge_metadata.json"), metadata)
    print("Metadata saved.")


def execute_merge(args, config):
    apply_config_defaults(args, config)

    runtime_logger = RuntimeLogger()

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    runtime_logger.start("total_merge_execution")

    args.base_model = config["models"]["base_model"]

    if args.method in MERGEKIT_METHODS:
        args.implementation = "mergekit"

    steering_hook.verify_experiment_config(args)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_model_name = config["models"]["base_model"]
    models_to_merge, safety_model_path = build_models_to_merge(config, args)

    os.makedirs(args.output_dir, exist_ok=True)

    input_models = {"base": base_model_name, **models_to_merge}
    num_utility_models = len([k for k in models_to_merge if k != "safety"])
    num_target_parameters = None

    temp_paths = {}
    notes = []

    if args.method in MERGEKIT_METHODS:
        temp_safety_full = create_full_safety_model(
            base_model_name,
            safety_model_path,
            temp_safety_full_dir(args),
            args,
            runtime_logger=runtime_logger,
        )

        temp_paths["temp_safety_full"] = temp_safety_full

        models_to_merge_full = models_to_merge.copy()
        models_to_merge_full["safety"] = temp_safety_full

        runtime_logger.start("mergekit_merge")
        run_mergekit(
            args.output_dir,
            args.method,
            to_model_ref(base_model_name),
            {k: to_model_ref(v) for k, v in models_to_merge_full.items()},
            args.alpha,
        )
        runtime_logger.end("mergekit_merge")

    elif args.method == "safemerge":
        util_key, util_path = require_single_utility(args, models_to_merge)

        notes.append("SafeMERGE uses SVD pseudo-LoRA conversion for utility model.")

        temp_util_lora = convert_full_to_lora(
            base_model_name,
            util_path,
            temp_util_lora_dir(args, util_key),
            args,
            runtime_logger=runtime_logger,
        )

        temp_safety_full = create_full_safety_model(
            base_model_name,
            safety_model_path,
            temp_safety_full_dir(args),
            args,
            runtime_logger=runtime_logger,
        )

        temp_paths["temp_util_lora"] = temp_util_lora
        temp_paths["temp_safety_full"] = temp_safety_full

        runtime_logger.start("safemerge_external")
        run_safemerge(
            args.output_dir,
            base_model_name,
            temp_util_lora,
            safety_model_path,
            base_model_name,
            temp_safety_full,
        )
        runtime_logger.end("safemerge_external")

        runtime_logger.start("safemerge_load_and_merge")
        import glob
        from peft import PeftModel
        peft_dirs = glob.glob(os.path.join(args.output_dir, "safemerge_*"))
        if not peft_dirs:
            raise FileNotFoundError("Could not find generated SafeMERGE PEFT directory")
        peft_dir = peft_dirs[0]

        print(f"Loading generated PEFT model from {peft_dir} to merge into full model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
        ).to(device)
        merged_model = PeftModel.from_pretrained(base_model, peft_dir)
        merged_model = merged_model.merge_and_unload()

        merged_model.save_pretrained(args.output_dir)
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=False)
        tokenizer.save_pretrained(args.output_dir)

        del base_model
        del merged_model
        clear_cuda()
        runtime_logger.end("safemerge_load_and_merge")

    elif args.method == "mergealign":
        _, util_path = require_single_utility(args, models_to_merge)

        temp_safety_full = create_full_safety_model(
            base_model_name,
            safety_model_path,
            temp_safety_full_dir(args),
            args,
            runtime_logger=runtime_logger,
            tokenizer_source=util_path,
        )

        temp_paths["temp_safety_full"] = temp_safety_full

        runtime_logger.start("mergealign_external")
        run_mergealign(args.output_dir, util_path, temp_safety_full)
        runtime_logger.end("mergealign_external")

    elif args.method == "led_merging":
        _, util_path = require_single_utility(args, models_to_merge)

        validate_led_config(config, util_path)

        temp_safety_full = create_full_safety_model(
            base_model_name,
            safety_model_path,
            temp_safety_full_dir(args),
            args,
            runtime_logger=runtime_logger,
        )

        temp_paths["temp_safety_full"] = temp_safety_full

        runtime_logger.start("led_merging_external")
        run_led_merging(args.output_dir, base_model_name, util_path, temp_safety_full)
        runtime_logger.end("led_merging_external")

    elif args.method in PROPOSED_METHODS + CUSTOM_BASELINES:
        data_free_enabled = False

        try:
            if args.method == "data_free_sst":
                steering_hook.enable_data_free_monitoring()
                data_free_enabled = True

            runtime_logger.start("load_tokenizer")
            tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=False)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            runtime_logger.end("load_tokenizer")

            runtime_logger.start("load_base_model_reference")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
            ).to(device)
            num_target_parameters = count_target_parameters(base_model)
            runtime_logger.end("load_base_model_reference")

            runtime_logger.start("load_safety_lora_and_merge")
            from peft import PeftModel

            safety_base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
            ).to(device)

            safe_model = PeftModel.from_pretrained(safety_base_model, safety_model_path)
            safe_model = safe_model.merge_and_unload()
            runtime_logger.end("load_safety_lora_and_merge")

            util_models = {}
            fim_b_dict = {}

            for m_name, m_path in models_to_merge.items():
                if m_name == "safety":
                    continue

                runtime_logger.start(f"load_utility_model_{m_name}")
                util_models[m_name] = AutoModelForCausalLM.from_pretrained(
                    m_path,
                    torch_dtype=torch.float16,
                ).to(device)
                runtime_logger.end(f"load_utility_model_{m_name}")

                if args.method in FIM_REQUIRED_METHODS:
                    benign_dataset_path = config["data"]["fim"]["benign_datasets"][m_name]

                    args.fim_dataset_path = benign_dataset_path
                    args.eval_dataset_path = "data/eval/eval_benign.json"
                    steering_hook.verify_experiment_config(args)

                    runtime_logger.start(f"fim_benign_{m_name}")
                    fim_b_dict[m_name] = load_or_estimate_fim(
                        model=util_models[m_name],
                        dataset_path=benign_dataset_path,
                        sample_size=args.sample_size,
                        tokenizer=tokenizer,
                        device=device,
                        args=args,
                        config=config,
                        kind="benign",
                        domain=m_name,
                        model_path=m_path,
                    )
                    runtime_logger.end(f"fim_benign_{m_name}")

            fim_h = None

            if args.method in FIM_REQUIRED_METHODS:
                harmful_data_path = config["data"]["fim"]["harmful_dataset"]

                runtime_logger.start("fim_harmful")
                fim_h = load_or_estimate_fim(
                    model=safe_model,
                    dataset_path=harmful_data_path,
                    sample_size=args.sample_size,
                    tokenizer=tokenizer,
                    device=device,
                    args=args,
                    config=config,
                    kind="harmful",
                    domain="safety",
                    model_path=safety_model_path,
                )
                runtime_logger.end("fim_harmful")

            runtime_logger.start("weight_merge")

            if args.method == "matena_fisher":
                merged_state_dict, matena_info = run_matena_fisher_baseline(
                    base_model=base_model,
                    all_models={**util_models, "safety": safe_model},
                    all_fim={**fim_b_dict, "safety": fim_h},
                    fisher_floor=1e-6,
                    normalize_fishers=True,
                )
                fisher_weight_stats = {}

            else:
                merged_state_dict, fisher_weight_stats = merge_sst(
                    base_model=base_model,
                    util_models_dict=util_models,
                    safe_model=safe_model,
                    method=args.method,
                    sst_ratio=args.sst_ratio,
                    variant=args.variant,
                    mask_type=args.mask_type,
                    layer_wise=args.layer_wise,
                    layer_prior=args.layer_prior,
                    alpha=args.alpha,
                    k_ratio=args.k,
                    fim_b_dict=fim_b_dict,
                    fim_h=fim_h,
                    norm_standardization=args.norm_standardization,
                    fisher_normalization=args.fisher_normalization,
                    norm_clipping=args.norm_clipping,
                    max_norm_ratio=args.max_norm_ratio,
                )
                matena_info = None

            runtime_logger.end("weight_merge")

            runtime_logger.start("load_fresh_base_for_save")
            merged_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
            ).to(device)

            merged_model.load_state_dict(merged_state_dict, strict=False)
            runtime_logger.end("load_fresh_base_for_save")

            runtime_logger.start("save_merged_model")
            merged_model.save_pretrained(args.output_dir)
            tokenizer.save_pretrained(args.output_dir)
            runtime_logger.end("save_merged_model")

            if args.method == "fisher_weighted":
                write_json(
                    os.path.join(args.output_dir, "fisher_weights_summary.json"),
                    {
                        "method": "fisher_weighted",
                        "pattern": args.pattern,
                        "seed": args.seed,
                        "sample_size": args.sample_size,
                        "model_path": args.output_dir,
                        "num_parameters_recorded": len(fisher_weight_stats),
                        "per_parameter": fisher_weight_stats,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            if args.method == "matena_fisher" and matena_info is not None:
                write_json(
                    os.path.join(args.output_dir, "matena_fisher_info.json"),
                    {
                        **matena_info,
                        "pattern": args.pattern,
                        "seed": args.seed,
                        "sample_size": args.sample_size,
                        "model_path": args.output_dir,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            del base_model
            del safety_base_model
            del safe_model
            del merged_model

            for m in util_models.values():
                del m

            clear_cuda()

        finally:
            if data_free_enabled:
                steering_hook.disable_data_free_monitoring()

    else:
        raise ValueError(f"Unknown method: {args.method}")

    runtime_logger.end("total_merge_execution")
    runtime_logger.save(os.path.join(args.output_dir, "runtime_profile.json"))

    complexity_summary = write_complexity_summary(
        args=args,
        runtime_logger=runtime_logger,
        num_utility_models=num_utility_models,
        num_target_parameters=num_target_parameters,
    )

    method_metadata = {}
    if args.method == "matena_fisher":
        method_metadata["matena_fisher"] = {
            "implementation": "causallm_reimplementation",
            "reference_repo": "mmatena/model_merging",
            "paper": "Merging Models with Fisher-Weighted Averaging (NeurIPS 2022)",
            "formula": "theta = sum_i(F_i * theta_i) / (sum_i F_i + epsilon)",
            "normalize_fishers": True,
            "normalization": "global_l2",
            "fisher_floor": 1e-6,
            "fisher_target_params": "target_modules_only",
            "target_modules": TARGET_MODULE_KEYWORDS,
            "non_target_params_treatment": "use_base_model_weights",
            "reused_existing_fim_cache": True,
            "uses_cached_fim": True,
        }
        if matena_info is not None:
            method_metadata["matena_fisher"]["runtime_info"] = matena_info

    save_success_metadata(
        args=args,
        config=config,
        input_models=input_models,
        temp_paths=temp_paths,
        notes=notes,
        complexity_summary=complexity_summary,
        method_metadata=method_metadata,
    )


def main():
    args = parse_args()

    try:
        config = load_config(args.config)
        execute_merge(args, config)

    except Exception as e:
        print(f"Merge failed: {e}")
        write_failed_metadata(args, e, stage="merge")
        raise


if __name__ == "__main__":
    main()