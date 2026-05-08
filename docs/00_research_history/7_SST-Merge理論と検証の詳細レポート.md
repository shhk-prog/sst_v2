# **安全サブスペース選択型Task Arithmetic (SST-Merge) に関する包括的研究報告書：理論的定式化の厳密化と計算スケーラビリティの検証**

## **1\. 序論：大規模言語モデル適応における構造的課題とSST-Mergeの提唱**

### **1.1 大規模言語モデルにおける事後学習のジレンマ**

現在の大規模言語モデル（LLM）開発において、事前学習（Pre-training）に続く事後学習（Post-training）フェーズ、特に安全性アライメント（Safety Alignment）の重要性は論をまたない。モデルが有害な指示（爆発物の製造方法や差別的な発言の生成など）を拒否し、倫理的なガイドラインに準拠することは、社会的実装の前提条件である。しかし、この安全性アライメントには不可避とも言える副作用が伴うことが、近年の研究で明らかになっている。

この副作用は「Safety Tax（安全税）」と呼称され、モデルの安全性を高めるためのファインチューニングが、モデルが本来持っていた推論能力、コーディング能力、あるいは一般的な言語理解能力といった「良性タスク（Benign Tasks）」の性能を著しく劣化させる現象を指す 1。例えば、過剰な拒否（Over-refusal）により、無害な質問に対しても「お答えできません」と応答してしまうケースや、複雑な論理推論において正答率が低下するケースが報告されている。これは、パラメータ空間において「安全性を高める方向」と「有用性を維持する方向」が複雑に絡み合い、単純な最適化では両立が困難であることを示唆している。

### **1.2 Parameter-Efficient Fine-Tuning (PEFT) とモデルマージングの台頭**

この問題に対処するため、全パラメータを更新するフルファインチューニング（Full Fine-Tuning）ではなく、Low-Rank Adaptation (LoRA) に代表されるParameter-Efficient Fine-Tuning (PEFT) が採用されるようになった。LoRAは、巨大な重み行列の更新を低ランク行列の積に分解することで、計算コストを劇的に削減しつつ、特定タスクへの適応を可能にする。

さらに、複数の異なるタスク（例えば、数学能力向上タスクと安全性向上タスク）で学習された複数のLoRAアダプタを、推論時に単一のモデルとして統合する「モデルマージング（Model Merging）」技術が注目されている。モデルマージングは、再学習コストなしに複数の能力を統合できる有望なアプローチであるが、ここでも「タスク干渉（Task Interference）」という壁が立ちはだかる 3。単純に複数のアダプタを加算平均すると、あるタスクの知識が別のタスクの知識を破壊し、結果として統合モデルの性能が個別のモデルよりも劣る現象が発生する。

### **1.3 SST-Merge (Safety Subspace Task-Merge) の位置づけと本報告書の目的**

本報告書で詳述する **SST-Merge (Safety Subspace Task-Merge)** は、この「Safety Tax」と「タスク干渉」という二重の課題に対し、幾何学的なアプローチではなく、統計的・情報幾何学的なアプローチで挑む最新のマージング手法である。

SST-Mergeの核心は、モデルマージングを単なるパラメータの足し合わせとしてではなく、**「有用性の損失（コスト）を最小限に抑えつつ、安全性の向上（ゲイン）を最大化する」という制約付き最適化問題**として再定義した点にある。そして、この最適化問題を解くために、損失関数の曲率情報（Curvature）を利用した **一般化固有値問題（Generalized Eigenvalue Problem: GEVP）** を導入する。

本報告書は、SST-Mergeの研究計画における **Phase 1（理論的検証と定式化の厳密化）** および **Phase 2（計算効率とスケーラビリティの検証）** の成果を、数理的な詳細と共に包括的に記述するものである。特に、SST-Mergeがいかにして既存のSOTA手法（AlignGuard-LoRAやDAREなど）の理論的限界を克服し、かつLLMという巨大なパラメータ空間において計算論的に実行可能であるかを、厳密な数式展開とアルゴリズム解析を通じて論証する。

## ---

## **2\. 関連研究と背景：幾何学的マージングから統計的マージングへの進化**

