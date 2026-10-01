import re

tex_file = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex"
with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r'\\begin\{table\}\[(?:H|htbp)\].*?\\caption\{Task Arithmeticにおける唯一の支配されない点（パレート点）の実測値\}.*?\\label\{tab:task-arithmetic-single-point\}.*?\\end\{table\}', re.DOTALL)

def replacer(match):
    return r"\input{tables/tab_task_arithmetic_single_point.tex}"

new_content = pattern.sub(replacer, content)

if new_content != content:
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced tab:task-arithmetic-single-point successfully.")
else:
    print("Not found or already replaced.")
