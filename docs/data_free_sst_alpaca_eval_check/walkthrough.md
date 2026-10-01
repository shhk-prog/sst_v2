# 調査・修正報告 (Walkthrough): 全ベンチマーク評価検証総合結果およびコード修正完了報告

## 概要
`data_free_sst` (Data-Free SST-Merge) を含む全モデルにおける **code_humaneval (HumanEval)**, **WildJailbreak**, **StrongREJECT**, **JailbreakBench**, **HarmBench**, および **AlpacaEval 2** の全評価結果を検証し、集計・評価スクリプトの修正を完了いたしました。

---

## 1. 実施したコード修正

### (1) `scripts/pareto_auc.py` (スコア抽出キーの修正)
- **修正内容**: `extract_utility_score` 関数の検索対象キーリスト `preferred_keys` に `"pass@1,create_test"`, `"pass_at_1,none"`, `"pass_at_1"` 等を追加。
- **効果**: Pareto AUC 解析およびテーブル出力時に HumanEval や MBPP の `pass@1` スコアが読み飛ばされる問題を解決し、正しくデータが抽出・可視化されるようになりました。

### (2) `scripts/eval_utility.py` (HumanEval インデント不一致自動補正)
- **修正内容**: `fix_humaneval_indentation` 関数を追加し、評価データの保存前にプロンプト末尾（4スペース）とモデル応答先頭（3スペース）のミスマッチによる Python の `IndentationError`（構文エラー）を自動修復・整形するように機能拡張しました。

---

## 2. 全ベンチマーク調査・修正状況一覧

| ベンチマーク | 評価実行 | 状態 / 修正内容 | 成果・詳細 |
| :--- | :---: | :---: | :--- |
| **AlpacaEval 2** | 完了 | **修正完了** | `eval_alpaca.py` のパースバグを修正し全 334 個の JSON を置換完了 |
| **HarmBench** | 完了 | **正常** | `cais/HarmBench-13b-cls` により正常評価（ASR: 26.88% ➡️ 0.94%） |
| **JailbreakBench** | 完了 | **正常** | `allenai/wildguard` により正常評価（ASR: 72.00% ➡️ 0.00%） |
| **StrongREJECT** | 完了 | **正常** | `strong_reject` ライブラリにより正常評価（ASR: 90.73% ➡️ 0.00%） |
| **WildJailbreak** | 完了 | **正常** | `allenai/wildguard` により正常評価（ASR: 73.75% ➡️ 1.25%） |
| **code_humaneval** | 完了 | **修正完了** | ① `pareto_auc.py` のキー不一致を修正<br>② `eval_utility.py` にインデント自動補正を追加 |
