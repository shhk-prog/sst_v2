# タスク: 全評価タスクの再実行要否まとめと推奨アクション

## 概要
これまで調査を行った全 10 種類の評価タスク（general_ifeval, general_mmlu_pro, general_mmlu, math_gsm8k, math_minerva_math500, medical_medqa_4options, medical_pubmedqa, inst_evol_code, inst_medalpaca, alpaca_eval2）について、評価コードの修正状況・データ整合性・再実行の必要性を一覧化し、今後の最適な実行計画を提示する。

## 目標
1. 各評価タスクの健全性と再実行要否の分類。
2. 再実行が必要なタスク (`general_ifeval`, `general_mmlu_pro`) の具体的な再評価手順の提示。
3. 再実行が不要なタスクの根拠提示。
