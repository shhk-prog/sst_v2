"""
AlpacaEval 2 evaluation script.

Features:
  - Saves model outputs one response at a time
  - Can resume generation after interruption
  - Checks whether limit responses already exist
  - Runs alpaca_eval after generation is complete
"""

import os
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
os.environ["VLLM_ENABLE_V1"] = "0"
import sys
import gc
import json
import yaml
import torch
import argparse
import subprocess
import traceback

from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from dotenv import load_dotenv


def load_env_file():
    possible_paths = [
        "/mnt/nas/home/hiromi/src/.env",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
        os.path.abspath(os.path.join(os.getcwd(), "..", ".env")),
        os.path.abspath(".env"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Loading environment variables from {path}")
            load_dotenv(dotenv_path=path, override=True)
            break
    else:
        print("WARNING: .env file not found.")

    if os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY loaded.")
    else:
        print("WARNING: OPENAI_API_KEY not found in environment.")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch_size", type=str, default="8", help="Batch size for model generation (int or 'auto')")
    parser.add_argument("--skip_generation", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--use_vllm", action="store_true", help="Use vLLM for high-speed inference")
    return parser.parse_args()


def clear_cuda():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def write_json_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def expected_limit(limit, dataset_len=None):
    if limit > 0:
        return limit
    if dataset_len is not None:
        return dataset_len
    return 805


def get_model_device(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def save_failed_result(results_json_path, error, stage, extra=None):
    output = {
        "status": "failed",
        "mockup": True,
        "completed": False,
        "stage": stage,
        "error": str(error),
        "traceback": traceback.format_exc(),
    }

    if extra:
        output.update(extra)

    write_json_atomic(results_json_path, output)
    print(f"Failed result saved to {results_json_path}")


def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"WARNING: config file not found: {config_path}")
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def safe_name(path):
    return (
        str(path)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )


def get_limit_tag(limit):
    return "full" if limit == 0 else f"limit{limit}"


def load_model_and_tokenizer(model_path, config):
    is_peft = os.path.exists(os.path.join(model_path, "adapter_config.json"))

    if is_peft:
        from peft import PeftModel

        base_model = config.get("models", {}).get("base_model")
        if not base_model:
            raise ValueError(
                "PEFT adapter detected, but config['models']['base_model'] is missing."
            )

        print(f"Detected PEFT adapter: {model_path}")
        print(f"Loading base model: {base_model}")

        tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=False)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        model = PeftModel.from_pretrained(model, model_path)
        model.eval()

    else:
        print(f"Loading full model: {model_path}")

        tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        model.eval()

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def load_alpaca_eval_dataset():
    print("Loading AlpacaEval dataset...")

    try:
        return load_dataset(
            "json",
            data_files="https://huggingface.co/datasets/tatsu-lab/alpaca_eval/resolve/main/alpaca_eval.json",
            split="train",
        )
    except Exception as e:
        print(f"Failed to load via raw JSON, trying fallback: {e}")
        return load_dataset(
            "tatsu-lab/alpaca_eval",
            "alpaca_eval",
            split="eval",
            trust_remote_code=True,
        )


def normalize_samples(alpaca_dataset, limit):
    samples = list(alpaca_dataset)
    if limit > 0:
        samples = samples[:limit]

    normalized = []
    for i, item in enumerate(samples):
        normalized.append({
            "sample_id": i,
            "instruction": item["instruction"],
            "input": item.get("input", ""),
        })

    return normalized


def load_existing_outputs(path):
    data = load_json(path)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]

    return []


def has_required_outputs(path, required_n):
    outputs = load_existing_outputs(path)

    if len(outputs) < required_n:
        return False

    for r in outputs[:required_n]:
        if not isinstance(r, dict):
            return False
        if r.get("output") is None:
            return False
        if r.get("instruction") is None:
            return False

    return True


def save_model_outputs_checkpoint(path, outputs, metadata=None, completed=False):
    payload = {
        "status": "success" if completed else "running",
        "mockup": False,
        "completed": completed,
        "metadata": metadata or {},
        "num_results": len(outputs),
        "expected_n": len(outputs),
        "results": outputs,
    }

    write_json_atomic(path, payload)


def export_alpaca_eval_list(path):
    data = load_json(path)

    if isinstance(data, list):
        return path

    if isinstance(data, dict) and isinstance(data.get("results"), list):
        list_path = path.replace(".json", "_for_alpaca_eval.json")
        write_json_atomic(list_path, data["results"])
        return list_path

    raise ValueError(f"Invalid model outputs file: {path}")


def generate_one(model, tokenizer, instruction, input_text):
    if input_text:
        prompt = f"{instruction}\n\n{input_text}"
    else:
        prompt = instruction

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    )

    model_device = get_model_device(model)
    inputs = {k: v.to(model_device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def generate_batch(model, tokenizer, items):
    prompts = []
    for item in items:
        inst = item.get("instruction", "")
        inp = item.get("input", "")
        if inp:
            prompts.append(f"{inst}\n\n{inp}")
        else:
            prompts.append(inst)

    if not prompts:
        return []

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    old_padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"

    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=2048,
    )

    model_device = get_model_device(model)
    inputs = {k: v.to(model_device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    tokenizer.padding_side = old_padding_side

    input_len = inputs["input_ids"].shape[1]
    responses = []
    for out_ids in output_ids:
        gen_ids = out_ids[input_len:]
        responses.append(tokenizer.decode(gen_ids, skip_special_tokens=True).strip())

    return responses



def generate_model_outputs(model_path, alpaca_dataset, limit, output_json_path, config, force=False, args=None):
    samples = normalize_samples(alpaca_dataset, limit)
    required_n = len(samples)

    if required_n == 0:
        raise ValueError("No AlpacaEval samples found.")

    if not force and has_required_outputs(output_json_path, required_n):
        print(f"[SKIP] Completed model outputs exist: {output_json_path}")
        return output_json_path

    existing = load_existing_outputs(output_json_path)
    by_id = {
        r.get("sample_id"): r
        for r in existing
        if isinstance(r, dict) and r.get("sample_id") is not None
    }

    outputs = []
    generator_name = os.path.splitext(os.path.basename(output_json_path))[0]

    for sample in samples:
        old = by_id.get(sample["sample_id"])
        if old and old.get("output") is not None and not force:
            outputs.append(old)
        else:
            outputs.append({
                "sample_id": sample["sample_id"],
                "instruction": sample["instruction"],
                "input": sample["input"],
                "output": None,
                "generator": generator_name,
            })

    metadata = {
        "model_path": model_path,
        "limit": limit,
        "required_n": required_n,
    }

    save_model_outputs_checkpoint(output_json_path, outputs, metadata, completed=False)

    missing_indices = [
        i for i, r in enumerate(outputs)
        if r.get("output") is None
    ]

    bs_val = getattr(args, "batch_size", "8") if args else "8"
    if isinstance(bs_val, str) and bs_val.isdigit():
        batch_size = int(bs_val)
    elif isinstance(bs_val, int):
        batch_size = bs_val
    else:
        batch_size = 8

    print(f"Missing AlpacaEval generations: {len(missing_indices)} / {required_n} (batch_size={batch_size})")

    if not missing_indices:
        save_model_outputs_checkpoint(output_json_path, outputs, metadata, completed=True)
        return output_json_path

    print(f"Preparing model: {model_path}")
    
    if getattr(args, "use_vllm", False):
        print("Using vLLM engine for generation.")
        is_peft = os.path.exists(os.path.join(model_path, "adapter_config.json"))
        if is_peft:
            raise ValueError("vLLM does not support directly loading PEFT adapters in this script without --enable-lora. Please use merged models or disable --use_vllm.")
        
        from vllm import LLM, SamplingParams
        llm = LLM(model=model_path, trust_remote_code=True, tensor_parallel_size=1)
        
        # Prepare prompts
        prompts = []
        for idx in missing_indices:
            item = outputs[idx]
            inst = item.get("instruction", "")
            inp = item.get("input", "")
            if inp:
                prompts.append(f"{inst}\n\n{inp}")
            else:
                prompts.append(inst)
        
        sampling_params = SamplingParams(temperature=0.0, max_tokens=512)
        vllm_outputs = llm.generate(prompts, sampling_params)
        
        for idx, out in zip(missing_indices, vllm_outputs):
            outputs[idx]["output"] = out.outputs[0].text.strip()
            
        print(f"Generated {len(missing_indices)} missing responses via vLLM.")
        
        del llm
        clear_cuda()
    else:
        model, tokenizer = load_model_and_tokenizer(model_path, config)

        for b_start in range(0, len(missing_indices), batch_size):
            b_indices = missing_indices[b_start : b_start + batch_size]
            b_items = [outputs[idx] for idx in b_indices]
            b_gen_responses = generate_batch(model, tokenizer, b_items)

            for idx, resp in zip(b_indices, b_gen_responses):
                outputs[idx]["output"] = resp

            save_model_outputs_checkpoint(
                output_json_path,
                outputs,
                metadata,
                completed=False,
            )

            print(f"Generated {b_start + len(b_indices)}/{len(missing_indices)} missing, total_saved={b_indices[-1] + 1}/{required_n}")

        del model
        clear_cuda()

    save_model_outputs_checkpoint(output_json_path, outputs, metadata, completed=True)

    print(f"Model outputs saved to {output_json_path}")
    return output_json_path


def run_alpaca_eval(model_outputs_path, results_json_path):
    if not os.environ.get("OPENAI_API_KEY"):
        save_failed_result(
            results_json_path,
            error="OPENAI_API_KEY not set",
            stage="openai_api_key_check",
            extra={"model_outputs_path": model_outputs_path},
        )
        return

    alpaca_input_path = export_alpaca_eval_list(model_outputs_path)

    alpaca_out_dir = os.path.splitext(results_json_path)[0] + "_alpaca_eval_out"
    os.makedirs(alpaca_out_dir, exist_ok=True)

    alpaca_eval_bin = os.path.join(os.path.dirname(sys.executable), "alpaca_eval")
    if not os.path.exists(alpaca_eval_bin):
        alpaca_eval_bin = "alpaca_eval"

    cmd = [
        alpaca_eval_bin,
        "evaluate",
        "--model_outputs",
        alpaca_input_path,
        "--annotators_config",
        "weighted_alpaca_eval_gpt4_turbo",
        "--output_path",
        alpaca_out_dir,
        "--caching_path",
        os.path.join(alpaca_out_dir, "annotations_cache.json"),
    ]

    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        save_failed_result(
            results_json_path,
            error=result.stderr,
            stage="alpaca_eval_cli",
            extra={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "model_outputs_path": model_outputs_path,
                "alpaca_eval_input_path": alpaca_input_path,
                "alpaca_eval_output_dir": alpaca_out_dir,
            },
        )
        return

    leaderboard_path = os.path.join(
        alpaca_out_dir,
        "weighted_alpaca_eval_gpt4_turbo",
        "leaderboard.csv",
    )

    if not os.path.exists(leaderboard_path):
        fallback_path = os.path.join(alpaca_out_dir, "leaderboard.csv")
        if os.path.exists(fallback_path):
            leaderboard_path = fallback_path

    if not os.path.exists(leaderboard_path):
        save_failed_result(
            results_json_path,
            error="leaderboard.csv not found",
            stage="parse_alpaca_eval_leaderboard",
            extra={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "alpaca_eval_output_dir": alpaca_out_dir,
                "model_outputs_path": model_outputs_path,
            },
        )
        return

    try:
        import pandas as pd

        df = pd.read_csv(leaderboard_path)
        first_col = df.columns[0]

        generator_name = os.path.splitext(os.path.basename(model_outputs_path))[0]

        # 1. Exact match by generator_name
        matching_rows = df[df[first_col] == generator_name]

        # 2. Substring match by generator_name
        if matching_rows.empty:
            matching_rows = df[df[first_col].astype(str).str.contains(generator_name, regex=False)]

        # 3. Match by checking if leaderboard model name is contained in output filename or vice versa
        if matching_rows.empty:
            target_stem = generator_name.replace("_alpaca_outputs", "")
            matching_rows = df[df[first_col].astype(str).apply(lambda s: str(s) in generator_name or target_stem in str(s))]

        # 4. Fallback to last row or non-NullModel if match fails
        if matching_rows.empty:
            print(f"WARNING: Could not find exact match for '{generator_name}' in leaderboard.csv columns. Using best fallback.")
            non_null = df[df[first_col] != "NullModel"]
            if not non_null.empty:
                row = non_null.iloc[-1]
            else:
                row = df.iloc[0]
        else:
            row = matching_rows.iloc[0]

        print(f"Parsed AlpacaEval score for model '{row[first_col]}': win_rate={row.get('win_rate')}")

        output = {
            "status": "success",
            "mockup": False,
            "completed": True,
            "win_rate": float(row.get("win_rate", 0)),
            "std_err": float(row.get("standard_error", 0)),
            "n_wins": int(row.get("n_wins", 0)),
            "n_draws": int(row.get("n_draws", 0)),
            "n_loses": int(row.get("n_loses", 0)) if "n_loses" in row else int(row.get("n_total", 0)) - int(row.get("n_wins", 0)) - int(row.get("n_draws", 0)),
            "model_name_in_leaderboard": str(row[first_col]),
            "length_controlled_winrate": float(row.get("length_controlled_winrate", 0)) if "length_controlled_winrate" in row and pd.notna(row.get("length_controlled_winrate")) else None,
            "model_outputs_path": model_outputs_path,
            "alpaca_eval_input_path": alpaca_input_path,
            "alpaca_eval_output_dir": alpaca_out_dir,
            "leaderboard_path": leaderboard_path,
            "expected_n": len(load_existing_outputs(model_outputs_path)),
        }

    except Exception as e:
        save_failed_result(
            results_json_path,
            error=f"Failed to parse leaderboard: {e}",
            stage="parse_alpaca_eval_leaderboard",
            extra={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "alpaca_eval_output_dir": alpaca_out_dir,
                "model_outputs_path": model_outputs_path,
            },
        )
        return

    write_json_atomic(results_json_path, output)
    print(f"AlpacaEval 2 results saved to {results_json_path}")


def adjust_output_file_for_vllm(output_file, use_vllm):
    if not use_vllm or not output_file:
        return output_file
    if "results/vllm/" in output_file:
        return output_file
    if output_file.startswith("results/"):
        return output_file.replace("results/", "results/vllm/", 1)
    return output_file


def main():
    load_env_file()
    args = parse_args()
    args.output_file = adjust_output_file_for_vllm(args.output_file, getattr(args, "use_vllm", False))

    num_threads = int(os.environ.get("OMP_NUM_THREADS", os.environ.get("SLURM_CPUS_PER_TASK", 16)))
    if torch.cuda.is_available():
        torch.set_num_threads(num_threads)
    print(f"[eval_alpaca] Configured PyTorch CPU threads: {num_threads}")

    config = load_config(args.config)

    model_name_safe = safe_name(args.model_path)
    limit_tag = get_limit_tag(args.limit)

    res_prefix = os.path.join("results", "vllm") if getattr(args, "use_vllm", False) else "results"
    model_outputs_path = os.path.join(
        res_prefix,
        "alpaca_outputs",
        limit_tag,
        f"{model_name_safe}_alpaca_outputs.json",
    )

    try:
        alpaca_dataset = load_alpaca_eval_dataset()
    except Exception as e:
        save_failed_result(
            args.output_file,
            error=e,
            stage="load_alpaca_eval_dataset",
        )
        return

    required_n = expected_limit(args.limit, dataset_len=len(alpaca_dataset))

    if not args.skip_generation:
        try:
            generate_model_outputs(
                model_path=args.model_path,
                alpaca_dataset=alpaca_dataset,
                limit=args.limit,
                output_json_path=model_outputs_path,
                config=config,
                force=args.force,
                args=args,
            )
        except Exception as e:
            save_failed_result(
                args.output_file,
                error=e,
                stage="generate_model_outputs",
                extra={
                    "model_path": args.model_path,
                    "model_outputs_path": model_outputs_path,
                },
            )
            return
    else:
        print(f"Skipping generation, using existing: {model_outputs_path}")

    if not has_required_outputs(model_outputs_path, required_n):
        save_failed_result(
            args.output_file,
            error=(
                f"Model outputs are incomplete: {model_outputs_path}. "
                f"required={required_n}"
            ),
            stage="model_outputs_completeness_check",
            extra={"model_outputs_path": model_outputs_path},
        )
        return

    if not args.force:
        existing_score = load_json(args.output_file)
        if isinstance(existing_score, dict) and existing_score.get("status") == "success":
            print(f"[SKIP] AlpacaEval score already exists: {args.output_file}")
            return

    run_alpaca_eval(model_outputs_path, args.output_file)


if __name__ == "__main__":
    main()
