"""
Scan all HarmBench safety evaluation JSON files and report statistics.
"""

import os
import glob
import json

def main():
    results_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results"
    pattern = os.path.join(results_dir, "**", "*_harmbench_safety.json")
    files = glob.glob(pattern, recursive=True)

    print(f"Found {len(files)} harmbench_safety.json files.")

    data_by_method = {}
    failed_count = 0
    incomplete_count = 0
    mock_count = 0
    valid_count = 0

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            failed_count += 1
            continue

        if not isinstance(data, dict):
            failed_count += 1
            continue

        if data.get("mockup") is True:
            mock_count += 1

        if data.get("status") != "success" or data.get("completed") is not True:
            incomplete_count += 1
            continue

        valid_count += 1
        asr = data.get("asr")
        n = data.get("n", 0)
        fname = os.path.basename(f)

        # Print some examples
        if "data_free_sst" in fname and "safety+math" in fname:
            print(f"{fname} -> asr={asr}, n={n}")

    print("\nSummary:")
    print(f"Total files: {len(files)}")
    print(f"Valid completed: {valid_count}")
    print(f"Incomplete/Failed: {incomplete_count}")
    print(f"Mockup flagged: {mock_count}")

if __name__ == "__main__":
    main()
