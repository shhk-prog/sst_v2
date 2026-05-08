import os
import json
from datasets import load_dataset

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

def prepare_utility_data():
    """Utility (金融等) データセットのダウンロードと前処理"""
    print("Preparing Utility Dataset (Financial PhraseBank)...")
    try:
        # FPB (Financial PhraseBank) のダウンロード
        dataset = load_dataset("financial_phrasebank", "sentences_allagree")
        # SFT用にフォーマット (Instruction -> Response 形式に擬似的に変換)
        formatted_data = []
        for item in dataset["train"]:
            label_map = {0: "negative", 1: "neutral", 2: "positive"}
            formatted_data.append({
                "instruction": f"Analyze the sentiment of the following financial text and classify it as negative, neutral, or positive.\n\nText: {item['sentence']}",
                "output": label_map[item['label']]
            })
        
        out_path = os.path.join(DATA_DIR, "utility_fpb.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(formatted_data)} records to {out_path}")
    except Exception as e:
        print(f"Error preparing Utility data: {e}")

def prepare_safety_data():
    """Safety (Jailbreak等) データセットのダウンロードと前処理"""
    print("Preparing Safety Dataset (TrustLLM JailbreakTrigger & HarmBench)...")
    try:
        # TrustLLM JailbreakTrigger は直接ダウンロードが難しい場合があるためモック的に構成するか、公開データを使う
        # ここでは AdvBench や Toxic なプロンプトに対する拒絶応答を生成するセットを作成
        dataset = load_dataset("walledai/AdvBench", split="train")
        formatted_data = []
        refusal_response = "I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant. My safety guidelines strictly prohibit me from assisting with harmful, illegal, unethical, or dangerous activities."
        
        for item in dataset:
            formatted_data.append({
                "instruction": item['prompt'],
                "output": refusal_response
            })
            
        out_path = os.path.join(DATA_DIR, "safety_advbench.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(formatted_data)} records to {out_path}")
    except Exception as e:
        print(f"Error preparing Safety data: {e}")

if __name__ == "__main__":
    prepare_utility_data()
    prepare_safety_data()
    print("Data preparation complete.")
