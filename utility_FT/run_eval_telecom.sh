#!/bin/bash

# TeleQnA (通信・専門ドメイン) 評価スクリプト
# TeleQnA公式リポジトリのOpenAI APIを、openai ライブラリの base_url を書き換えて
# ローカルLLM (Hugging Face + transformers) に直接接続して評価を行います。
# vLLM は使用しません。

RUN_ID=$1
SCRIPT_DIR="/mnt/nas/home/hiromi/src/sst_v2/utility_FT"

echo "Starting TeleQnA evaluation..."
cd "${SCRIPT_DIR}/TeleQnA"

if [ -z "$RUN_ID" ]; then
    echo "Evaluating BaseModel..."
    MODEL_PATH="meta-llama/Meta-Llama-3-8B-Instruct"
    PEFT_PATH=""
    OUT_DIR="${SCRIPT_DIR}/results/BaseModel"
else
    echo "Evaluating RUN_ID: ${RUN_ID}"
    MODEL_PATH="meta-llama/Meta-Llama-3-8B-Instruct"
    PEFT_PATH="${SCRIPT_DIR}/LLaMA-Factory/saves/llama3-8b/lora/${RUN_ID}"
    OUT_DIR="${SCRIPT_DIR}/results/${RUN_ID}"
fi

mkdir -p "$OUT_DIR"

# TeleQnA.txt の解凍 (まだ解凍されていない場合)
if [ ! -f "TeleQnA.txt" ]; then
    echo "Extracting TeleQnA dataset..."
    if command -v 7z &>/dev/null; then
        7z x -pteleqnadataset TeleQnA.zip
    elif command -v unzip &>/dev/null; then
        unzip -P teleqnadataset TeleQnA.zip || echo "WARNING: unzip failed (AES). Run: sudo apt install p7zip-full && 7z x -pteleqnadataset TeleQnA.zip"
    else
        echo "ERROR: Neither 7z nor unzip available. Install: sudo apt install p7zip-full"
    fi
fi

if [ ! -f "TeleQnA.txt" ]; then
    echo "WARNING: TeleQnA.txt not found. Skipping TeleQnA evaluation."
    exit 0
fi

# Hugging Face transformers を使って直接評価するPythonスクリプトを実行
# (公式のevaluation_tools.pyを呼ばず、公式run.pyのロジックをOpenAIなしで再現)
python3 - <<PYEOF
import json
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import os
import sys

MODEL_PATH = "${MODEL_PATH}"
PEFT_PATH = "${PEFT_PATH}"
QUESTIONS_PATH = "TeleQnA.txt"
OUT_PATH = "${OUT_DIR}/TeleQnA_answers.txt"

print(f"Loading model: {MODEL_PATH}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.bfloat16, device_map="cuda")

if PEFT_PATH:
    print(f"Loading PEFT adapter: {PEFT_PATH}")
    model = PeftModel.from_pretrained(model, PEFT_PATH)
    model = model.merge_and_unload()

model.eval()

with open(QUESTIONS_PATH, encoding="utf-8") as f:
    all_questions = json.loads(f.read())

results = {}
categories = []
correct_list = []

OPTION_KEYS = ["option 1", "option 2", "option 3", "option 4", "option 5"]

def predict_answer(question_data):
    q_text = question_data["question"]
    opts = {k: question_data[k] for k in OPTION_KEYS if k in question_data}
    prompt = f"Question: {q_text}\n"
    for opt_id, opt_text in opts.items():
        prompt += f"{opt_id}: {opt_text}\n"
    prompt += "Answer (state only the option number like 'option 1'):"
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=20, do_sample=False)
    out_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return out_text

for q_name, q_data in all_questions.items():
    pred = predict_answer(q_data)
    correct_answer = q_data.get("answer", "")
    # 正解のoption ID を抽出
    correct_option = correct_answer.split(":")[0].strip() if ":" in correct_answer else correct_answer.strip()
    is_correct = correct_option.lower() in pred.lower()
    
    results[q_name] = dict(q_data)
    results[q_name]["tested answer"] = pred
    results[q_name]["correct"] = is_correct
    categories.append(q_data.get("category", "unknown"))
    correct_list.append(is_correct)

with open(OUT_PATH, "w") as f:
    f.write(json.dumps(results))

res = pd.DataFrame({"categories": categories, "correct": correct_list})
summary = res.groupby("categories").mean()
summary["counts"] = res.groupby("categories").count()["correct"].values
print(summary)
print(f"\nFinal accuracy: {np.mean(correct_list):.4f}")
print(f"Results saved to: {OUT_PATH}")
PYEOF

echo "TeleQnA evaluation completed. Results saved in ${OUT_DIR}"
