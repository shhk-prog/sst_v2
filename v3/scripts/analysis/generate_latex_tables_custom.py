import os
import pandas as pd
import numpy as np
from generate_flmsec_hyo import collect_data, aggregate_main

# 新しいヘッダー定義
CUSTOM_HEADERS_SUMMARY = [
    "Pattern", "Method", "Alpha",
    "Safety Ave [Original ASR] (ASR↓ %)",
    "Safety Ave [Conditional ASR] (ASR↓ %)",
    "Valid Response Rate (%)",
    "Valid Safety Rate (%)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
    "EvolCode (PPL↓)", "MedAlpaca (PPL↓)"
]

CUSTOM_HEADERS_SEEDS = [
    "Pattern", "Method", "Alpha", "Seed",
    "Safety Ave [Original ASR] (ASR↓ %)",
    "Safety Ave [Conditional ASR] (ASR↓ %)",
    "Valid Response Rate (%)",
    "Valid Safety Rate (%)",
    "Math Ave (%)", "Code Ave (%)", "Medical Ave (%)", "General/Inst Ave (%)",
    "EvolCode (PPL↓)", "MedAlpaca (PPL↓)"
]

def format_latex_val(val, is_ppl=False):
    if pd.isna(val) or val is None or val == "-" or val == "---": return "---"
    if isinstance(val, tuple) and len(val) == 2:
        mean, std = val
        if pd.isna(mean) or mean is None: return "---"
        return f"{mean:.2f} $\\pm$ {std:.2f}"
    elif isinstance(val, (int, float)):
        if np.isnan(val): return "---"
        return f"{val:.2f}"
    return str(val).replace("_", "\\_")

def format_latex_table(df, title, headers, label="tab:result"):
    if df.empty:
        return f"% --- {title} (No data) ---\n\n"
    
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
        if ch == "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)": ch = "Original ASR (\\%)"
        if ch == "Safety Ave [Conditional ASR] (ASR$\\downarrow$ \\%)": ch = "Conditional ASR (\\%)"
        if ch == "Valid Response Rate (\\%)": ch = "VRR (\\%)"
        if ch == "Valid Safety Rate (\\%)": ch = "VSR (\\%)"
        clean_headers.append(f"\\textbf{{{ch}}}")
        
    latex_lines.append(" & ".join(clean_headers) + " \\\\")
    latex_lines.append("\\midrule")
    
    sort_cols = [c for c in ["Pattern", "Method", "Alpha", "Seed"] if c in df.columns]
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
                row_cells.append(format_latex_val(val))
        latex_lines.append(" & ".join(row_cells) + " \\\\")
        
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabularx}",
        "\\end{table}\n\n"
    ])
    return "\n".join(latex_lines)

def generate_documents(df_main_summary, df_main_seeds, output_path):
    latex_lines = [
        "% ==========================================================================",
        "% カスタム生成された全指標併記の実験結果表",
        "% ==========================================================================\n"
    ]
    
    if not df_main_summary.empty:
        df_main_nobase = df_main_summary[~df_main_summary["Method"].astype(str).str.startswith("Base")]
        
        # 1. 全ての手法の結果(α=0.6)(シード平均，標準偏差あり)
        df_target_06 = df_main_nobase[df_main_nobase["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" or x == "1.00" if isinstance(x, str) else False)]
        if not df_target_06.empty:
            latex_lines.append(format_latex_table(df_target_06, "全ての手法の結果（$\\alpha=0.6$, シード平均・標準偏差あり）", CUSTOM_HEADERS_SUMMARY, label="tab:custom_alpha06_summary"))
            
        # 2. 全ての手法の結果(シード平均，標準偏差あり，αスイープ)
        for pattern in df_main_nobase["Pattern"].unique():
            df_pat = df_main_nobase[df_main_nobase["Pattern"] == pattern]
            clean_pat = pattern.replace('+', '_')
            latex_lines.append(format_latex_table(df_pat, f"Alphaスイープ シード平均 - Pattern: {pattern}", CUSTOM_HEADERS_SUMMARY, label=f"tab:custom_sweep_summary_{clean_pat}"))
            
        # 3. 全ての手法の結果(シード別，αスイープ)
        df_seeds_nobase = df_main_seeds[~df_main_seeds["Method"].astype(str).str.startswith("Base")]
        for pattern in df_seeds_nobase["Pattern"].unique():
            df_pat_seeds = df_seeds_nobase[df_seeds_nobase["Pattern"] == pattern]
            if not df_pat_seeds.empty:
                clean_pat = pattern.replace('+', '_')
                latex_lines.append(format_latex_table(df_pat_seeds, f"Alphaスイープ シード別詳細 - Pattern: {pattern}", CUSTOM_HEADERS_SEEDS, label=f"tab:custom_sweep_seeds_{clean_pat}"))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))
    print(f"Successfully generated custom LaTeX table at:\n  -> {output_path}")

def main():
    normal_dir = "/Users/saki/lab/src/sst_v3/results/vllm"
    main_n, _ = collect_data(normal_dir, "vllm")
    
    print("\nAggregating collected data...")
    df_main_summary, df_main_seeds = aggregate_main(main_n)

    method_rename = {"data_free_sst_main": "data_free_sst", "diagonal_sst_main": "sst"}
    if not df_main_summary.empty:
        df_main_summary["Method"] = df_main_summary["Method"].replace(method_rename)
    if not df_main_seeds.empty:
        df_main_seeds["Method"] = df_main_seeds["Method"].replace(method_rename)
        
    output_path = "/Users/saki/lab/src/sst_v3/docs/flmsec/custom_vllm_tables.md"
    print("\nGenerating documents...")
    generate_documents(df_main_summary, df_main_seeds, output_path)

if __name__ == "__main__":
    main()
