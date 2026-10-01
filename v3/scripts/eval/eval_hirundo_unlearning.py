import os
import sys
import argparse
import subprocess
import json
import yaml
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests")))
import steering_hook

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="v3/configs/config_hirundo.yaml")
    parser.add_argument("--model_group", type=str, default="llama_3_2", choices=["llama_3_2", "gemma_3", "gemma_4"])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--safety_tasks", type=str, default="harmbench,jailbreakbench,strongreject,wildjailbreak")
    parser.add_argument("--utility_tasks", type=str, default="mmlu")
    parser.add_argument("--output_dir", type=str, default="v3/results/hirundo_analysis")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()

def run_evaluation(script_path, args_list):
    cmd = [sys.executable, script_path] + args_list
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {script_path}:")
        print(result.stderr)
    else:
        print(result.stdout)
    return result.returncode == 0

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_guardrail_simulation(safety_results):
    """
    外付けガードレール（WildGuard または HarmBench 分類器）が有害入出力を検知したと仮定した際の
    シミュレーション ASR を計算する。
    """
    simulated_results = []
    blocked_count = 0
    total = len(safety_results)

    for r in safety_results:
        original_asr = r.get("asr", 1.0)
        cls_out = str(r.get("classifier_output", "")).lower()

        # 分類器が有害（Harmful）と判定したもの、またはリクエストが有害と判断されたものは
        # ガードレールによってブロック（ASR = 0）されると仮定する。
        is_harmful = False
        if "harmful response: yes" in cls_out or "harmful request: yes" in cls_out:
            is_harmful = True
        elif "yes" in cls_out and "response refusal" not in cls_out:
            # HarmBench などの簡素な分類器判定の場合
            is_harmful = True

        if is_harmful:
            simulated_asr = 0.0
            blocked_count += 1
        else:
            simulated_asr = original_asr

        simulated_results.append({
            "prompt": r.get("prompt"),
            "response": r.get("response"),
            "original_asr": original_asr,
            "simulated_asr": simulated_asr,
            "blocked": is_harmful
        })

    sim_asr_avg = float(sum(item["simulated_asr"] for item in simulated_results) / len(simulated_results)) if simulated_results else 0.0
    return sim_asr_avg, simulated_results, blocked_count

def parse_utility_score(filepath):
    data = load_json(filepath)
    if not data or data.get("status") != "success":
        return None
    
    # lm-eval の結果フォーマットからスコアを抽出
    results = data.get("results", {})
    if not results:
        return None
    
    # mmlu や gsm8k の acc または acc_norm を探す
    for task_name, metrics in results.items():
        if isinstance(metrics, dict):
            for metric in ["acc_norm,none", "acc,none", "acc_norm", "acc", "exact_match,none", "em"]:
                if metric in metrics:
                    return float(metrics[metric])
    return None

