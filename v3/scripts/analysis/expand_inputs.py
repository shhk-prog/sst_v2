import re
import os

tex_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex"
out_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_standalone.tex"
base_dir = os.path.dirname(tex_file)

with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

def replacer(match):
    rel_path = match.group(1)
    abs_path = os.path.join(base_dir, rel_path)
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f_in:
            return f_in.read()
    else:
        print(f"Warning: File not found: {abs_path}")
        return match.group(0) # そのまま返す

# \input{...} を探す (空白を許容)
pattern = re.compile(r'\\input\{(.*?)\}')
expanded_content = pattern.sub(replacer, content)

with open(out_file, "w", encoding="utf-8") as f:
    f.write(expanded_content)

print(f"Expanded file created at: {out_file}")
