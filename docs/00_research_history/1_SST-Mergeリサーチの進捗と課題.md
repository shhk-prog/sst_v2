# **SST-Mergeの理論的基盤、新規性、および妥当性の包括的評価：Generalized Eigenvalue Problemと曲率情報に基づくモデルマージングの分析**

## **I. エグゼクティブサマリーと戦略的提言**

本報告書は、大規模言語モデル（LLM）のParameter-Efficient Fine-Tuning (PEFT) における最新鋭のマージング手法であるSST-Mergeに関して、その理論的根拠、既存研究に対する新規性、および実用的な妥当性（スケーラビリティ）を詳細に分析することを目的とする。

### **A. 調査結果の要約と新規性ステータスの結論**

SST-Mergeは、モデルマージングを、単なるパラメータの線形結合や幾何学的投影としてではなく、**曲率情報（Fisher Information Matrix: FIM）とスペクトル幾何学（Generalized Eigenvalue Problem: GEVP）を組み合わせた制約付き最適化問題**として再定式化していると推測される。

**主要な理論的優位性**は、既存のFIMベースの手法（例：Fisher Merging 1）がパラメータの絶対的な重要度に基づき重み付けを行うのに対し、SST-MergeはGEVP 2 を利用して、**ユーティリティの最大化と安全性の逸脱の最小化**という、トレードオフ関係にある二つの目的を同時に最適化する点にある。具体的には、GEVPは二つの二次形式間の比率を最大化する問題を解く 3。これにより、従来のモデルマージングが抱えるタスク干渉や安全性とユーティリティのトレードオフ（Safety Tax 5）に対し、より原理的で高度な解決策を提示する。

しかしながら、この理論的な新規性と洗練性は、計算論的なボトルネックと直結する。LLMにおけるFIMの計算コストは極めて高く 6、アンラーニングタスクにおいてさえ、その前処理が訓練プロセス自体を上回る計算時間を要することが指摘されている 7。したがって、SST-Mergeの理論的妥当性を実用的な妥当性に昇華させるためには、LoRA特有の効率的なFIM近似（例：VILA 8 やKronecker-Factored Approximate Curvature (K-FAC) 9）を採用し、GEVPの実行可能性を保証することが不可欠である。

### **B. 戦略的提言：研究計画の妥当性再確認**

SST-Mergeに関する研究計画は、その深さと複雑性から、極めて妥当であると判断される。特に、FIMとGEVPの融合は、PEFTの次のフロンティアを示唆している。

現行の研究計画を成功裏に推進するためには、理論的基盤の厳密な検証と計算効率の確認を優先するよう、フェーズ構成を再調整することが推奨される。具体的には、Phase 1（理論検証）とPhase 2（スケーラビリティ検証）を集中して実施し、GEVPの定式化が数学的に厳密であり、かつLLMの制約内で実行可能であることを確認した後、Phase 3（包括的検証）へ進むべきである。この順序は、計算論的に困難な要素がボトルネックとなり、実証フェーズに進めなくなるリスクを最小化する。

## **II. パラメータ効率型モデルマージング（PEFM）の理論的背景**

SST-Mergeの評価を行うにあたり、PEFTの文脈におけるモデルマージング技術の進化を、第一階手法から曲率情報に基づく手法へと系統立てて分析する。

### **A. 第一階手法とパラメトリック干渉の課題**

初期のモデルマージング手法は、主に勾配情報や単純なパラメータ操作に依存していた。

#### **1\. Task Arithmetic (TA) の限界と干渉**

Task Arithmetic (TA) は、追加の訓練なしにモデルを結合するための単純かつ有効な手法として登場した 10。TAは、ファインチューニング後のモデル ($\theta_{Task}$) と事前学習済みモデル ($\theta_{Pre}$) の差分ベクトル（タスクベクター $\Delta \theta = \theta_{Task} - \theta_{Pre}$）を線形結合することでマルチタスクモデルを構築する。しかし、TAとその派生手法は、ネットワーク全体を単なる高次元のパラメータベクトルとして扱うため、レイヤーレベルの構造情報や、パラメータ間の複雑な相互作用を見落としてしまうという本質的な限界を持つ 10。

