"""
Re-evaluate and fix existing MBPP JSON files by cleaning up [END] tags,
enforcing timeouts against infinite loops, and processing in parallel.
"""

import os
import glob
import json
import signal
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("Timed out!")


def clean_mbpp_response(code_str):
    if not isinstance(code_str, str):
        return code_str

    # Clean [END] tag
    if "[END]" in code_str:
        code_str = code_str.split("[END]")[0]

    # Clean markdown codeblocks if present
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

    return code_str.strip()


def check_mbpp_solution(cleaned_code, test_list, test_setup_code="", timeout=1):
    full_code = ""
    if test_setup_code:
        full_code += test_setup_code + "\n"
    full_code += cleaned_code + "\n"

    if isinstance(test_list, list):
        full_code += "\n".join(test_list) + "\n"
    elif isinstance(test_list, str):
        full_code += test_list + "\n"

    # Set up signal timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    global_env = {}
    try:
        exec(full_code, global_env)
        signal.alarm(0)
        return True
    except Exception:
        signal.alarm(0)
        return False


def fix_mbpp_json_file(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return f"Error loading {json_path}: {e}"

    if not isinstance(data, dict) or "samples" not in data:
        return None

    samples = data.get("samples", {}).get("mbpp", [])
    if not isinstance(samples, list) or not samples:
        return None

    passed_count = 0
    total_count = len(samples)

    for sample in samples:
        doc = sample.get("doc", {})
        test_list = doc.get("test_list", [])
        if not test_list and "target" in sample:
            test_list = sample.get("target", "")

        test_setup_code = doc.get("test_setup_code", "")

        resps = sample.get("filtered_resps", sample.get("resps", []))
        raw_resp = ""
        if isinstance(resps, list) and resps:
            if isinstance(resps[0], list) and resps[0]:
                raw_resp = resps[0][0]
            elif isinstance(resps[0], str):
                raw_resp = resps[0]

        cleaned_code = clean_mbpp_response(raw_resp)
        passed = check_mbpp_solution(cleaned_code, test_list, test_setup_code, timeout=1)

        if passed:
            passed_count += 1
            sample["pass_at_1"] = 1.0
            sample["pass@1"] = 1.0
        else:
            sample["pass_at_1"] = 0.0
            sample["pass@1"] = 0.0

    pass_rate = passed_count / total_count if total_count > 0 else 0.0

    # Update results in JSON
    if "results" in data and "mbpp" in data["results"]:
        old_pass = data["results"]["mbpp"].get("pass_at_1,none", data["results"]["mbpp"].get("pass@1", 0.0))
        data["results"]["mbpp"]["pass_at_1,none"] = pass_rate
        data["results"]["mbpp"]["pass_at_1_stderr,none"] = 0.0
        data["results"]["mbpp"]["pass@1"] = pass_rate

        tmp = json_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, json_path)

        return f"Updated {os.path.basename(json_path)}: {old_pass:.4f} -> {pass_rate:.4f} ({passed_count}/{total_count})"

    return None


def main():
    results_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results"
    pattern = os.path.join(results_dir, "**", "*_utility_code_mbpp*.json")
    files = glob.glob(pattern, recursive=True)

    print(f"Found {len(files)} utility_code_mbpp JSON files to fix in parallel.")

    num_workers = min(32, os.cpu_count() or 4)
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(fix_mbpp_json_file, f): f for f in files}
        count = 0
        for future in as_completed(futures):
            res = future.result()
            count += 1
            if res:
                print(f"[{count}/{len(files)}] {res}")
            else:
                if count % 20 == 0:
                    print(f"[{count}/{len(files)}] Processed...")


if __name__ == "__main__":
    main()
