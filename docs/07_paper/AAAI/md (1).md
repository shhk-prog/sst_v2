## 本レポートの目的

本レポートは、SST-Merge（Fisher-Ratio Subspace Steering for Safety-Preserving Model Merging）の提案論文における Related Work セクションおよび査読対応戦略の素材として、Fisher情報行列（FIM）活用系のモデルマージ研究5本と、Safety-Utilityトレードオフ解消系の研究5本、計10本の先行研究を体系的に整理したものである。各論文について、問題意識、解決策、技術的核心、限界を明確化し、SST-Mergeとの理論的差別化点を論じる。

## 1. これまでの研究の流れ（2022〜2026年）

### 1.1 研究の変遷：4つのフェーズ

モデルマージにおけるFisher情報行列の活用と、Safety-Utilityトレードオフ（Safety Tax／Alignment Tax）の解消に向けた研究の系譜は、以下の4フェーズで整理できる。

**Phase 1（2022〜2023年、黎明期）**は、複数モデルをマージする際の破滅的忘却の防止を主題とし、FIMを重要度指標として加重平均に利用する基礎理論が確立された時期である。Matena と Raffel によるFisher-Weighted Averaging（FWA）が起点となり、続いて Daheim らがモデル間の勾配ミスマッチに着目した Uncertainty-based Gradient Matching を提案した。[^1][^2]

**Phase 2（2024〜2025年、発展期）**では、Phase 1の手法が抱えていた外れ値への脆弱性やハイパーパラメータ手動調整の困難さを克服するため、手法の精緻化・ロバスト化が進んだ。Thennal らによる Fisher Mask Nodes は計算コストの大幅な削減を実現し、Fisher-Weighted Median（DRIFT-MEDIAN）は中央値集約により外れ値耐性を高め、Lee らの DF-Merge はベイズ最適化によって重み係数の自動探索を可能にした。[^3][^4][^5]

**Phase 3（2024〜2026年、Safety特化期）**は、SafetyパッチとUtilityパッチのパラメータ競合、すなわち「Safety Tax」の問題そのものに正面から取り組む研究群である。Hammoud らの MergeAlign はドメインベクトルとアライメントベクトルの分離・補間によってこの問題に対処し、Ma らの LED-Merging は勾配アトリビューションに基づくニューロン単位の競合分離を提案し、Djuhera らの SafeMERGE は層単位での選択的マージを行い、Wang らの AlignMerge は Fisher幾何上でのalignment-preserving制約付き最適化としてマージを定式化した。[^6][^7][^8][^9]

**Phase 4（2025〜2026年、実用制約期）**は、キャリブレーションデータを利用できないData-Free環境という現実的な制約への対応が中心的課題となっている時期であり、Wang らのランダムトークンベースの層適応的FIM近似手法がこれに該当する。[^10]

これら4フェーズを俯瞰すると、研究の本質的な問題意識は「いかにパラメータを壊さずにマージするか」（Phase 1〜2）から「いかにSafetyとUtilityを同時に最大化するか」（Phase 3〜4）へと移行してきたことが分かる。SST-Merge は、この移行の先に「その最適化にどのような理論的根拠を持たせるか」という問いを立てる位置づけにある。

### 1.2 フェーズ別の研究の重心と問題意識の変遷

| フェーズ | 期間 | 研究の中心問題 | 主なアプローチ |
|---|---|---|---|
| Phase 1: 黎明期 | 2022–2023 | 複数モデルマージ時の破滅的忘却の防止 | FIMを重要度指標とした加重平均[^1][^2] |
| Phase 2: 発展期 | 2024–2025 | 外れ値への脆弱性、ハイパーパラメータ手動調整の困難さ | 中央値・ベイズ最適化・マスクノードによる精緻化[^3][^4][^5] |
| Phase 3: Safety特化期 | 2024–2026 | SafetyパッチとUtilityパッチのパラメータ競合（Safety Tax） | タスクベクトルの分離・衝突回避・幾何学的制約[^6][^7][^8][^9] |
| Phase 4: 実用制約期 | 2025–2026 | 学習データが使えない（Data-Free）現実的制約への対応 | データフリーFIM近似・層別適応[^10] |
| SST-Merge（提案） | 2025– | Safety/Utilityコストパフォーマンスの同時最適化 | 一般化固有値問題（GEVP）・階層的サロゲート・座標単位補間 |

## 2. 先行研究：課題・解決策・限界の詳細分析

### 2.1 フェーズ1：黎明期（基礎理論の確立）

####  Merging Models with Fisher-Weighted Averaging（Matena & Raffel, NeurIPS 2022）[^1]

本論文は、モデルマージにFIMを活用するという発想そのものの理論的出発点であり、SST-Mergeが「Fisherをマージの重み付け根拠にする」という発想において最も直接的に依拠する先行研究である。[^1]

既存の課題として、単純な重み平均（Model Soup）では各タスクが学習した重要な内部表現が多数決的に平均化され、本質的な知識が失われる破滅的忘却が生じる点が挙げられる。解決策として、ラプラス近似に基づくベイズ推論の観点からFIMを定義し、各パラメータの重要度（そのパラメータが出力分布に与える影響の大きさ）をFIM対角成分で近似したうえで、重要度の高いパラメータを優先的に保持するFisher-Weighted Averagingを定式化した。2モデルの場合の技術的核心は \(\theta_{\text{merged}} = F_1^{-1}(F_1\theta_1 + F_2\theta_2)\) のような閉形式解に帰着する。