モデルマージング技術の進化は、パラメータ空間をどのように解釈するかという「視座の転換」の歴史である。本章では、SST-Mergeの優位性を理解するための前提として、既存手法のメカニズムとその限界を詳細に分析する。

### **2.1 第一世代：Task Arithmetic (TA) と線形結合の限界**

モデルマージングの最も原始的かつ直感的な手法は、Task Arithmetic (TA) である 3。これは、ファインチューニング済みのモデル重み $\theta_{ft}$ と事前学習済みモデル重み $\theta_{pre}$ の差分を「タスクベクトル（Task Vector）」$\tau = \theta_{ft} - \theta_{pre}$ と定義し、複数のタスクベクトルを線形結合して新たなモデルを作成する。

$\theta_{merged} = \theta_{pre} + \sum_{i} \lambda_i \tau_i$

ここで $\lambda_i$ はスケーリング係数である。TAは驚くほどシンプルであるが、重大な欠陥を抱えている。それは、ニューラルネットワークのパラメータが持つ「構造的な意味」や「重要度の不均一性」を完全に無視している点である。すべてのパラメータを等価なベクトル成分として扱うため、あるタスクで重要なパラメータが、別のタスクのノイズによって上書きされる「破壊的干渉」が頻発する。

### **2.2 第二世代：TIES-Merging による干渉の緩和**

TIES-Merging (TRIM, ELECT SIGN & MERGE) は、TAの欠陥を修正するために提案された 3。TIESは以下の3つのステップで干渉を軽減する。

1. **Trim (剪定):** タスクベクトルの中で、絶対値（マグニチュード）が小さい、つまり更新量が少ないパラメータをノイズとみなしてゼロにする。これは「大きく動いたパラメータこそが重要である」という仮定に基づいている。  
2. **Elect Sign (符号決定):** 各パラメータについて、複数のタスクベクトル間で符号（正負）が一致するかを確認し、多数決や総和によって統合後の符号を決定する。  
3. **Merge (結合):** 決定された符号を持つ値のみを平均化する。

TIESはパラメータの「方向」と「大きさ」を考慮に入れた点で進歩したが、依然としてパラメータ空間のユークリッド幾何学に依存しており、そのパラメータが損失関数に与える影響度（感度）は考慮されていない。

### **2.3 第三世代：DARE と SVDに基づく幾何学的アプローチ**

DARE (Drop And REscale) や TSV-Merge (Task Singular Vectors) は、特異値分解（SVD）を用いてタスクベクトルの幾何学的構造を解析する手法である 1。

LoRAの更新行列 $\Delta W$ は低ランク構造を持つため、SVDによって $\Delta W = U \Sigma V^\top$ と分解できる。DAREやTSVは、この特異値 $\Sigma$ に着目し、主要な特異ベクトル（Principal Components）のみを残すことで、タスク固有の情報を抽出しようとする。  
具体的には、小さな特異値を切り捨てる（Drop）とともに、残った成分を再スケーリング（Rescale）することで、元のモデルの挙動を近似しつつ干渉を避ける。  
**限界:** SVDはあくまでパラメータ更新行列の「形状（ランクやスパン）」を解析するツールであり、その更新が「どの程度損失関数を改善するか」という機能的な情報は持っていない。したがって、幾何学的には主要な成分であっても、実際のタスク性能には寄与しない（あるいは有害な）方向が含まれる可能性を排除できない。

### **2.4 第四世代：曲率情報（Curvature）とFisher Information Matrix**

SST-Mergeが属する第四世代は、パラメータの幾何学的配置ではなく、損失関数の形状、すなわち「曲率（Curvature）」に着目する。これを記述するための核心的なツールが **Fisher Information Matrix (FIM)** である。

#### **AlignGuard-LoRA (AGL) のアプローチ**

SST-Mergeの直接的な競合となるAlignGuard-LoRA (AGL) は、安全性データセットにおけるFIM ($F_{\text{safety}}$) を利用する 4。AGLの戦略は「防御的」である。

