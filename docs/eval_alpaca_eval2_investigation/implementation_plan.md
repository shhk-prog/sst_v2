# 調査・改善計画: alpaca_eval2 の評価検証

## 1. 調査目的
`alpaca_eval2` (AlpacaEval 2.0) が本評価フレームワークにおいて `length_controlled_winrate` (LC Win Rate) 経由で正しく指示追従能力を判定・集計できているかを検証・修復する。

## 2. 調査・対象ファイル
- **評価スクリプト**: `v3/scripts/eval_alpaca.py`
- **一括補正スクリプト**: `v3/scripts/fix_all_alpaca_eval_jsons.py`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_alpaca_eval2.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証と実施した変更
1. **LC Win Rate (Length-Controlled Win Rate) 優先取得ロジックの導入**:
   - `pareto_auc.py` にて `length_controlled_winrate` が存在する場合は最優先で抽出し、パレート可視化に反映するように改修
2. **テーブル出力名の改善**:
   - `generate_tables.py` にて `Alpaca Eval 2 (LC Win Rate↑ %)` に指標表示名を改修
3. **ベースモデルの定量比較**:
   - MedAlpaca (3.34%), WizardCoder (0.61%), WizardMath (0.11%), SafetyFT (0.09%) のスコア比較と整合性確認
