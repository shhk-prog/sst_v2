"""
Evaluation: eval_utility_v4.py
Rigorous utility evaluation according to Secure_Merge_Experiment_Plan.md Section 5.1.
Covers math (GSM8K, MATH500) and code (HumanEval, MBPP) benchmarks.
Distinguishes generation failure, answer extraction failure, and incorrect answers.
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def extract_math_answer(pred_text: str) -> Optional[str]:
    """Extract final numeric answer from chain-of-thought response."""
    # Look for 'The answer is X' or '#### X'
    patterns = [
        r"####\s*(-?[\d,]+(?:\.\d+)?)",
        r"[Tt]he answer is\s*:?\s*\$?\s*(-?[\d,]+(?:\.\d+)?)",
        r"\\boxed\{(-?[\d,]+(?:\.\d+)?)\}",
        r"= ?(-?[\d,]+(?:\.\d+)?)\s*$",
    ]
    for p in patterns:
        m = re.findall(p, pred_text)
        if m:
            return m[-1].replace(",", "").strip()

    # Fallback: search for last number
    nums = re.findall(r"-?\d+(?:\.\d+)?", pred_text)
    if nums:
        return nums[-1]
    return None


def run_math_evaluation(
    model_path: str,
    dataset: List[Dict[str, Any]],
    output_file: Optional[str] = None,
    max_new_tokens: int = 512,
) -> Dict[str, Any]:
    print(f"Running Math Utility evaluation on {model_path} with {len(dataset)} problems...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    model.eval()

    correct_count = 0
    extraction_fail_count = 0
    results = []

    for idx, item in enumerate(dataset):
        prompt = item["question"] + "\nPlease reason step by step, and put your final answer within \\boxed{}."
        gold = str(item.get("answer", "")).replace(",", "").strip()

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        resp = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        pred = extract_math_answer(resp)

        if pred is None:
            extraction_fail_count += 1
            is_correct = False
        else:
            is_correct = (pred == gold)

        if is_correct:
            correct_count += 1

        results.append({
            "id": idx,
            "question": item["question"],
            "response": resp,
            "predicted_answer": pred,
            "gold_answer": gold,
            "is_correct": is_correct,
            "extraction_failed": (pred is None),
        })

    accuracy = float(correct_count / len(dataset)) if dataset else 0.0

    report = {
        "model_path": model_path,
        "n_samples": len(dataset),
        "correct_count": correct_count,
        "extraction_fail_count": extraction_fail_count,
        "accuracy": accuracy,
        "results": results,
    }

    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Math utility report saved to {output_file}")

    return report


def extract_code_block(generation: str, entry_point: Optional[str] = None) -> str:
    """Extract python code block from generated text."""
    m = re.findall(r"```python(.*?)```", generation, re.DOTALL)
    if m:
        return m[0].strip()
    m_generic = re.findall(r"```(.*?)```", generation, re.DOTALL)
    if m_generic:
        return m_generic[0].strip()
    return generation.strip()


def _target_code_runner(program_code: str, result_queue: Any):
    """Worker process target that executes code in an isolated scope with stdout muted."""
    import sys
    import io
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        global_scope = {}
        exec(program_code, global_scope)
        result_queue.put({"status": "PASSED", "error": None})
    except AssertionError as e:
        result_queue.put({"status": "ASSERTION_ERROR", "error": str(e)})
    except Exception as e:
        result_queue.put({"status": "RUNTIME_ERROR", "error": f"{type(e).__name__}: {str(e)}"})


def execute_code_isolated(program_code: str, timeout: float = 3.0) -> Dict[str, Any]:
    """
    R3-01: Executes generated program in a separate multiprocessing process with strict timeout.
    Prevents host contamination and infinite execution loops.
    """
    import multiprocessing
    result_queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_target_code_runner, args=(program_code, result_queue))
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join(0.5)
        if proc.is_alive():
            proc.kill()
        return {"status": "TIMEOUT", "error": f"Execution exceeded {timeout}s"}

    if not result_queue.empty():
        return result_queue.get()
    return {"status": "CRASH", "error": "Worker process exited unexpectedly"}


def build_humaneval_test_program(prompt: str, code: str, test: str, entry_point: str) -> str:
    """
    R3-01: Builds complete test code for HumanEval.
    Crucially ensures check(entry_point) is actually executed, not just defined!
    """
    # If code does not include function definition or is just completion, merge with prompt
    candidate_code = code
    if entry_point and f"def {entry_point}" not in code:
        candidate_code = prompt + "\n" + code

    # Check if test defines `check(candidate)`
    call_line = ""
    if "def check(" in test:
        call_line = f"\ncheck({entry_point})\n"

    full_program = (
        candidate_code + "\n\n" +
        test + "\n" +
        call_line
    )
    return full_program


def build_mbpp_test_program(code: str, test_list: List[str]) -> str:
    """R3-01: Builds complete test code for MBPP from test_list assertions."""
    tests_str = "\n".join(test_list)
    return code + "\n\n" + tests_str + "\n"


def run_code_evaluation(
    model_path: str,
    dataset: List[Dict[str, Any]],
    output_file: Optional[str] = None,
    execute_code: bool = False,
    timeout: float = 3.0,
    max_new_tokens: int = 512,
) -> Dict[str, Any]:
    """
    Evaluates Code generation on HumanEval/MBPP with isolated execution (R3-01).
    Requires explicit execute_code=True for runtime test execution.
    """
    print(f"Running Code Utility evaluation on {model_path} with {len(dataset)} problems (execute={execute_code})...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    model.eval()

    passed_count = 0
    syntax_error_count = 0
    results = []

    for idx, item in enumerate(dataset):
        prompt = item["prompt"]
        entry_point = item.get("entry_point")
        test_cases = item.get("test", "")
        test_list = item.get("test_list", [])

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        resp = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        code = extract_code_block(resp, entry_point)

        # Syntax check
        syntax_valid = True
        try:
            compile(code, "<string>", "exec")
        except SyntaxError:
            syntax_valid = False
            syntax_error_count += 1

        exec_res = None
        if execute_code and syntax_valid:
            if test_cases:
                full_prog = build_humaneval_test_program(prompt, code, test_cases, entry_point or "")
            elif test_list:
                full_prog = build_mbpp_test_program(code, test_list)
            else:
                full_prog = code

            exec_res = execute_code_isolated(full_prog, timeout=timeout)
            if exec_res.get("status") == "PASSED":
                passed_count += 1

        results.append({
            "task_id": item.get("task_id", idx),
            "prompt": prompt,
            "entry_point": entry_point,
            "generated_code": code,
            "syntax_valid": syntax_valid,
            "exec_status": exec_res.get("status") if exec_res else None,
            "exec_error": exec_res.get("error") if exec_res else None,
        })

    pass_at_1 = float(passed_count / len(dataset)) if (execute_code and dataset) else None

    report = {
        "model_path": model_path,
        "n_samples": len(dataset),
        "execute_code": execute_code,
        "syntax_valid_rate": float((len(dataset) - syntax_error_count) / len(dataset)) if dataset else 0.0,
        "pass_at_1": pass_at_1,
        "results": results,
    }

    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Code utility report saved to {output_file}")

    return report


if __name__ == "__main__":
    # Test answer extraction
    cot = "First, 2 + 3 = 5. Then 5 * 4 = 20. The answer is \\boxed{20}."
    ans = extract_math_answer(cot)
    print(f"Extracted answer: {ans} (Expected: 20)")
    assert ans == "20"
