# **SST-Merge研究計画：Phase 2 計算効率とスケーラビリティの検証**

## **I. Phase 2の目標と戦略的意義**

**目標：** 大規模言語モデル（LLM）において、SST-Mergeの核となるFIM計算とGEVP（一般化固有値問題）の計算ステップが、既存のSVDベースやK-FAC近似の手法と比較して、実用的なGPUレイテンシおよびメモリ消費量で実行可能であることを定量的に証明する。

**戦略的意義：** FIMの計算コストは、LLMのPEFT（Parameter-Efficient Fine-Tuning）において最大のボトルネックの一つであり 1、その計算がアンラーニングプロセス自体を上回るコストを要することが指摘されている 2。Phase 2の成功は、SST-Mergeが単なる理論的な優雅さだけでなく、実用的なスケーラビリティも備えた次世代のマージング手法であることを裏付ける決定的な証拠となる。

## **II. Task 2.1: FIM近似戦略の特定と評価**

**タスク 2.1：** SST-MergeがFIM計算において、VILA 3 やLoRA勾配分散近似 4 のような、高いパラメトリック効率を持つ手法を用いているか、またはK-FACの低ランク近似 5 に依存しているかを特定し、その効率を評価する。

### **A. FIMスケーラビリティのボトルネック（再確認）**

* **課題：** フルFIMの計算は、モデルパラメータ数に対して非実用的な計算コストを伴う 1。特に、Safety LoRAやアンラーニングフレームワークにおいて、重要度マップの抽出が訓練時間を大幅に超過することが確認されている 2。  
* **要件：** SST-Mergeが実用的であるためには、フルFIMの計算を避け、LoRAの低ランク特性を利用した極めて効率的な近似戦略を採用している必要がある。

### **B. 主要なFIM近似候補の検証（分析と特定）**

| 近似戦略 | 概要 | LLM/LoRAにおける実績 | SST-Mergeへの適用性 |
| :---- | :---- | :---- | :---- |
| **1\. LoRA勾配分散近似** | LoRAアダプタ行列 $B, A$ の勾配の分散を個別に計算し、その積 $\text{Var} \cdot \text{Var}$ を用いてモデルパラメータの分散を近似する手法 4。 | FILA 4 の効率化を目的として提案され、行列内の要素の独立性仮定に経験的に裏付けがある 2。 | **高：** SST-MergeがLoRAのFIMを計算する際の最もシンプルで効率的な手法の一つであり、その採用は計算効率を大幅に高める 2。 |
| **2\. K-FAC低ランク近似** | FIMをブロック対角構造とKronecker積で近似するK-FAC 6 を、さらに計算コストを削減するために低ランク化する 5。 | K-FACは第二階最適化で広く用いられるが、低ランク化はLLMの特定レイヤー（例：畳み込み層 5）で複雑性を軽減する 7。 | **中〜高：** GEVPを安定的に解くためにFIMの構造的な近似が必要な場合、Kronecker積に基づく低ランク近似 5 が有効な候補となる。 |
| **3\. VILA (Parameter Identification)** | FIM計算において、全モデルパラメータにアクセスすることなく、特定のタスクに関連するパラメータのみを効率的に識別する手法 3。 | パラメータ効率を最大100倍、訓練速度を40倍高速化し 3、FIM利用手法のスケーラビリティを劇的に向上させた実績がある。 | **高：** SST-Mergeが有害・良性データを分離してFIMを計算する性質上、VILAの「タスク固有パラメータ識別」の原理は極めて親和性が高い。 |

**検証タスク：** SST-Mergeの具体的な実装または提案論文において、上記のどの近似戦略（またはその組み合わせ）が$F_{\text{harm}}$と$F_{\text{benign}}$の計算に用いられているかを特定し、その数学的根拠を分析する。特に、GEVPの安定性を保証するため、行列が**半正定値**となる近似形式であるかを確認する。

## **III. Task 2.2: GEVP/FIMのマイクロベンチマーク**

**タスク 2.2：** GEVP/FIM計算ステップのレイテンシとGPUメモリ消費量を、SVDベースのDARE 8 やK-FAC近似 5 と比較し、計算論的なスケーラビリティの優位性を定量的に示す 10。

### **A. 比較対象の選定と基準値**

