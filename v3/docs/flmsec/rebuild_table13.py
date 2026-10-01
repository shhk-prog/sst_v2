import re

def parse_replacements(filepath):
    replacements = {}
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    current_key = None
    for line in lines:
        line = line.strip()
        if line.startswith("% safety+"):
            parts = line[2:].split(" + ")
            if len(parts) == 2:
                current_key = (parts[0].strip(), parts[1].strip())
                replacements[current_key] = {}
        elif "=" in line and current_key:
            k, v = line.split("=", 1)
            replacements[current_key][k.strip()] = v.strip()
    return replacements

repls = parse_replacements('/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/new_vsr_results.txt')

# We need the Original ASR, Math Ave, Code Ave, Medical Ave, General Ave.
# Where do we get them? We can just read them from `flmsec_0818.tex` Table 13!
with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_0818.tex', 'r', encoding='utf-8') as f:
    text_0818 = f.read()

match_old = re.search(r"(\\begin\{table\}\[H\]\n\\centering\n\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6\}.*?\\end\{table\})", text_0818, re.DOTALL)
if match_old:
    table_old = match_old.group(1)
    lines_old = table_old.split('\n')
    
    table_a_lines = []
    table_b_lines = []
    
    for line in lines_old:
        if line.startswith("\\begin{tabular}"):
            table_a_lines.append("\\begin{tabular}{llrrrr}")
            table_b_lines.append("\\begin{tabular}{llrrrr}")
        elif "&" in line and "\\textbf{" in line:
            table_a_lines.append("\\textbf{Pattern} & \\textbf{Method} & \\textbf{Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)} & \\textbf{Safety Ave [Conditional ASR] (ASR$\\downarrow$ \\%)} & \\textbf{Valid Response Rate (\\%)} & \\textbf{Valid Safety Rate (\\%)} \\\\")
            table_b_lines.append("\\textbf{Pattern} & \\textbf{Method} & \\textbf{Math Ave (\\%)} & \\textbf{Code Ave (\\%)} & \\textbf{Medical Ave (\\%)} & \\textbf{General/Inst Ave (\\%)} \\\\")
        elif "&" in line and not line.strip().startswith("%"):
            parts = [p.strip() for p in line.split("&")]
            if len(parts) >= 7:
                pattern = parts[0]
                method = parts[1]
                o_asr = parts[2]
                math = parts[3]
                code = parts[4]
                med = parts[5]
                gen = parts[6]
                if gen.endswith("\\\\"):
                    gen = gen[:-2].strip()
                    
                if "Base" in pattern or "Base" in method:
                    ca = "---"
                    vrr = "---"
                    vsr = "---"
                else:
                    key = (pattern.replace("\\_", "_"), method.replace("\\_", "_"))
                    if key in repls:
                        ca = repls[key]["Conditional ASR"]
                        vrr = repls[key]["Valid Response Rate"]
                        vsr = repls[key]["Valid Safety Rate"]
                    else:
                        ca = "---"
                        vrr = "---"
                        vsr = "---"
                        
                table_a_lines.append(f"{pattern} & {method} & {o_asr} & {ca} & {vrr} & {vsr} \\\\")
                table_b_lines.append(f"{pattern} & {method} & {math} & {code} & {med} & {gen} \\\\")
            else:
                table_a_lines.append(line)
                table_b_lines.append(line)
        else:
            if "\\caption{" in line:
                # Need to update the caption for Table A
                new_caption = line.replace("詳細評価指標（$\\alpha=0.6$, $k=0.20$）。", "詳細評価指標 (Safety diagnostics)（$\\alpha=0.6$, $k=0.20$）。")
                # Ensure the MergeAlign text and Valid Safety Rate text are present
                if "MergeAlign" not in new_caption:
                    new_caption = new_caption.replace("マクロ平均である。", "マクロ平均である。Valid Response Rateは全安全性評価応答に占める有効応答の割合、Valid Safety Rateは全安全性評価応答に占める「有効かつ有害要求非追従」と判定された応答の割合である。MergeAlignは、生成出力の形式が本研究のGibberish判定および安全性評価パイプラインの前提を満たさず、全応答が無効（Valid Response Rateが0\\%）となったため、Conditional ASRおよびValid Safety Rateは算出しない。Original ASRおよび有用性指標のみを参考値として報告する。Valid Safety Rateは各seedおよび各ベンチマークについて先に算出し、その後にベンチマーク平均およびseed間平均・標準偏差を計算した。")
                table_a_lines.append(new_caption)
                
                new_caption_b = line.replace("詳細評価指標（$\\alpha=0.6$, $k=0.20$）。", "詳細評価指標 (Utility)（$\\alpha=0.6$, $k=0.20$）。")
                # Remove safety metric defs from B
                new_caption_b = re.sub(r"Safety Ave.*?マクロ平均である。", "", new_caption_b)
                table_b_lines.append(new_caption_b)
            elif "\\label{" in line:
                table_a_lines.append(line.replace("tab:evaluation_main_alpha=0.6", "tab:evaluation_main_alpha=0.6_safety"))
                table_b_lines.append(line.replace("tab:evaluation_main_alpha=0.6", "tab:evaluation_main_alpha=0.6_utility"))
            else:
                table_a_lines.append(line)
                table_b_lines.append(line)
                
    table_a_text = "\n".join(table_a_lines)
    table_b_text = "\n".join(table_b_lines)
    
    with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Replace the current Table A and Table B in text
    # First remove Table B, then replace Table A with Table A \n\n Table B
    match_a = re.search(r"(\\begin\{table\}\[H\]\s*\\centering\s*\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6_safety\}.*?\\end\{table\})", text, re.DOTALL)
    match_b = re.search(r"(\\begin\{table\}\[H\]\s*\\centering\s*\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6_utility\}.*?\\end\{table\})", text, re.DOTALL)
    
    if match_a and match_b:
        text = text.replace(match_b.group(1), "")
        text = text.replace(match_a.group(1), table_a_text + "\n\n" + table_b_text)
        
        with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully rebuilt Table 13 A and B from 0818.")
    else:
        print("Could not find current Table A or Table B.")