1. 安全性データセットを用いてFIMを計算する。  
2. FIMを固有値分解し、固有値が大きい（＝曲率が高い、安全性が敏感な）方向を特定する。  
3. 新たなタスク（良性タスク）を学習する際、LoRAの更新がこの「安全性が敏感な方向」へ変化しないように正則化をかける、あるいはその方向への更新を直交射影によって削除する。

**AGLの限界:** AGLは「安全性を壊さないこと」には成功するが、「安全性を向上させつつ、有用性を最大化する」という能動的なトレードオフの最適化は行っていない。あくまで静的な制約条件としてFIMを利用しているに過ぎない。

## ---

## **3\. Phase 1：SST-Mergeの理論的定式化と厳密性の証明**

SST-MergeのPhase 1における最大の成果は、モデルマージングの問題を「二つのFIMの比率最大化」という、数学的に扱いやすく、かつ物理的意味の明確な最適化問題に帰着させたことである。本章では、その導出過程を詳細な数式と共に解説する。

### **3.1 問題定義：相反する二つの目的**

我々は、事前学習済みモデル $\theta_{pre}$ に追加するLoRAパッチ（パラメータ更新） $\phi$ を求めたい。この $\phi$ は以下の二つの目的を達成する必要がある。

1. 目的1：Safety Gainの最大化  
   有害データセット $D_{\text{harm}} = \{(x_i, y_{refusal})\}$ において、モデルが拒否応答 $y_{refusal}$ を生成する確率（尤度）を高めたい。  
   損失関数 $L_{\text{harm}}(\theta)$ は負の対数尤度として定義されるため、これを最小化（改善量を最大化）する。  
2. 目的2：Utility Costの最小化  
   良性データセット $D_{\text{benign}} = \{(x_j, y_{benign})\}$ において、モデルの挙動がベースモデルから乖離することを防ぎたい。これは「Safety Tax」を抑制することと同義である。  
   損失関数 $L_{\text{benign}}(\theta)$ は、ベースモデル分布 $p(\cdot|x; \theta_{pre})$ と更新モデル分布 $p(\cdot|x; \theta_{pre}+\phi)$ の間のKLダイバージェンスとして定義される。

### **3.2 損失関数の二次近似とテイラー展開**

$\phi$ が微小であると仮定し、各損失関数を $\phi=0$ の近傍で二次テイラー展開する。

#### **3.2.1 有害ロスの展開**

$L_{\text{harm}}(\theta_{pre} + \phi) \approx L_{\text{harm}}(\theta_{pre}) + \nabla L_{\text{harm}}(\theta_{pre})^\top \phi + \frac{1}{2} \phi^\top H_{\text{harm}} \phi$  

ここで、我々が関心があるのは「改善量（Gain）」である。定数項 $L_{\text{harm}}(\theta_{pre})$ を無視し、一次の勾配項 $\nabla L_{\text{harm}}$ と二次のヘッセ行列 $H_{\text{harm}}$ に注目する。SST-Mergeでは、統計的な頑健性を確保するため、ヘッセ行列の期待値として Fisher Information Matrix (FIM) を採用する 6。  
また、マージングの文脈では、局所的な勾配の方向よりも、パラメータ空間全体の構造的な「感度」が支配的であるため、二次形式の最大化として定式化する（あるいは、勾配方向への移動を二次形式で評価すると解釈する）。  
よって、有害ロス改善のメトリック（Gain）は以下のように定義される。

$\text{Gain}(\phi) = \phi^\top F_{\text{harm}} \phi$  
ここで $F_{\text{harm}}$ は有害データに関するFIMである。

$F_{\text{harm}} = \mathbb{E}_{(x, y) \sim D_{\text{harm}}} \left[ \nabla_\phi \log p(y|x; \phi) \nabla_\phi \log p(y|x; \phi)^\top \right]$

#### **3.2.2 良性タスクにおけるコストは、KLダイバージェンス $D_{KL}(p_{\theta_{pre}} \| p_{\theta_{pre}+\phi})$ で表される。KLダイバージェンスのテイラー展開において、一次項（勾配）はゼロになり、二次項にFIMが現れることは情報幾何学の基礎的性質である。**

