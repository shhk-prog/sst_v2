# タスク: math_minerva_math500 の評価妥当性調査

## 概要
Math ドメインの難関数学競技問題ベンチマーク `math_minerva_math500` (HuggingFaceH4/MATH-500) について、評価パイプライン、数式検証モジュール (`math-verify`), および実際の評価結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `minerva_math500` の評価タスク構造および `math_verify` モジュール（`antlr4-python3-runtime`, `sympy`, `math-verify`）による同値性判定動作の確認。
2. 各モデル（WizardMath, WizardCoder, MedAlpaca, SafetyFT）の評価結果 JSON データの比較解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) における `math_verify,none` の読み込み検証。
4. 正しく評価されているかの最終判断の提示。
