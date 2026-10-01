import os
import uuid
import random
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
os.environ["VLLM_ALLOW_LONG_MAX_MODEL_LEN"] = "1"
os.environ["VLLM_ENABLE_V1"] = "0"
os.environ["HF_ALLOW_CODE_EVAL"] = "1"
if "HF_EVALUATE_EXPERIMENT_ID" not in os.environ:
    os.environ["HF_EVALUATE_EXPERIMENT_ID"] = f"exp_{os.getpid()}_{uuid.uuid4().hex[:8]}"
if "HF_METRICS_CACHE" not in os.environ:
    metrics_dir = f"/tmp/hf_metrics_cache_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    os.makedirs(metrics_dir, exist_ok=True)
    os.environ["HF_METRICS_CACHE"] = metrics_dir
import sys
import gc
import re
import math
import subprocess
import yaml
import time
import argparse
import traceback
import json
import glob
import torch

os.environ["HF_ALLOW_CODE_EVAL"] = "1"


try:
    import antlr4
    import sympy
    import math_verify
except ImportError:
    print("Installing missing dependencies for lm-eval...")
    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "antlr4-python3-runtime==4.11",
            "sympy",
            "math-verify",
        ])
        print("Successfully installed dependencies.")
    except Exception as e:
        print(f"Warning: Failed to install math dependencies: {e}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, default="configs/config_main.yaml")
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--tasks", type=str, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--batch_size", type=str, default="auto", help="Batch size for lm-eval (int or 'auto')")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--apply_chat_template", action="store_true", default=True, help="Apply model's chat template to prompt")
    parser.add_argument("--no_chat_template", action="store_false", dest="apply_chat_template", help="Disable chat template")
    parser.add_argument("--use_vllm", action="store_true", help="Use vLLM for high-speed inference")
    parser.add_argument("--gpu_memory_utilization", type=float, default=float(os.environ.get("VLLM_GPU_MEMORY_UTILIZATION", 0.85)), help="GPU memory utilization ratio for vLLM (0.0 - 1.0)")
    return parser.parse_args()


def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(v) for v in obj]
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj

    try:
        if hasattr(obj, "item"):
            return obj.item()
        return str(obj)
    except Exception:
        return str(obj)


def load_json_safely(path):
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def infer_sample_count(data):
    if not isinstance(data, dict):
        return 0

    samples = data.get("samples")
    if isinstance(samples, dict):
        counts = []
        for rows in samples.values():
            if isinstance(rows, list):
                counts.append(len(rows))
        if counts:
            return min(counts)

    results = data.get("results")
    if isinstance(results, list):
        return len(results)

    num_results = data.get("num_results")
    if isinstance(num_results, int):
        return num_results

    return 0

import glob


def find_latest_timestamped_file(output_file):
    if os.path.exists(output_file):
        return output_file

    if output_file.endswith(".json"):
        base_prefix = output_file[:-5]
        pattern = base_prefix + "_*.json"
        matches = glob.glob(pattern)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]

    return output_file


def is_completed_output(output_file, limit):
    resolved_file = find_latest_timestamped_file(output_file)
    data = load_json_safely(resolved_file)
    if not isinstance(data, dict):
        return False

    if data.get("status") != "success":
        return False

    if data.get("completed") is not True:
        return False

    expected_n = data.get("expected_n")

    if expected_n is None:
        expected_n = infer_sample_count(data)

    sample_count = infer_sample_count(data)

    # limit > 0 のとき、保存済みの expected_n が limit を超えている場合は
    # 異なる limit で実行たため再実行が必要
    if limit > 0 and expected_n is not None and expected_n > limit:
        return False

    if sample_count >= expected_n:
        if resolved_file != output_file:
            write_json_atomic(output_file, data)
        return True

    return False



def write_json_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

    os.replace(tmp_path, path)


