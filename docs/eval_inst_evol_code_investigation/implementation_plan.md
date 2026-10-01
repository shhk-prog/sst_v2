# 調査計画: inst_evol_code の評価検証

## 1. 調査目的
`inst_evol_code` (Evol-Instruct-Code) が本評価フレームワークにおいて Perplexity および Similarity Score 経由で正しくコード指示追従能力を定量化・集計できているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_instruction_datasets.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_inst_evol_code.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **Perplexity (PPL↓) と Similarity (Sim Score↑) の判定方式**:
   - `compute_loss_one` (交差エントロピー損失による PPL) と `SequenceMatcher` による文字類似度の正常動作確認
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `similarity_score` と `-perplexity` が採用されているかの確認
3. **ベースモデルの定量比較**:
   - コード特化モデル WizardCoder (PPL 1.41, Sim 15.10%) と他モデル (PPL 1.89〜2.15, Sim 7%〜9%) のコード理解精度差の妥当性評価