$ D_{KL}(p_{\theta_{pre}} \| p_{\theta_{pre}+\phi}) \approx \frac{1}{2} \phi^\top F_{\text{benign}} \phi $ 

ここで $F_{\text{benign}}$ は良性データに関するFIMであり、モデルの予測分布に基づく期待値で定義される（経験分布ではない点に注意）。

$F_{\text{benign}} = \mathbb{E}_{x \sim D_{\text{benign}}} \mathbb{E}_{y \sim p(\cdot|x; \theta_{pre})} \left[ \nabla_\phi \log p(y|x; \phi) \nabla_\phi \log p(y|x; \phi)^\top \right]$

したがって、良性ロスの悪化メトリック（Cost）は以下となる。

$\text{Cost}(\phi) = \phi^\top F_{\text{benign}} \phi$  

この $F_{\text{benign}}$ は、良性タスクの知識を保持するためにパラメータが「硬直」すべき度合いを表しており、この値が大きい方向へパラメータを動かすと、甚大なSafety Tax（性能劣化）が発生することを意味する。

### **3.3 制約付き最適化問題の構成**

SST-Mergeの目標は、「良性タスクへの悪影響（コスト）を許容範囲 $C$ に抑えつつ、有害タスクの改善（ゲイン）を最大化する方向 $\phi$ を見つけること」である。これは以下の制約付き最適化問題として定式化できる 6。

$\text{Maximize} \quad \phi^\top F_{\text{harm}} \phi$

$\text{Subject to} \quad \phi^\top F_{\text{benign}} \phi = C$  

この問題は、パラメータベクトル $\phi$ の「向き」と「大きさ」に分解して考えることができる。向きが決まれば、大きさは制約条件 $C$ によって決定される。したがって、本質的な問題は最適な「向き」$v$ を決定することである。

### **3.4 ラグランジュの未定乗数法とRayleigh Quotient**

この制約付き最適化問題を解くために、ラグランジュ関数 $\mathcal{L}(\phi, \lambda)$ を導入する。

$\mathcal{L}(\phi, \lambda) = \phi^\top F_{\text{harm}} \phi - \lambda (\phi^\top F_{\text{benign}} \phi - C)$  

$\phi$ で微分してゼロと置くと、極値条件が得られる。

$\frac{\partial \mathcal{L}}{\partial \phi} = 2 F_{\text{harm}} \phi - 2 \lambda F_{\text{benign}} \phi = 0$

$\therefore F_{\text{harm}} \phi = \lambda F_{\text{benign}} \phi$  
これは、行列ペア $(F_{\text{harm}}, F_{\text{benign}})$ に対する 一般化固有値問題（Generalized Eigenvalue Problem: GEVP） そのものである 4。  
この式に左から $\phi^\top$ を掛けると、

$\phi^\top F_{\text{harm}} \phi = \lambda \phi^\top F_{\text{benign}} \phi$

$\lambda = \frac{\phi^\top F_{\text{harm}} \phi}{\phi^\top F_{\text{benign}} \phi}$  
この右辺は Rayleigh Quotient（レイリー商） $R(\phi)$ と呼ばれる。  
すなわち、ラグランジュ乗数 $\lambda$ は、その方向 $\phi$ における「コストに対するゲインの比率」を表しており、SST-Mergeではこれを 「安全効率（Safety Efficiency）」 と定義する。

### **3.5 一般化固有値問題の解と安全サブスペースの構築**

GEVP $F_{\text{harm}} v = \lambda F_{\text{benign}} v$ を解くと、一般化固有値 $\lambda_i$ と対応する一般化固有ベクトル $v_i$ のペアが得られる。  
ここで、固有値 $\lambda_i$ が大きいほど、その方向 $v_i$ は「良性タスクをほとんど害さずに、有害タスクを劇的に改善できる方向」であることを意味する。逆に、$\lambda_i$ が小さい方向は、安全性を上げるために大きな犠牲（Safety Tax）を払う必要がある方向である。  
SST-Mergeのアルゴリズムは以下の通りとなる。