実験ではBERT、RoBERTa、ViTを対象に、RTE・MRPC・SST-2などのGLUEタスクおよびImageNet-A/R/Sketch/V2/ObjectNetでの評価が行われ、Fisher mergingは単純平均を上回り出力アンサンブルに近い性能を達成した。BERT 5モデルのアンサンブル相当の性能を単一モデルで実現し、推論コストを5分の1に削減できることが示されている。[^1]

限界として、①Safety と Utility のように相反する勾配方向を持つタスク間の競合には対応できない、②FIMを単一の意味（重要度）でしか用いておらず、Utilityへの影響とSafetyへの影響を区別しない、という2点が挙げられる。SST-Mergeとの違いは、先行研究がLaplace近似とFisher精度に基づく事後分布平均化を行うのに対し、SST-Mergeは2つの分布（Safety/Utility）のFisherを分離して扱い、その比率によって方向選択を行う点にある。

####  Model Merging by Uncertainty-Based Gradient Matching（Daheim et al., ICLR 2024, arXiv 2023）[^2]

既存の課題として、FWAのような対角FIM依存手法は、モデル間のパラメータ更新方向（勾配ベクトルの向き）のミスマッチを無視しており、方向が揃わないまま平均を取ると意味のある知識が打ち消し合ってしまう点が指摘される。解決策として、予測の不確実性を各パラメータの重みとして用い、勾配ベクトルが最大限に一致するようモデルの重みを整合させるGradient Matchingを提案した。[^2]

実験ではRoBERTa、ViT、GPT-2、GPT-J、Flan-T5を用いて、感情分析（IMDB、Yelp、RT、SST-2、Amazon）、画像分類（Cars、DTD、EuroSAT、GTSRB、MNIST、RESISC45、SUN397、SVHN）、および毒性・幻覚除去タスクで評価を行い、RoBERTaの感情分析においてTask Arithmeticの91.8に対し94.5、単純平均の94.7に対し96.6という改善を報告している。[^2]

限界として、「勾配の方向を合わせる」という目的はUtility（タスク性能）の保全には有効であるが、Safety（安全性の維持）という別種の目的を同時に組み込む枠組みは持たない。理論的な筋道はSST-Mergeに比較的近いが、一般的なマージ誤差の低減を目指す枠組みである一方、SST-Mergeはsecure merge設定に特化しharmful FisherとbenignFisherを競合させる点で異なる。

### 2.2 フェーズ2：発展期（手法の精緻化・ロバスト化）

####  Fisher Mask Nodes for Language Model Merging（Thennal, Nathan & Suchithra, LREC-COLING 2024）[^3]

既存の課題として、全パラメータを連続的な重みで結合する手法は、特定タスクにとって決定的に重要な特定のニューロン（ノード）への他タスクからの干渉を防げない点が挙げられる[^3]。解決策として、Transformerのマルチヘッドアテンションの各ヘッドおよびフィードフォワード層の各行（フィルタ）にマスクノードを挿入し、そのFIM（式(4)：\(I_{ii} := \frac{1}{|D|}\sum_{(x,y)\in D}(\frac{\partial}{\partial m_i}L(x,y;1))^2\)）を対応する重要パラメータブロックの重要度の代理指標として用いることで、計算コストを大幅に削減した重み付き平均マージスキームを構築した。

この手法の技術的な核心は、Matena & Raffel [^1] の閉形式解 \(\theta^* = \frac{\sum_j \lambda_j F_j \theta_j}{\sum_j \lambda_j F_j}\) において、全パラメータのFisherの代わりにマスクノードのFisher情報を代理指標として割り当てる点にある。これにより、計算が必要な勾配の数は \((H+D)\times L\) 個に抑えられ、全パラメータ \(|\theta|\) の勾配計算が必要な通常のFisher-weighted averagingに対して大幅な効率化が実現される。実験ではBERT-tiny、BERT-base、BERT-large、RoBERTa-baseを用いGLUEの6タスク（MNLI、QQP、QNLI、SST-2、MRPC、RTE）で評価し、RoBERTaでは単純平均の86.2に対し92.7（+6.5）の改善、BERT-baseでも+4.0の改善を得た一方、計算速度は既存のFisher-weighted averagingに対し57.4倍から321.7倍高速化されたことが報告されている[^3]。BERT-tinyでは性能低下も観測されている。

限界として、①マスクの閾値設定がヒューリスティックである、②安全性の維持という目的を明示的に最適化していない、③SafetyとUtilityのどちらの重要度でマスクするかという区別が本質的に存在しない、という点が挙げられる。SST-Mergeの対角Fisher近似やData-Free variantとの類似性は高いが、本論文は主に計算量削減とFisher mergeの効率化を目的とするのに対し、SST-Mergeは安全性対有用性という比率目的を保ったまま実用化するための近似という点で異なる。

####  Task-Aware Model Merging via Fisher-Weighted Median（DRIFT-MEDIAN, OpenReview, ICLR 2026投稿）[^4]

