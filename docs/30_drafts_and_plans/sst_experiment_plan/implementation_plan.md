# SST-Merge 実験計画 (Implementation Plan)

本計画は、SST-Mergeの核となる主張（$F_h$のSafety Gain表現能力、SST比のPareto最適性、Data-Free surrogateの順位保持能力、ならびに手法の統計的再現性と頑健性）を実証するための実験および解析の設計を定義するものです。

## 目的
ユーザーから提供された実験方針に基づき、以下の5つの仮説を検証し、論文の主張を強固なものとする。

1. **$F_h$ が単なるパラメータ変化量ではなく、Safety Gainと強い相関を持つこと**
2. **$F_h$ 単体よりも、Fisher比 ($F_h / F_b$) を用いたSSTがPareto効率において優れていること**
3. **Data-Free surrogate が元のFisher比ランキングを十分に近似し、実用的な代替となること**
4. **実験結果が統計的に再現可能であり、有意な差が存在すること**
5. **手法がFIMのサンプルサイズやデータセットの違いに対して頑健であること**

## ユーザーレビュー必須

> [!IMPORTANT]
> 以下の実験計画の具体的な設定（評価指標、比較基準、実行条件）について、意図した内容と合致しているかご確認をお願いいたします。
> また、実験を実行するための既存コードベースの構成について追加情報が必要な場合は、「オープンな質問」をご参照ください。

## オープンな質問

> [!WARNING]
> 実装および実行フェーズに進む前に、以下の点についてご教示ください。
> 1. **コードの所在**: これらの検証スクリプトを実装するにあたり、ベースとなるモデル評価やFIM計算のスクリプトはどのディレクトリ（例：`04_experiments` や `03_implementation`）に配置すべきでしょうか？また、再利用可能なユーティリティ（評価用関数など）は既に存在しますか？
> 2. **対象モデル・データセット**: 使用するモデルアーキテクチャ（例: Llama-3-8Bなど）および具体的な評価ベンチマーク（Utility: MMLU, ARC 等 / Safety: AdvBench, HarmBench 等）の指定はありますか？

---

## 先行研究に基づく評価ベンチマークとベースライン

提供された10本の先行研究（NeurIPS 2022, LREC 2024, NAACL 2025, OpenReview 2025, ACL 2025など）および最新の安全・有用性マージ研究（SafeMERGE, AlignMerge 等）に基づき、本実験では以下のベンチマーク・データセットおよび比較手法を採用します。

### 1. 評価データセット・ベンチマーク
**Utility（タスク性能）:**
- **MMLU** (Massive Multitask Language Understanding): 総合的な知識評価
- **ARC-Challenge / ARC-Easy**: 推論および科学的知識
- **GSM8K**: 数学推論性能（SafeMERGE等で採用）
- **TruthfulQA / AlpacaEval**: 指示追従および事実性評価

**Safety（安全性・アライメント）:**
- **AdvBench / HarmBench**: 悪意あるプロンプト（Jailbreak）に対する耐性評価
- **DirectHarm / HexPhi**: 安全性アライメントの維持・崩壊の評価
- **XSTest**: 安全性パッチによる過剰拒絶（Over-refusal）の測定

### 2. 比較手法（Baselines）
1. **Task Arithmetic** / **TIES-Merging**: 標準的なタスクベクトルベースの手法
2. **DARE** (Drop And REscale): ランダムドロップによる干渉低減
3. **FWA (Fisher-Weighted Averaging)**: FIMを用いた古典的な重要度加重平均 (NeurIPS 2022)
4. **Fisher Mask Nodes / Fisher-Weighted Median**: 発展的な単一FIM活用手法 (LREC 2024, OpenReview 2025)
5. **LED-Merging**: パラメータ競合の非干渉化 (ACL 2025)
6. **SafeMERGE / AlignMerge**: Safety-Utility間の層別選択・幾何学的制約による最新の保護マージ (Arxiv 2025)

---

## 提案する変更（実験内容の詳細設計）

### 1. $F_h$ がSafety Gainを表すことの検証

**目的**: $\Delta^\top F_h \Delta$ が安全性改善と相関する量であることを示す。

