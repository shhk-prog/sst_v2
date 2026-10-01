# df-merge ベースラインの実行計画

提供されたリポジトリ (`baseline/df-merge`) の README の手順に従い、環境構築からモデルのダウンロード、ファインチューニング(FT)、DF-Mergeの実行、および評価までの一連の流れを実行します。

## User Review Required

> [!IMPORTANT]
> 以下の手順で実行を進めてよろしいでしょうか？
> 特に、モデルは `t5-base` と `t5-large` のどちらで実行するか、あるいは両方実行するかご指定がある場合はお知らせください（本計画ではデフォルトとして `t5-base` で進める想定としています）。
> また、ファインチューニングにはGPUリソースと時間がかかります。バックグラウンドで実行し、適宜進捗をご報告する形で進める予定です。

## Proposed Changes

以下の手順で作業を行います。これらの作業内容は `docs/df_merge_baseline/task.md` にリスト化し、進捗を管理します。作業の履歴は `docs/df_merge_baseline/walkthrough.md` に随時追記します。

### 1. 環境構築
- `baseline/df-merge` ディレクトリにて `poetry install` を実行し、依存パッケージをインストールします。
- 必要に応じて、`poetry shell` で環境を有効化するか、`poetry run python ...` の形式で後続のスクリプトを実行します。

### 2. データセットとモデルのダウンロード
- **データセット**: `download_dataset.py` を作成・実行し、READMEに記載の6つのデータセット (`paws`, `qasc`, `quartz`, `story_cloze`, `wiki_qa`, `winogrande`) をダウンロード・保存します。
- **モデル**: `download_models.py` を作成・実行し、`.models/` ディレクトリに `google-t5/t5-base` (必要に応じて `t5-large`) をダウンロードします。
- **promptsource**: `promptsource` パッケージを clone してインストールします。

### 3. ファインチューニング (FT)
- `src/finetune.py` を用いて、各データセット (`paws`, `qasc`, `quartz`, `story_cloze`, `wiki_qa`, `winogrande`) に対して `t5-base` モデルのファインチューニングを行います。
- 実行後、モデルのチェックポイントが `./experiments/finetune/default/ckpt/t5-base/{dataset}/seed42/` に保存されることを確認します。

### 4. DF-Merge と評価の実行
- ファインチューニングしたチェックポイントを使用し、`src/df-merge.py` を実行して DF-Merge とその評価を行います。
- `acquisition_fn` は `ei` および `ucb` を指定し、結果が `experiments/df-merge/merge/metrics/...` に出力されることを確認します。

## Verification Plan

### 自動テスト
- データセットのダウンロード完了後、`.dataset` フォルダの中身を確認します。
- ファインチューニング完了後、各モデルのチェックポイントが生成されているか確認します。
- DF-Merge実行後、評価結果のメトリクスファイルが正常に出力されていることを確認し、その内容を報告します。
