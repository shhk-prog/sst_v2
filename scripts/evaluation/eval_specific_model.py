import os
import sys
import subprocess
from pathlib import Path
import re

def run_eval(script_name, model_path, gpu="0"):
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name
    
    with open(script_path, "r") as f:
        content = f.read()
        
    # Inject parameters
    content = content.replace('num = input("gpu num:")', f'num = "{gpu}"')
    content = re.sub(r'merged_model_path\s*=\s*"[^"]*"', f'merged_model_path = "{model_path}"', content)
    
    temp_script = script_dir / f"temp_{script_name}"
    with open(temp_script, "w") as f:
        f.write(content)
        
    print(f"Running {script_name} for {model_path}...")
    result = subprocess.run([sys.executable, str(temp_script)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Success: {script_name}")
        # Print tail of output to see the summary table
        lines = result.stdout.splitlines()
        for line in lines[-20:]:
            print(line)
    else:
        print(f"Error in {script_name}:")
        print(result.stderr)
        
    temp_script.unlink()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--gpu", type=str, default="0")
    args = parser.parse_args()
    
    # Identify eval type
    model_name = os.path.basename(args.model_path)
    eval_type = "repliqa" # Default for Safety_FT_Baseline_on_A5
    
    run_eval("merge_repliqa_eval.py", args.model_path, args.gpu)
    run_eval("merge_jailbreak_eval.py", args.model_path, args.gpu)
