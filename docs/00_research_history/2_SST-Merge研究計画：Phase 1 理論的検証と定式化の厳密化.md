# **SST-Merge研究計画：Phase 1 理論的検証と定式化の厳密化**

## **I. Phase 1の目標と戦略的意義**

**目標：** SST-Mergeの核となるGeneralized Eigenvalue Problem (GEVP) の定式化が数学的に厳密であり、かつ既存のSOTA手法（AlignGuard-LoRA, DAREなど）と比較して、安全性とユーティリティのトレードオフ解消において理論的に優位性を持つことを証明する。

**戦略的意義：** SST-Mergeの提案は、モデルマージングにおいて\*\*曲率情報（FIM/Hessian）**と**スペクトル解析（GEVP）\*\*を組み合わせた点に最大の新規性がある 1。このフェーズは、この新規なアプローチが単なるパラメータの操作ではなく、最適化の原理に基づいていることを厳密に立証する。

## **II. Task 1.1: GEVPの構成要素と数値解法の厳密化**

**タスク 1.1：** ユーティリティと安全性のFIM（$H_{Util}, F_{Safety}$）の定義、特に$H_{Util}$がHessianかFIMかを確認し、GEVPの解析解または数値解法の安定性を検証する 3。

### **A. 損失関数と曲率行列の形式的な定義**

SST-Mergeは、以下のRayleigh Quotient $R(v)$ の最大化を通じて、最適な安全効率を持つ方向 $v$ を探索する。

$R(v) = \frac{v^\top F_{\text{harm}} v}{v^\top F_{\text{benign}} v}$
この定式化が数学的に厳密であるためには、以下の各行列の定義と性質を明確にする必要がある。

| 行列 | 対応する損失関数 | 必須の性質 | 役割（Rayleigh Quotientにおける位置） |
| :---- | :---- | :---- | :---- |
| $F_{\text{harm}}$ | 有害側の安全ロス ($L_{\text{harm}}$) | 対称性、半正定値性 | **分子（ゲイン）：** 有害ロス改善の度合い 1 |
| $F_{\text{benign}}$ | 良性側の乖離ロス ($L_{\text{benign}}$) | 対称性、正定値性（非特異性） | **分母（コスト）：** 良性ロス悪化（Safety Tax）の度合い |

**実行ステップ：**

1. **$F_{\text{harm}}$ (有害ロス) の確認：**  
   * $L_{\text{harm}}$ の定義は、拒否応答 ($y_{\text{refusal}}$) の対数尤度の負値（最小化）であるため、**Fisher Information Matrix (FIM)**、すなわちスコア関数の分散として定義するのが統計的に最も自然である 。FIMは、尤度関数に関するパラメータの統計的な情報量（曲率/重要度）を定量化する 。  
2. **$F_{\text{benign}}$ (良性ロス) の確認：**  
   * $L_{\text{benign}}$ は、ベースモデル ($\theta_{\text{ft}}$) からの**KL乖離**（良性モデルの知識の保持）として定義されている。KL乖離の二次近似において、Natural Gradientのメトリックとして現れるのはFisher Information Matrixである 。したがって、$F_{\text{benign}}$ も**FIM**として定義され、良性タスクの知識保持に不可欠な方向の「硬さ」を示すことが最も妥当である。  
3. **Hessian vs. FIMの決定：**  
   * FIMを用いることで、$F_{\text{harm}}$ と $F_{\text{benign}}$ が共に半正定値である性質を保証でき、GEVPの数学的要件を満たす 1。これは、安全性とユーティリティの両タスクについて、パラメータ空間における**統計的頑健性**（曲率）を計測することを意味する 4。  
   * *結論：* 両行列をFisher Information Matrixとして厳密に定義し直すことで、理論的基盤を強化する。

### **B. GEVPの数値的実行可能性と安定性の検証**

GEVP ($F_{\text{harm}}v=\lambda F_{\text{benign}}v$) は、大規模行列に対しては計算論的に困難であり、その数値解法は安定性に直結する 5。

**実行ステップ：**

1. **行列構造の確認：** SST-MergeがLoRAパッチ $(\phi)$ のサブスペースで動作するため、問題となる行列 $F_{\text{harm}}$ と $F_{\text{benign}}$ は、フルモデルパラメータのFIMではなく、LoRAパラメータ空間（低次元）におけるFIMの射影であると仮定される 。  
2. **解法の確認：** 固有ベクトル $v$ と固有値 $\lambda$ の上位 $k$ 個を効率的かつ安定的に求めるために、一般の線形ソルバーではなく、**Jacobi–Davidsonタイプ**や**Generalized Krylov Subspaces**に基づく特殊な反復法が必須である 3。  
3. **検証：** SST-Mergeが、このGEVPを解くために、既存の第二階最適化で用いられる効率的なFIM近似手法（例：K-FACの低ランク化 、またはLoRA勾配分散近似 6）と、それに特化したGEVPソルバーを採用していることを確認する 5。これにより、理論の厳密性と計算の安定性を両立させる。

## **III. Task 1.2: 理論的優位性（新規性）の厳密な証明**

**タスク 1.2：** GEVPの解が、既存のSVDベースのDARE 7 やFIM分解ベースのAGL 9 よりも、トレードオフ解決において理論的に優位性を持つことを証明する。

SST-Mergeの優位性は、モデルマージング問題を、**二つの独立したメトリック**（ユーティリティと安全性の曲率）の**比率の最適化**として捉え、その最適な方向をGEVPで解く点にある 1。

