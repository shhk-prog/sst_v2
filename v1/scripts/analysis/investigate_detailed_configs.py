#!/usr/bin/env python3
"""
詳細設定の調査：DARE、補間型、Data-Free
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def extract_config_from_filename(filename):
    """ファイル名から設定を抽出"""
    config = {}
    
    # α値
    alpha_match = re.search(r'_a([\d.]+)', filename)
    if alpha_match:
        config['alpha'] = float(alpha_match.group(1))
    
    # k値
    k_match = re.search(r'_k(\d+)', filename)
    if k_match:
        config['k'] = int(k_match.group(1))
    
    # layerwise
    if '_lw_' in filename or '_lw.' in filename:
        config['layerwise'] = True
    elif '_k' in filename or '_sst' in filename or 'data_free' in filename:
        config['layerwise'] = False
    
    # GEVP
    if 'nogevp' in filename:
        config['gevp'] = False
    elif '_sst_interp_' in filename:
        config['gevp'] = True
    
    # ペア
    if 'A5_A7' in filename:
        config['pair'] = 'A5_A7'
    elif 'A6_A7' in filename:
        config['pair'] = 'A6_A7'
    
    # 評価タイプ
    if 'jailbreak' in filename:
        config['eval_type'] = 'jailbreak'
    elif 'alpaca' in filename:
        config['eval_type'] = 'alpaca'
    elif 'repliqa' in filename:
        config['eval_type'] = 'repliqa'
    
    return config

def load_result(filepath):
    """結果を読み込み"""
    try:
        with open(filepath) as f:
            data = json.load(f)
        
        result = {}
        if 'metrics' in data:
            result['resistance_rate'] = data['metrics'].get('resistance_rate', 0) * 100
            result['asr'] = data['metrics'].get('attack_success_rate', 0) * 100
            result['rouge1'] = data['metrics'].get('rouge1', {}).get('mean', 0) * 100
            result['rouge2'] = data['metrics'].get('rouge2', {}).get('mean', 0) * 100
            result['rougeL'] = data['metrics'].get('rougeL', {}).get('mean', 0) * 100
        
        return result
    except Exception as e:
        return {}

def investigate_dare():
    """DAREの詳細調査"""
    print("="*80)
    print("DARE（A6_A7）の詳細調査")
    print("="*80)
    
    dare_files = sorted(Path('merge_eval').glob('A6_A7_dare*.json'))
    
    results_by_alpha = defaultdict(dict)
    
    for filepath in dare_files:
        config = extract_config_from_filename(filepath.name)
        result = load_result(filepath)
        
        if 'alpha' in config and 'eval_type' in config:
            alpha = config['alpha']
            eval_type = config['eval_type']
            results_by_alpha[alpha][eval_type] = result
    
    print("\n### **DARE (A6_A7)**\n")
    print("| α | Jailbreak | Alpaca |")
    print("| --- | --- | --- |")
    
    for alpha in sorted(results_by_alpha.keys()):
        jb = results_by_alpha[alpha].get('jailbreak', {})
        alp = results_by_alpha[alpha].get('alpaca', {})
        
        jb_str = f"{jb.get('resistance_rate', 0):.2f}%" if jb else "N/A"
        alp_str = f"{alp.get('rouge1', 0):.2f}%" if alp else "N/A"
        
        print(f"| {alpha:.2f} | {jb_str} | {alp_str} |")

def investigate_interpolation():
    """補間型の詳細調査"""
    print("\n" + "="*80)
    print("SST-Merge補間型の詳細調査")
    print("="*80)
    
    interp_files = sorted(Path('merge_eval_interpolation').glob('*.json'))
    
    # ファイル名のパターンを確認
    print("\nファイル名パターン:")
    for f in interp_files[:5]:
        print(f"  {f.name}")
    
    # 設定を解析
    configs = set()
    results_by_config = defaultdict(lambda: defaultdict(dict))
    
    for filepath in interp_files:
        config = extract_config_from_filename(filepath.name)
        
        if 'k' in config:
            k = config.get('k', 'none')
            gevp = config.get('gevp', 'unknown')
            lw = config.get('layerwise', 'unknown')
            configs.add((k, gevp, lw))
        
        if 'alpha' in config and 'pair' in config and 'eval_type' in config:
            result = load_result(filepath)
            alpha = config['alpha']
            pair = config['pair']
            eval_type = config['eval_type']
            k = config.get('k', 5)
            gevp = config.get('gevp', True)
            lw = config.get('layerwise', False)
            
            key = (pair, k, gevp, lw)
            results_by_config[key][alpha][eval_type] = result
    
    print(f"\n検出された設定: {len(configs)}種類")
    for k, gevp, lw in sorted(configs):
        print(f"  k={k}, GEVP={gevp}, layerwise={lw}")
    
    # A5_A7とA6_A7で別々に表示
    for pair in ['A5_A7', 'A6_A7']:
        eval_name = 'RepliQA' if pair == 'A5_A7' else 'Alpaca'
        eval_type = 'repliqa' if pair == 'A5_A7' else 'alpaca'
        
        print(f"\n### **SST-Merge補間型 ({pair})**\n")
        
        # k値ごと
        for k in [5]:  # 補間型はk=5のみ
            for gevp in [True, False]:
                for lw in [False, True]:
                    key = (pair, k, gevp, lw)
                    if key not in results_by_config:
                        continue
                    
                    gevp_str = "GEVP有効" if gevp else "GEVP無効"
                    lw_str = "layerwise=True" if lw else "layerwise=False"
                    
                    print(f"**k={k}, {gevp_str}, {lw_str}**\n")
                    print(f"| α | Jailbreak | {eval_name} |")
                    print("| --- | --- | --- |")
                    
                    for alpha in sorted(results_by_config[key].keys()):
                        jb = results_by_config[key][alpha].get('jailbreak', {})
                        util = results_by_config[key][alpha].get(eval_type, {})
                        
                        jb_str = f"{jb.get('resistance_rate', 0):.2f}%" if jb else "N/A"
                        util_str = f"{util.get('rouge1', 0):.2f}%" if util else "N/A"
                        
                        print(f"| {alpha:.2f} | {jb_str} | {util_str} |")
                    
                    print()

def investigate_data_free():
    """Data-Freeの詳細調査"""
    print("\n" + "="*80)
    print("SST-Merge Data-Freeの詳細調査")
    print("="*80)
    
    df_files = sorted(Path('merge_eval_data_free_full').glob('*.json'))
    
    # ファイル名のパターンを確認
    print("\nファイル名パターン:")
    for f in df_files[:5]:
        print(f"  {f.name}")
    
    # 設定を解析
    configs = set()
    results_by_config = defaultdict(lambda: defaultdict(dict))
    
    for filepath in df_files:
        config = extract_config_from_filename(filepath.name)
        
        if 'k' in config:
            k = config.get('k', 'none')
            lw = config.get('layerwise', 'unknown')
            configs.add((k, lw))
        
        if 'alpha' in config and 'pair' in config and 'eval_type' in config:
            result = load_result(filepath)
            alpha = config['alpha']
            pair = config['pair']
            eval_type = config['eval_type']
            k = config.get('k', 'none')
            lw = config.get('layerwise', False)
            
            key = (pair, k, lw)
            results_by_config[key][alpha][eval_type] = result
    
    print(f"\n検出された設定: {len(configs)}種類")
    for k, lw in sorted(configs):
        print(f"  k={k}, layerwise={lw}")
    
    # A5_A7とA6_A7で別々に表示
    for pair in ['A5_A7', 'A6_A7']:
        eval_name = 'RepliQA' if pair == 'A5_A7' else 'Alpaca'
        eval_type = 'repliqa' if pair == 'A5_A7' else 'alpaca'
        
        print(f"\n### **SST-Merge Data-Free ({pair})**\n")
        
        # k値ごと
        for k in [5, 10, 20, 'none']:
            for lw in [False, True]:
                key = (pair, k, lw)
                if key not in results_by_config or not results_by_config[key]:
                    continue
                
                k_str = f"k={k}" if k != 'none' else "k指定なし"
                lw_str = "layerwise=True" if lw else "layerwise=False"
                
                print(f"**{k_str}, {lw_str}**\n")
                print(f"| α | Jailbreak | {eval_name} |")
                print("| --- | --- | --- |")
                
                for alpha in sorted(results_by_config[key].keys()):
                    jb = results_by_config[key][alpha].get('jailbreak', {})
                    util = results_by_config[key][alpha].get(eval_type, {})
                    
                    jb_str = f"{jb.get('resistance_rate', 0):.2f}%" if jb else "N/A"
                    util_str = f"{util.get('rouge1', 0):.2f}%" if util else "N/A"
                    
                    print(f"| {alpha:.2f} | {jb_str} | {util_str} |")
                
                print()

def main():
    # DARE調査
    investigate_dare()
    
    # 補間型調査
    investigate_interpolation()
    
    # Data-Free調査
    investigate_data_free()

if __name__ == '__main__':
    main()