既存の課題として、FWAのような加重平均は、一部のパラメータのFIM値が非常に大きい「外れ値」となる場合に計算が引っ張られ、マージ結果が不安定化する点が指摘される。解決策として、平均の代わりに「Fisher重み付き中央値（median）」を採用して外れ値への感受性を根本的に解消し、さらにSign Resolution（干渉処理）とTop-K選択を組み合わせた多段階パイプラインを構成した。[^4]

図1に示されるように、DRIFT-MEDIANは(a)符号解決によるタスクベクトルの整合、(b)対角Fisher行列の推定、(c)座標ごとのTop-Kモデル選択、(d)Fisher重み付き集約（L1最小化に基づく閉形式解）、という手順を経て最終的なマージパラメータを得る。実験ではGPT-2、Llama-3.1-8B、Llama-3.2-3B、Llama-2-7B、CLIP ViT-B/32を対象に、GLUE、コーディング、数学、多言語推論、安全性、視覚タスクにわたる評価が行われ、GPT-2のGLUE平均でTask ArithmeticやTIESの平均70.0に対しPerformance Retain Rate（PRR）で最良ベースラインを+1.9上回る結果を得ている。[^4]

限界として、①干渉処理とFisher重み付けが独立した直列プロセスであり、いずれかのステップで「重要なのに削除される」という事態が起こりうる、②Safety-Utilityのジレンマには未対応、という2点が指摘できる。またOpenReviewの査読過程では、新規性の欠如（既存手法の組み合わせにすぎない）、特定タスクでベースラインに劣後する事例の存在、ハイパーパラメータ探索の公平性、といった批判が実際になされている。この点はSST-Mergeへの転用予防として注意すべき査読リスクである。DRIFT-MEDIANが「うまく平均する方法」を追求するのに対し、SST-Mergeは「良い方向だけを選ぶ方法」を追求するという点で目的関数が本質的に異なる。

####  Dynamic Fisher-weighted Model Merging via Bayesian Optimization（Lee et al., NAACL 2025）[^5]

既存の課題として、FIMに基づくマージのハイパーパラメータ（重みや閾値）の設定は非自明であり、グリッドサーチ等の手動調整は計算コストが高く最適解の保証もない点が挙げられる。解決策として、モデル単位でスケールする General Task Arithmetic（GTA）と、パラメータ単位で重要度を組み込むFisher Mergingという2つの既存アプローチを式(7)の一般形 \(f = (\sum_i C_{\theta_i})^{-1}(\sum_i C_{\theta_i}\lambda_i \tau_i) + \theta_{\text{pre}}\) として統一し、ベイズ最適化によって各タスクの係数 \(\lambda_i\) をバリデーション性能が最大となるように動的に探索する DF-Merge を提案した。[^5]

実験ではT5-baseおよびT5-largeを用い、PAWS、QASC、QuaRTz、Story Cloze、WikiQA、Winograndeで評価を行い、T5-baseの平均でDF-Mergeが78.14を達成し最良ベースラインのDARE（73.66）を+4.48上回り、T5-largeでも平均83.59でTask Arithmetic（81.86）を+1.73上回ることを報告している。[^5]

限界として、①自動化・最適化の改善ではあるが「何を最適化するか」という目的関数の定義自体には本質的な革新がない、②Safety対Utilityという二目的最適化（multi-objective optimization）の設定には対応していない、という点が挙げられる。DF-Mergeは「validation performanceを最大化する係数探索」であるのに対し、SST-Mergeは「安全性効率の高い方向を選ぶ制約付き最適化」であり、探索ベースか解析的定式化かという点で方法論が対照的である。

### 2.3 フェーズ3：Safety-Utility特化期（Safety Taxへの挑戦）

####  MergeAlign / Combining Domain and Alignment Vectors（Hammoud et al., arXiv 2024）[^6]

既存の課題として、ドメイン特化ファインチューニングは知識・性能を向上させる一方、その過程でベースモデルが持っていた安全性アライメントが急激に劣化する「Safety Tax」が生じる点が挙げられる。解決策として、ドメイン特化タスクベクトルと安全性維持のためのアライメントベクトルを別々に抽出・管理し、線形結合によって両者のバランスを制御するMergeAlignを提案した。[^6]

実験ではLlama-3-8B系のドメイン専門モデルを対象に、Medicine、Finance、HH-Red Team、BeaverTails、GSM8Kで評価が行われ、MedicineドメインでMergeAlignは61.33、BeaverTailsでは99.67というスコアを達成し、比較対象のSlerpがドメイン性能では近い値を示しつつもアライメント指標で約10%劣ることが報告されている。HH-Red TeamやBeaverTailsにおいて、MergeAlignはアライメント済みモデルに近い水準を保持できることが示された。[^6]

限界として、①線形結合の重みはスカラーであり、パラメータごとにSafetyとUtilityのどちらに重要かを区別できない、②理論的な最適性の保証がなく、パレート最適点の特定には到達できない、という2点が指摘される。MergeAlignは「安全性を明示的に扱うが、Fisherではなくタスクベクトル加算によって行う」位置づけの手法であり、問題設定はSST-Mergeと極めて近いが、方法はより単純なベクトル補間による トレードオフ制御にとどまる。SST-Mergeが局所曲率とFisher比を用いて「どの方向・どの座標を通すか」を決定するのに対し、MergeAlignは「どのベクトルをどれだけ混ぜるか」に重心を置く点で異なる。

