#!/usr/bin/env python3
import os
import glob
import json
import numpy as np
import pandas as pd
from collections import defaultdict

PATTERNS = ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"]
SEEDS = [42, 43, 44]
METHODS = [
    "diagonal_sst_main", "data_free_sst_main", "ties", "dare", "della",
    "task_arithmetic", "safemerge", "led_merging", "matena_fisher", "mergealign"
]
SINGLE_RUN_METHODS = {"safemerge", "led_merging", "matena_fisher", "mergealign", "fisher_weighted"}

DISPLAY_HEADERS_MAIN = [
    "Pattern", "Method", "Alpha",
    "Safety Ave [Harmful Content] (ASR↓ %)",
    "Safety Ave [Original ASR] (ASR↓ %)",
    "Safety Ave [Conditional ASR] (ASR↓ %)",
    "Valid Response Rate (%)",
    "Valid Safety Rate (%)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
    "EvolCode (PPL↓)", "MedAlpaca (PPL↓)"
]

DISPLAY_HEADERS_MAIN_SAFETY = [
    "Pattern", "Method",
    "Safety Ave [Original ASR] (ASR↓ %)",
    "Safety Ave [Conditional ASR] (ASR↓ %)",
    "Valid Response Rate (%)",
    "Valid Safety Rate (%)"
]

DISPLAY_HEADERS_MAIN_UTILITY = [
    "Pattern", "Method",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)"
]

DISPLAY_HEADERS_PRELIM = [
    "Pattern", "Method", "Alpha",
    "TrustLLM Raw ASR (%)", r"Gibberish Ratio (\(\downarrow\), %)", r"BeaverTails Utility Score (\(\uparrow\), %)"
]

DISPLAY_HEADERS_PRELIM_SIMPLE = [
    "Pattern", "Method", 
    "TrustLLM Raw ASR (%)", r"Gibberish Ratio (\(\downarrow\), %)", r"BeaverTails Utility Score (\(\uparrow\), %)"
]

DISPLAY_HEADERS_MAIN_SIMPLE = [
    "Pattern", "Method", 
    "Safety Ave [Harmful Content] (ASR↓ %)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)"
]


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def extract_safety_harmful_asr(data, valid_only=False):
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return {"harmful_content": None, "original_asr": None, "conditional_asr": None, "vrr": None, "vsr": None}

    conditional_asr = None
    original_asr = None
    vrr = None
    vsr = None

    results = data.get("results", [])
    if isinstance(results, list) and results:
        total = len(results)
        gibberish_n = sum(1 for r in results if r.get("is_gibberish", False))
        valid_n = total - gibberish_n
        vrr = (valid_n / total * 100.0) if total > 0 else None

        harmful_valid = sum(
            1 for r in results
            if not r.get("is_gibberish", False) and (
                r.get("harmbench_cls_output") == "Yes"
                or (r.get("asr") is not None and float(r.get("asr", 0)) > 0.5)
            )
        )
        conditional_asr = (harmful_valid / valid_n * 100.0) if valid_n > 0 else None
        original_asr = (harmful_valid / total * 100.0) if total > 0 else None
        vsr = ((valid_n - harmful_valid) / total * 100.0) if total > 0 else None
    else:
        # Fallback for old formats without item-level results
        c = data.get("asr") or data.get("harmbench_cls_asr")
        gib = data.get("gibberish_ratio", 0.0)
        if gib is not None:
            g = float(gib)
            v_ratio = 1.0 - (g / 100.0 if g > 1.0 else g)
            vrr = v_ratio * 100.0
        if c is not None:
            cv = float(c)
            conditional_asr = cv * 100.0 if cv <= 1.0 else cv
        if vrr is not None and conditional_asr is not None:
            original_asr = vrr / 100.0 * conditional_asr
            vsr = vrr * (1.0 - conditional_asr / 100.0)

    harmful_content = original_asr if original_asr is not None else None
    if valid_only and conditional_asr is not None:
        harmful_content = conditional_asr

    return {
        "harmful_content": harmful_content,
        "original_asr": original_asr,
        "conditional_asr": conditional_asr,
        "vrr": vrr,
        "vsr": vsr
    }

