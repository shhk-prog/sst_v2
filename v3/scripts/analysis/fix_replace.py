import re
import os

tex_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex"
tables_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"

with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

table_pattern = re.compile(r'\\begin\{table\}.*?\\end\{table\}', re.DOTALL)

count_replaced = 0
files_in_tables = os.listdir(tables_dir)

def replace_table(match):
    global count_replaced
    block = match.group(0)
    label_match = re.search(r'\\label\{(.*?)\}', block)
    if label_match:
        label = label_match.group(1).strip()
        filename1 = label.replace(":", "_") + ".tex"
        filename2 = label.replace("tab:", "tab_") + ".tex"
        filename3 = label + ".tex"
        
        target_file = None
        for fn in [filename1, filename2, filename3]:
            if fn in files_in_tables:
                target_file = fn
                break
        
        if target_file:
            count_replaced += 1
            return f"\\input{{tables/{target_file}}}"
        else:
            print(f"Table found with label {label}, but no matching file in tables/. Tried {filename1}, {filename2}, {filename3}")
            
    return block

new_content = table_pattern.sub(replace_table, content)
print(f"Replaced {count_replaced} tables.")

if count_replaced > 0:
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_content)
