import re
import sys

with open("flmsec_en.tex", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if re.match(r'^\s*\\(section|subsection|subsubsection|abstract|begin\{abstract\}|end\{abstract\})', line):
        print(f"{i+1}: {line.strip()}")
