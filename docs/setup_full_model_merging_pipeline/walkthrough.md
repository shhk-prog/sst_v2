# 修正内容の確認 (Walkthrough): 感情分析 5 タスクのモデルマージ再現パイプラインの構築

5つの感情分析タスク（IMDB, Yelp, RT, SST2, Amazon）を一括で学習・Fisher推定・マージ・評価し、結果を構造化されたディレクトリに整理して出力するためのパイプラインを構築しました。

## 実施した変更

### 1. 設定ファイル (JSON) の作成とアップデート
各タスクの `学習(finetune)`・`Fisher情報推定`・`評価(evaluate)`・`マージ後評価` の設定ファイルを `scripts/` ディレクトリ配下に整備しました。
* **新規作成した設定ファイル群**:
  - `finetune_roberta_{task}_run.json` （学習データ数を `train[:25000]` に統一し、チェックポイントステップ数を `checkpoint-1563` に揃えるようスライス設計を行いました。※RTは元のサイズが小さいため全データ 8,530件、ステップ数 534 となります）
  - `fisher_roberta_{task}_run.json` （`dataset_test_split` に `train[:25000]` を指定し、勾配の計算に利用します）
  - `evaluate_roberta_{task}_run.json` （単体 Expert のテスト精度測定用）
  - `evaluate_roberta_merged_{task}.json` （マージ後モデルの各タスク上での精度測定用）
* **IMDB用設定ファイルのアップデート**:
  - 整理されたフォルダ構造（`models/imdb`、`fishers/imdb`、`metrics/imdb.json`）に出力されるよう、既存の設定をアップデートしました。

### 2. パイプラインスクリプトの作成
#### [run_model_merging_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/run_model_merging_pipeline.sh)
- **特徴**:
  - 多重実行時に、すでにファインチューニングされた重みや Fisher 情報ファイルが存在する場合は自動的にスキップして無駄な計算コストを省きます。
  - すべてのタスクの処理後、`code/uncertainty_based_gradient_matching.py` を呼び出してモデルをマージします。
  - マージ完了後、5タスクそれぞれでのマージ後精度を測定し、最後に結果を比較表（Markdown形式）としてターミナルに集計表示します。

---

## 実行・確認手順

構築したパイプラインは、以下の手順で実行できます。

### 1. 実行コマンド
ターミナル上で、作業用仮想環境（`venv_ugm`）があるディレクトリに移動し、スクリプトに実行権限を付与した上で実行してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging
chmod +x run_model_merging_pipeline.sh
./run_model_merging_pipeline.sh
```

### 2. 結果の整理先
スクリプトを実行すると、出力は以下のように自動で整理されて格納されます。

* **モデル**: `models/` (各タスクの `checkpoint-*` およびマージ後モデル `models/merged`)
* **Fisher重要度**: `fishers/` (各タスクの `hessian` フォルダ)
* **評価精度 JSON**: `metrics/` (`imdb.json` などの単体精度と、`merged_imdb.json` などのマージ後精度)
* **実行ログ**: `logs/` (プロセスごとの標準出力ログ。エラー発生時のデバッグに利用可能)

### 3. 出力される結果テーブルのイメージ
実行が完了すると、以下のように元の Expert 精度とマージ後（Ours）の精度の対比表が出力されます。

```
=== 再現実験結果サマリー (Accuracy) ===
| Task     | Expert (Single) | Merged (Ours)   | Diff       |
|----------|-----------------|-----------------|------------|
| imdb     | 0.94716         | 0.94680         | -0.00036   |
| yelp     | 0.96200         | 0.96110         | -0.00090   |
| rt       | 0.89500         | 0.89120         | -0.00380   |
| sst2     | 0.94300         | 0.94050         | -0.00250   |
| amazon   | 0.95100         | 0.95020         | -0.00080   |
==========================================================
```
