# Implementation Plan

## Goal Description
vLLM環境の評価結果に基づき、端点補完なしのObserved-range AUCとValidity-aware Pareto AUCの比較を行う表（Table D.2等）を作成する。
これに伴い、`v3/scripts/analysis/calculate_observed_range_auc.py` のスクリプトを作成・実行し、その結果を用いて `v3/docs/flmsec/flmsec.tex` 内の「補完なしAUC（Observed-range AUC）とValidity-aware Pareto AUCの比較」の表を更新する。

## 提案する変更
- **[NEW]** `v3/scripts/analysis/calculate_observed_range_auc.py`: 評価結果（ASRおよびUtility）からObserved-range AUCとValidity-aware Pareto AUCを計算し、ターミナルに出力するスクリプトを作成。
- **[MODIFY]** `v3/docs/flmsec/flmsec.tex`: 算出された結果（SST, Data-Free SST, TIES, DARE, Task Arithmetic などの手法）を表に挿入し、具体的な数値を埋め込む。

## Verification Plan
- 作成したスクリプトが正しく実行され、全手法に対してAUC・s_min・s_maxの値が取得できることを確認する。
- `flmsec.tex` の該当箇所の表がコンパイル可能な正しいLaTeXフォーマットで更新されていることを確認する。