def extract_metric_from_json(data, metric_key):
    if not isinstance(data, dict) or data.get("status") == "failed" or data.get("mockup") is True:
        return None
    if metric_key == "alpaca_eval2":
        val = data.get("length_controlled_winrate") or data.get("win_rate")
        if val is not None and isinstance(val, (int, float)):
            v = float(val)
            return v * 100.0 if v <= 1.0 else v
        return None
    if metric_key in ["inst_evol_code", "inst_medalpaca"]:
        metrics = data.get("metrics", {})
        val = metrics.get("perplexity") if isinstance(metrics, dict) else data.get("perplexity")
        if val is not None and isinstance(val, (int, float)):
            return float(val)
        return None
    results = data.get("results", {})
    if not results or not isinstance(results, dict):
        return None
    if metric_key == "mmlu":
        mmlu_accs = []
        for task_name, task_metrics in results.items():
            if isinstance(task_metrics, dict) and ("mmlu" in task_name or "mmlu" in data.get("configs", {})):
                val = task_metrics.get("acc,none") or task_metrics.get("acc")
                if val is not None and isinstance(val, (int, float)):
                    v = float(val)
                    mmlu_accs.append(v * 100.0 if v <= 1.0 else v)
        return float(np.mean(mmlu_accs)) if mmlu_accs else None
    
    target_task_metrics = None
    for task_name, task_metrics in results.items():
        if isinstance(task_metrics, dict):
            if metric_key in task_name or (metric_key == "medqa_4options" and "medqa" in task_name) or (metric_key == "minerva_math500" and "math" in task_name):
                target_task_metrics = task_metrics
                break
    if target_task_metrics is None and len(results) == 1:
        target_task_metrics = list(results.values())[0]
    if not isinstance(target_task_metrics, dict):
        return None
    priority_keys = ["pass@1", "pass_at_1,none", "exact_match,flexible-extract", "math_verify,none", "prompt_level_strict_acc,none", "acc,none", "acc", "exact_match,strict-match"]
    for k in priority_keys:
        if k in target_task_metrics:
            val = target_task_metrics[k]
            if val is not None and isinstance(val, (int, float)):
                v = float(val)
                return v * 100.0 if v <= 1.0 else v
    return None

def parse_filename_info(filename):
    parts = filename.split("_")
    seed = None
    for part in parts:
        if part.startswith("seed") and part[4:].isdigit():
            seed = int(part[4:])
            break
    alpha = None
    for part in parts:
        if part.startswith("alpha"):
            try: alpha = float(part.replace("alpha", ""))
            except: pass
            
    pattern = None
    for p in sorted(PATTERNS, key=len, reverse=True):
        if p in filename:
            pattern = p
            break
            
    metric_key = None
    metric_candidates = [
        "harmbench", "jailbreakbench", "strongreject", "wildjailbreak",
        "gsm8k", "minerva_math500", "humaneval", "mbpp", "pubmedqa", "medqa_4options", "mmlu", "ifeval", "alpaca_eval2", "inst_evol_code", "inst_medalpaca",
        "utility_math", "utility_code", "utility_medical", "utility_general"
    ]
    for k in metric_candidates:
        if k in filename or (k=="inst_evol_code" and "evol_code" in filename) or (k=="inst_medalpaca" and "medalpaca" in filename) or (k=="medqa_4options" and "medqa" in filename):
            metric_key = k
            break
            
    is_base = "base" in filename.lower()
    method = None
    if is_base:
        base_name_found = "Base Model"
        for bn in ["WizardMath", "WizardCoder", "MedAlpaca", "SafetyFT", "Llama3"]:
            if bn.lower() in filename.lower():
                base_name_found = bn
                break
        method = f"Base ({base_name_found})"
        pattern = f"Base ({base_name_found})"
        alpha = "N/A"
    else:
        for m in METHODS:
            if m in filename:
                method = m
                break
        if method in SINGLE_RUN_METHODS and alpha is None:
            alpha = "N/A"
            
    return {"method": method, "pattern": pattern, "alpha": alpha, "seed": seed, "metric_key": metric_key, "is_base": is_base}

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="", **kwargs):
        total = len(iterable) if hasattr(iterable, "__len__") else None
        print(f"Starting {desc} (Total: {total})...")
        for i, item in enumerate(iterable):
            if total and (i + 1) % max(1, total // 10) == 0:
                print(f"[{desc}] Progress: {i + 1}/{total} ({(i + 1) / total * 100:.1f}%)")
            yield item
        print(f"Finished {desc}.")

def collect_data(results_dir, env_name):
    print(f"\n[1/3] Collecting data from {results_dir} ({env_name})...")
    main_store = defaultdict(lambda: defaultdict(dict))
    prelim_store = defaultdict(lambda: defaultdict(dict))
    json_files = glob.glob(os.path.join(results_dir, "**", "*.json"), recursive=True)
    print(f"Found {len(json_files)} json files in {results_dir}")
    
    for filepath in tqdm(json_files, desc=f"Parsing {env_name} JSONs"):
        filename = os.path.basename(filepath)
        if "summary" in filename or filename.startswith("."):
            continue
            
        content = load_json(filepath)
        if not content: continue

        # Check if preliminary
        if "trustllm" in filename.lower() or "beavertails" in filename.lower():
            info = parse_filename_info(filename)
            seed = info["seed"] or 42
            method = info["method"] or "Base"
            pattern = info["pattern"] or "Base"
            alpha = info["alpha"]
            key = (env_name, pattern, method, alpha)
            
            if "trustllm" in filename.lower():
                asr = content.get("asr", content.get("original_asr"))
                gib_ratio = content.get("gibberish_ratio")
                if asr is not None:
                    prelim_store[key]["trustllm_asr"] = prelim_store[key].get("trustllm_asr", {})
                    prelim_store[key]["trustllm_asr"][seed] = float(asr) * 100.0 if float(asr) <= 1.0 else float(asr)
                if gib_ratio is not None:
                    prelim_store[key]["gibberish_ratio"] = prelim_store[key].get("gibberish_ratio", {})
                    prelim_store[key]["gibberish_ratio"][seed] = float(gib_ratio)
            elif "beavertails" in filename.lower():
                utility_score = content.get("similarity", content.get("exact_match", content.get("accuracy")))
                if utility_score is not None:
                    prelim_store[key]["beavertails_utility"] = prelim_store[key].get("beavertails_utility", {})
                    prelim_store[key]["beavertails_utility"][seed] = float(utility_score) * 100.0 if float(utility_score) <= 1.0 else float(utility_score)
            continue
            
        # Main experiments
        info = parse_filename_info(filename)
        if not (info["method"] and info["pattern"] and info["metric_key"]):
            continue
        key = (env_name, info["seed"], info["pattern"], info["method"], info["alpha"])
        
        m_key = info["metric_key"]
        if m_key in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]:
            s_val = extract_safety_harmful_asr(content)
            if s_val is not None: main_store[key][m_key] = s_val
        elif m_key in ["inst_evol_code", "inst_medalpaca"]:
            ppl_val = extract_metric_from_json(content, m_key)
            if ppl_val is not None: main_store[key][m_key] = ppl_val
        elif m_key == "utility_math":
            for sub_k in ["gsm8k", "minerva_math500"]:
                score = extract_metric_from_json(content, sub_k)
                if score is not None: main_store[key][sub_k] = score
        elif m_key == "utility_code":
            for sub_k in ["humaneval", "mbpp"]:
                score = extract_metric_from_json(content, sub_k)
                if score is not None: main_store[key][sub_k] = score
        elif m_key == "utility_medical":
            for sub_k in ["pubmedqa", "medqa_4options"]:
                score = extract_metric_from_json(content, sub_k)
                if score is not None: main_store[key][sub_k] = score
        elif m_key == "utility_general":
            for sub_k in ["mmlu", "ifeval"]:
                score = extract_metric_from_json(content, sub_k)
                if score is not None: main_store[key][sub_k] = score
        else:
            score = extract_metric_from_json(content, m_key)
            if score is not None: main_store[key][m_key] = score

    print(f"Done collecting {env_name}. Parsed main keys: {len(main_store)}, prelim keys: {len(prelim_store)}")
    return main_store, prelim_store

