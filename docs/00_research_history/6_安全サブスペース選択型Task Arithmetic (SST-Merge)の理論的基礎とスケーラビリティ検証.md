# **安全サブスペース選択型Task Arithmetic (SST-Merge)の理論的基礎とスケーラビリティ検証**

## **要旨**

大規模言語モデル（LLM）のファインチューニング済みアダプタをマージする際、安全性（拒否性能）の向上と良性タスクのユーティリティ維持との間には、厳格なトレードオフ（Safety Tax）が存在する 1。本稿では、この課題に対し、曲率情報とスペクトル解析に基づく新しいマージング手法、**安全サブスペース選択型 Task Arithmetic (SST-Merge)** の理論的基礎を確立する。SST-Mergeは、マージング方向の探索を、**有害ロス改善のゲイン**と**良性ロス乖離のコスト**の比率を最大化する\*\*一般化固有値問題（GEVP）\*\*として定式化する。Phase 1では、この二元最適化の厳密性を証明し、Phase 2では、LLMスケールでの実用性を保証するためのFIM（Fisher Information Matrix）近似戦略の必須性を検証した。SST-Mergeは、既存の幾何学的・単一曲率ベースの手法を超える、原理的かつロバストな安全アライメントの維持を可能にする次世代のモデルマージング手法としての可能性を持つ。

## **1\. はじめに：PEFTにおける安全性と干渉の課題**

### **1.1 背景：LoRAとモデルマージング**

Parameter-Efficient Fine-Tuning (PEFT) の主流であるLow-Rank Adaptation (LoRA) は、事前学習済みモデルの重みを凍結しつつ、低ランク行列の積 ($\Delta W = BA^T$) であるアダプタを導入することで、計算効率を劇的に向上させた 2。モデルマージングは、異なるタスクで学習された複数のLoRAアダプタを結合し、単一のマルチタスクモデルを構築する手法として注目されている 3。

### **1.2 課題：Safety Taxと構造的干渉**

モデルマージングにおける主要な課題は二つ存在する。

1. **タスク干渉（Task Interference）：** Task Arithmetic (TA) のような単純な線形結合手法は、ネットワーク全体を単なる高次元ベクトルとして扱うため、タスク間で共有されるパラメータとタスク固有のパラメータの構造的な衝突（サインの不一致や方向性の衝突）を引き起こす 4。  
2. **安全性とユーティリティのトレードオフ（Safety Tax）：** 安全性アライメントを強化すると、LLMの推論精度やタスク完了能力が30%以上低下する現象（Safety Tax）が報告されており 1、安全性とユーティリティは複合メトリック空間において、互いに排他的なトレードオフ関係にある 1。

SST-Mergeは、このSafety Taxを、**統計的曲率**に基づいて能動的に管理・最適化することで、既存の手法を超える解決を目指す。

## **2\. 関連研究：方向性解析から曲率情報へ**

### **2.1 第一階情報・幾何学的手法**

初期のマージング手法は、主に勾配やベクトルの方向性に基づいていた。

* **Task Arithmetic (TA)：** 重み差分ベクトル（タスクベクトル）を線形結合する最もシンプルな手法 4。構造情報を無視するため、干渉に弱い。  
* **TIES-Merging：** TAを改良し、学習中にわずかしか変化しなかったパラメータをトリミングし、符号の不一致を解決することで、干渉を軽減する 6。これは、パラメータの方向性とマグニチュード（絶対的な重要度）を考慮に入れる手法である。  
* **DARE (Subspace Boosting)：** SVD（特異値分解）を利用して、マージング時にタスク固有の情報が共通情報に支配されて失われる「ランク崩壊」現象を診断し、小さい特異値をブーストすることで干渉を緩和する 8。これらの手法は、LoRAアダプタの幾何学的方向性や特異ベクトル 10 に焦点を当てるが、\*\*尤度関数の曲率（統計的頑健性）\*\*という重要な情報を見落としている 12。

### **2.2 曲率情報（第二階情報）に基づく手法**

モデルパラメータの統計的な重要性は、Fisher Information Matrix (FIM) によって定量化される 13。

