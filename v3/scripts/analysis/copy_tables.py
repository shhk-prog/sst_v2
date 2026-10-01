import sys
import os

src = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_vllm_hyo_latex.md"
dst = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_appendix_tables.tex"

with open(src, "r", encoding="utf-8") as f:
    lines = f.readlines()

# find where detailed tables start
start_idx = 0
for i, line in enumerate(lines):
    if "1. 予備実験 (Preliminary Experiments)" in line:
        start_idx = i - 1
        break

with open(dst, "w", encoding="utf-8") as f:
    f.writelines(lines[start_idx:])

print(f"Extracted tables starting from line {start_idx} to {dst}")