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

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix table A (safety)
match_a = re.search(r"(\\begin\{table\}\[H\]\s*\\centering\s*\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6_safety\}.*?\\end\{table\})", text, re.DOTALL)

if match_a:
    table_a = match_a.group(1)
    lines_a = table_a.split("\n")
    new_lines_a = []
    
    for line in lines_a:
        if line.startswith("\\begin{tabular}"):
            new_lines_a.append("\\begin{tabular}{llrrrr}")
        elif "&" in line and "\\textbf{" in line:
            new_lines_a.append("\\textbf{Pattern} & \\textbf{Method} & \\textbf{Safety Ave [Original ASR] (ASR$\\downarrow$ \\%)} & \\textbf{Safety Ave [Conditional ASR] (ASR$\\downarrow$ \\%)} & \\textbf{Valid Response Rate (\\%)} & \\textbf{Valid Safety Rate (\\%)} \\\\")
        elif "&" in line and not line.strip().startswith("%"):
            parts = [p.strip() for p in line.split("&")]
            # parts: [Pattern, Method, Original ASR, Math, Code, Medical, General]
            if len(parts) >= 7:
                pattern = parts[0]
                method = parts[1]
                
                # Check for "Base" which has \pm in Pattern/Method sometimes?
                # Actually, the base models are Base (MedAlpaca) etc.
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
                        
                o_asr = parts[2]
                if o_asr.endswith("\\\\"):
                    o_asr = o_asr[:-2].strip()
                
                new_line = f"{pattern} & {method} & {o_asr} & {ca} & {vrr} & {vsr} \\\\"
                new_lines_a.append(new_line)
            else:
                new_lines_a.append(line)
        else:
            new_lines_a.append(line)
            
    text = text.replace(table_a, "\n".join(new_lines_a))
    
# Fix table B (utility)
match_b = re.search(r"(\\begin\{table\}\[H\]\s*\\centering\s*\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6_utility\}.*?\\end\{table\})", text, re.DOTALL)

if match_b:
    table_b = match_b.group(1)
    lines_b = table_b.split("\n")
    new_lines_b = []
    
    for line in lines_b:
        if line.startswith("\\begin{tabular}"):
            new_lines_b.append("\\begin{tabular}{llrrrr}")
        elif "&" in line and "\\textbf{" in line:
            new_lines_b.append("\\textbf{Pattern} & \\textbf{Method} & \\textbf{Math Ave (\\%)} & \\textbf{Code Ave (\\%)} & \\textbf{Medical Ave (\\%)} & \\textbf{General/Inst Ave (\\%)} \\\\")
        elif "&" in line and not line.strip().startswith("%"):
            parts = [p.strip() for p in line.split("&")]
            if len(parts) >= 7:
                pattern = parts[0]
                method = parts[1]
                math = parts[3]
                code = parts[4]
                med = parts[5]
                gen = parts[6]
                if gen.endswith("\\\\"):
                    gen = gen[:-2].strip()
                
                new_line = f"{pattern} & {method} & {math} & {code} & {med} & {gen} \\\\"
                new_lines_b.append(new_line)
            else:
                new_lines_b.append(line)
        else:
            new_lines_b.append(line)
            
    text = text.replace(table_b, "\n".join(new_lines_b))

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Table 13 A and B.")