### **A. AlignGuard-LoRA (AGL) との差別化：二元最適化の優位性**

| 評価基準 | AlignGuard-LoRA (AGL) | SST-Merge (GEVP) | 理論的優位性 |
| :---- | :---- | :---- | :---- |
| **曲率情報** | *単一の* 安全性FIMのみを使用 9。 | 安全性FIM ($F_{\text{harm}}$) と良性FIM ($F_{\text{benign}}$) の*二つ*を使用。 | **二元的な最適化** 1：一つの方向が安全性とユーティリティに与える影響を同時に考慮できる。 |
| **戦略** | FIM固有値分解に基づく**安全なサブスペースへの静的な射影**（回避戦略）。 | GEVPに基づく**最適なゲイン/コスト比の方向を動的に探索**（最大化戦略）。 | SST-Mergeは、「安全性を維持**しつつ**最大の性能改善を達成する」方向を数学的に厳密に特定できる。 |
| **制約** | 事前に定義された安全方向への正則化。 | 分母 ($F_{\text{benign}}$) が信頼領域（トラストリージョン）の境界として機能する 11。 | GEVPは、安全性（コスト）を一定に保ちながらユーティリティ（ゲイン）を最大化する**制約付き最適化の解**を与える 3。 |

**証明の方向性：** SST-Mergeによるrank-$k$ 射影は、二次近似のもと、良性ロス増加（コスト）を一定範囲に抑えつつ有害ロス改善（ゲイン）を最大化する最適な部分空間制限に近似する 3。これは、AGLの静的分解よりも高度な最適化解である。

### **B. DARE (SVD) との差別化：幾何学から統計的頑健性へ**

SVDベースの手法（TSV-Merge 13、DARE 7）は、LoRA差分ベクトルの\*\*幾何学的配置（スパン、特異値の大きさ）\*\*に焦点を当てる 。

**実行ステップ：**

1. **SVDの限界指摘：** DAREが扱う特異ベクトルは、単なる更新ベクトルの幾何学的方向であり、その方向が**尤度関数の曲率**（統計的頑健性）に与える影響を考慮していない 。  
2. **FIMの優位性の強調：** SST-MergeはFIMを使用することで、勾配のノイズに影響されにくい、**局所的な損失曲面の「硬さ」**（統計的重要性）をパラメータ方向の選択に組み込む 4。  
3. **結論：** SST-Mergeが特定する「安全サブスペース」は、幾何学的な意味だけでなく、**統計的な意味**においても最も頑健かつ効率的である（高い固有値 $\lambda$ は、有害ロス改善に強く効き、良性ロス悪化を招きにくい方向である） 1。

## **IV. Phase 1の成果物**

このフェーズの完了時には、以下の成果物が得られる。

1. **SST-Mergeの理論的定式化シート：**  
   * GEVPにおける $F_{\text{harm}}$ と $F_{\text{benign}}$ がFIMとして定義されることの厳密な数学的記述。  
   * SST-Mergeによる固有値展開が、各成分の「安全効率」（$\lambda$）によって有害/良性ロスに寄与することを解析的に示す 1。  
2. **数値解法要件定義：**  
   * LLMスケールでGEVPを解くために必要なFIM近似戦略（例：K-FAC低ランク近似 ）と、安定したGEVPソルバー（例：Jacobi–Davidson 5）の要件を定義。  
3. **新規性の厳密証明書：**  
   * AGL（単一FIM分解）およびDARE（SVD）と比較し、SST-Mergeが安全性とユーティリティの**二元的な最適解**を導出する点で、理論的に優位性を持つことの証明。

---

この計画に基づき、まずは理論的な厳密性と新規性の証明に焦点を当てて分析を進めます。特に、GEVPの解が**制約付き最適化の最適解**として機能することを明確にすることで、研究の核となる主張を確立します。

#### **引用文献**

1. RAE: A Neural Network Dimensionality Reduction Method for Nearest Neighbors Preservation in Vector Search \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2509.25839v1](https://arxiv.org/html/2509.25839v1)  
2. A Mesh-Free Physics-Informed Neural Network Based on Rayleigh Quotient for Structural Frequency Analysis of Beams and Plates \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates](https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates)  
3. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
4. TIES-MERGING: Resolving Interference When Merging Models \- NIPS papers, 12月 11, 2025にアクセス、 [https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf](https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf)  
5. Parameter Efficient Merging for Multimodal Large Language Models with Complementary Parameter Adaptation \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2502.17159v1](https://arxiv.org/html/2502.17159v1)  
6. Video-SafetyBench: A Benchmark for Safety Evaluation of Video LVLMs \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2505.11842v3](https://arxiv.org/html/2505.11842v3)  
7. \[1503.05671\] Optimizing Neural Networks with Kronecker-factored Approximate Curvature, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1503.05671](https://arxiv.org/abs/1503.05671)  
8. \[2511.07129\] LoRA on the Go: Instance-level Dynamic LoRA Selection and Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2511.07129](https://arxiv.org/abs/2511.07129)  
9. Algorithms for constrained optimization, 12月 11, 2025にアクセス、 [https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf](https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf)  
10. SKFAC: Training Neural Networks With Faster Kronecker-Factored Approximate Curvature \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf](https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf)  
11. Paper page \- AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers/2508.02079](https://huggingface.co/papers/2508.02079)  
12. Task Singular Vectors: Reducing Task Interference in Model Merging \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf](https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf)  
13. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)  
14. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)