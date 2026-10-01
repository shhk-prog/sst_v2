# 実装計画: Roberta-base-imdb の config.json 読み込みエラーの修正

`roberta-base-imdb` の Fisher 情報推定および評価の実行時に、モデル設定ファイル `config.json` が見つからずに `OSError` となる問題を修正します。

## ユーザーレビュー要求事項

> [!NOTE]
> 修正対象は実行用設定ファイル（JSON）のみであり、ソースコード本体への変更はありません。

## オープンクエスチョン

現在オープンな質問はありません。

## 提案する変更

設定ファイルにおける `model_name_or_path` のパス指定を、チェックポイントが存在するサブフォルダである `roberta-base-imdb/checkpoint-1563` に更新します。

### iclr2024-model-merging/scripts

#### [MODIFY] [fisher_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_imdb_run.json)
- `"model_name_or_path": "roberta-base-imdb"` を `"roberta-base-imdb/checkpoint-1563"` に変更します。

#### [MODIFY] [evaluate_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/evaluate_roberta_imdb_run.json)
- `"model_name_or_path": "roberta-base-imdb"` を `"roberta-base-imdb/checkpoint-1563"` に変更します。

## 検証計画

### 手動検証
1. `baseline/iclr2024-model-merging` ディレクトリで以下のコマンドを実行し、エラーが発生せずに処理が開始することを確認します。
   ```bash
   venv_ugm/bin/python code/train.py scripts/fisher_roberta_imdb_run.json
   ```