####  LED-Merging（Ma et al., ACL 2025）[^7]

既存の課題として、SafetyパッチとUtilityパッチをマージする際、同じパラメータ座標に対して両者が重要な更新を要求する競合が生じ、いずれかの性能が犠牲になる点が問題視される。解決策として、Location（勾配ベースの重要度スコア \(I(\theta_i) = \mathbb{E}_{x\sim X_i}[\theta_i \odot \nabla_{\theta_i}L(x)]\) による競合箇所の特定）、Election（ベースモデルとファインチューニング済みモデルの双方で高スコアを示すニューロンの積集合 \(T_{r_i} = N_{r_i} \cap N_{r_{\text{base}}}\) を取る選出）、Disjoint Merging（タスク間で重複する重要ニューロンを集合差演算によって排除する分離）という3段階処理によって競合を回避するフレームワークを構築した。[^7]

実験ではMistral-7B、Llama-3-8B、Llama2/WizardLM-13Bを対象に、HarmBench、SORRY-Bench、GSM8K、MATH、MBPP、HumanEval-Packで評価を行い、Llama-3-8BにおいてHarmBenchの安全性スコアを31.4%改善しつつGSM8Kの精度52.39を保持することを報告している。Mistral-7BではHarmBenchのASRを16.00%に抑えつつGSM8Kは50.34を達成し、アブレーションとしてDisjoint処理を除いた場合にはASRが63.00%まで悪化することも示されている。[^7]

限界として、①排他化（Disjoint）はゼロサム的な処理であり、SafetyもUtilityも同一座標で改善できる可能性を原理的に排除してしまう、②「コンフリクトを避ける」という防衛的な発想にとどまり、両者を同時に最大化する積極的最適化ではない、という2点が挙げられる。LED-Mergingの問題意識はSST-Mergeと非常に近く、「どのニューロンが衝突源か」を扱う点で共通するが、SST-Mergeは「どの更新方向が安全性効率的か」というレイリー商最大化の観点から方向選択を行う点で異なり、安全ニューロンと有用ニューロンの衝突を直接的に処理するアプローチと、比率最適化によって間接的に衝突を回避するアプローチという対比が成立する。

####  SafeMERGE（Djuhera et al., ACL Findings 2026, arXiv 2025）[^8]

既存の課題として、モデルの全層を均一にマージすると、安全性を主に担う特定の層の表現がUtilityタスクによって上書きされてしまう点が挙げられる。解決策として、各層が安全性にどの程度寄与しているかを、安全アライメント済みの部分空間 \(V_i\) を構築したうえでコサイン類似度によって定量化し、安全でない層のみを特定して選択的にマージする層別選択的マージフレームワークを提案した。[^8]

実験ではLlama-2-7B-Chat、Llama-3.1-8B-Instruct、Qwen-2/2.5-7Bを対象に、GSM8K、PubMedQA、TeleData、TeleQnA、TSpecLLM、DirectHarm、HexPhiで評価を行い、Llama-3.1のGSM8Kでベースラインの78.24／DirectHarmの28.30に対し、コサイン類似度選択を用いた場合GSM8Kは78.50に維持されつつDirectHarmは8.80まで低減されることを報告している。Qwen-2でもGSM8Kが70.13から72.90に、DirectHarmが25.30から8.20に改善されている。[^8]

限界として、①層単位の判断にとどまり、パラメータ単位の精細な制御ができない、②どの層が安全性を担うかの基準がヒューリスティックであり理論的な最適性の保証がない、③ファインチューニングで失われた安全性の回復を目的としており、本研究のように新たな安全パッチを外科的に注入するシナリオとは前提が異なる、という3点が挙げられる。SafeMERGEとSST-Mergeはともに「安全性を保ちながら有用性を残す」ことを狙う点で共通するが、SafeMERGEは層レベルでのコサイン類似度に基づく選択的マージであるのに対し、SST-Mergeは分布ごとのFisher比を用いたより一般的な方向・座標レベルの部分空間選択という点で、選択粒度が本質的に異なる。

####  AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints（Wang et al., arXiv 2025）[^9]

既存の課題として、線形マージやタスクベクトルマージは損失（loss）の値自体は維持できても、RLHF等で獲得したアライメントを密かに破壊してしまうことがある点が指摘される。解決策として、FIMの幾何学的な等高線（ロス地形の等値面）を「これ以上越えてはいけない制約」として導入し、この制約を満たしながらアライメントを保護するFIM-guided Geometric Constraint Mergingを構築した。モデル融合を「すでにアラインされたベースモデルの周りでの制約付き最適化問題」として定式化する点が特徴である。[^9]

実験ではLLaMA-3、Mistral、Qwen、Phi、Gemma系のモデルを対象に、毒性、拒否応答率、Alignment Quotient Index（AQI）、LLM-as-a-Judge、指示追従・推論の有用性指標を用いて評価が行われ、SafeMergeやMergeAlignが同程度の毒性・拒否応答率を示す場合でも、AlignMergeはalignment subspace driftをより小さく保ち、AQIの安定性が高いことが報告されている。[^9]

