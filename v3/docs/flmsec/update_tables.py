import re

with open("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Baseモデルの挿入
base_table = r"""
\begin{table}[H]
\centering
\caption{ベースモデル評価 集計 (Mean $\pm$ Std)}
\label{tab:base_models_app}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{lllrrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Alpha} & \textbf{Safety Ave [Harmful Content] (ASR$\downarrow$ \%)} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} & \textbf{EvolCode (PPL$\downarrow$)} & \textbf{MedAlpaca (PPL$\downarrow$)} \\
\midrule
Base (MedAlpaca) & Base (MedAlpaca) & N/A & 5.17 $\pm$ 0.00 & 4.53 $\pm$ 0.00 & 3.59 $\pm$ 0.00 & 52.81 $\pm$ 0.00 & 20.28 $\pm$ 0.00 & 2.32 $\pm$ 0.00 & 5.71 $\pm$ 2.88 \\
Base (SafetyFT) & Base (SafetyFT) & N/A & 0.00 $\pm$ 0.00 & 0.52 $\pm$ 0.48 & 4.22 $\pm$ 3.39 & 43.49 $\pm$ 11.80 & 11.38 $\pm$ 0.41 & 2.34 $\pm$ 0.03 & N/A \\
Base (WizardCoder) & Base (WizardCoder) & N/A & 24.69 $\pm$ 0.00 & 4.53 $\pm$ 0.00 & 21.03 $\pm$ 0.00 & 54.53 $\pm$ 0.00 & 18.41 $\pm$ 0.00 & 1.54 $\pm$ 0.00 & 3.72 $\pm$ 0.00 \\
Base (WizardMath) & Base (WizardMath) & N/A & 31.01 $\pm$ 0.00 & 6.41 $\pm$ 0.00 & 3.12 $\pm$ 0.00 & 55.00 $\pm$ 0.00 & 14.02 $\pm$ 0.00 & 2.03 $\pm$ 0.00 & 2.77 $\pm$ 0.00 \\
\bottomrule
\end{tabular}
}
\end{table}

\subsection{予備実験（Preliminary Experiment）結果}"""

content = content.replace(r"\subsection{予備実験（Preliminary Experiment）結果}", base_table, 1)

# 2. tab:prelim_detail_app の置換
new_prelim_table = r"""\begin{table}[H]
\centering
\caption{予備実験（TrustLLM / BeaverTails）における安全性と有用性の評価（詳細再掲）}
\label{tab:prelim_detail_app}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{TrustLLM Raw ASR (ASR$\downarrow$ \%)} & \textbf{Gibberish Ratio (崩壊率$\uparrow$ \%)} & \textbf{BeaverTails Utility (Score$\uparrow$ \%)} \\
\midrule
safety+code & Base & 0.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+code & dare & 100.00 $\pm$ 0.00 & 36.35 $\pm$ 12.66 & 64.06 $\pm$ 11.87 \\
safety+code & data\_free\_sst\_main & 92.60 $\pm$ 2.90 & 64.38 $\pm$ 1.13 & 27.40 $\pm$ 3.77 \\
safety+code & della & 100.00 $\pm$ 0.00 & 33.65 $\pm$ 8.21 & 67.19 $\pm$ 5.42 \\
safety+code & diagonal\_sst\_main & 98.12 $\pm$ 1.65 & 76.77 $\pm$ 3.31 & 19.58 $\pm$ 2.90 \\
safety+code & led\_merging & 87.19 $\pm$ 0.00 & 95.94 $\pm$ 0.00 & 5.00 $\pm$ 0.00 \\
safety+code & matena\_fisher & 95.62 $\pm$ 1.13 & 71.98 $\pm$ 1.57 & 28.33 $\pm$ 2.22 \\
safety+code & mergealign & 100.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+code & safemerge & 4.58 $\pm$ 5.81 & 6.25 $\pm$ 10.56 & 2.81 $\pm$ 2.19 \\
safety+code & task\_arithmetic & 82.40 $\pm$ 2.73 & 56.67 $\pm$ 4.07 & 24.38 $\pm$ 3.29 \\
safety+code & ties & 99.38 $\pm$ 0.31 & 62.29 $\pm$ 6.59 & 34.58 $\pm$ 2.37 \\
safety+math & Base & 0.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+math & dare & 17.19 $\pm$ 0.83 & 18.65 $\pm$ 0.95 & 9.69 $\pm$ 2.86 \\
safety+math & data\_free\_sst\_main & 36.88 $\pm$ 3.25 & 36.04 $\pm$ 4.24 & 21.15 $\pm$ 0.36 \\
safety+math & della & 19.06 $\pm$ 3.17 & 20.62 $\pm$ 5.20 & 7.81 $\pm$ 2.05 \\
safety+math & diagonal\_sst\_main & 24.38 $\pm$ 1.74 & 58.44 $\pm$ 5.94 & 12.81 $\pm$ 2.44 \\
safety+math & led\_merging & 87.19 $\pm$ 0.00 & 96.15 $\pm$ 0.18 & 5.00 $\pm$ 0.00 \\
safety+math & matena\_fisher & 19.79 $\pm$ 1.18 & 67.19 $\pm$ 3.52 & 10.00 $\pm$ 1.65 \\
safety+math & mergealign & 100.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+math & safemerge & 14.27 $\pm$ 22.55 & 31.15 $\pm$ 53.95 & 3.33 $\pm$ 3.34 \\
safety+math & task\_arithmetic & 9.69 $\pm$ 0.31 & 47.92 $\pm$ 18.35 & 6.35 $\pm$ 1.91 \\
safety+math & ties & 18.65 $\pm$ 4.77 & 36.67 $\pm$ 4.77 & 11.25 $\pm$ 1.08 \\
safety+math+code+medical & Base & 0.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+math+code+medical & dare & 100.00 $\pm$ 0.00 & 70.42 $\pm$ 40.72 & 31.46 $\pm$ 41.41 \\
safety+math+code+medical & data\_free\_sst\_main & 95.73 $\pm$ 6.35 & 84.79 $\pm$ 18.14 & 15.62 $\pm$ 15.77 \\
safety+math+code+medical & della & 100.00 $\pm$ 0.00 & 73.65 $\pm$ 24.63 & 28.65 $\pm$ 26.34 \\
safety+math+code+medical & diagonal\_sst\_main & 97.29 $\pm$ 2.01 & 95.31 $\pm$ 2.19 & 5.10 $\pm$ 0.48 \\
safety+math+code+medical & matena\_fisher & 100.00 $\pm$ 0.00 & 80.10 $\pm$ 0.18 & 16.56 $\pm$ 1.36 \\
safety+math+code+medical & task\_arithmetic & 66.25 $\pm$ 11.12 & 70.73 $\pm$ 14.23 & 4.90 $\pm$ 1.44 \\
safety+math+code+medical & ties & 100.00 $\pm$ 0.00 & 40.94 $\pm$ 49.27 & 60.21 $\pm$ 50.93 \\
safety+medical & Base & 0.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+medical & dare & 70.21 $\pm$ 51.60 & 63.75 $\pm$ 44.93 & 36.56 $\pm$ 44.96 \\
safety+medical & data\_free\_sst\_main & 100.00 $\pm$ 0.00 & 69.69 $\pm$ 15.86 & 27.40 $\pm$ 10.79 \\
safety+medical & della & 99.90 $\pm$ 0.18 & 70.83 $\pm$ 30.45 & 31.77 $\pm$ 32.89 \\
safety+medical & diagonal\_sst\_main & 100.00 $\pm$ 0.00 & 38.85 $\pm$ 53.60 & 59.58 $\pm$ 52.21 \\
safety+medical & matena\_fisher & 100.00 $\pm$ 0.00 & 62.19 $\pm$ 53.64 & 37.50 $\pm$ 53.89 \\
safety+medical & mergealign & 100.00 $\pm$ 0.00 & 100.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 \\
safety+medical & safemerge & 3.02 $\pm$ 0.18 & 0.00 $\pm$ 0.00 & 2.60 $\pm$ 1.83 \\
safety+medical & task\_arithmetic & 100.00 $\pm$ 0.00 & 97.60 $\pm$ 2.60 & 1.77 $\pm$ 2.01 \\
safety+medical & ties & 100.00 $\pm$ 0.00 & 88.96 $\pm$ 9.58 & 11.15 $\pm$ 9.45 \\
\bottomrule
\end{tabular}
}
\end{table}"""

import re
# re.sub で repl を関数にすればエスケープを無視できる
content = re.sub(r"\\begin\{table\}\[H\]\n\\centering\n\\caption\{予備実験（TrustLLM / BeaverTails）における安全性と有用性の評価（詳細再掲）\}.*?\\end\{table\}", lambda _: new_prelim_table, content, flags=re.DOTALL)


# 3. tab:evaluation_main_alpha=0.6 の置換
new_main_table = r"""\begin{table}[H]
\centering
\caption{メイン実験（vLLM）における主要merge手法の詳細評価指標（$\alpha=0.6$, $k=0.20$）}
\label{tab:evaluation_main_alpha=0.6}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{llrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Safety Ave [Harmful Content] (ASR$\downarrow$ \%)} & \textbf{Math Ave (\%)} & \textbf{Code Ave (\%)} & \textbf{Medical Ave (\%)} & \textbf{General/Inst Ave (\%)} \\
\midrule
Base (MedAlpaca) & Base (MedAlpaca) & 5.17 $\pm$ 0.00 & 4.53 $\pm$ 0.00 & 3.59 $\pm$ 0.00 & 52.81 $\pm$ 0.00 & 20.28 $\pm$ 0.00 \\
Base (SafetyFT) & Base (SafetyFT) & 0.00 $\pm$ 0.00 & 0.52 $\pm$ 0.48 & 4.22 $\pm$ 3.39 & 43.49 $\pm$ 11.80 & 11.38 $\pm$ 0.41 \\
Base (WizardCoder) & Base (WizardCoder) & 24.69 $\pm$ 0.00 & 4.53 $\pm$ 0.00 & 21.03 $\pm$ 0.00 & 54.53 $\pm$ 0.00 & 18.41 $\pm$ 0.00 \\
Base (WizardMath) & Base (WizardMath) & 31.01 $\pm$ 0.00 & 6.41 $\pm$ 0.00 & 3.12 $\pm$ 0.00 & 55.00 $\pm$ 0.00 & 14.02 $\pm$ 0.00 \\
safety+code & dare & 0.00 $\pm$ 0.00 & 0.05 $\pm$ 0.09 & 0.00 $\pm$ 0.00 & 29.58 $\pm$ 12.27 & 11.73 $\pm$ 0.70 \\
safety+code & data\_free\_sst\_main & 0.03 $\pm$ 0.05 & 0.21 $\pm$ 0.24 & 0.00 $\pm$ 0.00 & 78.75 $\pm$ 2.48 & 14.07 $\pm$ 0.05 \\
safety+code & della & 0.00 $\pm$ 0.00 & 0.62 $\pm$ 0.41 & 0.00 $\pm$ 0.00 & 43.54 $\pm$ 14.08 & 12.43 $\pm$ 0.46 \\
safety+code & diagonal\_sst\_main & 0.97 $\pm$ 0.42 & 0.89 $\pm$ 0.24 & 0.00 $\pm$ 0.00 & 86.25 $\pm$ 0.31 & 12.26 $\pm$ 0.55 \\
safety+code & led\_merging & 2.88 $\pm$ 0.14 & 1.41 $\pm$ 0.00 & 5.62 $\pm$ 0.00 & 83.75 $\pm$ 0.00 & 22.49 $\pm$ 0.04 \\
safety+code & matena\_fisher & 3.37 $\pm$ 1.40 & 1.09 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 83.12 $\pm$ 0.31 & 12.77 $\pm$ 0.37 \\
safety+code & mergealign & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 86.25 $\pm$ 0.00 & 15.73 $\pm$ 3.41 \\
safety+code & safemerge & 0.10 $\pm$ 0.18 & 1.51 $\pm$ 1.33 & 5.99 $\pm$ 5.39 & 73.75 $\pm$ 2.98 & 19.84 $\pm$ 8.02 \\
safety+code & task\_arithmetic & 29.17 $\pm$ 3.07 & 2.97 $\pm$ 0.68 & 4.63 $\pm$ 0.09 & 88.85 $\pm$ 0.79 & 17.39 $\pm$ 0.39 \\
safety+code & ties & 0.11 $\pm$ 0.04 & 1.41 $\pm$ 0.47 & 0.00 $\pm$ 0.00 & 38.65 $\pm$ 26.32 & 17.85 $\pm$ 9.81 \\
safety+math & dare & 6.14 $\pm$ 5.14 & 5.42 $\pm$ 0.79 & 5.00 $\pm$ 1.02 & 84.27 $\pm$ 2.35 & 22.85 $\pm$ 8.57 \\
safety+math & data\_free\_sst\_main & 14.73 $\pm$ 3.41 & 5.57 $\pm$ 0.24 & 7.19 $\pm$ 4.33 & 69.38 $\pm$ 13.52 & 24.69 $\pm$ 0.38 \\
safety+math & della & 6.66 $\pm$ 5.52 & 5.52 $\pm$ 0.63 & 5.31 $\pm$ 1.36 & 85.62 $\pm$ 0.54 & 31.03 $\pm$ 4.06 \\
safety+math & diagonal\_sst\_main & 17.09 $\pm$ 5.01 & 6.82 $\pm$ 0.86 & 6.72 $\pm$ 0.95 & 72.55 $\pm$ 15.91 & 22.48 $\pm$ 8.92 \\
safety+math & led\_merging & 2.80 $\pm$ 0.00 & 1.41 $\pm$ 0.00 & 5.62 $\pm$ 0.00 & 83.75 $\pm$ 0.00 & 22.51 $\pm$ 0.02 \\
safety+math & matena\_fisher & 4.29 $\pm$ 0.43 & 6.04 $\pm$ 0.86 & 6.61 $\pm$ 0.39 & 85.73 $\pm$ 0.65 & 26.72 $\pm$ 11.70 \\
safety+math & mergealign & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 86.25 $\pm$ 0.00 & 15.73 $\pm$ 3.41 \\
safety+math & safemerge & 4.61 $\pm$ 7.99 & 1.30 $\pm$ 0.86 & 6.67 $\pm$ 4.86 & 82.50 $\pm$ 1.74 & 13.09 $\pm$ 1.77 \\
safety+math & task\_arithmetic & 2.48 $\pm$ 2.89 & 6.88 $\pm$ 1.56 & 7.50 $\pm$ 0.68 & 75.21 $\pm$ 15.93 & 27.18 $\pm$ 6.92 \\
safety+math & ties & 9.03 $\pm$ 5.55 & 5.94 $\pm$ 0.83 & 6.15 $\pm$ 0.18 & 85.00 $\pm$ 2.44 & 27.65 $\pm$ 3.07 \\
safety+math+code+medical & dare & 0.08 $\pm$ 0.08 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 38.02 $\pm$ 41.77 & 11.53 $\pm$ 0.23 \\
safety+math+code+medical & data\_free\_sst\_main & 0.08 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 26.67 $\pm$ 24.56 & 11.85 $\pm$ 0.59 \\
safety+math+code+medical & della & 0.08 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 15.42 $\pm$ 16.18 & 12.53 $\pm$ 0.78 \\
safety+math+code+medical & diagonal\_sst\_main & 0.00 $\pm$ 0.00 & 0.42 $\pm$ 0.18 & 0.00 $\pm$ 0.00 & 57.29 $\pm$ 17.67 & 10.16 $\pm$ 0.49 \\
safety+math+code+medical & matena\_fisher & 0.00 $\pm$ 0.00 & 0.99 $\pm$ 0.24 & 0.00 $\pm$ 0.00 & 27.81 $\pm$ 3.29 & 13.12 $\pm$ 0.12 \\
safety+math+code+medical & task\_arithmetic & 5.88 $\pm$ 0.55 & 2.55 $\pm$ 0.39 & 0.05 $\pm$ 0.09 & 65.42 $\pm$ 9.24 & 13.26 $\pm$ 1.65 \\
safety+math+code+medical & ties & 0.05 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 9.17 $\pm$ 7.94 & 12.28 $\pm$ 0.40 \\
safety+medical & dare & 0.03 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 22.08 $\pm$ 10.81 & 12.39 $\pm$ 0.44 \\
safety+medical & data\_free\_sst\_main & 0.05 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 61.67 $\pm$ 41.50 & 12.27 $\pm$ 0.07 \\
safety+medical & della & 0.03 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 27.29 $\pm$ 23.45 & 12.10 $\pm$ 1.01 \\
safety+medical & diagonal\_sst\_main & 0.05 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 9.69 $\pm$ 8.46 & 12.06 $\pm$ 0.13 \\
safety+medical & matena\_fisher & 0.16 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 12.99 $\pm$ 0.18 \\
safety+medical & mergealign & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 86.25 $\pm$ 0.00 & 13.76 $\pm$ 3.41 \\
safety+medical & safemerge & 0.03 $\pm$ 0.05 & 1.09 $\pm$ 1.89 & 3.91 $\pm$ 6.77 & 53.44 $\pm$ 10.84 & 12.81 $\pm$ 1.63 \\
safety+medical & task\_arithmetic & 0.16 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 13.85 $\pm$ 0.18 & 12.72 $\pm$ 0.06 \\
safety+medical & ties & 0.05 $\pm$ 0.05 & 0.00 $\pm$ 0.00 & 0.00 $\pm$ 0.00 & 13.54 $\pm$ 0.36 & 11.90 $\pm$ 0.62 \\
\bottomrule
\end{tabular}
}
\end{table}"""

content = re.sub(r"\\begin\{table\}\[H\]\n\\centering\n\\caption\{メイン実験（vLLM）における主要merge手法の詳細評価指標（\$\\alpha=0.6\$, \$k=0.20\$）\}.*?\\end\{table\}", lambda _: new_main_table, content, flags=re.DOTALL)


with open("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated successfully!")