この構造情報の欠如は、**タスク干渉 (Task Interference)** を引き起こす主要な原因である。干渉は、あるタスクの知識を保持しようとすると、他のタスクの性能が損なわれる現象として現れる 10。タスクベクトルのコサイン類似度が高ければ、タスクがセマンティックに類似している傾向があることが観察されているが 11、これはあくまで高次元空間における粗い指標にすぎない。

#### **2\. TIES-Mergingによる方向性解析とスパース化**

TIES-Merging (TRIM, ELECT SIGN & MERGE) は、TAの限界に対処するために開発された 12。TIES-Mergingは、(1) ファインチューニング中にわずかしか変化しなかったパラメータをゼロにリセットするトリミング（Trim）、(2) サインの衝突を解決する、(3) 一致したサインを持つパラメータのみを結合するという三段階を踏む 12。

TIES-Mergingは、パラメータの**方向性**と\*\*重要性（マグニチュード）\*\*を考慮に入れることで干渉を軽減しようとする 13。これは、すべてのパラメータが等しく重要ではないという認識、すなわち、モデルマージングがパラメータ空間における構造的な方向を考慮する必要があるという認識の現れであり、SST-Mergeが採用するより洗練された幾何学的アプローチへの進化の萌芽である。

### **B. スペクトル幾何学に基づくサブスペース手法**

Parameter-Efficient Fine-Tuning (PEFT) の主流であるLow-Rank Adaptation (LoRA) は、更新行列を低ランク行列の積 ($\Delta W = BA^T$) として表現する 14。この低ランク構造は、モデル更新の解析に特異値分解（SVD）という幾何学的なツールを適用することを可能にした 15。

#### **1\. SVDによる干渉緩和とランク維持**

SVDは、LoRAアダプタの更新行列 $\Delta W$ の構造を理解する上で重要なレンズを提供する。LoRAによって学習された重み行列は、全ファインチューニングとは異なる構造、特に「侵入者次元（intruder dimensions）」と呼ばれる新しい高ランクの特異ベクトルを示すことが発見されている 16。

このSVDの知見を利用したモデルマージング手法が登場している。

* **TSV-Merge:** レイヤーレベルでSVDを実行し、Task Singular Vectors (TSV) を定義する 10。これにより、タスク干渉をより微細に測定し、タスクレイヤー行列を元のサイズの10%に圧縮しつつ、99%の精度を保持する 10。  
* **DARE (Subspace Boosting):** TAベースの手法で多くのエキスパートモデル（最大20モデル）をマージする際に、共通情報がタスク固有情報を支配し、性能低下を招く「ランク崩壊（Rank Collapse）」が必然的に発生するという限界を理論的・経験的に分析した 17。DAREは、SVD分解されたタスクベクトル空間上で、閾値 $\beta$ 以下の小さい特異値をブーストするSubspace Boostingを導入することで、モデルの有効ランクを維持し、マージングの有効性を大幅に向上させる 17。また、Higher-Order Generalized Singular Value Decomposition (HO-GSVD) を用い、タスクベクトル間の共通サブスペースを特定することで、タスク類似性を定量化し、モデルマージングに新たな解釈可能な視点を提供する 17。

#### **2\. 幾何学的手法の限界**

これらの幾何学的手法（SVD、GSVD）は、パラメータ更新ベクトルの**配置（スパン、直交性）とマグニチュード**に焦点を当てることで干渉を緩和する。しかし、これらの方向が**統計的にどれだけ頑健か**、すなわち、その方向での更新が尤度関数に与える影響がどの程度「曲がっている」か（曲率が高いか低いか）という情報が欠けている。SST-MergeがGEVPという曲率に基づく最適化を導入する背景には、幾何学的健全性（SVD）と統計的健全性（FIM）の両立が、真に構造的で頑健なモデルマージングを実現するために必要であるという理解がある。

### **C. 曲率情報に基づくパラメータの重要度推定**

モデルパラメータの統計的な重要性を定量化するために、Fisher Information Matrix (FIM) が用いられる。

#### **1\. Fisher Information Matrix (FIM) の基礎**

