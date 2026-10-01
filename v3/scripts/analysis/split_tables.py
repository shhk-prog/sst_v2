import re
import os

input_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_hyo_vllm_latex.md"
out_dir = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# 正規表現で各 table ブロックを抽出
# \begin{table} ... \label{...} ... \end{table}
table_pattern = re.compile(r'\\begin\{table\}(?:\[.*?\])?.*?\\label\{(.*?)\}.*?\\end\{table\}', re.DOTALL)

matches = table_pattern.finditer(content)
count = 0
for match in matches:
    label = match.group(1)
    block = match.group(0)
    # Generate filename
    # Usually we use tab_XXX.tex for tab:XXX
    filename = label.replace("tab:", "tab_") + ".tex"
    out_path = os.path.join(out_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(block)
    count += 1

print(f"Split {count} tables into {out_dir}")
