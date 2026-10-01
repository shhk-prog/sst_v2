import re

with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Locate Table 13 block
match = re.search(r"(\\begin\{table\}\[H\]\n\\centering\n\\caption\{メイン実験.*?tab:evaluation_main_alpha=0.6\}.*?\\end\{tabular\}\n\}\n\\end\{table\})", text, re.DOTALL)
if match:
    t13_full = match.group(1)
    
    # Split into A and B
    lines = t13_full.split('\n')
    table_a_lines = []
    table_b_lines = []
    
    for line in lines:
        if line.startswith("\\begin{tabular}"):
            table_a_lines.append("\\begin{tabular}{llrrrr}")
            table_b_lines.append("\\begin{tabular}{llrrrr}")
        elif "&" in line and "\\textbf{" in line:
            parts = line.split("&")
            if len(parts) >= 10:
                table_a_lines.append(" & ".join(parts[:6]) + " \\\\")
                table_b_lines.append(" & ".join(parts[:2] + parts[6:]))
            else:
                table_a_lines.append(line)
                table_b_lines.append(line)
        elif "&" in line and not line.strip().startswith("%"):
            parts = line.split("&")
            if len(parts) >= 10:
                a_part = " & ".join(parts[:6]).strip()
                if not a_part.endswith("\\\\"):
                    if a_part.endswith("\\"):
                        a_part += "\\"
                    else:
                        a_part += " \\\\"
                table_a_lines.append(a_part)
                table_b_lines.append(" & ".join(parts[:2] + parts[6:]))
            else:
                table_a_lines.append(line)
                table_b_lines.append(line)
        else:
            if "\\caption{" in line:
                # Add (Safety diagnostics) and (Utility)
                table_a_lines.append(line.replace("詳細評価指標", "詳細評価指標 (Safety diagnostics)"))
                table_b_lines.append(line.replace("詳細評価指標", "詳細評価指標 (Utility)"))
            elif "\\label{" in line:
                table_a_lines.append(line.replace("tab:evaluation_main_alpha=0.6", "tab:evaluation_main_alpha=0.6_safety"))
                table_b_lines.append(line.replace("tab:evaluation_main_alpha=0.6", "tab:evaluation_main_alpha=0.6_utility"))
            else:
                table_a_lines.append(line)
                table_b_lines.append(line)
                
    new_tables = "\n".join(table_a_lines) + "\n\n" + "\n".join(table_b_lines)
    text = text.replace(t13_full, new_tables)
    
    with open('/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Table 13 split successful.")
else:
    print("Could not find Table 13.")
