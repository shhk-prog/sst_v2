import os
import glob


def clean_all_ifeval_jsons(results_dir="results"):
    pattern1 = os.path.join(results_dir, "**", "*_utility_general_ifeval.json")
    pattern2 = os.path.join(results_dir, "**", "*general_ifeval*.json")

    files = sorted(list(set(glob.glob(pattern1, recursive=True) + glob.glob(pattern2, recursive=True))))

    if not files:
        print("No general_ifeval JSON files found.")
        return

    print(f"Found {len(files)} general_ifeval JSON result files to delete:")

    deleted_count = 0
    for filepath in files:
        try:
            os.remove(filepath)
            print(f"  Deleted: {filepath}")
            deleted_count += 1
        except Exception as e:
            print(f"  Failed to delete {filepath}: {e}")

    print(f"\nCompleted: Deleted {deleted_count}/{len(files)} general_ifeval JSON files.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", type=str, default="results")
    args = parser.parse_args()
    clean_all_ifeval_jsons(args.results_dir)