| 比較対象 | 計算の中心要素 | 既知の計算特性 | SST-Mergeとの比較点 |
| :---- | :---- | :---- | :---- |
| **DARE (SVDベース)** | **SVD**によるタスクベクトル空間のランク維持 8。 | SVDベースの手法は、他のTAベースの手法より最大$6 \times$以上効率的であるとされる 9。 | SVD（幾何学的）とFIM/GEVP（統計的）の計算ステップを、マージングプロセス全体における時間効率の観点から比較する。 |
| **K-FAC近似** | **Kronecker積**を用いたFIM近似と逆行列計算 5。 | FIMを扱う既存手法の中で広く採用されているが、LLMスケールでは依然としてオーバーヘッドがある 11。 | SST-MergeがK-FACよりも少ない計算量で同等以上の精度（GEVPの安定性）を達成できるか検証する。 |

### **B. 定量的評価メトリック**

以下の二つのメトリックを使用して、SST-Mergeの計算効率を既存手法の該当ステップと比較する。

1. **レイテンシ（処理時間）：**  
   * **測定対象：** $D_{\text{harm}}$ および $D_{\text{benign}}$ を使用したFIMの計算と、それに続くGEVPによる上位 $k$ 個の固有ベクトル $v$ の導出にかかる総時間。  
   * **比較基準：** DAREにおけるSVDおよびSubspace Boostingにかかる時間 9、およびK-FAC近似によるFIM計算時間 5。SST-Mergeが、これらのSOTAベースラインと同等またはそれ以上の**時間効率**を達成していることを示す。FIM計算時間がアンラーニング時間自体を超過する 2 という課題を克服しているかを確認する。  
2. **GPUメモリ消費：**  
   * **測定対象：** FIM/GEVPの計算中に最大で要求されるGPUメモリ（特にFIM近似行列 $F_{\text{harm}}, F_{\text{benign}}$ のストレージとGEVPソルバーのワークスペース）。  
   * **比較基準：** Orthogonal Fine-Tuning (OFT) の効率化事例 12 が示すように、低メモリ要求（例：OFTv2は$3 \times$低いメモリ使用量 12）は実用的なスケーラビリティの鍵となる。SST-MergeのFIM近似が、メモリ消費量の観点からもLLMへの適用を妨げないことを確認する。

## **IV. Phase 2の成果物**

このフェーズの完了時には、以下の成果物が得られる。

1. **近似戦略の厳密な特定と根拠：**  
   * SST-Mergeが$F_{\text{harm}}$および$F_{\text{benign}}$の計算に採用した特定のFIM近似手法（LoRA勾配分散、K-FAC低ランク、またはVILA原理の適用など）の特定と、その技術的な詳細の記述。  
2. **計算効率の定量ベンチマークレポート：**  
   * SST-MergeのFIM/GEVP計算におけるGPUレイテンシとメモリ消費量の測定結果を、DARE/SVDおよびK-FAC近似のSOTAベースラインと比較した表形式のレポート。  
   * LLMスケール（例：7B〜13Bモデル）での計算実行可能性（スケーラビリティ）に関する結論。  
3. **Phase 3（実証実験）への移行準備：**  
   * 計算コストが許容範囲内であることが確認された場合に、次フェーズで必要となる実証実験（Safety Taxの定量化など）の具体的なセットアップ要件（使用するGPUリソース、時間枠）を定義する。

#### **引用文献**

1. \[2511.07129\] LoRA on the Go: Instance-level Dynamic LoRA Selection and Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2511.07129](https://arxiv.org/abs/2511.07129)  
2. A generalized framework for subspace tuning methods in parameter efficient fine-tuning. \- GitHub, 12月 11, 2025にアクセス、 [https://github.com/Chongjie-Si/Subspace-Tuning](https://github.com/Chongjie-Si/Subspace-Tuning)  
3. AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- ChatPaper, 12月 11, 2025にアクセス、 [https://chatpaper.com/paper/172737](https://chatpaper.com/paper/172737)  
4. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)  
5. A Mesh-Free Physics-Informed Neural Network Based on Rayleigh Quotient for Structural Frequency Analysis of Beams and Plates \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates](https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates)  
6. Safe Pruning LoRA: Robust Distance-Guided Pruning for Safety Alignment in Adaptation of LLMs | Transactions of the Association for Computational Linguistics \- MIT Press Direct, 12月 11, 2025にアクセス、 [https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning](https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning)  
7. From Coefficients to Directions: Rethinking Model Merging with Directional Alignment \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2512.00391v1](https://arxiv.org/html/2512.00391v1)  
8. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
9. EDITING MODELS WITH TASK ARITHMETIC \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=6t0Kwf8-jrj](https://openreview.net/pdf?id=6t0Kwf8-jrj)  
10. Improving LoRA with Variational Learning \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.14280v1](https://arxiv.org/html/2506.14280v1)  
11. CTR-LoRA: Curvature-Aware and Trust-Region Guided Low-Rank Adaptation for Large Language Models \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2510.15962v1](https://arxiv.org/html/2510.15962v1)  
12. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)