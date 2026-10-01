"""
Evol-Instruct-Code and MedAlpaca evaluation script.

- Saves each sample incrementally
- Can resume after interruption
- Skips completed output when limit samples already exist
- Processes multiple datasets with a single vLLM loading
"""

import os
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
os.environ["VLLM_ENABLE_V1"] = "0"
import gc
import json
import math
import yaml
import argparse
import traceback

import torch
import numpy as np
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from difflib import SequenceMatcher


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    
    parser.add_argument(
        "--datasets",
        type=str,
        default="evol_code",
        help="Comma-separated list of datasets: evol_code,medalpaca"
    )
    
    parser.add_argument("--output_file", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--model_name", type=str, default=None)
    
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--batch_size", type=str, default="8", help="Batch size for text generation (int or 'auto')")
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


def load_existing_results(output_file):
    data = load_json(output_file)
    if not isinstance(data, dict):
        return [], {}

    details = data.get("eval_details", data.get("results", []))
    if not isinstance(details, list):
        details = []

    return details, data


def expected_limit(limit):
    return limit if limit > 0 else 1000


def is_complete(output_file, limit):
    data = load_json(output_file)
    if not isinstance(data, dict):
        return False

    if data.get("status") != "success":
        return False

    if data.get("completed") is not True:
        return False

    expected_n = data.get("expected_n", data.get("num_samples", 0))
    details = data.get("eval_details", [])

    if len(details) < expected_n:
        return False

    for r in details[:expected_n]:
        if r.get("response") is None:
            return False
        if r.get("similarity") is None:
            return False
        if r.get("loss") is None:
            return False

    return True


def save_checkpoint(args, dataset, output_file, results, completed=False):
    valid_losses = [
        float(r["loss"])
        for r in results
        if r.get("loss") is not None
        and not math.isnan(float(r["loss"]))
        and not math.isinf(float(r["loss"]))
    ]

    valid_sims = [
        float(r["similarity"])
        for r in results
        if r.get("similarity") is not None
    ]

    if valid_losses:
        avg_loss = float(np.mean(valid_losses))
        try:
            ppl = float(math.exp(avg_loss))
        except OverflowError:
            ppl = float("inf")
    else:
        ppl = float("nan")

    sim_score = float(np.mean(valid_sims)) if valid_sims else 0.0
    expected_n = len(results)

    payload = {
        "status": "success" if completed else "running",
        "mockup": False,
        "completed": completed,
        "dataset": dataset,
        "model_path": args.model_path,
        "limit": args.limit,
        "num_samples": len(results),
        "processed_perplexity_n": len(valid_losses),
        "processed_generation_n": len(valid_sims),
        "metrics": {
            "perplexity": ppl,
            "similarity_score": sim_score,
        },
        "perplexity": ppl,
        "similarity_score": sim_score,
        "eval_details": results,
        "expected_n": expected_n,
    }

    write_json_atomic(output_file, payload)


def save_failed_result(args, dataset, output_file, error, stage="unknown"):
    result = {
        "status": "failed",
        "mockup": True,
        "completed": False,
        "stage": stage,
        "error": str(error),
        "traceback": traceback.format_exc(),
        "dataset": dataset,
        "model_path": args.model_path,
        "output_file": output_file,
    }

    write_json_atomic(output_file, result)
    print(f"Failed result saved to {output_file}")


def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_model_device(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model_and_tokenizer(model_path, config):
    is_peft = os.path.exists(os.path.join(model_path, "adapter_config.json"))

    if is_peft:
        from peft import PeftModel

        base_model = config.get("models", {}).get("base_model")
        if not base_model:
            raise ValueError("config['models']['base_model'] is missing.")

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


def get_dataset_samples(dataset_name, limit):
    actual_limit = expected_limit(limit)

    if dataset_name == "evol_code":
        ds = load_dataset("nickrosh/Evol-Instruct-Code-80k-v1", split="train")
        start_idx = min(1000, max(len(ds) - 1, 0))
        end_idx = min(start_idx + actual_limit, len(ds))

        samples = []
        for i in range(start_idx, end_idx):
            samples.append({
                "sample_id": i,
                "instruction": ds[i]["instruction"],
                "input": ds[i].get("input", ""),
                "target": ds[i]["output"],
            })
        return samples

    if dataset_name == "medalpaca":
        ds = load_dataset("medalpaca/medical_meadow_medical_flashcards", split="train")
        start_idx = min(1000, max(len(ds) - 1, 0))
        end_idx = min(start_idx + actual_limit, len(ds))

        samples = []
        for i in range(start_idx, end_idx):
            instruction = ds[i]["instruction"]
            if ds[i].get("input", ""):
                instruction += "\n" + ds[i]["input"]

            samples.append({
                "sample_id": i,
                "instruction": instruction,
                "input": "",
                "target": ds[i]["output"],
            })
        return samples

    raise ValueError(f"Unknown dataset name: {dataset_name}")


def build_prompt(sample):
    prompt = sample["instruction"]
    if sample.get("input", ""):
        prompt = f"{prompt}\n\n{sample['input']}"
    return prompt


def init_or_resume_results(args, dataset, output_file, samples):
    old_results, _ = load_existing_results(output_file)

    by_id = {}
    for r in old_results:
        if isinstance(r, dict) and r.get("sample_id") is not None:
            by_id[r["sample_id"]] = r

    results = []
    for sample in samples:
        prompt = build_prompt(sample)
        old = by_id.get(sample["sample_id"], {})

        results.append({
            "sample_id": sample["sample_id"],
            "prompt": prompt,
            "target": sample["target"],
            "response": old.get("response"),
            "similarity": old.get("similarity"),
            "loss": old.get("loss"),
        })

    save_checkpoint(args, dataset, output_file, results, completed=False)
    return results


def format_chat_prompt(tokenizer, prompt):
    try:
        messages = [{"role": "user", "content": prompt}]
        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        pass
    return f"<s>[INST] {prompt} [/INST]"


def compute_loss_one(model, tokenizer, prompt, target):
    model_device = get_model_device(model)

    prefix_text = format_chat_prompt(tokenizer, prompt)
    full_text = f"{prefix_text}{target}"

    tokenized_full = tokenizer(
        full_text,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    )
    tokenized_prefix = tokenizer(
        prefix_text,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    )

    input_ids = tokenized_full["input_ids"].to(model_device)
    labels = input_ids.clone()

    target_start_idx = tokenized_prefix["input_ids"].shape[1]
    if target_start_idx >= input_ids.shape[1]:
        return None

    labels[:, :target_start_idx] = -100

    with torch.no_grad():
        outputs = model(input_ids=input_ids, labels=labels)
        loss = float(outputs.loss.item())

    if math.isnan(loss) or math.isinf(loss):
        return None

    return loss


def generate_batch(model, tokenizer, prompts):
    if not prompts:
        return []

    model_device = get_model_device(model)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    old_padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"

    formatted_prompts = [format_chat_prompt(tokenizer, p) for p in prompts]

    inputs = tokenizer(
        formatted_prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=1024,
    )
    inputs = {k: v.to(model_device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    tokenizer.padding_side = old_padding_side

    results = []
    input_length = inputs["input_ids"].shape[1]
    for i in range(len(prompts)):
        gen_tokens = outputs[i][input_length:]
        text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        results.append(text)

    return results


def adjust_output_file_for_vllm(output_file, use_vllm):
    if not use_vllm or not output_file:
        return output_file
    if "results/vllm/" in output_file:
        return output_file
    if output_file.startswith("results/"):
        return output_file.replace("results/", "results/vllm/", 1)
    return output_file


def main():
    args = parse_args()
    use_vllm = getattr(args, "use_vllm", False)

    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
    if not datasets:
        print("No datasets specified.")
        return

    num_threads = int(os.environ.get("OMP_NUM_THREADS", os.environ.get("SLURM_CPUS_PER_TASK", 16)))
    if torch.cuda.is_available():
        torch.set_num_threads(num_threads)
    print(f"[eval_instruction_datasets] Configured PyTorch CPU threads: {num_threads}")

    config = load_config(args.config)

    task_configs = []
    for dataset in datasets:
        if args.output_dir and args.model_name:
            out_file = os.path.join(args.output_dir, f"{args.model_name}_inst_{dataset}.json")
        else:
            out_file = args.output_file if len(datasets) == 1 else args.output_file.replace(".json", f"_{dataset}.json")

        out_file = adjust_output_file_for_vllm(out_file, use_vllm)
        
        if not args.force and is_complete(out_file, args.limit):
            print(f"[SKIP] Completed output exists for {dataset}: {out_file}")
            continue

        print(f"Evaluating {args.model_path} on {dataset} limit={args.limit}")
        samples = get_dataset_samples(dataset, args.limit)

        if not samples:
            print(f"Warning: No evaluation samples found for {dataset}.")
            continue

        print(f"Loaded {len(samples)} test samples for {dataset}.")

        results = init_or_resume_results(args, dataset, out_file, samples)
        task_configs.append({
            "dataset": dataset,
            "out_file": out_file,
            "samples": samples,
            "results": results
        })

    if not task_configs:
        print("All specified datasets are already complete.")
        return

    # 1. Compute loss for samples missing loss
    needs_loss = any(not r.get("loss") for tc in task_configs for r in tc["results"])
    model = None
    tokenizer = None

    if needs_loss:
        if use_vllm:
            print("Loading HF model for loss computation...")
            model, tokenizer = load_model_and_tokenizer(args.model_path, config)
        else:
            print("Loading HF model...")
            model, tokenizer = load_model_and_tokenizer(args.model_path, config)

        for tc in task_configs:
            missing_loss = [i for i, r in enumerate(tc["results"]) if r.get("loss") is None]
            if missing_loss:
                print(f"Computing loss for {len(missing_loss)} samples in {tc['dataset']}...")
                for i in tqdm(missing_loss, desc=f"Computing loss ({tc['dataset']})"):
                    r = tc["results"][i]
                    r["loss"] = compute_loss_one(
                        model=model,
                        tokenizer=tokenizer,
                        prompt=r["prompt"],
                        target=r["target"],
                    )
                save_checkpoint(args, tc["dataset"], tc["out_file"], tc["results"], completed=False)

        if use_vllm:
            print("Unloading HF model and clearing GPU cache before vLLM generation...")
            del model
            clear_cuda()
            model = None

    # 2. Generate responses for samples missing response
    needs_gen = any(not r.get("response") for tc in task_configs for r in tc["results"])
    
    bs_val = getattr(args, "batch_size", "8")
    batch_size = int(bs_val) if isinstance(bs_val, str) and bs_val.isdigit() else (bs_val if isinstance(bs_val, int) else 8)

    if needs_gen:
        if use_vllm:
            print("Loading vLLM engine for generation...")
            is_peft = os.path.exists(os.path.join(args.model_path, "adapter_config.json"))
            if is_peft:
                raise ValueError("vLLM does not support directly loading PEFT adapters in this script without --enable-lora.")
            
            from vllm import LLM, SamplingParams
            llm = LLM(model=args.model_path, trust_remote_code=True, tensor_parallel_size=1)
            sampling_params = SamplingParams(temperature=0.0, max_tokens=256)
            
            if tokenizer is None:
                tokenizer = AutoTokenizer.from_pretrained(args.model_path, use_fast=False)
            
            for tc in task_configs:
                missing_resp = [i for i, r in enumerate(tc["results"]) if r.get("response") is None]
                if not missing_resp: continue
                
                print(f"Generating responses for {len(missing_resp)} samples in {tc['dataset']} with vLLM...")
                b_prompts = [tc["results"][idx]["prompt"] for idx in missing_resp]
                formatted_prompts = [format_chat_prompt(tokenizer, p) for p in b_prompts]
                
                vllm_outputs = llm.generate(formatted_prompts, sampling_params)
                for i, idx in enumerate(missing_resp):
                    tc["results"][idx]["response"] = vllm_outputs[i].outputs[0].text.strip()
                    
                save_checkpoint(args, tc["dataset"], tc["out_file"], tc["results"], completed=False)
                
            print("Unloading vLLM and clearing GPU cache...")
            del llm
            clear_cuda()
        else:
            if model is None:
                model, tokenizer = load_model_and_tokenizer(args.model_path, config)
            
            for tc in task_configs:
                missing_resp = [i for i, r in enumerate(tc["results"]) if r.get("response") is None]
                if not missing_resp: continue

                print(f"Generating responses for {len(missing_resp)} samples in {tc['dataset']} in batches of {batch_size}...")
                for b_start in tqdm(range(0, len(missing_resp), batch_size), desc=f"Generating responses ({tc['dataset']})"):
                    b_indices = missing_resp[b_start : b_start + batch_size]
                    b_prompts = [tc["results"][idx]["prompt"] for idx in b_indices]
                    b_gen_responses = generate_batch(model, tokenizer, b_prompts)

                    for idx, resp in zip(b_indices, b_gen_responses):
                        tc["results"][idx]["response"] = resp
                    save_checkpoint(args, tc["dataset"], tc["out_file"], tc["results"], completed=False)
            
            del model
            clear_cuda()

    # 3. Compute similarity and finalize
    for tc in task_configs:
        try:
            missing_sim = [i for i, r in enumerate(tc["results"]) if r.get("similarity") is None]
            if missing_sim:
                for i in missing_sim:
                    r = tc["results"][i]
                    r["similarity"] = float(SequenceMatcher(None, r["response"], r["target"]).ratio())
                save_checkpoint(args, tc["dataset"], tc["out_file"], tc["results"], completed=False)

            save_checkpoint(args, tc["dataset"], tc["out_file"], tc["results"], completed=True)

            final = load_json(tc["out_file"])
            print(
                f"Evaluation completed for {tc['dataset']}. "
                f"Perplexity: {final['perplexity']:.4f}, "
                f"Similarity: {final['similarity_score']:.4f}, "
                f"n={final['num_samples']}"
            )
            print(f"Results saved to {tc['out_file']}")

        except Exception as e:
            print(f"Instruction dataset evaluation failed for {tc['dataset']}: {e}")
            save_failed_result(args, tc["dataset"], tc["out_file"], e, stage="eval_instruction_datasets")


if __name__ == "__main__":
    main()