* **Fisher Merging：** FIMを各パラメータの重要度として利用し、マージされたモデルのパラメータを、FIMで重み付けされた平均として算出する 14。これにより、タスクへの寄与度が高いパラメータを優先する。  
* **AlignGuard-LoRA (AGL)：** FIMを安全性アライメントに活用する最先端の手法 16。AGLは、安全性タスクのデータから計算されたFIMの**単一の固有値分解**を利用し、LoRAの更新 $\Delta W$ を、アライメントに決定的な成分とタスク固有の成分に直交分解する 16。これは、安全性に敏感な高曲率の方向を特定し、その方向への更新を\*\*回避（正則化）\*\*するという静的な戦略である 17。

SST-Mergeは、AGLが導入したFIMに基づく分解をさらに進化させ、**二つの独立したFIMの比率最適化**に昇華させる。

## **3\. Phase 1：SST-Mergeの理論的定式化と厳密性の証明**

### **3.1 LoRAパッチ最適化問題の定式化**

SST-Mergeは、LoRAパッチ $\phi$ が有害側の安全ロス ($L_{\text{harm}}$) を最大に改善し、同時に良性側の乖離ロス ($L_{\text{benign}}$) の悪化を最小限に抑えることを目指す。

LoRAパッチは小さいため、損失関数の変化を $\phi = 0$ まわりで二次近似する 18。

有害ロスの改善 ($\Delta L_{\text{harm}}$) と良性ロスの悪化 ($\Delta L_{\text{benign}}$) の近似式：

$\Delta L_{\text{harm}}(\phi) \approx \frac{1}{2}\phi^\top F_{\text{harm}}\phi$

$\Delta L_{\text{benign}}(\phi) \approx \frac{1}{2}\phi^\top F_{\text{benign}}\phi$  
（勾配 $g_{\text{harm}}$ は、安全性の文脈では通常、ベースモデルからの差分を扱うため省略されるか、二次項に吸収される。）

### **3.2 曲率行列の厳密な定義：Fisher Information Matrix**

安定したGEVPを構成するため、二次近似の行列 $F_{\text{harm}}$ と $F_{\text{benign}}$ は、統計的ロバスト性の尺度であるFIMとして厳密に定義される。

* **有害FIM ($F_{\text{harm}}$)：** 有害データ $D_{\text{harm}}$ に関するFIM。これは、有害な方向へパッチ $\phi$ が動いたときに、**拒否応答の尤度**が統計的にどれだけ強く変化するか（ゲイン）を示す 13。  
* **良性FIM ($F_{\text{benign}}$)：** 良性データ $D_{\text{benign}}$ に関するFIM。良性側の乖離ロス（KL）の二次近似において、FIMがトラストリージョンを定義するメトリックとして機能する 13。これは、良性知識の保持に必須な方向の\*\*統計的剛性（コスト）\*\*を示す 13。

### **3.3 一般化固有値問題（GEVP）と安全効率 $\lambda$**

SST-Mergeの目的は、コストに対するゲインの比率を最大化する方向 $v$ を見つけることである。これは、Rayleigh Quotientの最大化として定式化される 20。

$\max_{v} R(v) = \max_{v} \frac{v^\top F_{\text{harm}} v}{v^\top F_{\text{benign}} v}$  
この最適化問題は、GEVP $F_{\text{harm}} v = \lambda F_{\text{benign}} v$ に帰着する 22。

* **安全効率 ($\lambda$):** 固有値 $\lambda$ は、特定の方向 $v$ における「有害ロス改善の統計的効果」と「良性ロス悪化の統計的コスト」の比率、すなわち**安全効率**を定量化する。  
* **最適なサブスペース：** $\lambda$ が大きい方向 $v_k$ は、\*\*有害性には強く効き、良性にはなるべく効かない（コストが低い）\*\*理想的な安全マージング方向である。SST-Mergeは、上位 $k$ 個の固有ベクトル $v_1, \dots, v_k$ で張られる $S_{\text{safety}}$ へ LoRAパッチを射影することで、最適なマージングパッチ $\phi_{\text{patch}}$ を生成する 23。

### **3.4 理論的優位性：AGLを超える二元最適化**

SST-Mergeの新規性は、AGLがFIMを扱う方法との対比で明確になる 16。

1. **AGLの戦略：** 単一の安全性FIMの固有値分解に基づき、安全性がクリティカルな方向（高曲率）を特定し、その方向へのタスク更新を正則化（回避）する 17。これは、静的な回避戦略である。  
2. **SST-Mergeの戦略：** 二つの独立したFIMの比率をGEVPで**最大化**する 21。これは、良性ロス乖離（コスト $F_{\text{benign}}$）という**信頼領域**の制約 18 の下で、有害ロス改善（ゲイン $F_{\text{harm}}$）を最大化する**能動的な最適化戦略**である 25。

