# 実装計画: Roberta-base-imdb の validation スプリットエラーの修正

前回のパス修正後に `train.py` を実行したところ、IMDBデータセットに存在しない `"validation"` スプリットをロードしようとして `ValueError` が発生する新たな問題が見つかりました。このエラーを解決するための計画です。

## ユーザーレビュー要求事項

> [!NOTE]
> 今回も設定ファイル（JSON）のみの修正となり、コードの変更はありません。

## オープンクエスチョン

現在オープンな質問はありません。

## 提案する変更

IMDBデータセットには `train` と `test` スプリットしか存在しないため、`dataset_val_split` の値を明示的に `"test"` に指定します。

### iclr2024-model-merging/scripts

#### [MODIFY] [fisher_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_imdb_run.json)
- `"dataset_val_split": "test"` を追加します。

## 検証計画

### 手動検証
1. `baseline/iclr2024-model-merging` ディレクトリで以下のコマンドを実行し、データセットが正しくロードされ、エラーが発生しないことを確認します。
   ```bash
   venv_ugm/bin/python code/train.py scripts/fisher_roberta_imdb_run.json
   ```
