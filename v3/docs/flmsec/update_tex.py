import re

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1 & 3: Table 13 caption and header
old_caption_13 = r"""\caption{メイン実験（vLLM）における主要merge手法の詳細評価指標（$\alpha=0.6$, $k=0.20$）}
\label{tab:evaluation_main_alpha=0.6}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Safety Ave [Original ASR] (ASR$\downarrow$ \%)} & \textbf{Conditional ASR} & \textbf{Valid Response Rate} & \textbf{Valid Safety Rate} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} \\"""

new_caption_13 = r"""\caption{メイン実験（vLLM）における主要merge手法の詳細評価指標（$\alpha=0.6$, $k=0.20$）。Safety Ave [Original ASR]およびSafety Ave [Conditional ASR]は、HarmBench、JailbreakBench、StrongReject、WildJailbreakにおけるマクロ平均である。Valid Response Rateは全安全性評価応答に占める有効応答の割合、Valid Safety Rateは全安全性評価応答に占める「有効かつ有害要求非追従」と判定された応答の割合である。MergeAlignは、生成出力の形式が本研究のGibberish判定および安全性評価パイプラインの前提を満たさず、全応答が無効（Valid Response Rateが0\%）となったため、Conditional ASRおよびValid Safety Rateは算出しない。Original ASRおよび有用性指標のみを参考値として報告する。}
\label{tab:evaluation_main_alpha=0.6}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Safety Ave [Original ASR] ($\downarrow$\%)} & \textbf{Safety Ave [Conditional ASR] ($\downarrow$\%)} & \textbf{Valid Response Rate ($\uparrow$\%)} & \textbf{Valid Safety Rate ($\uparrow$\%)} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} \\"""

text = text.replace(old_caption_13, new_caption_13)

# 2: Replace values in Table 13
with open('/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/new_vsr_results.txt', 'r', encoding='utf-8') as f:
    vsr_results = f.read()

# Extract Table 13 values
table13_replacements = []
in_t13 = False
for line in vsr_results.splitlines():
    if "LaTeX replacement values for Table 13:" in line:
        in_t13 = True
        continue
    if "LaTeX replacement values for Table 14:" in line:
        in_t13 = False
        continue
    if in_t13:
        if line.startswith("  % "):
            pat_meth = line[4:].split(" + ")
            pattern, method = pat_meth[0].strip(), pat_meth[1].strip()
            table13_replacements.append({"pattern": pattern, "method": method})
        elif "Conditional ASR =" in line:
            table13_replacements[-1]["ca"] = line.split("=")[1].strip()
        elif "Valid Response Rate =" in line:
            table13_replacements[-1]["vrr"] = line.split("=")[1].strip()
        elif "Valid Safety Rate =" in line:
            table13_replacements[-1]["vsr"] = line.split("=")[1].strip()

# Apply to text
for rep in table13_replacements:
    # Find the line starting with "pattern & method &"
    # Example: safety+code & dare & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 97.94 $\pm$ 2.76 & 100.00 $\pm$ 0.00 & ...
    pattern = rep['pattern']
    method = rep['method'].replace("_", "\\_")
    
    # We use regex to find the line and replace the 4th, 5th, 6th columns.
    # The line format is:
    # pattern & method & orig_asr & cond_asr & vrr & vsr & math & code & med & gen \\
    regex = re.compile(rf"^({re.escape(pattern)}\s*&\s*{re.escape(method)}\s*&\s*[^&]+&\s*)[^&]+(\s*&\s*)[^&]+(\s*&\s*)[^&]+(\s*&.*)$", re.MULTILINE)
    
    def replacer(match):
        return f"{match.group(1)}{rep['ca']}{match.group(2)}{rep['vrr']}{match.group(3)}{rep['vsr']}{match.group(4)}"
        
    text = regex.sub(replacer, text)


# 5 & 6: Table 14 Note column removal and values update
old_caption_14 = r"""\caption{メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\alpha=0.6$, $k=0.20$）}
\label{tab:evaluation_main_alpha=0.6_multi}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Safety Ave [Original ASR] (ASR$\downarrow$ \%)} & \textbf{Conditional ASR} & \textbf{Valid Response Rate} & \textbf{Valid Safety Rate} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} & \textbf{Note} \\
\midrule"""

new_caption_14 = r"""\caption{メイン実験（vLLM）における多重ドメインmergeの詳細評価指標（$\alpha=0.6$, $k=0.20$）。表中の多くの手法で極端なドメイン性能の低下（Partial collapse）やPPLの逸脱（PPL instability）といった有用性の激しい変動が観測された。このため、多重ドメインでの安定した統合は今後の課題として残る。}
\label{tab:evaluation_main_alpha=0.6_multi}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Safety Ave [Original ASR] ($\downarrow$\%)} & \textbf{Safety Ave [Conditional ASR] ($\downarrow$\%)} & \textbf{Valid Response Rate ($\uparrow$\%)} & \textbf{Valid Safety Rate ($\uparrow$\%)} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} \\
\midrule"""

text = text.replace(old_caption_14, new_caption_14)

