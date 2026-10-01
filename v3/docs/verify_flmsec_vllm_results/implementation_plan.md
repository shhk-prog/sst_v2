# 実装計画 (Implementation Plan)

## 背景と目的
ユーザーからの要望に基づき、`flmsec.tex` 内の `\section{merge手法の詳細}` の内容を `AAAI.md` をベースに大幅に拡充する。特に、問題設定、関連研究との比較・新規性の明示、および提案手法（SST, Data-Free SST）の詳細な数理展開（Hard/Softマスク、補間、各プロキシの定義等）を網羅する。

## 提案する構成と追加内容の骨子

### 1. セクション名の変更
```diff
- \section{merge手法の詳細}
+ \section{merge手法の詳細と関連研究}
```

### 2. サブセクション構成案
以下の構成で、指定された資料（AAAI.md）の数式や参考文献（Author, Year 形式）を反映して執筆します。

#### 2.1 安全パッチ統合とSafety Taxの定式化
- ベースモデル $\theta_0$、有用性モデル $\theta_u$、安全モデル $\theta_s$ とタスクベクトル $\tau_u, \tau_s$ の定義。
- Task Arithmetic等の単純加算による統合と、それに伴う「Safety Tax（通常性能の劣化）」の課題を提示。

#### 2.2 既存のMerge手法とその限界（関連研究と比較）
- **General Model Merging**: TIES (Yadav et al. 2023), DARE (Yu et al. 2024), DELLA (Deep et al. 2024) などの干渉緩和。
- **Fisher-aware Model Merging**: Fisher-weighted averaging (Matena & Raffel 2022), DF-Merge (Sanwoo et al. 2025) など。これらは単一タスク空間の性能向上であり、競合する2分布の曲率比最適化は行わない点を指摘。
- **Safety-preserving Merging**: MergeAlign (Hammoud et al. 2024b), SafeMERGE (Djuhera et al. 2025), LED-Merging (Ma et al. 2025), AlignMerge (Wang et al. 2025)。SSTは反復最適化を不要とし、Fisher比からのClosed-formな抽出ルールを導く点で補完的であることを明記。
- **Data-free Merging**: FIM-Merging (Wang et al. 2026) と比較し、SSTは層単位ではなく要素単位（element-wise）で制御する優位性を記述。

#### 2.3 提案手法：Fisher-Ratio Safety Subspace (SST-Merge)
- **Utility Tax と Safety-Sensitive Energy**: $\frac{1}{2} \Delta^\top F_u \Delta$ と $\Delta^\top F_s \Delta$ の定義。
- **GEVPへの帰着**: $\max_v \frac{v^\top F_s v}{v^\top (F_u + \epsilon I) v}$ を解くことで「単位TaxあたりのSafety Energy」を最大化する方向（Fisher-Ratio Safety Subspace）を導出。
- **Diagonal SST-Merge**: $O(d^3)$ の計算コストを回避する対角近似 $r_i = \frac{f_{s,i}}{f_{u,i} + \epsilon}$。
- **マスキングと補間**:
  1. Hard Masking (Top-k Selection)
  2. Soft Masking (Sigmoid Masking)
  3. Coordinate-wise Interpolation (SST-Interpolation: $\alpha_i = \alpha \cdot w_i$)

#### 2.4 提案手法：Data-Free SST
- **モチベーション**: キャリブレーションデータが利用不可な環境への対応。
- **Task-Vector Ratio Proxy (SST-V)**: $r_i \approx \frac{\Delta_i^2}{\tau_{u,i}^2 + \epsilon}$ の数式と、その直感的なメカニズム（有用性獲得ベクトルをペナルティとし、安全アライメントベクトルを優先する）の解説。
- **Magnitude-only Ablation (SST-M)**: 重みサイズを用いた $\frac{|\theta_{s,i}|}{|\theta_{u,i}| + \epsilon}$。
- **Random-Token Fisher Variant**: 擬似テキストによる対角FIMの近似。

## User Review Required

上記の構成と内容で `flmsec.tex` の該当箇所を書き換えてもよろしいでしょうか？
関連研究の引用は、指定いただいた `(Author et al. Year)` の形式で直接テキストに埋め込む形で反映いたします。問題なければ、実際のLaTeXコードへ反映させます。
