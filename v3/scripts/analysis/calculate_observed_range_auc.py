import sys
import os
import glob
import argparse
import pandas as pd
import numpy as np
import json

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def extract_safety_harmful_asr(data):
    if not isinstance(data, dict): return None
    results = data.get("results", [])
    if not results or not isinstance(results, list):
        asr = data.get("asr", None)
        if asr is not None:
            asr = float(asr)
            if asr > 1.0: asr = asr / 100.0
            return asr
        return None
    valid_samples = [item for item in results if not item.get("is_gibberish", False)]
    total_valid = len(valid_samples)
    if total_valid == 0: return None
    harmful_count = 0
    for item in valid_samples:
        hb_cls = item.get("harmbench_cls_output")
        if hb_cls == "Yes":
            harmful_count += 1
        elif item.get("original_asr", 0.0) > 0.5 or item.get("asr", 0.0) > 0.5:
            harmful_count += 1
    return float(harmful_count) / float(total_valid)

def extract_metric(data, metric_name):
    if "results" not in data: return None
    results = data["results"]
    for task, metrics in results.items():
        if not isinstance(metrics, dict): continue
        if metric_name in metrics: return float(metrics[metric_name])
        for k, v in metrics.items():
            if "pass@1" in k or "pass_at_1" in k or "acc" in k or "exact_match" in k:
                if not str(k).endswith("_stderr"): return float(v)
    return None

def parse_info(filename):
    is_base = "base" in filename.lower()
    method = None
    pattern = None
    if is_base:
        base_name_found = "Base Model"
        for bn in ["WizardMath", "WizardCoder", "MedAlpaca", "SafetyFT", "Llama3"]:
            if bn.lower() in filename.lower():
                base_name_found = bn
                break
        method = f"Base ({base_name_found})"
        pattern = f"Base ({base_name_found})"
    else:
        for m in ["diagonal_sst_main", "data_free_sst_main", "task_arithmetic", "ties", "dare", "della", "mergealign", "safemerge", "led_merging", "matena_fisher"]:
            if m in filename:
                method = m
                break
        for p in ["safety+math+code+medical", "safety+math", "safety+code", "safety+medical"]:
            if p in filename:
                pattern = p
                break
    
    alpha = 0.5
    seed = 42
    for part in filename.split("_"):
        if part.startswith("alpha"):
            try: alpha = float(part.replace("alpha", ""))
            except: pass
        if part.startswith("seed"):
            try: seed = int(part.replace("seed", ""))
            except: pass
    return {"method": method, "pattern": pattern, "alpha": alpha, "seed": seed, "is_base": is_base}

def calculate_both_aucs(df_method):
    if df_method.empty: return 0.0, 0.0, None, None
    df_valid = df_method.dropna(subset=["asr", "utility"]).copy()
    if df_valid.empty: return 0.0, 0.0, None, None
    df_valid["asr"] = np.clip(df_valid["asr"], 0.0, 1.0)
    df_valid["utility"] = np.clip(df_valid["utility"], 0.0, 1.0)
    df_sorted = df_valid.sort_values(by=["asr", "utility"], ascending=[True, False])
    
    pareto_points = []
    max_util = -1.0
    for _, row in df_sorted.iterrows():
        if row["utility"] > max_util:
            pareto_points.append((float(row["asr"]), float(row["utility"])))
            max_util = float(row["utility"])
            
    if len(pareto_points) < 2: return 0.0, 0.0, None, None
    xs = [p[0] for p in pareto_points]
    ys = [p[1] for p in pareto_points]
    
    # xs is ASR. We want to output min and max Valid Safety Rate (1 - ASR).
    # Since xs is sorted in ascending order (0.0 to 1.0),
    # xs[0] is the min ASR (max VSR).
    # xs[-1] is the max ASR (min VSR).
    s_min = 1.0 - xs[-1]
    s_max = 1.0 - xs[0]
    
    observed_auc = float(np.trapezoid(ys, xs))
    
    xs_ext, ys_ext = xs.copy(), ys.copy()
    if xs_ext[0] > 0.0:
        xs_ext.insert(0, 0.0)
        ys_ext.insert(0, ys_ext[0])
    if xs_ext[-1] < 1.0:
        xs_ext.append(1.0)
        ys_ext.append(ys_ext[-1])
        
    validity_aware_auc = float(np.trapezoid(ys_ext, xs_ext))
    return validity_aware_auc, observed_auc, s_min, s_max

