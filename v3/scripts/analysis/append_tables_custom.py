import re

def append_custom_tables():
    tex_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone_nosst2.tex"
    custom_tables_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/custom_vllm_tables.md"

    # Read custom tables
    with open(custom_tables_file, "r", encoding="utf-8") as f:
        custom_content = f.read().strip()

    # Read target tex file
    with open(tex_file, "r", encoding="utf-8") as f:
        tex_content = f.read()

    # Find the section "\section{vLLM 全手法詳細結果}" and remove everything after it
    # We'll just replace from \section{vLLM 全手法詳細結果} to the \end{document}
    pattern = r"\\section\{vLLM 全手法詳細結果\}.*?\\end\{document\}"
    
    # We will replace it with the new section and the custom tables
    replacement = "\\section{vLLM 全手法詳細結果}\n\n" + custom_content + "\n\n\\end{document}"
    
    new_tex_content, count = re.subn(pattern, lambda m: replacement, tex_content, flags=re.DOTALL)
    
    if count == 0:
        print("Could not find the target section to replace.")
        return

    # Write back
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_tex_content)
        
    print("Successfully replaced the old result tables with the new custom tables.")

if __name__ == "__main__":
    append_custom_tables()
