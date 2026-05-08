#!/usr/bin/env python3
"""
全実験結果を詳細な表形式で出力
"""

import json
from collections import defaultdict

def load_results():
    with open('all_eval_results_summary.json') as f:
        return json.load(f)

def organize_results_by_method(results):
    """手法×α値×設定でデータを整理"""
    
    # A5_A7とA6_A7で分離
    a5_a7 = defaultdict(lambda: defaultdict(dict))
    a6_a7 = defaultdict(lambda: defaultdict(dict))
    base_models = {}
    
    for r in results:
        pair = r.get('pair')
        method = r.get('method', 'Unknown')
        alpha = r.get('alpha')
        eval_type = r.get('eval_type')
        gevp = r.get('gevp', False)
        layerwise = r.get('layerwise', False)
        
        # Data-Free判定
        if method == 'Unknown' and r.get('category') == 'data_free':
            method = 'SST-Merge (Data-Free)'
        
        # ベースモデル
        if method in ['Utility Adapter', 'Safety Adapter', 'Base Model']:
            if pair not in base_models:
                base_models[pair] = {}
            if method not in base_models[pair]:
                base_models[pair][method] = {}
            base_models[pair][method][eval_type] = r
            continue
        
        # k値抽出（SST-Mergeの場合）
        k_val = None
        if 'SST' in method:
            filename = r.get('filename', '')
            if '_k5_' in filename or '_k5.' in filename:
                k_val = 5
            elif '_k10_' in filename:
                k_val = 10
            elif '_k20_' in filename:
                k_val = 20
        
        # キー作成
        if alpha is not None:
            # SST-Mergeの場合はk値も含める
            if k_val is not None:
                key = (method, alpha, k_val, gevp, layerwise)
            else:
                key = (method, alpha, gevp, layerwise)
            
            if pair == 'A5_A7':
                a5_a7[key][eval_type] = r
            elif pair == 'A6_A7':
                a6_a7[key][eval_type] = r
    
    return base_models, a5_a7, a6_a7

def format_percentage(value, default='N/A'):
    """パーセンテージフォーマット"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return default

def format_score(value, default='N/A'):
    """スコアフォーマット"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return default

def generate_base_model_table(base_models):
    """ベースモデルの表を生成"""
    lines = []
    lines.append("## ベースモデル (マージ前)\n")
    lines.append("| モデル | タスク | Jailbreak | Utility (RepliQA/Alpaca) |")
    lines.append("| --- | --- | --- | --- |")
    
    # A5
    if 'A5_A7' in base_models and 'Utility Adapter' in base_models['A5_A7']:
        a5_jb = base_models['A5_A7']['Utility Adapter'].get('jailbreak', {})
        a5_util = base_models['A5_A7']['Utility Adapter'].get('repliqa', {})
        jb_rate = a5_jb.get('resistance_rate', 0)
        util_score = a5_util.get('rouge1', 0) * 100
        lines.append(f"| **A5 Utility** | RepliQA | {format_percentage(jb_rate)} | **{format_score(util_score)}** (RepliQA) |")
    
    # A6
    if 'A6_A7' in base_models and 'Utility Adapter' in base_models['A6_A7']:
        a6_jb = base_models['A6_A7']['Utility Adapter'].get('jailbreak', {})
        a6_util = base_models['A6_A7']['Utility Adapter'].get('alpaca', {})
        jb_rate = a6_jb.get('resistance_rate', 0)
        util_score = a6_util.get('rouge1', 0) * 100
        lines.append(f"| **A6 Utility** | Alpaca | {format_percentage(jb_rate)} | **{format_score(util_score)}** (Alpaca) |")
    
    # A7
    if 'A5_A7' in base_models and 'Safety Adapter' in base_models['A5_A7']:
        a7_jb = base_models['A5_A7']['Safety Adapter'].get('jailbreak', {})
        a7_repliqa = base_models['A5_A7']['Safety Adapter'].get('repliqa', {})
        jb_rate = a7_jb.get('resistance_rate', 0)
        repliqa_score = a7_repliqa.get('rouge1', 0) * 100
        
        # A6_A7からAlpacaも取得
        alpaca_score = 0
        if 'A6_A7' in base_models and 'Safety Adapter' in base_models['A6_A7']:
            a7_alpaca = base_models['A6_A7']['Safety Adapter'].get('alpaca', {})
            alpaca_score = a7_alpaca.get('rouge1', 0) * 100
        
        lines.append(f"| **A7 Safety** | Safety | **{format_percentage(jb_rate)}** | {format_score(repliqa_score)} (RepliQA), {format_score(alpaca_score)} (Alpaca) |")
    
    return '\n'.join(lines) + '\n'

