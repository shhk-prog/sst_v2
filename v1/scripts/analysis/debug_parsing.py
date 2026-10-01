
import re

def extract_config(filename):
    config = {}
    
    # k value (check for both _k and _topk)
    k_match = re.search(r'_k(\d+)', filename)
    topk_match = re.search(r'_topk(\d+)', filename)
    
    if k_match:
        config['k'] = int(k_match.group(1))
        config['k_source'] = 'k'
    elif topk_match:
        config['k'] = int(topk_match.group(1))
        config['k_source'] = 'topk'
    else:
        config['k'] = 5  # Default
        config['k_source'] = 'default'

    # Layerwise
    config['layerwise'] = '_lw' in filename or '_lw_' in filename
    
    # Method
    if 'data_free' in filename:
        if 'interp' in filename:
            config['method'] = 'SST-Merge (Data-Free Interpolation)'
        else:
            config['method'] = 'SST-Merge (Data-Free Additive)'

    return config

filenames = [
    "A6_A7_data_free_interp_k20_lw_a0.1_topk20_alpaca_eval_results.json",
    "A5_A7_data_free_k5_a1.0_topk5_repliqa_eval_results.json",
    "A6_A7_data_free_interp_k10_a0.5_topk10_jailbreak_eval_results.json"
]

for f in filenames:
    print(f"File: {f}")
    print(f"Parsed: {extract_config(f)}")
    print("-" * 20)
