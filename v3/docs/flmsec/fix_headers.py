import re

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# The current headers might be:
# \textbf{TrustLLM Raw ASR (ASR$\downarrow$ \%)} & \textbf{Gibberish Ratio (崩壊率$\uparrow$ \%)} & \textbf{BeaverTails Utility (Score$\uparrow$ \%)}
# or similar.
# Let's replace any line containing TrustLLM Raw ASR with the correct one if it's a table header.

lines = text.split('\n')
new_lines = []

for line in lines:
    if r"\textbf{TrustLLM Raw ASR" in line and r"\textbf{Gibberish Ratio" in line:
        if r"\textbf{Alpha}" in line:
            new_lines.append(r"\textbf{Pattern} & \textbf{Method} & \textbf{Alpha} & \textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio (\(\downarrow\), \%)} & \textbf{BeaverTails Utility Score (\(\uparrow\), \%)} \\")
        else:
            new_lines.append(r"\textbf{Pattern} & \textbf{Method} & \textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio (\(\downarrow\), \%)} & \textbf{BeaverTails Utility Score (\(\uparrow\), \%)} \\")
    else:
        new_lines.append(line)

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
    
print("Updated headers to exactly what the user requested.")