FIMは、観測可能な確率変数 $X$ が、モデル化された分布の未知のパラメータ $\theta$ について持つ情報量を測る数学的統計学の手法である 19。これは、スコア（対数尤度の勾配）の分散、または観測情報の期待値として形式的に定義される 19。

FIMは、最大尤度推定（MLE）の漸近理論において中心的役割を果たし、MLEに関連する共分散行列の計算に用いられる 19。また、ベイズ統計学では、Laplace近似を行う際に、FIMが適合されたガウス分布の共分散として現れる 19。これらの性質から、FIMはパラメータ空間における尤度関数の局所的な曲率（湾曲度）を示す指標として機能する。

#### **2\. FIMを用いた古典的なマージング手法**

**Fisher Merging** 1 は、FIMをパラメータの重要度として活用する古典的なアプローチである 13。この手法は、各タスクのFIMを計算し、その逆行列を共分散（不確かさ）として利用することで、マージされたモデルのパラメータを、すべてのタスクの事後分布で高確率となるように、FIMで重み付けされた平均として算出する 1。FIMは、マージングにおいて、どのパラメータを優先すべきかを決定するための統計的に健全な重み付けを提供する。

#### **3\. 安全・ユーティリティの構造的分解（AlignGuard-LoRA）**

LLMのファインチューニングにおいて、安全性アライメントとユーティリティ（タスク性能）の間には、Safety Taxと呼ばれる厳しいトレードオフが存在する 5。安全性アライメントは有害な出力率を大幅に減少させる一方で、推論精度を30%以上低下させる可能性がある 5。

AlignGuard-LoRA (AGL) 23 は、このトレードオフに対処するための最先端の手法であり、SST-Mergeを評価する上での主要な比較基準を提供する。AGLは、**Fisher-Guided Decomposition**を採用し、安全性タスクのデータから計算されたFIMの固有値分解（Eigen-decomposition）を利用する 23。この分解により、LoRAの更新 $\Delta W$ を、\*\*アライメントに決定的な成分 ($\Delta W_A$)**と**タスク固有の成分 ($\Delta W_T$)\*\*に直交分解する 23。これにより、AGLは、FIMによって特定された高曲率な安全性に敏感な方向に対して選択的な正則化を適用し、安全性の維持と性能低下の最小化を両立する 23。

## **III. SST-Mergeのメカニズム：詳細な理論的解体と新規性評価**

SST-Mergeは、第二階情報を利用した最新の研究トレンドの頂点に位置づけられ、安全性とユーティリティの間のトレードオフを、Generalized Eigenvalue Problem (GEVP) を用いて能動的に解決しようと試みている。

### **A. 提示されたメカニズム：GEVPによる最適サブスペースの特定**

SST-Mergeの理論的基盤は、マージング方向の探索を、**一つの目的を、別の目的によって制約された空間で最大化する問題**として定式化することにある。

GEVP ($A x = \lambda B x$) は、二次形式 $x^T A x$ を $x^T B x$ に関して最大化する問題の解法を提供する。この最適化は、**Rayleigh Quotient**の最大化に他ならない 3。Rayleigh Quotientは、物理情報ニューラルネットワーク（PINN）の固有振動数解析など、効率的な方向探索が求められる分野でも応用されている 4。

SST-Mergeの文脈において、これは以下のような最適化問題に対応すると解釈される。

$\Delta W^* = \text{argmax}_{\Delta W} \frac{\text{Utility Gain}(\Delta W)}{\text{Alignment Cost}(\Delta W)} = \text{argmax}_{\Delta W} \frac{\Delta W^T H_{Util} \Delta W}{\Delta W^T F_{Safety} \Delta W}$
ここで、

* $H_{Util}$ は、マージされたタスクの尤度関数に関するHessianまたはFIMであり、**ユーティリティの改善**度合いを示す。  
* $F_{Safety}$ は、安全性アライメントタスクのFIMであり、**安全性の逸脱**（コスト）の度合いを示す。FIMは、その方向におけるパラメータ変化に対するモデルの応答の「硬さ」を定量化するため、安全性の維持に不可欠な方向の曲率を表す。