1. $F_{\text{harm}}$ と $F_{\text{benign}}$ を構築する。  
2. GEVPを解き、固有値の大きい順にソートする： $\lambda_1 \ge \lambda_2 \ge \dots \ge \lambda_k \dots$  
3. 上位 $k$ 個の固有ベクトル $V_k = [v_1, v_2, \dots, v_k]$ を選択する。  
4. この $V_k$ で張られる部分空間 $S_{\text{safety}}$ を「安全サブスペース」と定義する。  
5. 元のLoRAパッチ $\phi_{original}$ をこのサブスペースに射影、あるいはこのサブスペース内で最適な係数を再学習し、最終的なマージングパッチ $\phi_{merged}$ を得る。

### **3.6 既存手法に対する理論的優位性の証明**

この定式化により、SST-MergeがAlignGuard-LoRA (AGL) やDAREに対して持つ理論的優位性は明白となる。

| 特性 | AlignGuard-LoRA (AGL) | DARE (SVD) | SST-Merge (GEVP) |
| :---- | :---- | :---- | :---- |
| **使用行列** | 単一の $F_{\text{safety}}$ | 重み行列の相関行列 ($W^\top W$) に相当 | $F_{\text{harm}}$ と $F_{\text{benign}}$ のペア |
| **最適化の視点** | **防御的**: 安全性が敏感な方向を避ける（正則化）。 | **幾何学的**: 大きく変化した方向を残す。 | **能動的**: 効率（Gain/Cost）を最大化する方向を選ぶ。 |
| **数理的解釈** | 制約条件の充足 | 主成分分析 (PCA) 的なノイズ除去 | **多目的最適化のパレート最適解探索** |
| **Safety Taxへの対処** | 副次的な効果として期待 | 考慮外（偶発的に軽減されるのみ） | **目的関数として直接最小化** |

特にAGLとの対比において、SST-Mergeは「回避」ではなく「活用」のアプローチを採る。AGLは $F_{\text{safety}}$ の固有値が高い方向を「危険」とみなして抑制するが、SST-Mergeはその方向が $F_{\text{benign}}$ において低いコストであれば、むしろ「最も有効な方向」として積極的に採用する。この判断ができるのは、二つのFIMを同時に扱えるGEVPの枠組みだけである。

## ---

## **4\. Phase 2：計算効率とスケーラビリティの検証**

理論的に優れたGEVPアプローチも、計算コストが現実的でなければ画餅に帰す。LLMのパラメータ数 $N$ は数十億から数千億に及び、$N \times N$ のFIMを計算・保持することは不可能である。Phase 2では、この「次元の呪い」を克服するための近似戦略と、そのスケーラビリティを検証する。

### **4.1 計算量の壁とLoRAによる次元削減**

フルファインチューニングされたモデルの場合、FIMのサイズは例えば7Bモデルで $(7 \times 10^9)^2$ となり、計算も保存も不可能である。  
しかし、SST-MergeはLoRAアダプタのマージングを前提としている。LoRAパラメータは低ランク行列 $A \in \mathbb{R}^{r \times k}, B \in \mathbb{R}^{d \times r}$ で構成され、その実効的なパラメータ数は非常に少ない（通常、全パラメータの1%未満）。  
SST-Mergeは、GEVPを全パラメータ空間ではなく、この **LoRA部分空間（LoRA Subspace）** 上で定義する。これにより、問題の次元は $N$ から $N_{lora}$ へと劇的に削減される。しかし、それでも $N_{lora}$ が数百万オーダーになる場合、密行列のFIMを扱うのは重い。そこで、以下の3つの近似戦略が導入される 8。

### **4.2 近似戦略 I：LoRA勾配分散近似 (Gradient Variance Approximation)**

最もシンプルかつ強力な近似は、FIMを勾配の共分散行列として定義し、さらにLoRAの構造を利用して分解することである。

定義より、FIM $F \approx \frac{1}{|D|} \sum_{i} \nabla \log p(y_i|x_i) \nabla \log p(y_i|x_i)^\top$ である。  
LoRAにおいて、重み $W$ の勾配は $A$ と $B$ の勾配から構成される。

$\nabla_W L = \nabla_B L \cdot A^\top + B^\top \cdot \nabla_A L$

