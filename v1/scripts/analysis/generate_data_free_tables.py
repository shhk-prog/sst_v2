
import json
from collections import defaultdict
from pathlib import Path

def load_results(json_path='all_eval_results_summary.json'):
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_table(pair, method, k, layerwise, results):
    # Filter results
    filtered = [r for r in results 
                if r.get('method') == method 
                and r.get('k') == k 
                and r.get('layerwise') == layerwise
                and (pair in r.get('filename', ''))]

    if not filtered:
        return None

    # Organize by alpha
    data = defaultdict(dict)
    for r in filtered:
        alpha = r.get('alpha')
        if alpha is None: continue
        
        eval_type = r.get('eval_type')
        if eval_type == 'jailbreak':
            data[alpha]['jb'] = r.get('resistance_rate', 0)
        elif eval_type in ['repliqa', 'alpaca']:
            data[alpha]['util'] = r.get('rouge1', 0) * 100

    alphas = sorted(data.keys())
    if not alphas:
        return None

    # Table Header
    util_name = 'RepliQA' if pair == 'A5_A7' else 'Alpaca'
    md = f"**k={k}, layerwise={layerwise}**\n\n"
    md += f"| α | JB Resistance | {util_name} |\n"
    md += "| --- | --- | --- |\n"

    for alpha in alphas:
        jb = data[alpha].get('jb', '-')
        util = data[alpha].get('util', '-')
        
        jb_str = f"{jb:.2f}%" if isinstance(jb, (int, float)) else jb
        util_str = f"{util:.2f}%" if isinstance(util, (int, float)) else util
        
        md += f"| {alpha} | {jb_str} | {util_str} |\n"
    
    return md

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    results = load_results(base_dir / 'all_eval_results_summary.json')

    pairs = ['A5_A7', 'A6_A7']
    methods = [
        ('SST-Merge (Data-Free Additive)', 'Data-Free Additive (SST-Merge)'),
        ('SST-Merge (Data-Free Interpolation)', 'Data-Free Interpolation (SST-Merge)')
    ]
    ks = [5, 10, 20, 50]
    layerwises = [False, True]

    print("# Data-Free Results\n")

    for pair in pairs:
        print(f"## Model Pair: {pair}\n")
        
        for method_key, method_name in methods:
            print(f"### {method_name}\n")
            
            for k in ks:
                for lw in layerwises:
                    table_md = generate_table(pair, method_key, k, lw, results)
                    if table_md:
                        print(table_md)
                        print("\n")

if __name__ == '__main__':
    main()
