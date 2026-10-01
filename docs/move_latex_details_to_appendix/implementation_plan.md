# Implementation Plan: 論文の構成変更（ベースライン手法と実験設計の付録への移動）

論文のメインテキストを簡潔にし、詳細な説明を付録（Appendix）に移動するための修正計画です。

## Goal Description
`flmsec.tex` に含まれている「ベースライン手法の詳しい説明」および「詳しい実験設計」を抽出して Appendix に移動し、メインテキストには簡潔な要約と関連する表（Table）のみを残します。

## Proposed Changes

### 1. Section 3 (Related Work) の修正
- **移動対象:** 
  - 3.2 基礎系統：Model SoupsとTask Arithmetic
  - 3.3 Fisher-Weighted Averagingと重要度系統
  - 3.4 干渉除去系：TIES、DARE、DELLA
  - 3.5 Safety–Utility特化系：MergeAlign、SafeMERGE、LED-Merging
  - 3.6 Fisher幾何型：AlignMergeとData-Free拡張
- **メインテキストに残すもの:**
  - 3.1 研究潮流の4フェーズ整理 (Table 1 を含む)
  - 3.7 関連研究の比較整理 (Table 2 を含む)
  - 移動したセクションの代わりに、「各ベースライン手法の数式を用いた詳細な説明については付録Aを参照されたい」という旨の簡単な要約を追加します。

### 2. Section 5 (Experiments) の修正
- **移動対象:**
  - 5.1 Target Models & Architecture の詳細なリスト
  - 5.2 Calibration Datasets & Curvature Estimation の詳細
  - 5.3 Evaluation Benchmarks & Metrics の詳細な数式（式13, 14）と説明文
  - 5.4 Evaluation Protocol & Baselines の詳細なリスト（予備実験と本実験のプロトコル詳細）
- **メインテキストに残すもの:**
  - 本実験で用いるモデル（Llama-2-7Bベース等）、キャリブレーションデータ概要、評価指標の簡単な説明。
  - Table 4 (評価タスク・指標および測定対象と望ましい基準の一覧)
  - 移動した詳細の代わりに、「実験で使用したモデルの詳細、ベンチマークごとの設定、および評価プロトコルの詳細については付録Bにまとめる」という旨の要約を追加します。

### 3. Appendix (\appendix) の修正
- ファイル末尾の `\appendix` セクション（現在 line 1102付近）に以下を追加します。
  - **Appendix A: ベースライン手法の詳細**（Section 3 から移動した内容）
  - **Appendix B: 実験設計の詳細**（Section 5 から移動した内容）

## User Review Required
> [!IMPORTANT]
> メインテキストに残す「簡単な説明」の分量や内容について、もし特定の事項（例えば特定の評価指標の定義だけは本文に残したい等）がありましたらお知らせください。
> 問題なければこの計画に基づいて `flmsec.tex` の編集を開始します。
