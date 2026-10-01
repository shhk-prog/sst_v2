import os

path = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_appendix_tables.tex"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

import re
# Replace something like "100.00 \pm 0.00" with "100.00 $\pm$ 0.00"
content = re.sub(r"([0-9.]+) \\pm ([0-9.]+)", r"\1 $\\pm$ \2", content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed LaTeX syntax in flmsec_appendix_tables.tex")

path2 = "/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_flmsec_hyo.py"
with open(path2, "r", encoding="utf-8") as f:
    content2 = f.read()

content2 = content2.replace('return f"{mean:.2f} \\\\pm {std:.2f}"', 'return f"{mean:.2f} $\\\\pm$ {std:.2f}"')

with open(path2, "w", encoding="utf-8") as f:
    f.write(content2)

print("Fixed generate_flmsec_hyo.py")