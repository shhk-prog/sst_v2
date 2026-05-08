import json
import os
import numpy as np
from typing import Dict

def load_predictions(file_path: str) -> Dict[str, dict]:
    res_map = {}
    if not os.path.exists(file_path):
        return res_map
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', [])
    for r in results:
        if '<nooutput>' in r.get('ground_truth', ''):
            continue
        res_map[r['instruction']] = r
    return res_map

def main():
    base_dir = "/mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v5/eval/merged/sst_merge/merge_eval/"
    alphas = ["0.2", "0.5", "0.8", "1.0"] 
    k_value = "5" # これまで見ていたk=5を使用
    
    print(f"--- SST-Merge (Interpolation, k={k_value}) のスコア低下分析 ---")
    
    all_data = {}
    all_rouges = {}
    
    # データを読み込み、各種平均を計算
    for alpha in alphas:
        # Interpolation のファイル
        filename = f"A6_A7_sst_k{k_value}_lw_a{alpha}_alpaca_eval_results.json"
        path = os.path.join(base_dir, filename)
        preds = load_predictions(path)
        all_data[alpha] = preds
        
        # 平均Rouge-Lを計算
        if preds:
            avg_rouge_l = sum(item.get('rougeL', 0) for item in preds.values()) / len(preds)
            all_rouges[alpha] = avg_rouge_l
            print(f"Alpha={alpha}: Avg Rouge-L = {avg_rouge_l:.4f} (Count: {len(preds)})")
        else:
            print(f"Alpha={alpha}: Data not found.")
            
    # alpha=0.2 で上手く答えられていて、alpha=1.0でRougeスコアが著しく落ちたプロンプトを特定する
    if not all_data["0.2"] or not all_data["1.0"]:
        print("Required alpha data missing for comparison.")
        return
        
    shared_instructions = set(all_data["0.2"].keys()).intersection(set(all_data["1.0"].keys()))
    
    # 低下幅 (alpha_0.2_rougeL - alpha_1.0_rougeL) を計算
    drops = []
    for inst in shared_instructions:
        r_02 = all_data["0.2"][inst].get('rougeL', 0)
        r_10 = all_data["1.0"][inst].get('rougeL', 0)
        drop = r_02 - r_10
        drops.append({
            'instruction': inst,
            'drop': drop,
            'r_02': r_02,
            'r_10': r_10,
            'gt': all_data["0.2"][inst].get('ground_truth', '')
        })
        
    # スコア低下が大きい順に並べ替え
    drops.sort(key=lambda x: x['drop'], reverse=True)
    
    print("\n\n--- スコア(Rouge-L) が大きく低下したプロンプト Top 5 ---")
    for i, item in enumerate(drops[:5]):
        inst = item['instruction']
        print(f"\n[{i+1}] スコア低下: {item['drop']:.4f} ( {item['r_02']:.4f} -> {item['r_10']:.4f} )")
        print(f"Q: {inst}")
        print(f"GT: {item['gt'].replace(chr(10), ' ')[:200]}...")
        print(f"A(alpha=0.2): {all_data['0.2'][inst]['prediction'].replace(chr(10), ' ')[:200]}...")
        print(f"A(alpha=1.0): {all_data['1.0'][inst]['prediction'].replace(chr(10), ' ')[:200]}...")
        
    # スコア低下がない、または微小なプロンプトの例（先ほどの抽出で見ていたようなもの）
    print("\n\n--- スコアがほぼ変わらない（堅牢だった）プロンプト サンプル ---")
    stable = [d for d in drops if abs(d['drop']) < 0.05]
    for i, item in enumerate(stable[:2]):
        inst = item['instruction']
        print(f"\n[{i+1}] スコア低下: {item['drop']:.4f} ( {item['r_02']:.4f} -> {item['r_10']:.4f} )")
        print(f"Q: {inst}")
        print(f"A(alpha=1.0): {all_data['1.0'][inst]['prediction'].replace(chr(10), ' ')[:200]}...")


if __name__ == "__main__":
    main()
