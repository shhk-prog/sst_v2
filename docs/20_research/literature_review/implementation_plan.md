# 実装計画 (Implementation Plan)

## 目的 (Goal Description)
SST-Mergeの実証実験内容と、提供された10本の先行研究（`FIM論文`ディレクトリ内の論文群）を比較し、モデルマージおよびSafety-Utilityトレードオフに関するこれまでの研究の流れ、各論文の課題と解決策、SST-Mergeの新規性と差別化のポイントを体系的に整理した詳細なレポートを作成する。

## 現状の論文の問題点

現在の `論文.md` の関連研究セクション（Section 2）は以下のみ：
- Jailbreak攻撃の定義
- モデルマージの一般的説明（Task Arithmetic, TIES, DARE）
- Secure Mergeの必要性
- 外部ガードレールの限界
- Fisher情報行列とLoRAの説明

**重大な欠落**：10本の先行研究（FIMを用いたマージ手法、Safety-Utilityトレードオフ解消手法）への言及が皆無。査読者から「既存研究との差別化が不明確」と指摘されることは確実。

## 提案する再構築の骨子

### Section 2（関連研究）の大幅拡充

現在の `Section 2` を以下の4つのサブセクションで再編成する：

**2.1 FIMに基づくモデルマージの基礎（Phase 1-2の先行研究との接続）**
- NeurIPS 2022 (FWA)：FIMを重要度として加重平均 → **SST-Mergeとの差異：単一FIMに留まる**
- Arxiv 2023 (UGM)：勾配ミスマッチの問題 → **SST-Mergeとの接続：FIMを二重化**
- LREC 2024 (Mask Nodes)：FIMによるマスク生成 → **SST-Mergeとの接続：マスク概念の継承・拡張**
- OpenReview 2025 (Median)：外れ値への対応 → **SST-Mergeとの差異：Safety/Utility区別なし**
- NAACL 2025 (Dynamic)：自動重み探索 → **SST-Mergeとの差異：目的関数が単一**

**2.2 Safety-Utilityトレードオフへの挑戦（Phase 3の先行研究との接続）**
- Arxiv 2024 (Domain+Align Vectors)：ベクトル分離による制御 → **SST-Mergeとの差異：スカラー線形結合に留まる**
- ACL 2025 (LED-Merging)：衝突の回避（排他的）→ **SST-Mergeとの差異：消極的防衛、GEVP的な積極最適化なし**
- Arxiv 2025 (SafeMERGE)：層別の選択的保護 → **SST-Mergeとの差異：層単位でありパラメータ単位の精細制御がない**
- Arxiv 2025 (AlignMerge)：FIM幾何学制約 → **SST-Mergeとの最接近：FIMを使うが制約（保護）のみ、積極的なGEVP最適化なし**

**2.3 Data-Free制約への対応（Phase 4の先行研究との接続）**
- Arxiv 2026 (Data-Free Layer-Adaptive)：データフリーFIM近似 → **SST-Mergeとの差異：目的関数がGEVPと接続されていない**

**2.4 既存手法の本質的限界と本研究の動機**
- 先行研究はすべて「単一FIMによるヒューリスティックな保護」か「排他的な競合回避」に留まる
- 「SafetyとUtilityを二つの別々のFIMで計量し、GEVPとして同時最適化する」発想は存在しない
- SST-Mergeの動機：デュアルFIM + GEVP = 理論的なパレート最適の達成

### Section 3（提案手法）の理論的再構築

現在の理論記述は独立しているが、先行研究との「引継ぎ関係」を明確化した記述に修正：

1. **FWA（NeurIPS 2022）の限界からGEVPへの発展**として導入を書き直す
2. **AlignMergeとの差異**（消極的制約 → 積極的最適化）を数式レベルで明記
3. **Data-Free Layer-Adaptiveとの差異**（ヒューリスティック近似 → Surrogate Hierarchy理論）を追記
4. LED-Mergingのディスジョイント戦略との対比として補間型マージを位置づけ

## 作成するファイル

- `docs/sst_merge_literature_review/revised_paper_draft.md`：先行研究を考慮した再構築版の論文（関連研究+提案手法の主要部分のみ）
- `docs/sst_merge_literature_review/walkthrough.md`：作業内容の要約

## 作業ステップ

1. [x] 実装計画の作成
2. [ ] `revised_paper_draft.md` の Section 2（関連研究）の再構築
3. [ ] `revised_paper_draft.md` の Section 3（提案手法）の理論的再構築
4. [ ] `walkthrough.md` の更新
