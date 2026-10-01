import re

filepath = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.md"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

table_cost = r"""\begin{table}[htbp]
\caption{各merge手法の理論的計算コストとデータ要件の比較}
\label{tab:cost}
\centering
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabularx}{\textwidth}{
>{\raggedright\arraybackslash}p{2.6cm}
>{\centering\arraybackslash}p{2.3cm}
>{\centering\arraybackslash}X
>{\centering\arraybackslash}p{1.9cm}
>{\centering\arraybackslash}X
}
\toprule
\textbf{Method} & \textbf{Calibration Data} & \textbf{FIM / Mask Calc.} & \textbf{Merge Execution} & \textbf{Total Time Complexity} \\
\midrule
\texttt{diagonal\_sst\_main} & Yes ($N$ samples) & $\mathcal{O}(N \cdot C_{\text{backward}})$ & $\mathcal{O}(P)$ & $\mathcal{O}(N \cdot C_{\text{backward}} + P)$ \\
\texttt{data\_free\_sst\_main} & No & None & $\mathcal{O}(P)$ & $\mathcal{O}(P)$ \\
\texttt{ties} & No & None & $\mathcal{O}(P)$ & $\mathcal{O}(P)$ \\
\texttt{dare} & No & None & $\mathcal{O}(P)$ & $\mathcal{O}(P)$ \\
\texttt{della} & No & None & $\mathcal{O}(P)$ & $\mathcal{O}(P)$ \\
\texttt{task\_arithmetic} & No & None & $\mathcal{O}(P)$ & $\mathcal{O}(P)$ \\
\bottomrule
\end{tabularx}
\end{table}"""

table_gpu = r"""\begin{table}[htbp]
\caption{各マージ手法の実測マージ時間とピークGPUメモリ（平均）}
\label{tab:gpu}
\centering
\small
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabularx}{\textwidth}{
>{\raggedright\arraybackslash}X
>{\centering\arraybackslash}p{3.4cm}
>{\centering\arraybackslash}p{3.4cm}
}
\toprule
\textbf{Method} & \textbf{Average Merge Time (s) $\downarrow$} & \textbf{Peak GPU Memory (GB) $\downarrow$} \\
\midrule
\texttt{data\_free\_sst\_main} & \textbf{107} & \textbf{0.00} \\
\texttt{diagonal\_sst\_main} & 596 & 24.50 \\
\texttt{dare} & 1003 & 0.00 \\
\texttt{ties} & 2179 & 0.00 \\
\texttt{della} & 1205 & 0.00 \\
\texttt{task\_arithmetic} & 115 & 0.00 \\
\bottomrule
\end{tabularx}
\end{table}"""

# Replace first table (tab:cost)
old_cost_table = r"""\begin{table}[H]
\centering
\caption{各マージ手法の理論的計算コストとデータ要件の比較}
\label{tab:cost}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{p{2.0cm}p{3.3cm}lp{2.2cm}}
\end{tabular}
}
\end{table}"""
content = content.replace(old_cost_table, table_cost)

# Replace second table (tab:gpu)
old_gpu_table = r"""\begin{table}[H]
\centering
\caption{各マージ手法の実測マージ時間とピークGPUメモリ(平均)}
\label{tab:gpu}
\small
\resizebox{\textwidth}{!}{
\begin{tabular}{p{2.0cm}p{3.3cm}ll}
\end{tabular}
}
\end{table}"""
content = content.replace(old_gpu_table, table_gpu)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Cost tables injected into flmsec.md")