def generate_method_table(results_dict, method_name, eval_type_util):
    """各手法のα値ごとの表を生成"""
    lines = []
    lines.append(f"### **{method_name}**\n")
    
    eval_type_jb = 'jailbreak'
    util_name = 'RepliQA' if eval_type_util == 'repliqa' else 'Alpaca'
    
    lines.append(f"| α | Jailbreak | {util_name} |")
    lines.append("| --- | --- | --- |")
    
    # α値でソート
    alpha_values = sorted(set(key[1] for key in results_dict.keys() 
                             if key[0] == method_name and len(key) >= 2))
    
    for alpha in alpha_values:
        # この手法×α値のデータを取得（GEVP/layerwiseバリエーションから最良を選択）
        matching_keys = [k for k in results_dict.keys() 
                        if k[0] == method_name and k[1] == alpha]
        
        if matching_keys:
            # 最良の結果を選択（Jailbreak最大、Utility最大）
            best_jb = None
            best_util = None
            best_jb_rate = 0
            best_util_score = 0
            
            for key in matching_keys:
                jb_data = results_dict[key].get(eval_type_jb, {})
                util_data = results_dict[key].get(eval_type_util, {})
                
                jb_rate = jb_data.get('resistance_rate', 0) if jb_data else 0
                util_score = util_data.get('rouge1', 0) if util_data else 0
                
                if jb_rate > best_jb_rate:
                    best_jb_rate = jb_rate
                    best_jb = jb_data
                
                if util_score > best_util_score:
                    best_util_score = util_score
                    best_util = util_data
            
            jb_str = format_percentage(best_jb_rate) if best_jb else 'N/A'
            util_str = format_score(best_util_score * 100) if best_util else 'N/A'
            
            # 強調表示（最高値）
            if best_jb_rate >= 99.5:
                jb_str = f"**{jb_str}**"
            if best_util_score >= 0.60:
                util_str = f"**{util_str}**"
            
            lines.append(f"| {alpha:.2f} | {jb_str} | {util_str} |")
    
    return '\n'.join(lines) + '\n'

def generate_sst_table(results_dict, method_name, k_val, layerwise, eval_type_util):
    """SST-Mergeの表を生成"""
    lines = []
    
    lw_str = 'layerwise=true' if layerwise else 'layerwise=False'
    lines.append(f"**SST-k{k_val} {lw_str}**\n")
    
    eval_type_jb = 'jailbreak'
    util_name = 'RepliQA' if eval_type_util == 'repliqa' else 'Alpaca'
    
    lines.append(f"| α | JB Resistance (Safety) | {util_name} |")
    lines.append("| --- | --- | --- |")
    
    # α値でソート
    alpha_values = sorted(set(key[1] for key in results_dict.keys() 
                             if key[0] == method_name and len(key) >= 5 
                             and key[2] == k_val and key[4] == layerwise))
    
    for alpha in alpha_values:
        # この設定のデータを取得
        matching_keys = [k for k in results_dict.keys() 
                        if k[0] == method_name and k[1] == alpha 
                        and len(k) >= 5 and k[2] == k_val and k[4] == layerwise]
        
        if matching_keys:
            key = matching_keys[0]  # GEVPバリエーションから1つ選択
            jb_data = results_dict[key].get(eval_type_jb, {})
            util_data = results_dict[key].get(eval_type_util, {})
            
            jb_rate = jb_data.get('resistance_rate', 0) if jb_data else 0
            util_score = util_data.get('rouge1', 0) if util_data else 0
            
            jb_str = format_percentage(jb_rate)
            util_str = format_score(util_score * 100)
            
            lines.append(f"| {alpha:.2f} | {jb_str} | {util_str} |")
    
    return '\n'.join(lines) + '\n'

