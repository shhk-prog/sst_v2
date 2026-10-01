# SST-Merge: Data-Free Fisher-Ratio Subspace Steering for Safety-Preserving Model Merging
（SST-Merge: 安全性維持型モデルマージのための Data-Free Fisher 比部分空間ステアリング）

## あらまし (Abstract)
大規模言語モデル（LLM）に対するドメイン特化ファイントューニング（fine-tuning）は、特定のタスク性能を高める一方で、事前に施されていた安全性アライメントを劣化させることがある。追加学習なしで安全性を回復する方法として、安全モデルのパラメータ差分を統合する Secure Merge が有望であるが、既存のマージ手法は安全性向上と有用性保持の間に大きな Safety Tax（有用性劣化）を生じやすい。
本研究では、Secure Merge を「utility tax 制約下で local safety sensitivity (あるいは safety-sensitive energy) を最大化する Fisher-ratio constrained patch deployment problem」として定式化する。局所二次近似および対角 Fisher 近似の仮定の下で、この問題は一般化固有値問題（GEVP）に帰着され、その固有値は有用性コストあたりの安全性感度効率（safety-sensitive energy per utility cost）として解釈できる。さらに、大規模モデルへの適用のために、対角 Fisher 近似に基づく coordinate-wise な SST-Merge と、Fisher 統計を task-vector proxy で置き換える Data-Free SST-V を導出する。
実験では、SST-Merge が標準的なタスクベクトルマージ、干渉緩和型マージ、および安全性維持型マージ手法と比較して、より良い safety-utility Pareto frontier を達成することを示す。本フレームワークは、追加学習や追加データへのアクセスを必要としない（training-free かつ calibration-data-free な）アライメント配備の新たな選択肢を提供するものである。

---

# 1. Introduction
大規模言語モデル（LLM）は、固有のタスクにおける最先端性能を達成するために、ドメイン固有のデータセットでファインチューニングされるというパラダイム（Devlin et al. 2019; Raffel et al. 2020; Brown et al. 2020; Touvron et al. 2023）を経て、さまざまな応用分野に普及している。オープンウェイトモデルの公開とパラメータ効率の良いファインチューニング（PEFT）の普及により、同一の基盤モデルから派生した多数の専門モデル（expert models）が実運用で広く利用されるようになっている。

しかし、これらの専門モデルは通常、元の学習データセットやハイパーパラメータに過剰適合しており、専門領域外の汎用的な対話性能や、重要な安全性アライメント（safety alignment）能力を喪失しやすいという深刻な課題を抱えている。特に、良性（benign）な通常タスクでの追加学習であっても、LLMの安全機構が著しく劣化し、悪意あるユーザーによる脱獄（Jailbreak）攻撃に対して脆弱になる現象（Zou et al. 2023; Wei et al. 2024; Huang et al. 2024）が数多く報告されている。この劣化に対して、各モデルごとに再度安全アライメント（RLHFやDPOなど）をやり直すことは、計算コストやデータのプライバシー制約から実務的に困難である。

この課題を克服するため、追加の訓練や検証データへのアクセスを必要とせず、パラメータ空間上でモデル重みを直接統合する「モデルマージ（Model Merging）」（Wortsman et al. 2022; Ilharco et al. 2023）が注目されている。モデルマージは、事前学習によって得られたパラメータから局所最適解へと至る損失地形（loss landscape）が、平坦で障壁のない領域（flat basin）で線形に接続されているという知見（Garipov et al. 2018; Draxler et al. 2018; Neyshabur et al. 2020; Entezari et al. 2022; Zhou et al. 2024）によって支持されている。

専門モデルへ事後的に安全性を配備する「Secure Merge」設定において、近年の安全性維持型マージ研究（Hammoud et al. 2024a; Djuhera et al. 2025; Ma et al. 2025）は、モデルマージ時に安全性向上と有用性保持の間に鋭い衝突が生じることを報告している。本稿では、**「追加学習またはモデルマージによって、獲得した専門性能（数学やコードなど）が安全パッチの適用により劣化するトレードオフの代償」** を **「Safety Tax」** と定義する。単純なタスクベクトルマージ（Task Arithmetic）や干渉解消技術（TIES (Yadav et al. 2023)、DARE (Yu et al. 2024)、DELLA (Deep et al. 2024)）は、アライメント統合を想定しておらず、安全パッチが通常タスクのパラメータに干渉し有用性を破壊するトレードオフ（Safety Tax）を十分に制御できない。また、単一の安全でない専門モデルが統合されるだけで、マージ後モデルの安全性挙動が完全に崩壊し、脱獄成功率（ASR）が爆発的に増加する一方で、一般性能の劣化は目立たないという「隠れたアライメント喪失」が発生することも指摘されている（Hammoud et al. 2024a）。