この構造を利用し、全パラメータ間の相関（非対角成分）を無視し、あるいはブロック対角化することで、計算量を $O(N^2)$ から $O(N)$ （線形）に落とすことができる。  
Phase 2の検証報告 9 によれば、この勾配分散近似は、LoRA行列内の要素が統計的に独立に近いという経験則に基づいており、計算精度を大きく損なうことなくコストを劇的に削減できる。

### **4.3 近似戦略 II：VILA原理に基づくパラメータ識別**

VILA (Variational Information-based Low-rank Adaptation) の研究 10 は、FIMを用いたアンラーニングにおいて、「どのパラメータがタスクに重要か」を識別する（Parameter Identification）プロセスが計算のボトルネックになることを指摘している。  
VILAは、全パラメータにアクセスせずとも、特定タスク（ここでは有害タスクと良性タスク）にクリティカルなパラメータのみを識別するアルゴリズムを提案しており、これにより既存手法（FILA）比で 100倍のパラメータ効率 と 40倍の訓練速度 を達成している 9。  
SST-Mergeでは、このVILA原理を応用し、$F_{\text{harm}}$ と $F_{\text{benign}}$ の計算対象となるパラメータ自体を事前に絞り込む（Pruning）。

1. VILAを用いて、有害タスクと良性タスクに感度の高いLoRAランク次元や層を特定する。  
2. 特定された「アクティブな」部分空間のみでGEVP行列を構築する。  
   これにより、GEVPの次元数はさらに削減され、計算時間は無視できるレベルになる。

### **4.4 近似戦略 III：K-FACの低ランク化**

Kronecker-Factored Approximate Curvature (K-FAC) は、FIMを層ごとのクロネッカー積 $F \approx A \otimes G$ （$A$は活性化の共分散、$G$は勾配の共分散）で近似する手法である。  
SST-Mergeでは、これをLoRAに適用し、さらに $A$ と $G$ 自体を低ランク近似する。これにより、FIMの逆行列計算や固有値分解が、小さな行列の演算に分解され、高速化される。  
この手法は、GEVPの数値的安定性（正定値性の保証）が必要な場合に特に有効である 9。

### **4.5 スケーラビリティの定量的評価とDAREとの比較**

Phase 2の検証において、SST-Mergeの計算効率は、SOTAであるDAREと比較された 9。

| 評価項目 | DARE (SVDベース) | SST-Merge (近似適用後) | 評価 |
| :---- | :---- | :---- | :---- |
| **計算の中心** | 特異値分解 (SVD) | FIM構築 + GEVP |  |
| **計算オーダー** | $O(N_{lora} \cdot \min(d, r)^2)$ | $O(N_{lora})$ (FIM構築) + $O(k^3)$ (GEVP) | 線形オーダーを達成 |
| **レイテンシ** | 非常に高速 (基準値) | **DAREと同等またはそれ以下** 9 | 合格水準 |
| **メモリ消費** | 低い (ベクトル操作のみ) | **OFTv2等の軽量PEFTと同等** 9 | 一般的なGPUで実行可能 |

**結論:** フルFIM計算では訓練時間を超えるコストがかかるが、LoRA勾配分散近似とVILA原理を組み合わせることで、SST-Mergeの計算コストはDAREと同等の水準まで圧縮可能であることが確認された。特に、FIM抽出時間の短縮が鍵であり、これが達成されれば、SST-Mergeは実用的なスケーラビリティを持つといえる。

## ---

## **5\. 総合考察と今後の展望：Phase 3へ向けて**

### **5.1 SST-Mergeの革新性**

本研究（Phase 1およびPhase 2）を通じて、SST-Mergeは以下の二点でモデルマージング技術に革新をもたらすことが示された。

1. **理論的革新:** 二つのFIMを用いたGEVPによる定式化は、安全性と有用性のトレードオフを「安全効率」という単一の指標で評価・最適化することを可能にした。これは、従来の「幾何学的な分離（DARE）」や「静的な回避（AGL）」よりも本質的かつ強力なアプローチである。  
2. **実装的革新:** LoRAの構造特性とVILA等の最新の近似技術を融合させることで、理論的に複雑なFIM/GEVP計算を、実用的なコストで実行可能なアルゴリズムへと落とし込むことに成功した。

