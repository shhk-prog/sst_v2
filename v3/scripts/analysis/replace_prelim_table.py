table_str = """\\begin{tabular}{\\textwidth}{llcrrr}
\\toprule
\\textbf{Pattern} & \\textbf{Method} & \\textbf{Alpha} & \\textbf{TrustLLM Raw ASR ($\\downarrow$ \\%)} & \\textbf{Gibberish Ratio ($\\uparrow$ \\%)} & \\textbf{BeaverTails Utility ($\\uparrow$ \\%)} \\\\
\\midrule
safety+code & Base & - & 0.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+code & \\texttt{dare} & 0.6 & 100.00 $\\pm$ 0.00 & 36.35 $\\pm$ 12.66 & 64.06 $\\pm$ 11.87 \\\\
safety+code & \\texttt{data\\_free\\_sst\\_main} & 0.6 & 92.60 $\\pm$ 2.90 & 64.38 $\\pm$ 1.13 & 27.40 $\\pm$ 3.77 \\\\
safety+code & \\texttt{della} & 0.6 & 100.00 $\\pm$ 0.00 & 33.65 $\\pm$ 8.21 & 67.19 $\\pm$ 5.42 \\\\
safety+code & \\texttt{diagonal\\_sst\\_main} & 0.6 & 98.12 $\\pm$ 1.65 & 76.77 $\\pm$ 3.31 & 19.58 $\\pm$ 2.90 \\\\
safety+code & \\texttt{led\\_merging} & - & 87.19 $\\pm$ 0.00 & 95.94 $\\pm$ 0.00 & 5.00 $\\pm$ 0.00 \\\\
safety+code & \\texttt{matena\\_fisher} & - & 95.62 $\\pm$ 1.13 & 71.98 $\\pm$ 1.57 & 28.33 $\\pm$ 2.22 \\\\
safety+code & \\texttt{mergealign} & - & 100.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+code & \\texttt{safemerge} & - & 4.58 $\\pm$ 5.81 & 6.25 $\\pm$ 10.56 & 2.81 $\\pm$ 2.19 \\\\
safety+code & \\texttt{task\\_arithmetic} & 0.6 & 82.40 $\\pm$ 2.73 & 56.67 $\\pm$ 4.07 & 24.38 $\\pm$ 3.29 \\\\
safety+code & \\texttt{ties} & 0.6 & 99.38 $\\pm$ 0.31 & 62.29 $\\pm$ 6.59 & 34.58 $\\pm$ 2.37 \\\\
\\midrule
safety+math & Base & - & 0.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+math & \\texttt{dare} & 0.6 & 17.19 $\\pm$ 0.83 & 18.65 $\\pm$ 0.95 & 9.69 $\\pm$ 2.86 \\\\
safety+math & \\texttt{data\\_free\\_sst\\_main} & 0.6 & 36.88 $\\pm$ 3.25 & 36.04 $\\pm$ 4.24 & 21.15 $\\pm$ 0.36 \\\\
safety+math & \\texttt{della} & 0.6 & 19.06 $\\pm$ 3.17 & 20.62 $\\pm$ 5.20 & 7.81 $\\pm$ 2.05 \\\\
safety+math & \\texttt{diagonal\\_sst\\_main} & 0.6 & 24.38 $\\pm$ 1.74 & 58.44 $\\pm$ 5.94 & 12.81 $\\pm$ 2.44 \\\\
safety+math & \\texttt{led\\_merging} & - & 87.19 $\\pm$ 0.00 & 96.15 $\\pm$ 0.18 & 5.00 $\\pm$ 0.00 \\\\
safety+math & \\texttt{matena\\_fisher} & - & 19.79 $\\pm$ 1.18 & 67.19 $\\pm$ 3.52 & 10.00 $\\pm$ 1.65 \\\\
safety+math & \\texttt{mergealign} & - & 100.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+math & \\texttt{safemerge} & - & 14.27 $\\pm$ 22.55 & 31.15 $\\pm$ 53.95 & 3.33 $\\pm$ 3.34 \\\\
safety+math & \\texttt{task\\_arithmetic} & 0.6 & 9.69 $\\pm$ 0.31 & 47.92 $\\pm$ 18.35 & 6.35 $\\pm$ 1.91 \\\\
safety+math & \\texttt{ties} & 0.6 & 18.65 $\\pm$ 4.77 & 36.67 $\\pm$ 4.77 & 11.25 $\\pm$ 1.08 \\\\
\\midrule
safety+medical & Base & - & 0.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+medical & \\texttt{dare} & 0.6 & 70.21 $\\pm$ 51.60 & 63.75 $\\pm$ 44.93 & 36.56 $\\pm$ 44.96 \\\\
safety+medical & \\texttt{data\\_free\\_sst\\_main} & 0.6 & 100.00 $\\pm$ 0.00 & 69.69 $\\pm$ 15.86 & 27.40 $\\pm$ 10.79 \\\\
safety+medical & \\texttt{della} & 0.6 & 99.90 $\\pm$ 0.18 & 70.83 $\\pm$ 30.45 & 31.77 $\\pm$ 32.89 \\\\
safety+medical & \\texttt{diagonal\\_sst\\_main} & 0.6 & 100.00 $\\pm$ 0.00 & 38.85 $\\pm$ 53.60 & 59.58 $\\pm$ 52.21 \\\\
safety+medical & \\texttt{matena\\_fisher} & - & 100.00 $\\pm$ 0.00 & 62.19 $\\pm$ 53.64 & 37.50 $\\pm$ 53.89 \\\\
safety+medical & \\texttt{mergealign} & - & 100.00 $\\pm$ 0.00 & 100.00 $\\pm$ 0.00 & 0.00 $\\pm$ 0.00 \\\\
safety+medical & \\texttt{safemerge} & - & 3.02 $\\pm$ 0.18 & 0.00 $\\pm$ 0.00 & 2.60 $\\pm$ 1.83 \\\\
safety+medical & \\texttt{task\\_arithmetic} & 0.6 & 100.00 $\\pm$ 0.00 & 97.60 $\\pm$ 2.60 & 1.77 $\\pm$ 2.01 \\\\
safety+medical & \\texttt{ties} & 0.6 & 100.00 $\\pm$ 0.00 & 88.96 $\\pm$ 9.58 & 11.15 $\\pm$ 9.45 \\\\
\\bottomrule
\\end{tabularx}"""

import re

path = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.md"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# find the tabular environment for the preliminary experiment table
match = re.search(r"\\begin\{tabular\}\{\\textwidth\}\{llrrr\}.*?\\end\{tabular\}", content, re.DOTALL)
if match:
    new_content = content[:match.start()] + table_str + content[match.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Preliminary table replaced successfully.")
else:
    print("Could not find the preliminary table to replace.")