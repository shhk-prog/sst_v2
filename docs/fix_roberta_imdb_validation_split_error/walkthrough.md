# 修正内容の確認 (Walkthrough): Roberta-base-imdb の validation スプリットエラー of 修正

IMDBデータセットに存在しない `"validation"` スプリットをロードしようとして `ValueError` が発生する問題を修正しました。

## 変更内容

### 設定ファイルの修正
IMDBデータセットには `train` と `test` スプリットしか存在しないため、`dataset_val_split` の値を明示的に `"test"` に指定するように設定を追加しました。

#### [fisher_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_imdb_run.json)
```diff
     "output_dir": "roberta-base-imdb-fisher",
     "dataset_name": "/mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/merging/datasets/imdb.py",
     "dataset_config_name": "classification",
-    "dataset_test_split": "train"
+    "dataset_test_split": "train",
+    "dataset_val_split": "test"
 }
```

## 検証方法

以下のコマンドをターミナルで実行し、データセットが正しくロードされ、エラーが発生しないことを確認してください。

### 検証用コマンド
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging
venv_ugm/bin/python code/train.py scripts/fisher_roberta_imdb_run.json
```