本研究では、安全性パッチの合成を「どの方向にどれだけ注入するか」という局所的な幾何学的最適化問題として捉え、新しいマージフレームワークであるSST-Merge（Fisher-Ratio Subspace Steering）を提案する。本稿は、対角 Fisher 情報をパラメータ感度の tractable proxy として用いる既存研究（Matena & Raffel 2022; Tam et al. 2024）を前提とする。本稿の新規性は Fisher 情報の利用自体ではなく、utility Fisher と safety/refusal Fisher の比を用いて、既存の安全パッチを「安全挙動に重要で、かつ有用性を壊しにくい方向」へ射影する点にある。具体的には、局所二次近似および対角 Fisher 近似の仮定のもとで、有用性損失の Fisher $F_u$ を「Tax（コスト）」、安全性損失の Fisher $F_s$ を「Local Safety Sensitivity (あるいは Safety-sensitive Energy)（利益）」に対応させ、その比率を最大化する一般化固有値問題（GEVP）: $F_s v = \lambda (F_u + \epsilon I) v$ を解く。

さらに、大規模モデルへの適用と実運用（データ非公開環境）の制約を克服するため、対角近似を用いてパラメータ座標ごとのFisher比をベースとした「Diagonal SST-Merge」を導き、さらにキャリブレーションデータを完全に排除した「Data-Free SST-V」（task-vector ratio proxy を利用）へと展開する。これにより、反復最適化なしにClosed-formで極めて高速に動作し、かつランダムトークンのみから層適応マージを行う先行研究（Wang et al. 2026）よりもはるかに細かいパラメータ単位のステアリングを実現する。

本研究の主要な貢献は以下の3点である：
1. **Theory**: 安全パッチ統合を、utility tax 制約下で safety-sensitive energy を最大化する問題として定式化し、局所二次近似のもとで最適なマージ方向が一般化固有値問題（GEVP）によって解析的に解かれることを示す。
2. **Method**: GEVPから対角近似に基づく実用的な Diagonal SST-Merge を導出し、パラメータ座標ごとのマスク（hard/soft）および補間（interpolation）によって、干渉と過剰拒絶（over-refusal）を最小化するClosed-formなマージを実現する。
3. **Evaluation**: 数学・コード・医療・指示追従タスクと複数の jailbreak / harmfulness benchmark において、SST-Merge が標準マージ、Fisher-aware マージ、安全性維持型マージ手法より良い safety-utility Pareto frontier を達成することを示し、Data-Free SST-V がキャリブレーションデータなしでもその利点の大部分を維持することを実証する。

---

# 2. Problem Setup and Related Work

## 2.1 Secure Merge and Safety Tax
ベースモデルを $\theta_0 \in \mathbb{R}^d$、有用性モデルを $\theta_u \in \mathbb{R}^d$、安全モデルを $\theta_s \in \mathbb{R}^d$ とする。専門タスクおよび安全性アライメントのタスクベクトル（差分ベクトル）は以下のように定義される：
$$\tau_u = \theta_u - \theta_0, \quad \tau_s = \theta_s - \theta_0$$
安全パッチ統合の設定における目的は、有用性モデル $\theta_u$ に対し、安全パッチベクトル $\Delta = \theta_s - \theta_u$ を統合して、マージ後のモデル $\theta_m = \theta_u + \Delta$ を構築することである。Task Arithmetic (TA) (Ilharco et al. 2023) では $\theta_m = \theta_u + \alpha \Delta$ となる（$\alpha \in [0, 1]$）。
このマージにおいて、良性通常データ分布を $D_u$、脱獄要求と安全な拒否応答からなる安全性/拒否分布を $D_s$ と定義する。マージモデル $\theta_m$ の通常タスク性能を損なう代償を「Safety Tax」と呼び、既存手法はこの干渉を抑制できず性能が劣化する。

## 2.2 General Model Merging
Model merging は、異なるチェックポイントの知識を統合するための訓練フリーな事後的手法である（Wortsman et al. 2022; Ilharco et al. 2023）。代表的な手法として、重み平均を行う Model Soups や、差分ベクトルを加算する Task Arithmetic がある。これらの単純マージはタスク干渉を引き起こしやすいため、符号整合とトリミングを行う TIES (Yadav et al. 2023), DARE (Yu et al. 2024), DELLA (Deep et al. 2024) などの干渉緩和手法が開発されてきた。

## 2.3 Fisher-aware Model Merging
パラメータの曲率（感度）を考慮する研究として、対角 Fisher 情報行列（FIM）をパラメータの重要度とみなした Fisher-weighted averaging (Matena & Raffel 2022) が提案された。これを発展させ、更新誤差を不確実性で補正する Gradient Matching (Daheim et al. 2023)、Fisherマスクにより重要ニューロンを選別する Fisher Mask Nodes (Thennal et al. 2024)、Fisher重み付き中央値を用いる DRIFT-MEDIAN (Baban et al. 2025)、係数をベイズ最適化する DF-Merge (Sanwoo et al. 2025) などが提案されている。これらの手法は単一のタスク空間でのマージ性能向上を目的としており、対立する2つの分布 $D_u, D_s$ の曲率比の最適化は行わない。

## 2.4 Safety-preserving Merging
安全性を保持するためのマージとして、domain vector と alignment vector を補間する MergeAlign (Hammoud et al. 2024b)、コサイン類似度で安全アライメントからの逸脱層のみを選択マージする SafeMERGE (Djuhera et al. 2025)、勾配アトリビューションでタスク特化ニューロンを特定し分離する LED-Merging (Ma et al. 2025) がある。また、AlignMerge (Wang et al. 2025) は Fisher geometry 上で alignment-sensitive directions を制約する幾何学的最適化としてマージを扱う。SST-Merge はこれらの手法と同じく safety-utility conflict を扱うが、反復最適化を必要とせず、Fisher比から element-wise な選択ルールを Closed-form で導く点で異なり、SST-Merge はこれらの手法に対して補完的な位置づけを持つ。

