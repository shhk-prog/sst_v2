# SST-Merge 実験結果詳細報告およびフロー構成計画

本計画は、ユーザーより提示された「実験A（データ混合とLR変更）」および「実験B, C（FIMと勾配の比較）」の詳細なまとめと、今後の実験ストーリー（実験フロー）の構築を目的としています。

## ユーザーレビュー必須

> [!IMPORTANT]
> 以下の項目について、現在の理解が正しいかご確認をお願いいたします。
> - **実験A**: 普通のプロンプトと有害データの混合比率（20-80%）および学習率（LR）の変動が、SafetyとUtilityのトレードオフに与える影響の評価。
> - **実験B, C**: Fisher情報行列（FIM）の対角近似 ($g_i^2$) と勾配の絶対値 ($|g_i|$) のランキングが一致することの数学的・実験的検証。
> - **実験フロー**: BaseモデルからFTを経てマージに至る一連の流れを、どのように論理的にストーリー立てるか。

## オープンな質問

> [!WARNING]
> - 実験Aに関して、具体的な「普通のプロンプト」のデータセット名（例：Alpaca, ShareGPT等）の指定はありますか？
> - 実験B, Cで比較する「インデックスの一致率」を定量化する指標として、Jaccard係数やSpearman順位相関を用いることでよろしいでしょうか？

## 提案するドキュメント構成

### 1. 実験結果詳細レポート (①, ②に対応)
`docs/31_experiment_reports/sst_safety_utility_deep_dive/detailed_experiment_analysis.md`
- **実験A: データ混合と学習率の感度分析**
  - 混合比率 (20:80 〜 80:20) による性能変化。
  - LRの変更がSafety/Utilityに与える影響のヒートマップ的整理。
- **実験B, C: FIM vs Gradient Absolute の理論的・実験的整合性**
  - FIMの対角成分 $g_i^2$ と勾配 $|g_i|$ の大小関係の一致についての論証。
  - 実験によるインデックス一致率の提示。
  - 「なぜMagnitudeより優れているか」および「なぜFTではなくマージか」に対する回答（データが少ない状況での強み）。

### 2. 実験フロー・ストーリーレポート (③に対応)
`docs/31_experiment_reports/sst_safety_utility_deep_dive/experiment_flow_narrative.md`
- **現状の実験フローの再定義**
  - Base Model $\rightarrow$ FT (Target Models) $\rightarrow$ Merge (with Utility/Safety Data)
- **ストーリー構築**
  - 「分散開発されたモデルの統合」というシナリオ。
  - データ制約下（Low-resource）におけるSSTの優位性の強調。
  - 安全性の注入と有用性の保護をGEVPとして定式化する意義。

## 実行タスク

### [NEW] [detailed_experiment_analysis.md](file:///Users/saki/lab/SST-main/docs/31_experiment_reports/sst_safety_utility_deep_dive/detailed_experiment_analysis.md)
### [NEW] [experiment_flow_narrative.md](file:///Users/saki/lab/SST-main/docs/31_experiment_reports/sst_safety_utility_deep_dive/experiment_flow_narrative.md)

## 検証計画

### 内容の整合性確認
- 既存の `analysis_summary.md` や `experiment_summary.md` との数値的・論理的整合性を確認します。
- ユーザーから提示された「一階微分と二階微分の差が出にくい」という仮説を数学的に補足します。

### マニュアル確認
- 作成したレポートのストーリー構成が、論文や技術報告書として説得力があるかユーザーにレビューを依頼します。
