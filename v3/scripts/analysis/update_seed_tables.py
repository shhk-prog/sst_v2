import re

def update_seed_tables():
    tex_files = [
        "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone_nosst2.tex",
        "/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone.tex"
    ]
    custom_tables_file = "/Users/saki/lab/src/sst_v3/docs/flmsec/custom_vllm_tables.md"

    # Read custom tables
    with open(custom_tables_file, "r", encoding="utf-8") as f:
        custom_content = f.read()

    # Extract the seed tables part from custom tables
    # Find the first occurrence of "% --- Alphaスイープ シード別詳細"
    match = re.search(r"(% --- Alphaスイープ シード別詳細.*)", custom_content, re.DOTALL)
    if not match:
        print("Could not find the new seed tables in custom tables.")
        return
    new_seed_tables = match.group(1).strip()

    for tex_file in tex_files:
        print(f"Processing {tex_file}...")
        # Read target tex file
        with open(tex_file, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Find the old seed tables block
        # Start: the first "% --- メイン実験 シード別詳細"
        # End: just before "\end{document}"
        start_pattern = r"% --- メイン実験 シード別詳細"
        start_match = re.search(start_pattern, tex_content)
        
        if not start_match:
            print(f"  Could not find the start of the old seed tables in {tex_file}.")
            continue
            
        start_idx = start_match.start()
        
        end_pattern = r"\\end\{document\}"
        end_match = re.search(end_pattern, tex_content[start_idx:])
        
        if not end_match:
            print(f"  Could not find the end document tag in {tex_file}.")
            continue
            
        end_idx = start_idx + end_match.start()
        
        # We want to replace everything from start_idx to end_idx with the new seed tables
        new_tex_content = tex_content[:start_idx] + new_seed_tables + "\n\n" + tex_content[end_idx:]

        # Write back
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(new_tex_content)
            
        print(f"  Successfully replaced the old seed tables in {tex_file}.")

if __name__ == "__main__":
    update_seed_tables()
