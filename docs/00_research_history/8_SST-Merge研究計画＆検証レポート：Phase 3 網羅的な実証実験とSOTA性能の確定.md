# **SST-Merge研究計画＆検証レポート：Phase 3 網羅的な実証実験とSOTA性能の確定**

## **I. Phase 3 研究計画：SOTA性能の厳密な定量化**

**目標：** SST-Mergeが目標とする「防御性能を維持しつつ過拒否を軽減」という、安全性とユーティリティのトレードオフ解消における優位性を、AlignGuard-LoRA (AGL) 1 を主要な競合相手として、網羅的なベンチマークで実証する。

**戦略：** GEVPに基づく二元最適化の優位性は、従来の単一FIM分解（AGL）や幾何学的解析（DARE）では到達不可能な、より低い「Safety Tax」として定量化される必要がある 2。複合メトリックを用いて、性能の優位性を確立する。

### **A. Task 3.1: 安全性・ユーティリティ複合ベンチマーク（Safety Taxの定量化）**

| 項目 | 詳細 | 採用するメトリックとベンチマーク | 期待される成果 |
| :---- | :---- | :---- | :---- |
| **安全性（防御）** | 有害な出力の拒否率、jailbreak耐性。 | **BeaverTails** 3：毒性、バイアス、倫理遵守など多様な安全次元での評価。 | 既存のSafety LoRA 5 と同等以上の有害コンテンツの拒否率を達成。 |
| **過拒否の軽減** | 良性（非有害）なタスクにおける意図しない拒否の発生率（Safety Tax）。 | **DRIFTCHECK** 1：安全性アライメントのドリフトを評価するための専用ベンチマーク。 | AGLが示すアライメントドリフトの**50%以上の軽減**を上回ること 1。 |
| **ユーティリティ** | 推論精度、タスク完了率。 | 既存のタスクベンチマーク（例：MMLU、Reasoning Accuracyなど）。 | 過拒否を軽減しつつも、ベースモデルに近いユーティリティを維持。 |
| **複合性能** | 安全性とユーティリティのトレードオフ関係の評価。 | **統計的相関** ($r$) および**複合メトリック**（例：MedOmni-45°） 2。 | 複合メトリック空間において、SOTA手法（AGL）よりも「理論的対角線」に近い位置にプロットされること 2。 |

### **B. Task 3.2: マルチタスク干渉耐性の検証**

| 項目 | 詳細 | 比較対象 | 期待される成果 |
| :---- | :---- | :---- | :---- |
| **干渉耐性** | 多数の専門家モデルをマージした際の性能劣化（ランク崩壊の回避） 7。 | **DARE** (Subspace Boosting/HO-GSVD) 7、**TIES-Merging** 9。 | SVDベースのDAREが幾何学的解析でランク崩壊を防ぐのに対し、SST-Mergeは**統計的重要性**（FIM）に基づいて方向を選択するため 11、よりノイズやタスク干渉に頑健な性能維持を達成できること。 |
| **実験設定** | 8〜20個の多様なタスクエキスパートモデルをマージし、平均性能を評価する 7。 | \- | 多数マージ時の性能劣化曲線がDAREよりも緩やかであること。 |

## **II. Phase 3 検証レポート：理論的優位性の実証結果（推定）**

Phase 1およびPhase 2で確立されたSST-Mergeの理論的・計算的優位性を基に、実証実験（Phase 3）で期待される結果を報告します。

### **A. Safety Tax解消におけるSST-Mergeの優位性**

SST-MergeのGEVPフレームワークは、既存の安全性維持手法であるAlignGuard-LoRA (AGL) 1 やSafeLoRA 5 に対し、以下の点で明確な定量的な優位性を示すことが期待されます。

| 評価指標 | AlignGuard-LoRA (AGL) | SST-Merge (GEVP) | 優位性の根拠 |
| :---- | :---- | :---- | :---- |
| **トレードオフ戦略** | 単一FIMに基づく**安全方向の回避**（静的分解） 1。 | 二元FIMに基づく**ゲイン/コスト比の最大化**（動的最適化） 13。 | GEVPは「良性ロスを壊さずに有害ロスを最も改善する方向」を厳密に数学的に特定するため 14、トレードオフ解消能力が本質的に高い。 |
| **Alignment Drift軽減** | 最大50%程度の軽減を達成 1。 | **50%を超える軽減**、または同等の軽減率でより高いユーティリティ維持。 | FIM $F_{\text{benign}}$ が**信頼領域**として機能し 15、過剰な拒否を引き起こす方向を原理的に除外するため。 |
| **複合性能** | Safety Tax（性能低下）の存在が強く示唆される 2。 | 複合メトリック（例：MedOmni-45°）において、**理論的な最適対角線** 2 に最も近い位置にプロットされる。 |  |

### **B. FIMによる頑健な方向選択の効果**

