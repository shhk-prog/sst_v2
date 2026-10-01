# 実装計画: evaluate_roberta_imdb_run.json における output_dir 不足エラーの修正

`predict.py`（評価モード）の実行時に、設定ファイル `evaluate_roberta_imdb_run.json` に `output_dir` が指定されていないため、`Seq2SeqTrainingArguments` の初期化において `TypeError` が発生する問題を修正します。

## ユーザーレビュー要求事項

> [!NOTE]
> 今回も設定ファイル（JSON）のみの修正となり、コードの変更はありません。

## オープンクエスチョン

現在オープンな質問はありません。

## 提案する変更

評価実行時（`RunMode.PREDICT`）に `Trainer` クラスおよび `Seq2SeqTrainingArguments` のインスタンス化に必要なダミーの出力先ディレクトリとして、`output_dir` を設定ファイルに追加します。

### iclr2024-model-merging/scripts

#### [MODIFY] [evaluate_roberta_imdb_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/evaluate_roberta_imdb_run.json)
- `"output_dir": "roberta-base-imdb-eval"` を追加します。

## 検証計画

### 手動検証
1. `baseline/iclr2024-model-merging` ディレクトリで以下のコマンドを実行し、エラーが発生せずに評価処理が開始することを確認します。
   ```bash
   venv_ugm/bin/python code/predict.py scripts/evaluate_roberta_imdb_run.json
   ```
