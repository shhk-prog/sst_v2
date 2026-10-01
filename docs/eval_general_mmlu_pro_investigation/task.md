# タスク: general_mmlu_pro の評価判定修正

## 概要
`general_mmlu_pro` (MMLU-Pro) の評価において、`lm_eval` の厳密すぎる正規表現抽出フィルタ (`custom-extract`) によって正しい回答（例: `"The answer is: H."`）が `[invalid]` として破棄されスコアが全滅していた問題を修正する。

## 修正目標
1. `eval_utility.py` に柔軟な回答抽出および再判定を行う `fix_mmlu_pro_responses` 関数を追加。
2. `pareto_auc.py` の `extract_utility_score` 内の `preferred_keys` に `"exact_match,custom-extract"` を追加。
3. 既存の `*utility_general_mmlu_pro.json` に対する一括修復スクリプト `fix_mmlu_pro_jsons.py` の作成。