この定式化におけるGEVPの最大固有値 $\lambda_{max}$ に対応する固有ベクトル $\Delta W^*$ は、**安全性の逸脱（コスト）を最小限に抑えながら、ユーティリティ（ゲイン）を最大化する**、パラメータ空間における最適なマージング方向を意味する。この手法は、制約付き最適化アルゴリズム、特にシーケンシャル二次計画法（SQP）において勾配を部分空間に射影する手法 25 と類似しており、FIMをトラストリージョン（信頼領域）の境界を定義するメトリックとして利用するという、第二階最適化のトレンドと一致する 27。FIMは、収束加速ではなく、更新の安定性や構造的コヒーレンスを保証する役割に機能転換している 29。

### **B. 新規性評価：AlignGuard-LoRAとの差別化**

SST-Mergeの真の新規性は、既存のFIMベースの分解手法、特にAlignGuard-LoRA (AGL) 23 と比較することで明らかになる。

AGLは、安全性タスクのFIM ($F_{Safety}$) の**単一の**固有値分解に基づいており、これにより安全性の高曲率方向を特定し、その方向を固定した基底へタスク更新 $\Delta W$ を射影する 23。これは、危険な方向を「回避」する戦略である。

一方、SST-Mergeは、ユーティリティと安全性の**二つの独立したメトリック** ($H_{Util}$ と $F_{Safety}$) を同時に考慮し、その**比率を最適化**する。GEVPは、このトレードオフ関係にある二つの目的のバランスを数学的に厳密に解決する。これにより、SST-Mergeは、単に安全なサブスペースに留まることを目的とするのではなく、**安全性の制約の下で最大のユーティリティを得る**という、より高度な最適解を追求する。この二指標に基づく最適化フレームワークは、モデルマージングにおける安全性とユーティリティのトレードオフに対し、既存のFIMベースの手法よりも原理的かつ高度な解決策を提供すると結論付けられる。

### **C. 妥当性の検証：計算量とスケーラビリティの課題**

SST-Mergeの理論的優位性を実証するためには、LLMスケールでの計算実行可能性が最も重要な妥当性評価項目となる。

#### **1\. FIM計算のボトルネック**

FIMの計算は、一般にモデルパラメータ数に対して計算コストが非常に高く、LLMの文脈で大きな運用上の制約を生じさせる 6。特に、アンラーニング手法であるFILA（Fisher Information based LoRA Adapter）の例では、忘却セットの重要度マップの抽出が、アンラーニングプロセス自体よりも大きな計算コストを要し、忘却セットのサイズに対してスケーラビリティが低いことが示されている 7。

したがって、SST-Mergeが実用的であるためには、フルFIMの計算は避けられ、LoRAの低ランク構造を利用した極めて効率的な近似戦略が必須となる。これには以下のような手法が候補となる。

* **Kronecker積近似:** K-FAC 9 やその低ランク化 30 は、FIMをブロック対角構造とKronecker積で近似することで計算量を削減する。  
* **勾配の分散近似:** LoRAアダプタの行列 $A$ と $B$ の勾配の分散を独立に計算し、その積を用いることで、モデルパラメータ $\Delta W$ の分散を近似する手法が提案されている 7。  
* **部分的なパラメータ識別:** VILA 8 のように、FIMの計算において全モデルパラメータにアクセスすることなく、特定のタスクに関連するパラメータのみを効率的に識別する手法は、計算効率を最大100倍、訓練速度を40倍高速化する結果を示しており、FIMを利用するPEFT手法のスケーラビリティを確保する上で決定的に重要となる 8。

#### **2\. GEVPの実行可能性**

Generalized Eigenvalue Problem自体も、一般に大規模な行列に対しては解くのが難しい問題である。3パラメータの固有値問題でさえ、その拡張は困難であり、計算には特殊なサブスペース反復法（Generalized Krylov subspaces）やJacobi–Davidsonタイプの手法が必要となる 2。

SST-MergeがLLMスケールで実用的であるためには、行列 $H_{Util}$ と $F_{Safety}$ が、前述のKronecker積近似 9 やその他の構造的近似によって、超効率的な低ランク表現でなければならない。Phase 2では、SST-Mergeが具体的にどのような行列近似とGEVPソルバーを採用しているかを厳密に検証する必要がある。