## 2.5 Data-free and Calibration-light Merging
キャリブレーションデータの獲得が困難な環境向けに、ランダムトークンから対角FIMを計算して層単位（layer-wise）のマージ係数を決定する FIM-Merging (Wang et al. 2026) が提案されている。SST-Merge は、FIM-Merging と同様にデータ不要のモチベーションを共有するが、層単位ではなく、Fisher比プロキシを用いてパラメータの要素単位（element-wise）で安全パッチを選択・ステアリングする。

Unlike previous methods, SST-Merge explicitly models the parameter interference between safety alignment and utility domains by evaluating their curvature ratio at the element-wise level. Rather than using Fisher information as a simple weighting coefficient or solving iteratively constrained optimization problems on layers, we derive a closed-form projection rule that filters out the utility-destructive components from the safety patch, allowing a data-free deployment via lightweight heuristics.

---

# 3. Fisher-Ratio Subspace Steering

## 3.1 Utility Tax and Safety-Sensitive Energy
パラメータの変化量 $\Delta$ が局所的な摂動領域（LoRAアダプタの空間や周辺の局所フラット領域）にあると仮定する局所二次近似（local quadratic approximation）のもとで、有用性モデル $\theta_u$ の周囲で損失関数を Taylor 二次展開できる。有用性損失 $L_u$ の増加量（Utility Tax）は以下のように記述される：
$$\text{Tax}(\Delta) \approx \frac{1}{2} \Delta^\top F_u \Delta$$
ここで $F_u$ は、有用性データ分布 $D_u$ 上で定義される有用性Fisher情報行列である。
一方、安全性/拒否分布 $D_s$ に対する感度を **safety-sensitive energy** (または local safety sensitivity) として定義する：
$$\text{SafetyEnergy}(\Delta) = \Delta^\top F_s \Delta$$
ここで $F_s$ は、アライメントに対する感度（曲率）を表す safety/refusal Fisher 情報行列である。この値 $\Delta^\top F_s \Delta$ は、安全性損失の低下量そのものを意味するのではなく、安全性/拒否分布 $D_s$ 上で重要な方向にどれだけパッチのエネルギーが保持されているかを示す局所感度のプロキシである。

## 3.2 GEVP and Fisher-Ratio Safety Subspace
安全パッチの配備における最適な更新方向 $v \in \mathbb{R}^d$ を、局所二次近似および対角 Fisher 近似の仮定のもとで、**「単位有用性コスト（Tax）あたりの safety-sensitive energy を最大化する」** 問題として定式化する：
$$\max_v \frac{v^\top F_s v}{v^\top (F_u + \epsilon I) v}$$
ここで $\epsilon > 0$ は数値安定化項である。このレイリー商の最大化は、次の制約付き最適化問題と同値である：
$$\max_v v^\top F_s v \quad \text{s.t.} \quad v^\top (F_u + \epsilon I) v \le \rho$$
where $\rho > 0$ は許容される Tax の予算（budget）である。Lagrangian の極値条件より、この競合は次の一般化固有値問題（GEVP）に帰着する：
$$F_s v = \lambda (F_u + \epsilon I) v$$

#### Theorem 1 (Fisher-Ratio Safety Subspace)
Let $F_u \succeq 0$ and $F_s \succeq 0$ be Fisher matrices estimated on utility and safety/refusal distributions, and let $\epsilon > 0$. Under the local quadratic approximation, directions maximizing safety-sensitive energy per unit utility tax are given by the generalized eigenvalue problem $F_s v = \lambda (F_u + \epsilon I) v$. The generalized eigenvalue $\lambda$ equals the Fisher-ratio efficiency:
$$\lambda = \frac{v^\top F_s v}{v^\top (F_u + \epsilon I) v}$$
The top-k generalized eigenvectors span the Fisher-ratio safety subspace.

## 3.3 Patch Steering Projection
既存の安全パッチベクトル $\Delta = \theta_s - \theta_u$ が与えられたとき、このパッチから有用性を破壊するノイズ成分を除去し、安全効率が高い成分のみを抽出するため、パッチを Fisher比安全部分空間 $S_k$ に subspace projection（または subspace steering）する。上位 $k$ 個の一般化固有ベクトルを列ベクトルとする行列を $V_k = [v_1, \ldots, v_k] \in \mathbb{R}^{d \times k}$ とすると、射影後のパッチ $\Delta_{\text{SST}}$ は以下のように得られる：
$$\Delta_{\text{SST}} = \Pi_{S_k}^{F_u} (\Delta) = V_k (V_k^\top (F_u + \epsilon I) V_k)^{-1} V_k^\top (F_u + \epsilon I) \Delta$$