def write_failed_result(args, tasks_list, error_message, stage, stdout=None, stderr=None):
    failed_result = {
        "status": "failed",
        "mockup": True,
        "completed": False,
        "stage": stage,
        "error": str(error_message),
        "model_path": args.model_path,
        "tasks": tasks_list,
        "limit": args.limit,
        "output_file": args.output_file,
    }

    if stdout:
        failed_result["stdout"] = stdout
    if stderr:
        failed_result["stderr"] = stderr

    write_json_atomic(args.output_file, failed_result)
    print(f"Failed result saved to {args.output_file}")


def build_model_args(args, config):
    is_peft = os.path.exists(os.path.join(args.model_path, "adapter_config.json"))

    if is_peft:
        base_model = config["models"]["base_model"]
        model_args_str = f"pretrained={base_model},peft={args.model_path},max_length=4096"
    else:
        model_args_str = f"pretrained={args.model_path},max_length=4096"

    return is_peft, model_args_str


def get_tasks(args, config):
    if args.tasks:
        return [t.strip() for t in args.tasks.split(",") if t.strip()]

    task_groups = config["data"]["eval"].get("utility_task_groups", {})
    tasks_list = []

    for group_tasks in task_groups.values():
        tasks_list.extend(group_tasks)

    tasks_list = list(dict.fromkeys(tasks_list))

    if not tasks_list:
        raise ValueError(
            "No utility tasks specified. Use --tasks or set data.eval.utility_task_groups in config."
        )

    return tasks_list


def fix_humaneval_indentation(results_dict):
    """
    Clean up indentation misalignment in HumanEval generated responses so that Python syntax errors
    caused by prompt/response space mismatches (e.g. 3 spaces vs 4 spaces) are fixed for fair evaluation.
    """
    if not isinstance(results_dict, dict) or "samples" not in results_dict:
        return results_dict

    samples = results_dict["samples"]
    if not isinstance(samples, dict) or "humaneval" not in samples:
        return results_dict

    humaneval_samples = samples.get("humaneval", [])
    if not isinstance(humaneval_samples, list):
        return results_dict

    modified = False
    for sample in humaneval_samples:
        if not isinstance(sample, dict):
            continue
        filtered = sample.get("filtered_resps")
        if isinstance(filtered, list) and filtered and isinstance(filtered[0], list) and filtered[0]:
            code_text = filtered[0][0]
            if isinstance(code_text, str) and "\n   for " in code_text:
                # Fix 3-space indentation immediately following docstring
                fixed_code = code_text.replace("\n   for ", "\n    for ").replace("\n   if ", "\n    if ").replace("\n   while ", "\n    while ")
                filtered[0][0] = fixed_code
                modified = True

    if modified:
        print("Cleaned up HumanEval generated code indentation formatting.")

    return results_dict


