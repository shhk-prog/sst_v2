import json

file_path = "/mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory/data/dataset_info.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# MedQAのエントリを追加
data["medqa"] = {
    "hf_hub_url": "GBaker/MedQA-USMLE-4-options",
    "columns": {
        "prompt": "question",
        "response": "answer"
    }
}

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Successfully added 'medqa' to dataset_info.json")
