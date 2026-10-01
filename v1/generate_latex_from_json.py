import json

with open('all_eval_results_summary.json', 'r') as f:
    data = json.load(f)

# Group the data
results = {'SST-Merge': {}, 'Data-Free Merge': {}}
alphas = [0.05, 0.07, 0.09, 0.10, 0.12, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
k_values = [5, 10, 20, 30, 40, 50]

for k in k_values:
    results['SST-Merge'][k] = {}
    results['Data-Free Merge'][k] = {}
    for a in alphas:
        results['SST-Merge'][k][a] = {}
        results['Data-Free Merge'][k][a] = {}

for item in data:
    if item.get('pair') != 'A6_A7':
        continue
        
    k = item.get('k')
    if k not in k_values:
        continue
        
    alpha = item.get('alpha')
    if alpha is None:
        continue
        
    closest_alpha = min(alphas, key=lambda x: abs(x - alpha))
    if abs(closest_alpha - alpha) > 0.001:
        continue
    alpha = closest_alpha
    
    lw = item.get('layerwise')
    method_str = item.get('method', '')
    category = item.get('category')
    mask_type = item.get('mask_type')
    
    val = None
    if item.get('eval_type') == 'jailbreak':
        val = item.get('resistance_rate')
        metric = 'jb'
    elif item.get('eval_type') == 'alpaca':
        val = item.get('rouge1')
        if val is not None:
            val = val * 100.0
        metric = 'alpaca'
    else:
        continue
        
    if val is None:
        continue
        
    # SST-Merge (mask_type=hard)
    if category in ['additive', 'interpolation'] and mask_type == 'hard':
        method_type = 'Interpolation' if 'Interpolation' in method_str or 'interp' in method_str.lower() else 'Additive'
        key = (method_type, lw)
        if metric not in results['SST-Merge'][k][alpha].get(key, {}):
            if key not in results['SST-Merge'][k][alpha]:
                results['SST-Merge'][k][alpha][key] = {}
            results['SST-Merge'][k][alpha][key][metric] = val
            
    # Data-Free Merge (mask_type=soft)
    if category == 'data_free' and mask_type == 'soft':
        method_type = 'Interpolation' if 'Interpolation' in method_str or 'interp' in method_str.lower() else 'Additive'
        key = (method_type, lw)
        if metric not in results['Data-Free Merge'][k][alpha].get(key, {}):
            if key not in results['Data-Free Merge'][k][alpha]:
                results['Data-Free Merge'][k][alpha][key] = {}
            results['Data-Free Merge'][k][alpha][key][metric] = val

# Generate LaTeX
output = ""

for ttype in ['SST-Merge', 'Data-Free Merge']:
    for k in k_values:
        has_data = False
        for a in alphas:
            if results[ttype][k][a]:
                has_data = True
                break
        if not has_data:
            continue
            
        if ttype == 'SST-Merge':
            caption = f"SST-Merge layerwise= True/False $k={k}$: A6 (Alpaca) + A7 (Safety)"
            label = f"tab:res_a6_sst_{k}"
            output += f"% SST k={k}\n"
        else:
            caption = f"Data-Free SST-Merge layerwise= True/False $k={k}$: A6 (Alpaca) + A7 (Safety)"
            label = f"tab:res_a6_data_free_sst_{k}"
            output += f"% Data Free SST k={k}\n"
            
        output += f"\\begin{{table}}[h]\n\\centering\n\\caption{{{caption}}}\n\\label{{{label}}}\n\\begin{{tabular}}{{c|cc|cc|cc|cc}}\n\\hline\n"
        output += " & \\multicolumn{2}{c|}{\\textbf{Additive Lw=True}} & \\multicolumn{2}{c|}{\\textbf{Additive Lw=False}} & \\multicolumn{2}{c|}{\\textbf{Interpolation lw=True}}& \\multicolumn{2}{c}{\\textbf{Interpolation lw=False}} \\\\\n"
        output += "$\\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\\\\n\\hline\n"
        
        for a in alphas:
            row = [f"{a:.2f}"]
            for method_type, lw in [('Additive', True), ('Additive', False), ('Interpolation', True), ('Interpolation', False)]:
                data_dict = results[ttype][k][a].get((method_type, lw), {})
                jb = f"{data_dict.get('jb', 0):.2f}\\%" if 'jb' in data_dict else "-"
                alpaca = f"{data_dict.get('alpaca', 0):.2f}\\%" if 'alpaca' in data_dict else "-"
                row.extend([jb, alpaca])
                
            # Only print row if it's not all dashes
            if any(x != "-" for x in row[1:]):
                output += " & ".join(row) + " \\\\\n"
                
        output += "\\hline\n\\end{tabular}\n\\end{table}\n\\FloatBarrier\n\n"

with open('docs/SST_Merge_Tables_Analysis/generated_latex_tables.tex', 'w') as f:
    f.write(output)

print("Successfully generated docs/SST_Merge_Tables_Analysis/generated_latex_tables.tex")
