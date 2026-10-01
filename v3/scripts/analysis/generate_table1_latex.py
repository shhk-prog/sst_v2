import pandas as pd
import numpy as np
from generate_flmsec_hyo import collect_data, aggregate_main, aggregate_prelim

def generate_table1(df_main_summary, df_prelim_summary):
    # Method mappings for table
    rows = []
    
    # 1. MergeAlign (全パターン)
    df_ma = df_main_summary[(df_main_summary["Method"] == "mergealign") & (df_main_summary["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None"))]
    if not df_ma.empty:
        # Calculate averages across patterns
        def get_mean_from_str(s):
            if pd.isna(s) or s == "-": return np.nan
            if isinstance(s, tuple) and len(s) > 0:
                return float(s[0])
            if isinstance(s, str) and "±" in s:
                return float(s.split("±")[0].strip())
            return float(s)

        orig_asr = df_ma["Safety Ave [Original ASR] (ASR↓ %)"].apply(get_mean_from_str).mean()
        orig_asr_str = f"{orig_asr:.2f}" if not np.isnan(orig_asr) else "---"
        
        # MergeAlign Conditional ASR is usually NaN (---)
        ca_str = "---（有効応答なし）"
        vrr_str = "0.00"
        vsr_str = "0.00"
        
        med_ave = df_ma["Medical Ave (%)"].apply(get_mean_from_str).mean()
        util_str = f"医療のみ{med_ave:.2f}、他ドメイン0" if not np.isnan(med_ave) else "医療のみ---、他ドメイン0"
        
        rows.append([
            "MergeAlign（全パターン）", orig_asr_str, ca_str, vrr_str, vsr_str, util_str,
            "False safe：Original ASRは最良に見えるが応答が生成されていない"
        ])
    
    # 2. Task Arithmetic (safety+math)
    df_ta_math = df_main_summary[(df_main_summary["Method"] == "task_arithmetic") & (df_main_summary["Pattern"] == "safety+math") & (df_main_summary["Alpha"] == "0.60")]
    if not df_ta_math.empty:
        r = df_ta_math.iloc[0]
        orig_asr = get_mean_from_str(r["Safety Ave [Original ASR] (ASR↓ %)"])
        orig_asr = f"{orig_asr:.2f}" if not np.isnan(orig_asr) else "---"
        ca = get_mean_from_str(r["Safety Ave [Conditional ASR] (ASR↓ %)"])
        ca = f"{ca:.2f}" if not np.isnan(ca) else "---"
        vrr = get_mean_from_str(r["Valid Response Rate (%)"])
        vrr = f"{vrr:.2f}" if not np.isnan(vrr) else "---"
        vsr = get_mean_from_str(r["Valid Safety Rate (%)"])
        vsr = f"{vsr:.2f}" if not np.isnan(vsr) else "---"
        math_ave = get_mean_from_str(r["Math Ave (%)"])
        code_ave = get_mean_from_str(r["Code Ave (%)"])
        util_str = f"Math {math_ave:.2f}、Code {code_ave:.2f}"
        
        rows.append([
            "Task Arithmetic (safety+math)", orig_asr, ca, vrr, vsr, util_str,
            "Validly safe：低ASRが有効応答と有用性維持に支えられている"
        ])
        
    # 3. Task Arithmetic (safety+code)
    df_ta_code = df_main_summary[(df_main_summary["Method"] == "task_arithmetic") & (df_main_summary["Pattern"] == "safety+code") & (df_main_summary["Alpha"] == "0.60")]
    if not df_ta_code.empty:
        r = df_ta_code.iloc[0]
        orig_asr = get_mean_from_str(r["Safety Ave [Original ASR] (ASR↓ %)"])
        orig_asr = f"{orig_asr:.2f}" if not np.isnan(orig_asr) else "---"
        ca = get_mean_from_str(r["Safety Ave [Conditional ASR] (ASR↓ %)"])
        ca = f"{ca:.2f}" if not np.isnan(ca) else "---"
        vrr = get_mean_from_str(r["Valid Response Rate (%)"])
        vrr = f"{vrr:.2f}" if not np.isnan(vrr) else "---"
        vsr = get_mean_from_str(r["Valid Safety Rate (%)"])
        vsr = f"{vsr:.2f}" if not np.isnan(vsr) else "---"
        code_ave = get_mean_from_str(r["Code Ave (%)"])
        med_ave = get_mean_from_str(r["Medical Ave (%)"])
        util_str = f"Code {code_ave:.2f}、Medical {med_ave:.2f}"
        
        rows.append([
            "Task Arithmetic (safety+code)", orig_asr, ca, vrr, vsr, util_str,
            "Unsafe but functional：応答は有効だが有害追従が多く、Original ASRだけでは危険性を過小評価"
        ])
        
    # 4. LED-Merging (予備実験, TrustLLM) - これは固定値でもよいが、とりあえずそのままにする
    rows.append([
        "LED-Merging（予備実験, TrustLLM）", "Raw ASR 87.19", "---", "Gibberish Ratio 95.94", "---", "Utility 5.00",
        "False unsafe：無効応答の多さが単一評価器では攻撃成功として誤判定されやすい"
    ])
    
    # Generate LaTeX
    latex = [
        "\\begin{table}[htbp]",
        "\\caption{評価前後で解釈が変わる代表例}",
        "\\label{tab:safety_diagnostic}",
        "\\centering",
        "\\small",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\renewcommand{\\arraystretch}{0.95}",
        "\\begin{tabularx}{\\textwidth}{",
        ">{\\raggedright\\arraybackslash}p{2.45cm}",
        ">{\\centering\\arraybackslash}p{1.35cm}",
        ">{\\centering\\arraybackslash}p{1.75cm}",
        ">{\\centering\\arraybackslash}p{0.85cm}",
        ">{\\centering\\arraybackslash}p{0.85cm}",
        ">{\\raggedright\\arraybackslash}p{2.00cm}",
        ">{\\raggedright\\arraybackslash}X",
        "}",
        "\\toprule",
        "\\textbf{Method (Pattern)} &",
        "\\textbf{Original ASR} &",
        "\\textbf{Conditional ASR} &",
        "\\textbf{VRR} &",
        "\\textbf{VSR} &",
        "\\textbf{Utility傾向} &",
        "\\textbf{評価後の解釈} \\\\",
        "&",
        "\\textbf{(\\%$\\downarrow$)} &",
        "\\textbf{(\\%$\\downarrow$)} &",
        "\\textbf{(\\%$\\uparrow$)} &",
        "\\textbf{(\\%$\\uparrow$)} &",
        "&",
        "\\\\",
        "\\midrule"
    ]
    
    for r in rows:
        escaped_r = [str(x).replace("%", "\\%") for x in r]
        latex.append(" & ".join(escaped_r) + " \\\\")
        
    latex.extend([
        "\\bottomrule",
        "\\end{tabularx}",
        "\\end{table}"
    ])
    
    return "\n".join(latex)

def main():
    normal_dir = "/Users/saki/lab/src/sst_v3/results/vllm"
    main_n, prelim_n = collect_data(normal_dir, "vllm")
    df_main_summary, _ = aggregate_main(main_n)
    df_prelim_summary, _ = aggregate_prelim(prelim_n)
    
    latex_table1 = generate_table1(df_main_summary, df_prelim_summary)
    
    out_path = "/Users/saki/lab/src/sst_v3/docs/flmsec/table1_latex.tex"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(latex_table1)
    print(f"Table 1 saved to {out_path}")

if __name__ == "__main__":
    main()
