# 論文改訂計画: AAAI 2027 向けセキュアマージフレームワークの再構築

## 目的
プロジェクト内の `/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/論文 copy 2.md` を、AAAI 2027 への投稿を念頭に置いた、学術的かつ論理的に締まった構成の日本語論文草稿へ全面的に書き換えます。

提案手法を単なるマージ手法のヒューリスティックとしてではなく、**「有用性破壊コスト（Utility Tax）の制約下で安全性（Safety Gain）を最大化する “Fisher-ratio constrained patch deployment framework”」** として再定義し、2025年〜2026年の最先端関連研究（AlignMerge, SafeMERGE, LED-Merging 等）との技術的差異を明確にします。また、`/mnt/nas/home/hiromi/src/sst_v2/v3` で得られた `limit 320` での実証結果データを統合します。

---

## 1. 提案タイトル
**SST-Merge: Data-Free Fisher-Ratio Subspace Steering for Safety-Preserving Model Merging**
（SST-Merge: 安全性維持型モデルマージのための Data-Free Fisher 比部分空間ステアリング）

---

## 2. 論文の中心メッセージと構成設計
「安全パッチを単純に足すのではなく、**有用性を壊すコストあたりの安全性改善（safety gain per unit utility cost）が高い方向** だけを選別して注入する」というメッセージで論文全体を貫きます。

AAAIの7ページ制限（本文＋図表、参考文献除く）をクリアするため、以下の配分で書き換えます。

### セクション構成と役割

1. **Abstract (概要)**: 6文構成（問題、既存の限界（Safety Tax）、提案（SST-Merge）、理論的帰着（一般化固有値問題）、実用近似（対角 & Data-Free）、実験結果）。
2. **1. Introduction (導入)**: 安全パッチの配備要求から入り、Safety Tax を定義。先行研究10本を「Fisherベース一般マージ」「Layer適応/不確実性マージ」「アライメント維持型マージ」の3群に整理し、本手法の「Closed-form でありながらパラメータレベルの解像度で部分空間をステアリングする」という位置付けを明確化。
3. **2. Background and Problem Setup (背景と定式化)**: Base $\theta_0$, Utility $\theta_u$, Safety $\theta_a$ の記号を統一。Benign utility 分布 $D_u$ と Safety/Refusal 分布 $D_s$ を厳密に定義し、タスクの競合定式化。
4. **3. Fisher-Ratio Subspace Steering (理論の核)**: 局所二次近似、Tax と Gain の定義、制約付き最適化問題としての一般化 Rayleigh quotient への帰着、一般化固有値問題（GEVP）の定理化、対角 SST（パラメータごとの比）への展開。
5. **4. Data-Free SST and Algorithms (データフリー近似)**: キャリブレーションデータ不要な実用設定として、Task-vector ratio proxy（SST-V）と Magnitude proxy（SST-M）を理論的に整理。
6. **5. Experiments & Analysis (実験と分析)**: 5つの研究質問（RQ）を明示。`v3` で得られた結果（gsm8k, HarmBench ASR 等）を用いて、SST-Merge が高い数学力を維持しつつ、ASRを劇的に抑え込む Pareto frontier を示す。TIES, DARE などの競合比での優位性、および Della や `fisher_weighted` で見られたモデル崩壊の回避メカズムを解説。
7. **6. Limitation & Conclusion (限界と結論)**: 局所近似の制約、Data-free proxy の限界を分析し、結論を述べる。

---

## 3. 実装方針と変更ファイル

### [MODIFY] [論文 copy 2.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/%E8%AB%96%E6%96%87%20copy%202.md)
* 既存の記述を破棄し、上記の理論・論理構造に沿って日本語で全面的に再執筆します。
* `v3` の実証データ（`WizardMath`単体: gsm8k 39.38% / ASR 25.00%、`SafetyFT`: gsm8k 7.19% / ASR 0.00%、`SST alpha=0.8`: gsm8k 33.44% / ASR 3.75%、`TIES`: ASR 14.38%、`DARE`: ASR 10.31% 等）を正確に結果記述に反映します。

---

## 4. 検証計画
* 書き換えた Markdown ドキュメントの論理展開（Abstract から Conclusion まで）が、AAAIのフォーマットに合致しているか確認します。
* 数式（GEVP, 対角比 $f_{s,i} / (f_{u,i}+\epsilon)$ 等）や記号（$\theta_0$, $\theta_u$, $\theta_a$）の統一性が取れているかを検証します。
* 実験データが、現在の実行結果と完全に一致しているかを相互参照します。
