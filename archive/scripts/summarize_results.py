#!/usr/bin/env python3
"""
既存の評価結果を集計
"""
import json
import glob
from pathlib import Path
from collections import defaultdict

# 応答ファイルを集計
results = defaultdict(lambda: defaultdict(dict))

response_files = sorted(glob.glob('results/model_evaluation/responses_*.jsonl'))

print(f"Found {len(response_files)} response files\n")

for file_path in response_files:
    filename = Path(file_path).stem
    parts = filename.split('_')
    
    # ファイル名解析: responses_{model}_{adapter}_{dataset}_{timestamp}
    if 'llama' in filename:
        model = 'llama-3.1-8b'
        idx = 3  # llama-3.1-8b の後
    elif 'mistral' in filename:
        model = 'mistral-7b-v0.2'
        idx = 3
    else:
        continue
    
    # アダプター名を抽出
    adapter_parts = []
    dataset = None
    for i in range(idx, len(parts)):
        if parts[i] in ['jailbreak', 'beavertails', 'mmlu', 'repliqa', 'alpaca']:
            dataset = parts[i]
            break
        adapter_parts.append(parts[i])
    
    if not dataset:
        continue
    
    adapter = ' '.join(adapter_parts)
    
    # データを読み込み
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if not lines:
                continue
            
            # データセットごとの集計
            if dataset == 'jailbreak':
                # RtA計算
                resistant_count = sum(1 for line in lines if json.loads(line).get('is_resistant', False))
                rta = resistant_count / len(lines)
                results[model][adapter]['jailbreak'] = rta
                
            elif dataset == 'beavertails':
                # Refusal Rate計算
                refusal_count = sum(1 for line in lines if json.loads(line).get('is_refusal', False))
                harmful_count = sum(1 for line in lines if json.loads(line).get('is_harmful', False))
                results[model][adapter]['refusal_rate'] = refusal_count / len(lines)
                results[model][adapter]['harmful_rate'] = harmful_count / len(lines)
                
            elif dataset in ['mmlu', 'repliqa', 'alpaca']:
                # Accuracy/ROUGE-L計算
                if dataset == 'mmlu':
                    correct_count = sum(1 for line in lines if json.loads(line).get('is_correct', False))
                    accuracy = correct_count / len(lines)
                    results[model][adapter][dataset] = accuracy
                else:
                    # ROUGE-L平均
                    rouge_scores = [json.loads(line).get('rouge_l', 0) for line in lines]
                    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0
                    results[model][adapter][dataset] = avg_rouge
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        continue

# 結果を表示
for model in sorted(results.keys()):
    print(f"\n{'='*80}")
    print(f"Model: {model}")
    print('='*80)
    
    for adapter in sorted(results[model].keys()):
        print(f"\n{adapter}:")
        data = results[model][adapter]
        
        if 'jailbreak' in data:
            print(f"  Jailbreak Resistance (RtA): {data['jailbreak']:.2%}")
        
        if 'refusal_rate' in data:
            print(f"  Safety:")
            print(f"    Refusal Rate: {data['refusal_rate']:.2%}")
            print(f"    Harmful Response Rate: {data['harmful_rate']:.2%}")
        
        if any(k in data for k in ['mmlu', 'repliqa', 'alpaca']):
            print(f"  Utility:")
            if 'mmlu' in data:
                print(f"    MMLU: {data['mmlu']:.2%}")
            if 'repliqa' in data:
                print(f"    RepliQA (ROUGE-L): {data['repliqa']:.2%}")
            if 'alpaca' in data:
                print(f"    Alpaca (ROUGE-L): {data['alpaca']:.2%}")

print(f"\n{'='*80}\n")
