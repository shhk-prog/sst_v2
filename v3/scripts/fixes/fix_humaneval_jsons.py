"""
Re-evaluate and fix existing HumanEval JSON files by correcting indentation and running tests.
"""

import os
import glob
import json
import traceback

def check_solution(prompt, response, test, entry_point):
    """
    Executes HumanEval test for a prompt and generated response.
    Returns True if pass@1, False if fail.
    """
    # Clean up 3-space indentation right after prompt
    clean_resp = response
    if clean_resp.startswith("   for ") or "\n   for " in clean_resp:
        clean_resp = clean_resp.replace("\n   for ", "\n    for ").replace("   for ", "    for ")
    if clean_resp.startswith("   if ") or "\n   if " in clean_resp:
        clean_resp = clean_resp.replace("\n   if ", "\n    if ").replace("   if ", "    if ")
    if clean_resp.startswith("   while ") or "\n   while " in clean_resp:
        clean_resp = clean_resp.replace("\n   while ", "\n    while ").replace("   while ", "    while ")
    if clean_resp.startswith("   def ") or "\n   def " in clean_resp:
        clean_resp = clean_resp.replace("\n   def ", "\n    def ").replace("   def ", "    def ")
    if clean_resp.startswith("   return ") or "\n   return " in clean_resp:
        clean_resp = clean_resp.replace("\n   return ", "\n    return ").replace("   return ", "    return ")

    full_code = prompt + clean_resp + "\n" + test + f"\ncheck({entry_point})\n"

    global_scope = {}
    try:
        exec(full_code, global_scope)
        return True, clean_resp
    except Exception:
        return False, clean_resp


def fix_humaneval_json_file(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return

    if not isinstance(data, dict) or "samples" not in data:
        return

    samples = data.get("samples", {}).get("humaneval", [])
    if not isinstance(samples, list) or not samples:
        return

    passed_count = 0
    total_count = len(samples)

    for sample in samples:
        doc = sample.get("doc", {})
        prompt = doc.get("prompt", "")
        test = doc.get("test", "")
        entry_point = doc.get("entry_point", "")

        resps = sample.get("resps", [[]])
        if resps and resps[0]:
            raw_resp = resps[0][0]
            passed, fixed_resp = check_solution(prompt, raw_resp, test, entry_point)
            if passed:
                passed_count += 1
                sample["pass@1"] = 1.0
            else:
                sample["pass@1"] = 0.0

    pass_rate = passed_count / total_count if total_count > 0 else 0.0
    
    # Update results
    if "results" in data and "humaneval" in data["results"]:
        old_pass = data["results"]["humaneval"].get("pass@1,create_test")
        data["results"]["humaneval"]["pass@1,create_test"] = pass_rate
        data["results"]["humaneval"]["pass@1"] = pass_rate
        print(f"Updated {os.path.basename(json_path)}: {old_pass} -> {pass_rate:.4f} ({passed_count}/{total_count})")

        tmp = json_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, json_path)


def main():
    results_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results"
    pattern = os.path.join(results_dir, "**", "*_utility_code_humaneval.json")
    files = glob.glob(pattern, recursive=True)

    print(f"Found {len(files)} utility_code_humaneval.json files to fix.")
    for f in files:
        fix_humaneval_json_file(f)

if __name__ == "__main__":
    main()
