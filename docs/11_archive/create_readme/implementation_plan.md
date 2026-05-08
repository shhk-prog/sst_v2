# README.md 作成の実装計画

リポジトリルートにSST-Mergeプロジェクトの包括的な `README.md` を作成します。これにより、プロジェクトの目的、構造、および使用方法を他の開発者や研究者が容易に理解できるようになります。

## 目的

SST-Merge (Safety-Utility alignment via Generalized Eigenvalue Problem) 手法について、その理論的背景と実験的評価の手順を明確に示すドキュメントを整備する。

## 提案するREADME.mdの構成案

以下のセクションを設けて `README.md` を構成します。

1. **プロジェクト名と概要 (Title & Overview)**
   - SST-Merge の全体像の簡単な説明
   - Safety と Utility のトレードオフ（Safety Tax）を解消するための Generalized Eigenvalue Problem (GEVP) と Fisher Information Matrix を活用したマージング手法であることを記載。

2. **主な特徴 (Key Features)**
   - GEVPに基づく理論的な最適化
   - データフリー (Data-Free surrogate) アプローチのサポート
   - レイヤーごとの事前分布 (Layer-wise prior) による柔軟な調整

3. **リポジトリ構成 (Repository Structure)**
   - `core/`: 提案手法のコア実装
   - `scripts/`: 実験・評価スクリプト
   - `scripts/sst_eval_pipeline/`: 新しい5つの実験パイプライン (exp1〜exp5)
   - `docs/`: 理論、実装、実験計画のドキュメント
   - `data/`: 実験用データセット

4. **インストール (Installation)**
   - `requirements.txt` を用いた環境構築手順 (`pip install -r requirements.txt` など)

5. **使用方法と実験の実行 (Usage & Experiments)**
   - 全体実験の実行スクリプト (`run_all_experiments.sh`)
   - 評価パイプラインの使用例 (例: `python scripts/sst_eval_pipeline/exp2_fisher_ratio_pareto.py ...`)

6. **主な実験結果 (Key Results)**
   - 概要レベルでの結果への言及（または `experiment_summary.md` への誘導）

## User Review Required

> [!IMPORTANT]
> 提案している構成に、不足しているセクション（例：ライセンス情報、引用/Citationのプレースホルダー、特定の用語の補足など）や、特に強調したいポイントはありますか？問題なければこの構成で `README.md` の作成に進みます。

## Verification Plan

- ルートディレクトリに `README.md` が正しく作成され、Markdownとして正しくレンダリングできるフォーマットになっているかを確認する。
- リンク切れ（特に `scripts/` や `docs/` 内の既存ファイルへのリンク）が発生していないか目視確認する。
