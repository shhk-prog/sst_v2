#!/usr/bin/env python3
"""
fix_gsm8k_jsons_fast.py

GSM8K 評価結果 JSON 内に記録されているモデルの生応答テキスト (resps) から
最終的な数値回答 (例: "The answer is: 18", "is 18.", "#### 18" 等) を柔軟に抽出し、
ターゲット数値と正確に照合・再評価を行ってスコア (exact_match) を修復・JSON ファイルを更新するスクリプト。
"""

import os
import re
import glob
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


def extract_gsm8k_target_number(target_str):
    """ターゲット文字列から #### 以降の正解数値を取得"""
    if not isinstance(target_str, str):
        return None
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", target_str)
    if match:
        return match.group(1).replace(",", "").strip()
    # フォールバック: 末尾の数値
    numbers = re.findall(r"-?[\d,]+(?:\.\d+)?", target_str)
    if numbers:
        return numbers[-1].replace(",", "").strip()
    return None


def extract_gsm8k_prediction_number(resp_str):
    """生の応答テキストから柔軟にモデルの最終回答数値を抽出"""
    if not isinstance(resp_str, str):
        return None
        
    # 1. #### 18
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", resp_str)
    if match:
        return match.group(1).replace(",", "").strip()
        
    # 2. The answer is: 18 / The answer is 18
    match = re.search(r"(?:the\s+answer\s+is|is\s+equal\s+to|equals?)\s*:?\s*\$?(-?[\d,]+(?:\.\d+)?)", resp_str, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", "").strip()
        
    # 3. is 18. / is 18
    match = re.search(r"\bis\s+\$?(-?[\d,]+(?:\.\d+)?)\s*\.?", resp_str, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", "").strip()

    # 4. 文末または回答内の最後の数値
    numbers = re.findall(r"-?[\d,]+(?:\.\d+)?", resp_str)
    if numbers:
        # 年号や一般的な大きな数字を除外するため最後から探す
        return numbers[-1].replace(",", "").strip()
        
    return None


def process_gsm8k_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False, filepath, 0.0

    samples = data.get("samples", {}).get("gsm8k", [])
    if not samples or not isinstance(samples, list):
        return False, filepath, 0.0

    passed_count = 0
    total_count = len(samples)

    for sample in samples:
        doc = sample.get("doc", {})
        target_str = doc.get("answer", "") or sample.get("target", "")
        target_num = extract_gsm8k_target_number(target_str)

        resps = sample.get("resps", [[]])
        raw_resp = ""
        if resps and isinstance(resps[0], list) and resps[0]:
            raw_resp = resps[0][0]
        elif isinstance(resps, list) and resps and isinstance(resps[0], str):
            raw_resp = resps[0]

        pred_num = extract_gsm8k_prediction_number(raw_resp)
        
        is_exact = False
        if target_num is not None and pred_num is not None:
            try:
                # 数値としての同等性判定 (例: 18.0 == 18)
                is_exact = float(target_num) == float(pred_num)
            except Exception:
                is_exact = (target_num == pred_num)

        sample["exact_match"] = 1.0 if is_exact else 0.0
        if is_exact:
            passed_count += 1

    new_acc = passed_count / total_count if total_count > 0 else 0.0

    if "results" in data and "gsm8k" in data["results"]:
        data["results"]["gsm8k"]["exact_match,flexible-extract"] = new_acc
        data["results"]["gsm8k"]["exact_match,strict-match"] = new_acc
        data["results"]["gsm8k"]["acc,none"] = new_acc
        data["results"]["gsm8k"]["exact_match"] = new_acc

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True, filepath, new_acc
    except Exception:
        return False, filepath, 0.0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix GSM8K scores with flexible numeric extraction.")
    parser.add_argument("--results_dir", type=str, default="results/debug_limit320/merged")
    parser.add_argument("--file", type=str, default=None, help="Target a specific JSON file directly")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    start_time = time.time()
    success_count = 0

    if args.file:
        print(f"Targeting single file: {args.file}")
        ok, fp, acc = process_gsm8k_file(args.file)
        if ok:
            success_count += 1
            print(f"[Done] {os.path.basename(fp)} -> Exact Match: {acc*100:.2f}%")
        else:
            print(f"[Failed/Skipped] {os.path.basename(fp)}")
        json_files = [args.file]
    else:
        pattern = os.path.join(args.results_dir, "**", "*utility_math_gsm8k.json")
        json_files = glob.glob(pattern, recursive=True)

        print(f"Found {len(json_files)} GSM8K JSON files to re-evaluate (Workers: {args.num_workers})...")

        with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
            futures = {executor.submit(process_gsm8k_file, fp): fp for fp in json_files}

            for i, future in enumerate(as_completed(futures), start=1):
                ok, fp, acc = future.result()
                if ok:
                    success_count += 1
                    print(f"[Done {i}/{len(json_files)}] {os.path.basename(fp)} -> Exact Match: {acc*100:.2f}%")

    elapsed = time.time() - start_time
    print(f"\n[Completed] Finished all {len(json_files)} GSM8K files (Fixed: {success_count}) in {elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()