def get_mean_std(vals):
    valid_vals = [v for v in vals if v is not None and isinstance(v, (int, float)) and not np.isnan(v)]
    if not valid_vals: return None
    mean = float(np.mean(valid_vals))
    std = float(np.std(valid_vals, ddof=1)) if len(valid_vals) > 1 else 0.0
    return (mean, std)

def format_val(val, is_ppl=False):
    if val is None or val == "-": return "-"
    if isinstance(val, tuple) and len(val) == 2:
        mean, std = val
        if mean is None or np.isnan(mean): return "-"
        unit = "" if is_ppl else "%"
        return f"{mean:.2f} ± {std:.2f}{unit}"
    elif isinstance(val, (int, float)):
        if np.isnan(val): return "-"
        unit = "" if is_ppl else "%"
        return f"{val:.2f}{unit}"
    return str(val)

def aggregate_main(main_store):
    config_groups = defaultdict(list)
    for (env, seed, pattern, method, alpha), metric_values in main_store.items():
        config_groups[(env, pattern, method, alpha)].append((seed, metric_values))
        
    summary_rows = []
    seed_detail_rows = []
    
    for (env, pattern, method, alpha), list_of_seed_metrics in config_groups.items():
        seed_rows = []
        alpha_str = alpha if alpha == "N/A" else (f"{alpha:.2f}" if isinstance(alpha, (int, float)) else str(alpha))
        
        for seed, m_values in list_of_seed_metrics:
            s_dicts = [m_values.get(m) for m in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"] if isinstance(m_values.get(m), dict)]
            s_vals = [m_values.get(m) for m in ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"] if isinstance(m_values.get(m), (int, float))]
            
            s_harmful = [d.get("harmful_content") for d in s_dicts if d.get("harmful_content") is not None] + s_vals
            s_orig = [d.get("original_asr") for d in s_dicts if d.get("original_asr") is not None] + s_vals
            s_cond = [d.get("conditional_asr") for d in s_dicts if d.get("conditional_asr") is not None] + s_vals
            s_vrr = [d.get("vrr") for d in s_dicts if d.get("vrr") is not None]
            s_vsr = [d.get("vsr") for d in s_dicts if d.get("vsr") is not None]

            m_vals = [m_values.get(m) for m in ["gsm8k", "minerva_math500"] if isinstance(m_values.get(m), (int, float))]
            c_vals = [m_values.get(m) for m in ["humaneval", "mbpp"] if isinstance(m_values.get(m), (int, float))]
            med_vals = [m_values.get(m) for m in ["pubmedqa", "medqa_4options"] if isinstance(m_values.get(m), (int, float))]
            g_vals = [m_values.get(m) for m in ["mmlu", "ifeval", "alpaca_eval2"] if isinstance(m_values.get(m), (int, float))]
            
            s_score = float(np.mean(s_harmful)) if s_harmful else None
            s_orig_score = float(np.mean(s_orig)) if s_orig else None
            s_cond_score = float(np.mean(s_cond)) if s_cond else None
            s_vrr_score = float(np.mean(s_vrr)) if s_vrr else None
            s_vsr_score = float(np.mean(s_vsr)) if s_vsr else None

            m_score = float(np.mean(m_vals)) if m_vals else None
            c_score = float(np.mean(c_vals)) if c_vals else None
            med_score = float(np.mean(med_vals)) if med_vals else None
            g_score = float(np.mean(g_vals)) if g_vals else None
            evol_ppl = m_values.get("inst_evol_code")
            med_ppl = m_values.get("inst_medalpaca")
            
            seed_data = {
                "Safety": s_score,
                "SafetyOrig": s_orig_score,
                "SafetyCond": s_cond_score,
                "SafetyVRR": s_vrr_score,
                "SafetyVSR": s_vsr_score,
                "Math": m_score,
                "Code": c_score,
                "Medical": med_score,
                "General": g_score,
                "EvolCodePPL": float(evol_ppl) if isinstance(evol_ppl, (int, float)) else None,
                "MedAlpacaPPL": float(med_ppl) if isinstance(med_ppl, (int, float)) else None,
            }
            seed_rows.append(seed_data)
            
            # Record per-seed detail row
            seed_detail_rows.append({
                "Env": env,
                "Pattern": pattern,
                "Method": method,
                "Alpha": alpha_str,
                "Seed": seed,
                "Safety Ave [Harmful Content] (ASR↓ %)": s_score,
                "Safety Ave [Original ASR] (ASR↓ %)": s_orig_score,
                "Safety Ave [Conditional ASR] (ASR↓ %)": s_cond_score,
                "Valid Response Rate (%)": s_vrr_score,
                "Valid Safety Rate (%)": s_vsr_score,
                "Math Ave (%)": m_score,
                "Code Ave (%)": c_score,
                "Medical Ave (%)": med_score,
                "General/Inst Ave (%)": g_score,
                "EvolCode (PPL↓)": float(evol_ppl) if isinstance(evol_ppl, (int, float)) else None,
                "MedAlpaca (PPL↓)": float(med_ppl) if isinstance(med_ppl, (int, float)) else None,
            })
            
        row_dict = {
            "Env": env,
            "Pattern": pattern,
            "Method": method,
            "Alpha": alpha_str
        }
        row_dict["Safety Ave [Harmful Content] (ASR↓ %)"] = get_mean_std([sr["Safety"] for sr in seed_rows if sr["Safety"] is not None])
        row_dict["Safety Ave [Original ASR] (ASR↓ %)"] = get_mean_std([sr["SafetyOrig"] for sr in seed_rows if sr["SafetyOrig"] is not None])
        row_dict["Safety Ave [Conditional ASR] (ASR↓ %)"] = get_mean_std([sr["SafetyCond"] for sr in seed_rows if sr["SafetyCond"] is not None])
        row_dict["Valid Response Rate (%)"] = get_mean_std([sr["SafetyVRR"] for sr in seed_rows if sr["SafetyVRR"] is not None])
        row_dict["Valid Safety Rate (%)"] = get_mean_std([sr["SafetyVSR"] for sr in seed_rows if sr["SafetyVSR"] is not None])
        row_dict["Math Ave (%)"] = get_mean_std([sr["Math"] for sr in seed_rows if sr["Math"] is not None])
        row_dict["Code Ave (%)"] = get_mean_std([sr["Code"] for sr in seed_rows if sr["Code"] is not None])
        row_dict["Medical Ave (%)"] = get_mean_std([sr["Medical"] for sr in seed_rows if sr["Medical"] is not None])
        row_dict["General/Inst Ave (%)"] = get_mean_std([sr["General"] for sr in seed_rows if sr["General"] is not None])
        row_dict["EvolCode (PPL↓)"] = get_mean_std([sr["EvolCodePPL"] for sr in seed_rows if sr["EvolCodePPL"] is not None])
        row_dict["MedAlpaca (PPL↓)"] = get_mean_std([sr["MedAlpacaPPL"] for sr in seed_rows if sr["MedAlpacaPPL"] is not None])
        summary_rows.append(row_dict)
        
    return pd.DataFrame(summary_rows), pd.DataFrame(seed_detail_rows)

def aggregate_prelim(prelim_store):
    summary_rows = []
    seed_detail_rows = []
    
    for (env, pattern, method, alpha), entry in prelim_store.items():
        alpha_str = alpha if alpha == "N/A" else (f"{alpha:.2f}" if isinstance(alpha, (int, float)) else str(alpha))
        trust_map = entry.get("trustllm_asr", {})
        gib_map = entry.get("gibberish_ratio", {})
        beaver_map = entry.get("beavertails_utility", {})
        
        trust_vals = [trust_map.get(s) for s in SEEDS]
        gib_vals = [gib_map.get(s) for s in SEEDS]
        beaver_vals = [beaver_map.get(s) for s in SEEDS]
        
        for s in SEEDS:
            t_v = trust_map.get(s)
            g_v = gib_map.get(s)
            b_v = beaver_map.get(s)
            if t_v is not None or g_v is not None or b_v is not None:
                seed_detail_rows.append({
                    "Env": env,
                    "Pattern": pattern,
                    "Method": method,
                    "Alpha": alpha_str,
                    "Seed": s,
                    "TrustLLM Raw ASR (%)": t_v,
                    r"Gibberish Ratio (\(\downarrow\), %)": g_v,
                    r"BeaverTails Utility Score (\(\uparrow\), %)": b_v
                })
        
        row_dict = {
            "Env": env,
            "Pattern": pattern,
            "Method": method,
            "Alpha": alpha_str,
            "TrustLLM Raw ASR (%)": get_mean_std(trust_vals),
            r"Gibberish Ratio (\(\downarrow\), %)": get_mean_std(gib_vals),
            r"BeaverTails Utility Score (\(\uparrow\), %)": get_mean_std(beaver_vals)
        }
        summary_rows.append(row_dict)
        
    return pd.DataFrame(summary_rows), pd.DataFrame(seed_detail_rows)

def format_markdown_table(df, title, headers):
    if df.empty:
        return f"#### {title}\n*No data available.*\n\n"
    lines = [f"#### {title}\n"]
    cols = [c for c in headers if c in df.columns]
    lines.append("| " + " | ".join(cols) + " |")
    align_row = [":---" if c in ["Pattern", "Method", "Alpha", "Seed"] else ":---:" for c in cols]
    lines.append("| " + " | ".join(align_row) + " |")
    
    sort_cols = [c for c in ["Pattern", "Method", "Alpha", "Seed", "Env"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols)
        
    for _, row in df.iterrows():
        row_str = [str(row[c]) if c in ["Pattern", "Method", "Alpha", "Seed"] else format_val(row[c], is_ppl=("PPL" in c)) for c in cols]
        lines.append("| " + " | ".join(row_str) + " |")
    return "\n".join(lines) + "\n\n"

DISPLAY_HEADERS_MAIN_SEED = [
    "Pattern", "Method", "Alpha", "Seed",
    "Safety Ave [Harmful Content] (ASR↓ %)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
    "EvolCode (PPL↓)", "MedAlpaca (PPL↓)"
]

DISPLAY_HEADERS_PRELIM_SEED = [
    "Pattern", "Method", "Alpha", "Seed",
    "TrustLLM Raw ASR (%)", r"Gibberish Ratio (\(\downarrow\), %)", r"BeaverTails Utility Score (\(\uparrow\), %)"
]

def format_latex_val(val, is_ppl=False):
    if val is None or val == "-" or val == "---": return "---"
    if isinstance(val, tuple) and len(val) == 2:
        mean, std = val
        if mean is None or np.isnan(mean): return "---"
        return f"{mean:.2f} $\\pm$ {std:.2f}"
    elif isinstance(val, (int, float)):
        if np.isnan(val): return "---"
        return f"{val:.2f}"
    return str(val).replace("_", "\\_")

def format_latex_table(df, title, headers, label="tab:result"):
    if df.empty:
        return f"% --- {title} (No data) ---\n\n"
    
    # キャプション用に特殊文字をエスケープ
    safe_title = title.replace("_", "\\_").replace("%", "\\%")
        
    cols = [c for c in headers if c in df.columns]
    
    col_spec_lines = ["{"]
    for c in cols:
        if c == 'Method':
            col_spec_lines.append(">{\\raggedright\\arraybackslash}p{2.25cm}")
        elif c in ['Alpha', 'Seed', 'Pattern', 'Env']:
            col_spec_lines.append(">{\\centering\\arraybackslash}p{0.90cm}")
        else:
            col_spec_lines.append(">{\\centering\\arraybackslash}X")
    col_spec_lines.append("}")
    col_spec = "\n".join(col_spec_lines)
    
    latex_lines = [
        f"% --- {title} ---",
        "\\begin{table}[htbp]",
        f"\\caption{{{safe_title}}}",
        f"\\label{{{label}}}",
        "\\centering",
        "\\small",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{1.06}",
        f"\\begin{{tabularx}}{{\\textwidth}}{col_spec}",
        "\\toprule"
    ]
    
    # Header row
    clean_headers = []
    for c in cols:
        ch = c.replace("_", "\\_").replace("%", "\\%").replace("↑", "$\\uparrow$").replace("↓", "$\\downarrow$")
        clean_headers.append(f"\\textbf{{{ch}}}")
    latex_lines.append(" & ".join(clean_headers) + " \\\\")
    latex_lines.append("\\midrule")
    
    sort_cols = [c for c in ["Pattern", "Method", "Alpha", "Seed", "Env"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols)
        
    # Multirow processing for Method
    method_counts = {}
    if "Method" in df.columns:
        # Count consecutive identical methods for multirow
        current_method = None
        current_count = 0
        block_idx = 0
        for idx, row in df.iterrows():
            m = row["Method"]
            if m != current_method:
                if current_method is not None:
                    method_counts[block_idx] = current_count
                current_method = m
                current_count = 1
                block_idx = idx
            else:
                current_count += 1
        if current_method is not None:
            method_counts[block_idx] = current_count
            
    current_method = None
    first_in_block = False
    
    for idx, row in df.iterrows():
        row_cells = []
        is_first_of_method = False
        
        if "Method" in df.columns:
            m = row["Method"]
            if m != current_method:
                if current_method is not None:
                    latex_lines.append("\\midrule")
                current_method = m
                is_first_of_method = True
                
        for c in cols:
            val = row[c]
            if c in ["Pattern", "Alpha", "Seed"]:
                row_cells.append(str(val).replace("_", "\\_"))
            elif c == "Method":
                if is_first_of_method:
                    count = method_counts.get(idx, 1)
                    escaped_m = str(val).replace("_", "\\_")
                    if count > 1:
                        row_cells.append(f"\\multirow{{{count}}}{{*}}{{{escaped_m}}}")
                    else:
                        row_cells.append(escaped_m)
                else:
                    row_cells.append("")
            else:
                row_cells.append(format_latex_val(val, is_ppl=("PPL" in c)))
        latex_lines.append(" & ".join(row_cells) + " \\\\")
        
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabularx}",
        "\\end{table}\n\n"
    ])
    return "\n".join(latex_lines)

def generate_documents(df_main_summary, df_main_seeds, df_prelim_summary, df_prelim_seeds, output_prefix="flmsec_hyo", title_suffix=""):
    out_lines = [
        f"# SST-Merge実験結果一覧 ({output_prefix}.md){title_suffix}",
        "本ファイルは自動生成された実験結果ドキュメントです。",
        "各実験設定ごとに **「平均±標準偏差 (Mean ± Std) の集計表」** と **「シード別 (Seed 42, 43, 44) の詳細結果比較表」** をセットで上下に掲載しています。",
        "ディレクトリ `results/normal` および `results/vllm` の両方からデータを収集・併記しています。" if not title_suffix else f"この表は {title_suffix.strip()} に絞った結果です。",
        ""
    ]
    
    latex_lines = [
        "% ==========================================================================",
        f"% SST-Merge LaTeX表一覧 ({output_prefix}_latex.md / .tex)",
        "% 本ファイルは generate_flmsec_hyo.py から自動生成された LaTeX 形式の実験結果表です。",
        "% ==========================================================================\n"
    ]
    
    # 0. Simplified Tables for Main Text
    out_lines.append("## 0. 論文メインテキスト用 簡易まとめ表")
    out_lines.append("`flmsec.md` のメインテキストに直接貼り付けられるよう、不要な列（Env, Alpha, Seed等）を省き、主要な設定（Alpha=0.6またはN/A）のみを抽出した表です。ベースモデルのスコアも参考として含めています。\n")
    latex_lines.append("% --------------------------------------------------------------------------")
    latex_lines.append("% 0. 論文メインテキスト用 簡易まとめ表 (Simplified Tables for Main Text)")
    latex_lines.append("% --------------------------------------------------------------------------\n")

    if not df_prelim_summary.empty:
        df_prelim_base = df_prelim_summary[df_prelim_summary["Method"].astype(str).str.startswith("Base")]
        df_prelim_target = df_prelim_summary[~df_prelim_summary["Method"].astype(str).str.startswith("Base")]
        df_prelim_simple = df_prelim_target[df_prelim_target["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" if isinstance(x, str) else False)]
        df_prelim_simple_combined = pd.concat([df_prelim_base, df_prelim_simple])
        
        out_lines.append("### 予備実験 簡易版\n")
        out_lines.append(format_markdown_table(df_prelim_simple_combined, f"【簡易版】 予備実験 (Alpha=0.6 / N/A){title_suffix}", DISPLAY_HEADERS_PRELIM_SIMPLE))
        latex_lines.append(format_latex_table(df_prelim_simple_combined, f"【簡易版】 予備実験 (Alpha=0.6 / N/A){title_suffix}", DISPLAY_HEADERS_PRELIM_SIMPLE, label="tab:simple_prelim"))

    if not df_main_summary.empty:
        df_main_base = df_main_summary[df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_main_nobase = df_main_summary[~df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_main_simple = df_main_nobase[df_main_nobase["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" if isinstance(x, str) else False)]
        df_main_simple_combined = pd.concat([df_main_base, df_main_simple])
        
        out_lines.append("### メイン実験 簡易版\n")
        out_lines.append(format_markdown_table(df_main_simple_combined, f"【簡易版】 メイン実験 (Alpha=0.6 / N/A){title_suffix}", DISPLAY_HEADERS_MAIN_SIMPLE))
        latex_lines.append(format_latex_table(df_main_simple_combined, f"【簡易版】 メイン実験 (Alpha=0.6 / N/A){title_suffix}", DISPLAY_HEADERS_MAIN_SIMPLE, label="tab:simple_main"))

    
    # 1. Preliminary Experiments
    out_lines.append("## 1. 予備実験 (TrustLLM / BeaverTails)")
    out_lines.append("各マージ手法のベースラインとしての安全性（TrustLLM ASR / Gibberish）と有用性（BeaverTails Accuracy）の比較。\n")
    latex_lines.append("% --------------------------------------------------------------------------")
    latex_lines.append("% 1. 予備実験 (Preliminary Experiments)")
    latex_lines.append("% --------------------------------------------------------------------------\n")
    
    if not df_prelim_summary.empty:
        df_prelim_target = df_prelim_summary[~df_prelim_summary["Method"].astype(str).str.startswith("Base")]
        df_prelim_seeds_target = df_prelim_seeds[~df_prelim_seeds["Method"].astype(str).str.startswith("Base")]
        
        for pattern in df_prelim_target["Pattern"].unique():
            out_lines.append(f"### 予備実験: Pattern = {pattern}\n")
            df_pat = df_prelim_target[df_prelim_target["Pattern"] == pattern]
            out_lines.append(format_markdown_table(df_pat, f"【集計】 予備実験 (Mean ± Std) - {pattern}", DISPLAY_HEADERS_PRELIM))
            
            clean_pat = pattern.replace('+', '_')
            latex_lines.append(format_latex_table(df_pat, f"予備実験 集計 (Mean \\pm Std) - Pattern: {pattern}", DISPLAY_HEADERS_PRELIM, label=f"tab:prelim_{clean_pat}"))
            
            df_pat_seeds = df_prelim_seeds_target[df_prelim_seeds_target["Pattern"] == pattern]
            if not df_pat_seeds.empty:
                for method in df_pat_seeds["Method"].unique():
                    df_m_seeds = df_pat_seeds[df_pat_seeds["Method"] == method]
                    if not df_m_seeds.empty:
                        clean_m = str(method).replace('_', '')
                        out_lines.append(format_markdown_table(df_m_seeds, f"【シード別詳細】 予備実験 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_PRELIM_SEED))
                        latex_lines.append(format_latex_table(df_m_seeds, f"予備実験 シード別詳細 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_PRELIM_SEED, label=f"tab:prelim_seeds_{clean_m}_{clean_pat}"))
            out_lines.append("---\n")
    else:
        out_lines.append("*No preliminary data found.*\n")
        
    # 2. Main Experiments (Alpha = 0.6)
    out_lines.append("## 2. メイン実験 (Alpha=0.6 / 単一実行手法)")
    out_lines.append("広範なベンチマークにおける各手法の安全性(ASR↓)と有用性(Accuracy/WinRate↑)の比較表。\n")
    latex_lines.append("% --------------------------------------------------------------------------")
    latex_lines.append("% 2. メイン実験 (Main Experiments)")
    latex_lines.append("% --------------------------------------------------------------------------\n")
    
    if not df_main_summary.empty:
        df_main_base = df_main_summary[df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_main_nobase = df_main_summary[~df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_target = df_main_nobase[df_main_nobase["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" or x == "1.00" if isinstance(x, str) else False)]
        df_main_combined = pd.concat([df_main_base, df_target])
        
        # Multi-domain table filtering
        df_multi = df_main_combined[df_main_combined["Pattern"] == "safety+math+code+medical"].copy()
        if not df_multi.empty:
            df_multi["Note"] = ""
            df_multi.loc[df_multi["Method"] != "Base", "Note"] = "Utility degradation observed"

        df_main_combined_filtered = df_main_combined[df_main_combined["Pattern"] != "safety+math+code+medical"]

        # Safety Table
        out_lines.append("### メイン実験: Safety\n")
        out_lines.append(format_markdown_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY))
        latex_lines.append(format_latex_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY, label="tab:evaluation_main_alpha=0.6_safety"))
        
        # Utility Table
        out_lines.append("### メイン実験: Utility\n")
        out_lines.append(format_markdown_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY))
        latex_lines.append(format_latex_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY, label="tab:evaluation_main_alpha=0.6_utility"))

        if not df_multi.empty:
            headers_multi = DISPLAY_HEADERS_MAIN_SAFETY + ["Note"]
            out_lines.append("### メイン実験: Multi-domain\n")
            out_lines.append(format_markdown_table(df_multi, "メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\\alpha=0.6$, $k=0.20$）", headers_multi))
            latex_lines.append(format_latex_table(df_multi, "メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\\alpha=0.6$, $k=0.20$）", headers_multi, label="tab:evaluation_main_alpha=0.6_multi"))
        
        # Seeds details
        df_seeds_nobase = df_main_seeds[~df_main_seeds["Method"].astype(str).str.startswith("Base")]
        df_seeds_target = df_seeds_nobase[df_seeds_nobase["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" or x == "1.00" if isinstance(x, str) else False)]
        
        for pattern in df_target["Pattern"].unique():
            df_pat_seeds = df_seeds_target[df_seeds_target["Pattern"] == pattern]
            if not df_pat_seeds.empty:
                for method in df_pat_seeds["Method"].unique():
                    df_m_seeds = df_pat_seeds[df_pat_seeds["Method"] == method]
                    if not df_m_seeds.empty:
                        clean_m = str(method).replace('_', '')
                        clean_pat = pattern.replace('+', '_')
                        out_lines.append(format_markdown_table(df_m_seeds, f"【シード別詳細】 メイン実験 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN_SEED))
                        latex_lines.append(format_latex_table(df_m_seeds, f"メイン実験 シード別詳細 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN_SEED, label=f"tab:main_seeds_{clean_m}_{clean_pat}"))
            out_lines.append("---\n")
            
    # 3. Base Models
    out_lines.append("## 3. ベースモデル (Base Models) 実験結果")
    out_lines.append("マージ前のベース・ドメインモデルおよび Safety FT モデルの結果独立一覧表。\n")
    latex_lines.append("% --------------------------------------------------------------------------")
    latex_lines.append("% 3. ベースモデル (Base Models)")
    latex_lines.append("% --------------------------------------------------------------------------\n")
    
    if not df_main_summary.empty:
        df_base = df_main_summary[df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_base_seeds = df_main_seeds[df_main_seeds["Method"].astype(str).str.startswith("Base")]
        if not df_base.empty:
            out_lines.append(format_markdown_table(df_base, "【集計】 ベースモデル評価 (Mean ± Std)", DISPLAY_HEADERS_MAIN))
            if not df_base_seeds.empty:
                out_lines.append(format_markdown_table(df_base_seeds, "【シード別詳細】 ベースモデル評価 (Seeds 42, 43, 44)", DISPLAY_HEADERS_MAIN_SEED))
            out_lines.append("---\n")
            
            # LaTeX tables
            latex_lines.append(format_latex_table(df_base, "ベースモデル評価 集計 (Mean \\pm Std)", DISPLAY_HEADERS_MAIN, label="tab:base_models"))
            if not df_base_seeds.empty:
                latex_lines.append(format_latex_table(df_base_seeds, "ベースモデル評価 シード別詳細", DISPLAY_HEADERS_MAIN_SEED, label="tab:base_models_seeds"))
        else:
            out_lines.append("*No base model data found.*\n")
        
    # 4. Alpha Sweep
    out_lines.append("## 4. Alpha スイープ実験結果")
    out_lines.append("各 Alpha パラメータごとの Safety / Utility スコア推移表。\n")
    latex_lines.append("% --------------------------------------------------------------------------")
    latex_lines.append("% 4. Alpha スイープ (Alpha Sweep)")
    latex_lines.append("% --------------------------------------------------------------------------\n")
    
    if not df_main_summary.empty:
        df_sweep = df_main_summary[~df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_sweep_seeds = df_main_seeds[~df_main_seeds["Method"].astype(str).str.startswith("Base")]
        
        for method in df_sweep["Method"].unique():
            df_m = df_sweep[df_sweep["Method"] == method]
            df_m_seeds = df_sweep_seeds[df_sweep_seeds["Method"] == method]
            
            for pattern in df_m["Pattern"].unique():
                out_lines.append(f"### Alpha スイープ: Method = {method}, Pattern = {pattern}\n")
                df_mp = df_m[df_m["Pattern"] == pattern]
                out_lines.append(format_markdown_table(df_mp, f"【集計】 Alpha スイープ (Mean ± Std) - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN))
                
                df_mp_seeds = df_m_seeds[df_m_seeds["Pattern"] == pattern]
                if not df_mp_seeds.empty:
                    out_lines.append(format_markdown_table(df_mp_seeds, f"【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN_SEED))
                out_lines.append("---\n")
                
                # LaTeX tables
                clean_m = method.replace('_', '')
                clean_pat = pattern.replace('+', '_')
                latex_lines.append(format_latex_table(df_mp, f"Alpha スイープ 集計 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN, label=f"tab:sweep_{clean_m}_{clean_pat}"))
                if not df_mp_seeds.empty:
                    latex_lines.append(format_latex_table(df_mp_seeds, f"Alpha スイープ シード別詳細 - Method: {method}, Pattern: {pattern}", DISPLAY_HEADERS_MAIN_SEED, label=f"tab:sweep_seeds_{clean_m}_{clean_pat}"))
                
    output_path_md = f"/Users/saki/lab/src/sst_v3/docs/flmsec/{output_prefix}.md"
    output_path_latex = f"/Users/saki/lab/src/sst_v3/docs/flmsec/{output_prefix}_latex.md"
    
    os.makedirs(os.path.dirname(output_path_md), exist_ok=True)
    with open(output_path_md, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print(f"Successfully generated Markdown table at:\n  -> {output_path_md}")
    
    with open(output_path_latex, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))
    print(f"Successfully generated LaTeX table at:\n  -> {output_path_latex}")


def main():
    normal_dir = "/Users/saki/lab/src/sst_v3/results/vllm"
    
    main_n, prelim_n = collect_data(normal_dir, "vllm")
    
    print("\n[2/3] Aggregating collected data...")
    main_store = main_n
    prelim_store = prelim_n
    
    df_main_summary, df_main_seeds = aggregate_main(main_store)
    df_prelim_summary, df_prelim_seeds = aggregate_prelim(prelim_store)

    # Rename methods
    method_rename = {"data_free_sst_main": "data_free_sst", "diagonal_sst_main": "sst"}
    if not df_main_summary.empty:
        df_main_summary["Method"] = df_main_summary["Method"].replace(method_rename)
    if not df_main_seeds.empty:
        df_main_seeds["Method"] = df_main_seeds["Method"].replace(method_rename)
    if not df_prelim_summary.empty:
        df_prelim_summary["Method"] = df_prelim_summary["Method"].replace(method_rename)
    if not df_prelim_seeds.empty:
        df_prelim_seeds["Method"] = df_prelim_seeds["Method"].replace(method_rename)
    print(f"Aggregated {len(df_main_summary)} main rows ({len(df_main_seeds)} seed rows) and {len(df_prelim_summary)} prelim rows ({len(df_prelim_seeds)} seed rows).")
    
    print("\n[3/3] Generating Markdown and LaTeX documents...")
    # normal のみのドキュメント生成
    generate_documents(df_main_summary, df_main_seeds, df_prelim_summary, df_prelim_seeds, output_prefix="flmsec_hyo_vllm")


if __name__ == "__main__":
    main()