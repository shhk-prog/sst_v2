# Ablation Additive (Addactive) 集計作業報告 (Walkthrough)

アブレーション実験における `additive` 変分（および標準の `interpolation` 変分との比較）に関する結果データの自動抽出・集計を実施しました。

## 変更・作成したコンポーネント

1. **集計スクリプト**: [generate_ablation_additive_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_ablation_additive_tables.py)
   - アブレーション実験の評価結果 JSON から `variant=additive` / `interpolation` や各種ハイパーパラメータ、シード平均スコアを全自動で集計するPythonスクリプト。

2. **集計結果ドキュメント**: [ablation_additive_summary_tables.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/ablation_additive_summary_tables.md)
   - 抽出・集計された比較マークダウンテーブル。

3. **集計結果 CSV**: [ablation_additive_summary_tables.csv](file:///mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/ablation_additive_summary_tables.csv)
   - 分析やグラフ作成用のCSVデータ。

## 検証内容
- スクリプトによる全結果ファイル走査の適用および出力ファイル生成の正常性を確認しました。
