#!/usr/bin/env python3
"""
clean_coding_data.py
====================
既存の utility_coding.json / utility_coding_eval.json に対して、
output フィールドのコードブロック外の説明文を除去するクリーニングを実行する。

使用方法:
    python clean_coding_data.py [--dry-run]

オプション:
    --dry-run  実際には書き込まず、クリーニング前後のサンプルを表示する

目的:
    Magicoder のデータセットでは output に以下のようなフォーマットが多い:
    ```python
    def foo():
        ...
    ```
    This solution provides... (説明文)

    説明文がコードブロックの後に続くため、モデルが「コードの後に説明文を書く」
    ことを学習してしまい、HumanEval 評価時に \\ndef で生成が途中打ち切られる原因になる。
    このスクリプトはコードブロックの中身のみを output に残す。
"""
import json
import re
import argparse
import os

from coding_data_utils import extract_code_from_output

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))


def clean_file(path: str, dry_run: bool = False):
    print(f"\n=== Processing: {path} ===")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    had_code_block = 0
    had_explanation = 0
    skipped_empty = 0
    cleaned_data = []

    for item in data:
        output_raw = item.get("output", "")
        has_block = bool(re.search(r'```[\w]*\n', output_raw))
        if has_block:
            had_code_block += 1

        output_clean = extract_code_from_output(output_raw)

        if not output_clean:
            skipped_empty += 1
            continue

        if has_block and output_clean != output_raw.strip():
            had_explanation += 1

        if dry_run and had_explanation <= 3 and has_block and output_clean != output_raw.strip():
            print(f"\n--- サンプル例 (説明文あり) ---")
            print(f"BEFORE (先頭200文字): {repr(output_raw[:200])}")
            print(f"AFTER  (先頭200文字): {repr(output_clean[:200])}")

        cleaned_data.append({**item, "output": output_clean})

    print(f"  Total          : {total}")
    print(f"  Code block あり: {had_code_block} ({had_code_block/total*100:.1f}%)")
    print(f"  説明文を除去   : {had_explanation} ({had_explanation/total*100:.1f}%)")
    print(f"  空になりスキップ: {skipped_empty}")
    print(f"  クリーニング後 : {len(cleaned_data)}")

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 上書き保存完了: {path}")
    else:
        print(f"  [DRY-RUN] 書き込みはスキップ")


def main():
    parser = argparse.ArgumentParser(description="Clean explanation text from coding dataset output fields.")
    parser.add_argument("--dry-run", action="store_true", help="実際に書き込まず確認だけ行う")
    args = parser.parse_args()

    targets = [
        os.path.join(DATA_DIR, "utility_coding.json"),
        os.path.join(DATA_DIR, "utility_coding_eval.json"),
    ]

    for path in targets:
        if not os.path.exists(path):
            print(f"[SKIP] ファイルが存在しません: {path}")
            continue
        clean_file(path, dry_run=args.dry_run)

    if args.dry_run:
        print("\n✅ DRY-RUN 完了。問題なければ --dry-run なしで再実行してください。")
    else:
        print("\n✅ クリーニング完了。")


if __name__ == "__main__":
    main()
