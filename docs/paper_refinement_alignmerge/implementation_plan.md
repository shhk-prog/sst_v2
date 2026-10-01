# Implementation Plan: AlignMerge論文を参考にした Secure Merge 統一比較評価論文 (1, 2節) の改訂

AlignMerge (arXiv:2512.16245) の 1, 2 節の先進的な論理展開（モデルマージにおける事後アライメントドリフトのメカニズム、既存の安全性対応マージ手法の限界、パラメータ幾何学とグローバル不変量としての安全性の定義）を参考にして、`/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md` の 1 節 (Introduction) および 2 節 (研究課題 / 背景) をブラッシュアップします。また、すべての参照箇所に適切な引用文献を明記します。

---

## ユーザー確認事項 (User Review Required)

> [!IMPORTANT]
> **改訂の基本方針**
> 1. **論理構造の刷新 (Introduction)**:
>    - **モデルマージの隆盛とアライメントドリフトの危機**: 専門化モデルの事後的統合 (Model Soups, Task Arithmetic, DF-Merge 等) が盛んになる一方で、アライメントが副次的に扱われ、「1つの悪影響モデルが全体を損なう (one bad model spoils the bunch)」ことや高分散方向へのマージ軌道による安全性崩壊が明示されていない問題を提示する。
>    - **安全性対応マージの進展と限界**: SafeMerge, MergeAlign, LED-Merging, SALSA 等の進展を認めつつも、これらが層単位・ニューロン単位の局所的・ヒューリスティックな対策に止まり、**パラメータ空間上のグローバルな安全性不変領域を定式化できていない限界**を示す。
>    - **幾何学的観点：アライメントはスカラーではなく幾何学的不変量である**: 重み空間の線形性はアライメント中立でないこと、干渉解消 (TIES, DARE, DELLA) は必要条件だが十分条件でないこと、グローバル不変量の欠如を要約し、「アライメントは幾何学的不変量として扱うべきである」という中心的視点を導入する。
>    - **本論文 (Secure Merge 統一比較評価) の位置づけ**: 上記の限界を踏まえ、介入粒度（ベクトル、層、ニューロン、パラメータ、部分空間・幾何）や利用情報（差分、符号・振幅、勾配、Fisher情報）の観点から既存・最新マージ手法を統一的に比較評価する意義をクリアに打ち出す。
>
> 2. **引用文献の完全整備**:
>    - AlignMerge (Wang et al., 2025; arXiv:2512.16245), Ortiz-Jiménez et al. (2023), Chegini et al. (2024; SALSA), Crisostomi et al. (2024; C2M3), Yang et al. (2024; Merging Survey), Akiba et al. (2025; Evolutionary Merging) などを網羅的に参考文献リストに追加し、本文と正確に対応付ける。

---

## 変更内容 (Proposed Changes)

### 1. ドキュメントの改訂: [secure-merge_統一比較評価論文_改訂版.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_%E7%B5%B1%E4%B8%80%E6%AF%94%E8%BC%83%E8%A9%95%E4%BE%A1%E8%AB%96%E6%96%87_%E6%94%B9%E8%A8%82%E7%89%88.md)

#### [MODIFY] `secure-merge_統一比較評価論文_改訂版.md`
- **Section 1: Introduction**
  - **1.1 事後的なモデル融合におけるアライメントのドリフト (Alignment Drift under Post-hoc Model Fusion)**:
    - Model Soups [3], Fisher-weighted averaging [10], Task Arithmetic [4], Tangent Task Arithmetic (Ortiz-Jiménez et al., 2023), DF-Merge [14] の発展と、アライメント無視の問題。
    - Hammoud et al. [1] の「One bad model spoils the bunch」現象（1つの非安全モデルが混ざるだけで全体のアライメントを破壊する）と、Yang et al. (2024) のパラメータ空間における高分散方向選択のメカニズムを解説。
  - **1.2 安全性を考慮したマージ：進展と限界 (Safety-Aware Merging: Progress and Limits)**:
    - SafeMerge [8] (層ごとのコサインリバート), MergeAlign [2] (合成安全データ混合), SALSA (Chegini et al., 2024; SFT平均), LED-Merging [9] (ニューロン分離) などの進展。
    - 局所性・ヒューリスティック性、合成データ依存性、グローバルな安全性不変領域 (global invariant region) の不在という限界の提示。
  - **1.3 なぜ幾何学か：アライメントはスカラーではなく不変量である (Why Geometry: Alignment as an Invariant, Not a Scalar)**:
    - C2M3 (Crisostomi et al., 2024) 等の幾何学的マージの観点を取り入れつつ、以下の3原則を整理：
      1. 重み空間の線形性はアライメントに対して中立ではない [1, Yang et al. 2024]
      2. 干渉の解消は必要条件だが十分条件ではない (TIES [5], DARE [6], DELLA [7], DF-Merge [14])
      3. 現在の安全性対応マージ手法はグローバルな不変量を欠いている [2, 8, 9]
    - **中心的主張**: アライメントを単なるスカラー評価値ではなくパラメータ多様体上の幾何学的不変量として扱う必要性。
  - **1.4 本研究の目的と貢献**:
    - 上述の背景を踏まえ、Secure Merge 設定において各種マージ手法（標準マージ、安全性維持マージ、Fisher重要度マージ、Fisher比率マージ SST-Merge/Data-Free SST-Merge、AlignMerge等）を介入粒度・利用情報の視点から統一比較評価する枠組みと3つの貢献を定式化。

- **Section 2: 研究課題 (Research Questions)**
  - RQ1〜RQ5 を最新の幾何学的観点・グローバル不変量 vs 局所ヒューリスティックの観点を含めて磨き上げる。

- **参考文献 (References)**
  - 新規参照文献（Ortiz-Jiménez et al., 2023; Chegini et al., 2024 [SALSA]; Crisostomi et al., 2024 [C2M3]; Yang et al., 2024 [Survey]; Akiba et al., 2025 [Evolutionary Merging] 等）を追加・整理する。

---

### 2. トピック用保存フォルダの整備
`/mnt/nas/home/hiromi/src/sst_v2/docs/paper_refinement_alignmerge/` 配下に以下のファイルを保存・維持します。
- `task.md`
- `implementation_plan.md`
- `section1_2_revised.md` (改訂した 1, 2 節の抜粋・作業履歴)
- `walkthrough.md`

---

## 検証計画 (Verification Plan)

### 手動・概念検証
- **論理的一貫性の確認**: Introductionの展開が、単なる論文の列挙ではなく、「事後融合でのドリフト現象 → 既存安全マージの局所的限界 → 幾何学的観点・不変量の必要性 → 統一比較評価の必要性と本論文の位置づけ」という一貫したストーリーラインになっているか。
- **引用文献の正確性**: 本文中の `[1]`, `[2]` などの番号および著者・年が、文末の参考文献リストと完全に一致しているか。
- **日本語記述の品質**: 学術論文として適切で洗練された日本語表現になっているか。
