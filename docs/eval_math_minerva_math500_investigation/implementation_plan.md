# 調査計画: math_minerva_math500 の評価検証

## 1. 調査目的
`math_minerva_math500` (MATH-500) が本評価フレームワークにおいて数式評価モジュール経由で正しく精度判定・集計されているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_utility.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_utility_math_minerva_math500.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **数式検証ライブラリ `math_verify` の自動インストールと動作確認**:
   - `math_verify` (math-verify / sympy) による LaTeX・数式同値性判定の検証
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `math_verify,none` が正しくプライマリ指標として採用されているかの確認
3. **ベースモデルの定量比較**:
   - WizardMath (5.31%) と他モデル (2.19%〜2.81%) の高難易度数学精度差の妥当性評価
