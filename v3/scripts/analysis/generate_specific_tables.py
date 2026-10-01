#!/usr/bin/env python3
import os
import pandas as pd
import generate_flmsec_hyo as gf

out_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"
os.makedirs(out_dir, exist_ok=True)

def main():
    normal_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm"
    main_n, prelim_n = gf.collect_data(normal_dir, "vllm")
    
    df_main_summary, df_main_seeds = gf.aggregate_main(main_n)
    df_prelim_summary, df_prelim_seeds = gf.aggregate_prelim(prelim_n)

    method_rename = {"data_free_sst_main": "data_free_sst", "diagonal_sst_main": "sst"}
    if not df_main_summary.empty: df_main_summary["Method"] = df_main_summary["Method"].replace(method_rename)
    if not df_main_seeds.empty: df_main_seeds["Method"] = df_main_seeds["Method"].replace(method_rename)
    if not df_prelim_summary.empty: df_prelim_summary["Method"] = df_prelim_summary["Method"].replace(method_rename)
    if not df_prelim_seeds.empty: df_prelim_seeds["Method"] = df_prelim_seeds["Method"].replace(method_rename)

    latex_lines = []

    # 1. tab:prelim_detail_app
    if not df_prelim_summary.empty:
        df_prelim_target = df_prelim_summary[~df_prelim_summary["Method"].astype(str).str.startswith("Base")]
        df_prelim_simple = df_prelim_target[df_prelim_target["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" if isinstance(x, str) else False)]
        df_prelim_base = df_prelim_summary[df_prelim_summary["Method"].astype(str).str.startswith("Base")]
        df_prelim_combined = pd.concat([df_prelim_base, df_prelim_simple])
        
        # Rename columns to match requested exactly
        df_prelim_combined = df_prelim_combined.rename(columns={
            "TrustLLM Raw ASR (%)": "TrustLLM Raw ASR* (ASR$\\downarrow$ \\%)",
            r"Gibberish Ratio (\(\downarrow\), %)": "Gibberish Ratio ($\\downarrow$ \\%)",
            r"BeaverTails Utility Score (\(\uparrow\), %)": "BeaverTails Utility (Score$\\uparrow$ \\%)"
        })
        
        headers = [
            "Pattern", "Method", "TrustLLM Raw ASR* (ASR$\\downarrow$ \\%)", 
            "Gibberish Ratio ($\\downarrow$ \\%)", "BeaverTails Utility (Score$\\uparrow$ \\%)"
        ]
        
        latex = gf.format_latex_table(
            df_prelim_combined, 
            "予備実験（TrustLLM / BeaverTails）における安全性と有用性の評価（詳細再掲）",
            headers,
            label="tab:prelim_detail_app"
        )
        latex_lines.append(latex)

    # 2. tab:evaluation_main_alpha=0.6
    if not df_main_summary.empty:
        df_main_base = df_main_summary[df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_main_nobase = df_main_summary[~df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_main_simple = df_main_nobase[df_main_nobase["Alpha"].apply(lambda x: x == "0.60" or x == "N/A" or x == "None" if isinstance(x, str) else False)]
        df_main_combined = pd.concat([df_main_base, df_main_simple])
        
        df_main_combined_filtered = df_main_combined[df_main_combined["Pattern"] != "safety+math+code+medical"]

        df_main_combined_filtered = df_main_combined_filtered.rename(columns={
            "Valid Response Rate (%)": "Valid Response Rate",
            "Valid Safety Rate (%)": "Valid Safety Rate"
        })
        
        headers = [
            "Pattern", "Method", "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)",
            "Safety Ave [Conditional ASR] (ASR$\\downarrow$ \\%)", "Valid Response Rate", "Valid Safety Rate",
            "Math Ave (\\%)", "Code Ave (\\%)", "Medical Ave (\\%)", "General/Inst Ave (\\%)"
        ]
        
        # We need to make sure Conditional ASR column is renamed to just "Conditional ASR"
        df_main_combined_filtered = df_main_combined_filtered.rename(columns={
            "Safety Ave [Conditional ASR] (ASR↓ %)": "Conditional ASR",
            "Math Ave (%)": "Math Ave (\\%)",
            "Code Ave (%)": "Code Ave (\\%)",
            "Medical Ave (%)": "Medical Ave (\\%)",
            "General/Inst Ave (%)": "General/Inst Ave (\\%)",
            "Safety Ave [Original ASR] (ASR↓ %)": "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)"
        })
        headers[3] = "Conditional ASR"

        latex = gf.format_latex_table(
            df_main_combined_filtered,
            "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\alpha=0.6$, $k=0.20$）",
            headers,
            label="tab:evaluation_main_alpha=0.6"
        )
        latex_lines.append(latex)
        
    # 3. tab:base_models and tab:base_models_seeds
    if not df_main_summary.empty:
        df_base = df_main_summary[df_main_summary["Method"].astype(str).str.startswith("Base")]
        df_base_seeds = df_main_seeds[df_main_seeds["Method"].astype(str).str.startswith("Base")]
        
        rename_map = {
            "Safety Ave [Original ASR] (ASR↓ %)": "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)",
            "Math Ave (%)": "Math Ave (\\%)",
            "Code Ave (%)": "Code Ave (\\%)",
            "Medical Ave (%)": "Medical Ave (\\%)",
            "General/Inst Ave (%)": "General/Inst Ave (\\%)",
            "EvolCode (PPL↓)": "EvolCode (PPL$\\downarrow$)",
            "MedAlpaca (PPL↓)": "MedAlpaca (PPL$\\downarrow$)"
        }
        headers_base = ["Pattern", "Method", "Alpha", "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)", "Math Ave (\\%)", "Code Ave (\\%)", "Medical Ave (\\%)", "General/Inst Ave (\\%)", "EvolCode (PPL$\\downarrow$)", "MedAlpaca (PPL$\\downarrow$)"]
        headers_base_seeds = ["Pattern", "Method", "Alpha", "Seed", "Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)", "Math Ave (\\%)", "Code Ave (\\%)", "Medical Ave (\\%)", "General/Inst Ave (\\%)", "EvolCode (PPL$\\downarrow$)", "MedAlpaca (PPL$\\downarrow$)"]

        if not df_base.empty:
            df_base = df_base.rename(columns=rename_map)
            latex = gf.format_latex_table(df_base, "ベースモデル評価 集計 (Mean \\pm Std)", headers_base, label="tab:base_models")
            latex_lines.append(latex)
            
        if not df_base_seeds.empty:
            df_base_seeds = df_base_seeds.rename(columns=rename_map)
            latex = gf.format_latex_table(df_base_seeds, "ベースモデル評価 シード別詳細", headers_base_seeds, label="tab:base_models_seeds")
            latex_lines.append(latex)

    output_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/specific_tables.tex"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))
    print(f"Generated specific tables to {output_path}")

if __name__ == "__main__":
    main()