- **比較方向 ($u_j$)**: SST上位、SST下位、ランダム、Magnitude上位、Safety Task Vector、Utility Task Vector
- **手法**: 微小スケール $\eta$ で $\theta' = \theta_{\mathrm{util}} + \eta u_j$ を作成し、以下を測定。
  - 推定Safety Gain: $G_h(u_j) = u_j^\top F_h u_j$
  - 実測Safety改善量: $\Delta \mathrm{JBRes}(u_j) = \mathrm{JBRes}(\theta') - \mathrm{JBRes}(\theta_{\mathrm{util}})$
- **評価データセット**:
  - 推定用 ($F_h$): Jailbreak trigger
  - 実測用 ($\Delta \mathrm{JBRes}$): AdvBench / HarmBench
- **評価指標**:
  - Spearman相関 / Pearson相関
  - Top-k方向 vs Bottom-k方向の平均Safety改善
  - bootstrap 95% CI
- **期待される結果**: $u^\top F_h u$ が高い方向ほどJB Resistanceが上がり、Fisher比 ($u^\top F_h u / u^\top F_b u$) がPareto改善と最も強く相関する。

### 2. Fisher比の有効性（SSTの本丸）検証

**目的**: $F_h$ 単体ではなく、$F_b$ と競合させるFisher比がPareto最適であることを示す。

- **選別基準**:
  - $f_{h,i}$ 上位 (Safety感度のみ)
  - $1/f_{b,i}$ 上位 (Utility保持のみ)
  - $|\Delta_s|$ 上位 (Task vector magnitude)
  - $\lambda_i = f_{h,i}/(f_{b,i}+\epsilon)$ 上位 (SST)
  - Random (Control)
- **比較対象手法**: 
  - 標準マージ: Task Arithmetic, TIES-Merging, DARE
  - FIMベース手法: FWA (NeurIPS 2022), Fisher-Weighted Median (OpenReview 2025)
  - 安全性保護マージ: LED-Merging (ACL 2025), SafeMERGE (Arxiv 2025), AlignMerge (Arxiv 2025)
- **評価データセット**:
  - **Utility**: MMLU, ARC, GSM8K (数学推論), AlpacaEval
  - **Safety**: HarmBench, AdvBench, DirectHarm (Jailbreak耐性)
- **統一条件**: 同じ $k$、同じ $\alpha$、同じマージ形式
- **評価指標**: 
  - JB Resistance (Safety向上度)
  - Utility score (性能維持率)
  - Over-refusal rate (過剰拒絶率: XSTestで測定)
  - Collapse rate (推論崩壊率)
  - Pareto AUC, Safety gain per utility loss
- **期待される結果**: SST比 $\lambda_i$ が全ての最先端手法 (SafeMERGE等) を上回る最もPareto効率が高いことを示し、$F_b$ との競合の必要性を実証する。

### 3. Data-Free Surrogateの順位保持検証

**目的**: Data-Free SSTがFisher比の順位を実用的なレベルで保持していることを示す。

#### 実験3-1: 順位相関
- **対象**: FIM版の比 $\lambda_i$ と Data-Free版の比 $\hat{\lambda}_i$
- **評価指標**: Spearman $\rho$, Kendall $\tau$, Top-k overlap, Jaccard overlap, Precision@k ($k \in \{1\%, 5\%, 10\%, 20\%, 50\%\}$)
- **期待される結果**: 全座標の相関は中程度でも、Top 5〜20%での一致率がRandomより有意に高い。

#### 実験3-2: Data-Free rankingの忠実度
- **対象**: Fisher比 Top-k, Data-Free Top-k, Random Top-k で実際の二次形式 $R(M)$ を測定。
- **期待される結果**: Data-Free Top-k がRandomより高く、方向選別の傾向を保持していることを実証。

### 4. 統計的再現性の実験

**目的**: 手法の堅牢性を統計的に証明し、査読への対策とする。

- **シード数**: 各手法で最低3シード（可能なら5シード）
- **変動要素**: LoRA学習シード、FIM sample subsetシード、DARE random maskシード、評価サンプル順序シード
- **報告項目**: 平均 ± 標準偏差、95% CI、paired bootstrap test、Pareto AUCの有意差
- **主要報告指標**: Pareto AUC または Utility (MMLU / GSM8K 等) @ JBRes (HarmBench 等) $\geq 80\%, 90\%$

### 5. 頑健性実験（アブレーション）

**目的**: FIM計算のコストやデータセット依存性への懸念を払拭する。

#### 実験5-1: FIM sample size ablation
- **対象**: $N \in \{50, 100, 250, 500, 1000\}$
- **評価指標**: $\lambda_i$ ranking stability, Top-k overlap with $N=1000$, 最終的なJB/Utility
- **期待される結果**: 少数サンプルでも十分な安定性を示す。

#### 実験5-2: Dataset transfer
- **対象**: 異なるデータセットでの推定と評価。
  - $F_b$: RepliQAやGSM8K等で推定 $\rightarrow$ MMLU / ARC / AlpacaEval / GSM8K でUtility評価
  - $F_h$: Jailbreak trigger等で推定 $\rightarrow$ AdvBench / HarmBench / DirectHarm / XSTest でSafetyと過剰拒絶を評価
- **期待される結果**: 単一データセットへの過適合ではなく、方向選別が一般化していることを証明。

---

## 確認計画 (Verification Plan)

### スクリプトの実装とテスト
- 各実験に対応する解析スクリプトおよび可視化スクリプトを作成する。
- 小規模なダミーデータまたは軽量モデルを用いてパイプラインが正常に動作することを確認する。

### 結果の集計と可視化
- 散布図、相関行列、Paretoフロントカーブなどの図表を出力し、論文に直接組み込める形式（PDF/PNG等）で保存する機能を実装する。
