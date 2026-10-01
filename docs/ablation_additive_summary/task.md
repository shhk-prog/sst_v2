# Task: Ablationのadditive (addactive) 結果の集計

- [x] `v3/results/debug_limit320/merged` 配下の結果 JSON から ablation 実験（特に `additive` 変分）のデータを抽出・集計するスクリプト `v3/scripts/analysis/generate_ablation_additive_tables.py` を作成
- [x] `additive` と `interpolation` の比較、および `additive` の alpha / seed 平均（42, 43, 44）スコア表をマークダウン (`.md`) および CSV (`.csv`) 形式で出力
- [x] 集計結果を `v3/results/summary_tables/ablation_additive_summary_tables.md` に出力し、確認
- [x] 作業概要および修正内容のまとめを `docs/ablation_additive_summary/walkthrough.md` に更新
