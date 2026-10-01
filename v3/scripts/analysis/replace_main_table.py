import re

def replace_main_table():
    tex_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone.tex"
    custom_tables_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/custom_vllm_tables.md"

    # Read custom tables
    with open(custom_tables_file, "r", encoding="utf-8") as f:
        custom_content = f.read().strip()

    # Extract the first table (alpha=0.6 summary)
    # The table is between \begin{table}[H] or [htbp] and \end{table} for tab:custom_alpha06_summary
    match = re.search(r"(\\begin\{table\}\[(?:H|htbp)\].*?\\label\{tab:custom_alpha06_summary\}.*?\\end\{table\})", custom_content, re.DOTALL)
    if not match:
        print("Could not find tab:custom_alpha06_summary in custom tables.")
        return
        
    new_table_content = match.group(1)
    # Modify the label to match the original one just in case
    new_table_content = new_table_content.replace("\\label{tab:custom_alpha06_summary}", "\\label{tab:evaluation_main_alpha=0.6_1}")
    
    # Read target tex file
    with open(tex_file, "r", encoding="utf-8") as f:
        tex_content = f.read()

    # Find the old table to replace
    # \begin{table}[htbp] ... \label{tab:evaluation_main_alpha=0.6_1} ... \end{table}
    pattern = r"\\begin\{table\}\[(?:H|htbp)\].*?\\label\{tab:evaluation_main_alpha=0\.6_1\}.*?\\end\{table\}"
    
    new_tex_content, count = re.subn(pattern, lambda m: new_table_content, tex_content, flags=re.DOTALL)
    
    if count == 0:
        print("Could not find the target table to replace.")
        return

    # Write back
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_tex_content)
        
    print("Successfully replaced the main evaluation table with the new custom table.")

if __name__ == "__main__":
    replace_main_table()