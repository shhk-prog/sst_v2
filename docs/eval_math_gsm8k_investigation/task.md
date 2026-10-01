# タスク: math_gsm8k の評価妥当性調査

## 概要
Math ドメインの主要数学ベンチマークタスク `math_gsm8k` (openai/gsm8k) について、評価スクリプト、生成プロンプト、数値抽出フィルタ (`flexible-extract` / `strict-match`)、および実際の評価結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `gsm8k` の評価タスク構造と数値抽出フィルタ (`flexible-extract`) の動作確認。
2. 実際に生成された評価結果 JSON データ (WizardMath, WizardCoder, MedAlpaca, SafetyFT) の数値解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) におけるメトリクス取得処理の検証。
4. 正しく評価されているかの最終判断の提示。
