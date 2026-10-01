import os
import re

def inline_inputs(filepath, base_dir):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        filename = match.group(1)
        full_path = os.path.join(base_dir, filename)
        if os.path.exists(full_path):
            print(f"Inlining {filename}...")
            return inline_inputs(full_path, base_dir)
        else:
            print(f"Warning: {filename} not found!")
            return match.group(0)

    pattern = re.compile(r'\\input\{([^}]+)\}')
    return pattern.sub(replacer, content)

md_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.md"
base_dir = os.path.dirname(md_path)

inlined_content = inline_inputs(md_path, base_dir)

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(inlined_content)

print("Done!")