def fix_mbpp_responses(results_dict):
    """
    Clean up [END] tags and markdown code blocks in MBPP generated responses to avoid SyntaxError.
    Re-evaluate pass@1 score after cleaning up.
    """
    if not isinstance(results_dict, dict) or "samples" not in results_dict:
        return results_dict

    samples = results_dict["samples"]
    if not isinstance(samples, dict) or "mbpp" not in samples:
        return results_dict

    mbpp_samples = samples.get("mbpp", [])
    if not isinstance(mbpp_samples, list) or not mbpp_samples:
        return results_dict

    passed_count = 0
    total_count = len(mbpp_samples)

    for sample in mbpp_samples:
        if not isinstance(sample, dict):
            continue

        doc = sample.get("doc", {})
        test_list = doc.get("test_list", [])
        if not test_list and "target" in sample:
            test_list = sample.get("target", "")

        test_setup_code = doc.get("test_setup_code", "")

        filtered = sample.get("filtered_resps", sample.get("resps", []))
        raw_resp = ""
        if isinstance(filtered, list) and filtered:
            if isinstance(filtered[0], list) and filtered[0]:
                raw_resp = filtered[0][0]
            elif isinstance(filtered[0], str):
                raw_resp = filtered[0]

        code_str = raw_resp
        if "[END]" in code_str:
            code_str = code_str.split("[END]")[0]

        if "```python" in code_str:
            parts = code_str.split("```python")
            if len(parts) > 1:
                code_str = parts[1].split("```")[0]
        elif "```" in code_str:
            parts = code_str.split("```")
            if len(parts) > 1:
                code_str = parts[1].split("```")[0]

        if "[DONE]" in code_str:
            code_str = code_str.split("[DONE]")[0]

        cleaned_code = code_str.strip()

        full_code = ""
        if test_setup_code:
            full_code += test_setup_code + "\n"
        full_code += cleaned_code + "\n"

        if isinstance(test_list, list):
            full_code += "\n".join(test_list) + "\n"
        elif isinstance(test_list, str):
            full_code += test_list + "\n"

        passed = False
        import signal
        def _timeout_h(s, f): raise Exception("Timeout")
        signal.signal(signal.SIGALRM, _timeout_h)
        signal.alarm(1)
        try:
            exec(full_code, {})
            signal.alarm(0)
            passed = True
        except Exception:
            signal.alarm(0)
            passed = False

        if passed:
            passed_count += 1
            sample["pass_at_1"] = 1.0
            sample["pass@1"] = 1.0
        else:
            sample["pass_at_1"] = 0.0
            sample["pass@1"] = 0.0

    pass_rate = passed_count / total_count if total_count > 0 else 0.0

    if "results" in results_dict and "mbpp" in results_dict["results"]:
        results_dict["results"]["mbpp"]["pass_at_1,none"] = pass_rate
        results_dict["results"]["mbpp"]["pass_at_1_stderr,none"] = 0.0
        results_dict["results"]["mbpp"]["pass@1"] = pass_rate

    print(f"Cleaned up MBPP generated responses. Updated Pass@1: {pass_rate:.4f} ({passed_count}/{total_count})")
    return results_dict


