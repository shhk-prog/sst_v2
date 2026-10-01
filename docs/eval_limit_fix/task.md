# タスクリスト: eval スクリプトのlimit/データセット件数対応修正

## 目的
各evalスクリプトが「1件ずつ応答を保存し、実行時にlimit以下であれば足りない分のみ生成する」という要件に正しく対応しているかを確認し、問題点を修正する。

## タスク

- [x] 各スクリプトのコード調査
  - [x] `eval_alpaca.py` — 調査
  - [x] `eval_instruction_datasets.py` — 調査
  - [x] `eval_safety.py` — 調査
  - [x] `eval_utility.py` — 調査
  - [x] `merge_eval_parallel.py` — 調査
- [x] 問題点の特定
  - [x] `eval_safety.py`: `is_complete()` が `limit` パラメータを使っていない
  - [x] `eval_utility.py`: `is_completed_output()` が `limit` パラメータを使っていない
  - [x] `merge_eval_parallel.py`: `get_expected_n()` が途中停止とデータセット小を区別できない
- [x] 修正実施
  - [x] `eval_safety.py`: `is_complete()` に `expected_n > limit` チェックを追加
  - [x] `eval_utility.py`: `is_completed_output()` に `expected_n > limit` チェックを追加（lm_evalの実行ロジックは維持）
  - [x] `merge_eval_parallel.py`: `get_expected_n()` に `completed=True` のチェックを追加
- [x] ドキュメント作成
