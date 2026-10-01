import os
import re

file_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_flmsec_hyo.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. replace Method names in summary dataframes
repl1 = """    df_main_summary, df_main_seeds = aggregate_main(main_store)
    df_prelim_summary, df_prelim_seeds = aggregate_prelim(prelim_store)"""
repl1_new = """    df_main_summary, df_main_seeds = aggregate_main(main_store)
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
        df_prelim_seeds["Method"] = df_prelim_seeds["Method"].replace(method_rename)"""
content = content.replace(repl1, repl1_new)


# 2. Extract tab:evaluation_main_alpha=0.6_multi
repl2 = """        # Safety Table
        out_lines.append("### メイン実験: Safety\\n")
        out_lines.append(format_markdown_table(df_main_combined, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY))
        latex_lines.append(format_latex_table(df_main_combined, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY, label="tab:evaluation_main_alpha=0.6_safety"))
        
        # Utility Table
        out_lines.append("### メイン実験: Utility\\n")
        out_lines.append(format_markdown_table(df_main_combined, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY))
        latex_lines.append(format_latex_table(df_main_combined, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY, label="tab:evaluation_main_alpha=0.6_utility"))"""

repl2_new = """        # Multi-domain table filtering
        df_multi = df_main_combined[df_main_combined["Pattern"] == "safety+math+code+medical"].copy()
        if not df_multi.empty:
            df_multi["Note"] = ""
            df_multi.loc[df_multi["Method"] != "Base", "Note"] = "Utility degradation observed"

        df_main_combined_filtered = df_main_combined[df_main_combined["Pattern"] != "safety+math+code+medical"]

        # Safety Table
        out_lines.append("### メイン実験: Safety\\n")
        out_lines.append(format_markdown_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY))
        latex_lines.append(format_latex_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_SAFETY, label="tab:evaluation_main_alpha=0.6_safety"))
        
        # Utility Table
        out_lines.append("### メイン実験: Utility\\n")
        out_lines.append(format_markdown_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY))
        latex_lines.append(format_latex_table(df_main_combined_filtered, "メイン実験（vLLM）における主要merge手法の詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", DISPLAY_HEADERS_MAIN_UTILITY, label="tab:evaluation_main_alpha=0.6_utility"))

        if not df_multi.empty:
            headers_multi = DISPLAY_HEADERS_MAIN_SAFETY + ["Note"]
            out_lines.append("### メイン実験: Multi-domain\\n")
            out_lines.append(format_markdown_table(df_multi, "メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", headers_multi))
            latex_lines.append(format_latex_table(df_multi, "メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\\\\alpha=0.6$, $k=0.20$）", headers_multi, label="tab:evaluation_main_alpha=0.6_multi"))"""
content = content.replace(repl2, repl2_new)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("generate_flmsec_hyo.py updated successfully.")