def normalize_value(val):
    if val is None: return None
    val = float(val)
    if val > 1.0: val /= 100.0
    return np.clip(val, 0.0, 1.0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", type=str, default="../../results/vllm")
    parser.add_argument("--merge_target", type=str, default="safety+math")
    args = parser.parse_args()

    print(f"Loading data from {args.results_dir}...")
    json_files = glob.glob(os.path.join(args.results_dir, "**", "*.json"), recursive=True)
    
    main_store = {}
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        if "summary" in filename or filename.startswith("."): continue
        
        # Fast filter
        if args.merge_target not in filename and "base" not in filename.lower(): continue
        
        info = parse_info(filename)
        if info["pattern"] != args.merge_target and info["pattern"] != "Base (WizardMath)": continue
        
        m_key = None
        for k in ["harmbench", "gsm8k", "minerva_math500", "utility_math"]:
            if k in filename:
                m_key = k
                break
        if not m_key: continue
        
        key = (info["seed"], info["method"], info["alpha"])
        
        content = load_json(filepath)
        if not content: continue
        
        if key not in main_store: main_store[key] = {}
        
        if m_key == "harmbench":
            val = extract_safety_harmful_asr(content)
            if val is not None: main_store[key]["harmbench"] = val
        elif m_key == "utility_math":
            v1 = extract_metric(content, "gsm8k")
            v2 = extract_metric(content, "minerva_math500")
            if v1 is not None: main_store[key]["gsm8k"] = v1
            if v2 is not None: main_store[key]["minerva_math500"] = v2
        elif m_key in ["gsm8k", "minerva_math500"]:
            val = extract_metric(content, m_key)
            if val is not None: main_store[key][m_key] = val

    records = []
    for (seed, method, alpha), metrics in main_store.items():
        if method is None: continue
        asr = metrics.get("harmbench")
        gsm8k = metrics.get("gsm8k")
        minerva = metrics.get("minerva_math500")

        if asr is None or (gsm8k is None and minerva is None): continue

        utils = []
        if gsm8k is not None: utils.append(normalize_value(gsm8k))
        if minerva is not None: utils.append(normalize_value(minerva))
        
        records.append({
            "method": "base" if method.startswith("Base") else method.lower(),
            "seed": seed,
            "alpha": alpha,
            "asr": normalize_value(asr),
            "utility": np.mean(utils) if utils else None
        })

    df_task = pd.DataFrame(records)
    if df_task.empty:
        print("No data found.")
        return

    results = []
    for method, df_m in df_task.groupby("method"):
        if method == "base": continue
        
        auc_va_list, auc_obs_list, s_min_list, s_max_list = [], [], [], []
        for seed, df_s in df_m.groupby("seed"):
            va_auc, obs_auc, s_min, s_max = calculate_both_aucs(df_s)
            if s_min is not None:
                auc_va_list.append(va_auc)
                auc_obs_list.append(obs_auc)
                s_min_list.append(s_min)
                s_max_list.append(s_max)
                
        if auc_va_list:
            results.append({
                "Method": method,
                "VA_AUC_mean": np.mean(auc_va_list),
                "VA_AUC_std": np.std(auc_va_list) if len(auc_va_list) > 1 else 0.0,
                "Obs_AUC_mean": np.mean(auc_obs_list),
                "Obs_AUC_std": np.std(auc_obs_list) if len(auc_obs_list) > 1 else 0.0,
                "s_min": np.mean(s_min_list),
                "s_max": np.mean(s_max_list)
            })

    res_df = pd.DataFrame(results)
    method_order = ["diagonal_sst_main", "data_free_sst_main", "ties", "dare", "task_arithmetic"]
    res_df["order"] = res_df["Method"].apply(lambda x: method_order.index(x) if x in method_order else 999)
    res_df = res_df.sort_values("order").drop(columns=["order"])

    latex_auc = r"""\begin{table}[H]
\centering
\caption{Observed-range Pareto AUCとEndpoint-extended Pareto AUCの比較}
\label{tab:auc_no_interpolation}
\small
\begin{tabular}{lrrrr}
\toprule
Method & Endpoint-extended AUC & Observed-range AUC & \(s_{\min}\) & \(s_{\max}\) \\
\midrule
"""
    for _, row in res_df.iterrows():
        m_name = row["Method"].replace("_main", "").replace("diagonal_sst", "SST").replace("data_free_sst", "Data-Free SST").replace("task_arithmetic", "Task Arithmetic").replace("ties", "TIES").replace("dare", "DARE")
        if m_name == "Task Arithmetic":
            continue
        latex_auc += f"{m_name} & ${row['VA_AUC_mean']:.3f} \\pm {row['VA_AUC_std']:.3f}$ & ${row['Obs_AUC_mean']:.5g} \\pm {row['Obs_AUC_std']:.5g}$ & {row['s_min']:.3f} & {row['s_max']:.3f} \\\\\n"
    
    latex_auc += r"""Task Arithmetic & - & - & - & - \\
\bottomrule
\multicolumn{5}{l}{\footnotesize \(s_{\min}\)および\(s_{\max}\)は、各seedにおける最小値・最大値を平均した値である。} \\
\multicolumn{5}{l}{\footnotesize 各AUCは、各seedでパレート前線を個別に構成して算出し、その平均を報告した。標準偏差も併記した。} \\
\multicolumn{5}{l}{\footnotesize SST、Data-Free SST、およびTIESについては、AUC算出に用いたパレート点がseed間で一致したため、丸め前の標準偏差も0であった。} \\
\multicolumn{5}{l}{\footnotesize Task Arithmeticは、支配されない点が1点のみであり、前線形状に基づくAUC比較が成立しないため、AUCを報告しない。} \\
\multicolumn{5}{l}{\footnotesize その唯一の点の\(s_{\mathrm{valid}}\)、utility、および対応する\(\alpha\)をTable~\ref{tab:task-arithmetic-single-point}に示す。} \\
\end{tabular}
\end{table}"""
    
    out_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "tab_auc_no_interpolation.tex"), "w", encoding="utf-8") as f:
        f.write(latex_auc)
    print("Saved tab_auc_no_interpolation.tex")
        
    df_ta = df_task[df_task["method"] == "task_arithmetic"].copy()
    if not df_ta.empty:
        # Find single pareto point for each seed (the one with highest utility among those with max VSR (min asr))
        ta_records = []
        for seed, df_s in df_ta.groupby("seed"):
            df_s = df_s.sort_values(by=["asr", "utility"], ascending=[True, False])
            if not df_s.empty:
                best = df_s.iloc[0]
                ta_records.append(best)
        if ta_records:
            best_ta = ta_records[0] # taking the first seed for simplicity or mean
            mean_alpha = np.mean([r["alpha"] for r in ta_records])
            mean_vsr = np.mean([1.0 - r["asr"] for r in ta_records])
            mean_util = np.mean([r["utility"] for r in ta_records])
            latex_ta = r"""\begin{table}[H]
\centering
\caption{Task Arithmeticにおける唯一の支配されない点（パレート点）の実測値}
\label{tab:task-arithmetic-single-point}
\small
\begin{tabular}{lrrr}
\toprule
Method & \(\alpha\) & Valid Safety Rate & Utility \\
\midrule
"""
            latex_ta += f"Task Arithmetic & {mean_alpha:.1f} & {mean_vsr:.3f} & {mean_util:.3f} \\\\\n"
            latex_ta += r"""\bottomrule
\end{tabular}
\end{table}"""
            with open(os.path.join(out_dir, "tab_task_arithmetic_single_point.tex"), "w", encoding="utf-8") as f:
                f.write(latex_ta)
            print("Saved tab_task_arithmetic_single_point.tex")

if __name__ == "__main__":
    main()
