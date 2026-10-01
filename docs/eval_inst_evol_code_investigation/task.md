# タスク: inst_evol_code の評価妥当性調査

## 概要
Instruction/Evol-Instruct-Code ドメインの指示追従評価タスク `inst_evol_code` (nickrosh/Evol-Instruct-Code-80k-v1) について、評価スクリプト `eval_instruction_datasets.py` の動作、Perplexity (PPL) および Similarity Score の算出ロジック、結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `eval_instruction_datasets.py` による Perplexity (PPL↓) および Similarity Score (Sim Score↑) の計算方式の整合性確認。
2. 各ベースモデル (WizardCoder, WizardMath, MedAlpaca, SafetyFT) の評価結果 JSON データの比較解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) におけるスコア取り込みの確認。
4. 正しく評価されているかの最終判断の提示。