限界として、①「アライメントを壊さない」という消極的な制約にとどまり、SafetyとUtilityを同時に最大化する積極的な最適化ではない、②SafetyのGainをどの方向で得るかという明確な基準を持たず、単なる保護機構にとどまる、という2点が指摘される。10本の先行研究の中でAlignMergeはSST-Mergeに最も近い問題設定を持つ論文の一つであり、Fisher幾何上でalignment-sensitive subspaceを推定し安全性を明示的に守りながらマージするという枠組みは、SST-MergeのGEVPによる部分空間選択と強い親和性を持つ。両者の違いは、AlignMergeが「alignment subspaceを守る」という保護（保存）志向であるのに対し、SST-Mergeは「安全性効率の高いパッチ成分だけを積極的に注入する」という獲得（配備）志向である点にある。

### 2.4 フェーズ4：実用制約への適応期

####  Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs（Wang et al., arXiv 2026）[^10]

既存の課題として、FIMの計算には元の学習データが必要であるが、実運用ではデータが非公開（Data-Free）であることが多く、従来のFIMベース手法は実用が困難である。さらに、長文推論能力（long-to-short reasoning）がマージ後に喪失しやすいという課題も存在する。解決策として、ランダムトークン列（擬似テキスト）から入力を生成し、データを用いずに対角FIMを近似する手法を導入したうえで、層ごとに適応的にマージ比率を変える手法（FIM-Merging、FIM-TIES）を提案した。[^10]

実験ではQwen2.5-Math-7B、DeepSeek-R1-Distill-Qwen-7Bおよび1.5B系モデルを対象に、GSM8K、MATH500、Minerva Math、OlympiadBench、CollegeMath、AIME24で評価を行い、7BモデルにおいてMATH500で90.2を達成し、比較対象のACM-TIES（84.0）を+6.2上回った。GSM8Kでは92.2とACM-TIESとほぼ同等の性能を維持しつつ、応答長はlong-CoTに対して92.6%削減されたことが報告されている。[^10]

限界として、①近似手法の妥当性、特にFisher比のランキング保存性が理論的に保証されていない、②Data-Freeな近似が明確な最適化目標（GEVPのような）と接続されておらずヒューリスティックの域を出ない、という2点が挙げられる。データフリーかつFisherベースであるという意味で、本論文はSST-Mergeの実用的variant（Data-Free SST）に最も近い先行研究であるが、対象問題がlong-to-short reasoningであり、SST-Mergeのようにbenign／harmfulの二分布を対立させる安全性問題ではない点、また層単位（layer-wise）の粒度にとどまりパラメータ単位（element-wise）のステアリングを行わない点で異なる。

## 3. 先行研究の比較サマリー

### 3.1 手法特性の比較マトリクス

| 論文 | FIM活用法 | Safety-Utility同時最適化 | Data-Free対応 | 理論的最適性 |
|---|---|---|---|---|
| NeurIPS 2022（FWA）[^1] | 重要度重み付け | ✗ | ✗ | △（ベイズ近似） |
| ICLR 2024（UGM）[^2] | 勾配整合性 | ✗ | ✗ | △ |
| LREC 2024（Mask Nodes）[^3] | マスク生成 | ✗ | ✗ | ✗（ヒューリスティック） |
| OpenReview（DRIFT-MEDIAN）[^4] | 外れ値耐性 | ✗ | ✗ | △ |
| NAACL 2025（DF-Merge）[^5] | 自動重み探索 | ✗ | ✗ | △（BO保証） |
| arXiv 2024（MergeAlign）[^6] | なし（ベクトル分離） | △（線形のみ） | △ | ✗ |
| ACL 2025（LED-Merging）[^7] | なし | △（排他的回避） | ✗ | ✗ |
| arXiv 2025（SafeMERGE）[^8] | 層別重要度 | △（保護のみ） | ✗ | ✗ |
| arXiv 2025（AlignMerge）[^9] | 制約条件 | △（保護のみ） | △ | △ |
| arXiv 2026（Data-Free FIM-Merging）[^10] | 近似FIM | ✗ | ✓ | ✗ |
| **SST-Merge（提案）** | **デュアルFIM（コスト/利益）** | **✓（GEVP最適化）** | **✓（Data-Free SST-V）** | **✓（GEVP保証）** |

この整理から、既存研究群はいずれもSafety-Utilityの「同時最適化」「Data-Free対応」「理論的最適性の保証」の3条件を全て満たす手法を提示していないことが明確になる。特にFisher活用系（〜）は単一タスク空間の最適化にとどまり、Safety系（〜）は保護・回避志向の消極的定式化にとどまる。SST-MergeはこれらのギャップをGEVPという単一の理論的枠組みで統一的に埋める点に新規性の主張根拠がある。[^5][^9][^1][^6]

### 3.2 実験設定・主要結果の比較

