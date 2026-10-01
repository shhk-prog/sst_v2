# 論文公式コードのフル再現実験計画

ユーザーからの要望に基づき、公式コードが提供されている6つのモデルマージ手法について、`baseline/` ディレクトリ配下に `git clone` し、論文に記載されている条件（モデルサイズ、データセットなど）に従ってフルスケールでの再現実験を行います。

## ユーザーレビューが必要な項目

> [!WARNING]
> 1. **計算リソースと実行時間の考慮:**
>    - 論文に準拠したフルスケールの実験（LLaMA-3-8BやT5-Largeのマージ、およびGLUE、HarmBenchなどのフル評価）を実行するため、非常に長い処理時間（数時間〜数十時間）と大容量のGPUメモリが必要となります。
>    - 実験はバックグラウンドプロセスとして実行し、進捗およびログを記録します。
> 2. **コマンドの実行権限:**
>    - `git clone`、`pip install`、`python3` による学習・評価・マージスクリプトの実行、および `nvidia-smi` などのリソース監視コマンドを実行するため、ターミナルコマンド実行権限が必要です。

## 再現対象の手法およびリポジトリ

1. **model_merging** (Matena & Raffel, 2022)
   - リポジトリ: https://github.com/mmatena/model_merging
   - 状態: すでに `baseline/model_merging` に存在。
2. **iclr2024-model-merging** (Daheim et al., ICLR 2024)
   - リポジトリ: https://github.com/UKPLab/iclr2024-model-merging
   - 状態: クローンが必要。
3. **fisher-nodes-merging** (Thennal D K et al., LREC-COLING 2024)
   - リポジトリ: https://github.com/thennal10/fisher-nodes-merging
   - 状態: クローンが必要。
4. **df-merge** (Sanwoo Lee et al., NAACL 2025)
   - リポジトリ: https://github.com/sanwooo/df-merge
   - 状態: すでに `baseline/df-merge` に存在。
5. **LED-Merging** (Qianli Ma et al., ACL 2025)
   - リポジトリ: https://github.com/MqLeet/LED-Merging
   - 状態: クローンが必要。
6. **SafeMERGE** (Aladin Djuhera et al., 2025-2026)
   - リポジトリ: https://github.com/aladinD/SafeMERGE
   - 状態: すでに `baseline/SafeMERGE` に存在。

## 提案する変更（作成するファイル）

### 新規ドキュメントの作成

#### [NEW] [reproduction_report.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_reproduction/reproduction_report.md)
各手法のフル再現実験における設定、評価結果（元論文の記述数値と再現数値の比較）、遭遇した課題および実行ログへのリンクを記載した詳細なレポートを作成します。

## 実行フェーズのステップ

1. **未クローンリポジトリの取得:**
   - `git` コマンドを使用して、残りの3つのリポジトリを `baseline/` 下にクローンします。
2. **依存関係のセットアップ:**
   - 各リポジトリの環境要求（PyTorch, Transformers など）を満たすため、`venv_sst` などの適切な Python 仮想環境に依存パッケージをインストールします。
3. **フルスケール再現実験の実行:**
   - 各リポジトリの主要なマージ・評価スクリプトを、元論文で指定されているモデル（LLaMA-3, Mistral-7B, T5-Large, BERT-Base 等）とデータセット（GLUE, HarmBench, PAWS等）を用いてバックグラウンドで実行します。
4. **ログ・結果の整理:**
   - 実行結果を収集し、`reproduction_report.md` にまとめます。

## 検証計画

### 自動確認
- 各実験プロセスの標準出力・標準エラーログ（`*.log`）を保存し、完了ステータスおよび評価指標（Accuracy, F1, 安全性スコアなど）が正しく出力されていることを検証します。
