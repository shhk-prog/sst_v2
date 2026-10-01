import os
import json
import glob
import numpy as np

def extract_safety_harmful_asr(data):
    if not isinstance(data, dict):
        return None
    hb_cls_asr = data.get("harmbench_cls_asr")
    if hb_cls_asr is not None:
        v = float(hb_cls_asr)
        return v * 100.0 if v <= 1.0 else v
    filt_asr = data.get("asr")
    if filt_asr is not None:
        v = float(filt_asr)
        return v * 100.0 if v <= 1.0 else v
    return None

def extract_metric_from_json(data, metric_key):
    if not isinstance(data, dict):
        return None
    if metric_key == "alpaca_eval2":
        val = data.get("length_controlled_winrate") or data.get("win_rate")
        if val is not None:
            v = float(val)
            return v * 100.0 if v <= 1.0 else v
        return None
    if metric_key in ["inst_evol_code", "inst_medalpaca"]:
        metrics = data.get("metrics", {})
        val = metrics.get("perplexity") if isinstance(metrics, dict) else None
        if val is None:
            val = data.get("perplexity")
        return float(val) if val is not None else None
    
    results = data.get("results", {})
    if not results or not isinstance(results, dict): return None
    
    if metric_key == "mmlu":
        accs = []
        for tk, tv in results.items():
            if isinstance(tv, dict) and "mmlu" in tk:
                val = tv.get("acc,none") or tv.get("acc")
                if val is not None:
                    v = float(val)
                    accs.append(v * 100.0 if v <= 1.0 else v)
        return float(np.mean(accs)) if accs else None
    
    target_task_metrics = None
    for tk, tv in results.items():
        if isinstance(tv, dict) and (metric_key in tk or (metric_key=="medqa_4options" and "medqa" in tk) or (metric_key=="minerva_math500" and "math" in tk)):
            target_task_metrics = tv
            break
    if not target_task_metrics and len(results) == 1:
        target_task_metrics = list(results.values())[0]
    
    if not isinstance(target_task_metrics, dict): return None
    priority_keys = ["pass@1", "pass_at_1,none", "exact_match,flexible-extract", "math_verify,none", "prompt_level_strict_acc,none", "acc,none", "acc", "exact_match,strict-match"]
    for k in priority_keys:
        if k in target_task_metrics:
            val = target_task_metrics[k]
            if val is not None:
                v = float(val)
                return v * 100.0 if v <= 1.0 else v
    return None

base_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/base"
models = ["SafetyFT", "WizardMath", "WizardCoder", "MedAlpaca"]

base_scores = {m: {"Safety": [], "Math": [], "Code": [], "Medical": [], "General": []} for m in models}

for filepath in glob.glob(os.path.join(base_dir, "*.json")):
    filename = os.path.basename(filepath)
    model = None
    for m in models:
        if m in filename:
            model = m
            break
    if not model: continue
    
    try:
        data = json.load(open(filepath))
    except Exception:
        continue
    
    # Safety
    if any(k in filename for k in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]):
        s = extract_safety_harmful_asr(data)
        if s is not None: base_scores[model]["Safety"].append(s)
    
    # Math
    if any(k in filename for k in ["gsm8k", "minerva_math500"]):
        s = extract_metric_from_json(data, "gsm8k" if "gsm8k" in filename else "minerva_math500")
        if s is not None: base_scores[model]["Math"].append(s)
        
    # Code
    if any(k in filename for k in ["humaneval", "mbpp"]):
        s = extract_metric_from_json(data, "humaneval" if "humaneval" in filename else "mbpp")
        if s is not None: base_scores[model]["Code"].append(s)
        
    # Medical
    if any(k in filename for k in ["pubmedqa", "medqa_4options"]):
        s = extract_metric_from_json(data, "pubmedqa" if "pubmedqa" in filename else "medqa_4options")
        if s is not None: base_scores[model]["Medical"].append(s)
        
    # General (MMLU, IFEval, AlpacaEval2)
    if any(k in filename for k in ["mmlu", "ifeval", "alpaca_eval2"]):
        key = "mmlu" if "mmlu" in filename else "ifeval" if "ifeval" in filename else "alpaca_eval2"
        s = extract_metric_from_json(data, key)
        if s is not None: base_scores[model]["General"].append(s)

# Format base rows
base_rows = []
for model in models:
    s_ave = np.mean(base_scores[model]["Safety"]) if base_scores[model]["Safety"] else 0.0
    m_ave = np.mean(base_scores[model]["Math"]) if base_scores[model]["Math"] else 0.0
    c_ave = np.mean(base_scores[model]["Code"]) if base_scores[model]["Code"] else 0.0
    med_ave = np.mean(base_scores[model]["Medical"]) if base_scores[model]["Medical"] else 0.0
    g_ave = np.mean(base_scores[model]["General"]) if base_scores[model]["General"] else 0.0
    base_rows.append(f"| {model} (Base) | - | - | {s_ave:.2f} ± 0.00% | {m_ave:.2f} ± 0.00% | {c_ave:.2f} ± 0.00% | {med_ave:.2f} ± 0.00% | {g_ave:.2f} ± 0.00% |")

# Extract main rows from existing table
main_rows = []
with open("/mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/paper_evaluation_summary_tables.md", "r") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "diagonal_sst_main" in line and "safety+" in line and "0.60" in line:
            parts = line.strip().split("|")
            if len(parts) >= 9:
                pattern = parts[1].strip()
                method = parts[2].strip()
                main_rows.append(f"| {method} ({pattern}) | 0.60 | 0.20 | {parts[4].strip()} | {parts[5].strip()} | {parts[6].strip()} | {parts[7].strip()} | {parts[8].strip()} |")
        elif "data_free_sst_main" in line and "safety+" in line and "0.60" in line:
            parts = line.strip().split("|")
            if len(parts) >= 9:
                pattern = parts[1].strip()
                method = parts[2].strip()
                main_rows.append(f"| {method} ({pattern}) | 0.60 | 0.20 | {parts[4].strip()} | {parts[5].strip()} | {parts[6].strip()} | {parts[7].strip()} | {parts[8].strip()} |")
        elif "task_arithmetic" in line and "safety+" in line and "0.60" in line:
            parts = line.strip().split("|")
            if len(parts) >= 9:
                pattern = parts[1].strip()
                method = parts[2].strip()
                main_rows.append(f"| {method} ({pattern}) | 0.60 | - | {parts[4].strip()} | {parts[5].strip()} | {parts[6].strip()} | {parts[7].strip()} | {parts[8].strip()} |")
        elif "ties" in line and "safety+" in line and "0.60" in line:
            parts = line.strip().split("|")
            if len(parts) >= 9:
                pattern = parts[1].strip()
                method = parts[2].strip()
                main_rows.append(f"| {method} ({pattern}) | 0.60 | - | {parts[4].strip()} | {parts[5].strip()} | {parts[6].strip()} | {parts[7].strip()} | {parts[8].strip()} |")

table_md = """**Table 2: ベースモデルと主要マージ手法の 5大ドメイン平均性能比較**

| Method (Model / Pattern) | Alpha (α) | Top-k (k) | Safety Ave (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General Ave (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
""" + "\n".join(base_rows) + "\n| --- | --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(main_rows) + "\n"

output_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/base_vs_main_summary.md"
with open(output_path, "w") as f:
    f.write(table_md)
print(f"Success! Saved table to {output_path}")