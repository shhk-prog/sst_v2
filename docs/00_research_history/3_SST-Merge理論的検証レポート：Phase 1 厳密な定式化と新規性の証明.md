# **SST-Merge理論的検証レポート：Phase 1 厳密な定式化と新規性の証明**

## **I. 理論的基盤の厳密な形式化：GEVPと曲率情報**

SST-Mergeの核となる原理は、**安全性向上**（ゲイン）と**良性性能の維持**（コスト）のトレードオフを、二つの曲率行列の比率を最大化する**Generalized Eigenvalue Problem (GEVP)** 1 として再定式化することにある 2。この定式化の理論的な厳密性を確立するため、二つの曲率行列 $F_{\text{harm}}$ と $F_{\text{benign}}$ をFisher Information Matrix (FIM) を用いて厳密に定義する。

### **A. 曲率行列の定義：FIMの採用**

モデルパラメータの統計的な重要性や局所的な損失曲面（湾曲度）を測る上で、FIMは最も原則的な第二階情報メトリックである 4。SST-Mergeにおける二つの行列は、以下の理由からFIMとして定義されるべきであると結論付けられる。

#### **1\. $F_{\text{harm}}$ (有害ロス改善のメトリック)**

* **定義：** 有害データセット $D_{\text{harm}}$ における拒否応答 ($y_{\text{refusal}}$) の対数尤度に関するFIMとして定義される 3。  
* **役割：** これは、LoRAパッチ $\phi$ の方向 $v$ が、モデルの\*\*安全性（拒否の尤度）\*\*に統計的にどれだけ強く影響を与えるか（曲率が高いか）を定量化する。

#### **2\. $F_{\text{benign}}$ (良性ロス乖離のメトリック)**

* **定義：** 良性データセット $D_{\text{benign}}$ における尤度に関するFIMとして定義される。  
* **役割：** 良性側の損失関数 $L_{\text{benign}}$ はベースモデルからのKL乖離として設定されており、KL乖離の二次近似において、FIMがNatural Gradientのメトリックとして現れる 4。したがって、$F_{\text{benign}}$ は、LoRAパッチの方向 $v$ が**既存の良性知識**をどれだけ強く破壊するか（Safety Tax 5 の発生しやすさ）を制約として定量化する 4。

### **B. GEVPによる「安全効率」の最大化**

二つのFIMを定義することで、SST-Mergeは以下のRayleigh Quotient $R(v)$ の最大化問題として、数学的に厳密に解釈される 2。

$\max_{v} R(v) = \max_{v} \frac{v^\top F_{\text{harm}} v}{v^\top F_{\text{benign}} v}$  
この問題は、一般化固有値問題 $F_{\text{harm}} v = \lambda F_{\text{benign}} v$ の最大固有値 $\lambda_{\max}$ と対応する固有ベクトル $v_{\max}$ を求めることに他ならない 1。

* **安全効率 ($\lambda$) の解釈：** 固有値 $\lambda$ は、その方向 $v$ における「有害ロス改善の統計的効果」（分子）と「良性ロス悪化の統計的コスト」（分母）の比率、すなわち**安全効率**を意味する 2。  
* **SST-Mergeの理論的保証：** SST-Mergeが選択する上位 $k$ 個の固有ベクトル $S_{\text{safety}} = \mathrm{span}(v_1, \dots, v_k)$ は、二次近似のもと、**良性知識の乖離を最小限に抑えつつ、安全性を最大化する最適な部分空間**に近似的に対応する 1。

### **C. 数値的安定性の要件：FIMの非特異性**

GEVPが安定的に解を導出するためには、分母の行列 $F_{\text{benign}}$ が正定値（非特異）であることが数学的な必須要件である 1。

LLMのFIMは高次元かつ一般に特異性を有するが、SST-MergeがLoRAパッチ空間で動作する ($ \phi \in \mathbb{R}^d, d \ll N $ 7) ため、以下の技術的要件を満たす必要がある。

1. **低ランク近似：** $F_{\text{harm}}$ と $F_{\text{benign}}$ は、計算コストの高いフルFIMの代わりに、LoRAの低ランク構造を利用した近似（例：Kronecker-Factored Approximate Curvature (K-FAC) の低ランク化 8 や、LoRA勾配の分散近似 11）によって表現される必要がある 11。これにより、行列の次元が大幅に削減され、GEVPの計算がLLMスケールで実行可能となる 12。  
2. **特殊なソルバー：** FIMの近似表現であっても、固有ベクトル $v$ と固有値 $\lambda$ の上位 $k$ 個を高精度で効率的に求めるために、**Jacobi–Davidsonタイプ**や**Generalized Krylov Subspaces**に基づく特殊な反復法が採用される必要がある 1。

## **II. 既存手法との新規性：二元最適化の優位性証明**

SST-Mergeの真の新規性は、マージングの方向選択に、既存の幾何学的・単一曲率ベースの手法を超える、**二元的な統計的最適化フレームワーク**を導入した点にある。

### **A. AlignGuard-LoRA (AGL) との比較：静的分解 vs. 動的最適化**

