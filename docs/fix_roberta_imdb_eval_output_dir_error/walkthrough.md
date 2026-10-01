# 修正内容の確認 (Walkthrough): evaluate_roberta_imdb_run.json における output_dir 不足エラーの修正

`predict.py`（評価モード）の実行時に、設定ファイル `evaluate_roberta_imdb_run.json` に `output_dir` が指定されていないため、`Seq2SeqTrainingArguments` の初期化において `TypeError` が発生する問題を修正しました。

## 変更内容

### 設定ファイルの修正
`Seq2SeqTrainingArguments` の初期化に必須となる `output_dir` パラメータを満たすため、ダミーの出力先ディレクトリ名を追加しました。

#### [evaluate_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/evaluate_roberta_imdb_run.json)
```diff
     "prediction_output_file": "roberta_base_imdb.search_output.json",
     "dataset_name": "/mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/merging/datasets/imdb.py",
     "dataset_config_name": "classification",
-    "dataset_test_split": "test"
+    "dataset_test_split": "test",
+    "output_dir": "roberta-base-imdb-eval"
 }
```

## 検証方法

以下のコマンドをターミナルで実行し、エラーが発生せずに評価処理が開始されることを確認してください。

### 検証用コマンド
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging
venv_ugm/bin/python code/predict.py scripts/evaluate_roberta_imdb_run.json
```