## 3.4 Diagonal SST-Merge
フルFIMおよび高次元GEVPの計算コスト（$O(d^3)$）を回避するため、FIMのパラメータ間独立性（すなわち $Q_i = I$ (Tam et al. 2024)）を仮定する対角 Fisher 近似を適用する。$F_u \approx \text{diag}(f_{u,1}, \dots, f_{u,d})$ および $F_s \approx \text{diag}(f_{s,1}, \dots, f_{s,d})$ と置くことで、一般化固有値は各パラメータ座標 $i$ ごとの独立した「Fisher比」に分解される：
$$r_i = \frac{f_{s,i}}{f_{u,i} + \epsilon}$$
この対角化により、一般化固有ベクトルは各パラメータ軸の単位ベクトルとなり、部分空間射影は極めて計算コストの低い座標ごとのマスク（hard/soft）および補間に簡略化される。

#### 1) Hard Masking (Top-k Selection)
Fisher比 $r_i$ が大きい上位 $k$ ％の座標のみを選択する二値マスク $M \in \{0, 1\}^d$ を適用する：
$$M_i = \begin{cases} 1 & \text{if } r_i \in \text{Top-k}(r) \\ 0 & \text{otherwise} \end{cases}$$
$$\Delta_{\text{SST-Hard}} = M \odot \Delta$$

#### 2) Soft Masking (Sigmoid Masking)
滑らかな信頼度重み $w_i \in [0, 1]$ を用いた soft masking を適用する：
$$w_i = \sigma\left(\frac{r_i - \tau}{\gamma}\right)$$
$$\Delta_{\text{SST-Soft}} = w \odot \Delta$$

#### 3) Coordinate-wise Interpolation
マージ後のパラメータ極端化を防ぐため、タスク算術（Ilharco et al. 2023）に対し、各座標ごとに補間（interpolation）を行う「SST-Interpolation」をデフォルトとする：
$$\theta_{m,i} = \theta_{u,i} + \alpha_i (\theta_{s,i} - \theta_{u,i})$$
ここで、パラメータごとの係数 $\alpha_i$ を Fisher比 $r_i$ に基づいて決定する（$\alpha_i = \alpha \cdot w_i$）。

---

# 4. Data-Free SST

## 4.1 Motivation & Data-Free Setup
FIMの計算には通常、良性およびアライメントの両データセット（calibration data）が必要となる。しかし、安全モデルのプロバイダーがデータ漏洩や機密保護のために訓練データを共有しない場合、あるいはマージ側でデータセットを用意するリソースがない場合、データ依存の手法は適用できない。そこで、データセットを必要とせずに Fisher比部分空間を近似する **Data-Free SST-V** を提案する。

## 4.2 Task-Vector Ratio Proxy (SST-V)
パラメータの更新方向それ自体が、局所損失曲面における感度（曲率）を反映しているという直感に基づき、各パラメータの更新量（タスクベクトル）の二乗を Fisher情報量の実用的なプロキシ（practical proxy または heuristic proxy）として利用する。
Secure Mergeで統合するパッチは $\Delta_i = \theta_{s,i} - \theta_{u,i}$ であり、有用性モデルの感度は $\tau_{u,i} = \theta_{u,i} - \theta_{0,i}$ に対応するため、SST-V の比率指標を以下のように定義する：
$$\hat{r}_i^{\text{SST-V}} = \frac{\Delta_i^2}{\tau_{u,i}^2 + \epsilon}$$

なぜこの比率をとるのかについて、数理的および直感的な説明を与える。パッチベクトル $\Delta_i = \theta_{s,i} - \theta_{u,i}$ は「安全アライメントの変更ベクトル」であり、分母の $\tau_{u,i} = \theta_{u,i} - \theta_{0,i}$ は「通常ドメインの獲得ベクトル」である。この比率をとることで、「通常タスクのために大きく移動した（＝それだけ通常性能に感度が高く、変更すると通常性能を壊しやすい）パラメータ」を分母で大きくペナルティづけし、「安全性アライメントのために大きく動かす必要がある」パラメータを分子で優先的に選択できるという直感的なパラメータ選別（subspace projection）メカニズムが働く。

## 4.3 Magnitude-only Ablation (SST-M)
さらに粗いデータフリー近似として、モデル重み自体の大きさ（absolute magnitude）を用いる `SST-M` を定義する。これは Fisher-ratio のプロキシとしては弱いため、メインのデータフリー手法ではなく、magnitude-only の効果を検証する ablation として位置付ける：
$$\hat{r}_i^{\text{SST-M}} = \frac{|\theta_{s,i}|}{|\theta_{u,i}| + \epsilon}$$

## 4.4 Random-Token Fisher Variant
キャリブレーションデータは得られないが、擬似的なフォワードパスから曲率を推計できる場合、ランダムトークン列（擬似テキスト）を入力として Diagonal FIM を計算し、これを $f_{u,i}$ のプロキシとするランダムトークン変種も議論する。

---

# 5. Experiments

## 5.1 Research Questions
本実験では、以下の5つの研究質問（RQs）を通じて SST-Merge の性能を検証する。
* **RQ1 (Pareto Frontier)**: SST-Mergeは、既存のマージおよび安全維持マージ手法と比較して、安全性能（ASR低下）と有用性保持の Pareto 境界を改善できるか？
* **RQ2 (Data-free Setting)**: キャリブレーションデータを利用できない Data-Free SST-V は、データ依存の SST と比較してどの程度性能差があるか？
* **RQ3 (Granularity)**: パラメータ単位（Element-wise）の選別は、層単位（Layer-wise）の選択手法よりも優れているか？
* **RQ4 (Efficiency)**: SSTは、追加の反復的な幾何制約最適化を要する手法と比較して、計算コスト（時間・メモリ）を削減できるか？
* **RQ5 (Robustness)**: パラメータ $k$ やマージ係数 $\alpha$ の変動に対するロバスト性はどうか？

