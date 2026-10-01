import re

def extract_tables(filepath):
    tables = {}
    current_label = None
    current_content = []
    in_table = False
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if r"\begin{table}" in line:
                    in_table = True
                    current_content = []
                    current_label = None
                if in_table:
                    current_content.append(line)
                    m = re.search(r'\\label\{(tab:[^}]+)\}', line)
                    if m:
                        current_label = m.group(1)
                if r"\end{table}" in line:
                    if in_table and current_label:
                        tables[current_label] = "".join(current_content)
                    in_table = False
    except Exception as e:
        print(f"Error: {e}")
    return tables

md_tables = extract_tables("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_hyo_vllm_latex.md")
tex_tables = extract_tables("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex")

mismatch = []
for label, md_content in md_tables.items():
    if label in ["tab:simple_main", "tab:simple_prelim"]:
        continue
    
    if label not in tex_tables:
        print(f"Missing in tex: {label}")
        continue
        
    # compare contents ignoring whitespace differences
    md_norm = re.sub(r'\s+', ' ', md_content).strip()
    tex_norm = re.sub(r'\s+', ' ', tex_tables[label]).strip()
    
    if md_norm != tex_norm:
        mismatch.append(label)

if mismatch:
    print(f"Content mismatch found in {len(mismatch)} tables:")
    for m in mismatch[:10]:
        print(f" - {m}")
else:
    print("All appendix table contents match perfectly with flmsec_hyo_vllm_latex.md!")
