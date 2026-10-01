# 調査計画: math_gsm8k の評価検証

## 1. 調査目的
`math_gsm8k` (GSM8K) が本フレームワークにおいて正しくモデルの数学解法能力を測定・集計できているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_utility.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_utility_math_gsm8k.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **抽出フィルタの挙動比較 (`strict-match` vs `flexible-extract`)**:
   - `strict-match` (`####` 形式要求) と `flexible-extract` (数値一般抽出) の差分確認
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `exact_match,flexible-extract` が正しくプライマリ指標として採用されているかの確認
3. **ベースモデルの定量比較**:
   - WizardMath と他モデル (WizardCoder, SafetyFT, MedAlpaca) の解法精度差の妥当性評価