| # | 論文 | 対象モデル | 主要ベンチマーク | 比較ベースライン | 主な結果 |
|---|---|---|---|---|---|
| 1 | Fisher-Weighted Averaging[^1] | BERT, RoBERTa, ViT | GLUE, ImageNet-A/R/Sketch/V2/ObjectNet | Isotropic merging, Output ensemble | Fisher mergingは単純平均を上回り出力アンサンブルに近い性能。推論コストを5分の1に削減。 |
| 2 | Uncertainty-Based Gradient Matching[^2] | RoBERTa, ViT, GPT-2, GPT-J, Flan-T5 | 感情分析・画像分類・毒性/幻覚除去 | Task Arithmetic, Averaging, Fisher Averaging, RegMean, TIES | RoBERTa感情分析でTA比91.8→94.5、単純平均比94.7→96.6。 |
| 3 | Fisher Mask Nodes[^3] | BERT-base/large/tiny, RoBERTa | GLUE 6タスク | Simple Averaging, Fisher-Weighted Averaging | RoBERTaで+6.5、BERT-baseで+4.0。計算は57.4〜321.7倍高速。 |
| 4 | DRIFT-MEDIAN[^4] | GPT-2, Llama-3.1-8B, Llama-3.2-3B, Llama-2-7B, CLIP | GLUE, coding, math, multilingual, safety, vision | Averaging, TA, TIES, DARE, AdaMerging, Fisher, PCB | GPT-2 GLUEでPRR最良ベースライン比+1.9。8視覚タスクでも改善。 |
| 5 | DF-Merge[^5] | T5-base, T5-large | PAWS, QASC, QuaRTz, Story Cloze, WikiQA, Winogrande | Averaging, Fisher Merging, TA, DARE, TIES | T5-base平均78.14（DARE比+4.48）、T5-large平均83.59（TA比+1.73）。 |
| 6 | MergeAlign[^6] | Llama-3-8B系ドメイン専門モデル | Medicine, Finance, HH-Red Team, BeaverTails, GSM8K | ORPO, DPO, Slerp, Full Model Interpolation | Medicine 61.33、BeaverTails 99.67。Slerpはalignmentで約10%劣化。 |
| 7 | LED-Merging[^7] | Mistral-7B, Llama-3-8B, Llama2/WizardLM-13B | HarmBench, SORRY-Bench, GSM8K, MATH, MBPP, HumanEval-Pack | Task Arithmetic, TIES, Model Stock, Breadcrumbs | Llama-3-8BでHarmBench安全性31.4%改善、GSM8K 52.39維持。Disjointなしでは ASR 63.00%に悪化。 |
| 8 | SafeMERGE[^8] | Llama-2-7B-Chat, Llama-3.1-8B-Instruct, Qwen-2/2.5-7B | GSM8K, PubMedQA, TeleData等, DirectHarm, HexPhi | SafeInstruct, RESTA, SafeLoRA, Linear, DARE-Linear, TIES | Llama-3.1でGSM8K 78.50維持、DirectHarm 28.30→8.80。 |
| 9 | AlignMerge[^9] | LLaMA-3, Mistral, Qwen, Phi, Gemma系 | toxicity, refusal, AQI, LLM-as-a-Judge, utility | SafeMerge, MergeAlign, SALSA, Euclidean/Layer-wise interpolation | alignment subspace driftが小さくAQI安定性が高い。 |
| 10 | Data-Free FIM-Merging[^10] | Qwen2.5-Math-7B, DeepSeek-R1-Distill-Qwen系 | GSM8K, MATH500, Minerva Math, OlympiadBench, CollegeMath, AIME24 | Task Arithmetic, TIES, Sens-Merging, ACM-TA/TIES | MATH500で90.2（ACM-TIES比+6.2）。応答長92.6%削減。 |

## 4. SST-Mergeの新規性と差別化戦略

上記の分析を踏まえると、SST-Mergeの新規性は個々の要素技術（Fisher情報の利用、対角近似、パラメータ単位の選択、安全性と有用性のトレードオフ制御、Data-Free化）のいずれについても単独では新規ではなく、これらを「utility tax制約下でのsafety-sensitive energy最大化」という単一の一般化固有値問題（GEVP）に統一的に定式化した点にある。この統一的定式化により、LED-Mergingのような排他的（ゼロサム）分離処理や、SafeMERGE・AlignMergeのような消極的な保護制約とは異なり、「Safetyの獲得」と「Utilityの保存」を単一の比率最大化問題として同時に扱うことが可能になる。[^3][^7][^8][^9][^1][^6][^10]

想定される査読上の批判として、DRIFT-MEDIANが実際に受けた「既存手法の組み合わせにすぎない」という指摘がSST-Mergeにも向けられる可能性が高い。これに対する対抗戦略としては、(1) Theorem 1によるGEVPへの帰着という理論的貢献を、単なるヒューリスティックの組み合わせと明確に区別して提示すること、(2) AlignMergeやLED-Mergingなど問題設定が近い手法との定量比較において、パレートAUCなど定量指標での優位性を示すこと、(3) Data-Free SST-Vが、単なる重み絶対値比率（SST-M）や、Wang et al.のような層単位のランダムトークンFIM近似に対して、パラメータ単位でのより高い分解能を提供することを実証的に裏付けること、が有効と考えられる。[^4][^7][^9][^10]

