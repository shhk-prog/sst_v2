# Implementation Plan - flmsec.tex 論文の体系的整理と推敲計画

本計画は、ユーザーから提示された査読フィードバックに基づき、論文 `/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex` の論理構造、RQと結論の整合性、論文タイプの統一（比較評価論文への寄せ）、数値・表・参照の不整合修正、考察の断定の緩和等を体系的に実施するための詳細計画です。

## User Review Required

> [!IMPORTANT]
> **論文主軸の統一**: 提案手法（SST-Merge）の単なる優越性をアピールする構成から、「**偽の安全性（gibberishによる見かけ上のASR低下）を除外・再評価する Secure Model Merge 評価枠組みの提案と、主要手法の比較評価・条件依存性の整理**」へと論文の軸を一本化します。
> これにより、研究の学術的整合性と査読における評価を大幅に向上させます。

> [!NOTE]
> **数値・表記の完全整合化**: 予備実験表（`Table \ref{tab:simple_prelim}` と `Table \ref{tab:prelim_detail_app}`）の不整合や、参照切れ（`JailbreakBench[2-]` 等）、手法名と References 引用キーのズレを完全に修正します。

## Proposed Changes

### 1. Document Structure & Meta Data
- [MODIFY] [flmsec.tex](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex)
  - Title / Author / Affiliation の NeurIPS / ICLR ダミー枠を適切なドラフト表記に更新
  - Abstract & Introduction: 比較研究・評価枠組みとしての論文タイプを最初に明確化

### 2. Result Section Refactoring (RQ Answers)
- [MODIFY] [flmsec.tex](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex)
  - `Results and Analysis` 節内に明示的な RQ 回答小節を追加:
    - `\subsection{Answer to RQ1: Pareto Frontiers and Architectural Discrepancies}`: 各手法群のパレート境界、ドメイン間干渉（code/medical等での落とし穴）の構造差を整理。
    - `\subsection{Answer to RQ2: Trade-offs in Sign/Magnitude Heuristics vs. Geometric Rules}`: 計算コスト、幾何計算のオーバーヘッド、攻撃頑健性・性能トレードオフを比較。
    - `\subsection{Answer to RQ3: Efficacy and Limits of Data-Free Merging}`: データアクセス制約下における Data-Free 手法の有効性と実用範囲を明確化。

### 3. Conclusion & Discussion Tone Adjustment
- [MODIFY] [flmsec.tex](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex)
  - Conclusion: 断定的な表現（"圧倒" "全ベースラインを凌駕" 等）を避け、以下の3点に再整理：
    1. SST系が特定設定で高い適合性・データ非依存の安定性を示すこと
    2. 高干渉条件（複合ドメイン）では複数手法に崩壊リスクが存在すること
    3. ASR単独評価は不十分であり、有効応答率を含めた評価枠組みが不可欠であること
  - Discussion: 「Delta Weightノルム乖離」「FIMスケール不均衡」「Norm Explosion」等の機序記述を「仮説的解釈・示唆 (suggests / hypothesized as)」として客観化。

### 4. Inconsistency & Reference Cleanup
- [MODIFY] [flmsec.tex](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex)
  - `tab:simple_prelim` と `tab:prelim_detail_app` の同名条件値（`data_free_sst`, `sst` 等）の数値を完全に同期化・修正
  - `JailbreakBench[2-]` などの崩れた参照の修復 (`\cite{chao2024jailbreakbench}`)
  - 本文中の手法参照 (`MergeAlign`, `SafeMERGE`, `LED-Merging`) と Citation List の完全一致
  - Raw Pareto AUC と Validity-aware Pareto AUC の定義の早期化
  - Limitations 節（Llama-2-7B中心、評価上限320、classifier依存性など）を追加

## Verification Plan

### Automated Tests
- LaTeXコンパイル環境でのビルド確認 (`pdflatex` / `latexmk`)。コンパイルエラーや未解決参照（`??`）が発生しないことを検証。
- `grep_search` による参照エラー (`[2-]`, `\ref{??}`) の完全全滅チェック。

### Manual Verification
- 予備実験表および本実験表の数値の整合性、結果・付録間での数値完全一致の手動照合。
- 各RQ（RQ1, RQ2, RQ3）と Results 内の解答小節、ならびに Conclusion の1対1対応の査読的セルフチェック。