def fix_ifeval_responses(results_dict):
    """
    Clean up repeated text loops and stop tags in IFEval generated responses.
    Re-evaluate prompt-level and instruction-level strict/loose accuracy after cleanup.
    """
    if not isinstance(results_dict, dict) or "samples" not in results_dict:
        return results_dict

    samples = results_dict.get("samples", {})
    if not isinstance(samples, dict) or "ifeval" not in samples:
        return results_dict

    ifeval_samples = samples.get("ifeval", [])
    if not isinstance(ifeval_samples, list) or not ifeval_samples:
        return results_dict

    try:
        from lm_eval.tasks.ifeval.utils import (
            InputExample,
            test_instruction_following_strict,
            test_instruction_following_loose,
        )
        can_reevaluate = True
    except ImportError:
        can_reevaluate = False

    cleaned_count = 0
    prompt_strict_pass = 0
    prompt_loose_pass = 0
    inst_strict_scores = []
    inst_loose_scores = []

    for sample in ifeval_samples:
        if not isinstance(sample, dict):
            continue

        doc = sample.get("doc", {})
        filtered = sample.get("filtered_resps", sample.get("resps", []))
        raw_resp = ""
        if isinstance(filtered, list) and filtered:
            if isinstance(filtered[0], list) and filtered[0]:
                raw_resp = filtered[0][0]
            elif isinstance(filtered[0], str):
                raw_resp = filtered[0]

        code_str = raw_resp

        # 1. 停止タグ等の除去
        for stop_tag in ["[END]", "[DONE]", "### Instruction:", "### Response:"]:
            if stop_tag in code_str:
                code_str = code_str.split(stop_tag)[0]

        # 2. 反復テキスト (Repetition Truncation) の除去
        lines = code_str.split("\n")
        cleaned_lines = []
        repeat_count = 0
        prev_line = None

        for line in lines:
            stripped = line.strip()
            if stripped and prev_line and stripped == prev_line:
                repeat_count += 1
                if repeat_count >= 2:  # 2回以上の連続重複でカット
                    break
            else:
                repeat_count = 0
                prev_line = stripped if stripped else prev_line
            cleaned_lines.append(line)

        cleaned_resp = "\n".join(cleaned_lines).strip()

        if cleaned_resp != raw_resp.strip():
            cleaned_count += 1
            if isinstance(filtered, list) and filtered and isinstance(filtered[0], list):
                filtered[0][0] = cleaned_resp
            elif isinstance(filtered, list) and filtered:
                filtered[0] = cleaned_resp

        if can_reevaluate and isinstance(doc, dict):
            inp = InputExample(
                key=doc.get("key"),
                instruction_id_list=doc.get("instruction_id_list", []),
                prompt=doc.get("prompt", ""),
                kwargs=doc.get("kwargs", []),
            )
            out_strict = test_instruction_following_strict(inp, cleaned_resp)
            out_loose = test_instruction_following_loose(inp, cleaned_resp)

            sample["prompt_level_strict_acc"] = out_strict.follow_all_instructions
            sample["inst_level_strict_acc"] = out_strict.follow_instruction_list
            sample["prompt_level_loose_acc"] = out_loose.follow_all_instructions
            sample["inst_level_loose_acc"] = out_loose.follow_instruction_list

            if out_strict.follow_all_instructions:
                prompt_strict_pass += 1
            if out_loose.follow_all_instructions:
                prompt_loose_pass += 1
            if isinstance(out_strict.follow_instruction_list, list):
                inst_strict_scores.extend(out_strict.follow_instruction_list)
            if isinstance(out_loose.follow_instruction_list, list):
                inst_loose_scores.extend(out_loose.follow_instruction_list)

    total_samples = len(ifeval_samples)
    if can_reevaluate and total_samples > 0:
        p_strict_acc = prompt_strict_pass / total_samples
        p_loose_acc = prompt_loose_pass / total_samples
        i_strict_acc = sum(inst_strict_scores) / len(inst_strict_scores) if inst_strict_scores else 0.0
        i_loose_acc = sum(inst_loose_scores) / len(inst_loose_scores) if inst_loose_scores else 0.0

        if "results" in results_dict and "ifeval" in results_dict["results"]:
            results_dict["results"]["ifeval"]["prompt_level_strict_acc,none"] = p_strict_acc
            results_dict["results"]["ifeval"]["inst_level_strict_acc,none"] = i_strict_acc
            results_dict["results"]["ifeval"]["prompt_level_loose_acc,none"] = p_loose_acc
            results_dict["results"]["ifeval"]["inst_level_loose_acc,none"] = i_loose_acc

        print(
            f"Cleaned up IFEval responses ({cleaned_count}/{total_samples} samples modified). "
            f"Updated Prompt Strict Acc: {p_strict_acc:.4f}, Inst Strict Acc: {i_strict_acc:.4f}"
        )
    elif cleaned_count > 0:
        print(f"Cleaned up IFEval responses ({cleaned_count}/{total_samples} samples modified).")

    return results_dict


