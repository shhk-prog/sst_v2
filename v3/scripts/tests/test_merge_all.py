import os
import subprocess
import sys
import shutil

def run_cmd(cmd):
    print(f"\nRunning command: {' '.join(cmd)}")
    res = subprocess.run(cmd, text=True)
    return res.returncode

def main():
    # v3 ディレクトリがカレントディレクトリであることを想定
    config_path = "configs/config_dummy.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Please run this script from the 'v3' directory.")
        sys.exit(1)
        
    # テスト対象の手法と対応するマージ用コマンド引数
    methods = {
        "diagonal_sst": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "diagonal_sst",
            "--sst_ratio", "Fh/Fb",
            "--variant", "interpolation",
            "--mask_type", "hard mask",
            "--alpha", "0.5",
            "--k", "0.2",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_diagonal_sst"
        ],
        "data_free_sst": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "data_free_sst",
            "--sst_ratio", "Fh/Fb",
            "--variant", "interpolation",
            "--mask_type", "hard mask",
            "--alpha", "0.5",
            "--k", "0.2",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_data_free_sst"
        ],
        "ties": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "ties",
            "--alpha", "0.5",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_ties"
        ],
        "dare": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "dare",
            "--alpha", "0.5",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_dare"
        ],
        "task_arithmetic": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "task_arithmetic",
            "--alpha", "0.5",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_task_arithmetic"
        ],
        "della": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "della",
            "--alpha", "0.5",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_della"
        ],
        "fisher_weighted": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "fisher_weighted",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_fisher_weighted"
        ],
        "safemerge": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "safemerge",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_safemerge"
        ],
        "led_merging": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "led_merging",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_led_merging"
        ],
        "mergealign": [
            sys.executable, "scripts/merge.py",
            "--config", config_path,
            "--method", "mergealign",
            "--pattern", "safety+math",
            "--seed", "42",
            "--output_dir", "models/merged/test_mergealign"
        ]
    }
    
    # 既存のテスト用出力をクリア
    test_merged_dir = "models/merged"
    if os.path.exists(test_merged_dir):
        print(f"Cleaning up old test outputs in {test_merged_dir}...")
        # ディレクトリごと消去すると一時フォルダも消えるので、test_で始まるディレクトリのみ削除
        for item in os.listdir(test_merged_dir):
            if item.startswith("test_"):
                shutil.rmtree(os.path.join(test_merged_dir, item))
                
    results = {}
    
    print("\n==================================================")
    print("Starting Model Merging Validation for All 10 Methods")
    print("==================================================")
    
    for method, cmd in methods.items():
        print(f"\n--- Testing Method: {method} ---")
        ret = run_cmd(cmd)
        
        # モデルが保存されたか確認
        out_dir = cmd[-1]
        success = (ret == 0) and os.path.exists(out_dir)
        
        # SafeMERGE は出力ディレクトリ名に閾値やパラメータが含まれる特殊な構造のため、
        # ディレクトリの存在チェックを配下の検索で行う
        if method == "safemerge" and ret == 0:
            if os.path.exists(out_dir) and len(os.listdir(out_dir)) > 0:
                success = True
                
        results[method] = {
            "exit_code": ret,
            "success": success,
            "output_dir": out_dir
        }
        
    print("\n==================================================")
    print("Validation Summary")
    print("==================================================")
    all_success = True
    for method, res in results.items():
        status = "SUCCESS" if res["success"] else "FAILED"
        if not res["success"]:
            all_success = False
        print(f"- {method:<20}: {status} (Exit Code: {res['exit_code']}, Path: {res['output_dir']})")
        
    print("==================================================")
    if all_success:
        print("ALL METHODS COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME METHODS FAILED. PLEASE CHECK THE LOG ABOVE.")
        sys.exit(1)

if __name__ == "__main__":
    main()
