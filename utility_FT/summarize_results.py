import os
import json
import pandas as pd

results_dir = "/mnt/nas/home/hiromi/src/sst_v2/utility_FT/results"
models = [
    "BaseModel",
    "model1_math_ep3.0_bs16_lr2.0e-4",
    "model2_coding_ep3.0_bs16_lr2.0e-4",
    "model3_medicine_ep3.0_bs16_lr2.0e-4"
]

data = []

for model in models:
    model_dir = os.path.join(results_dir, model)
    if not os.path.isdir(model_dir):
        print(f"Skipping {model} - Directory not found.")
        continue
    
    # JSON ファイルを探す
    json_files = [f for f in os.listdir(model_dir) if f.endswith(".json")]
    if not json_files:
        print(f"Skipping {model} - No JSON results found.")
        continue
    
    # 最初のJSONファイルを読み込む（結果ファイル）
    with open(os.path.join(model_dir, json_files[0]), 'r') as f:
        res = json.load(f)
        
    metrics = res.get("results", {})
    
    row = {"Model": model}
    
    # GSM8K
    gsm8k = metrics.get("gsm8k", {})
    row["GSM8K (exact_match)"] = gsm8k.get("exact_match,strict-match", gsm8k.get("exact_match", "N/A"))
    
    # PubMedQA
    pubmedqa = metrics.get("pubmedqa", {})
    row["PubMedQA (acc)"] = pubmedqa.get("acc,none", pubmedqa.get("acc", "N/A"))
    
    # BoolQ
    boolq = metrics.get("boolq", {})
    row["BoolQ (acc)"] = boolq.get("acc,none", boolq.get("acc", "N/A"))
    
    # MRPC
    mrpc = metrics.get("mrpc", {})
    row["MRPC (f1)"] = mrpc.get("f1,none", mrpc.get("f1", "N/A"))
    
    data.append(row)

df = pd.DataFrame(data)
print(df.to_markdown(index=False))
