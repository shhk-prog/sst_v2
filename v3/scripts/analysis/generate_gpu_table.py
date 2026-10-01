import os
import json
import re
from pathlib import Path

def main():
    merged_dir = Path("/Users/saki/lab/src/sst_v3/models/merged")
    
    # Store lists of times and memory for each method
    stats = {
        "data_free_sst_main": {"times": [], "mems": []},
        "diagonal_sst_main": {"times": [], "mems": []},
        "dare": {"times": [], "mems": []},
        "ties": {"times": [], "mems": []},
        "della": {"times": [], "mems": []},
        "task_arithmetic": {"times": [], "mems": []},
        "matena_fisher": {"times": [], "mems": []},
        "mergealign": {"times": [], "mems": []},
        "safemerge": {"times": [], "mems": []},
        "led_merging": {"times": [], "mems": []},
    }
    
    for p in merged_dir.glob("sst_merge_v3_main_*"):
        if not p.is_dir():
            continue
            
        profile_path = p / "runtime_profile.json"
        if not profile_path.exists():
            continue
            
        dir_name = p.name
        matched_method = None
        for method in stats.keys():
            if f"v3_main_{method}_" in dir_name:
                matched_method = method
                break
                
        if not matched_method:
            continue
            
        with open(profile_path, "r") as f:
            try:
                profile = json.load(f)
            except json.JSONDecodeError:
                continue
                
        total_time = None
        peak_mem = None
        for stage in profile:
            if stage.get("stage") == "total_merge_execution":
                total_time = stage.get("elapsed_sec")
                end_stats = stage.get("end_stats", {})
                peak_mem = end_stats.get("gpu_max_memory_allocated_gb", 0.0)
                break
                
        if total_time is not None and peak_mem is not None:
            stats[matched_method]["times"].append(total_time)
            stats[matched_method]["mems"].append(peak_mem)
            
    # Compute averages
    results = {}
    for method, data in stats.items():
        if data["times"]:
            avg_time = sum(data["times"]) / len(data["times"])
            avg_mem = sum(data["mems"]) / len(data["mems"])
            results[method] = (avg_time, avg_mem)
        else:
            results[method] = (0.0, 0.0)
            
    table = r"""\begin{table}[htbp]
\caption{各マージ手法の実測マージ時間とピークGPUメモリ（平均）}
\label{tab:gpu}
\centering
\small
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabularx}{\textwidth}{
>{\raggedright\arraybackslash}X
>{\centering\arraybackslash}p{3.4cm}
>{\centering\arraybackslash}p{3.4cm}
}
\toprule
\textbf{Method} &
\textbf{Average Merge Time (s) $\downarrow$} &
\textbf{Peak GPU Memory (GB) $\downarrow$} \\
\midrule
"""
    
    order = [
        "data_free_sst_main",
        "diagonal_sst_main",
        "dare",
        "ties",
        "della",
        "task_arithmetic",
        "matena_fisher",
        "mergealign",
        "safemerge",
        "led_merging"
    ]
    
    for method in order:
        time, mem = results[method]
        escaped_method = f"\\texttt{{{method.replace('_', '\\_')}}}"
        
        if method == "data_free_sst_main":
            table += f"{escaped_method} & \\textbf{{{int(round(time))}}} & \\textbf{{{mem:.2f}}} \\\\\n"
        else:
            table += f"{escaped_method} & {int(round(time))} & {mem:.2f} \\\\\n"
            
    table += r"""\bottomrule
\end{tabularx}
\end{table}"""

    print("Generated Table:\n")
    print(table)
    
    out_path = "/Users/saki/lab/src/sst_v3/docs/flmsec/tables/tab_gpu.tex"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(table)
    print(f"\nTable successfully written to {out_path}")

if __name__ == "__main__":
    main()