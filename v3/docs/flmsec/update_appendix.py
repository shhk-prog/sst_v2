import re

# flmsec.tex の読み込み
with open("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex", "r", encoding="utf-8") as f:
    tex_content = f.read()

# flmsec_hyo_vllm_latex.md の読み込み
with open("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_hyo_vllm_latex.md", "r", encoding="utf-8") as f:
    vllm_content = f.read()

# vLLMの表ファイルから、"1. 予備実験" 以降のすべてを抽出する
# （0. 簡易まとめ表は不要）
match_vllm = re.search(r"(% --------------------------------------------------------------------------\n% 1\. 予備実験 \(Preliminary Experiments\).*)$", vllm_content, re.DOTALL)
if not match_vllm:
    print("Could not find start of section 1 in vLLM file")
    exit(1)

vllm_tables = match_vllm.group(1)

# tex ファイルの 1411行目 (\newpage) あたりから \end{document} の前までを切り出す。
# コメントで "% ==========================================================================" などがあるのでそこを基準にする
match_tex = re.search(r"(\\newpage\s*% ==========================================================================\s*% SST-Merge LaTeX表一覧.*?)(\\end\{document\})", tex_content, re.DOTALL)
if not match_tex:
    print("Could not find target block in flmsec.tex")
    # 代替手段: \newpage 以降を置換してみる
    match_tex2 = re.search(r"(\\newpage\s*% ==========================================================================.*?)(?=\\end\{document\})", tex_content, re.DOTALL)
    if not match_tex2:
        print("Still could not find it.")
        exit(1)

# 置換するコンテンツの作成
replacement = "\\newpage\n" + vllm_tables + "\n"

# tex ファイルを置換
new_tex_content = re.sub(r"\\newpage\s*% ==========================================================================\s*% SST-Merge LaTeX表一覧.*?(?=\\end\{document\})", lambda _: replacement, tex_content, flags=re.DOTALL)

with open("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex", "w", encoding="utf-8") as f:
    f.write(new_tex_content)

print("Replaced appendix tables with vLLM tables successfully.")
