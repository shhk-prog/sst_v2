# 調査計画: inst_medalpaca の評価検証

## 1. 調査目的
`inst_medalpaca` (MedAlpaca-Flashcards) が本評価フレームワークにおいて Perplexity および Similarity Score 経由で正しく医療指示追従能力を定量化・集計できているかを検証する。

## 2. 調査対象
- **評価スクリプト**: `v3/scripts/eval_instruction_datasets.py`
- **設定ファイル**: `v3/configs/config_main.yaml`
- **結果 JSON データ**: `v3/results/debug_limit320/base/*_inst_medalpaca.json`
- **集計スクリプト**: `v3/scripts/pareto_auc.py`, `v3/scripts/generate_tables.py`

## 3. 主な検証項目
1. **Perplexity (PPL↓) と Similarity (Sim Score↑) の判定方式**:
   - 医療フラッシュカード QA に対する交差エントロピー損失 PPL と SequenceMatcher 文字一致度の動作確認
2. **集計スクリプトでの優先キー読み込み**:
   - `pareto_auc.py` で `similarity_score` と `-perplexity` が採用されているかの確認
3. **ベースモデルの定量比較**:
   - 医療特化モデル MedAlpaca (PPL 1.15, Sim 55.50%) と他モデル (PPL 2.56〜3.02, Sim 12%〜14%) のドメイン知識精度差の妥当性評価