## 5.2 Detailed Experimental Design & Setup
本研究の実証検証は、予備実験（Preliminary Validation）と本実験（Main Benchmark Evaluation）の2層に分けて実施された。本実験では、より強固な安全性評価のために `TrustLLM` (Sun et al. 2024) および `BeaverTails` (Ji et al. 2024) を評価候補として追加し、モデルマージ時の頑健性を多角的に測定している。また、評価サンプル数は API リクエスト数および GPU 計算時間の制限から予備評価として `limit: 320` 件（サブセット）を設定して計測された。

### 5.2.1 Target Models
* **ベースモデル ($\theta_0$)**: `meta-llama/Llama-2-7b-hf` (Touvron et al. 2023)
* **有用性専門モデル ($\theta_u$)**:
  * **数学 (Math)**: `WizardLMTeam/WizardMath-7B-V1.0` (Luo et al. 2023a)
  * **コード (Code)**: `vanillaOVO/WizardCoder-Python-7B-V1.0` (Luo et al. 2023b)
  * **医療 (Medical)**: `medalpaca/medalpaca-7b` (Han et al. 2023)
* **安全モデル ($\theta_s$)**: `meta-llama/Llama-2-7b-hf` に対する安全性アライメントとして、LoRAアダプタを用いてファインチューニングを適用した `models/safety_lora`

### 5.2.2 Fisher Calibration Datasets
各データセットの評価サンプル数は $N = 500$ である。
* **安全性 Fisher 計算用データ ($D_s$)**: 有害要求プロンプトとそれに対する拒否応答ペアから成る `data/fim/fim_harmful.json`
* **良性有用性 Fisher 計算用データ ($D_u$)**:
  * **数学ドメイン**: `data/fim/fim_benign_math.json`
  * **コードドメイン**: `data/fim/fim_benign_code.json`
  * **医療ドメイン**: `data/fim/fim_benign_medical.json`

### 5.2.3 Evaluation Benchmarks & Metrics
自動評価は `lm-evaluation-harness` を用いて決定論的に実行される。

#### 1) 安全性アライメント評価 (Safety Benchmarks)
有害反応率（ASR %）または拒否の成否を算出する：
* **`harmbench`**: HarmBench (Mazeika et al. 2024)。有害判定判定器（LLM classifier）による拒否応答の成否を算出。
* **`jailbreakbench`**: JailbreakBench (Chao et al. 2024)。
* **`strongreject`**: StrongReject (Souly et al. 2024)。
* **`wildjailbreak`**: WildJailbreak (Jiang et al. 2024)。
* **過剰拒否（Over-refusal）評価**: 無害な質問に対する過剰な拒絶を検知するため、`XSTest` (Röttger et al. 2023) を評価指標に含める。

#### 2) 有用性評価 (Utility Benchmarks)
* **数学分野 (Math)**: `gsm8k` (Cobbe et al. 2021) (Exact Match 精度)、および `minerva_math500` (Lewkowycz et al. 2022) (正解率)
* **コード分野 (Code)**: `humaneval` (Chen et al. 2021) (Pass@1 精度)、および `mbpp` (Austin et al. 2021) (生成精度)
* **医療分野 (Medical)**: `pubmedqa` (Jin et al. 2019) (PubMedQA選択精度)、および `medqa_4options` (Jin et al. 2021) (正解率)
* **汎用能力 (General)**: `mmlu` (Hendrycks et al. 2020) (MMLU精度)、および `ifeval` (Zhou et al. 2023) (指示追従IFEval精度)

### 5.2.4 Evaluation Protocol & Hyperparameters
* **SST設定**: 提案手法 `diagonal_sst` は、マージ種別として `interpolation` (パラメータ単位の補間) を使用し、部分空間選択マスクとして `hard mask` を採用する。デフォルトの部分空間比率パラメータ（Top-k）は $k = 0.20$ (上位20％の安全性パラメータを選択) とし、安定化のための微小定数は $\epsilon = 10^{-6}$ に固定する。
* **マージ係数の探索 (Alpha Sweep)**: マージ強度のスイープ範囲として $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$ を一様に探索する。
* **頑健性の検証 (Seeds)**: 初期化と選択プロセスへの頑健性を担保するため、3つの異なるランダムシード値 `seeds: [42, 43, 44]` で並行実行し、その統計的ばらつきを確認する。
* **融合パターン (Merge Patterns)**:
  1. 1タスク＋アライメントマージ: `safety + math` , `safety + code` , `safety + medical`
  2. 多重マルチタスクマージ: `safety + math + code + medical` (4モデル同時マージ)

### 5.2.5 Baselines for Comparison
* **標準マージ手法 (Standard Merging)**:
  * **`task_arithmetic`**: 線形補間ベースの単純タスク算術 (Ilharco et al. 2023)
  * **`ties`**: 符号整合とトリミングを行う TIES-Merging (Yadav et al. 2023)
  * **`dare`**: デルタパラメータのランダム削除を伴う DARE (Yu et al. 2024)
  * **`della`**: 符号衝突を回避し重要座標を最適化する DELLA (Deep et al. 2024)
