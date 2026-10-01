# 調査計画: medical_medqa_4options の評価検証

## 1. 調査目的
`medical_medqa_4options` (MedQA) が本評価フレームワークにおいて対数尤度比較方式で正しく医療知識精度を判定・集計できているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_utility.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_utility_medical_medqa_4options.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **`multiple_choice` (対数尤度比較) 評価方式の整合性**:
   - 4 択肢 (A, B, C, D) の Loglikelihood 比較判定の正常動作確認
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `acc_norm,none` / `acc,none` が正しく採用されているかの確認
3. **ベースモデルの定量比較**:
   - 医療特化モデル MedAlpaca (43.44%) と他モデル (22.50%〜31.88%) のドメイン専門性精度の妥当性評価