## 参考文献

 Matena, M. S.; and Raffel, C. A. 2022. Merging Models with Fisher-Weighted Averaging. In NeurIPS.[^1]

 Daheim, N.; Möllenhoff, T.; Ponti, E.; Gurevych, I.; and Khan, M. E. 2024. Model Merging by Uncertainty-Based Gradient Matching. In ICLR (arXiv:2310.12808).[^2]

 Thennal, D. K.; Nathan, G.; and Suchithra, M. S. 2024. Fisher Mask Nodes for Language Model Merging. In LREC-COLING 2024.[^3]

 Baban, G.; and et al. 2025/2026. Task-Aware Model Merging via Fisher-Weighted Median (DRIFT-MEDIAN). Under review, ICLR 2026 (OpenReview).[^4]

 Lee, S.; Liu, J.; Wang, Q.; Wang, J.; Cai, X.; and Wu, Y. 2025. Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In NAACL 2025, pp. 4923–4935.[^5]

 Hammoud, H. A. A.; and et al. 2024. MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.[^6]

 Ma, Q.; and et al. 2025. LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In ACL 2025.[^7]

 Djuhera, A. N. D.; Kadhe, S. R.; Ahmed, F.; Zawad, S.; and Boche, H. 2025/2026. SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging. Findings of ACL 2026 (arXiv:2503.17239).[^8]

 Wang, Z.; and et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.[^9]

 Wang, Z.; and et al. 2026. Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.[^10]

 Ilharco, G.; Wortsman, M.; Sameer, M. T.; and et al. 2023. Editing Models with Task Arithmetic. In ICLR (arXiv:2212.04089).[^11]

 Yadav, P.; Tam, D.; Choshen, L.; Raffel, C.; and Bansal, M. 2023. TIES-Merging: Resolving Interference When Merging Models. In NeurIPS (arXiv:2306.01708).[^12]

 Yu, L.; Yu, B.; Yu, H.; Huang, F.; and et al. 2024. Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch (DARE). arXiv:2311.03099.[^13]

 Deep, P. T.; Bhardwaj, R.; and Poria, S. 2024. DELLA-Merging: Reducing Interference in Model Merging Through Magnitude-Based Sampling. arXiv:2406.11617.[^14]

 Wortsman, M.; Ilharco, G.; Gadre, S. Y.; and et al. 2022. Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Accuracy Without Increasing Inference Time. In ICML.[^15]

 Hammoud, H. A. A.; and et al. 2024. One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. arXiv:2406.07542.[^16]

 Tam, D.; and et al. 2024. Merging Models in the Geometric Space. In ICLR.[^17]

 Kirkpatrick, J.; and et al. 2017. Overcoming Catastrophic Forgetting in Neural Networks. PNAS 114(13):3521–3526.[^18]

 Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In NAACL.[^19]

 Touvron, H.; and et al. 2023. Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.[^20]

 Zou, A.; Wang, Z.; Kolter, J. Z.; and Fredrikson, M. 2023. Universal and Transferable Adversarial Attacks on Aligned Language Models. arXiv:2307.15043.[^21]

 Wei, A.; Haghtalab, N.; and Steinhardt, J. 2024. Jailbroken: How Does LLM Safety Training Fail? In ICLR.[^22]

 Huang, Y.; Sun, L.; and et al. 2024. TrustLLM: A Benchmark for Trustworthy Large Language Models. arXiv:2401.05561.[^23][^24]

 Ji, J.; and et al. 2024. BeaverTails: Towards Improved Safety Alignment in Large Language Models. arXiv:2307.04657.[^25]

 Mazeika, M.; and et al. 2024. HarmBench: A Standardized Benchmark for Evaluating and Red-Teaming Safety of Language Models. arXiv:2402.04249.[^26]

 Chao, P.; and et al. 2024. JailbreakBench: An Open-Source Benchmark for Evaluating Jailbreak Attacks and Defenses on LLMs. arXiv:2403.04789.[^27]

 Souly, A.; and et al. 2024. StrongReject: A Benchmarking Framework for Evaluating Harmful Prompt Detection and Prevention. arXiv:2404.15689.[^28]

 Jiang, Y.; and et al. 2024. WildJailbreak: A Multi-Task Dataset for Evaluation of Jailbreak Robustness and Alignment. arXiv:2406.12903.[^29]

 Röttger, P.; and et al. 2023. XSTest: A Test Suite for Identifying Exaggerated Safety Refusals in Large Language Models. arXiv:2308.06999.[^30]

---

## References

