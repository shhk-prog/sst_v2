# scripts/evaluation/eval_llama2_suite.py
import os
import sys
import json
import yaml
import argparse
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# scripts フォルダをパスに追加して steering_hook をインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import steering_hook

def parse_args():
    parser = argparse.ArgumentParser(description="Llama-2-7B Evaluation Suite (Utility & Safety)")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    parser.add_argument("--model_path", type=str, required=True, help="Merged model path to evaluate")
    parser.add_argument("--output_dir", type=str, default="results/raw", help="Directory to save raw results")
    parser.add_argument("--device", type=str, default="cuda:0", help="Computation device (e.g. cuda:0, cpu)")
    parser.add_argument("--skip_utility", action="store_true", help="Skip utility evaluation")
    parser.add_argument("--skip_safety", action="store_true", help="Skip safety evaluation")
    return parser.parse_args()

class Llama2Evaluator:
    def __init__(self, config_path, model_path, output_dir, device):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.model_path = model_path
        self.output_dir = output_dir
        self.device = device
        self.model_name_or_path = self.config["model"]["base_model"]
        
        # steering_hookによる事前検証
        class DummyArgs:
            pass
        args = DummyArgs()
        args.base_model = self.model_name_or_path
        args.method = self.config["merge"]["method"]
        args.eval_dataset_path = None
        args.utility_dataset_path = None
        steering_hook.verify_experiment_config(args)

    def run_utility_eval(self):
        """lm-evaluation-harnessを用いてUtility評価を一括実行 (既存のrun_utility_eval.pyを呼び出し)"""
        print(f"=== Running Real Utility Evaluation for {self.model_path} ===")
        basename = os.path.basename(self.model_path.rstrip("/"))
        
        # coding, general それぞれで評価を実行
        for eval_type in ["coding", "general"]:
            cmd = [
                "python3", "scripts/fine_tuning/run_utility_eval.py",
                "--base_model", self.model_path,
                "--model_name", basename,
                "--eval_type", eval_type,
                "--output_json", os.path.join(self.output_dir, f"{basename}_utility_summary.json"),
                "--batch_size", "4"
            ]
            if "cuda" in self.device:
                cmd += ["--apply_chat_template"]
                
            print(f"Executing utility command: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[Error] Failed to run utility eval for {eval_type}: {e}")

    def run_safety_eval(self):
        """Safety評価 (既存のrun_safety_eval.pyおよびrun_harmbench_eval.pyを呼び出してLlama-Guard-3でASRを判定)"""
        print(f"=== Running Real Safety Evaluation for {self.model_path} ===")
        basename = os.path.basename(self.model_path.rstrip("/"))
        
        # 1. AdvBench 評価
        advbench_data = "data/safety_advbench.json"
        if os.path.exists(advbench_data):
            cmd = [
                "python3", "scripts/fine_tuning/run_safety_eval.py",
                "--base_model", self.model_path,
                "--model_name", basename,
                "--data_path", advbench_data,
                "--task_name", "safety_advbench",
                "--n_samples", "100",
                "--output_json", os.path.join(self.output_dir, f"{basename}_safety_summary.json")
            ]
            print(f"Executing safety command: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[Error] Failed to run safety eval: {e}")
                
        # 2. HarmBench 評価 (OOD)
        harmbench_data = "data/safety_harmbench.json"
        if os.path.exists(harmbench_data):
            cmd = [
                "python3", "scripts/fine_tuning/run_harmbench_eval.py",
                "--base_model", self.model_path,
                "--model_name", basename,
                "--data_path", harmbench_data,
                "--n_samples", "100",
                "--output_json", os.path.join(self.output_dir, f"{basename}_safety_summary.json")
            ]
            print(f"Executing harmbench command: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[Error] Failed to run harmbench eval: {e}")

def main():
    args = parse_args()
    evaluator = Llama2Evaluator(args.config, args.model_path, args.output_dir, args.device)
    
    if not args.skip_utility:
        evaluator.run_utility_eval()
    if not args.skip_safety:
        evaluator.run_safety_eval()

if __name__ == "__main__":
    main()
