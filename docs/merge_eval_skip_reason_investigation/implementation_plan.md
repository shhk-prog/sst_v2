# 実装・調査計画: スキップ判定ロジックおよび結果ファイルの調査

## 調査方針
1. `scripts/merge_eval_parallel.py` における `--resume` 時のスキップ判定関数 `output_complete(path, limit)` のコードを分析。
2. スキップされなかった2つの結果ファイル (`utility_general_mmlu.json`, `alpaca_eval2.json`) および実行ログ (`sst_merge_v3_main_task_arithmetic_safety+medical_alpha0.6_seed43_seed43.log`) の内容を確認。
3. 他のスキップされた結果ファイル（例: `harmbench_safety.json`）のフォーマットと判定ロジックとの適合性を比較。

## 調査項目
- **`output_complete()` の条件**
  - ファイルの存在確認 (`find_latest_timestamped_file`)
  - JSON形式および辞書オブジェクトの検証
  - `"status"` / `"completed"` フィールドの有無
  - `win_rate` / `expected_n` / `count` の一致確認
- **`utility_general_mmlu.json` の検証**
  - MMLU結果ファイルの構造確認と `output_complete()` への不適合理由の特定
- **`alpaca_eval2.json` の検証**
  - 前回実行時のエラーログ/失敗ステータス (`"status": "failed"`) の確認
