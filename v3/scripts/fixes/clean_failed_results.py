import os
import json
import glob

def main():
    results_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320"
    
    # 指定ディレクトリ以下のすべての JSON ファイルを再帰的に取得
    json_files = glob.glob(os.path.join(results_dir, "**/*.json"), recursive=True)
    
    print(f"Scanning {len(json_files)} JSON files in {results_dir}...")
    
    deleted_count = 0
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # completed が False、または status が failed のファイルを特定
            if isinstance(data, dict) and (data.get("completed") is False or data.get("status") == "failed"):
                print(f"Deleting: {file_path}")
                os.remove(file_path)
                deleted_count += 1
        except Exception as e:
            # 破損ファイルや読み込めないファイルはスキップ
            print(f"Skip (Error reading {file_path}): {e}")

    print(f"\nCompleted! Deleted {deleted_count} failed result files.")

if __name__ == "__main__":
    main()