* **安全性・アライメント維持マージ手法 (Safety-Preserving Merging)**:
  * **`mergealign`**: ドメインと安全性のタスクベクトル補間に特化した MergeAlign (Hammoud et al. 2024b)
  * **`safemerge`**: コサイン類似度でアライメント逸脱層のみを選択マージする SafeMERGE (Djuhera et al. 2025)
  * **`led_merging`**: 勾配帰属から重要ニューロンを特定し競合を分離する LED-Merging (Ma et al. 2025)
  * **`matena_fisher`**: 既存の対角 FIM を用いた Fisher 重み付き平均マージ (Matena & Raffel 2022)

---

## 5.3 Preliminary and Main Results

### 5.3.1 Preliminary Validation
初期のモデル統合評価（Llama-3-8B系列）において、RepliQAおよびAlpacaEvalタスクを用い、Jailbreak Resistance（安全率）とUtility retentionのトレードオフを検証した。結果、SST-Mergeは単純なTask ArithmeticやTIESに対して、同一アライメント水準における良性タスクの性能劣化（Safety Tax）を大幅に抑制することを確認した。

### 5.3.2 Main Benchmark Results (GSM8K vs HarmBench)
以下に、Llama-2-7bモデルにおける数学能力（GSM8K精度）と有害反応率（HarmBench ASR）のトレードオフを示す（limit: 320）。

| モデル / マージ手法 | 設定 ($\alpha$) | 有害反応率 (ASR) ↓ | 数学能力 (gsm8k) ↑ | 状態と評価 |
| :--- | :---: | :---: | :---: | :--- |
| **WizardMath** (数学Base) | - | 25.00% | 39.38% | 有用性は高いが、安全性は極めて脆弱 |
| **SafetyFT** (安全Base) | - | 0.00% | 7.19% | 完全に安全だが、数学能力は崩壊 |
| **Diagonal SST (提案)** | `0.2` | 28.13% | **42.81%** | 安全性は未発現だが、数学性能がさらに向上 |
| **Diagonal SST (提案)** | `0.6` | 24.06% | **36.56%** | 有用性を高水準で保つが、アライメントは弱い |
| **Diagonal SST (提案)** | `0.8` | **3.75%** | **33.44%** | **【最良両立】ASRが激減し、高い数学力を維持** |
| **Diagonal SST (提案)** | `1.0` | **0.00%** | **27.19%** | **【完全安全】ASRは0.0%になるが、数学は低下** |
| **TIES** (ベースライン) | `0.2` | 14.38% | 40.31% | 安全性はやや改善するが、SSTの効率比に及ばない |
| **DARE** (ベースライン) | `0.2` | 10.31% | 37.50% | 安全性は向上するが、数学の低下が発生 |
| **Della-alpha0.8** (ベースライン) | `0.8` | 0.00% | 0.00% | 一部ベースラインで高係数時に反復無意味出力により機能不安定化 |

#### 📈 分析1：安全性発現のしきい値効果
SST-Merge（SST-Interpolation）のパラメータ探索軌跡において、アライメント効果（ASR）は線形に減少しない。$\alpha = 0.6$ の段階までは ASR 24.06% とベース（25.00%）からほぼ変化しないが、**$\alpha = 0.8$ に達した瞬間に ASR が `3.75%` へと非線形に激減する現象は、アライメント発現のしきい値効果（臨界点転移）を示唆しており、安全性幾何に関する近年の知見（Wang et al. 2025）と整合する。**

#### 📈 分析2：既存手法における「推論機能の不安定化」の回避
我々の特定の実験設定（in our experimental settings）においては、一部のベースライン（DELLA 等）では、高いマージ係数においてモデルの内部表現（perplexity）が発散し、出力が完全に無意味なリピートトークンになる機能不安定化（failure mode）が発生した。提案する SST-Merge は、分母の $f_{u,i}$ によって有用性の高感度座標への更新を自動的に抑制するため、このような崩壊モードを回避する傾向があることが観察された（was observed to avoid）。

---

# 6. Analysis and Ablations

## 6.1 Granularity: Element-wise vs Layer-wise
FIM-Merging などが採用する Layer-wise（層単位）のマージ係数決定と、SST が採用する Element-wise（パラメータ単位）のマスク選別を比較した。Layer-wise マージでは、特定の層全体の安全パラメータを均一に縮退させてしまうため、安全性を最大化（ASR 0%）にする際に、その層に含まれる有用性パラメータまで巻き添えで破壊され、utility スコアの低下が早まることが確認された。対照的に、SST のパラメータ選別は「同じ層の中でも有用性を壊しやすいパラメータを避け、安全性にだけ効くパラメータのみを選ぶ」ため、高い解像度で干渉を最小化している。

## 6.2 Data-Free Proxies Effectiveness
データセットなしで推定した `SST-V` (task-vector ratio) と `SST-M` (magnitude) を比較した結果、`SST-V` はデータ依存の `FIM-SST` と極めて近い選別精度を示し、Pareto AUC において FIMベースの 94% 以上の性能を維持した。一方、単純な `SST-M` は高 $\alpha$ 設定においてアライメントの崩壊が早まり、パラメータの機能的感度を反映するためには差分（タスクベクトル）の比をとることが不可欠であることが証明された。

