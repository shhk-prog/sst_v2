
import os
import re
import json
from pathlib import Path
from collections import defaultdict

def verify_files(data_dir):
    files = list(Path(data_dir).rglob('*.json'))
    print(f"Found {len(files)} JSON files in {data_dir}")
    
    config_map = defaultdict(list)
    
    for f in files:
        filename = f.name
        
        # Parse logic similar to collect_all_results.py
        parts = {}
        
        if 'A5_A7' in filename:
            parts['pair'] = 'A5_A7'
            parts['utility'] = 'RepliQA'
        elif 'A6_A7' in filename:
            parts['pair'] = 'A6_A7'
            parts['utility'] = 'Alpaca'
        
        if 'data_free' in filename:
            if 'interp' in filename:
                parts['method'] = 'SST-Merge (Data-Free Interpolation)'
            else:
                parts['method'] = 'SST-Merge (Data-Free Additive)'
        else:
            # Skip non-data-free if any found
            continue

        # Extract k
        k_match = re.search(r'_k(\d+)', filename)
        topk_match = re.search(r'_topk(\d+)', filename)
        
        k_val = None
        topk_val = None
        
        if k_match:
            k_val = int(k_match.group(1))
        if topk_match:
            topk_val = int(topk_match.group(1))
            
        if k_val and topk_val and k_val != topk_val:
            print(f"WARNING: k ({k_val}) != topk ({topk_val}) in {filename}")
        
        final_k = k_val if k_val else topk_val
        parts['k'] = final_k
        
        # Alpha
        alpha_match = re.search(r'_a([0-9\.]+)', filename)
        if alpha_match:
            parts['alpha'] = float(alpha_match.group(1))
        
        # Layerwise
        parts['layerwise'] = '_lw' in filename
        
        # Eval Type
        if 'jailbreak' in filename:
            parts['eval_type'] = 'jailbreak'
        elif 'alpaca' in filename:
            parts['eval_type'] = 'alpaca'
        elif 'repliqa' in filename:
            parts['eval_type'] = 'repliqa'
            
        # Key for uniqueness check
        key = (
            parts.get('pair'),
            parts.get('method'),
            parts.get('k'),
            parts.get('layerwise'),
            parts.get('alpha'),
            parts.get('eval_type')
        )
        
        config_map[key].append(f)

    # Report duplicates
    dup_count = 0
    for key, paths in config_map.items():
        if len(paths) > 1:
            print(f"DUPLICATE CONFIG FOUND: {key}")
            for p in paths:
                print(f"  - {p}")
            dup_count += 1
            
    print(f"Total Duplicate Configs: {dup_count}")

verify_files('eval/merged/data_free')
