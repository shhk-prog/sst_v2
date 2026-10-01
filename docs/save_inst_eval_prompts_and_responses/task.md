# タスクリスト

- [x] `v3/scripts/eval_instruction_datasets.py` の `compute_generation_metrics` 関数を修正し、詳細ログ（プロンプト・ターゲット・モデル応答・類似度）を返却するようにする
- [x] 同スクリプトの `main` 関数で詳細ログを JSON 結果に出力するよう修正する
- [x] 修正後のスクリプトを少数のサンプル制限（limit=2）で実行し、JSON 内に `eval_details` が正常に出力されるか確認する（ユーザー環境での実行を推奨）
