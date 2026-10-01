#!/usr/bin/env python3
"""
fix_mbpp_jsons_fast.py

MBPP 評価結果 JSON 内に記録されているモデルの生応答テキスト (resps) から
Python コードを安全に抽出し、テストコードに対して再評価を行って
スコア (pass@1) を修復・JSON ファイルを上書き更新するスクリプト。

【完全無停止・堅牢化の仕組み】
- 1ファイルごとに独立した multiprocessing.Process を起動
- タイムアウト(例: 10秒)を超えたフリーズコードは p.terminate() で強制切断して確実に次へ進行
- 絶対に途中でフリーズしない完全安定並列処理
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


def extract_python_code(text):
    """生応答テキストから Python コードブロックを抽出する。"""
    if not isinstance(text, str):
        return ""

    # 1. ```python ... ```
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 2. ``` ... ```
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        code_candidate = match.group(1).strip()
        if "def " in code_candidate or "return " in code_candidate:
            return code_candidate

    # 3. def ... から始まる関数定義
    match = re.search(r"(def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*)", text, re.DOTALL)
    if match:
        code_lines = []
        for line in match.group(1).splitlines():
            if line.startswith("The answer is:") or line.startswith("[INST]") or line.startswith("```"):
                break
            code_lines.append(line)
        return "\n".join(code_lines).strip()

    return text.strip()


def _eval_single_sample(code, test_list):
    """1つのサンプルを評価 (print抑止)"""
    full_code = code + "\n\n" + "\n".join(test_list) + "\n"
    global_scope = {}
    f_out = io.StringIO()
    f_err = io.StringIO()

    try:
        with redirect_stdout(f_out), redirect_stderr(f_err):
            exec(full_code, global_scope)
        return True
    except Exception:
        return False


def _worker_process_file(filepath, return_dict):
    """ワーカープロセス: 1ファイルの評価を実行し結果を return_dict に格納"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return_dict["ok"] = False
        return

    samples = data.get("samples", {}).get("mbpp", [])
    if not samples:
        return_dict["ok"] = False
        return

    passed_count = 0
    total_count = len(samples)

    for sample in samples:
        doc = sample.get("doc", {})
        test_list = doc.get("test_list", [])
        resps = sample.get("resps", [[]])

        raw_resp = ""
        if resps and isinstance(resps[0], list) and resps[0]:
            raw_resp = resps[0][0]
        elif isinstance(resps, list) and resps and isinstance(resps[0], str):
            raw_resp = resps[0]

        code = extract_python_code(raw_resp)
        is_pass = _eval_single_sample(code, test_list)
        
        sample["pass_at_1"] = 1.0 if is_pass else 0.0
        if is_pass:
            passed_count += 1

    new_pass1 = passed_count / total_count if total_count > 0 else 0.0

    if "results" in data and "mbpp" in data["results"]:
        data["results"]["mbpp"]["pass_at_1,none"] = new_pass1
        data["results"]["mbpp"]["pass@1"] = new_pass1

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return_dict["ok"] = True
        return_dict["pass1"] = new_pass1
    except Exception:
        return_dict["ok"] = False


def process_file_with_hard_timeout(filepath, timeout_sec=5):
    """1ファイルにつき最大 timeout_sec 秒で強制管理し、無限ループを確実に撃破"""
    manager = mp.Manager()
    return_dict = manager.dict()

    p = mp.Process(target=_worker_process_file, args=(filepath, return_dict))
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

    parser = argparse.ArgumentParser(description="Fix MBPP scores with hard timeout guarantee.")
    parser.add_argument("--results_dir", type=str, default="results/debug_limit320/merged")
    parser.add_argument("--file", type=str, default=None, help="Target a specific JSON file directly")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--file_timeout", type=int, default=5, help="Hard timeout per file in seconds")
    args = parser.parse_args()

    start_time = time.time()
    success_count = 0

    if args.file:
        print(f"Targeting single file: {args.file} (Timeout: {args.file_timeout}s)")
        ok, fp, pass1 = process_file_with_hard_timeout(args.file, args.file_timeout)
        if ok:
            success_count += 1
            print(f"[Done] {os.path.basename(fp)} -> Pass@1: {pass1*100:.2f}%")
        else:
            print(f"[Timeout/Skipped] {os.path.basename(fp)}")
        json_files = [args.file]
    else:
        pattern = os.path.join(args.results_dir, "**", "*utility_code_mbpp.json")
        json_files = glob.glob(pattern, recursive=True)

        print(f"Found {len(json_files)} MBPP JSON files to process (Workers: {args.num_workers}, Timeout: {args.file_timeout}s/file)...")

        # マルチスレッドで硬直監視プロセス群を発行・スケジューリング
        with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
            futures = {executor.submit(process_file_with_hard_timeout, fp, args.file_timeout): fp for fp in json_files}

            for i, future in enumerate(futures, start=1):
                ok, fp, pass1 = future.result()
                if ok:
                    success_count += 1
                    print(f"[Done {i}/{len(json_files)}] {os.path.basename(fp)} -> Pass@1: {pass1*100:.2f}%")
                else:
                    print(f"[Timeout/Skipped {i}/{len(json_files)}] {os.path.basename(fp)}")

    elapsed = time.time() - start_time
    print(f"\n[Completed] Finished all {len(json_files)} files (Fixed: {success_count}) in {elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()

