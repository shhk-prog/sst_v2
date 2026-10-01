import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent.parent
results_file = project_root / "scripts/fim_validation_ablation_results.json"
output_dir = project_root / "docs/Rebuttal/figures"
output_dir.mkdir(parents=True, exist_ok=True)

with open(results_file, "r") as f:
    results = json.load(f)

def plot_intervention(data, method_name, title, ylabel, filename):
    plt.figure(figsize=(8, 6))
    
    colors = {"fim": "#1f77b4", "magnitude": "#ff7f0e", "gradient": "#2ca02c", "random": "#9467bd"}
    labels = {"fim": "Utility FIM", "magnitude": "Weight Magnitude", "gradient": "Gradient absolute", "random": "Random"}
    markers = {"fim": "o", "magnitude": "s", "gradient": "^", "random": "x"}
    
    for score_type, series in data.items():
        if not series: continue
        ratios = [item["ratio"] * 100 for item in series]
        deltas = [item["delta"] for item in series]
        
        plt.plot(ratios, deltas, marker=markers[score_type], 
                 color=colors[score_type], label=labels[score_type], linewidth=2, markersize=8)
                 
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    plt.xlabel(f"Intervention Ratio (%)", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(title, fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=300)
    print(f"Saved {filename}")

# Experiment B: Prune Top-K (Destruction)
# 期待: Utility FIM上位を破壊するとLossが大きく増加する（= FIMが高いパラメータはUtilityにとって本当に重要）
if "prune_top" in results:
    plot_intervention(
        results["prune_top"], 
        "prune_top", 
        "Utility Degradation when Pruning Top-K Important Params",
        "Utility Loss Increase (Delta)",
        "fim_validation_prune_top.png"
    )

# Experiment C: Modify Bottom-K (Protection)
# 期待: Utility FIM下位のみを少し変更してもLossは増加しない（= 低FIM領域はSafety書き換えに安全）
if "modify_bottom" in results:
    plot_intervention(
        results["modify_bottom"], 
        "modify_bottom", 
        "Utility Degradation when Modifying Bottom-K Important Params",
        "Utility Loss Increase (Delta)",
        "fim_validation_modify_bottom.png"
    )