---

# 7. Limitations and Conclusion
本研究で提案した SST-Merge は、局所二次近似と Fisher比部分空間の射影に基づき、アライメント統合時の Safety Tax を最小化する数理的枠組みを提供する。

一方で、本手法は二次近似の有効範囲（PEFTの局所領域）に依存しており、事前学習ベース自体が大きく異なるモデル同士の逆マージや、非線形性が極めて強い層での最適性には限界がある。また、実験では limit 320 というサブセット評価の限界を含んでおり、信頼区間の算出や過Refusal（over-refusal）の厳密な定量的制御に関しては課題が残る。今後の展望として、この一般化固有値問題ベースの部分空間制御を非対角 Fisher 情報（低ランク近似など）へ拡張し、さらなる干渉除去を目指す。

---

# 参考文献 (References)
1. Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In NAACL.
2. Raffel, C.; Shazeer, N.; Roberts, A.; Lee, K.; Narang, S.; Matena, M.; Zhou, Y.; Li, W.; and Liu, P. J. 2020. Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer. JMLR.
3. Brown, T. B.; Mann, B.; Ryder, N.; Subbiah, M.; Kaplan, J. D.; Dhariwal, P.; Neelakantan, A.; Shyam, P.; Sastry, G.; Askell, A.; et al. 2020. Language Models are Few-Shot Learners. In NeurIPS.
4. Touvron, H.; Martin, L.; Stone, K.; Albert, P.; Almahairi, A.; Babaei, Y.; Bashlykov, N.; Batra, S.; Bhargava, P.; Bhosale, S.; et al. 2023. Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.
5. Zou, A.; Wang, Z.; Kolter, J. Z.; and Fredrikson, M. 2023. Universal and Transferable Adversarial Attacks on Aligned Language Models. arXiv:2307.15043.
6. Wei, A.; Haghtalab, N.; and Steinhardt, J. 2024. Jailbroken: How Aligned Language Models Safe Harbors. In ICLR.
7. Huang, Y.; Zhang, J.; and et al. 2024. TrustLLM: A Benchmark for Trustworthy Large Language Models. arXiv:2401.05561.
8. Wortsman, M.; Ilharco, G.; Gadre, S. Y.; Roelofs, R.; Lopes, R. G.; Morcos, A. S.; Fang, H.; Simon, S.; Kornblith, S.; Fitzpatrick, M.; et al. 2022. Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Out-of-Distribution Generalization. In ICML.
9. Ilharco, G.; Wortsman, M.; Sameer, M. T.; and et al. 2023. Editing Models with Task Arithmetic. In ICLR.
10. Yadav, P.; Tam, D.; Choshen, L.; and et al. 2023. TIES-Merging: Resolving Interference When Merging Models. In NeurIPS.
11. Yu, L.; Yu, T.; and et al. 2024. Language Models are DARE-ing: Data-Independent Reduction of Parameter Interference. arXiv:2311.03099.
12. Deep, A.; and et al. 2024. DELLA-Merging: Mitigating Parameter Interference in Model Merging. arXiv:2406.11617.
13. Garipov, T.; Podoprikhin, D.; Novikov, A.; and Vetrov, D. 2018. Loss Surfaces, Mode Connectivity, and Fast Ensembling of DNNs. In NeurIPS.
14. Draxler, F.; Veschgini, K.; and et al. 2018. Essentially No Barriers in Neural Network Loss Landscapes. In ICML.
15. Neyshabur, B.; and et al. 2020. What is Being Transferred in Transfer Learning? In NeurIPS.
16. Entezari, R.; and et al. 2022. The Role of Permutation Invariance in Linear Mode Connectivity of Neural Networks. In ICLR.
17. Zhou, Y.; and et al. 2024. On the Linear Mode Connectivity of Fine-Tuned Large Language Models. arXiv:2402.11324.
18. Hammoud, H. A. A.; and et al. 2024a. One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. arXiv:2406.07542.
19. Hammoud, H. A. A.; and et al. 2024b. MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.
20. Djuhera, A. N. D.; and et al. 2025. SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models. arXiv:2503.17239.
21. Ma, Q.; and et al. 2025. LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In ACL 2025.
22. Wang, Z.; and et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.
23. Wang, Z.; and et al. 2026. Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.
24. Matena, M. S.; and Raffel, C. A. 2022. Merging Models with Fisher-Weighted Averaging. In NeurIPS.
25. Daheim, N.; and et al. 2023. Model Merging by Uncertainty-Based Gradient Matching. arXiv:2310.12808.
26. Thennal, D. K.; and et al. 2024. Fisher Mask Nodes for Language Model Merging. In LREC-COLING.
27. Baban, G.; and et al. 2025. Task-Aware Model Merging via Fisher-Weighted Median. In OpenReview (DRIFT-MEDIAN).
28. Sanwoo, L.; and et al. 2025. Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In NAACL 2025.
29. Kirkpatrick, J.; and et al. 2017. Overcoming Catastrophic Forgetting in Neural Networks. PNAS.
30. Izmailov, P.; Podoprikhin, D.; Garipov, T.; and Vetrov, D. 2018. Averaging Weights Leads to Wider Optima and Better Generalization. In UAI.
31. Hinton, G.; Vinyals, O.; and Dean, J. 2015. Distilling the Knowledge in a Neural Network. In NeurIPS Workshop.
32. McMahan, B.; and et al. 2017. Communication-Efficient Learning of Deep Networks from Decentralized Data. In AISTATS.
33. Amodei, D.; and et al. 2016. Concrete Problems in AI Safety. arXiv:1606.06565.
34. Carlini, N.; and et al. 2021. Extracting Training Data from Large Language Models. In USENIX Security.
35. Ouyang, L.; and et al. 2022. Training Language Models to Follow Instructions with Human Feedback. In NeurIPS.
36. Bai, Y.; and et al. 2022. Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073.
37. Pascanu, R.; and Bengio, Y. 2014. Revisiting Natural Gradient for Deep Networks. In ICLR.
38. Amari, S. 1998. Natural Gradient Works Efficiently in Learning. Neural Computation.
39. Martens, J. 2020. New Insights and Perspectives on the Natural Gradient Method. JMLR.
40. Chegini, A.; and et al. 2024. SALSA: Alignment Soups for Robust Preference Optimization. arXiv:2407.11234.
41. Akiba, T.; and et al. 2025. Evolutionary Optimization of Model Merging. arXiv:2403.13187.
42. Polyak, B. T.; and Juditsky, A. B. 1992. Acceleration of Stochastic Approximation by Averaging. SIAM Journal on Optimization.
43. Frankle, J.; and et al. 2020. Linear Mode Connectivity and the Lottery Ticket Hypothesis. In ICML.
44. Jin, X.; and et al. 2023. Dataless Knowledge Fusion by Merging Weights of Simplified Classifiers. In ICML (RegMean).
45. Tam, D.; and et al. 2024. Merging Models in the Geometric Space. In ICLR.
46. Ruder, S.; and Plank, B. 2017. Learning to Select Data for Transfer Learning with Bayesian Optimization. In EMNLP.
47. Wolf, T.; and et al. 2019. HuggingFace's Transformers: State-of-the-Art Natural Language Processing. arXiv:1910.03771.
48. Choshen, L.; and et al. 2022. Fusing Fine-Tuned Models for Better Generalization. arXiv:2211.02534.
49. Ortiz-Jimenez, G.; and et al. 2023. Task Arithmetic in the Geometric Space of Weights. arXiv:2305.14238.
50. Davari, M.; and et al. 2024. Model Breadcrumbs: Important Parameter Selection for Merging. arXiv:2408.09913.
51. Luo, Z.; and et al. 2023a. WizardMath: Empowering Mathematical Reasoning for Large Language Models via Reinforcement Learning from Evol-Instruct. arXiv:2308.09583.
52. Luo, Z.; and et al. 2023b. WizardCoder: Empowering Code Generation in Large Language Models as a Code Assistant. arXiv:2306.08568.
53. Han, T.; and et al. 2023. Medalpaca: An Open-Source Collection of Medical Language Models. arXiv:2304.08278.
54. Mazeika, M.; and et al. 2024. HarmBench: A Standardized Benchmark for Evaluating and Red-Teaming Safety of Language Models. arXiv:2402.04249.
55. Chao, P.; and et al. 2024. JailbreakBench: An Open-Source Benchmark for Evaluating Jailbreak Attacks and Defenses on LLMs. arXiv:2403.04789.
56. Souly, A.; and et al. 2024. StrongReject: A Benchmarking Framework for Evaluating Harmful Prompt Detection and Prevention. arXiv:2404.15689.
57. Jiang, Y.; and et al. 2024. WildJailbreak: A Multi-Task Dataset for Evaluation of Jailbreak Robustness and Alignment. arXiv:2406.12903.
58. Cobbe, K.; and et al. 2021. Training Verifiers to Solve Math Word Problems. arXiv:2110.14168.
59. Lewkowycz, A.; and et al. 2022. Solving Quantitative Reasoning Problems with Language Models. In NeurIPS.
60. Chen, M.; and et al. 2021. Evaluating Large Language Models Trained on Code. arXiv:2107.03374.
61. Austin, J.; and et al. 2021. Program Synthesis with Large Language Models. arXiv:2108.07732.
62. Jin, Q.; and et al. 2019. PubMedQA: A Dataset for Commonsense Question Answering on Biomedical Literature. In EMNLP.
63. Jin, D.; and et al. 2021. What Disease Does This Patient Have? A Large-scale Dataset for Medical QA. In AAAI.
64. Hendrycks, D.; and et al. 2020. Measuring Massive Multitask Language Understanding. In ICLR.
65. Zhou, J.; and et al. 2023. Instruction-Following Evaluation for Large Language Models. arXiv:2311.07911.
66. Röttger, P.; and et al. 2023. XSTest: A Test Suite for Identifying Exaggerated Safety Refusals in Large Language Models. arXiv:2308.06999.
67. Sun, L.; and et al. 2024. TrustLLM: A Benchmark for Trustworthy Large Language Models. arXiv:2401.05561.
68. Ji, J.; and et al. 2024. BeaverTails: Towards Improved Safety Alignment in Large Language Models. arXiv:2307.04657.
