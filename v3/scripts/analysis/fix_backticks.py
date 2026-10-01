import re

files_to_fix = [
    "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.md",
    "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_appendix.tex"
]

def process_backticks(match):
    content = match.group(1)
    # escape underscores
    content = content.replace("_", "\\_")
    return f"\\texttt{{{content}}}"

for path in files_to_fix:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # We only want to replace backticks if they are inline.
    # Be careful not to replace multiline code blocks (though there shouldn't be any in latex)
    new_text = re.sub(r"`([^`]+)`", process_backticks, text)
    
    # Also fix some other unescaped underscores in text if any? 
    # Let's just fix the backticks for now, as that's the main issue.
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)

print("Fixed backticks and escaped underscores inside them.")