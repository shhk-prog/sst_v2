#!/usr/bin/env python3
"""
update_appendix.py

evaluation_summary_tables.md の最新 3-seed Mean ± Std 集計テーブルを読み込み、
論文原稿 (secure-merge_統一比較評価論文_改訂版.md) の Appendix セクションを最新の内容で上書き更新する。
"""

import os
import re

source_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/evaluation_summary_tables.md"
target_file = "/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md"

if not os.path.exists(source_file):
    print(f"Error: {source_file} not found.")
    exit(1)

with open(source_file, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()

# セクションの自動切り出し
# 1. Alpha=0.6 手法間比較表 (safety+math, safety+code, safety+medical)
# 2. safety+math 手法別全 Alpha パラメータ一覧

sections = []

cur_title = None
cur_lines = []

for line in lines:
    if line.startswith("#### ドメインパターン:"):
        if cur_title and cur_lines:
            sections.append((cur_title, "\n".join(cur_lines)))
            cur_lines = []
        cur_title = line.strip()
    elif cur_title:
        cur_lines.append(line)

if cur_title and cur_lines:
    sections.append((cur_title, "\n".join(cur_lines)))

appendix_md = []
appendix_md.append("## Appendix: 詳細な評価指標およびパラメータスイープ結果\n")
appendix_md.append("本セクションでは、主要なドメインパターン（`safety+math`, `safety+code`, `safety+medical`）における全指標の比較表、および `safety+math` における各手法の $\\alpha$ パラメータスイープ結果の詳細を記載する。\n")

for title, body in sections:
    # 対象とするテーブルのフィルタリング
    if "safety+math+code+medical" in title:
        continue  # 4ドメイン同時マージは本論外
    
    # 1. Alpha=0.6 比較表
    if "比較表: Alpha=0.6" in title:
        pat_match = re.search(r"`(safety\+[a-z]+)`", title)
        pat_name = pat_match.group(1) if pat_match else ""
        appendix_md.append(f"### ドメインパターン: {pat_name} (Alpha=0.6 / 単一実行手法含む)\n")
        appendix_md.append(f"{title}\n")
        appendix_md.append(f"{body.strip()}\n")
    # 2. safety+math の αスイープ表
    elif "パターン: `safety+math`" in title:
        meth_match = re.search(r"手法: `([a-z_]+)`", title)
        meth_name = meth_match.group(1) if meth_match else ""
        appendix_md.append(f"### safety+math / {meth_name} (αスイープ)\n")
        appendix_md.append(f"{title}\n")
        appendix_md.append(f"{body.strip()}\n")

new_appendix_str = "\n".join(appendix_md)

# 対象論文原稿の読み込みと Appendix の置き換え
with open(target_file, "r", encoding="utf-8") as f:
    paper_text = f.read()

app_marker = "## Appendix: 詳細な評価指標およびパラメータスイープ結果"
if app_marker in paper_text:
    base_paper = paper_text.split(app_marker)[0].rstrip()
else:
    base_paper = paper_text.rstrip()

final_paper_text = base_paper + "\n\n---\n\n" + new_appendix_str + "\n"

with open(target_file, "w", encoding="utf-8") as f:
    f.write(final_paper_text)

print(f"[Success] Successfully updated Appendix in {target_file}")