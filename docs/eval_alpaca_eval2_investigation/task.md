# タスク: alpaca_eval2 の評価妥当性調査

## 概要
Instruction/General ドメインの標準指示追従ベンチマーク `alpaca_eval2` (AlpacaEval 2.0) について、評価スクリプト `eval_alpaca.py` の動作、アノテータ出力 `leaderboard.csv` からのスコア抽出処理 (`win_rate` vs `length_controlled_winrate`)、および実際の評価結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `eval_alpaca.py` および `fix_all_alpaca_eval_jsons.py` による AlpacaEval 2.0 結果抽出動作の確認。
2. 標準勝率 `win_rate` (0.00% になりやすい現象) と公式本質指標である文字長補正勝率 `length_controlled_winrate` の相違検証。
3. `pareto_auc.py` および `generate_tables.py` における LC Win Rate 優先読み込みへの改善。
4. 各ベースモデル (MedAlpaca, WizardCoder, WizardMath, SafetyFT) の評価結果比較と妥当性提示。
