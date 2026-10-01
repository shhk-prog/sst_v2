# 実装計画: 感情分析 5 タスクのモデルマージ再現パイプラインの構築

残りの4つの感情分析タスク（Yelp, RT, SST2, Amazon）について、学習・Fisher情報の推定・評価を行う設定ファイルを作成し、最終的なモデルマージ処理までを一括で実行・整理できるパイプラインを構築します。

## ユーザーレビュー要求事項

> [!IMPORTANT]
> - Yelp や Amazon などの超巨大データセットの学習には膨大な時間がかかるため、再現実験を効率的かつリソースを抑えて行うために、Hugging Face Datasets のスライス機能（`train[:25000]`）を使用して各タスクの学習データを最大 25,000 サンプルに統一します。
> - これにより、全タスクのチェックポイントステップ数が一律 `checkpoint-1563` に統一され、管理が非常に容易になります。

## オープンクエスチョン

現在オープンな質問はありません。

## 提案する変更

### 1. 整理されたディレクトリ構成の定義
生成されるログや結果ファイルが散らからないよう、以下のディレクトリ構成に出力を整理します。
* `models/` : 各タスクのファインチューニングモデルの保存先
* `fishers/` : 各タスクの Fisher情報（Hessian）の保存先
* `metrics/` : 各モデルおよびマージ後の評価精度（JSON）の保存先
* `logs/` : 各プロセスの実行ログファイルの保存先

### 2. 設定ファイル (JSON) の新規作成
以下の 4 タスクに対して、それぞれ `学習`・`Fisher推定`・`評価` の設定ファイルを `scripts/` ディレクトリ配下に作成します。

#### Yelp タスク
* `finetune_roberta_yelp_run.json` (学習)
* `fisher_roberta_yelp_run.json` (Fisher推定)
* `evaluate_roberta_yelp_run.json` (評価)

#### Rotten Tomatoes (RT) タスク
* `finetune_roberta_rt_run.json`
* `fisher_roberta_rt_run.json`
* `evaluate_roberta_rt_run.json`

#### SST-2 タスク
* `finetune_roberta_sst2_run.json`
* `fisher_roberta_sst2_run.json`
* `evaluate_roberta_sst2_run.json`

#### Amazon タスク
* `finetune_roberta_amazon_run.json`
* `fisher_roberta_amazon_run.json`
* `evaluate_roberta_amazon_run.json`

### 3. 一括実行用マスタースクリプトの新規作成
#### [NEW] [run_model_merging_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/run_model_merging_pipeline.sh)
- 5タスク（IMDB含む）の学習・Fisher推定・評価を順次実行し、最後に `code/uncertainty_based_gradient_matching.py` を呼び出してモデルをマージし、マージ後のモデルの評価までを一括で行うシェルスクリプトを作成します。
- 各プロセスの出力を `logs/` ディレクトリに保存し、進捗状況をターミナルに見やすく表示します。

---

## 検証計画

### 自動検証
- スクリプト作成後、文法チェックを行い、正常に機能することを確認します。
- スクリプトの実行はユーザーのGPU環境（ターミナル）で行っていただきます。