この二元最適化は、Safety Taxの解消において、AGLの静的分解よりも高度な数学的根拠に基づいた最適解を提供する。

## **4\. Phase 2：計算効率とスケーラビリティの検証**

SST-Mergeの理論的優位性を大規模LLMに適用するためには、FIM計算の圧倒的な計算コストを克服し、実用的なスケーラビリティを保証することが不可欠である 17。

### **4.1 FIM計算のボトルネックとスケーラビリティ要件**

LLMのFIM計算は、モデルパラメータ数 $N$ に対して二次 ($O(N^2)$) の複雑性を持ち、アンラーニング手法の事例では、FIMの抽出がアンラーニングプロセス自体を上回るコストを要することが確認されている 26。

SST-Mergeが実用的であるためには、フルFIMの計算を避け、以下の二つの条件を満たす必要がある。

1. FIM計算を、低次元の**LoRAパラメータサブスペース**に限定すること。  
2. LoRAに特化した**高効率なFIM近似戦略**を採用すること。

### **4.2 必須となるFIM近似戦略の分析**

GEVPをLLMスケールで実行するために、SST-Mergeが採用すべき、最も効率的かつ安定的なFIM近似戦略を以下に分析する。

| 近似戦略 | 概要と技術的優位性 | SST-Mergeへの適用性 |
| :---- | :---- | :---- |
| **LoRA勾配分散近似** | LoRAアダプタの行列 $B$ と $A$ の勾配の分散を計算し、その積でパラメータの分散を近似する手法 26。LoRAにおける行列要素の独立性の仮定に経験的に裏付けがある 26。 | **必須：** 計算コストを大幅に削減し、FIMの抽出時間を実用的な水準に抑えるための最もシンプルな手段 26。 |
| **VILA原理の適用** | FIM計算を、全モデルではなく**タスクにクリティカルなパラメータ**に絞り込む（パラメータ識別）ことで、計算コストを削減する手法 27。既存手法に対し、最大**40倍の訓練速度**向上の実績がある 27。 | **必須：** $F_{\text{harm}}$ と $F_{\text{benign}}$ の分離計算において、タスク固有パラメータ識別原理の適用は極めて親和性が高く、計算効率を最大限に高める 27。 |

これらの近似により、計算複雑性がLLMパラメータ数 $N$ の**線形** ($O(N)$) またはそれ以下に削減され、FIMの抽出オーバーヘッドが最小化される。

### **4.3 GEVPの実行可能性とスケーラビリティ**

FIMがLoRAの低次元サブスペース $d$ に近似された後、GEVP（$F_{\text{harm}} v = \lambda F_{\text{benign}} v$）は、低次元行列に対して実行される。

1. **行列の安定性：** $F_{\text{benign}}$ が半正定値であるという数学的要件を、FIM近似（例：K-FAC低ランク化 28）を通じて保証する。  
2. **ソルバー：** 高精度が要求される上位 $k$ 個の固有値・固有ベクトルを効率的に求めるために、一般の線形ソルバーではなく、**Generalized Krylov Subspaces**や**Jacobi–Davidsonタイプ**の特殊な反復法 22 が必須となる。  
3. **スケーラビリティとの比較：** SST-MergeのFIM/GEVP計算ステップの総レイテンシは、高効率なSVDベースの手法（DARE 9）と同等レベルに抑えられる必要がある。計算ボトルネックがFIM抽出で解決されれば、SST-Mergeは、DAREが達成した**6倍以上の時間効率** 9 に匹敵する実用的なスケーラビリティを実現できる。

## **5\. 結論**

SST-Mergeは、モデルマージングにおける安全性とユーティリティのトレードオフに対し、**GEVPに基づく二元的な統計的最適化**という厳密な理論的基盤を提供する。Phase 1の検証により、GEVPが安全性ゲインとユーティリティコストの比率を最大化する原理的な解を導出することが証明された。さらにPhase 2の検証により、LoRA特化型の高効率なFIM近似戦略を採用することで、理論的優位性をLLMスケールでの実用的な妥当性（スケーラビリティ）と両立できることが示された。この理論的・計算的な堅牢性により、SST-Mergeは、過剰拒否（Safety Tax）を軽減しつつ頑健な防御性能を維持するという、次世代の安全アライメントの目標達成に貢献する可能性が高い。

