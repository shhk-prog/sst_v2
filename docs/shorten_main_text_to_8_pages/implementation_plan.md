# Implementation Plan: 論文の8ページ以内への短縮化

ユーザーの要望に従い、`flmsec.tex` のメインテキスト（参考文献より前の部分）を8ページ以内に収めるため、Section 6 (Results and Analysis) の詳細な実験結果・分析や大きな図表をAppendixに移動し、メインテキストには重要な要約のみを残す構成変更を行います。

## Goal Description
現在750行程度あるメインテキストから、スペースを大きく占有している図表（Figure 2, Table 5, Table 6, Table 7, Table 8）とそれに付随する詳細な分析をAppendixへ移動します。これにより、NeurIPS等で一般的な8ページの制限内に安全に収まる分量（実質4〜5ページ分のテキスト＋主要な表）にスリム化します。

## Proposed Changes

### 1. Section 6.1 予備実験結果 の移動
- **移動対象:** 6.1 予備実験（Preliminary Experiment）結果 の本文および Table 5 (`tab:simple_prelim`)
- **メインテキストへの変更:** 「予備実験における基礎的なトレードオフ検証の結果については、付録Cを参照されたい。」という一文のみを残し、セクション自体を削除または極小化します。

### 2. Section 6.4 および 6.5 の詳細分析の移動
- **移動対象:** 
  - 6.4 臨界点転移と偽の安全性の排除 (Figure 2 `fig:pareto_three_panel` を含む)
  - 6.5 出力崩壊のメカニズムと正常応答に基づくPareto AUC評価 (Table 6 `tab:pareto_auc` および Table 7 `tab:yugaioutou_rei` を含む)
- **メインテキストへの変更:** 
  これらのセクションを統合・要約し、「推論崩壊（偽の安全性）を排除した正常応答に基づくPareto AUC評価において提案手法が最も良好な結果を示したこと、および出力崩壊の具体的なメカニズム（Table 7等）については付録Dを参照されたい。」といった短い段落に置き換えます。

### 3. Section 6.7 計算効率と頑健性の移動
- **移動対象:** 6.7 計算効率と頑健性(RQ4) の本文および Table 8 (`tab:cost`)
- **メインテキストへの変更:** 「各手法の計算コストやデータ依存性に関する理論的比較については付録Eにまとめている。」という短い言及に留めます。

### 4. Appendix への追記
- `\appendix` セクション内に以下を新設し、抽出した内容を配置します。
  - **Appendix C: 予備実験（Preliminary Experiment）の追加結果**
  - **Appendix D: 偽の安全性（推論崩壊）の詳細分析とPareto AUC**
  - **Appendix E: 計算効率とデータ要件の詳細比較**

## User Review Required
> [!IMPORTANT]
> メインテキストから Figure 2 や Validity-aware Pareto AUC の Table 6 までも Appendix に移動する提案となっています。これらの図表のうち「これだけはメインテキストに残したい」というものがあればお知らせください（例えば、Figure 2 だけはメインに残す、等）。
> 特に指定がなければ、上記の計画に沿って一気にスリム化を実行します。
