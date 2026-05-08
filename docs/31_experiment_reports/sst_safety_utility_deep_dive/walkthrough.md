# ウォークスルー: SST-Merge 実験結果とフローの再構築

本タスクでは、ユーザーより提示された最新の実験結果と論理構成に基づき、詳細なレポートを作成しました。

## 作成されたドキュメント

1.  **[detailed_experiment_analysis.md](file:///Users/saki/lab/SST-main/docs/31_experiment_reports/sst_safety_utility_deep_dive/detailed_experiment_analysis.md)**
    - 実験A: データ混合（20-80%）とLR変更による感度分析のまとめ。
    - 実験B, C: FIM（$g_i^2$）と勾配（$|g_i|$）のランキング一致に関する理論的・実験的裏付け。
    - 批判的な問い（なぜマージか？なぜFTではないのか？）に対する回答の集約。
2.  **[experiment_flow_narrative.md](file:///Users/saki/lab/SST-main/docs/31_experiment_reports/sst_safety_utility_deep_dive/experiment_flow_narrative.md)**
    - 現状の実験フロー（Base $\rightarrow$ FT $\rightarrow$ Merge）の定義。
    - 「Safety Tax（安全性の代償）」を最小化するストーリーとしての構成案。

## 修正内容の要点

### 実験B, Cの理論的解釈
FIMの対角近似が $g_i^2$ であることから、勾配絶対値 $|g_i|$ とのランキング一致は数学的に必然であることを明文化しました。これにより、実験結果で両手法が似た挙動を示す理由を明確に説明できるようになりました。

### マージの優位性の強調
データが豊富にある場合のFTよりも、データが限られている状況（Low-resource）や、データ共有が困難な分散開発環境において、Fisher比に基づくマージが真価を発揮するという論理を構築しました。

## 今後のステップ
- 作成したレポートを論文や技術報告書の草案として活用。
- 追加の比較実験（Jaccard係数によるインデックス一致率の定量化など）の実施検討。
