# タスク: ベンチマーク評価の正当性検証

## 目的
以下の16個のベンチマークについて、`sst_v2` (特に `v3`) における評価パイプライン、データセット設定、評価ロジック、評価結果ログを調査し、正しく評価されているか（または問題・改善点があるか）を総合的に調査・検証する。

### 対象ベンチマークリスト
1. `harmbench` (Safety)
2. `jailbreakbench` (Safety)
3. `strongreject` (Safety)
4. `wildjailbreak` (Safety)
5. `code_humaneval` (Utility - Code)
6. `code_mbpp` (Utility - Code)
7. `general_ifeval` (Utility - General)
8. `general_mmlu_pro` (Utility - General)
9. `general_mmlu` (Utility - General)
10. `math_gsm8k` (Utility - Math)
11. `math_minerva_math500` (Utility - Math)
12. `medical_medqa_4options` (Utility - Medical)
13. `medical_pubmedqa` (Utility - Medical)
14. `inst_evol_code` (Instruction FT domain)
15. `inst_medalpaca` (Instruction FT domain)
16. `alpaca_eval2` (Instruction/General)

## 進行状況
- [x] 1. 調査計画の作成と承認
- [x] 2. 各ベンチマークの定義・実装スクリプト・データセットの確認
- [x] 3. 過去の調査レポート (`docs/*_investigation`, `docs/code_mbpp_evaluation_audit` 等) の確認
- [x] 4. ログファイルおよび最新評価結果 json の詳細確認
- [x] 5. 16個のベンチマークそれぞれの評価正当性判定（正常/問題あり/注意点）の集計
- [x] 6. 総合評価レポートの作成と `walkthrough.md` の更新
