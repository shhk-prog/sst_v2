# タスク: inst_medalpaca の評価妥当性調査

## 概要
Instruction/MedAlpaca-Flashcards ドメインの医療指示追従評価タスク `inst_medalpaca` (medalpaca/medical_meadow_medical_flashcards) について、評価スクリプト `eval_instruction_datasets.py` の動作、Perplexity (PPL) および Similarity Score の算出ロジック、結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `eval_instruction_datasets.py` による Perplexity (PPL↓) および Similarity Score (Sim Score↑) の計算ロジックの整合性確認。
2. 各ベースモデル (MedAlpaca, SafetyFT, WizardMath, WizardCoder) の評価結果 JSON データの比較解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) におけるスコア取り込みの確認。
4. 正しく評価されているかの最終判断の提示。