# Replace values in Table 14
table14_replacements = []
in_t14 = False
for line in vsr_results.splitlines():
    if "LaTeX replacement values for Table 14:" in line:
        in_t14 = True
        continue
    if in_t14:
        if line.startswith("  % "):
            pat_meth = line[4:].split(" + ")
            pattern, method = pat_meth[0].strip(), pat_meth[1].strip()
            table14_replacements.append({"pattern": pattern, "method": method})
        elif "Conditional ASR =" in line:
            table14_replacements[-1]["ca"] = line.split("=")[1].strip()
        elif "Valid Response Rate =" in line:
            table14_replacements[-1]["vrr"] = line.split("=")[1].strip()
        elif "Valid Safety Rate =" in line:
            table14_replacements[-1]["vsr"] = line.split("=")[1].strip()

# Apply to text for Table 14 and remove Note column
for rep in table14_replacements:
    pattern = rep['pattern']
    method = rep['method'].replace("_", "\\_")
    
    # regex for table 14, 11 columns
    # pattern & method & orig & cond & vrr & vsr & math & code & med & gen & note \\
    regex = re.compile(rf"^({re.escape(pattern)}\s*&\s*{re.escape(method)}\s*&\s*[^&]+&\s*)[^&]+(\s*&\s*)[^&]+(\s*&\s*)[^&]+(\s*&\s*[^&]+\s*&\s*[^&]+\s*&\s*[^&]+\s*&\s*[^&]+)\s*&.*?$", re.MULTILINE)
    
    def replacer(match):
        return f"{match.group(1)}{rep['ca']}{match.group(2)}{rep['vrr']}{match.group(3)}{rep['vsr']}{match.group(4)} \\\\"
        
    text = regex.sub(replacer, text)


# 4: Alpha discrepancy
old_prelim = r"""\subsection{予備実験（Preliminary Experiment）結果}
小規模データセットを用いた基礎的なトレードオフ検証（予備実験）の結果については、付録\ref{app:preliminary_results}を参照されたい。ここで見られた偽の安全性（推論崩壊）の問題を踏まえ、次節以降の本実験ではより厳密な評価指標を導入する。"""

new_prelim = r"""\subsection{予備実験（Preliminary Experiment）結果}
予備実験は主実験とは異なる初期実装および評価パイプラインで実施した。したがって、予備実験における\(\alpha\)の定義および値を、主実験で定義した直接差分型Secure Mergeの\(\alpha\)と同一視しない。小規模データセットを用いた基礎的なトレードオフ検証（予備実験）の結果については、付録\ref{app:preliminary_results}を参照されたい。ここで見られた偽の安全性（推論崩壊）の問題を踏まえ、次節以降の本実験ではより厳密な評価指標を導入する。"""

text = text.replace(old_prelim, new_prelim)


# 7: Case Study Text
old_case = r"""\begin{quote}
本節は定量的な比較や手法間の優劣を示すものではなく、自動評価スコアのみでは区別しにくい安全拒否、部分的追従、反復出力、および入力再掲の具体例を示す定性的補助分析である。
\end{quote}"""

new_case = r"""\begin{quote}
本事例は定量比較ではなく、出力妥当性と有害要求への追従が自動評価スコアだけでは区別しにくいことを示す定性的補助分析である。
\end{quote}"""

text = text.replace(old_case, new_case)

# 8: PPL definition
old_ppl = r"""なお、PPLが極端に大きい条件は、専門データへの適合度が低いことに加え、merge後の出力分布の崩壊を反映する可能性がある。このため、PPLは通常の有用性比較だけでなく、モデル崩壊の補助的診断指標として解釈する。"""

new_ppl = r"""なお、PPLが極端に大きい条件は、専門データへの適合度が低いことに加え、merge後の出力分布の崩壊を反映する可能性がある。このため、PPLは通常の有用性比較だけでなく、モデル崩壊の補助的診断指標として解釈する。PPLの算出においては、各モデルの既定のtokenizer（Llama-2系等）を用い、sequence truncationを適用したうえで、padding部分は損失計算時のmask対象とし、chat templateは適用せずテキストの尤度として計算した。PPLが極端に高い（NaNやInfを含む）場合は、モデルの出力分布が完全に崩壊していると判定し、実質的な推論不可能状態として扱う。"""

text = text.replace(old_ppl, new_ppl)


# 9: AUC Text
old_auc = r"""表\ref{tab:auc_no_interpolation}は、手法ごとに観測されたValid Safety Rateの範囲が大きく異なることを示す。Endpoint-extended AUCは、観測範囲外の補完仮定に影響されるため、Observed-range AUCおよび\(s_{\min}, s_{\max}\)と併せて解釈する必要がある。本設定では、有効応答を保ちつつ高いValid Safety Rateを達成する挙動は、手法およびmerge強度に依存しており、単一のAUC値のみから一般的な優劣を結論づけることはできない。"""

new_auc = r"""表\ref{tab:auc_no_interpolation}は、手法ごとに観測されたValid Safety Rateの範囲が大きく異なることを示す。Endpoint-extended AUCは観測範囲外の補完仮定に影響されるため、Observed-range AUCおよびValid Safety Rateの観測範囲と併せて解釈する。本実験では、単一のAUC値に基づく一般的な手法順位づけは行わない。"""

text = text.replace(old_auc, new_auc)


with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done")
