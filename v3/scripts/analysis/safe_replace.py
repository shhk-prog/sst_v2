import re
import os

tex_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex"
tables_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"

with open(tex_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_table = False
table_lines = []

files_in_tables = os.listdir(tables_dir)
count_replaced = 0

for line in lines:
    if "\\begin{table}" in line:
        in_table = True
        table_lines = [line]
    elif "\\end{table}" in line and in_table:
        table_lines.append(line)
        in_table = False
        
        table_content = "".join(table_lines)
        label_match = re.search(r'\\label\{(.*?)\}', table_content)
        
        replaced = False
        if label_match:
            label = label_match.group(1).strip()
            
            filename_candidates = [
                label.replace(":", "_") + ".tex",
                label.replace("tab:", "tab_") + ".tex",
                label + ".tex",
                label.replace("tab:", "tab_").replace("-", "_") + ".tex"
            ]
            
            if label == "tab:base_models_app":
                filename_candidates.append("tab_base_models.tex")
            if label == "tab:base_models_seeds_app":
                filename_candidates.append("tab_base_models_seeds.tex")
            if label == "tab:task-arithmetic-single-point":
                filename_candidates.append("tab_task_arithmetic_single_point.tex")
            
            target_file = None
            for fn in filename_candidates:
                if fn in files_in_tables:
                    target_file = fn
                    break
            
            if target_file:
                new_lines.append(f"\\input{{tables/{target_file}}}\n")
                count_replaced += 1
                replaced = True
                print(f"Replaced: {label} -> {target_file}")
        
        if not replaced:
            new_lines.extend(table_lines)
            if label_match:
                print(f"Not replaced: {label_match.group(1).strip()}")
            else:
                print("Not replaced: (no label found)")
            
    elif in_table:
        table_lines.append(line)
    else:
        new_lines.append(line)

with open(tex_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
    
print(f"Total replaced: {count_replaced} tables.")
