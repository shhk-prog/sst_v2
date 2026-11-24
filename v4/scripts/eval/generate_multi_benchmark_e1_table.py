"""
Multi-Benchmark Comprehensive Results Table across 10 Merge Methods.
Adheres strictly to the dataset division of labor:
  - Safety (All Candidates): HarmBench, JailbreakBench, StrongReject, WildJailbreak
  - Math Track (Primary Utility): GSM8K, MATH500 -> U_math = (GSM8K + MATH500) / 2
  - General Utility (Secondary Guardrails): IFEval, MMLU, AlpacaEval 2
  - Code / Medical (Separate Track / Transfer / Guardrail if available, NOT mixed into U_math)

Aggregates the 10 representative methods at their fixed settings (selected on Seed 42 Dev)
across seeds 42, 43, 44 (3-Seed Mean ± SD).
"""

import os
import json
import glob
from pathlib import Path
import numpy as np

def extract_benchmark_metrics(fpath):
    """Extract metrics from benchmark json."""
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None

    fname = os.path.basename(fpath)
    res = {}

    # Safety
    if "harmbench_safety.json" in fname:
        res["harmbench_asr"] = d.get("asr", 0.0)
    elif "jailbreakbench_safety.json" in fname:
        res["jailbreakbench_asr"] = d.get("asr", 0.0)
    elif "strongreject_safety.json" in fname:
        res["strongreject_asr"] = d.get("asr", 0.0)
    elif "wildjailbreak_safety.json" in fname:
        res["wildjailbreak_asr"] = d.get("asr", 0.0)

    # Math
    elif "utility_math_gsm8k.json" in fname:
        if "results" in d and "gsm8k" in d["results"]:
            res["gsm8k"] = d["results"]["gsm8k"].get("exact_match,strict-match", d["results"]["gsm8k"].get("exact_match", 0.0))
    elif "utility_math_minerva_math500.json" in fname:
        if "results" in d and "minerva_math500" in d["results"]:
            res["math500"] = d["results"]["minerva_math500"].get("math_verify,none", 0.0)

    # General
    elif "utility_general_ifeval.json" in fname:
        if "results" in d and "ifeval" in d["results"]:
            res["ifeval"] = d["results"]["ifeval"].get("prompt_level_strict_acc,none", 0.0)
    elif "utility_general_mmlu.json" in fname:
        if "results" in d and "mmlu" in d["results"]:
            res["mmlu"] = d["results"]["mmlu"].get("acc,none", 0.0)
    elif "alpaca_eval2.json" in fname:
        res["alpaca_eval2"] = d.get("length_controlled_winrate", d.get("win_rate", 0.0))

    # Code / Medical (Separate Track / Transfer)
    elif "utility_code_humaneval.json" in fname:
        if "results" in d and "humaneval" in d["results"]:
            res["humaneval"] = d["results"]["humaneval"].get("pass@1", 0.0)
    elif "utility_code_mbpp.json" in fname:
        if "results" in d and "mbpp" in d["results"]:
            res["mbpp"] = d["results"]["mbpp"].get("pass@1", 0.0)
    elif "utility_medical_medqa_4options.json" in fname:
        if "results" in d and "medqa_4options" in d["results"]:
            res["medqa"] = d["results"]["medqa_4options"].get("acc,none", 0.0)
    elif "utility_medical_pubmedqa.json" in fname:
        if "results" in d and "pubmedqa" in d["results"]:
            res["pubmedqa"] = d["results"]["pubmedqa"].get("acc,none", 0.0)

    return res

def scan_candidate_benchmarks(method_dir, prefix):
    """Collect all metrics for candidate prefix in method_dir."""
    cand_metrics = {}
    pattern = os.path.join(method_dir, f"{prefix}_*.json")
    for f in glob.glob(pattern):
        m = extract_benchmark_metrics(f)
        if m:
            cand_metrics.update(m)
    return cand_metrics

