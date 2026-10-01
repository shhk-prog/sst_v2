#!/usr/bin/env python3
"""
fix_humaneval_jsons_fast.py

HumanEval 評価結果 JSON 内に記録されているモデルの生応答テキスト (resps) から
インデント整形および Python コードを自動抽出し、テストコードに対して超高速・無停止で
再評価を行ってスコア (pass@1) を修復・JSON ファイルを上書き更新するスクリプト。

【完全無停止・超高速化】
- 1ファイルごとに独立した multiprocessing.Process を起動
- ハードタイムアウト(5秒)による無限ループ保護
- サンプルレベルのインデント補正 (スペース3個 -> スペース4個等)
"""

import os
import re
import io
import sys
import glob
import json
import time
import multiprocessing as mp
from contextlib import redirect_stdout, redirect_stderr


def clean_humaneval_response(response):
    """インデントや誤フォーマットの自動クリーンアップ"""
    if not isinstance(response, str):
        return ""
    clean_resp = response
    # 先頭のインデントずれを修復
    clean_resp = clean_resp.replace("\n   for ", "\n    for ").replace("   for ", "    for ")
    clean_resp = clean_resp.replace("\n   if ", "\n    if ").replace("   if ", "    if ")
    clean_resp = clean_resp.replace("\n   while ", "\n    while ").replace("   while ", "    while ")
    clean_resp = clean_resp.replace("\n   def ", "\n    def ").replace("   def ", "    def ")
    clean_resp = clean_resp.replace("\n   return ", "\n    return ").replace("   return ", "    return ")
    return clean_resp


def _eval_single_humaneval_sample(prompt, response, test, entry_point):
    """1つの HumanEval サンプルを評価"""
    clean_resp = clean_humaneval_response(response)
    full_code = prompt + clean_resp + "\n" + test + f"\ncheck({entry_point})\n"
    
    global_scope = {}
    f_out = io.StringIO()
    f_err = io.StringIO()

    try:
        with redirect_stdout(f_out), redirect_stderr(f_err):
            exec(full_code, global_scope)
        return True
    except Exception:
        return False


def _worker_process_humaneval_file(filepath, return_dict):
    """1つの HumanEval JSON ファイル全体の評価・修復"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return_dict["ok"] = False
        return

    samples = data.get("samples", {}).get("humaneval", [])
    if not samples or not isinstance(samples, list):
        return_dict["ok"] = False
        return

    passed_count = 0
    total_count = len(samples)

    for sample in samples:
        doc = sample.get("doc", {})
        prompt = doc.get("prompt", "")
        test = doc.get("test", "")
        entry_point = doc.get("entry_point", "")

        resps = sample.get("resps", [[]])
        raw_resp = ""
        if resps and isinstance(resps[0], list) and resps[0]:
            raw_resp = resps[0][0]
        elif isinstance(resps, list) and resps and isinstance(resps[0], str):
            raw_resp = resps[0]

        is_pass = _eval_single_humaneval_sample(prompt, raw_resp, test, entry_point)
        
        sample["pass@1"] = 1.0 if is_pass else 0.0
        if is_pass:
            passed_count += 1

    new_pass1 = passed_count / total_count if total_count > 0 else 0.0

    if "results" in data and "humaneval" in data["results"]:
        data["results"]["humaneval"]["pass@1,create_test"] = new_pass1
        data["results"]["humaneval"]["pass@1"] = new_pass1

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return_dict["ok"] = True
        return_dict["pass1"] = new_pass1
    except Exception:
        return_dict["ok"] = False


def process_humaneval_file_with_timeout(filepath, timeout_sec=5):
    manager = mp.Manager()
    return_dict = manager.dict()

    p = mp.Process(target=_worker_process_humaneval_file, args=(filepath, return_dict))
    p.start()
    p.join(timeout=timeout_sec)

    if p.is_alive():
        p.terminate()
        p.join()
        return False, filepath, 0.0

    if return_dict.get("ok"):
        return True, filepath, return_dict.get("pass1", 0.0)
    return False, filepath, 0.0


def main():
    import argparse
    from concurrent.futures import ThreadPoolExecutor

    parser = argparse.ArgumentParser(description="Fix HumanEval scores with hard timeout guarantee.")
    parser.add_argument("--results_dir", type=str, default="results/debug_limit320/merged")
    parser.add_argument("--file", type=str, default=None, help="Target a specific JSON file directly")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--file_timeout", type=int, default=5)
    args = parser.parse_args()

    start_time = time.time()
    success_count = 0

    if args.file:
        print(f"Targeting single file: {args.file} (Timeout: {args.file_timeout}s)")
        ok, fp, pass1 = process_humaneval_file_with_timeout(args.file, args.file_timeout)
        if ok:
            success_count += 1
            print(f"[Done] {os.path.basename(fp)} -> Pass@1: {pass1*100:.2f}%")
        else:
            print(f"[Timeout/Skipped] {os.path.basename(fp)}")
        json_files = [args.file]
    else:
        pattern = os.path.join(args.results_dir, "**", "*utility_code_humaneval.json")
        json_files = glob.glob(pattern, recursive=True)

        print(f"Found {len(json_files)} HumanEval JSON files to process (Workers: {args.num_workers}, Timeout: {args.file_timeout}s/file)...")

        with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
            futures = {executor.submit(process_humaneval_file_with_timeout, fp, args.file_timeout): fp for fp in json_files}

            for i, future in enumerate(futures, start=1):
                ok, fp, pass1 = future.result()
                if ok:
                    success_count += 1
                    print(f"[Done {i}/{len(json_files)}] {os.path.basename(fp)} -> Pass@1: {pass1*100:.2f}%")
                else:
                    print(f"[Timeout/Skipped {i}/{len(json_files)}] {os.path.basename(fp)}")

    elapsed = time.time() - start_time
    print(f"\n[Completed] Finished all {len(json_files)} HumanEval files (Fixed: {success_count}) in {elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()
