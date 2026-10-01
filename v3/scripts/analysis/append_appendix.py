import os

source_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/evaluation_summary_tables.md"
target_file = "/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md"

with open(source_file, "r") as f:
    lines = f.readlines()

# 抽出したいセクションの行範囲（インデックスは行番号 - 1）
ranges = [
    (26, 40, "### ドメインパターン: safety+math (Alpha=0.6 / 単一実行手法含む)"),
    (42, 56, "### ドメインパターン: safety+code (Alpha=0.6 / 単一実行手法含む)"),
    (58, 72, "### ドメインパターン: safety+medical (Alpha=0.6 / 単一実行手法含む)"),
    (90, 100, "### safety+math / diagonal_sst_main (αスイープ)"),
    (140, 150, "### safety+math / data_free_sst_main (αスイープ)"),
    (190, 200, "### safety+math / ties (αスイープ)"),
    (240, 250, "### safety+math / dare (αスイープ)"),
    (290, 300, "### safety+math / della (αスイープ)"),
    (340, 350, "### safety+math / task_arithmetic (αスイープ)")
]

appendix_content = "\n\n---\n\n## Appendix: 詳細な評価指標およびパラメータスイープ結果\n\n"
appendix_content += "本セクションでは、主要なドメインパターン（`safety+math`, `safety+code`, `safety+medical`）における全指標の比較表、および `safety+math` における各手法の $\\alpha$ パラメータスイープ結果の詳細を記載する。\n\n"

for start, end, title in ranges:
    appendix_content += f"{title}\n\n"
    # 指定した行範囲を抽出して結合
    table_lines = lines[start:end]
    appendix_content += "".join(table_lines) + "\n\n"

# 論文ファイルの末尾に追記
with open(target_file, "a") as f:
    f.write(appendix_content)

print("Success! Appended appendix tables to the paper.")