## **IV. 妥当性と研究ギャップ：詳細な評価**

### **A. 理論的妥当性：サブスペース内での性能保証**

SST-Mergeの理論的妥当性は、GEVPによって導出された最適なマージング方向 $\Delta W^*$ が、安全性とユーティリティのトレードオフ空間において、実際にロバストで安定した性能向上を保証できるかどうかにかかっている。

#### **1\. 制約付き最適化としての厳密性**

SST-Mergeは、本質的に「安全性アライメントの制約（$F_{Safety}$ が定義する安全圏）内に留まりながら、タスク性能（$H_{Util}$）を最大化する」という制約付き最適化をサブスペース内で実行している 25。

既存のSafety LoRA 31 は、LoRAの更新を、アライメントされたモデルとアライメントされていないモデルの差分によって定義される安全サブスペースに静的に射影することで、安全リスクを軽減する。SST-Mergeは、FIM（曲率）を通じて、この「安全なサブスペース」をより動的かつ最適化の目的関数に組み込む形で定義できる点が優れている。

#### **2\. 曲率情報の機能転換**

従来の最適化手法（Adam, SGD）は、一次勾配情報に依存するため、尤度関数の曲率情報が不足し、ロバスト性を欠くことが指摘されている 33。SST-Mergeや、Trust Region Policy Optimization (TRPO) 27 のような第二階手法は、FIMやHessianを、単に勾配降下を加速するためではなく、**更新の安定性を保証するメトリック**（トラストリージョン）として利用する方向に進化している 29。SST-Mergeでは、GEVPの分母にFIMを配置することで、安全性という制約に対する更新の感度を調整し、構造的コヒーレンスと安全性の境界を定義する役割をFIMに与えている。この機能転換は、第二階情報をマージングの文脈で利用する上での理論的鍵である。

### **B. 実験的妥当性：評価指標の厳格化**

SST-Mergeの実証的妥当性を確立するためには、SOTA手法（特にAGL）に対し、安全性とユーティリティの複合的なベンチマークで明確な優位性を示す必要がある。

#### **1\. Safety Taxの定量化と複合評価**

モデルの妥当性を確立するためには、既存のLLMが抱えるSafety Tax 5 をSST-Mergeがどの程度緩和できるかを定量的に示すことが不可欠である。これは、単純な拒否率（Refusal Accuracy）のような粗粒度な評価指標 6 ではなく、より洗練された複合的な評価手法を採用する必要がある。

例えば、AGLが導入したDRIFTCHECKベンチマーク 23 は、アライメントドリフトを評価するために設計されており、Safety Taxの緩和率を厳密に定量化するための標準として機能する。また、Safety Taxは負の相関（$r < -0.75$）で定量化されることがあり、MedOmni-45°のような複合メトリックは、モデルの性能（精度）と安全性（忠実性、シコファシー）のバランスを評価するのに有用である 5。

#### **2\. 包括的ベンチマークの採用**

SST-Mergeが広範なシナリオで有効であることを証明するためには、毒性、バイアス、倫理遵守など多様な安全側面を網羅する専門ベンチマークを使用する必要がある。BeaverTails 35 やその多言語対応（例：BeaverTails-IT 36）のようなデータセットは、モデルの行動を多様な安全次元にわたって評価するために不可欠である。SST-Mergeは、これらのベンチマークで、SOTA手法と比較してアライメントドリフトを最大50%低減しつつ、タスク性能を維持できるかどうかが焦点となる 23。

## **V. 研究計画の再検証と将来のロードマップ**

SST-Mergeの調査項目の深さと複雑性を踏まえ、現在の研究計画の妥当性を再確認し、成功に向けた戦略的なロードマップを提示する。

### **A. 現在の調査項目の複雑性評価**

以下の表は、SST-Mergeの研究を構成する主要な理論的要素と、それらが持つ複雑性および研究継続における必須性を示す。GEVPとFIMの近似は、ともに最高レベルの理論的・計算的困難を伴うことが確認される。

Table 1: SST-Merge研究の主要な複雑性と必須性の評価

