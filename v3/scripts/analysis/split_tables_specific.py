import re
import os

input_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/specific_tables.tex"
out_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

table_pattern = re.compile(r'\\begin\{table\}(?:\[.*?\])?.*?\\label\{(.*?)\}.*?\\end\{table\}', re.DOTALL)

matches = table_pattern.finditer(content)
count = 0
for match in matches:
    label = match.group(1).strip()
    block = match.group(0)
    
    filename = label.replace(":", "_") + ".tex"
    filename2 = label.replace("tab:", "tab_") + ".tex"
    
    out_path = os.path.join(out_dir, filename2)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(block)
    count += 1
    print(f"Saved {label} to {filename2}")

print(f"Split {count} tables into {out_dir}")
