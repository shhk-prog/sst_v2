# 調査計画: general_mmlu の評価検証

## 1. 調査目的
`general_mmlu` (MMLU) が本リポジトリの評価フレームワークにおいて正常かつ正確にスコア算出されているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_utility.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_utility_general_mmlu.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **評価ロジックと出力タイプ**:
   - `output_type: loglikelihood` (対数尤度比較) による評価の整合性確認
2. **集計スクリプトでのキー取得**:
   - `preferred_keys` の `"acc,none"` による全体平均およびサブタスクスコアの読み込み
3. **ベースモデルのスコア妥当性**:
   - MedAlpaca, WizardMath, SafetyFT, WizardCoder のスコア比較と分布の検証
