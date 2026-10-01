import re
import os

tex_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex"
tables_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"

with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

# \begin{table} ... \end{table} のブロックを見つける正規表現
table_pattern = re.compile(r'\\begin\{table\}(?:\[.*?\])?.*?\\end\{table\}', re.DOTALL)

def replace_table(match):
    block = match.group(0)
    label_match = re.search(r'\\label\{(.*?)\}', block)
    if label_match:
        label = label_match.group(1)
        # Check if corresponding .tex file exists
        # To map label to filename, we need to know the mapping rules
        # Or simply, if there is ANY file in tables/ that contains the label name, use it?
        # Let's map directly if possible.
        # generate_flmsec_hyo.py uses the label as the filename for some, but not all.
        # Actually we generated tables as:
        # tab_base_models.tex -> tab:base_models
        # tab_evaluation_main_alpha=0.6_safety.tex -> tab:evaluation_main_alpha=0.6_safety
        # etc.
        # Generally, filename is label.replace("tab:", "tab_") + ".tex"
        # However, for some, the label is exactly tab:something and file is tab_something.tex. Let's check:
        # label: "tab:base_models" -> filename: "tab_base_models.tex"
        # label: "tab:prelim_detail_app" -> filename: "tab_prelim_detail_app.tex"
        
        filename1 = label.replace(":", "_") + ".tex"
        filename2 = label.replace("tab:", "tab_") + ".tex"
        filename3 = label + ".tex"
        
        target_file = None
        for fn in [filename1, filename2, filename3]:
            if os.path.exists(os.path.join(tables_dir, fn)):
                target_file = fn
                break
        
        if target_file:
            # We found a generated table. Replace the block with \input{tables/filename}
            return f"\\input{{tables/{target_file}}}"
            
    return block

new_content = table_pattern.sub(replace_table, content)

if content != new_content:
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced tables with \input successfully.")
else:
    print("No tables replaced.")

