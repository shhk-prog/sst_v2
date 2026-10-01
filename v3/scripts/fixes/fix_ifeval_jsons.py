import os
import sys
import glob
import json
import argparse

# v3/scripts/eval を path に追加
eval_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval"))
if eval_dir not in sys.path:
    sys.path.insert(0, eval_dir)

from eval_utility import fix_ifeval_responses, write_json_atomic


def fix_all_ifeval_jsons(results_dir):
    pattern = os.path.join(results_dir, "**", "*_utility_general_ifeval.json")
    files = glob.glob(pattern, recursive=True)
    print(f"Found {len(files)} utility_general_ifeval JSON files to inspect/fix.")

    modified_files = 0

    for filepath in sorted(files):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "samples" not in data:
                continue

            results_before = data.get("results", {}).get("ifeval", {}).copy()

            data = fix_ifeval_responses(data)

            results_after = data.get("results", {}).get("ifeval", {})

            if results_before != results_after:
                write_json_atomic(filepath, data)
                modified_files += 1
                b_strict = results_before.get("prompt_level_strict_acc,none")
                a_strict = results_after.get("prompt_level_strict_acc,none")
                print(f"  Fixed: {os.path.basename(filepath)} | Strict Acc: {b_strict} -> {a_strict}")

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print(f"\nProcessing complete. Updated {modified_files}/{len(files)} JSON files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", type=str, default="results")
    args = parser.parse_args()

    fix_all_ifeval_jsons(args.results_dir)