1. [[2212.04089] Editing Models with Task Arithmetic](https://arxiv.org/abs/2212.04089) - G Ilharco 著 · 2022 · 被引用数: 1663 — We show that these task vectors can be modified and combined toget...

2. [Efficient Model Editing with Task Vector Bases](https://arxiv.org/html/2502.01015v1)

3. [Task Arithmetic in the Tangent Space: Improved Editing of ...](https://proceedings.neurips.cc/paper_files/paper/2023/file/d28077e5ff52034cd35b4aa15320caea-Paper-Conference.pdf)

4. [[PDF] POLITECNICO DI TORINO Repository ISTITUZIONALE](https://iris.polito.it/retrieve/4f47c543-21c0-4bd5-b6df-348d076bbb59/7582_Efficient_Model_Editing_w-8.pdf)

5. [On Fairness of Task Arithmetic: The Role of Task Vectors](https://openreview.net/attachment?id=nAb0PEDDbS&name=pdf)

6. [[논문 퀵 리뷰] Editing Models with Task Arithmetic](https://liner.com/ko/review/editing-models-with-task-arithmetic) - 이 ICLR 2022 논문에 관하여, 이 리뷰는 신경망 동작을 유도하기 위해 가중치 벡터에 대한 task arithmetic을 사용하여 모델을 편집하는 방법을 요약합니다.

7. [Efficient Model Editing with Task-localized Sparse Fine- ...](https://iclr.cc/media/iclr-2025/Slides/29556.pdf)

8. [TIES-Merging: Resolving Interference When Merging Models](https://arxiv.org/abs/2306.01708) - P Yadav 著 · 2023 · 被引用数: 1081 — View a PDF of the paper titled TIES-Merging: Resolving Interference ...

9. [[Re] TIES-Merging: Resolving Interference When ...](https://openreview.net/pdf/3fc3c3e3f7e4b23847275d30ccf4dc715a9fbf97.pdf)

10. [Task Arithmetic: Model Editing Paradigm](https://www.emergentmind.com/topics/task-arithmetic-ta) - Task Arithmetic abstracts task-specific model changes as vectors, enabling efficient multi-task lear...

11. [【論文まとめ】Editing Models with Task Arithmetic](https://yuta0306.github.io/Editing-Models-with-Task-Arithmetic) - 概要. Task vectorに基づいたニューラルネットワークの編集の新たなパラダイムを提案． element-wiseにモデルの重みをベクトル演算する ...

12. [000](https://openreview.net/pdf/71da4f984b5c3b8bb4c748262ab763e04a35a535.pdf)

13. [[PDF] TIES-Merging: Resolving Interference When Merging Models | Semantic Scholar](https://www.semanticscholar.org/paper/TIES-Merging:-Resolving-Interference-When-Merging-Yadav-Tam/2651f0179874bd010f58d2c9fa7d118807c80977) - This paper proposes a method, TRIM, ELECT SIGN&MERGE (TIES-Merging), which introduces three novel st...

14. [TIES-Merging - AI Wiki](https://aiwiki.ai/wiki/ties_merging) - TIES-Merging is a training-free model merging method that combines several models fine-tuned from a ...

15. [[PDF] Combining Domain and Alignment Vectors to ... - OpenReview](https://arxiv.org/pdf/2411.06824v2.pdf)

16. [Language Models are Super Mario: Absorbing Abilities ...](https://arxiv.org/abs/2311.03099) - L Yu 著 · 2023 · 被引用数: 774 — Language Models are Super Mario: Absorbing Abilities from Homologous Mod...

17. [MergeLM/README.md at main · yule-BUAA ...](https://github.com/yule-BUAA/MergeLM/blob/main/README.md) - This repository is built for the paper Language Models are Super Mario: Absorbing Abilities from Hom...

18. [SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging](https://aclanthology.org/2026.findings-acl.1761/) - Aladin Djuhera, Swanand Ravindra Kadhe, Farhan Ahmed, Syed Zawad, Holger Boche. Findings of the Asso...

19. [Purifying Finetuning Data to Preserve LLM Safety Alignment](https://ar5iv.labs.arxiv.org/html/2507.18631) - With rapid advancement and increasing accessibility of LLMs, fine-tuning aligned models has become a...

20. [dare.md](https://huggingface.co/datasets/tbukuai/hf-papers-wiki/raw/0961e6ca813cae3a9d6c621d07b72dba0972c985/sources/dare.md)

21. [SafeMERGE: Preserving Safety Alignment in Fine-Tuned ...](https://arxiv.org/html/2503.17239v1)

22. [論文紹介: Language Models are Super Mario: Absorbing ...](https://qiita.com/hiyoko1729/items/0b3482a3528d7d3347c4) - DAREを既存のモデルマージ手法の前処理として利用することで、パラメータの干渉を軽減し、マージの性能を向上させることができます。 例えば、Task ...

23. [Paper Review: Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free…](https://medium.com/@kimseongu15/language-models-are-super-mario-absorbing-abilities-from-homologous-models-as-a-free-lunch-review-943c8d04a488) - 1. Intro

24. [SafeMERGE/README.md at main · aladinD/SafeMERGE](https://github.com/aladinD/SafeMERGE/blob/main/README.md) - Code for SafeMERGE (ICLR 2025). Contribute to aladinD/SafeMERGE development by creating an account o...

25. [Language models are super mario: absorbing abilities from ...](https://dl.acm.org/doi/10.5555/3692070.3694452) - L Yu 著 · 2024 · 被引用数: 773 — ... DARE can effortlessly eliminate 90% or even 99% of them; (2) DARE ca...

26. [Safety-Preserving Fine-Tuning (SPF)](https://www.emergentmind.com/topics/safety-preserving-fine-tuning-spf) - SPF adapts safety-aligned language models to downstream tasks while preserving refusal behavior and ...

27. [DELLA-Merging: Reducing Interference in Model ...](https://arxiv.org/abs/2406.11617) - PT Deep 著 · 2024 · 被引用数: 80 — In this paper, we propose a new model merging technique, Drop and rEsc...

28. [GitHub - martyn/safetensors-merge-supermario: Merge safetensor files using the technique described in "Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch"](https://github.com/martyn/safetensors-merge-supermario) - Merge safetensor files using the technique described in "Language Models are Super Mario: Absorbing ...

29. [Language Models as Super Mario: Merge AI Skills Without Retraining](https://www.youtube.com/watch?v=sGnu5RaDBqY) - This episode explores a groundbreaking paper on language models that introduces a novel technique ca...

30. [Fine-Tuning 후 Safety Alignment를 보존하는 선택적 Layer- ...](https://ai-paper-delta.vercel.app/ko/papers/2503.17239)

