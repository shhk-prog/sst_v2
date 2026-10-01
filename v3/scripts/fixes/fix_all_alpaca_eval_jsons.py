"""
Fix existing _alpaca_eval2.json files by correctly parsing leaderboard.csv for the target model row.
"""

import os
import glob
import json
import pandas as pd

def fix_alpaca_json(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return False

    if not isinstance(data, dict):
        return False

    # Find leaderboard.csv
    alpaca_out_dir = data.get("alpaca_eval_output_dir")
    leaderboard_path = data.get("leaderboard_path")

    if not leaderboard_path or not os.path.exists(leaderboard_path):
        if alpaca_out_dir:
            possible_lb = os.path.join(alpaca_out_dir, "weighted_alpaca_eval_gpt4_turbo", "leaderboard.csv")
            if os.path.exists(possible_lb):
                leaderboard_path = possible_lb
            else:
                possible_lb2 = os.path.join(alpaca_out_dir, "leaderboard.csv")
                if os.path.exists(possible_lb2):
                    leaderboard_path = possible_lb2

    # Also search adjacent directory matching _alpaca_eval_out
    if not leaderboard_path or not os.path.exists(leaderboard_path):
        adjacent_dir = json_path.replace(".json", "_alpaca_eval_out")
        possible_lb = os.path.join(adjacent_dir, "weighted_alpaca_eval_gpt4_turbo", "leaderboard.csv")
        if os.path.exists(possible_lb):
            leaderboard_path = possible_lb

    if not leaderboard_path or not os.path.exists(leaderboard_path):
        # Print if missing
        # print(f"Skip (no leaderboard): {json_path}")
        return False

    model_outputs_path = data.get("model_outputs_path", "")
    base_name = os.path.basename(json_path).replace("_alpaca_eval2.json", "")
    output_stem = os.path.splitext(os.path.basename(model_outputs_path))[0] if model_outputs_path else ""

    try:
        df = pd.read_csv(leaderboard_path)
    except Exception as e:
        print(f"Error reading {leaderboard_path}: {e}")
        return False

    first_col = df.columns[0]

    matching_rows = df[df[first_col] == output_stem]

    if matching_rows.empty and output_stem:
        matching_rows = df[df[first_col].astype(str).str.contains(output_stem, regex=False)]

    if matching_rows.empty:
        target_stem = output_stem.replace("_alpaca_outputs", "")
        matching_rows = df[df[first_col].astype(str).apply(lambda s: str(s) in output_stem or (target_stem and target_stem in str(s)))]

    if matching_rows.empty:
        matching_rows = df[df[first_col].astype(str).apply(lambda s: s in base_name or base_name in s)]

    if matching_rows.empty:
        non_null = df[df[first_col] != "NullModel"]
        if not non_null.empty:
            row = non_null.iloc[-1]
        else:
            row = df.iloc[0]
    else:
        row = matching_rows.iloc[0]

    win_rate = float(row.get("win_rate", 0))
    model_name_in_lb = str(row[first_col])

    old_win_rate = data.get("win_rate")
    if old_win_rate != win_rate:
        print(f"Fixing {os.path.basename(json_path)}: {old_win_rate} -> {win_rate} (model: {model_name_in_lb})")
        data["win_rate"] = win_rate
        data["std_err"] = float(row.get("standard_error", 0))
        data["n_wins"] = int(row.get("n_wins", 0))
        data["n_draws"] = int(row.get("n_draws", 0))
        if "n_loses" in row:
            data["n_loses"] = int(row.get("n_loses", 0))
        elif "n_total" in row:
            data["n_loses"] = int(row.get("n_total", 0)) - int(row.get("n_wins", 0)) - int(row.get("n_draws", 0))
        data["model_name_in_leaderboard"] = model_name_in_lb
        if "length_controlled_winrate" in row and pd.notna(row.get("length_controlled_winrate")):
            data["length_controlled_winrate"] = float(row.get("length_controlled_winrate"))
        data["leaderboard_path"] = leaderboard_path

        tmp = json_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, json_path)
        return True

    return False

def main():
    results_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results"
    pattern = os.path.join(results_dir, "**", "*_alpaca_eval2.json")
    files = glob.glob(pattern, recursive=True)

    print(f"Found {len(files)} _alpaca_eval2.json files to check.")
    fixed_count = 0
    for f in files:
        if fix_alpaca_json(f):
            fixed_count += 1

    print(f"Completed! Fixed {fixed_count} files.")

if __name__ == "__main__":
    main()
