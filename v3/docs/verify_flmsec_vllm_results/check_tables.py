import re

def get_labels(filepath):
    labels = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                matches = re.findall(r'\\label\{(tab:[^}]+)\}', line)
                for m in matches:
                    labels.add(m)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return labels

md_labels = get_labels("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_hyo_vllm_latex.md")
tex_labels = get_labels("/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex")

missing = md_labels - tex_labels

if missing:
    print(f"Missing {len(missing)} tables in flmsec.tex:")
    for m in sorted(list(missing)):
        print(f" - {m}")
else:
    print("All tables from flmsec_hyo_vllm_latex.md are present in flmsec.tex!")