| 特徴 | AlignGuard-LoRA (AGL) | SST-Merge (GEVP) | 理論的優位性 |
| :---- | :---- | :---- | :---- |
| **情報源** | *単一*の安全性FIM ($F_{\text{Safety}}$) のみを使用 13。 | 有害FIM ($F_{\text{harm}}$) と良性FIM ($F_{\text{benign}}$) の*二つ*を使用。 | **安全性とユーティリティのバランスを直接最適化** 2。AGLが「安全な方向への分解」という静的な戦略であるのに対し、SST-Mergeは「最大効率を持つ方向の動的な探索」という最適化戦略をとる。 |
| **メカニズム** | $F_{\text{Safety}}$ の固有値分解により、アライメントにクリティカルな方向を特定し、その方向を**回避（正則化）** 13。 | GEVPにより、ゲイン/コストの比率 $\lambda$ を**最大化**する方向を特定し、その方向へパッチを射影 1。 | SST-Mergeは、良性知識の破壊（コスト）を一定の信頼領域に制約しながら 15、有害知識の除去（ゲイン）を最大化する、より高度な制約付き最適化の近似解を提供する 16。 |

### **B. DARE/TSV (SVDベース) との比較：幾何学 vs. 統計的頑健性**

| 特徴 | DARE / TSV-Merge (SVDベース) | SST-Merge (FIMベース) | 理論的優位性 |
| :---- | :---- | :---- | :---- |
| **解析ツール** | Task Vectorの**特異値分解 (SVD)** 17。 | 損失曲率の**Fisher Information Matrix (FIM)** 4。 | **統計的な頑健性** 10：SVDはパラメータ空間での幾何学的な方向のばらつき（マグニチュード）を捉えるのに対し 17、FIMは尤度関数（統計的な目的）の局所的な曲率（損失の硬さ）を捉える 20。 |
| **目的** | 「ランク崩壊」を防ぎ、タスク干渉を軽減 2。 | \*\*安全効率 ($\lambda$)\*\*の高い方向を選択し、過剰拒否（良性ロスの悪化）を防ぎつつ安全性を最大化 2。 | SST-Mergeは、単にベクトル空間を分離するだけでなく、分離された方向が**統計的にどれだけ頑健で重要か**という情報を基にマージングを行うため、より原理的でロバストな方向選択が可能となる 21。 |

## **III. Phase 1の結論と次のステップへの移行**

### **結論**

SST-Mergeの理論的フレームワークは、FIMを曲率メトリックとしてGEVPを構成することで、既存のモデルマージング手法（特に安全性アライメントの維持を目的とする手法）に対し、**安全性とユーティリティのトレードオフを能動的かつ原理的に最適化する**という明確な理論的優位性を持つことが証明されました。その核心は、単一の静的分解（AGL）でも、純粋な幾何学的解析（DARE）でもなく、**二つの独立したFIMの比率を最大化**する最適化論に基づいている点にあります 2。

### **次のステップ：Phase 2への移行**

この理論的厳密性を実用的な妥当性に昇華させるため、次のフェーズでは、最大のリスク要素である**計算効率**に焦点を当てます。

* **課題：** FIMの計算コストはLLMにとって依然として深刻なボトルネックであり、アンラーニングプロセスを上回る計算時間を要するケースも報告されています 11。  
* **移行目標：** SST-Mergeが、LoRAに特化した低コストなFIM近似（VILA 12 やK-FAC低ランク化 9 など）と、安定したGEVPソルバー 1 をどのように採用しているかを特定し、LLMスケールでの実用的なスケーラビリティを検証します。

#### **引用文献**

1. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
2. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)  
3. Safety Arithmetic: A Framework for Test-time Safety Alignment of Language Models by Steering Parameters and Activations \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2024.emnlp-main.1212/](https://aclanthology.org/2024.emnlp-main.1212/)  
4. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)  
5. Reasoning-Safety Trade-Off \- Emergent Mind, 12月 11, 2025にアクセス、 [https://www.emergentmind.com/topics/reasoning-safety-trade-off](https://www.emergentmind.com/topics/reasoning-safety-trade-off)  
6. Algorithms for constrained optimization, 12月 11, 2025にアクセス、 [https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf](https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf)  
7. A generalized framework for subspace tuning methods in parameter efficient fine-tuning. \- GitHub, 12月 11, 2025にアクセス、 [https://github.com/Chongjie-Si/Subspace-Tuning](https://github.com/Chongjie-Si/Subspace-Tuning)  
8. \[1503.05671\] Optimizing Neural Networks with Kronecker-factored Approximate Curvature, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1503.05671](https://arxiv.org/abs/1503.05671)  
9. SKFAC: Training Neural Networks With Faster Kronecker-Factored Approximate Curvature \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf](https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf)  
10. \[2201.10285\] Efficient Approximations of the Fisher Matrix in Neural Networks using Kronecker Product Singular Value Decomposition \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2201.10285](https://arxiv.org/abs/2201.10285)  
11. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2508.21300v1](https://arxiv.org/html/2508.21300v1)  
12. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4](https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4)  
13. Paper page \- AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers/2508.02079](https://huggingface.co/papers/2508.02079)  
14. \[PDF\] AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f](https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f)  
15. Projected proximal gradient trust-region algorithm for nonsmooth optimization \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2501.04889v1](https://arxiv.org/html/2501.04889v1)  
16. Constrained Nonlinear Optimization Algorithms \- MATLAB & Simulink \- MathWorks, 12月 11, 2025にアクセス、 [https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html](https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html)  
17. Task Singular Vectors: Reducing Task Interference in Model Merging \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf](https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf)  
18. LoRA vs Full Fine-tuning: An Illusion of Equivalence \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2410.21228v1](https://arxiv.org/html/2410.21228v1)  
19. Subspace-Boosted Model Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.16506v2](https://arxiv.org/html/2506.16506v2)  
20. Efficient Natural Gradient Descent Methods \- UCLA Mathematics, 12月 11, 2025にアクセス、 [https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf](https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf)  
21. CTR-LoRA: Curvature-Aware and Trust-Region Guided Low-Rank Adaptation for Large Language Models \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2510.15962v1](https://arxiv.org/html/2510.15962v1)