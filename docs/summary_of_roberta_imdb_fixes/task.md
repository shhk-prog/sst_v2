# タスクリスト: Roberta-base-imdb の実行エラーに対する一連の修正まとめ

- `[x]` 各種エラーに対する設定ファイルの修正
  - `[x]` `evaluate_roberta_imdb_run.json` および `fisher_roberta_imdb_run.json` のモデルパス修正
  - `[x]` `fisher_roberta_imdb_run.json` への `dataset_val_split` の追加
  - `[x]` `evaluate_roberta_imdb_run.json` への `output_dir` の追加
- `[x]` 動作検証の完了
  - `[x]` 評価スクリプト（`predict.py`）がエラーなく完了し、metrics が出力されることを確認
  - `[x]` Fisher情報推定スクリプト（`train.py`）がエラーなく完了し、hessian が出力されることを確認
- `[x]` 統合ドキュメントの作成と整理
  - `[x]` 統合版の `walkthrough.md` などのドキュメントの保存
