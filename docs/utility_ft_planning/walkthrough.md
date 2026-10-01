# Utility FT フルパイプライン実行・評価 Walkthrough (総括レポート)

## 概要
本プロジェクトでは、モデルマージおよびPerformance Retain Rate (PRR) などの検証・先行研究の比較を目的として、ベースモデル（`Meta-Llama-3-8B-Instruct`）に対し異なる3つの専門ドメイン（数学・コーディング・医学）のFine-Tuningモデルを構築し、公式の評価ハーネスを用いた網羅的な評価パイプラインを構築しました。

## 実施内容と成果

### 1. 開発環境・ツールのセットアップ
- 評価フレームワークとして `lm-evaluation-harness` および `bigcode-evaluation-harness` を公式リポジトリからcloneし、正常に動作する環境を構築しました。
- FT実行用として `LLaMA-Factory` を導入し、効率的なLoRA学習パイプラインを整備しました。

### 2. 専門ドメインモデルの構築 (Utility FT)
ハイパーパラメータごとにモデルや評価結果を区別して管理する仕組みを導入し、以下の3つのモデルに対してLoRAを用いた学習（フルデータ, 3 Epochs）を正常に完了しました。
1. **Model 1 (Math)**: `mathinstruct` データセット
2. **Model 2 (Coding)**: `sahil2801/CodeAlpaca-20k` データセット
3. **Model 3 (Medicine)**: `GBaker/MedQA-USMLE-4-options` データセット

生成された RUN_ID（例: `model1_math_ep3.0_bs16_lr2.0e-4`）に基づき、学習結果は別々のディレクトリに保存されています。

### 3. ベースラインおよびモデル一括評価 (lm-evaluation-harness)
各モデルおよびベースモデルに対し、代表的なタスク (`gsm8k`, `pubmedqa`, `boolq`, `mrpc`) の本番評価スクリプト (`run_eval_all_utility.sh`) を実行しました。

| 評価タスク (Metric) | BaseModel (Llama-3-8B) | Model1 (Math) | Model2 (Coding) | Model3 (Medicine) |
|---------------------|------------------------|---------------|-----------------|-------------------|
| **GSM8K** (Exact Match)| **75.7%**             | 60.2%         | 63.8%           | 57.6%             |
| **PubMedQA** (Accuracy)| 74.4%                  | 73.8%         | 72.0%           | **74.6%**         |
| **BoolQ** (Accuracy)   | 84.5%                  | 80.1%         | 84.3%           | **84.6%**         |
| **MRPC** (Accuracy)    | **69.6%**             | 69.4%         | 68.6%           | 68.4%             |

> [!NOTE]
> - フルデータでの学習・評価が正常に完了し、各ハイパーパラメータに紐づくディレクトリ（例: `results/model1_math_ep3.0_bs16_lr2.0e-4`）にスコアが保存されました。
> - ベースモデルと比較すると、Model3 (Medicine) で PubMedQA のスコア向上が確認できます。
> - この評価パイプラインにより、今後マージ手法のPerformance Retain Rate (PRR) を一元的に算出・比較できる基盤が完成しました。

## 今後のステップ
- 構築したベースラインモデルとFTモデルを用いて、既存のモデルマージ手法（Fisher-Weighted Averaging等）の比較・検証フェーズへ移行
- マージ後モデルのPRR（性能保持率）の定量化と、ドメイン特化性能の両立性の分析
