# 関連研究の統合とSST-Merge理論の再構築

本計画は、現在作成中の論文（`/Users/saki/lab/SST-main/docs/07_paper/論文.md`）において、指定された10本の先行研究を取り入れ、それらを基盤として提案手法（SST-Merge）の理論を再構築するものです。現在は提案手法が先行研究と切り離されて唐突に展開されていますが、これを「既存研究の限界を克服する自然な理論的帰結」として論理的に接続します。

## 背景と課題の整理（指定された10本の論文の分類）

提供された文献を以下の3つの理論的潮流として整理します。

1. **Fisher情報を用いたモデルマージの基礎**
   - *Merging Models with Fisher-Weighted Averaging [NeurIPS 2022]*
   - *Model Merging by Uncertainty-Based Gradient Matching [arXiv:2310.12808]*
   - *Fisher Mask Nodes for Language Model Merging [LREC 2024]*
   - *Task-Aware Model Merging via Fisher-Weighted Median [OpenReview]*
   - **要点**: 従来のTask Arithmetic（単純加算）の限界を克服するため、局所曲率や不確実性（Hessianの代替としてのFisher）を用いて、パラメータごとの重要度を重み付けする手法群。

2. **Safety-Utility競合とAlignment-Preserving Merging**
   - *AlignMerge - Alignment-Preserving LLM Merging via Fisher-Guided Geometric Constraints [arXiv:2512.16245]*
   - *SafeMERGE: Preserving Safety Alignment via Selective Layer-Wise Merging [arXiv:2503.17239]*
   - *MergeAlign: Combining Domain and Alignment Vectors [arXiv:2411.06824]*
   - *LED-Merging: Mitigating Safety-Utility Conflicts [ACL 2025]*
   - **要点**: 単なるタスク合成ではなく、アライメント（安全性）とドメインタスク（有用性）のトレードオフを解消する研究群。AlignMergeなどのように、単一のFisher計量空間内でアライメント軸をペナルティ化するといった幾何学的制約アプローチが登場している。

3. **Data-Free / 層別アプローチへの発展**
   - *Data-Free Layer-Adaptive Merging via Fisher Information [arXiv:2603.21705]*
   - **要点**: Fisher行列をデータフリーで近似し、層ごとの適応的マージ係数として利用する最新の理論。

## Proposed Changes (提案する修正内容)

### 1. 第2章：関連研究の再構築
以下のサブセクションを設け、既存研究の文脈を構築します。
- **A. Fisher情報と曲率に基づくモデルマージ**: Task Arithmeticの限界と、Fisherを用いた重み付け（Fisher-Weighted Averaging等）の発展を記述。
- **B. Safety-Utilityの競合とAlignment-Preserving**: MergeAlign, SafeMERGE, LED-Mergingなどの安全性と有用性を両立する手法の動向と、AlignMergeに見られる幾何学的アプローチを紹介。
- **C. 既存アプローチの限界（本研究の立ち位置）**: 既存手法は「事後的な重み付け」や「単一のベースモデルの曲率」に基づくペナルティである点を指摘。相反する2つの目的（安全性向上と一般性能維持）を、それぞれのデータ分布の曲率に基づく「競合」として直接定式化できていないという課題を提示。

### 2. 第3章：提案手法（SST-Merge）の理論的接続
現状の数式（Tax, Gain, GEVP, Surrogate）を活かしつつ、導入の論理展開を刷新します。
- **A. 理論の出発点**: 既存のAlignMerge等が単一のFisher計量でアライメントを扱うのに対し、本手法は「良性分布のFisher（$F_b$）＝Utilityのコスト」「有害分布のFisher（$F_h$）＝Safetyのゲイン」という2つの独立した計量を定義する点からスタート。
- **B. GEVPの導出**: 単なる足し算や事後ヒューリスティックではなく、「Tax上限の制約下でGainを最大化する」という最適化問題が、Rayleigh商の最大化および一般化固有値問題（GEVP）に帰着する理論的必然性を説明。
- **C. Surrogateへの橋渡し**: FIMを用いたマージが計算コストの壁に直面すること（*arXiv:2603.21705*等でも議論されている）を引き合いに出し、Diagonal SSTおよびData-Free SSTが「GEVPによる座標順位の保持」を目的とした現実的な近似手法（Surrogate）であることを位置づける。

---

## User Review Required

1. **数式構造の維持**:
   GEVPやSurrogateといった第3章の数式構造・定義自体は既存のものを維持し、その前後の「意味付け」や「他手法との対比・接続」を書き換えるという方針でよろしいでしょうか？
2. **論文リストの網羅性**:
   提供いただいた10本の論文は、2章の「関連研究」と3章の「理論の比較」の両方に適切に分散させて引用する形とします。

問題なければ、この計画に基づいて `論文.md` の書き換えを実行し、タスクリスト（`task.md`）の作成とウォークスルー（`walkthrough.md`）へ進みます。
