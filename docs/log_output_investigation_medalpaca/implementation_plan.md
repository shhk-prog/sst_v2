# 調査・検証計画 (Implementation Plan): medalpacaログ出力検証

## 概要
`v3_merged_eval_parallel_limit320` 内の評価ログにおける `inst_medalpaca` のログ出力が他と異なる原因を解明し、評価が正しく完了しているかを検証する。

## 調査方針

1. **ログの比較調査**
   - 対象ログ: `v3_merged_eval_parallel_limit320/sst_merge_v3_main_data_free_sst_main_safety+math_alpha0.0_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42_seed42.log`
   - 比較ログ: `v3_merged_eval_parallel_320_seed43/sst_merge_v3_main_data_free_sst_main_safety+code_alpha0.0_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed43_seed43.log`
   - スクリプト: `scripts/eval/eval_instruction_datasets.py`

2. **出力ファイル検証**
   - 生成結果ファイル: `results/debug_limit320/merged/seed42/safety+math/data_free_sst_main/sst_merge_v3_main_data_free_sst_main_safety+math_alpha0.0_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42_inst_medalpaca.json`
   - 検証項目: サンプル数 (320件)、Perplexity, Similarity, 各サンプルの response の格納状態

3. **原因特定とレポート作成**
   - ログ出力差分の理由（`--batch_size` 引数と標準エラー出力 `[transformers]` 警告の上書き現象）を明示。
