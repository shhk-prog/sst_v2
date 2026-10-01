# Walkthrough: 論文の必須修正（AUC定義統一、Seed統計、主表再構成、比較条件）

論文ファイル [`07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md) に対し、査読対策として重要な4つの必須修正を適用完了しました。

---

## 修正内容のまとめ

### 1. Pareto AUCの定義と値の名称分離・統一
- **Raw Pareto AUC**（0.945 / 0.912）: 崩壊・無意味応答も含めた全体の曲面積として名称・定義を明確化（6.1節）。
- **Validity-aware Pareto AUC**（0.2935 / 0.2914）: Gibberish等の崩壊応答を除外し、正常応答サンプルのみで各軸を正規化して再計算した本質的な曲面積として名称・定義を明確化（6.3節）。

### 2. 「3 Seeds Average」の実データ（平均 ± 標準偏差）への更新
- 実データの集計プログラム `extract_metrics.py` により、3つのシード（seed=42, 43, 44）における平均および標準偏差（$\text{mean} \pm \text{std}$）を正確に算出しました。

### 3. 主表 (Table 2) への Valid Safety Rate および Valid Response Rate の追加
- 既存の5大ドメイン平均性能表を廃止し、ご指定の列構成（`Method` | `Harmful ASR ↓` | `XSTest過剰拒否 ↓` | `Valid response rate ↑` | `Valid Safety Rate ↑` | `GSM8K ↑` | `HumanEval ↑`）に全面刷新しました。
- 各手法の「見かけ上のASR低下（ASR 0%）」と「完全な出力崩壊（Valid Response Rate 0%）」を判別できるように改善されました（例：MergeAlignがValid response rate 0%で完全に崩壊していることが同一表内で明示化）。

### 4. 対象手法間の比較条件の明示（パレート優先）
- 5.4節の `Evaluation Protocol & Baselines` に、ハイパーパラメータ（$\alpha$）を網羅的に掃引し Pareto Frontier 上で最適・典型的な設定（$\alpha=0.6$ 等）で比較した点、および調整を伴わない手法は原著推奨・既定設定（$\alpha = \text{N/A}$）で評価した旨（**パレート優先**）を明記しました。

---

## 変更箇所のプレビュー

- **5.4節 (Evaluation Protocol)**: 比較条件（パレート優先）および 3 Seeds Average 算定プロトコルを追加
- **Table 2**: 3 Seeds Average ($\text{mean} \pm \text{std}$) による実データ詳細評価表
- **6.1節 / 6.3節**: `Raw Pareto AUC` と `Validity-aware Pareto AUC` の二分および定義補足
