# タスク: data_free_sst 全ベンチマーク評価状況調査・修正 (AlpacaEval2, Safety4種, HumanEval)

## 概要
`data_free_sst` (Data-Free SST-Merge) 手法における `safety+math` および `safety+code` タスクペアの全ベンチマーク評価整合性を完全検証・修正。
`alpaca_eval2` のバグ修正、全 Safety ベンチマーク4種の正確性確認、および `code_humaneval` (HumanEval) の集計キー不一致バグの修正とインデント補正処理を追加した。

## タスクリスト
- [x] AlpacaEval2 の結果評価JSONおよび集計CSVの検証・バグ修正
- [x] HarmBench, JailbreakBench, StrongREJECT, WildJailbreak の評価正確性検証
- [x] `code_humaneval` (HumanEval) の評価結果および集計キーミスマッチ原因の特定
- [x] `pareto_auc.py` に HumanEval/MBPP の抽出キー (`pass@1,create_test`, `pass_at_1,none`) を追加修正
- [x] `eval_utility.py` に HumanEval 生成コードのインデント構文エラー自動修復処理 (`fix_humaneval_indentation`) を追加実装
- [x] 調査報告・検証ドキュメントの作成と更新