| 調査項目 | 複雑性（評価基準 C1-C5） | SST-Mergeにおける必須性 | 妥当性確認のための鍵となる課題 |
| :---- | :---- | :---- | :---- |
| GEVPメカニズムの理論的厳密性 | C5 (最高) 2 | 必須：新規性の核となる。 | GEVPが、単一FIM固有値分解を超える、真の最適解を提供することの証明。 |
| FIM/Hessianの近似効率 | C4 (高) 6 | 必須：実用的なスケーラビリティ。 | LoRAに特化した低コスト近似の採用有無とその性能検証 7。 |
| Safety/Utilityの構造的分解 | C4 (高) 5 | 必須：主要なパフォーマンス目標。 | AGL 23 を上回るSafety Taxの緩和率の定量化。 |

### **B. 研究継続のための戦略的ロードマップ**

研究継続の妥当性は高く、SST-MergeがPEFM分野におけるブレークスルーを達成する可能性を秘めている。しかし、成功を確実にするため、理論的基盤と計算効率の確保を最優先する以下のロードマップに沿ってリサーチを継続することを提言する。

#### **Phase 1: 理論的検証と定式化の厳密化（期間：短期）**

**目標:** SST-Mergeの核となるGEVP定式化の数学的厳密性と、それが導く最適解の特性を確立する。

* **タスク 1.1:** ユーティリティと安全性のFIM（$H_{Util}, F_{Safety}$）の定義、特に$H_{Util}$がHessianかFIMかを確認し、GEVPの解析解または数値解法の安定性を検証する。  
* **タスク 1.2:** GEVPの解が、既存のSVDベースのDARE 17 やFIM分解ベースのAGL 23 よりも、トレードオフ解決において理論的に優位性を持つこと（例：よりタイトな安全制約下で高い効用を達成すること）を証明する。

#### **Phase 2: 計算効率とスケーラビリティの検証（期間：中期）**

**目標:** LLMにおける実用的な妥当性を確認するため、計算コストのボトルネックを特定し、その近似戦略の効率を評価する。このフェーズの成功が、実証実験への移行を正当化する。

* **タスク 2.1 (近似戦略の確認):** SST-MergeがFIM計算において、VILA 8 やLoRA勾配分散近似 7 のような、高いパラメトリック効率を持つ手法を用いているか、またはK-FACの低ランク近似 9 に依存しているかを確認する。  
* **タスク 2.2 (マイクロベンチマーク):** GEVP/FIM計算ステップのレイテンシとGPUメモリ消費量を、SVDベースのDAREやK-FAC近似と比較し、計算論的なスケーラビリティの優位性を定量的に示す 37。

#### **Phase 3: 網羅的な実証実験とSOTA性能の確定（期間：長期）**

**目標:** SST-Mergeの性能をSOTAと比較し、特に安全性とユーティリティのトレードオフ解消における優位性を実証する。

* **タスク 3.1 (安全性検証):** AGL 23 を主要な競合相手として、DRIFTCHECKおよびBeaverTails 36 を使用した安全性とユーティリティの複合ベンチマークを実施し、Safety Taxの削減率を厳密に提示する 5。  
* **タスク 3.2 (マルチタスク干渉耐性):** 多数の専門家モデル（10〜20モデル）をマージし 17、TIES-MergingやDAREに対する頑健性と性能向上を検証する。特に、HO-GSVDがタスク類似性を定量化する能力に対し、SST-Mergeがタスク間の最適方向を特定する能力がどれだけ優れているかを比較する 17。

#### **引用文献**

