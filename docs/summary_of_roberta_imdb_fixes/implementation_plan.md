# 実装計画: Roberta-base-imdb の実行エラーに対する一連の修正まとめ

`roberta-base-imdb` の Fisher 情報推定および評価の実行時において発生する、モデルパス、データセット、および引数の不整合を修正する計画です。

## 提案する変更

### 1. モデルパスの修正
モデルの `config.json` が存在する正しいチェックポイントディレクトリへのパスに更新します。
- `fisher_roberta_imdb_run.json` と `evaluate_roberta_imdb_run.json` の `model_name_or_path` を `"roberta-base-imdb/checkpoint-1563"` に変更します。

### 2. データ分割（Validation Split）の修正
IMDBデータセットに存在しない `"validation"` スプリットをロードするエラーを防ぐため、検証用スプリットを明示します。
- `fisher_roberta_imdb_run.json` に `"dataset_val_split": "test"` を追加します。

### 3. output_dir引数の追加
評価モード実行時において `TypeError` を防ぐため、必須である `output_dir` 引数を設定します。
- `evaluate_roberta_imdb_run.json` に `"output_dir": "roberta-base-imdb-eval"` を追加します。

## 検証計画
修正後、評価スクリプトおよびFisher情報推定スクリプトを実行し、エラーなく完了することを確認します。
- `python3 code/predict.py scripts/evaluate_roberta_imdb_run.json`
- `python3 code/train.py scripts/fisher_roberta_imdb_run.json`
