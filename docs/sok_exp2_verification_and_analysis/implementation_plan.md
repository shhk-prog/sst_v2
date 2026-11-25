# 実装計画: SoK 実証 2 完了監査および最終解析

## 監査項目
1. 全 3 seed（`task 0, 1, 2`）および対照 2 本の正常終了確認（`local_launcher.log`, `local_task*.log`, 例外・フォールバック・`.tmp` 残骸の有無）。
2. 全 80 安全性 JSON・全 20 有用性 JSON の欠損フィールド（`response`, `asr`, `classifier_output`, `harmbench_cls_output`, `samples` 件数）チェック。
3. 時系列・GPU 切替（`04:34` の GPU `0,1,2` → `1,2,3` 切替）前後での出力長・文字化け率・seed 間一貫性の監査（四分位比較および α=0.0 再現性）。
4. `v5/scripts/analyze_sok_exp2.py` を本番結果に対して実行し、`v5/outputs/sok_exp2/exp2_analysis_summary.{md,json}`・`exp2_safety_utility_curve.png`・`exp2_injection_ratio_curve.png` を生成。