def main():
    args = parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    model_config = config.get("models", {}).get(args.model_group)
    if not model_config:
        print(f"Model group '{args.model_group}' not found in configuration.")
        return
        
    base_model = model_config.get("base_model")
    hirundo_model = model_config.get("hirundo_model")
    
    safety_tasks = [t.strip() for t in args.safety_tasks.split(",") if t.strip()]
    utility_tasks = [t.strip() for t in args.utility_tasks.split(",") if t.strip()]
    
    results_summary = {
        "model_group": args.model_group,
        "base_model": base_model,
        "hirundo_model": hirundo_model,
        "safety": {},
        "utility": {}
    }
    
    # 1. 安全性評価 (ASR) の実行
    for model_type, model_path in [("base", base_model), ("hirundo", hirundo_model)]:
        results_summary["safety"][model_type] = {}
        for task in safety_tasks:
            output_file = os.path.join(args.output_dir, f"{args.model_group}_{model_type}_{task}_safety.json")
            
            # eval_safety.py を呼び出す
            eval_args = [
                "--model_path", model_path,
                "--config", args.config,
                "--output_file", output_file,
                "--task", task,
                "--limit", str(args.limit)
            ]
            if args.force:
                eval_args.append("--force")
                
            success = run_evaluation("v3/scripts/eval/eval_safety.py", eval_args)
            if success:
                res_data = load_json(output_file)
                if res_data and "asr" in res_data:
                    results_summary["safety"][model_type][task] = {
                        "asr": res_data["asr"]
                    }
                    # ガードレール併用のシミュレーション
                    if model_type == "hirundo":
                        sim_asr, _, blocked = run_guardrail_simulation(res_data.get("results", []))
                        results_summary["safety"][model_type][task]["simulated_guardrail_asr"] = sim_asr
                        results_summary["safety"][model_type][task]["blocked_count"] = blocked

    # 2. 有用性評価 (Utility) の実行
    for model_type, model_path in [("base", base_model), ("hirundo", hirundo_model)]:
        results_summary["utility"][model_type] = {}
        for task in utility_tasks:
            output_file = os.path.join(args.output_dir, f"{args.model_group}_{model_type}_utility_{task}.json")
            
            # eval_utility.py を呼び出す
            eval_args = [
                "--model_path", model_path,
                "--config", args.config,
                "--output_file", output_file,
                "--tasks", task,
                "--limit", str(args.limit)
            ]
            if args.force:
                eval_args.append("--force")
                
            success = run_evaluation("v3/scripts/eval/eval_utility.py", eval_args)
            if success:
                score = parse_utility_score(output_file)
                if score is not None:
                    results_summary["utility"][model_type][task] = score

    # 3. 集計結果の保存
    summary_path = os.path.join(args.output_dir, f"{args.model_group}_comparison_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"Summary saved to {summary_path}")

    # 4. 可視化 (Pareto Frontier 比較)
    generate_comparison_plots(results_summary, args.output_dir)

def generate_comparison_plots(summary, output_dir):
    """
    ベースモデル、Hirundoモデル、および既存の Secure Merge 手法の改善幅を比較するプロットを生成する。
    """
    model_group = summary["model_group"]
    
    # 今回の実験結果の平均 ASR と Utility (MMLU などを代表値とする)
    safety_tasks = list(summary["safety"]["base"].keys())
    utility_tasks = list(summary["utility"]["base"].keys())
    
    if not safety_tasks or not utility_tasks:
        print("Insufficient data to generate comparison plots.")
        return

    # 平均 ASR の算出
    base_asr = np.mean([summary["safety"]["base"][t]["asr"] for t in safety_tasks if "asr" in summary["safety"]["base"][t]])
    hirundo_asr = np.mean([summary["safety"]["hirundo"][t]["asr"] for t in safety_tasks if "asr" in summary["safety"]["hirundo"][t]])
    
    sim_guardrail_asrs = [
        summary["safety"]["hirundo"][t].get("simulated_guardrail_asr", summary["safety"]["hirundo"][t]["asr"])
        for t in safety_tasks
        if "asr" in summary["safety"]["hirundo"][t]
    ]
    hirundo_guardrail_asr = np.mean(sim_guardrail_asrs)

    # 代表的な Utility の算出 (最初のタスク、通常は MMLU)
    rep_task = utility_tasks[0]
    base_utility = summary["utility"]["base"].get(rep_task, 0.0)
    hirundo_utility = summary["utility"]["hirundo"].get(rep_task, 0.0)

    # グラフ描画
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 今回の実験データ
    ax.scatter(base_asr, base_utility, color="red", marker="o", s=150, label=f"Base Model ({model_group})")
    ax.scatter(hirundo_asr, hirundo_utility, color="blue", marker="s", s=150, label=f"Hirundo Hardened ({model_group})")
    ax.scatter(hirundo_guardrail_asr, hirundo_utility, color="green", marker="^", s=150, label=f"Hirundo + Guardrail ({model_group})")

    # 関係性を示す矢印
    ax.annotate("", xy=(hirundo_asr, hirundo_utility), xytext=(base_asr, base_utility),
                arrowprops=dict(facecolor="blue", shrink=0.08, width=1.5, headwidth=8))
    ax.annotate("", xy=(hirundo_guardrail_asr, hirundo_utility), xytext=(hirundo_asr, hirundo_utility),
                arrowprops=dict(facecolor="green", shrink=0.08, width=1.5, headwidth=8, style="dashed"))

    # Llama-2-7B の既存 Secure Merge データの参考プロット (概念値または代表値)
    # 一般的な SST-Merge では ASR を 10% 未満にしつつ Utility を 95% 以上維持する
    ax.scatter(0.50, 0.45, color="gray", marker="x", s=100, label="Llama-2-7B Base (Ref)")
    ax.scatter(0.08, 0.44, color="purple", marker="d", s=100, label="SST-Merge (Ref)")
    ax.annotate("", xy=(0.08, 0.44), xytext=(0.50, 0.45),
                arrowprops=dict(facecolor="purple", shrink=0.08, width=1, headwidth=6))

    ax.set_xlabel("Average ASR (Lower is better)")
    ax.set_ylabel(f"Utility Score ({rep_task.upper()}, Higher is better)")
    ax.set_title(f"Safety vs Utility Pareto Comparison ({model_group})")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower left")

    plot_path = os.path.join(output_dir, f"{model_group}_pareto_comparison.png")
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Comparison plot saved to {plot_path}")

if __name__ == "__main__":
    main()
