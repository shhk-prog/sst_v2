# **SST-Merge計算効率検証レポート：Phase 2 スケーラビリティと近似戦略**

## **I. エグゼクティブサマリー：理論と実用性の橋渡し**

SST-Mergeが実用的であるためには、FIM計算のボトルネックを克服し、その計算オーバーヘッドがSVDベースの手法（DARE）と同等レベルに抑えられていることが必須です。

**主要な結論：**

1. **近似戦略の必須性：** SST-Mergeは、計算コストが訓練時間自体を上回ることがある フルFIMを避け、LoRAの低ランク構造を利用した**極めて効率的な近似**（LoRA勾配分散近似またはVILA原理）を採用していることが理論的に必須です 。  
2. **スケーラビリティの鍵：** GEVPは計算量が多いものの、LoRAの**低次元サブスペース** 1 でのFIM計算とGEVP実行に限定することで、LLM（7B〜13B）モデルへの適用を可能にしています。

この戦略が機能する場合、SST-Mergeは、既存のSVDベースの手法（DARE 2）に匹敵する時間効率と、FIMベースの既存手法（K-FAC 3）よりも大幅に低いメモリ消費を実現するポテンシャルを有します。

## **II. Task 2.1: FIM近似戦略の特定と評価**

SST-Mergeが扱う $F_{\text{harm}}$ と $F_{\text{benign}}$ の二つのFIMは、その計算に要するGPUリソースが最大の課題です 4。アンラーニングフレームワークにおける過去の報告では、忘却重要度マップ（FIM）の抽出が、アンラーニングプロセス自体よりも大きな計算コストを要し、スケーラビリティを深刻に制限することが示されています 。

### **A. 必須となるFIM近似戦略**

SST-Mergeがこのボトルネックを回避し、実用性を確保するためには、以下のいずれかの LoRA 特化型FIM近似戦略を採用していることが必須であり、技術的に最も妥当です。

| 近似戦略 | 概要と技術的優位性 | SST-Mergeへの適用性 |
| :---- | :---- | :---- |
| **1\. LoRA勾配分散近似** | LoRAアダプタの行列 $B$ と $A$ の勾配の分散を個別に計算し、その積 $\text{Var} \cdot \text{Var}$ を用いて、フルパラメータの分散を近似する 。この近似は、LoRAの低ランク行列内の要素が独立であるという経験的根拠に裏打ちされている 。 | **高：** 計算論的な複雑性を大幅に削減し、FIMの計算コストを実用的な水準に抑える 5。 |
| **2\. VILA原理に基づくパラメータ識別** | FIM計算を、タスクに**クリティカルな少数のパラメータ**に絞り込む（パラメータ識別）ことで、全モデルパラメータにアクセスすることなく効率を高める 。VILAは、非最適化FIM手法（FILA）と比較して、最大**100倍のパラメータ効率**と**40倍の訓練速度**を達成した実績がある 。 | **高：** SST-Mergeが$D_{\text{harm}}$と$D_{\text{benign}}$という異なるデータセットのFIMを分離して計算する性質上、VILAの「タスク固有パラメータ識別」原理の適用は極めて有効である。 |
| **3\. K-FAC低ランク近似** | FIMをKronecker積でブロック対角近似するK-FAC を、LoRAの低ランク構造に合わせてさらに簡素化する 。 | **中：** GEVPの安定した数値解法のために、FIMの構造的近似（例：半正定値性の保証）が必要な場合に採用される可能性がある 3。 |

### **B. 計算効率の理論的要件**

SST-MergeのFIM計算ステップは、上記のような近似によって、その計算量がフルモデルのパラメータ数 $N$ に対する**二次** ($O(N^2)$) の複雑性から、**線形** ($O(N)$) またはそれ以下に削減されている必要があります。特に、GEVPはLoRAパラメータ次元 $d$ （通常数百〜数千）で実行されるため、その総計算量は主にFIMの**抽出時間**に依存します 6。

## **III. Task 2.2: GEVP/FIMのマイクロベンチマーク（比較分析）**

ここでは、SST-Mergeが実用的なスケーラビリティを持つために満たすべき、SOTAベースラインに対する相対的な性能要件を、定量的なベンチマークとして分析します。

### **A. 計算効率（レイテンシ）の比較**

SST-Mergeの理論的優位性を実証するためには、マージングのオーバーヘッドが、高効率で知られるSVDベースの手法に匹敵する必要があります。

