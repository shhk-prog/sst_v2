# 修正内容の確認 (Walkthrough): Roberta-base-imdb の config.json 読み込みエラーの修正

`roberta-base-imdb` の Fisher 情報推定および評価の実行時に、モデル設定ファイル `config.json` が見つからずに `OSError` となる問題を修正しました。

## 変更内容

### 設定ファイルのパス修正
モデル学習（Fine-tuning）の出力ディレクトリ `roberta-base-imdb` の中には直接 `config.json` がなく、実際には `roberta-base-imdb/checkpoint-1563` の下に保存されていました。
そのため、実行用設定ファイル内の `model_name_or_path` の値を正しいチェックポイントディレクトリに修正しました。

#### [fisher_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_imdb_run.json)
```diff
 {
-    "model_name_or_path": "roberta-base-imdb",
+    "model_name_or_path": "roberta-base-imdb/checkpoint-1563",
     "method": "sequence_classification_squared_gradients",
```

#### [evaluate_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/evaluate_roberta_imdb_run.json)
```diff
 {
-    "model_name_or_path": "roberta-base-imdb",
+    "model_name_or_path": "roberta-base-imdb/checkpoint-1563",
     "per_device_eval_batch_size": 32,
```

## 検証方法

以下のコマンドをターミナルで実行し、モデルが正しく読み込まれ、`config.json` に起因する `OSError` が発生せずに処理が開始されることを確認してください。

### 検証用コマンド
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging
venv_ugm/bin/python code/train.py scripts/fisher_roberta_imdb_run.json
```
