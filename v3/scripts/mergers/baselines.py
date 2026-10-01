import os
import sys
import subprocess


def infer_led_order(util_path):
    p = util_path.lower()

    if "math" in p:
        return "math"
    if "code" in p or "coder" in p:
        return "code"
    if "med" in p or "medical" in p:
        return "medical"

    raise ValueError(f"Cannot infer LED-Merging utility order from path: {util_path}")


def validate_led_config(config, util_path):
    led_cfg = config.get("led_merging", {})
    require_scores = led_cfg.get("require_precomputed_scores", True)

    if not require_scores:
        return

    score_root = led_cfg.get("score_root", "baselines/LED-Merging/locate/score")
    util_order = infer_led_order(util_path)

    required_dirs = [
        os.path.join(score_root, "safety"),
        os.path.join(score_root, util_order),
    ]

    missing = [d for d in required_dirs if not os.path.exists(d)]

    if missing:
        raise FileNotFoundError(
            "LED-Merging precomputed score directories are missing: "
            + ", ".join(missing)
        )


def run_led_merging(output_dir, base_model, util_path, safe_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    led_root = os.path.abspath(os.path.join(script_dir, "../../baselines/LED-Merging"))
    script_path = os.path.join(led_root, "merge_llms.py")

    if not os.path.exists(script_path):
        raise RuntimeError(f"LED-Merging script not found: {script_path}")

    util_order = infer_led_order(util_path)

    safe_path_abs = os.path.abspath(safe_path)
    output_dir_abs = os.path.abspath(output_dir)

    cmd = [
        sys.executable,
        script_path,
        "--models_to_merge", safe_path_abs, util_path,
        "--pretrained_model_name", base_model,
        "--merging_method_name", "top_merging",
        "--scaling_coefficient", "0.9",
        "--mask_apply_method", "task_arithmetic",
        "--fuse_rates", "0.5", "0.5",
        "--orders", "safety", util_order,
        "--fuse_types", "o", "o",
        "--fuse_patterns", "01", "01",
        "--save", output_dir_abs,
        "--model_ft_name", "llama2",
        "--model_base_name", "llama2-base",
    ]

    print(f"Running LED-Merging: {' '.join(cmd)}")
    res = subprocess.run(cmd, text=True, cwd=led_root)

    if res.returncode != 0:
        raise RuntimeError("LED-Merging execution failed.")


def run_safemerge(output_dir, base_model, util_lora_path, safe_lora_path, unaligned_path, aligned_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "../../baselines/SafeMERGE/get_safemerge_model.py")

    if not os.path.exists(script_path):
        raise RuntimeError(f"SafeMERGE script not found: {script_path}")

    cmd = [
        sys.executable,
        script_path,
        "--base_model_id", base_model,
        "--finetuned_model_id", util_lora_path,
        "--safety_model_id", safe_lora_path,
        "--safelora_unaligned_model_id", unaligned_path,
        "--safelora_aligned_model_id", aligned_path,
        "--output_path", output_dir,
    ]

    res = subprocess.run(cmd, text=True)

    if res.returncode != 0:
        raise RuntimeError("SafeMERGE execution failed.")


def run_mergealign(output_dir, util_path, safe_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(
        script_dir,
        "../../baselines/MergeAlign/merging/lm_cocktail/lmcocktail_merge_align.py",
    )

    if not os.path.exists(script_path):
        raise RuntimeError(f"MergeAlign script not found: {script_path}")

    cmd = [
        sys.executable,
        script_path,
        "--all_types",
        "--temp", "1.0",
        "--max_per_task", "100",
        "--model_names", safe_path, util_path,
        "--dataset_path", "data/response_dataframe.csv",
        "--output_path", output_dir,
    ]

    res = subprocess.run(cmd, text=True)

    if res.returncode != 0:
        raise RuntimeError("MergeAlign execution failed.")


def run_matena_fisher_baseline(base_model, all_models, all_fim, fisher_floor=1e-6, normalize_fishers=True):
    """
    Wrapper for matena_fisher external baseline.
    """
    from matena_fisher import run_matena_fisher
    return run_matena_fisher(
        base_model=base_model,
        all_models=all_models,
        all_fim=all_fim,
        fisher_floor=fisher_floor,
        normalize_fishers=normalize_fishers,
    )
