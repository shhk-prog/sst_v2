import re

# Read the original good file
with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_0818.tex', 'r', encoding='utf-8') as f:
    text_0818 = f.read()

# Read the current file
with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
    text_current = f.read()

start_marker = r"% 1. 予備実験 \(Preliminary Experiments\)"
end_marker = r"% 2. メイン実験 \(Main Experiments\)"

match_0818 = re.search(f"({start_marker}.*?)({end_marker})", text_0818, re.DOTALL)
if match_0818:
    prelim_text = match_0818.group(1)
    
    # Unified headers replacement
    old_header1 = r"\textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio (\%)} & \textbf{BeaverTails Utility Score (\%)}"
    new_header = r"\textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio ($\downarrow$\%)} & \textbf{BeaverTails Utility Score ($\uparrow$\%)}"
    prelim_text = prelim_text.replace(old_header1, new_header)
    
    old_header2 = r"\textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio ($\downarrow$ \%)} & \textbf{BeaverTails Utility Score ($\uparrow$ \%)}"
    prelim_text = prelim_text.replace(old_header2, new_header)
    
    # Add the disclaimer
    disclaimer = r"""
\begin{quote}
\textbf{指標に関する注意：}本節の予備実験は、TrustLLMおよびBeaverTailsを用いた探索的分析である。TrustLLM Raw ASR、Gibberish Ratio、およびBeaverTails Utility Scoreは、主実験で定義したOriginal ASR、Conditional ASR、Valid Response Rate、Valid Safety Rateとは異なる評価パイプラインに基づく。したがって、予備実験の数値を主実験の安全性指標と直接比較しない。
\end{quote}
"""
    
    prelim_text = prelim_text.replace("% 1. 予備実験 (Preliminary Experiments)", "% 1. 予備実験 (Preliminary Experiments)\n" + disclaimer)
    
    # Find the section in the current file to replace
    match_current = re.search(f"({start_marker}.*?)({end_marker})", text_current, re.DOTALL)
    
    if match_current:
        new_text = text_current[:match_current.start(1)] + prelim_text + text_current[match_current.start(2):]
        with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Successfully replaced Preliminary Experiments section.")
    else:
        print("Could not find markers in flmsec.tex")
else:
    print("Could not find markers in flmsec_0818.tex")