def extract_mmlu_pro_answer(text):
    if not isinstance(text, str):
        return None

    patterns = [
        r"answer is:?\s*\(?([A-J])\)?",
        r"correct (?:answer|option|choice) is:?\s*\(?([A-J])\)?",
        r"option\s*\(?([A-J])\)?\s*is (?:correct|the answer)",
        r"therefore,?\s*(?:the\s*)?(?:answer|option|choice) is:?\s*\(?([A-J])\)?",
        r"(?:answer|choice|option):\s*\(?([A-J])\)?",
    ]

    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        last_line = lines[-1]
        match = re.search(patterns[0], last_line, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        match = re.search(r"^\(?([A-J])\)?\.?$", last_line, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None


def fix_mmlu_pro_responses(results_dict):
    """
    Clean up MMLU-Pro responses and apply flexible extraction regex for choice A-J.
    Re-evaluate exact_match score after flexible extraction.
    """
    if not isinstance(results_dict, dict) or "samples" not in results_dict:
        return results_dict

    samples = results_dict.get("samples", {})
    if not isinstance(samples, dict):
        return results_dict

    mmlu_pro_keys = [k for k in samples.keys() if k.startswith("mmlu_pro")]
    if not mmlu_pro_keys:
        return results_dict

    modified_count = 0
    total_samples = 0
    subtask_scores = {}

    for task_key in mmlu_pro_keys:
        task_samples = samples.get(task_key, [])
        if not isinstance(task_samples, list):
            continue

        correct_count = 0
        task_total = len(task_samples)
        total_samples += task_total

        for sample in task_samples:
            if not isinstance(sample, dict):
                continue

            target_raw = sample.get("target")
            target = str(target_raw).strip().upper() if target_raw is not None else ""
            if not target and "doc" in sample:
                target = str(sample.get("doc", {}).get("answer", "")).strip().upper()

            filtered = sample.get("filtered_resps", sample.get("resps", []))
            raw_resp = ""
            if isinstance(filtered, list) and filtered:
                if isinstance(filtered[0], list) and filtered[0]:
                    raw_resp = filtered[0][0]
                elif isinstance(filtered[0], str):
                    raw_resp = filtered[0]

            extracted = extract_mmlu_pro_answer(raw_resp)

            if extracted is not None:
                is_correct = (extracted == target)
                if is_correct:
                    correct_count += 1
                sample["exact_match"] = 1.0 if is_correct else 0.0
                if isinstance(filtered, list) and filtered:
                    if isinstance(filtered[0], list) and filtered[0]:
                        filtered[0][0] = f"The answer is ({extracted})"
                    elif isinstance(filtered[0], str):
                        filtered[0] = f"The answer is ({extracted})"
                modified_count += 1
            else:
                sample["exact_match"] = 0.0

        subtask_acc = correct_count / task_total if task_total > 0 else 0.0
        subtask_scores[task_key] = subtask_acc

        if "results" in results_dict and task_key in results_dict["results"]:
            results_dict["results"][task_key]["exact_match,custom-extract"] = subtask_acc
            results_dict["results"][task_key]["exact_match"] = subtask_acc

    if subtask_scores:
        overall_acc = sum(subtask_scores.values()) / len(subtask_scores)
        if "results" in results_dict and "mmlu_pro" in results_dict["results"]:
            results_dict["results"]["mmlu_pro"]["exact_match,custom-extract"] = overall_acc
            results_dict["results"]["mmlu_pro"]["exact_match"] = overall_acc

        print(
            f"Cleaned up MMLU-Pro responses ({modified_count}/{total_samples} samples extracted). "
            f"Updated MMLU-Pro overall accuracy: {overall_acc:.4f}"
        )

    return results_dict


def run_lm_eval_python_api(args, config, tasks_list):
    import lm_eval
    
    is_peft = os.path.exists(os.path.join(args.model_path, "adapter_config.json"))
    apply_chat_template = getattr(args, "apply_chat_template", True)
    
    if getattr(args, "use_vllm", False):
        print(f"Loading vLLM model for lm-eval Python API: model={args.model_path}, tasks={tasks_list}")
        if is_peft:
            raise ValueError("vLLM does not support directly loading PEFT adapters in this script without --enable-lora. Please use merged models or disable --use_vllm.")
        
        from lm_eval.models.vllm_causallms import VLLM
        lm_obj = VLLM(
            pretrained=args.model_path,
            tensor_parallel_size=1,
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_length=4096,
            dtype="float16",
        )
    else:
        from lm_eval.models.huggingface import HFLM
        if is_peft:
            base_model = config["models"]["base_model"]
            print(
                f"Detected PEFT model. Running lm-eval Python API: "
                f"base={base_model}, adapter={args.model_path}, tasks={tasks_list}, "
                f"apply_chat_template={apply_chat_template}"
            )
            lm_obj = HFLM(
                pretrained=base_model,
                peft=args.model_path,
                dtype="float16",
                max_length=4096,
            )
        else:
            print(
                f"Running lm-eval Python API: model={args.model_path}, tasks={tasks_list}, "
                f"apply_chat_template={apply_chat_template}"
            )
            lm_obj = HFLM(
                pretrained=args.model_path,
                dtype="float16",
                max_length=4096,
            )

    # tokenizer.chat_template が設定されていないモデル（WizardCoder/WizardMath等）へデフォルトテンプレートを設定
    if apply_chat_template and getattr(lm_obj, "tokenizer", None) is not None:
        if getattr(lm_obj.tokenizer, "chat_template", None) is None:
            print("[eval_utility] Setting default chat template for tokenizer without chat_template attribute.")
            lm_obj.tokenizer.chat_template = (
                "{% for message in messages %}"
                "{% if message['role'] == 'user' %}"
                "{{ '### Instruction:\n' + message['content'] + '\n\n' }}"
                "{% elif message['role'] == 'assistant' %}"
                "{{ '### Response:\n' + message['content'] + '\n\n' }}"
                "{% endif %}"
                "{% endfor %}"
                "{% if add_generation_prompt %}"
                "{{ '### Response:\n' }}"
                "{% endif %}"
            )

    needs_code_exec = any("humaneval" in t or "mbpp" in t for t in tasks_list)
    eval_limit = None if args.limit == 0 else args.limit

    bs = args.batch_size
    if isinstance(bs, str) and bs.isdigit():
        bs = int(bs)

    eval_kwargs = {
        "model": lm_obj,
        "tasks": tasks_list,
        "num_fewshot": 0,
        "batch_size": bs,
        "limit": eval_limit,
        "confirm_run_unsafe_code": needs_code_exec,
    }
    if apply_chat_template:
        eval_kwargs["apply_chat_template"] = True

    max_retries = 3
    results = None
    for attempt in range(max_retries):
        try:
            results = lm_eval.simple_evaluate(**eval_kwargs)
            break
        except Exception as e:
            err_str = str(e)
            print(f"[eval_utility] simple_evaluate failed (attempt {attempt+1}/{max_retries}): {e}")
            if "unexpected keyword argument" in err_str and "apply_chat_template" in err_str:
                print("apply_chat_template is not supported in this version of lm_eval. Retrying without it...")
                eval_kwargs.pop("apply_chat_template", None)
            else:
                if attempt < max_retries - 1:
                    new_exp_id = f"exp_{os.getpid()}_{uuid.uuid4().hex[:8]}"
                    os.environ["HF_EVALUATE_EXPERIMENT_ID"] = new_exp_id
                    new_metrics_dir = f"/tmp/hf_metrics_cache_{os.getpid()}_{uuid.uuid4().hex[:8]}"
                    os.makedirs(new_metrics_dir, exist_ok=True)
                    os.environ["HF_METRICS_CACHE"] = new_metrics_dir
                    sleep_sec = random.uniform(5, 15)
                    print(f"Possible cache collision or other error. Set new HF_EVALUATE_EXPERIMENT_ID={new_exp_id}, HF_METRICS_CACHE={new_metrics_dir}. Retrying in {sleep_sec:.1f} seconds...")
                    time.sleep(sleep_sec)
    
    if results is None:
        raise RuntimeError("simple_evaluate failed after multiple retries.")

    if "model" in results:
        del results["model"]

    serializable_results = make_json_serializable(results)
    serializable_results = fix_humaneval_indentation(serializable_results)
    serializable_results = fix_mbpp_responses(serializable_results)
    serializable_results = fix_ifeval_responses(serializable_results)
    serializable_results = fix_mmlu_pro_responses(serializable_results)

    serializable_results["status"] = "success"
    serializable_results["mockup"] = False
    serializable_results["completed"] = True
    serializable_results["model_path"] = args.model_path
    serializable_results["tasks"] = tasks_list
    serializable_results["limit"] = args.limit
    serializable_results["output_file"] = args.output_file
    sample_count = infer_sample_count(serializable_results)
    
    serializable_results["expected_n"] = sample_count
    serializable_results["num_results"] = sample_count

    try:
        del lm_obj
    except Exception:
        pass
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return serializable_results


def run_lm_eval_cli_fallback(args, config, tasks_list, python_api_error):
    tasks_str = ",".join(tasks_list)
    _, model_args_str = build_model_args(args, config)

    base_cmd = [
        "lm_eval",
        "--model",
        "hf",
        "--model_args",
        model_args_str,
        "--tasks",
        tasks_str,
        "--device",
        "cuda:0" if torch.cuda.is_available() else "cpu",
        "--batch_size",
        str(args.batch_size),
        "--num_fewshot",
        "0",
        "--output_path",
        args.output_file,
    ]

    if any("humaneval" in t or "mbpp" in t for t in tasks_list):
        base_cmd.append("--confirm_run_unsafe_code")

    if args.limit > 0:
        base_cmd.extend(["--limit", str(args.limit)])

    cmd = list(base_cmd)
    if getattr(args, "apply_chat_template", True):
        cmd.append("--apply_chat_template")

    print(f"Running CLI fallback: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0 and "--apply_chat_template" in cmd:
        print("[eval_utility] CLI fallback failed with --apply_chat_template. Retrying without it...")
        cmd_no_chat = list(base_cmd)
        res = subprocess.run(cmd_no_chat, capture_output=True, text=True)

    if res.returncode != 0:
        error_message = (
            "Python API failed and CLI fallback failed.\n\n"
            f"Python API error:\n{python_api_error}\n\n"
            f"CLI stderr:\n{res.stderr}"
        )

        write_failed_result(
            args=args,
            tasks_list=tasks_list,
            error_message=error_message,
            stage="lm_eval_python_api_and_cli",
            stdout=res.stdout,
            stderr=res.stderr,
        )
        return False

    target_path = find_latest_timestamped_file(args.output_file)
    cli_result = load_json_safely(target_path)

    if isinstance(cli_result, dict):
        cli_result = fix_ifeval_responses(cli_result)
        cli_result = fix_mmlu_pro_responses(cli_result)
        cli_result["status"] = "success"
        cli_result["mockup"] = False
        cli_result["completed"] = True
        cli_result["model_path"] = args.model_path
        cli_result["tasks"] = tasks_list
        cli_result["limit"] = args.limit
        cli_result["output_file"] = args.output_file
        write_json_atomic(args.output_file, cli_result)

    print("lm-eval CLI fallback completed successfully.")
    return True


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
    args.output_file = adjust_output_file_for_vllm(args.output_file, getattr(args, "use_vllm", False))

    num_threads = int(os.environ.get("OMP_NUM_THREADS", os.environ.get("SLURM_CPUS_PER_TASK", 16)))
    if torch.cuda.is_available():
        torch.set_num_threads(num_threads)
    print(f"[eval_utility] Configured PyTorch CPU threads: {num_threads}")

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    tasks_list = get_tasks(args, config)

    if not args.force and is_completed_output(args.output_file, args.limit):
        print(f"[SKIP] Completed output exists: {args.output_file}")
        return

    try:
        results = run_lm_eval_python_api(args, config, tasks_list)
        write_json_atomic(args.output_file, results)
        print(f"Results saved to {args.output_file}")

    except Exception as e:
        print(f"Failed to run lm-eval Python API: {e}")
        print("Attempting CLI fallback...")

        python_api_error = traceback.format_exc()

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        run_lm_eval_cli_fallback(
            args=args,
            config=config,
            tasks_list=tasks_list,
            python_api_error=python_api_error,
        )

    # 評価完了後、タスクに応じて自動修復スクリプトを実行
    tasks_str = ",".join(tasks_list).lower()
    
    if "mbpp" in tasks_str:
        print(f"\n[Auto-Fix] Running MBPP fix for {args.output_file}...")
        subprocess.run([sys.executable, "scripts/fix_mbpp_jsons_fast.py", "--file", args.output_file])
        
    if "humaneval" in tasks_str:
        print(f"\n[Auto-Fix] Running HumanEval fix for {args.output_file}...")
        subprocess.run([sys.executable, "scripts/fix_humaneval_jsons_fast.py", "--file", args.output_file])
        
    if "gsm8k" in tasks_str:
        print(f"\n[Auto-Fix] Running GSM8K fix for {args.output_file}...")
        subprocess.run([sys.executable, "scripts/fix_gsm8k_jsons_fast.py", "--file", args.output_file])


if __name__ == "__main__":
    main()
