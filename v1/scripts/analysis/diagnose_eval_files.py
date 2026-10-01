#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def diagnose_directory(dir_path, category_name):
    """Diagnose a specific eval directory"""
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        print(f"\n{category_name}: Directory not found: {dir_path}")
        return
    
    files = list(dir_path.rglob('*.json'))
    print(f"\n{'='*80}")
    print(f"{category_name}: {len(files)} JSON files")
    print(f"{'='*80}")
    
    # Group by subdirectory
    by_subdir = defaultdict(list)
    for f in files:
        # Get relative path from the category dir
        rel_path = f.relative_to(dir_path)
        parent_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'
        by_subdir[parent_name].append(f.name)
    
    for subdir, filenames in sorted(by_subdir.items()):
        print(f"\n  Subdirectory: {subdir} ({len(filenames)} files)")
        # Show first 3 examples
        for fname in sorted(filenames)[:3]:
            print(f"    - {fname}")
        if len(filenames) > 3:
            print(f"    ... and {len(filenames) - 3} more")

# Run diagnostics
base_dir = Path(__file__).resolve().parent.parent.parent

diagnose_directory(base_dir / 'eval/merged/data_free', 'DATA_FREE')
diagnose_directory(base_dir / 'eval/merged/interpolation', 'INTERPOLATION')
diagnose_directory(base_dir / 'eval/merged/sst_merge', 'SST_MERGE')
diagnose_directory(base_dir / 'eval/merged/ A7-7ep', 'A7-7ep (with space)')