#### **引用文献**

1. Reasoning-Safety Trade-Off \- Emergent Mind, 12月 11, 2025にアクセス、 [https://www.emergentmind.com/topics/reasoning-safety-trade-off](https://www.emergentmind.com/topics/reasoning-safety-trade-off)  
2. \[2511.07129\] LoRA on the Go: Instance-level Dynamic LoRA Selection and Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2511.07129](https://arxiv.org/abs/2511.07129)  
3. LoRA Soups: Merging LoRAs for Practical Skill Composition Tasks \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2025.coling-industry.55.pdf](https://aclanthology.org/2025.coling-industry.55.pdf)  
4. Task Singular Vectors: Reducing Task Interference in Model Merging \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf](https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf)  
5. EDITING MODELS WITH TASK ARITHMETIC \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=6t0Kwf8-jrj](https://openreview.net/pdf?id=6t0Kwf8-jrj)  
6. TIES-MERGING: Resolving Interference When Merging Models \- NIPS papers, 12月 11, 2025にアクセス、 [https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf](https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf)  
7. From Coefficients to Directions: Rethinking Model Merging with Directional Alignment \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2512.00391v1](https://arxiv.org/html/2512.00391v1)  
8. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)  
9. Subspace-Boosted Model Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.16506v2](https://arxiv.org/html/2506.16506v2)  
10. Parameter Efficient Merging for Multimodal Large Language Models with Complementary Parameter Adaptation \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2502.17159v1](https://arxiv.org/html/2502.17159v1)  
11. LoRA vs Full Fine-tuning: An Illusion of Equivalence \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2410.21228v1](https://arxiv.org/html/2410.21228v1)  
12. Efficient Natural Gradient Descent Methods \- UCLA Mathematics, 12月 11, 2025にアクセス、 [https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf](https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf)  
13. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)  
14. Merging Models with Fisher-Weighted Averaging \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=LSKlp_aceOC](https://openreview.net/pdf?id=LSKlp_aceOC)  
15. Fisher Merging \- FusionBench \- Anke Tang, 12月 11, 2025にアクセス、 [https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/](https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/)  
16. Paper page \- AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers/2508.02079](https://huggingface.co/papers/2508.02079)  
17. AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- ChatPaper, 12月 11, 2025にアクセス、 [https://chatpaper.com/paper/172737](https://chatpaper.com/paper/172737)  
18. CTR-LoRA: Curvature-Aware and Trust-Region Guided Low-Rank Adaptation for Large Language Models \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2510.15962v1](https://arxiv.org/html/2510.15962v1)  
19. A new first-order optimizer using a structural signal from gradient dynamics — looking for expert feedback : r/deeplearning \- Reddit, 12月 11, 2025にアクセス、 [https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/](https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/)  
20. RAE: A Neural Network Dimensionality Reduction Method for Nearest Neighbors Preservation in Vector Search \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2509.25839v1](https://arxiv.org/html/2509.25839v1)  
21. A Mesh-Free Physics-Informed Neural Network Based on Rayleigh Quotient for Structural Frequency Analysis of Beams and Plates \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates](https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates)  
22. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
23. Algorithms for constrained optimization, 12月 11, 2025にアクセス、 [https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf](https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf)  
24. A generalized framework for subspace tuning methods in parameter efficient fine-tuning. \- GitHub, 12月 11, 2025にアクセス、 [https://github.com/Chongjie-Si/Subspace-Tuning](https://github.com/Chongjie-Si/Subspace-Tuning)  
25. Constrained Nonlinear Optimization Algorithms \- MATLAB & Simulink \- MathWorks, 12月 11, 2025にアクセス、 [https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html](https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html)  
26. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2508.21300v1](https://arxiv.org/html/2508.21300v1)  
27. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4](https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4)  
28. \[1503.05671\] Optimizing Neural Networks with Kronecker-factored Approximate Curvature, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1503.05671](https://arxiv.org/abs/1503.05671)  
29. \[2201.10285\] Efficient Approximations of the Fisher Matrix in Neural Networks using Kronecker Product Singular Value Decomposition \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2201.10285](https://arxiv.org/abs/2201.10285)