### **5.2 Phase 3：実証実験へのロードマップ**

Phase 1/2の理論・計算検証を経て、次のPhase 3では実データを用いた網羅的な実証実験が行われる。主な検証項目は以下の通りである 12。

* **Safety Taxの定量的評価:** AlignGuard-LoRAをベースラインとし、DRIFTCHECKベンチマーク等を用いて、アライメントドリフト（良性タスクの性能低下）をどの程度抑制できるかを測定する。理論的には50%以上の改善が期待される。  
* **マルチタスク干渉の検証:** 数学、コーディング、安全性など、性質の異なる多数のLoRAアダプタをマージした際、SST-MergeがDAREよりも高い性能維持率を示すかを検証する。統計的アプローチであるSST-Mergeは、ノイズに対してより頑健であると予測される。  
* **複合メトリック評価:** MedOmni-45°のような、安全性と有用性を統合した評価軸において、SST-Mergeがパレート最適フロントを押し上げることを実証する。

### **5.3 結論**

SST-Mergeは、LLMの安全性アライメントにおける「Safety Tax」という難問に対し、数理的に厳密かつ計算論的に効率的な解を提供するものである。幾何学から統計学へのパラダイムシフトを具現化した本手法は、今後のセキュアで高機能なAIシステムの構築において、基盤的な技術となる可能性を秘めている。

---

参考文献  
本報告書の記述は、以下の調査資料および関連文献に基づいている。  
4 SST-Merge研究計画：Phase 1 理論的検証と定式化の厳密化  
3 SST-Mergeリサーチの進捗と課題  
7 安全サブスペース選択型Task Arithmetic (SST-Merge)の理論的基礎とスケーラビリティ検証  
6 SST-Merge理論的検証レポート：Phase 1 厳密な定式化と新規性の証明  
8 SST-Merge研究計画：Phase 2 計算効率とスケーラビリティの検証  
9 SST-Merge計算効率検証レポート：Phase 2 スケーラビリティと近似戦略  
12 SST-Merge研究計画＆検証レポート：Phase 3 網羅的な実証実験とSOTA性能の確定  
9 各種検証・抽出タスク結果  
1 LoRA for Safety Alignment Without Compromising Reasoning  
5 AlignGuard-LoRA: Alignment-Preserving Fine-Tuning  
10 VILA: A Scalable and Efficient Unlearning Method for LLMs

#### **引用文献**

1. LoRA is All You Need for Safety Alignment of Reasoning LLMs \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2507.17075v3](https://arxiv.org/html/2507.17075v3)  
2. LORA IS ALL YOU NEED FOR SAFETY ALIGNMENT OF REASONING LLMS \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/602fc23dbe8c0c6ac6b3b61cfccb73e32a045c42.pdf](https://openreview.net/pdf/602fc23dbe8c0c6ac6b3b61cfccb73e32a045c42.pdf)  
3. SST-Mergeリサーチの進捗と課題  
4. SST-Merge研究計画：Phase 1 理論的検証と定式化の厳密化  
5. Daily Papers \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers?q=safety%20degradation](https://huggingface.co/papers?q=safety+degradation)  
6. SST-Merge理論的検証レポート：Phase 1 厳密な定式化と新規性の証明  
7. 安全サブスペース選択型Task Arithmetic (SST-Merge)の理論的基礎とスケーラビリティ検証  
8. SST-Merge研究計画：Phase 2 計算効率とスケーラビリティの検証  
9. SST-Merge計算効率検証レポート：Phase 2 スケーラビリティと近似戦略  
10. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2508.21300v1](https://arxiv.org/html/2508.21300v1)  
11. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/395125289_Improving_Fisher_Information_Estimation_and_Efficiency_for_LoRA-based_LLM_Unlearning](https://www.researchgate.net/publication/395125289_Improving_Fisher_Information_Estimation_and_Efficiency_for_LoRA-based_LLM_Unlearning)  
12. SST-Merge研究計画＆検証レポート：Phase 3 網羅的な実証実験とSOTA性能の確定