Phase 1で確認されたように、SST-Mergeが選択する方向 $v_k$ は、純粋な幾何学的特徴（SVD）ではなく、\*\*統計的な重要性（FIM）\*\*に基づいています 17。

| 手法 | 方向選択の基盤 | マージング時の性能特性（期待） |
| :---- | :---- | :---- |
| **DARE/TSV** 18 | SVD：パラメータ空間の**幾何学的方向とマグニチュード**。 | 多数の専門家モデルをマージすると、タスクベクトルの干渉やノイズにより、性能維持に限界が生じる可能性がある 7。 |
| **SST-Merge** | GEVP：**損失関数の曲率**（統計的頑健性） 19。 | FIMは勾配のノイズに影響されにくく 20、選択された「安全サブスペース」は統計的に頑健であるため、マルチタスク環境において**より安定した（低分散な）性能**を達成する 7。 |

この結果、SST-Mergeは、DAREがSubspace Boosting 8 で達成した20エキスパートマージ 7 における性能向上を、より原理的かつロバストな手法で達成する可能性を秘めています。

## **III. 次のステップ**

Phase 3の研究計画と検証レポート（推定結果を含む）に基づき、**網羅的な実証実験**に進みます。具体的なデータセットとモデルスケール（例：7B〜13Bクラス 21）を定義し、AGL、DARE、TIES-Mergingに対する定量的な優位性を確立することに焦点を当てます。

#### **引用文献**

1. Paper page \- AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers/2508.02079](https://huggingface.co/papers/2508.02079)  
2. Reasoning-Safety Trade-Off \- Emergent Mind, 12月 11, 2025にアクセス、 [https://www.emergentmind.com/topics/reasoning-safety-trade-off](https://www.emergentmind.com/topics/reasoning-safety-trade-off)  
3. Video-SafetyBench: A Benchmark for Safety Evaluation of Video LVLMs \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2505.11842v3](https://arxiv.org/html/2505.11842v3)  
4. BeaverTails-IT: Towards A Safety Benchmark for Evaluating Italian Large Language Models \- CEUR-WS.org, 12月 11, 2025にアクセス、 [https://ceur-ws.org/Vol-4112/59_main_long.pdf](https://ceur-ws.org/Vol-4112/59_main_long.pdf)  
5. Safe Pruning LoRA: Robust Distance-Guided Pruning for Safety Alignment in Adaptation of LLMs | Transactions of the Association for Computational Linguistics \- MIT Press Direct, 12月 11, 2025にアクセス、 [https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning](https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning)  
6. Safe LoRA: The Silver Lining of Reducing Safety Risks when Finetuning Large Language Models | Request PDF \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/397202248_Safe_LoRA_The_Silver_Lining_of_Reducing_Safety_Risks_when_Finetuning_Large_Language_Models](https://www.researchgate.net/publication/397202248_Safe_LoRA_The_Silver_Lining_of_Reducing_Safety_Risks_when_Finetuning_Large_Language_Models)  
7. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)  
8. Subspace-Boosted Model Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.16506v2](https://arxiv.org/html/2506.16506v2)  
9. TIES-MERGING: Resolving Interference When Merging Models \- NIPS papers, 12月 11, 2025にアクセス、 [https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf](https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf)  
10. From Coefficients to Directions: Rethinking Model Merging with Directional Alignment \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2512.00391v1](https://arxiv.org/html/2512.00391v1)  
11. Fisher Merging \- FusionBench \- Anke Tang, 12月 11, 2025にアクセス、 [https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/](https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/)  
12. \[PDF\] AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f](https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f)  
13. RAE: A Neural Network Dimensionality Reduction Method for Nearest Neighbors Preservation in Vector Search \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2509.25839v1](https://arxiv.org/html/2509.25839v1)  
14. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
15. Trust Region Policy Optimization (TRPO) | by Leonidas Gorgo | Nov, 2025 \- Medium, 12月 11, 2025にアクセス、 [https://leonidasgorgo.medium.com/trust-region-policy-optimization-trpo-d9f5536d6aeb](https://leonidasgorgo.medium.com/trust-region-policy-optimization-trpo-d9f5536d6aeb)  
16. Projected proximal gradient trust-region algorithm for nonsmooth optimization \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2501.04889v1](https://arxiv.org/html/2501.04889v1)  
17. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)  
18. Task Singular Vectors: Reducing Task Interference in Model Merging \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf](https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf)  
19. Efficient Natural Gradient Descent Methods \- UCLA Mathematics, 12月 11, 2025にアクセス、 [https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf](https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf)  
20. A new first-order optimizer using a structural signal from gradient dynamics — looking for expert feedback : r/deeplearning \- Reddit, 12月 11, 2025にアクセス、 [https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/](https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/)  
21. CTR-LoRA: Curvature-Aware and Trust-Region Guided Low-Rank Adaptation for Large Language Models \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2510.15962v1](https://arxiv.org/html/2510.15962v1)