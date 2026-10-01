import json
import sys
import os

def test_code(code, test_cases):
    full_code = code + "\n" + test_cases
    global_env = {}
    try:
        exec(full_code, global_env)
        return True, None
    except Exception as e:
        return False, str(e)

def clean_mbpp_code(resp):
    if not isinstance(resp, str):
        return resp
    # [END] タグの削除
    if "[END]" in resp:
        resp = resp.split("[END]")[0]
    # Markdown のコードブロック除去
    if "```python" in resp:
        resp = resp.split("```python")[1].split("```")[0]
    elif "```" in resp:
        resp = resp.split("```")[1].split("```")[0]
    return resp.strip()

def main():
    json_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/base/sst_merge_v3_main_base_WizardCoder_utility_code_mbpp.json"
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", {}).get("mbpp", [])
    print(f"Total samples: {len(samples)}")

    raw_correct = 0
    cleaned_correct = 0

    syntax_errors_raw = 0
    syntax_errors_cleaned = 0

    for i, s in enumerate(samples):
        resps = s.get("filtered_resps", s.get("resps", [[""]]))
        if isinstance(resps[0], list):
            code_raw = resps[0][0]
        else:
            code_raw = resps[0]

        target = s.get("target", "")

        # Raw test
        ok_raw, err_raw = test_code(code_raw, target)
        if ok_raw:
            raw_correct += 1

        # Cleaned test
        code_cleaned = clean_mbpp_code(code_raw)
        ok_clean, err_clean = test_code(code_cleaned, target)
        if ok_clean:
            cleaned_correct += 1

    print(f"Raw Pass@1: {raw_correct} / {len(samples)} ({raw_correct / len(samples) * 100:.2f}%)")
    print(f"Cleaned Pass@1: {cleaned_correct} / {len(samples)} ({cleaned_correct / len(samples) * 100:.2f}%)")

if __name__ == "__main__":
    main()
