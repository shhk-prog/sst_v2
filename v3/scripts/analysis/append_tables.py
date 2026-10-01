import re

def append_and_replace():
    tex_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone_nosst2.tex"
    table1_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/table1_latex.tex"
    vllm_tables_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_hyo_vllm_latex.md"

    # 1. Read table1 latex
    with open(table1_file, "r", encoding="utf-8") as f:
        table1_latex = f.read().strip()

    # 2. Extract needed tables from vllm_tables_file
    with open(vllm_tables_file, "r", encoding="utf-8") as f:
        vllm_content = f.read()
    
    # We want tables from Section 2, and Section 4.
    # Actually, to make it comprehensive as requested, we can extract all LaTeX tables from the file
    # and append them as a new appendix section.
    # Let's extract lines that start with % --- and end with \end{table}
    tables_to_append = []
    
    # Extract Section 2 (Main Experiments) and Section 4 (Alpha Sweep)
    lines = vllm_content.splitlines()
    append_lines = []
    in_target_section = False
    
    for line in lines:
        if "2. メイン実験 (Main Experiments)" in line or "4. Alpha スイープ (Alpha Sweep)" in line:
            in_target_section = True
            append_lines.append(line)
        elif "3. ベースモデル (Base Models)" in line:
            in_target_section = False
        elif in_target_section:
            append_lines.append(line)
            
    appended_content = "\\section{vLLM 全手法詳細結果}\n\n" + "\n".join(append_lines)
    
    # 3. Read target tex file
    with open(tex_file, "r", encoding="utf-8") as f:
        tex_content = f.read()
        
    # Replace Table 1 markdown
    # The markdown starts around "**表1：評価前後で解釈が変わる代表例**" and ends at the empty line after the table
    pattern = r"\*\*表1：評価前後で解釈が変わる代表例\*\*.*?\| False unsafe：無効応答の多さが単一評価器では攻撃成功として誤判定されやすい \|"
    
    match = re.search(pattern, tex_content, re.DOTALL)
    if match:
        tex_content = tex_content[:match.start()] + table1_latex + tex_content[match.end():]
    else:
        print("Could not find Markdown Table 1 to replace.")
        return
        
    # Append to the end before \end{document}
    if "\\end{document}" in tex_content:
        tex_content = tex_content.replace("\\end{document}", appended_content + "\n\n\\end{document}")
    else:
        print("Could not find \\end{document}.")
        return

    # 4. Write back
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(tex_content)
        
    print("Successfully replaced Table 1 and appended all result tables to the end of the document.")

if __name__ == "__main__":
    append_and_replace()