def generate_comprehensive_tables(base_models, a5_a7, a6_a7):
    """包括的な表を生成"""
    lines = []
    
    # タイトル
    lines.append("# SST-Merge v5 完全実験結果\n")
    lines.append(f"**生成日**: 2026-02-02\n")
    
    # ベースモデル
    lines.append(generate_base_model_table(base_models))
    
    # A5_A7 (RepliQA)
    lines.append("## A5_A7 (RepliQA タスク)\n")
    
    # Task Arithmetic
    lines.append(generate_method_table(a5_a7, 'Task Arithmetic', 'repliqa'))
    
    # TIES
    lines.append(generate_method_table(a5_a7, 'TIES', 'repliqa'))
    
    # DARE
    lines.append(generate_method_table(a5_a7, 'DARE', 'repliqa'))
    
    # SST-Merge (Additive)
    lines.append("### **SST-Merge (加算型): 全結果 (k=5,10,20 × layerwise=True/False)**\n")
    for k_val in [5, 10, 20]:
        for layerwise in [False, True]:
            lines.append(generate_sst_table(a5_a7, 'SST-Merge (Additive)', k_val, layerwise, 'repliqa'))
    
    # SST-Merge (Interpolation)
    lines.append("### **SST-Merge (補間型): 全結果**\n")
    lines.append(generate_method_table(a5_a7, 'SST-Merge (Interpolation)', 'repliqa'))
    
    # SST-Merge (Data-Free)
    lines.append("### **SST-Merge (Data-Free): 全結果**\n")
    lines.append(generate_method_table(a5_a7, 'SST-Merge (Data-Free)', 'repliqa'))
    
    # A6_A7 (Alpaca)
    lines.append("\n## A6_A7 (Alpaca タスク)\n")
    
    # Task Arithmetic
    lines.append(generate_method_table(a6_a7, 'Task Arithmetic', 'alpaca'))
    
    # TIES
    lines.append(generate_method_table(a6_a7, 'TIES', 'alpaca'))
    
    # DARE
    lines.append(generate_method_table(a6_a7, 'DARE', 'alpaca'))
    
    # SST-Merge (Additive)
    lines.append("### **SST-Merge (加算型): 全結果 (k=5,10,20 × layerwise=True/False)**\n")
    for k_val in [5, 10, 20]:
        for layerwise in [False, True]:
            lines.append(generate_sst_table(a6_a7, 'SST-Merge (Additive)', k_val, layerwise, 'alpaca'))
    
    # SST-Merge (Interpolation)
    lines.append("### **SST-Merge (補間型): 全結果**\n")
    lines.append(generate_method_table(a6_a7, 'SST-Merge (Interpolation)', 'alpaca'))
    
    # SST-Merge (Data-Free)
    lines.append("### **SST-Merge (Data-Free): 全結果**\n")
    lines.append(generate_method_table(a6_a7, 'SST-Merge (Data-Free)', 'alpaca'))
    
    return '\n'.join(lines)

def main():
    results = load_results()
    base_models, a5_a7, a6_a7 = organize_results_by_method(results)
    
    report = generate_comprehensive_tables(base_models, a5_a7, a6_a7)
    
    with open('complete_results_tables.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Generated complete results tables: complete_results_tables.md")
    print(f"Total A5_A7 configurations: {len(a5_a7)}")
    print(f"Total A6_A7 configurations: {len(a6_a7)}")

if __name__ == '__main__':
    main()