def main():
    # Load previous formal legacy E1 table to get fixed settings
    formal_table_path = "v4/results/eval/legacy_e1/formal_legacy_e1_table.json"
    if not os.path.exists(formal_table_path):
        print(f"Error: {formal_table_path} not found. Run generate_formal_legacy_e1_table.py first.")
        return

    with open(formal_table_path, "r", encoding="utf-8") as f:
        formal_data = json.load(f)

    # Load legacy rescored data to get harmful valid/VRR metrics
    rescore_data_path = "v4/results/eval/legacy_e1/legacy_e1_math_comprehensive_summary.json"
    with open(rescore_data_path, "r", encoding="utf-8") as f:
        rescored_summary = json.load(f)

    cand_list = rescored_summary.get("candidates", rescored_summary)
    rescored_map = {item.get("candidate_id", item.get("candidate", "")): item for item in cand_list}

    if isinstance(formal_data, list):
        fixed_settings = {item["method"]: item["setting"] for item in formal_data}
    else:
        fixed_settings = formal_data.get("selected_settings_on_dev", {})
    print("Fixed Settings chosen on Development (Seed 42):")
    for m, s in fixed_settings.items():
        print(f"  {m}: {s}")

    seeds = [42, 43, 44]
    methods = [
        "diagonal_sst_main",
        "task_arithmetic",
        "ties",
        "dare",
        "della",
        "matena_fisher",
        "data_free_sst_main",
        "led_merging",
        "safemerge",
        "mergealign"
    ]

    all_method_stats = []

    for m in methods:
        setting = fixed_settings.get(m, "default")
        alpha_val = None
        if "alpha=" in setting:
            alpha_val = float(setting.split("alpha=")[1])

        seed_results = []
        for s in seeds:
            # find candidate matching method, alpha, seed
            matched_item = None
            for cand_id, item in rescored_map.items():
                if item["method"] == m and item["seed"] == s:
                    if alpha_val is not None:
                        if abs(item.get("alpha", -999) - alpha_val) < 1e-4:
                            matched_item = item
                            break
                    else:
                        matched_item = item
                        break

            if not matched_item:
                continue

            # Scan raw files for other benchmarks
            cand_prefix = matched_item.get("candidate_id", matched_item.get("candidate", ""))
            m_dir = f"v3/results/vllm/debug_limit320/merged/seed{s}/safety+math/{m}"
            raw_metrics = scan_candidate_benchmarks(m_dir, cand_prefix)

            # Combine
            combined = dict(matched_item)
            combined.update(raw_metrics)

            # Safety aggregate from json
            s_agg = matched_item.get("safety_aggregate", {})
            combined["asr_valid"] = s_agg.get("asr_valid", matched_item.get("asr_valid", 0.0))
            combined["vrr"] = s_agg.get("vrr_harmful", matched_item.get("vrr_harmful", matched_item.get("vrr", 0.0)))

            # Harmful Safety Benchmarks
            s_bench = matched_item.get("safety_by_benchmark", {})
            combined["harmbench_asr"] = s_bench.get("harmbench_safety", {}).get("asr_valid", combined.get("harmbench_asr", 0.0))
            combined["jailbreakbench_asr"] = s_bench.get("jailbreakbench_safety", {}).get("asr_valid", combined.get("jailbreakbench_asr", 0.0))
            combined["strongreject_asr"] = s_bench.get("strongreject_safety", {}).get("asr_valid", combined.get("strongreject_asr", 0.0))
            combined["wildjailbreak_asr"] = s_bench.get("wildjailbreak_safety", {}).get("asr_valid", combined.get("wildjailbreak_asr", 0.0))

            # Math Utility from matched_item['utility']
            u = matched_item.get("utility", {})
            gsm = u.get("math_gsm8k", 0.0)
            m500 = u.get("math_minerva500", 0.0)
            combined["gsm8k"] = gsm
            combined["math500"] = m500
            combined["u_math"] = (gsm + m500) / 2.0
            mmlu = combined.get("mmlu", 0.0)
            alpaca = combined.get("alpaca_eval2", 0.0)

            # Code / Medical Transfer
            he = combined.get("humaneval", 0.0)
            mb = combined.get("mbpp", 0.0)
            medqa = combined.get("medqa", 0.0)
            pubmed = combined.get("pubmedqa", 0.0)

            seed_results.append(combined)

        if not seed_results:
            continue

        # Compute Mean ± SD for each metric
        def mean_sd(key):
            vals = [r[key] for r in seed_results if key in r and r[key] is not None]
            if not vals:
                return None, None
            return float(np.mean(vals)), float(np.std(vals))

        m_asr_valid, sd_asr_valid = mean_sd("asr_valid")
        m_vrr, sd_vrr = mean_sd("vrr")
        m_hb, sd_hb = mean_sd("harmbench_asr")
        m_jb, sd_jb = mean_sd("jailbreakbench_asr")
        m_sr, sd_sr = mean_sd("strongreject_asr")
        m_wj, sd_wj = mean_sd("wildjailbreak_asr")
        m_gsm, sd_gsm = mean_sd("gsm8k")
        m_m500, sd_m500 = mean_sd("math500")
        m_umath, sd_umath = mean_sd("u_math")
        m_ifeval, sd_ifeval = mean_sd("ifeval")
        m_mmlu, sd_mmlu = mean_sd("mmlu")
        m_alpaca, sd_alpaca = mean_sd("alpaca_eval2")
        m_he, sd_he = mean_sd("humaneval")
        m_mb, sd_mb = mean_sd("mbpp")
        m_medqa, sd_medqa = mean_sd("medqa")
        m_pubmed, sd_pubmed = mean_sd("pubmedqa")

        feasible_count = 0
        for r in seed_results:
            av = r.get("asr_valid")
            vr = r.get("vrr")
            if av is not None and vr is not None and av <= 0.05 and vr >= 0.95:
                feasible_count += 1

        # Method Display Name
        disp_name = m
        if m == "task_arithmetic":
            disp_name = "Linear Safety-Patch"
        elif m == "diagonal_sst_main":
            disp_name = "SST-Merge (Diagonal)"
        elif m == "data_free_sst_main":
            disp_name = "Data-Free SST"
        elif m == "matena_fisher":
            disp_name = "Fisher-weighted"
        elif m == "led_merging":
            disp_name = "LED-Merging"
        elif m == "safemerge":
            disp_name = "SafeMERGE"
        elif m == "mergealign":
            disp_name = "MergeAlign"
        elif m == "ties":
            disp_name = "TIES"
        elif m == "dare":
            disp_name = "DARE"
        elif m == "della":
            disp_name = "DELLA"

        all_method_stats.append({
            "method": m,
            "display_name": disp_name,
            "setting": setting,
            "n_seeds": len(seed_results),
            "feasible_count": feasible_count,
            "asr_valid": (m_asr_valid, sd_asr_valid),
            "vrr_harmful": (m_vrr, sd_vrr),
            "harmbench_asr": (m_hb, sd_hb),
            "jailbreakbench_asr": (m_jb, sd_jb),
            "strongreject_asr": (m_sr, sd_sr),
            "wildjailbreak_asr": (m_wj, sd_wj),
            "gsm8k": (m_gsm, sd_gsm),
            "math500": (m_m500, sd_m500),
            "u_math": (m_umath, sd_umath),
            "ifeval": (m_ifeval, sd_ifeval),
            "mmlu": (m_mmlu, sd_mmlu),
            "alpaca_eval2": (m_alpaca, sd_alpaca),
            "humaneval": (m_he, sd_he),
            "mbpp": (m_mb, sd_mb),
            "medqa": (m_medqa, sd_medqa),
            "pubmedqa": (m_pubmed, sd_pubmed),
        })

    # Sort by U_math descending among Feasible, then rest
    all_method_stats.sort(key=lambda x: (x["feasible_count"] == 3, x["u_math"][0]), reverse=True)

    # 1. Print Primary Table: Safety 4-Benchmark + Math Primary Utility + General Guardrails
    print("\n" + "=" * 135)
    print(" COMPREHENSIVE MULTI-BENCHMARK TABLE FOR ALL 10 MERGE METHODS (3-Seed Protocol: Mean ± SD)")
    print(" Evaluated on Fixed Settings chosen on Development (Seed 42)")
    print("=" * 135)

    headers = [
        "Method", "Setting",
        "HarmBench", "JailbreakB", "StrongRej", "WildJailB", "VRR-H",
        "GSM8K", "MATH500", "U_math (Primary)",
        "IFEval", "MMLU",
        "Status"
    ]
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")

    def fmt_pct(val, sd):
        if val is None or sd is None:
            return "N/A"
        return f"{val*100:.1f}±{sd*100:.1f}%"

    for s in all_method_stats:
        status = f"FEASIBLE ({s['feasible_count']}/3)" if s["feasible_count"] == 3 else f"FAIL ({s['feasible_count']}/3)"
        row = [
            f"**{s['display_name']}**",
            s["setting"],
            fmt_pct(*s["harmbench_asr"]),
            fmt_pct(*s["jailbreakbench_asr"]),
            fmt_pct(*s["strongreject_asr"]),
            fmt_pct(*s["wildjailbreak_asr"]),
            fmt_pct(*s["vrr_harmful"]),
            fmt_pct(*s["gsm8k"]),
            fmt_pct(*s["math500"]),
            f"**{fmt_pct(*s['u_math'])}**",
            fmt_pct(*s["ifeval"]),
            fmt_pct(*s["mmlu"]),
            f"**{status}**"
        ]
        print("| " + " | ".join(row) + " |")

    # 2. Print Secondary Guardrail & Cross-Domain Table (Code & Medical Transfer)
    print("\n" + "=" * 115)
    print(" SECONDARY GUARDRAILS & CROSS-DOMAIN TRANSFER TABLE (Math Merged Models evaluated on Code & Medical)")
    print(" Note: Code & Medical metrics are NOT mixed into U_math; shown strictly for capability preservation check.")
    print("=" * 115)

    headers_sec = [
        "Method", "Setting", "U_math",
        "HumanEval", "MBPP", "U_code (Trans)",
        "MedQA", "PubMedQA",
        "IFEval", "MMLU", "AlpacaEval2"
    ]
    print("| " + " | ".join(headers_sec) + " |")
    print("|" + "|".join(["---"] * len(headers_sec)) + "|")

    for s in all_method_stats:
        he_val = s["humaneval"][0]
        mb_val = s["mbpp"][0]
        if he_val is not None and mb_val is not None:
            u_code_m = (he_val + mb_val) / 2.0
            u_code_sd = (s["humaneval"][1] + s["mbpp"][1]) / 2.0
            code_str = fmt_pct(u_code_m, u_code_sd)
        else:
            code_str = "N/A"

        alpaca_str = "N/A"
        if s["alpaca_eval2"][0] is not None and s["alpaca_eval2"][0] > 0:
            alpaca_str = f"{s['alpaca_eval2'][0]:.1f}±{s['alpaca_eval2'][1]:.1f}%"

        row_sec = [
            f"**{s['display_name']}**",
            s["setting"],
            fmt_pct(*s["u_math"]),
            fmt_pct(*s["humaneval"]),
            fmt_pct(*s["mbpp"]),
            code_str,
            fmt_pct(*s["medqa"]),
            fmt_pct(*s["pubmedqa"]),
            fmt_pct(*s["ifeval"]),
            fmt_pct(*s["mmlu"]),
            alpaca_str
        ]
        print("| " + " | ".join(row_sec) + " |")

    # Save to JSON
    out_json = "v4/results/eval/legacy_e1/comprehensive_multi_benchmark_e1_table.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_method_stats, f, indent=2)
    print(f"\n[Saved] Full multi-benchmark table saved to: {out_json}")

if __name__ == "__main__":
    main()
