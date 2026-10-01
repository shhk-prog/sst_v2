# 実装計画: AAAI評価論文の結果・考察セクションの改訂

## 1. 目的 (Goal Description)
`/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md` の第6章 (Results and Analysis) および 第7章 (Conclusion & Future Work) を、`v3` フォルダ内にある最新の実験結果（特に `paper_evaluation_summary_tables.md` および `pareto_auc_task_summary.md`）に基づき、数値を正確に反映した形に書き換えます。

旧版の記述（「DELLA崩壊行の実験条件混同」「Diagonal SST-Merge数値の不整合」など）を修正し、推論崩壊（Gibberish）を排除した正常応答（Valid Only）に基づく厳密なPareto AUC評価を主軸として、評価論文として高い完成度を持つよう文章を再構成します。

## 2. ユーザー確認事項 (User Review Required)
> [!IMPORTANT]
> - 本計画では、ファイルの250行目以降（`6. Results and Analysis` から最後まで）を中心に大幅な加筆・修正を行います。元の構成要素（表の形式など）は維持しつつ、最新データを埋め込みます。
> - `v3` の結果 (`alpha=0.6` 時点の比較表や、`safety_math` での AUC値 等) を全面的に信用して論文に反映します。特定の数値を見せたい意図等があれば事前にお知らせください。

## 3. オープンクエスチョン (Open Questions)
> [!NOTE]
> - 現在の `v3/results/summary_tables/paper_evaluation_summary_tables.md` には `led_merging` の medical ドメイン結果が含まれていません（公式サポート対象外と本文に記載済み）。表の該当箇所は `-` や `N/A` として扱いますがよろしいでしょうか。
> - 第6.5節「計算効率と頑健性」内の実行時間（Table Y）は、本タスクで取得した新しいデータが見当たらないため、現状の原稿の数値をそのまま残す形でよろしいでしょうか？（Data-Free SST-Merge: 107.05秒 などの値）

## 4. 提案する変更内容 (Proposed Changes)

### 論文ドキュメントの更新
以下のファイルを修正します。

#### [MODIFY] [secure-merge_統一比較評価論文_改訂版.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md)
*   **6.1節**: Table 2 (ベースモデルと主要手法の比較) を最新の `paper_evaluation_summary_tables.md` (Alpha=0.6) の値に更新。Table 3 (GSM8K詳細) の数値も見直し。
*   **6.2節 & 6.3節**: 偽の安全性とGibberish排除の議論を強化。`pareto_auc_task_summary.md` に示された厳密なAUC値（Diagonal SST: 0.2935, Data-Free SST: 0.2914, TIES: 0.2929 等）を正確に反映し、各手法の順位付けや考察を修正。
*   **6.4節 & 6.5節**: 介入粒度とデータフリー性、計算コストに関する記述を、更新された結果と矛盾しないように論理展開を微調整。
*   **7節**: v3 の最終結果を踏まえた、統一比較評価の総括として Conclusion を洗練。

## 5. 検証計画 (Verification Plan)
### 手動検証 (Manual Verification)
1. 修正後の `.md` ファイルをMarkdownプレビュー等で表示し、表の崩れがないか確認する。
2. 論文内に記載された数値が `paper_evaluation_summary_tables.md` と正確に一致しているか、整合性をクロスチェックする。
3. ユーザーに修正後のテキストを一読いただき、論文としての論理展開に問題がないか確認を依頼する。