1. Merging Models with Fisher-Weighted Averaging \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=LSKlp_aceOC](https://openreview.net/pdf?id=LSKlp_aceOC)  
2. \[1802.07386\] Subspace Methods for 3-Parameter Eigenvalue Problems \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1802.07386](https://arxiv.org/abs/1802.07386)  
3. RAE: A Neural Network Dimensionality Reduction Method for Nearest Neighbors Preservation in Vector Search \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2509.25839v1](https://arxiv.org/html/2509.25839v1)  
4. A Mesh-Free Physics-Informed Neural Network Based on Rayleigh Quotient for Structural Frequency Analysis of Beams and Plates \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates](https://www.researchgate.net/publication/393590186_A_Mesh-Free_Physics-Informed_Neural_Network_Based_on_Rayleigh_Quotient_for_Structural_Frequency_Analysis_of_Beams_and_Plates)  
5. Reasoning-Safety Trade-Off \- Emergent Mind, 12月 11, 2025にアクセス、 [https://www.emergentmind.com/topics/reasoning-safety-trade-off](https://www.emergentmind.com/topics/reasoning-safety-trade-off)  
6. AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- ChatPaper, 12月 11, 2025にアクセス、 [https://chatpaper.com/paper/172737](https://chatpaper.com/paper/172737)  
7. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2508.21300v1](https://arxiv.org/html/2508.21300v1)  
8. Improving Fisher Information Estimation and Efficiency for LoRA-based LLM Unlearning, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4](https://www.semanticscholar.org/paper/Improving-Fisher-Information-Estimation-and-for-LLM-Kim-Kim/3d6291914e7f461460ef6852c3ef9457b8a292b4)  
9. \[1503.05671\] Optimizing Neural Networks with Kronecker-factored Approximate Curvature, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/1503.05671](https://arxiv.org/abs/1503.05671)  
10. Task Singular Vectors: Reducing Task Interference in Model Merging \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf](https://openaccess.thecvf.com/content/CVPR2025/papers/Gargiulo_Task_Singular_Vectors_Reducing_Task_Interference_in_Model_Merging_CVPR_2025_paper.pdf)  
11. EDITING MODELS WITH TASK ARITHMETIC \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=6t0Kwf8-jrj](https://openreview.net/pdf?id=6t0Kwf8-jrj)  
12. TIES-MERGING: Resolving Interference When Merging Models \- NIPS papers, 12月 11, 2025にアクセス、 [https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf](https://papers.neurips.cc/paper_files/paper/2023/file/1644c9af28ab7916874f6fd6228a9bcf-Paper-Conference.pdf)  
13. From Coefficients to Directions: Rethinking Model Merging with Directional Alignment \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2512.00391v1](https://arxiv.org/html/2512.00391v1)  
14. \[2511.07129\] LoRA on the Go: Instance-level Dynamic LoRA Selection and Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/abs/2511.07129](https://arxiv.org/abs/2511.07129)  
15. Parameter Efficient Merging for Multimodal Large Language Models with Complementary Parameter Adaptation \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2502.17159v1](https://arxiv.org/html/2502.17159v1)  
16. LoRA vs Full Fine-tuning: An Illusion of Equivalence \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2410.21228v1](https://arxiv.org/html/2410.21228v1)  
17. SUBSPACE-BOOSTED MODEL MERGING \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf](https://openreview.net/pdf/22985c05771dd87f418be6942009ba193f1e9a70.pdf)  
18. Subspace-Boosted Model Merging \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.16506v2](https://arxiv.org/html/2506.16506v2)  
19. Fisher information \- Wikipedia, 12月 11, 2025にアクセス、 [https://en.wikipedia.org/wiki/Fisher_information](https://en.wikipedia.org/wiki/Fisher_information)  
20. Fisher Merging \- FusionBench \- Anke Tang, 12月 11, 2025にアクセス、 [https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/](https://tanganke.github.io/fusion_bench/algorithms/fisher_merging/)  
21. TOWARDS COMPREHENSIVE AND EFFICIENT POST SAFETY ALIGNMENT OF LARGE LANGUAGE MODELS \- OpenReview, 12月 11, 2025にアクセス、 [https://openreview.net/pdf?id=09JVxsEZPf](https://openreview.net/pdf?id=09JVxsEZPf)  
22. Exploring Safety-Utility Trade-Offs in Personalized Language Models \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2025.naacl-long.565/](https://aclanthology.org/2025.naacl-long.565/)  
23. Paper page \- AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via Fisher-Guided Decomposition and Riemannian-Geodesic Collision Regularization \- Hugging Face, 12月 11, 2025にアクセス、 [https://huggingface.co/papers/2508.02079](https://huggingface.co/papers/2508.02079)  
24. \[PDF\] AlignGuard-LoRA: Alignment-Preserving Fine-Tuning via, 12月 11, 2025にアクセス、 [https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f](https://www.semanticscholar.org/paper/391370ff035339bf3f38239afb556b7ddda2b93f)  
25. Constrained Nonlinear Optimization Algorithms \- MATLAB & Simulink \- MathWorks, 12月 11, 2025にアクセス、 [https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html](https://www.mathworks.com/help/optim/ug/constrained-nonlinear-optimization-algorithms.html)  
26. Algorithms for constrained optimization, 12月 11, 2025にアクセス、 [https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf](https://mdav.ece.gatech.edu/ece-6270-spring2021/notes/17-constrained-algs-intro.pdf)  
27. Trust Region Policy Optimization (TRPO) | by Leonidas Gorgo | Nov, 2025 \- Medium, 12月 11, 2025にアクセス、 [https://leonidasgorgo.medium.com/trust-region-policy-optimization-trpo-d9f5536d6aeb](https://leonidasgorgo.medium.com/trust-region-policy-optimization-trpo-d9f5536d6aeb)  
28. CTR-LoRA: Curvature-Aware and Trust-Region Guided Low-Rank Adaptation for Large Language Models \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2510.15962v1](https://arxiv.org/html/2510.15962v1)  
29. A new first-order optimizer using a structural signal from gradient dynamics — looking for expert feedback : r/deeplearning \- Reddit, 12月 11, 2025にアクセス、 [https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/](https://www.reddit.com/r/deeplearning/comments/1pfio8x/a_new_firstorder_optimizer_using_a_structural/)  
30. SKFAC: Training Neural Networks With Faster Kronecker-Factored Approximate Curvature \- CVF Open Access, 12月 11, 2025にアクセス、 [https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf](https://openaccess.thecvf.com/content/CVPR2021/papers/Tang_SKFAC_Training_Neural_Networks_With_Faster_Kronecker-Factored_Approximate_Curvature_CVPR_2021_paper.pdf)  
31. Safe Pruning LoRA: Robust Distance-Guided Pruning for Safety Alignment in Adaptation of LLMs | Transactions of the Association for Computational Linguistics \- MIT Press Direct, 12月 11, 2025にアクセス、 [https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning](https://direct.mit.edu/tacl/article/doi/10.1162/TACL.a.44/133861/Safe-Pruning-LoRA-Robust-Distance-Guided-Pruning)  
32. Safe LoRA: The Silver Lining of Reducing Safety Risks when Finetuning Large Language Models | Request PDF \- ResearchGate, 12月 11, 2025にアクセス、 [https://www.researchgate.net/publication/397202248_Safe_LoRA_The_Silver_Lining_of_Reducing_Safety_Risks_when_Finetuning_Large_Language_Models](https://www.researchgate.net/publication/397202248_Safe_LoRA_The_Silver_Lining_of_Reducing_Safety_Risks_when_Finetuning_Large_Language_Models)  
33. Efficient Natural Gradient Descent Methods \- UCLA Mathematics, 12月 11, 2025にアクセス、 [https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf](https://ww3.math.ucla.edu/wp-content/uploads/2023/04/Cam23-018.pdf)  
34. Projected proximal gradient trust-region algorithm for nonsmooth optimization \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2501.04889v1](https://arxiv.org/html/2501.04889v1)  
35. Video-SafetyBench: A Benchmark for Safety Evaluation of Video LVLMs \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2505.11842v3](https://arxiv.org/html/2505.11842v3)  
36. BeaverTails-IT: Towards A Safety Benchmark for Evaluating Italian Large Language Models \- CEUR-WS.org, 12月 11, 2025にアクセス、 [https://ceur-ws.org/Vol-4112/59_main_long.pdf](https://ceur-ws.org/Vol-4112/59_main_long.pdf)  
37. Improving LoRA with Variational Learning \- arXiv, 12月 11, 2025にアクセス、 [https://arxiv.org/html/2506.14280v1](https://arxiv.org/html/2506.14280v1)  
38. Orthogonal Finetuning Made Scalable \- ACL Anthology, 12月 11, 2025にアクセス、 [https://aclanthology.org/2025.emnlp-main.1627.pdf](https://aclanthology.org/2025.emnlp-main.1627.pdf)