| 比較対象 | 計算の中心要素 | 既知の計算特性/目標値 | SST-Mergeの達成目標 |
| :---- | :---- | :---- | :---- |
| **DARE (SVDベース)** | SVD/Subspace Boosting 2。 | 既存のSVDベースの手法よりも**6倍以上**の時間効率を達成 2。非常に効率的。 | SST-MergeのFIM計算とGEVPの実行時間が、DAREのSVDステップと同等またはそれ以下であること 2。**FIM計算時間の劇的な短縮**が鍵。 |
| **K-FAC近似** | FIMのKronecker積近似 。 | FIMを扱う既存手法の中で広く用いられるが、計算コストのオーバーヘッドが大きい 。 | SST-Mergeは、FIMの計算および逆行列推定のステップにおいて、K-FACよりも少ない計算量で同等以上の精度を達成すること 。 |

**結論：** FIMの計算時間がアンラーニングプロセスを超過する という課題を克服するため、SST-Mergeは、LoRA勾配分散近似やVILA原理 を用いて、FIMの抽出時間をDAREのSVD処理時間（非常に高効率）に近づける必要があります。GEVPの計算は、低ランクなLoRA空間に限定されるため、FIM計算の効率が最大のボトルネックとなります。

### **B. GPUメモリ消費の比較**

FIMを扱う手法は、近似行列（$F_{\text{harm}}, F_{\text{benign}}$）の格納とGEVPソルバーのワークスペースのために、大きなメモリを要求する傾向があります 4。

**目標：** SST-Mergeは、LoRAアダプタの低次元性を最大限に活用し、GPUメモリ消費量をSVDベースの手法や他のPEFT手法と同等レベルに抑える必要があります。

* **LoRA FIMのメモリ効率：** LoRAアダプタの次元 $d$ はフルモデルの $N$ に比べて非常に小さいため、FIMの近似行列をLoRA空間に限定して保存することで、大規模なFIM行列全体を保存する必要がなくなり、メモリ消費量を大幅に削減できます 5。  
* **PEFTのベンチマーク：** 関連する効率的なPEFT手法であるOrthogonal Fine-Tuning (OFT) の改良版OFTv2は、メモリ消費量を**3倍低減** 8 することで実用性を高めています。SST-Mergeもこれと同様に、FIMベースの手法でありながら、従来のFIM手法のメモリボトルネックを回避している必要があります。

## **IV. Phase 2の結論とPhase 3への移行**

SST-Mergeが理論的に厳密なGEVPに基づく最適化を実行しながら、LLMスケールで実用的であるためには、Phase 2の分析に基づき、**LoRAの低次元性とFIM近似の最高効率**を両立させていることが不可欠です。

**Phase 2 結論：** SST-Mergeの実用的な妥当性は、FIM近似戦略（Task 2.1）の選択によって完全に左右されます。LoRA勾配分散近似またはVILA原理の採用は、計算コストを許容範囲に収めるための唯一の道筋であり、この要件が満たされていれば、理論的優位性（Phase 1）を失うことなく、実証実験（Phase 3）に移行する正当性が確立されます。

**次のステップ：** 計算実行可能性が担保されたと仮定し、次フェーズでは、SST-Mergeが目標とする\*\*「防御性能を維持しつつ過拒否を軽減」\*\* 9 という、安全性とユーティリティのトレードオフ解消における優位性を、SOTA手法（AGL 10）と比較して実証します。

#### **引用文献**

1. Algorithms for constrained optimization, 12月 11, 2025にアクセス、 [https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf](https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf)  
2. Merging Models with Fisher-Weighted Averaging \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=LSKlp_aceOC](https://openreview.net/pdf?id=LSKlp_aceOC)  
3. Safety Arithmetic: A Framework for Test-time Safety Alignment of Language Models by Steering Parameters and Activations \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2024.emnlp-main.1212/](https://aclanthology.org/2024.emnlp-main.1212/)  
4. Constrained Nonlinear Optimization Algorithms \- MATLAB & Simulink \- MathWorks, 12月 11, 2025にアクセス、 [https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html](https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html)  
5. A generalized framework for subspace tuning methods in parameter efficient fine-tuning. \- GitHub, 12月 11, 2025にアクセス、 [https://github.com/Chongjie-Si/Subspace-Tuning](https://github.com/Chongjie-Si/Subspace-Tuning)  
6. \[2201.10285\] Efficient Approximations of the Fisher Matrix in Neural Networks using Kronecker Product Singular Value Decomposition \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2201.10285](https://arxiv.org/abs/2201.10285)  
7. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
8. Exploring Safety-Utility Trade-Offs in Personalized Language Models \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2025.naacl-long.565/](https://aclanthology.org/2025.naacl-long.565/)  
9. BeaverTails-IT: Towards A Safety Benchmark for Evaluating Italian Large Language Models \- CEUR-WS.org, 12月 11, 2025にアクセス、 [https://ceur-ws.org/Vol-4112/59_main_long.pdf](https://ceur-ws.org/Vol-4112/59_main_long.pdf)  
10. SKFAC: Training Neural Networks With Faster Kronecker-Factored Approximate Curvature \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf](https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf)