import subprocess
import os
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from dotenv import load_dotenv

# .env をロード
load_dotenv(os.path.expanduser("~/src/.env"))
sst_home = os.getenv("SST_HOME", "/mnt/nas/home/hiromi/src/sst_v2")

project_root = Path(sst_home) / "v1"
checkpoints = [
    "checkpoint-15",
    "checkpoint-30",
    "checkpoint-45",
    "checkpoint-60",
    "checkpoint-75"
]

def eval_checkpoint(cp_name, gpu_id):
    model_path = f"models/finetuned/adapters/FT_model/Safety_FT_Baseline_on_A5/{cp_name}"
    print(f"Starting evaluation for {cp_name} on GPU {gpu_id}...")
    
    # 仮想環境の python パスを設定
    python_exe = Path(sst_home) / "venv_sst/bin/python"
    if not python_exe.exists():
        python_exe = Path(sst_home) / "v1/sst/bin/python"

    cmd = [
        str(python_exe),
        "scripts/evaluation/eval_specific_model.py",
        "--model_path", model_path,
        "--gpu", str(gpu_id),
    ]
    
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Finished {cp_name} successfully.")
    else:
        print(f"Error evaluating {cp_name}: {result.stderr}")
    return cp_name, result.stdout

def main():
    for cp in checkpoints:
        eval_checkpoint(cp, gpu_id=2)
    print("All evaluations complete.")

if __name__ == "__main__":
    main()
