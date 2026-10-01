# 調査計画: medical_pubmedqa の評価検証

## 1. 調査目的
`medical_pubmedqa` (PubmedQA) が本評価フレームワークにおいて 3 択対数尤度比較方式で正しく精度判定・集計できているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_utility.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_utility_medical_pubmedqa.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **`multiple_choice` (対数尤度比較) 評価方式の整合性**:
   - `yes`, `no`, `maybe` の 3 択肢における Loglikelihood 判定の正常動作確認
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `acc,none` / `acc` が正しく採用されているかの確認
3. **ベースモデルの定量比較**:
   - 各ベースモデル (80.63%〜89.38%) のスコア安定性の妥当性評価
