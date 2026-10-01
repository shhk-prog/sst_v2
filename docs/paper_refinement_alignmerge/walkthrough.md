# Walkthrough: AlignMerge論文 (arXiv:2512.16245) を参考にした Section 1 & 2 の改訂成果

arXiv:2512.16245 (AlignMerge論文) の Section 1, 2 におけるロジック展開と最新の文献・知見を取り入れ、[/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_%E7%B5%B1%E4%B8%80%E6%AF%94%E8%BC%83%E8%A9%95%E4%BE%A1%E8%AB%96%E6%96%87_%E6%94%B9%E8%A8%82%E7%89%88.md) の Introduction (Section 1) および Research Questions (Section 2) の改訂を完了しました。

---

## 主な改訂内容と成果

### 1. Introduction (Section 1) の強化
- **1.1 事後的なモデル融合におけるアライメントのドリフト (Alignment Drift under Post-hoc Model Fusion)**:
  - Model Soups [3], Fisher-Weighted Averaging (FWA) [10], Task Arithmetic [4, 25], Dynamic Fisher-weighted Merging (DF-Merge) [14] といったモデル融合パラダイムの隆盛を説明。
  - アライメントが副次的に扱われている問題を提示し、Hammoud et al. [1] の中心的概念「**一つ悪影響を及ぼすモデルが混ざるだけで全体が崩壊する (one bad model spoils the bunch)**」や、Yang et al. [26] による「パラメータ空間における高分散方向（high-variance directions）へのマージ軌道による安全性低下」メカニズムを定式化。

- **1.2 安全性を考慮したマージ：進展と限界 (Safety-Aware Merging: Progress and Limits)**:
  - SafeMerge [8]（選択的・層ごとのコサインリバート）, MergeAlign [2]（合成安全データ混合）, LED-Merging [9]（ニューロン競合分離）, SALSA [27]（RLHF向けSFT平均）などの最新動向を紹介。
  - これらの手法が**局所的・ヒューリスティック**であり、合成データや層・ニューロン判定に依存しており、**パラメータ空間上のグローバルな安全性不変領域（global invariant region）を規定できていない限界**を明確化。

- **1.3 なぜ幾何学か：アライメントはスカラーではなく不変量である (Why Geometry: Alignment as an Invariant, Not a Scalar)**:
  - C2M3 [28] 等の幾何学的マージの流れを汲み、以下の3大原則に要約：
    1. *重み空間の線形性はアライメントに対して中立ではない* [1, 26]
    2. *干渉の解消は必要条件だが十分条件ではない*（TIES [5], DARE [6], DELLA [7], DF-Merge [14], 進化的マージ [29] はアライメント敏感方向を制約しないためミスアライメント漏洩を防げない）
    3. *現在の安全性対応マージ手法はグローバルな不変量を欠いている* [2, 8, 9]
  - 本論文の中心的メッセージ：「**アライメントは単なるスカラー評価値ではなく、モデル族における幾何学的な不変量（geometric invariant）として扱うべきである**」を導入。

- **1.4 本研究の目的と貢献 (Objectives and Contributions)**:
  - 介入粒度（ベクトル、層、ニューロン、パラメータ、部分空間・幾何）、利用情報（差分、符号・振幅、勾配、Fisher情報）、およびデータ依存性の観点から Secure Merge を比較分析する3つの主要貢献を再整理。

---

### 2. Research Questions (Section 2) の刷新
- **RQ1**: 幾何学的制約とパレート限界構造の解明
- **RQ2**: 介入粒度（ベクトル〜部分空間・幾何）が安全性・有用性・過剰拒否に与える影響
- **RQ3**: 符号・振幅のヒューリスティック vs Fisher・幾何感度制御の解明
- **RQ4**: データアクセス制限下でのデータフリー手法の頑健性
- **RQ5**: 条件別（モデル系列、計算量、過剰拒否許容度）の適用限界ガイドライン

---

### 3. 参考文献（References）の完全対応
引用箇所に対応する文献を漏れなく整理・追加しました：
- **[1]** Hammoud et al. (2024a) - *One Bad Model Spoils the Bunch*
- **[2]** Hammoud et al. (2024b) - *MergeAlign*
- **[3]** Wortsman et al. (2022) - *Model Soups*
- **[4]** Ilharco et al. (2023) - *Task Arithmetic*
- **[5]** Yadav et al. (2023) - *TIES-Merging*
- **[6]** Yu et al. (2024) - *DARE*
- **[7]** Deep et al. (2024) - *DELLA-Merging*
- **[8]** Djuhera et al. (2026) - *SafeMERGE*
- **[9]** Ma et al. (2025) - *LED-Merging*
- **[10]** Matena & Raffel (2022) - *Fisher-Weighted Averaging (FWA)*
- **[14]** Lee et al. (2025) - *Dynamic Fisher-weighted Merging (DF-Merge)*
- **[15]** Wang et al. (2025) - *AlignMerge (arXiv:2512.16245)*
- **[25]** Ortiz-Jiménez et al. (2023) - *Task Arithmetic in the Tangent Space*
- **[26]** Yang et al. (2024) - *Model Merging in LLMs: A Survey*
- **[27]** Chegini et al. (2024) - *SALSA: Alignment Soups*
- **[28]** Crisostomi et al. (2024) - *Cycle-Consistent Multi-Model Merging (C2M3)*
- **[29]** Akiba et al. (2025) - *Evolutionary Optimization of Model Merging Recipes*

---

## 保存ファイル一覧
- 改訂対象主要論文: [secure-merge_統一比較評価論文_改訂版.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_%E7%B5%B1%E4%B8%80%E6%AF%94%E8%BC%83%E8%A9%95%E4%BE%A1%E8%AB%96%E6%96%87_%E6%94%B9%E8%A8%82%E7%89%88.md)
- 改訂1・2節の抜粋履歴: [section1_2_revised.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_refinement_alignmerge/section1_2_revised.md)
- タスク管理: [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_refinement_alignmerge/task.md)
- 実装計画: [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_refinement_alignmerge/implementation_plan.md)
