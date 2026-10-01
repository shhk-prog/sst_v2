import os
import sys
import argparse
import subprocess
from pathlib import Path


ROOT = Path("/mnt/nas/home/hiromi/src/sst_v2/v3").resolve()
LED_LOCATE = ROOT / "baselines" / "LED-Merging" / "locate"
PYTHON = ROOT / "venv_led" / "bin" / "python"


MODEL_ALIASES = {
    "llama2-base": "meta-llama/Llama-2-7b-hf",
    "llama2-math": "WizardLMTeam/WizardMath-7B-V1.0",
    "llama2-code": "vanillaOVO/WizardCoder-Python-7B-V1.0",
    "llama2-medical": "medalpaca/medalpaca-7b",
    "llama2-safety-seed42": str(ROOT / "models" / "temp_safety_full_seed42"),
    "llama2-safety-seed43": str(ROOT / "models" / "temp_safety_full_seed43"),
    "llama2-safety-seed44": str(ROOT / "models" / "temp_safety_full_seed44"),
}


def run(cmd, cwd=ROOT, env=None):
    print("\nRunning:", " ".join(map(str, cmd)))
    res = subprocess.run(cmd, cwd=cwd, env=env, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd))}")


def ensure_temp_safety_models(config_path):
    for seed in [42, 43, 44]:
        out_dir = ROOT / "models" / f"temp_safety_full_seed{seed}"
        if (out_dir / "config.json").exists():
            print(f"exists: {out_dir}")
            continue

        run([
            ROOT / "venv_v3" / "bin" / "python",
            "scripts/merge.py",
            "--config", config_path,
            "--method", "ties",
            "--alpha", "1.0",
            "--pattern", "safety+math",
            "--seed", str(seed),
            "--output_dir", f"models/_tmp_create_safety_full_seed{seed}",
        ])


def patch_led_locate_main():
    main_py = LED_LOCATE / "main.py"
    text = main_py.read_text(encoding="utf-8")

    insert = "\n# Auto-added aliases for SST-Merge LED score generation\n"
    for k, v in MODEL_ALIASES.items():
        insert += f'modeltype2path["{k}"] = "{v}"\n'

    if "Auto-added aliases for SST-Merge LED score generation" not in text:
        pos = text.find("\ndef get_llm(")
        if pos == -1:
            raise RuntimeError("Could not find get_llm() in LED locate/main.py")
        text = text[:pos] + insert + text[pos:]

    old = "if model_name in ["
    if old in text and "if model_name in modeltype2path:" not in text:
        start = text.find(old)
        end = text.find("]:", start)
        if end == -1:
            raise RuntimeError("Could not patch get_llm model allow-list")
        text = text[:start] + "if model_name in modeltype2path" + text[end + 1:]

    main_py.write_text(text, encoding="utf-8")
    print(f"patched: {main_py}")


def patch_led_medical_scorebook():
    for rel in [
        "model_merging_methods/merging_methods.py",
        "model_merging_methods/mask_weights_utils.py",
    ]:
        path = LED_LOCATE.parent / rel
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8")
        if '"medical"' not in text and '"code"' in text:
            text = text.replace(
                '"code" : "./locate/score/code/{model_ft_name}-code/wanda_score",',
                '"code" : "./locate/score/code/{model_ft_name}-code/wanda_score",\n'
                '    "medical" : "./locate/score/medical/{model_ft_name}-medical/wanda_score",',
            )
            text = text.replace(
                '"base-code" : "./locate/score/code/{model_base_name}/wanda_score",',
                '"base-code" : "./locate/score/code/{model_base_name}/wanda_score",\n'
                '    "base-medical" : "./locate/score/medical/{model_base_name}/wanda_score",',
            )

        path.write_text(text, encoding="utf-8")


def make_score(model, model_base, prune_data, save_dir, gpu):
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)

    run([
        PYTHON,
        "main.py",
        "--model", model,
        "--model_base", model_base,
        "--prune_method", "wandg",
        "--prune_data", prune_data,
        "--sparsity_ratio", "0.01",
        "--sparsity_type", "unstructured",
        "--neg_prune",
        "--save", save_dir,
        "--dump_wanda_score",
    ], cwd=LED_LOCATE, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--skip_patch", action="store_true")
    parser.add_argument("--skip_temp_safety", action="store_true")
    parser.add_argument("--include_medical", action="store_true")
    args = parser.parse_args()

    if not args.skip_temp_safety:
        ensure_temp_safety_models(args.config)

    if not args.skip_patch:
        patch_led_locate_main()
        patch_led_medical_scorebook()

    jobs = []

    for seed in [42, 43, 44]:
        jobs.append((
            f"llama2-safety-seed{seed}",
            "llama2-base",
            "align",
            f"./score/safety/llama2-seed{seed}-instruct",
        ))

    jobs += [
        ("llama2-base", "llama2-base", "align", "./score/safety/llama2-base"),
        ("llama2-math", "llama2-base", "math", "./score/math/llama2-math"),
        ("llama2-base", "llama2-base", "math", "./score/math/llama2-base"),
        ("llama2-code", "llama2-base", "code", "./score/code/llama2-code"),
        ("llama2-base", "llama2-base", "code", "./score/code/llama2-base"),
    ]

    if args.include_medical:
        jobs += [
            ("llama2-medical", "llama2-base", "medical", "./score/medical/llama2-medical"),
            ("llama2-base", "llama2-base", "medical", "./score/medical/llama2-base"),
        ]

    for model, base, data, save in jobs:
        score_dir = LED_LOCATE / save / "wanda_score"
        if score_dir.exists() and any(score_dir.glob("*.pkl")):
            print(f"skip existing: {score_dir}")
            continue

        make_score(model, base, data, save, args.gpu)

    print("\nLED score generation completed.")


if __name__ == "__main__":
    main()
