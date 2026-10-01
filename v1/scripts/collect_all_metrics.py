#!/usr/bin/env python3
"""
全手法・全alphaのJailbreakおよびRepliQA(Utility)スコアを収集して出力するスクリプト
"""
import json
import re
from pathlib import Path

EVAL_DIR  = Path("eval/merged/sst_merge/merge_eval")
BASE_DIR  = Path("eval/merged/baseline")
BASE_OTHER_DIR = Path("eval/merged/baseline_other")
INTERP_DIR = Path("eval/merged/interpolation")

METHOD_PATTERNS = [
    ("Task Arithmetic",    BASE_DIR,       r"A5_A7_task_arithmetic_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
    ("TIES",               BASE_DIR,       r"A5_A7_ties_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
    ("TIES (other)",       BASE_OTHER_DIR, r"A5_A7_ties_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
    ("DARE",               EVAL_DIR,       r"A5_A7_dare_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
    ("SST-Merge (Interp)", INTERP_DIR,     r"A5_A7_sst_interp_k10_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
    ("SST-Merge (LW k5)",  EVAL_DIR,       r"A6_A7_sst_k5_lw_a([\d.]+)_(jailbreak|repliqa)_eval_results\.json"),
]

def get_metric(filepath, eval_type):
    with open(filepath) as f:
        d = json.load(f)
    m = d.get("metrics", {})
    if eval_type == "jailbreak":
        return m.get("resistance_rate")
    else:
        # try various keys
        for k in ("rouge_l", "rougeL", "rouge-l", "rougel", "ROUGE-L"):
            if k in m:
                v = m[k]
                if isinstance(v, dict):
                    return v.get("fmeasure", v.get("f1", v.get("score")))
                return float(v) if v is not None else None
        # fallback: first float value or dict with fmeasure
        for v in m.values():
            if isinstance(v, float):
                return v
            elif isinstance(v, dict) and "fmeasure" in v:
                return v["fmeasure"]
    return None

def collect():
    results = {}
    for method, search_dir, pattern in METHOD_PATTERNS:
        results[method] = {"jailbreak": {}, "repliqa": {}}
        if not search_dir.exists():
            continue
        for fpath in sorted(search_dir.iterdir()):
            mo = re.fullmatch(pattern, fpath.name)
            if mo:
                alpha = float(mo.group(1))
                eval_type = mo.group(2)
                try:
                    val = get_metric(fpath, eval_type)
                    if val is not None:
                        results[method][eval_type][alpha] = val
                except Exception as e:
                    pass
    return results

def print_table(results):
    all_alphas_jb = sorted(set(a for d in results.values() for a in d["jailbreak"]))
    all_alphas_rq = sorted(set(a for d in results.values() for a in d["repliqa"]))

    print("=" * 90)
    print("### Jailbreak 防御率 (resistance_rate) の手法・alpha別推移")
    print("=" * 90)
    col = "".join(f"  α={a:.2f}" for a in all_alphas_jb)
    print(f"{'Method':<28}" + col)
    print("-" * (28 + len(col)))
    for method, data in results.items():
        row = f"{method:<28}"
        for a in all_alphas_jb:
            val = data["jailbreak"].get(a)
            row += f"  {val*100:5.1f}%" if val is not None else "       N/A"
        print(row)

    print()
    print("=" * 90)
    print("### Utility スコア (ROUGE-L) の手法・alpha別推移")
    print("=" * 90)
    col = "".join(f"   α={a:.2f}" for a in all_alphas_rq)
    print(f"{'Method':<28}" + col)
    print("-" * (28 + len(col)))
    for method, data in results.items():
        row = f"{method:<28}"
        for a in all_alphas_rq:
            val = data["repliqa"].get(a)
            row += f"   {val:.4f}" if val is not None else "      N/A"
        print(row)

    print()
    print("=" * 90)
    print("### 手法ごとの Jailbreak防御率/ROUGE-L 対応表")
    print("=" * 90)
    for method, data in results.items():
        jb, rq = data["jailbreak"], data["repliqa"]
        common = sorted(set(jb) & set(rq))
        if not common:
            continue
        print(f"\n--- {method} ---")
        print(f"  {'alpha':>6}  {'JB抵抗率':>10}  {'ROUGE-L':>10}")
        for a in common:
            jb_s = f"{jb[a]*100:8.1f}%" if a in jb else "      N/A"
            rq_s = f"{rq[a]:.4f}" if a in rq else "     N/A"
            print(f"  {a:6.2f}  {jb_s}  {rq_s}")

    # also dump JSON for downstream use
    out_path = Path("docs/SST_merge_refinement/all_metrics_collected.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        # convert float keys to str for JSON
        dump = {}
        for m, d in results.items():
            dump[m] = {
                "jailbreak": {str(k): v for k, v in d["jailbreak"].items()},
                "repliqa":   {str(k): v for k, v in d["repliqa"].items()},
            }
        json.dump(dump, f, indent=2)
    print(f"\n[JSON saved to {out_path}]")

if __name__ == "__main__":
    results = collect()
    print_table(results)
