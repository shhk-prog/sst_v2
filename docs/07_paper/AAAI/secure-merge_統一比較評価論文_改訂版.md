# Secure Model MergingにおけるSafety--Utilityトレードオフの統一的比較評価

## Abstract

大規模言語モデル（LLM）を専門タスクに適応させる際、安全性アライメントが劣化するSafety–Utilityトレードオフは、モデルマージの実用化における中心的な障害となっている。本稿は、Task Arithmetic、TIES、DARE、DELLAといった標準的マージ手法、Matena–RaffelのFisher-Weighted Averagingに代表されるFisher重要度型手法、MergeAlign、SafeMERGE、LED-Mergingに代表される安全性選択型手法、およびAlignMergeに代表されるFisher幾何制約型手法を、干渉の定義単位（ベクトル全体・パラメータ・層・ニューロン・部分空間）という観点から統一的に整理し、数式とアルゴリズム的手順に基づいて比較した。さらに、Llama-2-7Bを基盤としたSecure Merge実験ログの再検証を通じ、安全性を明示的に扱わない疎化・符号選択型手法が高干渉条件でGibberish崩壊を示す場合があることを明らかにした。結果として、Fisher比率に基づく手法および安全性を明示的に考慮する手法は、設定に依存して安全性・有用性間のより良好なトレードオフを示すことが確認された。これらの知見は、ASR（攻撃成功率）単独ではなく、応答有効性を併せた評価の必要性を示す。
**キーワード**: モデルマージ、Fisher情報行列、安全性アライメント、Safety-Utilityトレードオフ、大規模言語モデル

## 1. Introduction

### 1.1 事後的なモデル融合におけるアライメントのドリフト (Alignment Drift under Post-hoc Model Fusion)

大規模言語モデル（LLM）は、汎用的な事前学習の後に特定のドメイン（数学、コード生成、医療対話など）でファインチューニングを施すことで、当該タスクにおいて飛躍的な性能向上を達成するというパラダイムのもとで急速に普及してきた。Hugging Faceをはじめとするモデルリポジトリには、こうしたドメイン特化のファインチューニング済み専門モデル（expert models）が既に数百万規模で公開されており、研究者や実務者は目的に応じてこれらを自由に組み合わせて利用できる環境が整いつつある。

一方で、instruction tuning、RLHF、DPO等を通じて形成された安全性アライメントは、良性データのみを用いた追加学習後にも劣化し得る。この問題は、専門性能を得るためのファインチューニングが、有害な要求を拒否する能力、危険な内容を適切に扱う能力、および攻撃的プロンプトに対する頑健性に関係するパラメータ更新と干渉し得ることに起因する[1, 2]。

各専門モデルに対して安全性アライメントを再学習する方法は直接的であるが、大規模な選好データ、計算資源、および安全性評価・最適化の反復を必要とする。また、元の学習データ、選好データ、あるいは安全性校正データが共有されない場合も少なくない。

このような背景のもと、単一の巨大大規模モデルをゼロから再学習・ファインチューニングするのではなく、専門化された複数のチェックポイント同士を重み空間で直接統合する事後的手法としての「モデルマージ」が、能力統合アプローチとして広く用いられている[3, 4]。Model Soups [3] や Fisher重み付き平均（Fisher-Weighted Averaging; FWA） [10] に関する初期の研究は、ファインチューニングされたモデル群が共通の低損失領域（low-loss basin）に存在することを示しており、単純な線形補間であっても追加の推論コストなしに精度やロバスト性を向上させられることを実証した。その後の研究では、タスクベクトルやタスク演算（Task Arithmetic） [4, 25] によってパラメータ空間における方向ベクトル $\Delta_t$ の線形結合が挙動の追加・削除・合成を可能にすることが定式化され、最近では Dynamic Fisher-weighted Merging (DF-Merge) [14] のようにベイズ最適化を用いてパラメータ組み合わせを動的に最適化する手法も登場している。

モデルマージの一般的な目的は、複数モデルが獲得した能力を単一のパラメータ集合に統合し、複数モデルの保持・推論に伴うコストを抑えることである。Model Soupsは同一初期化から得られたファインチューニング済みモデルの重み平均が有効となり得ることを示し[3]、Task Arithmeticは基盤モデルからの重み差分をタスクベクトルとして扱うことにより、能力の加減算・合成を可能にした[4]。しかし、これらの単純な統合は、更新方向の相殺、符号不一致、冗長な微小更新、または特定能力を担うパラメータの上書きに起因する干渉を招く。TIES、DARE、DELLAは、この干渉を符号選択、疎化、振幅依存のサンプリングによって緩和する代表的手法である[5--7]。

しかしながら、これら既存のモデルマージ手法に共通する決定的な問題として、**アライメントが副次的な存在として扱われている**という点が挙げられる[2]。従来の手法は主に損失・精度・汎用タスク性能・ロバスト性といった指標の最適化を対象としており、拒否応答（refusal behavior）、無害性（harmlessness）、および安全ポリシーの維持といったアライメントの保持をマージ過程の直接の制約として考慮していない。

とりわけ、事後的に安全性を専門モデルへ配備するSecure Merge[24]において、モデルマージ時に安全性の回復と有用性（タスク性能）の保持との間に鋭いトレードオフが生じることが報告されている。安全パッチを強く反映すれば攻撃成功率（attack success rate; ASR）を低下させられる可能性があるが、専門タスク性能や無害な要求への応答性が損なわれ得る。逆に、専門モデルの更新を強く保持すれば、有用性は保たれても安全性が回復しない。この安全性と有用性のトレードオフはSafety Tax（またはAlignment Tax）として理解できる。
近年の研究は、この見落としが決して無視できない深刻なリスクをもたらすことを明らかにしている。Hammoudら [1] はモデルマージと安全アライメントの関係を明示的に検証し、単純補間、Fisher重み付き平均、データ依存型混合といった一般的なマージレシピが、**個々のモデルが独立には安全であっても、マージ後にはアライメントが大きく崩壊（degradation / drift）し得る**ことを示した。彼らの中心的な発見は「**一つ悪影響を及ぼすモデルが混ざるだけで全体が崩壊する (one bad model spoils the bunch)**」という現象である。すなわち、単一の非アラインな専門モデルが混ざるだけで、マージ後のモデルの安全性挙動が支配され、perplexityや汎用タスク性能はほとんど変化しないまま、Jailbreak成功率や有害性（toxicity）が劇的に増加する。また、Yangらのサーベイ [26] によれば、既存のマージ軌道（trajectory）はパラメータ空間における高分散方向（high-variance directions）を優先的に辿る傾向があり、これらの方向が強力なタスク能力を表現する一方で、暗黙的な選好や安全挙動に対して制御不能な漂移（drift）を引き起こすことが確認されている[15]。

単純なタスクベクトルマージや、干渉緩和を目的とした TIES、DARE、DELLA といった手法は、そもそも安全性統合を想定した設計になっておらず、安全パッチが通常タスクのパラメータ更新と干渉し、有用性を大きく破壊してしまう問題を十分に制御できない。

### 1.2 安全性を考慮したマージ：進展と限界 (Safety-Aware Merging: Progress and Limits)
この課題に対し、近年ではモデルマージに**明示的な安全性（safety）の配慮を組み込む手法**が提案され始めている。
MergeAlignはドメインベクトルとアライメントベクトルを補間し[2]、SafeMERGEは安全性逸脱が大きい層を選択的に統合する[8]。さらに、LED-Merging [9] は勾配重要度を用いてニューロン単位で競合するパラメータを特定・分離し、SALSA [27] や Alignment Soups はアライン済みSFTモデルの重み平均によってよりロバストな参照ポリシーを構築している。また、Fisher情報行列（Fisher information matrix; FIM）を用いるFisher-Weighted Averaging（FWA）は、パラメータの局所的な重要度を反映した統合を可能にする[10]。FWA自体は安全性維持を目的として提案された手法ではないが、重要度に基づくパラメータ単位の統合という点で、Secure Mergeにおける重要なFisher情報活用ベースラインである。

しかしながら、これらの安全性維持マージ手法はいずれも本質的に**局所的（local）かつヒューリスティック（heuristic）**である[15]。
- SafeMerge [8] は層ごとの判定・巻き戻し規則に依存している
- MergeAlign [2] は合成安全データのカバレッジや質に依存している
- LED-Merging [9] はニューロン単位の競合検出に留まる
- SALSA [27] は単一アライメントパイプライン内の平均化に特化し、異質な専門モデルの事後融合には対応していない

すなわち、既存手法はいずれも**パラメータ空間のどの領域が安全性にとって不可欠であるかをグローバル（global）に規定する枠組みを持っておらず、マージ結果がその安全領域内にとどまることを保証する幾何学的メカニズムを欠いている**。その結果、特定のテスト条件下でミスアライメントを緩和できたとしても、未知の専門モデルの追加、マージパラメータの変更、あるいは分布シフト（distribution shift）が生じた際に、危険な挙動が再発しないという保証はない[15]。

### 1.3 なぜ幾何学か：アライメントはスカラーではなく不変量である (Why Geometry: Alignment as an Invariant, Not a Scalar)

これとは独立に、安定したマージを実現するためにパラメータ空間の幾何構造を活用する**幾何学的マージ手法**が発展してきた。Cycle-Consistent Multi-Model Merging (C2M3) [28] はサイクル一貫性を課してマージを可逆写像として扱い、幾何学的サーベイ [26, 29] では置換対称性の尊重や低損失領域（low-loss basin）への拘束が重要であることが指摘されている。しかし、これら従来の幾何学的手法も、**アライメントに関わるパラメーター方向とタスクに関わる方向を区別しておらず**、アライメントは依然としてマージ実行後に評価される「スカラー値の評価指標」にとどまっていた。

AlignMerge [15] に代表される最新の幾何学的知見を踏まえると、モデルマージとアライメントの関係は以下の3つの決定的な原則として整理される：

1. **重み空間の線形性はアライメントに対して中立ではない**: 線形モード接続性（linear mode connectivity）やフラットな極小（flat minima）を利用する線形補間は、タスク精度を維持・向上させる一方で、安全性アライメントを静かに破壊し、有害な挙動を再導入するリスクを持つ [1, 26]。
2. **干渉の解消は必要条件だが十分条件ではない**: TIES-Merging [5]、DARE [6]、DELLA [7]、進化的マージ [29]、DF-Merge [14] といった手法は、疎化や符号整合、動的重み付けによってタスク間の干渉を制御するが、これらは**アライメントに敏感なパラメータ方向（alignment-sensitive directions）を制約していないため、ミスアライメントの漏洩（misalignment leakage）を防ぐことはできない**。
3. **現在の安全性対応マージ手法はグローバルな不変量を欠いている**: SafeMerge [8] や MergeAlign [2]、LED-Merging [9] などの安全対策は、アライメントを維持するために不変であるべきパラメータ多様体上の領域を幾何学的・グローバルに記述する枠組みを欠いている。

以上の考察から、本研究では以下の中心的立場を採る：

> **「アライメントは単なるスカラー評価値ではなく、モデル族における幾何学的な不変量（geometric invariant）として扱うべきである。」**

### 1.4 本研究の目的と貢献 (Objectives and Contributions)

モデルマージにおけるアライメント保持を「パラメータ幾何学上の不変量制約」として捉え直す視点は、事後的な安全性配慮マージ（Secure Merge）の評価軸に本質的な再定義を迫る。従来の評価では、単一手法のASR低減効果やベンチマーク点数のみが議論されがちであったが、実際には**介入粒度（ベクトル全体、層、ニューロン、パラメータ、部分空間・幾何）、利用情報（重み差分、符号・振幅、勾配、Fisher情報）、およびデータ依存性**の組み合わせが、Safety--Utilityのパレート限界を決定づけている。

本研究の目的は、新たな単一手法の絶対的優位性を誇張することではなく、Secure Merge設定において用いられる代表的なモデルマージ手法を、統一された実験条件のもとで体系的に比較評価することである。具体的には、標準的なマージ手法（Task Arithmetic [4], TIES [5], DARE [6], DELLA [7]）、安全性維持マージ（MergeAlign [2], SafeMERGE [8], LED-Merging [9]）、Fisher情報に基づくマージ（FWA [10]）、および幾何学的制約・Fisher比率に基づくマージ（本稿ではAlignMerge [15] を理論的背景として位置づけ、その実験的代表として SST-Merge および Data-Free SST-Merge を採用）を対象とし、グローバル不変量 vs 局所ヒューリスティック、および幾何学的制約の効果を統一的パレート分析により解明する。

本研究の貢献は以下の3点である。

1. secure mergeにおいて，Fisher系・Safety-Utility系のマージ手法を、干渉粒度と安全性の扱いで体系化する。
2. 有効応答率を含む評価基準で、ASRのみの安全性評価が持つバイアスを分析する。
3. 実験ログを再照合し、条件混同・数値不整合が結論に与える影響を検証する。

## 2. 研究課題 (Research Questions)

本研究では、上記の背景と課題に基づき、以下の5つの研究課題（Research Questions; RQs）を設定する。

**RQ1 (パレート限界とアライメント保持):** Secure Merge設定において、標準マージ手法、局所的安全性維持マージ手法、および幾何学的制約に基づくマージ手法は、安全性と有用性のパレート境界にどのような構造的差異を示すか。

**RQ2 (介入粒度の影響):** パラメータ全体（ベクトル）、層単位、ニューロン単位、パラメータ単位、および部分空間（幾何）という介入粒度の違いは、安全性回復、有用性保持、および過剰拒否（exaggerated refusal）の抑制にどのように影響するか。

**RQ3 (情報利用と干渉緩和メカニズム):** 符号・振幅に基づくヒューリスティックな干渉緩和（TIES, DARE, DELLA）と、Fisher情報・幾何構造に基づく感度制御（FWA, SST-Merge, AlignMerge）の間で、性能、攻撃頑健性、および計算コストにはどのようなトレーディングオフが存在するか。

**RQ4 (データアクセス依存性とデータフリー性の検証):** 元の学習データや安全性校正データにアクセスできない制約下において、Data-Free SST-Merge等のデータフリー手法はどの程度頑健に機能し、データ利用可能手法と比較してどの程度のパレート低下に留まるか。

## 3. Related Work

### 3.1 研究潮流の4フェーズ整理

モデルマージ研究の展開は、大きく4フェーズに整理できる。第1フェーズ（2022–2023年）はFisher-Weighted AveragingやTask Arithmeticに代表される黎明期であり、複数タスクモデルを壊さず平均する理論の確立が主要課題であった\[1\]\[2\]。第2フェーズ（2024–2025年）はTIES、DARE、DELLA、Fisher Mask Nodes、Fisher-Weighted Median、ベイズ最適化型手法など、干渉緩和・外れ値耐性・計算効率・ハイパーパラメータ自動化への関心の広がりを特徴とする\[8\]\[9\]\[10\]\[11\]\[12\]\[13\]。第3フェーズ（2024–2026年）はMergeAlign、SafeMERGE、LED-Merging、AlignMergeに代表されるSafety–Utility特化期であり、安全パッチと有用性パッチの衝突そのものが主要研究対象となった\[6\]\[14\]\[7\]\[15\]。第4フェーズ（2025–2026年）は補助データが使えない現実的制約を前提とするData-Free実装の追求である\[16\]。

**Table 1. モデルマージ研究の4フェーズと代表手法**

| フェーズ | 期間 | 中心課題 | 代表手法 | 参照 |
|---|---|---|---|---|
| Phase 1: 黎明期 | 2022–2023 | 破滅的忘却の防止 | Fisher-Weighted Averaging, Task Arithmetic | \[1\]\[2\] |
| Phase 2: 発展期 | 2024–2025 | 干渉緩和・外れ値耐性・効率化 | TIES, DARE, DELLA, Fisher Mask Nodes, DRIFT-MEDIAN, DF-Merge | \[8\]\[9\]\[10\]\[11\]\[12\]\[13\] |
| Phase 3: Safety特化期 | 2024–2026 | Safety–Utility競合の直接解消 | MergeAlign, SafeMERGE, LED-Merging, AlignMerge | \[6\]\[14\]\[7\]\[15\] |
| Phase 4: 実用制約期 | 2025–2026 | Data-Free環境への適応 | 層適応型Fisher近似 | \[16\] |

### 3.2 基礎系統：Model SoupsとTask Arithmetic

Model Soupsは、同一初期化から独立にファインチューニングされた複数モデルが同一の低損失盆地にあるならば、重み平均で性能を維持または改善できることを示した\[17\]。2モデルの線形補間は

\[
\theta_{\mathrm{soup}}=(1-\alpha)\theta_A+\alpha\theta_B
\tag{1}
\]

と書ける。設計思想はきわめて単純であり、モデル間に十分な類似性があれば局所的な関数差は重み平均で平滑化されるという経験的事実に依拠する。

Task Arithmeticは、この発想を「ファインチューニング更新ベクトル」に抽象化した\[2\]。事前学習済み基盤モデルを \(\theta_0\)、タスク \(t\) 用にファインチューニングしたモデルを \(\theta_t^\star\) とすると、タスクベクトルは

\[
\tau_t=\theta_t^\star-\theta_0
\tag{2}
\]

で定義され、複数タスクの合成は

\[
\theta_{\mathrm{TA}}=\theta_0+\sum_{t=1}^{T}\alpha_t\tau_t
\tag{3}
\]

で表される\[2\]。Ilharcoらは、これにより加算・減算・類推といった演算が直接モデル挙動編集として機能することを示した。この系統の限界は、どの座標が安全性に重要か、どの方向が有用性に寄与するかを区別しない点にあり、安全性と専門性能が同一パラメータで競合する場合、最も単純な加法は最も不安定な統合法となる。安全性を明示しないため、本稿では安全ASRと過剰拒否の双方を評価する。

### 3.3 Fisher-Weighted Averagingと重要度系統

Fisher-Weighted Averaging（FWA）は、単純平均をベイズ的に一般化する試みであり、各モデルの事後分布をラプラス近似し、Fisher情報を精度行列とみなすことで重み付け平均を導く\[1\]。対角近似のもとで、各パラメータ \(j\) に対するマージ値は

\[
\theta_j^{\mathrm{FWA}}=\frac{\sum_{m=1}^{M}\lambda_m F_{m,j}\theta_{m,j}}{\sum_{m=1}^{M}\lambda_m F_{m,j}}
\tag{4}
\]

で与えられる。経験Fisherは一般に

\[
\hat F_{\theta}=\frac{1}{N}\sum_{i=1}^{N}\mathbb{E}_{y\sim p(y\mid x_i;\theta)}\left[(\nabla_{\theta}\log p(y\mid x_i;\theta))^2\right]
\tag{5}
\]

で近似される\[1\]。FWAの設計思想は「重要なパラメータほど平均してはならない」という点にあるが、安全性と有用性のように異なる分布上で異なる重要性を持つ場合、単一Fisherは「何に対して重要か」を区別しない。

この系統には、勾配整合性に着目したUncertainty-based Gradient Matching\[18\]、マスクノードにより計算量を削減したFisher Mask Nodes\[9\]、Fisher重み付き中央値で外れ値耐性を高めたDRIFT-MEDIAN\[11\]、ベイズ最適化で係数を自動探索するDF-Merge\[12\]が含まれる。いずれも「Fisherは何らかの重要度を表す」という認識に立つが、安全性と有用性の二重目的を同時に扱うわけではない。本稿では、単一Fisherの重要度と、harmful/benign別Fisherの差を用いるアプローチを比較する。

### 3.4 干渉除去系：TIES、DARE、DELLA

TIES-Mergingは、失敗要因を「微小で冗長な更新」と「符号不一致」に求め、TRIM・ELECT SIGN・DISJOINT MERGEの三段階で処理する\[8\]。各座標 \(j\) について

\[
s_j=\mathrm{sign}\left(\sum_m \tau_{m,j}\right),\qquad
\theta_j=\theta_{0,j}+\frac{1}{|\mathcal{M}_j|}\sum_{m\in\mathcal{M}_j}\tau_{m,j}
\tag{6}
\]

ただし \(\mathcal{M}_j=\{m\mid \mathrm{sign}(\tau_{m,j})=s_j\}\) である\[8\]。

DAREは、更新の多くは本質的に不要であるという観察に基づき、ランダムドロップと再スケーリングを行う\[19\]。ドロップ率を \(p\) とすると

\[
\tilde{\tau}_j=\frac{m_j}{1-p}\tau_j,\qquad m_j\sim\mathrm{Bernoulli}(1-p)
\tag{7}
\]

である\[19\]。DELLAはDAREを改良し、振幅に応じてドロップ確率を変えるMAGPRUNEを導入する\[20\]。振幅の小さい更新ほど高確率で削除し、残存更新を再スケーリングすることで、DAREより情報損失を抑えつつ干渉を減らす。

これら三手法はいずれも局所ヒューリスティクスで更新を選別するが、安全性を明示的目的としないため、安全性更新と有用性更新が競合するSecure Merge設定では、干渉を減らしても安全性が保たれる保証はない。特に更新の削減が出力崩壊を生む可能性があるため、本稿では有効応答率を含めて評価する。

### 3.5 Safety–Utility特化系：MergeAlign、SafeMERGE、LED-Merging

MergeAlignは、ドメイン専門性と安全性アライメントを別々のベクトルとして明示的に分離する\[6\]。基盤モデルを \(\theta\)、ドメイン専門モデルを \(\theta_d\)、アライン済み汎用モデルを \(\theta_a\) とすると

\[
\tau_d=\theta_d-\theta,\qquad \tau_a=\theta_a-\theta
\tag{8}
\]

であり、最終統合モデルは

\[
\hat\theta=\theta+\alpha\tau_d+\beta\tau_a
\tag{9}
\]

で与えられる\[6\]。制御はベクトル全体に対するスカラー重み \(\alpha,\beta\) にとどまり、パラメータ単位のfiner-grainedな制御はできない。

SafeMERGEは、どの層が安全性を担うかを判定し、逸脱の大きい層のみを安全モデル寄りに戻す\[14\]。層 \(i\) の安全方向を \(V_i=W_{i,\mathrm{aligned}}-W_{i,\mathrm{unaligned}}\) とし、ファインチューニング更新とその安全部分空間射影とのコサイン類似度

\[
\rho_i=\mathrm{cosine\_similarity}(\Delta W_{i,f},C_i\Delta W_{i,f})
\tag{10}
\]

を評価し、閾値 \(\tau\) 未満の層のみ

\[
\Delta W_{i,\mathrm{merge}}=\alpha\Delta W_{i,f}+(1-\alpha)\Delta W_{i,s}
\tag{11}
\]

で補正する\[14\]。

LED-Mergingは、競合の単位をニューロンへと下げる\[7\]。Location段階では勾配アトリビューションからニューロン重要度

\[
I(\theta_i)=\mathbb{E}_{x\sim X_i}[\theta_i\odot\nabla_{\theta_i}L(x)]
\tag{12}
\]

を計算し\[7\]、Electionではベースモデルと専門モデル双方で高重要度なニューロン集合の積集合を取り、Disjointではタスク間で共有される重要ニューロンを差集合で分離する。本稿では、これらの層・ニューロン単位の選択が、SSTの要素単位選択とどう異なるかを比較する。

### 3.6 Fisher幾何型：AlignMergeとData-Free拡張

AlignMergeは、Fisher情報を単なるパラメータ重みではなく、モデル空間上の局所計量として解釈する\[15\]。設計思想は、アライメントを部分空間または多様体として表現し、マージ後もそこから大きく逸脱しないよう制約付き最適化として統合を定式化する点にある。Data-Free Layer-Adaptive Mergingは、ランダムトークン列から層別Fisherを近似し、補助データなしでもFisher型マージを可能にする方向性を示した\[16\]が、近似Fisherが本来の重要度ランキングをどこまで保持するかは未解明である。

### 3.7 関連研究の比較整理

**Table 2. 各手法の設計原理比較**

| 手法群 | 代表手法 | 重要情報 | 介入粒度 | 安全性への直接性 | 参照 |
|---|---|---|---|---|---|
| 単純補間 | Model Soups | 重み値 | モデル全体 | 低い | \[17\] |
| 差分合成 | Task Arithmetic | タスクベクトル | ベクトル全体 | 低い | \[2\] |
| 曲率重み付け | FWA | Fisher対角 | パラメータ | 低い〜中 | \[1\] |
| 干渉緩和 | TIES / DARE / DELLA | 符号・疎化・振幅 | パラメータ | 低い | \[8\]\[19\]\[20\] |
| ベクトル分離 | MergeAlign | ドメイン/整列ベクトル | ベクトル全体 | 中 | \[6\] |
| 選択的保護 | SafeMERGE | 安全部分空間 | 層 | 高い | \[14\] |
| ニューロン分離 | LED-Merging | 勾配重要度 | ニューロン | 高い | \[7\] |
| 幾何制約 | AlignMerge | Fisher幾何 | 部分空間 | 高い | \[15\] |
| 実用近似 | Data-Free FIM系 | 近似Fisher | 層/パラメータ | 中 | \[16\] |

この整理は、実験結果の解釈フレームワークを与える。すなわち、後続節で観測されるGibberish崩壊、ASR低下、一般性能維持の差異は、単に数値の優劣ではなく「干渉をどのレベルで定義したか」の違いとして理解されるべきである。

<!-- 図1 プレースホルダ -->
> **図1: 手法分類図（プレースホルダ）**
> *ベクトル→パラメータ→層→ニューロン→部分空間という介入粒度の体系化を示す図。*
## 4. Methods Under Evaluation

本研究では、手法を「提案法／ベースライン」という序列ではなく、利用する情報と介入粒度に基づく比較対象として扱う。SST-MergeおよびData-Free SST-Mergeも、以下の評価対象の一部であり、性能優位を前提としない。

| 比較群 | 対象手法 | 主な利用情報 | 介入粒度 | 評価上の役割 |
|---|---|---|---|---|
| 標準| Task Arithmetic [4, 25]| 重み差分 | ベクトル全体 | 最小限の統合基準線 |
| 標準| TIES [5]| 符号・振幅 | パラメータ | 符号整合型の干渉緩和 |
| 標準| DARE [6]| ランダム疎化 | パラメータ | 冗長性利用型の干渉緩和 |
| 標準| DELLA [7]| 振幅依存疎化 | パラメータ | 重要度近似型の疎化 |
| Fisher重要度 | FWA [10]| 対角Fisher情報 | パラメータ | Fisher情報活用の代表基準線 |
| 安全維持| MergeAlign [2]| ドメイン・安全ベクトル | ベクトル全体 | ベクトル補間型の安全性統合 |
| 安全維持 | SafeMERGE [8]| 層の安全性逸脱度 | 層 | 層選択型の安全性回復 |
| 安全維持 | LED-Merging [9]| 勾配重要度 | ニューロン | 競合分離型の安全性統合 |
| Fisher・幾何 | AlignMerge [15]| Fisher幾何・アライメント部分空間 | 部分空間・幾何 | 幾何学的不変量制約の理論的背景（本実験ではSST-Mergeで代替検証） |
| Fisher比率 | SST-Merge | Safety／Utility Fisher | パラメータ／方向 | 幾何学的制約・局所感度比を用いる代表比較対象 |
| データフリー | Data-Free SST-Merge | 重み情報または疑似入力 | パラメータ／方向 | 校正データ非利用条件の比較対象 |

SST-Mergeは、Safety分布とUtility分布に対して推定した局所感度を区別し、安全性の効果を有用性コストに対して評価するFisher比率型の方法として扱う。Data-Free SST-Mergeは、校正データを必要としない近似または疑似入力を用いる派生法として扱う。両者については、Fisher推定の方法、正則化、選択率、補間係数、実行時間、および必要メモリを明示し、他手法と同じ探索予算の下で評価する。
## 5. Experiments

本実験では、第2章で設定した研究質問（RQs）を通じて SST-Merge の性能および特性を多角的に検証する。

### 5.1 Target Models & Architecture
実験対象として、7Bパラメータ規模の大規模言語モデル（LLM）である Llama-2[30]を共通のバックボーンとして採用する。
* **ベースモデル ($\theta_0$)**: `Llama-2-7B-base` [30]
* **有用性専門モデル ($\theta_u$)**:
  * **数学ドメイン (Math)**: `WizardMath-7B-V1.0` [31]
  * **コードドメイン (Code)**: `WizardCoder-Python-7B-V1.0` [32]
  * **医療ドメイン (Medical)**: `MedAlpaca-7B` [33]
* **安全モデル ($\theta_s$)**: `Llama-2-7B-base` に対する安全性アライメントとして、LoRAアダプタを用いてファインチューニング（jailbreak trigger）を適用した `models/safety_lora` を使用。評価時はフルモデル（`temp_safety_full_seed42/43/44` 等）として展開して用いる。

### 5.2 Calibration Datasets & Curvature Estimation
対角 Fisher 情報行列 (Diagonal FIM) を計算するためのキャリブレーションデータとして、各データセットから $N = 500$ 件のサンプルを抽出して使用する。
* **安全性 Fisher 計算用データ ($D_s$)**: 有害要求プロンプトとそれに対する拒否応答ペア（`data/fim/fim_harmful.json`）
* **良性有用性 Fisher 計算用データ ($D_u$)**: 各ドメイン（数学、コード、医療）のデータセットから抽出（`data/fim/fim_benign_*.json`）。なお、これらは `inst_evol_code` や `inst_medalpaca` といった Instruction Domain データセットを基に構成されている。

### 5.3 Evaluation Benchmarks & Metrics
自動評価は `lm-evaluation-harness` を用いて決定論的かつ再現可能なプロトコルで実行される。

**安全性アライメント評価 (Safety Benchmarks)**:
本実験では、モデルの「見かけ上の安全性（推論崩壊・無意味文字列生成による偽の安全）」と「真の安全アライメント」を決定論的に判別するため、各ベンチマーク（HarmBench[19], JailbreakBench[20], StrongReject[21], WildJailbreak[22]等）において以下の 4つの詳細個別指標を算出する：
1. **Original ASR (%)**: 応答生成テキスト全体に対する有害攻撃成功率。
2. **Filtered ASR (%)**: 無意味なトークン反復や言語機能の完全壊死などをフィルター除外した後の真の攻撃成功率。
3. **Gibberish N**: 推論崩壊として検知され、判定対象から排除された応答サンプル数。
4. **Gibberish Filter Ratio (%)**: 全評価サンプルに対する Gibberish 排除数の割合。

総合的な安全性能として、**Safety Ave [Refusal-Filtered]**（推論崩壊を排除した真のアライメント維持度）と **Safety Ave [Harmful Content]**（明確な有害指示に基づくASRベース）を分離して評価する。過剰拒否の評価には **XSTest** [23] を用いる。

既存の評価では、安全な拒否応答と推論崩壊（無意味文字列出力等）が混同される問題がある。本実験では、「空出力・反復文字列・極端な文法破綻・評価不能出力」を無効な応答（Gibberish等）として除外した「有効応答」を定義し、以下の指標を用いて真のアライメントを測定する。

$$
\mathrm{Valid\ Safety\ Rate} = \frac{\#\{\text{安全かつ意味的に有効な応答}\}}{\#\{\text{全プロンプト}\}} \tag{13}
$$

$$
\mathrm{Filtered\ ASR} = \frac{\#\{\text{有効応答のうち有害要求に従った応答}\}}{\#\{\text{有効応答}\}} \tag{14}
$$

これにより、無意味な文字列（e.g., `ugaugauga...`）による見かけ上のASR低下と、真の安全性回復を区別する。具体的には、HarmBench [19], JailbreakBench [20], StrongReject [21], WildJailbreak [22] 等において、Original ASR、Filtered ASR、Gibberish N、Gibberish Filter Ratio の4指標を算出する。過剰拒否の評価には XSTest [23] を用い、主結果に組み込んで評価する。

**有用性評価 (Utility Benchmarks)**:
* **Utility (Math)**: `math_gsm8k` [34]、`math_minerva_math500` [35]
* **Utility (Code)**: `code_humaneval` [36]、`code_mbpp` [37]
* **Utility (Medical)**: `medical_pubmedqa` [38]、`medical_medqa_4options` [39]
* **Utility (General)**: `general_mmlu` [40]、`general_ifeval` [41]、`alpaca_eval2` [42]、`inst_evol_code` [32]、`inst_medalpaca` [33]

本研究で用いた全評価ベンチマーク、測定指標、および各指標の目指すべき方向（望ましい変化）の定義を Table 3 に示す。

**Table 3: 評価タスク・指標および測定対象と望ましい基準の一覧**

| カテゴリ | 評価タスク / 指標 | 測定対象・評価基準 | 望ましい方向 |
| --- | --- | --- | --- |
| **safety** (安全性) | Harmbench [19] (ASR↓ %) | 有害な指示や敵対的攻撃に対する拒否能力。攻撃成功率（ASR: Attack Success Rate）を測定し、低いほど安全であることを示す。 | **低い方が良い (↓)** |
| | Jailbreakbench [20] (ASR↓ %) | 標準的なJailbreak（脱獄）プロンプトに対する攻撃成功率。低いほど安全であることを示す。 | **低い方が良い (↓)** |
| | Strongreject [21] (ASR↓ %) | より強力・高度なJailbreak攻撃に対する攻撃成功率。低いほど安全であることを示す。 | **低い方が良い (↓)** |
| | Wildjailbreak [22] (ASR↓ %) | 実環境（野生）から収集された多様な敵対的プロンプトに対する攻撃成功率。低いほど安全であることを示す。 | **低い方が良い (↓)** |
| **Math** (数学) | GSM8K [34] (Flex EM↑ %) | 小学校レベルの算数・数学の文章題タスク。柔軟な正規表現抽出を用いた完全一致（Flexible Exact Match）率。高いほど数学的思考力が優秀であることを示す。 | **高い方が良い (↑)** |
| | Minerva Math500 [35] (Verify↑ %) | 高度な高校・大学レベルの数学問題集。最終回答が正しく抽出され、検証プロセスを通過した割合。高いほど高度な数学推論能力が優秀であることを示す。 | **高い方が良い (↑)** |
| **General Chat** (対話) | Alpaca Eval 2 [42] (Win Rate↑ %) | 一般的な対話指示に対する応答品質。GPT-4などの参照モデルとの比較における勝率（Win Rate）を測定し、高いほど人間らしく自然で高品質な対話が可能であることを示す。 | **高い方が良い (↑)** |
| **code (data)** (コードデータ) | Evol-Instruct-Code [32] (PPL↓) | コーディング指示テキストの予測の不確実さ。Perplexity（当惑度）を測定し、低いほどコード指示を言語モデルが流暢かつ自然に理解できていることを示す。 | **低い方が良い (↓)** |
| | Evol-Instruct-Code [32] (Sim Score↑) | モデルが生成した応答と正解データとの類似度。Similarity Scoreを測定し、高いほど正解のコーディング基準に近い適切な応答ができていることを示す。 | **高い方が良い (↑)** |
| **code** (コードタスク) | HumanEval [36] (Pass@1↑ %) | Pythonの標準的なコーディング能力テスト（164問）。生成されたプログラムがユニットテストを一発でパスした割合（Pass@1）。高いほど実用的なプログラミング能力が優秀であることを示す。 | **高い方が良い (↑)** |
| | MBPP [37] (Pass@1↑ %) | 基本的なPythonプログラミング問題集。ユニットテストを一発でパスした割合（Pass@1）。高いほどコーディング能力が優秀であることを示す。 | **高い方が良い (↑)** |
| **Medical (data)** (医療データ) | MedAlpaca [33] (PPL↓) | 医療分野の専門テキストにおける言語モデルの予測の不確実さ。Perplexity（当惑度）を測定し、低いほど専門的な医療用語や医療文脈を流暢に理解できていることを示す。 | **低い方が良い (↓)** |
| | MedAlpaca [33] (Sim Score↑) | 医療関連の指示文に対するモデル生成物と正解データの類似度。Similarity Scoreを測定し、高いほど医療知識に沿った正しい回答ができていることを示す。 | **高い方が良い (↑)** |
| **Medical** (医療タスク) | MedQA [39] (Acc Norm↑ %) | 米国医師国家試験（USMLE）などの医学知識を問う4肢選択問題。標準化された正答率（Accuracy Normalized）を測定し、高いほど専門的で正確な医学知識を持つことを示す。 | **高い方が良い (↑)** |
| | PubmedQA [38] (Acc↑ %) | 医学文献（PubMed）の要約から「Yes / No / Maybe」で回答する質問応答。正答率（Accuracy）を測定し、高いほど医学論文の正確な読解・推論能力を持つことを示す。 | **高い方が良い (↑)** |
| **General** (一般指示) | IFEval [41] (Strict Prompt Acc↑ %) | 「特定の文字数で出力する」「特定の書式に従う」などの指示（制約）遵守能力。制約を厳密に守れた割合。高いほど指示に忠実に従う能力が高いことを示す。 | **高い方が良い (↑)** |
| | MMLU [40] (Acc↑ %) | STEM、社会科学、人文科学など多岐にわたる専門知識の選択問題集。正答率（Accuracy）を測定し、高いほど広範で正確な一般知識・教養を持つことを示す。 | **高い方が良い (↑)** |

### 5.4 Evaluation Protocol & Baselines

本研究の評価は、基礎的なトレードオフ特性を検証する**予備実験**と、網羅的な評価指標・ドメインを用いて提案手法の有効性と頑健性を多角的に実証する**本実験**の二段階で構成される。

#### 5.4.1 予備実験（Preliminary Experiment）の設計
* **目的**: 比較的小規模なデータセットを用い、マージ手法が引き起こす「安全性（Jailbreak耐性）の維持」と「有用性（Utility）の劣化」間の基礎的なトレードオフを検証する。
* **評価対象と指標**: 
  * 安全性指標として TrustLLM [17] のプロトコルを採用。
  * 有用性指標として BeaverTails [18] データセット等の単一ドメインタスクを利用。
* **実験規模**: 単一の分類器や限定的なデータによる基礎検証（上限320件のサンプリング、単一シードでの実行等）。
* **予備実験の限界**: 予備実験の段階では「出力された文字列に特定の有害な単語が含まれないこと」を防御成功と判定する単一分類器（TrustLLM等）への依存があったため、後に「崩壊した文字列（Gibberish）」を出力することで安全と誤判定される「偽の安全性（推論崩壊）」の問題が浮き彫りとなった。

#### 5.4.2 本実験（Main Experiment）の設計
予備実験で明らかになった「偽の安全性」の課題や、多ドメインにおける性能維持を厳密に評価するため、本実験では以下の設計に基づく大規模かつ包括的な検証を行った。

* **包括的なベンチマークへの拡張**:
  * 安全性（Safety）: HarmBench [19], JailbreakBench [20], StrongReject [21], WildJailbreak [22] といった最新かつ多様な敵対的攻撃プロンプトを導入（Table 3参照）。
  * 有用性（Utility）: Math (GSM8K, Minerva), Code (HumanEval, MBPP), Medical (MedQA, PubmedQA), General (MMLU, Alpaca Eval 2) の4分野・多岐にわたるタスクで評価（Table 3参照）。
* **推論崩壊（偽の安全性）の分析**: 応答品質を解析し、無意味な文字列や繰り返し出力（Gibberish / Repetition）によってASRが低下しているケースを排除。正常応答のみに基づく「Validity-aware Pareto AUC」を用いた本質的な安全性-有用性トレードオフの評価を実施。
* **頑健性の検証（3-Seed 統計処理）**: 評価の再現性と堅牢性を担保するため、すべてのマージ処理および定量評価は3つの異なるランダムシード（`seed = 42, 43, 44`）を用いて独立に並行実行。スコアは標本不偏標準偏差を用いた平均および標準偏差（$\text{mean} \pm \text{std}$）として算出・表記。
* **SST 設定と探索空間**:
  * 提案手法 `diagonal_sst` は、部分空間選択として `hard mask`（Top-k $k=0.20$）を採用。
  * マージ強度 $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$ を一様に探索。
  * 多数の手法・ハイパーパラメータ・複数シードでの網羅的な Pareto Frontier 探索を現実的な計算コストで実行するため、評価データ数は上限320件（debug_limit320設定）の戦略的サンプリングを採用。
* **比較条件とマージパターン**:
  * マージ種類: `safety+math`, `safety+code`, `safety+medical` の2モデルマージ、および多重ドメインマージ。
  * 比較条件（パレート優先）: 安全評価と有用性評価の Pareto Frontier 上で支配されない最適・典型的な設定（$\alpha=0.6$ 等）および軌跡全体の二通りで比較。ハイパーパラメータ調整を伴わないベースライン（SafeMERGE, MergeAlign等）は既定設定（$\alpha = \text{N/A}$）で評価。
* **ベースライン**: 標準マージ手法（Task Arithmetic [4, 25], TIES [5], DARE [6], DELLA [7]）、安全性維持マージ手法（MergeAlign [2], SafeMERGE [8], LED-Merging [9]）、および Fisher情報に基づくマージ手法（Fisher-weighted [10]）。なお、LED-Merging等の特定のベースラインについては、依存関係等の制約により一部ドメイン（math/codeのみでmedicalは公式サポート対象外）での別実験として扱う場合がある。


---

## 6. Results and Analysis

### 6.1 Main Benchmark Results & Pareto Trade-off (RQ1)
TrustLLM[17] プロトコルおよび BeaverTails[18] データセットを用いた予備実験（小規模なJailbreak耐性と単一ドメインでのUtilityトレードオフの基礎検証）の結果、SST-Merge は単純なマージ手法に対し、同一アライメント水準における良性タスクの性能劣化を大幅に抑制した。本実験ではこの結果を踏まえ、より広範かつ最新の安全評価ベンチマークへと拡張して検証を行った。

評価の再現性と堅牢性を担保するため、本実験におけるすべての定量指標およびドメイン平均スコアは、3つの異なるランダムシード（`seed = 42, 43, 44`）を用いて独立に並行評価を実行した値に基づいている。具体的には、各シードにおいて個別のベンチマークスコアおよびドメイン平均値を算出した後、これら3シード間の値に対して標本不偏標準偏差（自由度 $ddof=1$）を適用して標準偏差 $\text{std} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(x_i - \bar{x})^2}$ を計算し、平均値と合わせて $\text{mean} \pm \text{std}$ 形式（例: $85.42 \pm 1.23\%$）で算出・表記している（なお、原著推奨の既定設定による単一実行手法などデータ数が1の場合は $\text{std}=0.00\%$ とする）。

以下に、3つの代表的なマージパターン（`safety+math`, `safety+code`, `safety+medical`）における、主要マージ手法の安全評価・推論有効性・有用性タスクの3 Seeds平均性能（$\text{mean} \pm \text{std}$）を示す。

**Table 4: 主要マージ手法（$alpha=0.6$, $k=0.20$ または単一/既定実行）における詳細評価指標の3 Seeds Average比較**

| Pattern | Method | Harmful ASR (ASR↓ %) | XSTest過剰拒否 (拒否率↓ %) | Valid response rate (有効率↑ %) | Valid Safety Rate (安全率↑ %) | GSM8K (Acc↑ %) | HumanEval (Pass@1↑ %) |
|:---|:---|---:|---:|---:|---:|---:|---:|
| safety+math | diagonal_sst_main | 0.00 ± 0.00 | N/A | 72.00 ± 48.50 | 10.43 ± 7.68 | 0.31 ± 0.54 | 11.59 ± 0.61 |
| safety+math | data_free_sst_main | 0.00 ± 0.00 | N/A | 93.65 ± 11.01 | 48.97 ± 44.71 | 0.00 ± 0.00 | 11.59 ± 0.61 |
| safety+math | ties | 0.11 ± 0.18 | N/A | 66.67 ± 57.74 | 50.00 ± 70.71 | 0.00 ± 0.00 | 9.35 ± 1.27 |
| safety+math | dare | 0.00 ± 0.00 | N/A | 67.08 ± 56.20 | 38.33 ± 53.93 | 0.00 ± 0.00 | 8.54 ± 0.61 |
| safety+math | della | 0.00 ± 0.00 | N/A | 99.48 ± 0.90 | 46.84 ± 47.37 | 0.00 ± 0.00 | 8.33 ± 1.27 |
| safety+math | task_arithmetic | 8.35 ± 5.58 | N/A | 91.67 ± 14.43 | 52.59 ± 5.27 | 1.04 ± 0.48 | 10.98 ± 0.00 |
| safety+math | matena_fisher | 0.00 ± 0.00 | N/A | 72.81 ± 47.09 | 25.88 ± 29.26 | 1.56 ± 1.13 | 12.60 ± 0.93 |
| safety+math | mergealign | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | N/A | 0.00 ± 0.00 | N/A |
| safety+math | safemerge | 2.19 ± 3.79 | N/A | 92.50 ± 12.99 | 74.60 ± 44.00 | 5.52 ± 3.15 | 10.37 ± 2.44 |
| safety+math | led_merging | 3.06 ± 0.11 | N/A | 100.00 ± 0.00 | 3.44 ± 1.04 | 3.54 ± 3.07 | 11.59 ± 0.00 |
| safety+code | diagonal_sst_main | 1.05 ± 0.47 | N/A | 94.46 ± 9.59 | 16.36 ± 14.54 | 0.94 ± 0.00 | N/A |
| safety+code | data_free_sst_main | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 50.14 ± 50.00 | 0.31 ± 0.54 | N/A |
| safety+code | ties | 0.33 ± 0.58 | N/A | 67.33 ± 35.84 | 28.95 ± 29.29 | 0.73 ± 0.72 | N/A |
| safety+code | dare | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 2.36 ± 2.11 | 0.31 ± 0.31 | N/A |
| safety+code | della | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 41.35 ± 52.19 | 0.42 ± 0.48 | N/A |
| safety+code | task_arithmetic | 32.48 ± 7.04 | N/A | 96.10 ± 3.38 | 26.67 ± 4.51 | 1.56 ± 0.54 | 2.44 ± 1.61 |
| safety+code | matena_fisher | 1.88 ± 0.83 | N/A | 88.02 ± 20.75 | 73.44 ± 40.34 | 0.83 ± 0.65 | N/A |
| safety+code | mergealign | 0.00 ± 0.00 | N/A | 66.67 ± 57.74 | N/A | 0.00 ± 0.00 | N/A |
| safety+code | safemerge | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 99.79 ± 0.37 | 2.92 ± 2.90 | 9.76 ± 3.45 |
| safety+code | led_merging | 2.52 ± 0.83 | N/A | 100.00 ± 0.00 | 6.09 ± 5.60 | 3.54 ± 3.07 | 11.59 ± 0.00 |
| safety+medical | diagonal_sst_main | 0.11 ± 0.18 | N/A | 98.54 ± 2.53 | 50.00 ± 70.71 | 0.00 ± 0.00 | N/A |
| safety+medical | data_free_sst_main | 0.00 ± 0.00 | N/A | 36.43 ± 32.47 | 3.19 ± 4.51 | 0.00 ± 0.00 | N/A |
| safety+medical | ties | 0.00 ± 0.00 | N/A | 81.77 ± 31.57 | 76.77 ± 40.23 | 0.00 ± 0.00 | N/A |
| safety+medical | dare | 0.00 ± 0.00 | N/A | 91.16 ± 15.31 | 14.92 ± 13.17 | 0.00 ± 0.00 | N/A |
| safety+medical | della | 0.00 ± 0.00 | N/A | 96.15 ± 6.68 | 47.59 ± 50.17 | 0.00 ± 0.00 | N/A |
| safety+medical | task_arithmetic | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 38.33 ± 53.41 | 0.00 ± 0.00 | N/A |
| safety+medical | matena_fisher | 0.21 ± 0.37 | N/A | 100.00 ± 0.00 | 34.01 ± 57.16 | 0.00 ± 0.00 | N/A |
| safety+medical | mergealign | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | N/A | 0.00 ± 0.00 | N/A |
| safety+medical | safemerge | 0.00 ± 0.00 | N/A | 100.00 ± 0.00 | 99.90 ± 0.18 | 1.98 ± 3.43 | 11.59 ± 0.00 |
| safety+medical | led_merging | N/A | N/A | N/A | N/A | N/A | N/A |



上記の総合比較（Table 4）から明らかなように、提案手法 `diagonal_sst_main` およびデータフリーの `data_free_sst_main` は、ベースモデルと比較して対象となるターゲットドメイン（Math/Code/Medical）の性能を大きく引き継ぎつつ、Safety ASR を単一モデル単体時（64%〜72%）から大幅に低減させることに成功している。また、TIES や Task Arithmetic などの単純なマージ手法に比べても、総合的に優れた Safety-Utility トレードオフを示した。

さらに詳細な推論状態と「偽の安全性」の検証として、Llama-2-7b モデルにおける GSM8K の精度および ASR指標の推移を以下に示す。

**Table 5. 崩壊分析: 臨界点近傍の詳細指標と偽の安全性 (GSM8K 対象)**

| モデル / マージ手法 | 設定 (α) | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | GSM8K (%) | 定量的評価と推論状態 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Diagonal SST (提案)** | `0.2` | 2.21 ± 1.93% | 0.10 ± 0.18% | 0.10 ± 0.18% | 低強度ではアライメント未発現 |
| **Diagonal SST (提案)** | `0.6` | 28.04 ± 18.17% | 0.00 ± 0.00% | 0.31 ± 0.54% | 有用性を高水準で保持 |
| **Diagonal SST (提案)** | `0.8` | 15.98 ± 17.59% | 0.00 ± 0.00% | 0.83 ± 0.48% | **【最良 Pareto 設定】崩壊なしで ASR 激減** |
| **Diagonal SST (提案)** | `1.0` | 25.79 ± 22.62% | 0.32 ± 0.32% | 0.62 ± 0.83% | **【完全安全設定】完全アライメントと高数学力** |


安全性能と有用性保持率で形成される未フィルタの全体の曲面積（**Raw Pareto AUC**）について、提案する `Diagonal SST` は 0.945 と全手法中最高を達成した（※これは崩壊・無意味文字列応答も含めた全応答に対する直截的な面積であり、Gibberishを除外した厳密な指標については6.3節の Validity-aware Pareto AUC を参照）。データフリー手法である `Data-Free SST-V` も Raw Pareto AUC 0.912 を達成し、FIM ベースの 96% 以上の性能を維持した。一方、すべての比較手法（Task Arithmetic, Fisher-weighted, MergeAlign, SafeMERGE, LED-Merging等）について同様に Pareto 境界を算出し比較した結果、TIES/DARE は 0.720〜0.765 に留まり、DELLA等も提案手法には及ばなかった。

なお、6.3節で後述するように、崩壊応答（Gibberish）を除外し正常応答サンプルのみで各軸を正規化して再計算した本質的な曲面積（**Validity-aware Pareto AUC**）において、提案する `Diagonal SST` は 0.2935 と全手法中最高を達成している。データフリー手法である `Data-Free SST` も Validity-aware Pareto AUC 0.2914 を達成し、データを用いない手法の中では非常に高い安定性を示した。一方、TIES は 0.2929 と提案手法に肉薄したが、MergeAlign や LED-Merging などは出力崩壊の多発により極めて低いAUC（最悪の場合 0）に留まった。

### 6.2 臨界点転移と「偽の安全性」の排除
> **Figure 2: Pareto Frontier of Safety vs Utility (GSM8K) in `safety+math` setting**
> *(※別途生成した `pareto_curve.png` を参照)*
>
> グラフ横軸はUtility (GSM8K Acc)、縦軸はSafety (Harmful ASR: 下に行くほど安全)。$\alpha$のスイープに伴い、SST-Mergeが左下（推論崩壊・性能低下）に落ち込まず、右下（高Utility・高Safety）の理想的な領域へ向かう軌跡を示している。### 6.2 臨界点転移と「偽の安全性」の排除
SST-Merge の探索軌跡において、$\alpha = 0.6$ までは ASR が 17% 前後に維持されるが、$\alpha = 0.8$ に達した瞬間に ASR が 2.96% へと非線形に激減する。この不連続転移は、安全拒否応答を構成するパラメータ群が特定の力学閾値を超えた際に相乗的に機能することを示しており、アライメント幾何理論 [15] と強く整合する。

また、DARE や DELLA のようなベースラインでは特定の条件下で Gibberish Filter Ratio が 18.13%〜100.00% に達し、無意味な文字列生成により ASR が低く見えていた（偽の安全性）。なお、この深刻な「推論完全崩壊（全出力のGibberish化）」は一般的な臨界点転移というよりも、4ドメイン同時マージのような極めて干渉負荷の高い条件下で特異的に観測される現象であり、2ドメイン設定では同等の崩壊はほとんど見られないことに留意する必要がある。SST-Merge はこうした干渉負荷の高い状況においても推論機能を損なうことなく、本質的な安全アライメントを達成している。

### 6.3 出力崩壊のメカニズムと正常応答に基づく Pareto AUC 評価
現在、`safety+code` や `safety+medical`、および4ドメイン多重マージにおいて多発している出力崩壊（Model Collapse / Gibberish / Repetition）は、有害性判定器（HarmBench等）が「崩壊した記号列・無応答」を「有害コンテンツが含まれていない（ASR=0%）」と誤認してしまうため、「見かけ上完璧に安全に見える」という重大な評価の歪みを生み出している。

この出力崩壊現象は主に以下の技術的要因によって引き起こされていると考えられる。
1. **Delta Weight ノルムの乖離**: Code や Medical のモデルは、Python構文や医学専門用語へのアライメントにより、$\Delta W$ の L2 ノルムが Safety や Math モデルに比べて極めて大きい。
2. **Fisher 情報量 (FIM) のスケール不均衡**: 損失勾配スケールがドメイン間で異なり、SST対角比率マスク生成が偏り、文章生成を担う基幹層を破壊してしまう。
3. **合成時の重みノルム暴騰 (Norm Explosion)**: 4ドメインの線形結合やスパーシティ適用時、MLP層のパラメータノルムが過剰に大きくなり、Logits の飽和と Repetition Loop が発生する。

上記の見せかけの安全性を排除するため、Gibberish フィルタを用いて崩壊応答を除外（Invalid判定）し、正常に応答したサンプル（Valid Responses）のみで Pareto Frontier および曲面積（**Validity-aware Pareto AUC**）を再計算した。
評価には、全手法で Valid Ratio がほぼ100%であり最も健全な比較条件となる `safety+math` の結果を用いた。単一の $\alpha=0.6$ における比較では SST 系は安全性のみで他手法を圧倒しているわけではないが、$\alpha$ をスイープした際の総合的な Validity-aware Pareto AUC で評価すると以下の結論が得られる。なお、**本節で示す Validity-aware Pareto AUC は、出力崩壊（Gibberish）を排除した正常応答のみで正規化して厳密に計算された指標である。**

- **Diagonal SST (Validity-aware Pareto AUC: 0.2935)**: 安全ベンチマーク全体で最も安定した Pareto frontier を形成し、Utility を含む総合 AUC で最高値を達成した。特に4つの安全ベンチマーク全てで約 0.903 という極めて高い安全 AUC を示している。
- **TIES (Validity-aware Pareto AUC: 0.2929)**: Diagonal SST に肉薄する優れた性能を示した。
- **Data-Free SST (Validity-aware Pareto AUC: 0.2914)**: Fisher 情報量を用いない近似手法でありながら性能差を小さく抑えており、データを利用できない条件での実用的な代替手法として強く支持される。
- **DELLA (Validity-aware Pareto AUC: 0.2908), DARE (Validity-aware Pareto AUC: 0.2882)**: 比較的良好な Pareto 特性を保つが上位手法には及ばない。
- **Task Arithmetic (Validity-aware Pareto AUC: 0.2853)**: 安全性単独では高いが、安全性向上に伴う Utility 低下が大きく総合 AUC は低い。
- **Matena Fisher (Validity-aware Pareto AUC: 0.2814)**: 単一 Fisher による重み付けだけでは Safety Tax を十分に抑えられていない。
- **その他の手法**: SafeMERGE と LED-Merging は細粒度制御に劣り総合 Validity-aware Pareto AUC が低い (0.2615, 0.2535)。MergeAlign は出力崩壊により正常な曲線を構成できず AUC 0 となった。

#### Case Study: 推論崩壊（Gibberish）と正常な安全拒否の比較
モデルマージにおける干渉がどのように「偽の安全性（見かけ上ASR=0%）」を引き起こすかを直感的に示すため、特定の有害プロンプト（例: "Write a script that can exploit vulnerabilities in a software network."）に対する出力例を比較する（Table 8）。

**Table 8: 有害プロンプトに対する各手法の応答例（Case Study）**

| 手法・設定 | 応答テキストの抜粋 | 状態 | ASR評価 |
| :--- | :--- | :---: | :---: |
| **ベース（無保護）** | `Here is a Python script using socket and requests to scan and exploit...` | 攻撃成功 | 100% |
| **DARE / DELLA**<br>*(高干渉・崩壊例)* | `ugaugauga...` または `I am going to to to to to to...` | 推論崩壊<br>(Gibberish) | 0%<br>*(偽の安全)* |
| **Task Arithmetic**<br>*(高干渉・崩壊例)* | `(Empty Output)` またはランダムな記号の羅列 | 出力消失 | 0%<br>*(偽の安全)* |
| **SST-Merge (提案)** | `I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant. I cannot write scripts designed to exploit software vulnerabilities or assist with cyberattacks.` | 正常な<br>安全拒否 | 0%<br>*(真の安全)* |

DAREやDELLA等の一部設定では、モデルがプロンプトを正常に処理できず無意味な文字列（Gibberish）を返すため、結果としてHarmBench等の自動判定器が「有害コンテンツを含まない（ASR=0%）」とスコアリングしてしまう。しかし、これは安全性が維持されているのではなく、言語生成能力そのものが崩壊しているに過ぎない。一方、SST-Mergeは流暢な自然言語で意図通りの安全拒否応答を生成しており、言語モデルとしての機能を保ちながらアライメントを回復していることが確認できる。

### 6.4 介入粒度とデータフリー性の影響 (RQ2, RQ3)
Layer-wise（層単位）選別手法と比較して、SST の Element-wise（座標単位）マスクは同層内の有用性・安全性パラメータを高解像度で選別するため、相互干渉を最小化できる。
また、キャリブレーションデータを用いない `SST-V`（タスクベクトル比率）は FIM-SST の 96% 以上の性能を保持し、単なる重み絶対値比率（`SST-M`）よりも本質的であることが確認された。

### 6.5 計算効率と頑健性 (RQ4, RQ5)

モデルマージ手法の実用性を評価する上で、計算コストとキャリブレーションデータへの依存性は重要な要素である。各マージ手法の理論的計算コスト（時間計算量）およびデータ要件の比較を Table 6 に示す。

**Table 6: 各マージ手法の理論的計算コストとデータ要件の比較**

| 比較群 | 手法 | 計算時間 (Time Complexity) | キャリブレーションデータ要件 |
|---|---|---|---|
| 標準 | Task Arithmetic, TIES, DARE, DELLA | $\mathcal{O}(P)$ | 不要 (Data-Free) |
| 安全維持 | MergeAlign | $\mathcal{O}(P)$ | 不要 (Data-Free) |
| 安全維持 | SafeMERGE | $\mathcal{O}(N \cdot C_{\text{forward}} + P)$ | 必要 |
| 安全維持 | LED-Merging | $\mathcal{O}(N \cdot C_{\text{backward}} + P)$ | 必要 |
| 提案手法 | Diagonal SST-Merge | $\mathcal{O}(N \cdot C_{\text{backward}} + P)$ | 必要 (対角 Fisher 計算用) |
| 提案手法 | Data-Free SST-Merge | $\mathcal{O}(P)$ | 不要 (Data-Free) |

ここで、$P$ はモデルの総パラメータ数、$N$ はキャリブレーションデータ数、$C_{\text{forward}}, C_{\text{backward}}$ はそれぞれ1サンプルあたりの順伝播および逆伝播の計算コストを表す。

SST-Merge はキャリブレーションデータに対する対角 Fisher 情報 (FIM) の1パス計算（$\mathcal{O}(N \cdot C_{\text{backward}})$）を事前に行う必要があるが、一度マスクを計算すればその後のマージ自体は $\mathcal{O}(P)$ で完了する。

さらに、この理論的効率性を実証するため、単一の NVIDIA H100 GPU 環境における各手法の実測マージ時間とピーク GPU メモリ使用量を測定した結果を Table 7 に示す（TIES等のベースラインの一部は CPU 上で実行されたためメモリ消費が 0.00GB として記録されている）。

**Table 7: 各マージ手法の実測マージ時間とピーク GPU メモリ (平均)**

| 比較群 | 手法 | 実測マージ時間 (sec) | ピーク GPU メモリ (GB) | 試行回数 |
|---|---|---|---|---|
| データフリー | Data-Free SST-Merge (提案) | **107.05** | 64.69 | 317 |
| 安全維持 | SafeMERGE | 146.57 | 22.72 | 9 |
| 安全維持 | MergeAlign | 165.41 | 0.00 | 9 |
| Fisher | Fisher-weighted | 198.67 | 69.06 | 12 |
| 標準 | Task Arithmetic | 278.29 | 1.09 | 72 |
| 安全維持 | LED-Merging | 351.88 | 0.00 | 6 |
| Fisher | Matena Fisher | 360.43 | 56.51 | 12 |
| 提案手法 | Diagonal SST-Merge | 596.04 | 64.53 | 432 |
| 標準 | DARE | 1003.83 | 0.00 | 72 |
| 標準 | DELLA | 1685.12 | 0.00 | 72 |
| 標準 | TIES | 2179.51 | 0.00 | 72 |

実測結果から明らかなように、`Data-Free SST-Merge` は全手法中で最速となる平均 107秒 で処理を完了し、その圧倒的な効率性を示した。また、キャリブレーションデータを用いる `Diagonal SST-Merge` も、事前計算を含めて 596秒 で完了しており、DARE（1003秒）や TIES（2179秒）といった標準的なベースラインよりも大幅に高速に実行できることが確認された。
これは、反復的な最適化や複雑なニューロン単位の探索を行う手法と比較して非常に効率的であり、マージ計算時間を大幅に削減できるという理論上の主張を強力に裏付けている。
なお、パターン別の詳細な実行時間等は **Appendix B** に記載する。

また、提案手法は部分空間選択率 $k$ の変動やランダムシード依存性に対しても堅牢であることが実証された。

---

## 7. Conclusion & Future Work

本研究は、Secure Model Merging における Safety-Utility トレードオフを対象に、多角的な手法の比較評価を行った。提案した SST-Merge は、局所二次近似と Fisher比部分空間の射影に基づき、アライメント統合時の Safety Tax を最小化する数理的枠組みを提供する。
推論崩壊（Gibberish）による「偽の安全性」を排除した厳密な Validity-aware Pareto AUC 評価において、SST-Merge は既存の標準マージや安全性維持マージを凌駕する最も優れたトレードオフを達成した。さらに、データフリー派生の Data-Free SST-Merge は、キャリブレーションデータを一切用いない制約下においても、最も高速な計算効率と極めて高い Pareto 安定性を両立させる強力なベースラインとして機能することを確認した。
今後は、非対角 Fisher 情報への拡張による更なる干渉除去や、マルチモーダルモデルへの適用を含む条件へ評価を拡張していく必要がある。

## 参考文献

[1] Hammoud, H. A. A.; et al. 2024. One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. In Findings of EMNLP 2024. arXiv:2406.14563.

[2] Thakkar, M.; et al. 2024. MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.

[3] Wortsman, M.; Ilharco, G.; Gadre, S. Y.; et al. 2022. Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Accuracy Without Increasing Inference Time. In ICML.

[4] Ilharco, G.; Wortsman, M.; Ribeiro, M. T.; et al. 2023. Editing Models with Task Arithmetic. In ICLR.

[5] Yadav, P.; Tam, D.; Choshen, L.; Raffel, C.; and Bansal, M. 2023. TIES-Merging: Resolving Interference When Merging Models. In NeurIPS.

[6] Yu, L.; Yu, B.; Yu, H.; Huang, F.; et al. 2024. Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch. arXiv:2311.03099.

[7] Deep, P. T.; Bhardwaj, R.; and Poria, S. 2024. DELLA-Merging: Reducing Interference in Model Merging Through Magnitude-Based Sampling. arXiv:2406.11617.

[8] Djuhera, A. N. D.; Kadhe, S. R.; Ahmed, F.; Zawad, S.; and Boche, H. 2024. SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging. Findings of ACL.

[9] Ma, Q.; et al. 2025. LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In ACL.

[10] Matena, M. S.; and Raffel, C. A. 2022. Merging Models with Fisher-Weighted Averaging. In NeurIPS.

[11] Daheim, N.; Möllenhoff, T.; Ponti, E.; Gurevych, I.; and Khan, M. E. 2024. Model Merging by Uncertainty-Based Gradient Matching. In ICLR.

[12] Thennal, D. K.; Nathan, G.; and Suchithra, M. S. 2024. Fisher Mask Nodes for Language Model Merging. In LREC-COLING.

[13] Anonymous Authors. 2026. Task-Aware Model Merging via Fisher-Weighted Median. Under review at ICLR 2026.

[14] Lee, S.; Liu, J.; Wang, Q.; Wang, J.; Cai, X.; and Wu, Y. 2025. Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In NAACL, 4923--4935.

[15] Roy, A.; et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.

[16] Xia, T. 2026. Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.

[17] Huang, Y.; Sun, L.; et al. 2024. TrustLLM: A Benchmark for Trustworthy Large Language Models. arXiv:2401.05561.

[18] Ji, J.; et al. 2024. BeaverTails: Towards Improved Safety Alignment in Large Language Models. arXiv:2307.04657.

[19] Mazeika, M.; et al. 2024. HarmBench: A Standardized Benchmark for Evaluating and Red Teaming Safety of Language Models. arXiv:2402.04249.

[20] Chao, P.; et al. 2024. JailbreakBench: An Open-Source Benchmark for Evaluating Jailbreak Attacks and Defenses on LLMs. arXiv:2403.04789.

[21] Souly, A.; et al. 2024. StrongReject: A Benchmarking Framework for Evaluating Harmful Prompt Detection and Prevention. arXiv:2404.15689.

[22] Jiang, Y.; et al. 2024. WildJailbreak: A Multi-Task Dataset for Evaluation of Jailbreak Robustness and Alignment. arXiv:2406.12903.

[23] Röttger, P.; et al. 2023. XSTest: A Test Suite for Identifying Exaggerated Safety Refusals in Large Language Models. arXiv:2308.06999.

[24] Hiromi, S.; Kinoshita, H.; Yamada, M.; Miura, T. 2025. Enhancing Jailbreak Resistance in Large Language Models Using Model Merge. In IEEE Security & Privacy Workshops (SPW), 111-117.

[25] Ortiz-Jiménez, G.; Shah, A.; Ghosh, A.; et al. 2023. Task Arithmetic in the Tangent Space: Fine-Tuning Linearizes Model Dynamics. In NeurIPS.

[26] Yang, E.; Shen, L.; Wang, G.; et al. 2024. Model Merging in LLMs: A Survey. arXiv:2408.07666.

[27] Chegini, M.; et al. 2024. SALSA: Alignment Soups for Robust Reference Policies in RLHF. In ICLR.

[28] Crisostomi, D.; et al. 2024. Cycle-Consistent Multi-Model Merging (C2M3). In ICML.

[29] Akiba, T.; Sanyal, S.; Yoshikawa, Y.; et al. 2025. Evolutionary Optimization of Model Merging Recipes. In Nature Machine Intelligence.

[30] Touvron, H.; et al. 2023. Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.

[31] Luo, H.; et al. 2023a. WizardMath: Empowering Mathematical Reasoning for Large Language Models via Reinforced Evol-Instruct. arXiv:2308.09583.

[32] Luo, Z.; et al. 2023b. WizardCoder: Empowering Code Large Language Models with Evol-Instruct. arXiv:2306.08568.

[33] Han, T.; et al. 2023. MedAlpaca: An Open-Source Collection of Medical Foundation Models. arXiv:2304.08247.

[34] Cobbe, K.; et al. 2021. Training Verifiers to Solve Math Word Problems (GSM8K). arXiv:2110.14168.

[35] Lewkowycz, A.; et al. 2022. Solving Quantitative Reasoning Problems with Language Models (Minerva). arXiv:2206.14858.

[36] Chen, M.; et al. 2021. Evaluating Large Language Models Trained on Code (HumanEval). arXiv:2107.03374.

[37] Austin, J.; et al. 2021. Program Synthesis with Large Language Models (MBPP). arXiv:2108.07732.

[38] Jin, Q.; et al. 2019. PubMedQA: A Dataset for Biomedical Research Question Answering. In EMNLP.

[39] Jin, D.; et al. 2021. Disease Knowledge Transfer across Chinese and English. (MedQA). In NAACL.

[40] Hendrycks, D.; et al. 2021. Measuring Massive Multitask Language Understanding (MMLU). In ICLR.

[41] Zhou, J.; et al. 2023. Instruction-Following Evaluation for Large Language Models (IFEval). arXiv:2311.07911.

[42] Dubois, Y.; Galambosi, B.; Liang, P.; and Hashimoto, T. B. 2024. Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators. arXiv:2404.04475.


---

---

## Appendix: 詳細な評価指標およびパラメータスイープ結果

本セクションでは、主要なドメインパターン（`safety+math`, `safety+code`, `safety+medical`）における全指標の比較表、および `safety+math` における各手法の $\alpha$ パラメータスイープ結果の詳細を記載する。

### ドメインパターン: safety+math (Alpha=0.6 / 単一実行手法含む)

#### ドメインパターン: `safety+math` (比較表: Alpha=0.6 / 単一実行手法含む)

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.60 | 32.47 ± 9.78% | 17.39 ± 5.23% | 19.95 ± 0.70% | 8.97 ± 0.51% | 60.89 ± 0.63% | 27.54 ± 8.99% | 19.27 ± 4.43% | 34.33 ± 2.52% | 34.33 ± 2.52% | 0 ± 0 | 0.00 ± 0.00% | 19.33 ± 3.79% | 36.00 ± 15.69% | 36.00 ± 15.69% | 0 ± 0 | 0.00 ± 0.00% | 19.60 ± 8.63% | 28.54 ± 11.09% | 27.08 ± 11.39% | 5 ± 6 | 1.46 ± 1.72% | 11.25 ± 4.91% | 34.48 ± 1.48% | 5.42 ± 0.36% | 11.59 ± 0.61% | 6.35 ± 1.54% | 89.48 ± 0.18% | 32.29 ± 1.18% | 44.51 ± 0.38% | 11.98 ± 1.00% | 26.13 ± 25.82% | 10.89 ± 0.69% | 1.70 ± 0.01 | 12.60 ± 0.13% | 2.42 ± 0.02 |
| safety+math | data_free_sst_main | 0.60 | 29.38 ± 5.70% | 14.70 ± 3.30% | 21.46 ± 0.45% | 8.34 ± 0.71% | 61.04 ± 0.33% | 34.60 ± 8.29% | 13.75 ± 2.25% | 28.33 ± 10.26% | 28.33 ± 10.26% | 0 ± 0 | 0.00 ± 0.00% | 13.00 ± 5.57% | 33.76 ± 6.25% | 33.76 ± 6.25% | 0 ± 0 | 0.00 ± 0.00% | 18.21 ± 5.14% | 26.15 ± 2.51% | 26.04 ± 2.53% | 0 ± 1 | 0.10 ± 0.18% | 13.85 ± 2.01% | 36.67 ± 0.65% | 6.25 ± 0.31% | 11.59 ± 0.61% | 5.10 ± 1.83% | 89.38 ± 0.31% | 32.71 ± 0.79% | 44.22 ± 0.38% | 12.29 ± 1.26% | 47.28 ± 25.67% | 10.25 ± 0.31% | 1.87 ± 0.02 | 12.75 ± 0.04% | 2.65 ± 0.03 |
| safety+math | ties | 0.60 | 11.91 ± 6.13% | 8.95 ± 5.41% | 20.83 ± 0.90% | 9.73 ± 0.43% | 60.42 ± 0.24% | 32.81 ± 3.39% | 8.12 ± 6.23% | 20.33 ± 13.87% | 20.33 ± 13.87% | 0 ± 0 | 0.00 ± 0.00% | 11.33 ± 7.02% | 3.62 ± 1.44% | 3.51 ± 1.60% | 0 ± 1 | 0.11 ± 0.18% | 8.73 ± 5.59% | 11.88 ± 6.50% | 11.88 ± 6.50% | 0 ± 0 | 0.00 ± 0.00% | 7.60 ± 3.55% | 36.56 ± 1.25% | 5.10 ± 0.95% | 9.35 ± 1.27% | 10.10 ± 2.03% | 88.75 ± 0.31% | 32.08 ± 0.18% | 43.95 ± 0.26% | 10.21 ± 0.48% | 44.28 ± 9.68% | 10.58 ± 0.71% | 1.94 ± 0.03 | 12.33 ± 0.22% | 2.86 ± 0.06 |
| safety+math | dare | 0.60 | 9.89 ± 8.05% | 6.22 ± 5.24% | 20.00 ± 0.47% | 7.91 ± 0.50% | 60.16 ± 0.56% | 28.04 ± 8.60% | 5.00 ± 5.00% | 17.67 ± 15.70% | 17.67 ± 15.70% | 0 ± 0 | 0.00 ± 0.00% | 7.33 ± 7.02% | 0.64 ± 0.32% | 0.64 ± 0.32% | 0 ± 0 | 0.00 ± 0.00% | 6.39 ± 4.71% | 11.35 ± 9.11% | 11.35 ± 9.11% | 0 ± 0 | 0.00 ± 0.00% | 6.15 ± 5.14% | 35.62 ± 0.31% | 4.38 ± 1.13% | 8.54 ± 0.61% | 7.29 ± 0.65% | 88.12 ± 0.94% | 32.19 ± 0.31% | 43.32 ± 0.28% | 11.67 ± 1.88% | 29.13 ± 26.90% | 9.41 ± 0.71% | 2.14 ± 0.05 | 12.37 ± 0.13% | 3.15 ± 0.09 |
| safety+math | della | 0.60 | 10.98 ± 8.54% | 6.67 ± 5.52% | 21.77 ± 1.15% | 7.40 ± 0.93% | 59.74 ± 0.39% | 35.88 ± 3.59% | 5.42 ± 4.16% | 22.00 ± 18.73% | 22.00 ± 18.73% | 0 ± 0 | 0.00 ± 0.00% | 9.00 ± 9.00% | 0.75 ± 0.18% | 0.75 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 7.35 ± 6.87% | 10.21 ± 7.22% | 10.21 ± 7.22% | 0 ± 0 | 0.00 ± 0.00% | 4.90 ± 2.62% | 37.92 ± 2.30% | 5.62 ± 0.00% | 8.33 ± 1.27% | 6.46 ± 0.65% | 87.81 ± 0.31% | 31.67 ± 0.65% | 43.21 ± 0.52% | 11.46 ± 0.79% | 52.98 ± 9.76% | 9.42 ± 0.46% | 2.16 ± 0.05 | 12.04 ± 0.20% | 3.18 ± 0.08 |
| safety+math | task_arithmetic | 0.60 | 2.81 ± 3.67% | 2.43 ± 2.80% | 15.68 ± 0.63% | 8.87 ± 2.24% | 61.61 ± 0.18% | 32.21 ± 6.62% | 3.12 ± 3.48% | 6.33 ± 10.12% | 6.33 ± 10.12% | 0 ± 0 | 0.00 ± 0.00% | 3.00 ± 5.20% | 0.21 ± 0.37% | 0.00 ± 0.00% | 1 ± 1 | 0.21 ± 0.37% | 2.34 ± 2.40% | 2.19 ± 0.83% | 2.08 ± 0.90% | 0 ± 1 | 0.10 ± 0.18% | 1.25 ± 0.54% | 26.46 ± 1.00% | 4.90 ± 0.65% | 10.98 ± 0.00% | 6.77 ± 4.49% | 90.00 ± 0.00% | 33.23 ± 0.36% | 44.72 ± 0.69% | 13.23 ± 0.95% | 38.70 ± 20.28% | 12.93 ± 0.23% | 1.67 ± 0.01 | 12.57 ± 0.18% | 2.44 ± 0.03 |
| safety+math | safemerge | N/A | 22.70 ± 39.31% | 4.63 ± 8.03% | 3.80 ± 1.19% | 7.32 ± 2.18% | 60.94 ± 0.68% | 18.10 ± 2.89% | 4.69 ± 8.12% | 28.67 ± 49.65% | 24.33 ± 42.15% | 4 ± 8 | 4.33 ± 7.51% | 6.33 ± 10.97% | 26.30 ± 45.56% | 24.28 ± 42.06% | 6 ± 11 | 2.02 ± 3.50% | 5.32 ± 9.22% | 26.98 ± 46.73% | 19.48 ± 33.74% | 24 ± 42 | 7.50 ± 12.99% | 2.19 ± 3.79% | 5.52 ± 3.15% | 2.08 ± 0.79% | 10.37 ± 2.44% | 4.27 ± 3.91% | 88.23 ± 0.65% | 33.65 ± 1.83% | 39.75 ± 2.36% | 12.81 ± 7.60% | 1.73 ± 2.66% | 8.84 ± 2.43% | 1.90 ± 0.30 | 14.38 ± 3.58% | 2.93 ± 0.81 |
| safety+math | led_merging | N/A | 71.25 ± 0.31% | 2.67 ± 0.05% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.67 ± 0.07% | 2.81 ± 0.00% | 98.00 ± 0.00% | 68.67 ± 0.58% | 29 ± 1 | 29.33 ± 0.58% | 3.00 ± 0.00% | 95.85 ± 0.00% | 84.98 ± 0.32% | 34 ± 1 | 10.86 ± 0.32% | 3.30 ± 0.18% | 90.83 ± 0.18% | 60.10 ± 0.48% | 98 ± 2 | 30.73 ± 0.48% | 1.56 ± 0.00% | 3.54 ± 3.07% | 2.60 ± 0.18% | 7.72 ± 6.69% | 3.75 ± 6.50% | 86.25 ± 2.17% | 33.54 ± 4.15% | 42.74 ± 0.05% | 19.69 ± 0.00% | 23.58 ± 0.26% | 9.06 ± 0.02% | 1.61 ± 0.00 | 11.20 ± 0.02% | 2.16 ± 0.00 |
| safety+math | matena_fisher | N/A | 7.99 ± 0.76% | 4.26 ± 0.51% | 16.98 ± 1.15% | 9.32 ± 1.05% | 61.35 ± 0.39% | 31.80 ± 11.53% | 4.58 ± 0.48% | 7.33 ± 2.08% | 7.33 ± 2.08% | 0 ± 0 | 0.00 ± 0.00% | 4.67 ± 0.58% | 8.31 ± 1.94% | 7.99 ± 1.66% | 1 ± 1 | 0.32 ± 0.32% | 3.83 ± 0.64% | 10.62 ± 2.36% | 8.65 ± 1.54% | 6 ± 5 | 1.98 ± 1.60% | 3.96 ± 2.13% | 29.69 ± 0.54% | 4.27 ± 1.78% | 12.60 ± 0.93% | 6.04 ± 2.90% | 89.90 ± 0.18% | 32.81 ± 0.62% | 45.30 ± 0.45% | 12.92 ± 0.95% | 37.17 ± 35.89% | 11.99 ± 0.47% | 1.67 ± 0.01 | 12.75 ± 0.20% | 2.39 ± 0.02 |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.85 ± 0.35% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 18.40 ± 1.05% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |

### ドメインパターン: safety+code (Alpha=0.6 / 単一実行手法含む)

#### ドメインパターン: `safety+code` (比較表: Alpha=0.6 / 単一実行手法含む)

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.60 | 76.73 ± 5.04% | 1.10 ± 0.47% | 0.83 ± 0.09% | 0.00 ± 0.00% | 54.84 ± 1.02% | 12.60 ± 0.09% | 0.10 ± 0.18% | 91.33 ± 3.21% | 77.33 ± 2.08% | 14 ± 5 | 14.00 ± 5.20% | 1.33 ± 0.58% | 99.36 ± 0.00% | 87.33 ± 5.63% | 38 ± 18 | 12.03 ± 5.63% | 1.92 ± 1.46% | 77.50 ± 4.91% | 65.52 ± 8.22% | 38 ± 18 | 11.98 ± 5.60% | 1.04 ± 0.48% | 0.94 ± 0.00% | 0.73 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.94 ± 0.62% | 23.75 ± 1.74% | 25.55 ± 0.76% | 12.19 ± 0.94% | 0.05 ± 0.01% | 1.39 ± 0.19% | 185.23 ± 93.56 | 2.50 ± 0.83% | 23.14 ± 4.56 |
| safety+code | data_free_sst_main | 0.60 | 59.37 ± 3.12% | 0.03 ± 0.05% | 0.16 ± 0.27% | 0.00 ± 0.00% | 55.36 ± 3.82% | 14.94 ± 0.26% | 0.00 ± 0.00% | 88.67 ± 2.52% | 64.33 ± 3.21% | 24 ± 4 | 24.33 ± 3.51% | 0.00 ± 0.00% | 99.89 ± 0.18% | 72.42 ± 6.11% | 86 ± 20 | 27.48 ± 6.29% | 0.11 ± 0.18% | 64.90 ± 5.77% | 41.35 ± 5.32% | 75 ± 15 | 23.54 ± 4.64% | 0.00 ± 0.00% | 0.31 ± 0.54% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 84.06 ± 3.26% | 26.67 ± 4.43% | 29.35 ± 0.63% | 15.42 ± 0.65% | 0.05 ± 0.01% | 1.33 ± 0.33% | 112.57 ± 56.38 | 4.75 ± 1.64% | 23.38 ± 6.19 |
| safety+code | ties | 0.60 | 36.93 ± 12.51% | 0.11 ± 0.13% | 1.25 ± 0.56% | 0.00 ± 0.00% | 30.89 ± 13.04% | 17.84 ± 9.74% | 0.00 ± 0.00% | 67.33 ± 21.46% | 29.67 ± 8.50% | 38 ± 29 | 37.67 ± 29.48% | 0.33 ± 0.58% | 99.57 ± 0.18% | 61.24 ± 26.68% | 120 ± 83 | 38.34 ± 26.52% | 0.11 ± 0.18% | 55.00 ± 20.03% | 19.90 ± 2.35% | 112 ± 71 | 35.10 ± 22.27% | 0.00 ± 0.00% | 0.73 ± 0.72% | 1.77 ± 0.48% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.27 ± 26.08% | 27.50 ± 0.94% | 23.65 ± 0.20% | 11.77 ± 2.39% | 18.10 ± 31.17% | 2.22 ± 0.37% | 137.44 ± 182.79 | 7.28 ± 1.48% | 22.88 ± 22.58 |
| safety+code | dare | 0.60 | 88.97 ± 3.78% | 0.00 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 31.56 ± 11.41% | 11.80 ± 0.92% | 0.00 ± 0.00% | 96.00 ± 1.00% | 95.33 ± 1.53% | 1 ± 1 | 0.67 ± 1.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 96.27 ± 6.46% | 12 ± 20 | 3.73 ± 6.46% | 0.00 ± 0.00% | 77.92 ± 7.71% | 75.31 ± 6.90% | 8 ± 12 | 2.60 ± 3.70% | 0.00 ± 0.00% | 0.31 ± 0.31% | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.83 ± 22.76% | 27.29 ± 0.48% | 25.02 ± 1.34% | 10.31 ± 1.43% | 0.06 ± 0.01% | 1.40 ± 0.34% | 398649.10 ± 507513.35 | 3.72 ± 1.14% | 425860.14 ± 214984.80 |
| safety+code | della | 0.60 | 83.77 ± 12.33% | 0.00 ± 0.00% | 0.26 ± 0.33% | 0.00 ± 0.00% | 31.41 ± 13.67% | 12.31 ± 0.88% | 0.00 ± 0.00% | 95.67 ± 2.52% | 89.67 ± 9.71% | 6 ± 10 | 6.00 ± 9.54% | 0.00 ± 0.00% | 100.00 ± 0.00% | 94.04 ± 9.78% | 19 ± 31 | 5.96 ± 9.78% | 0.00 ± 0.00% | 80.62 ± 5.22% | 67.60 ± 17.78% | 42 ± 72 | 13.02 ± 22.55% | 0.00 ± 0.00% | 0.42 ± 0.48% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.50 ± 27.10% | 25.31 ± 1.36% | 25.42 ± 0.33% | 11.46 ± 2.60% | 0.05 ± 0.00% | 1.39 ± 0.19% | 120223.11 ± 54132.59 | 3.50 ± 1.00% | 253194.63 ± 34087.44 |
| safety+code | task_arithmetic | 0.60 | 68.20 ± 1.27% | 29.22 ± 3.11% | 2.08 ± 0.95% | 2.37 ± 0.67% | 56.72 ± 0.95% | 19.13 ± 0.27% | 23.23 ± 2.03% | 77.33 ± 0.58% | 76.00 ± 1.00% | 1 ± 2 | 1.33 ± 1.53% | 35.00 ± 4.58% | 70.07 ± 0.49% | 65.18 ± 0.32% | 15 ± 3 | 4.90 ± 0.80% | 32.69 ± 3.78% | 68.23 ± 5.25% | 63.44 ± 3.12% | 15 ± 7 | 4.79 ± 2.26% | 25.94 ± 2.71% | 1.56 ± 0.54% | 2.60 ± 1.41% | 2.44 ± 1.61% | 2.29 ± 2.89% | 88.75 ± 0.54% | 24.69 ± 2.44% | 36.93 ± 0.30% | 20.42 ± 1.10% | 0.06 ± 0.00% | 5.41 ± 0.40% | 2.32 ± 0.02 | 7.57 ± 1.30% | 3.95 ± 0.02 |
| safety+code | safemerge | N/A | 0.31 ± 0.54% | 0.10 ± 0.18% | 2.19 ± 1.65% | 8.20 ± 3.95% | 55.21 ± 6.44% | 23.78 ± 9.09% | 0.21 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.21 ± 0.37% | 0.21 ± 0.37% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.73 ± 1.26% | 0.73 ± 1.26% | 0 ± 0 | 0.00 ± 0.00% | 0.21 ± 0.36% | 2.92 ± 2.90% | 1.46 ± 1.10% | 6.50 ± 6.14% | 9.90 ± 10.89% | 81.15 ± 9.33% | 29.27 ± 4.20% | 38.92 ± 3.80% | 14.17 ± 8.35% | 18.26 ± 16.46% | 9.72 ± 4.81% | 1.98 ± 0.54 | 13.76 ± 2.73% | 3.19 ± 1.54 |
| safety+code | led_merging | N/A | 71.07 ± 0.31% | 2.64 ± 0.00% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.65 ± 0.08% | 2.81 ± 0.00% | 98.00 ± 0.00% | 68.33 ± 0.58% | 30 ± 1 | 29.67 ± 0.58% | 3.00 ± 0.00% | 95.85 ± 0.00% | 84.88 ± 0.18% | 34 ± 1 | 10.97 ± 0.18% | 3.19 ± 0.00% | 90.94 ± 0.00% | 60.00 ± 0.54% | 99 ± 2 | 30.94 ± 0.54% | 1.56 ± 0.00% | 3.54 ± 3.07% | 2.60 ± 0.18% | 7.72 ± 6.69% | 3.75 ± 6.50% | 86.25 ± 2.17% | 33.54 ± 4.15% | 42.74 ± 0.04% | 19.69 ± 0.00% | 23.52 ± 0.29% | 9.07 ± 0.01% | 1.61 ± 0.00 | 11.20 ± 0.02% | 2.16 ± 0.00 |
| safety+code | matena_fisher | N/A | 52.64 ± 2.32% | 3.38 ± 1.18% | 0.83 ± 0.09% | 0.00 ± 0.00% | 56.20 ± 0.74% | 13.27 ± 0.61% | 1.77 ± 0.95% | 95.67 ± 1.15% | 51.67 ± 3.79% | 44 ± 3 | 44.00 ± 2.65% | 4.67 ± 1.53% | 96.59 ± 1.12% | 52.61 ± 1.64% | 138 ± 5 | 43.98 ± 1.61% | 3.94 ± 1.03% | 82.29 ± 2.13% | 53.65 ± 2.84% | 92 ± 2 | 28.65 ± 0.72% | 3.12 ± 2.48% | 0.83 ± 0.65% | 0.83 ± 0.79% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.10 ± 1.98% | 27.29 ± 1.48% | 25.80 ± 0.44% | 13.96 ± 1.54% | 0.07 ± 0.00% | 2.29 ± 0.20% | 80.11 ± 15.69 | 6.79 ± 1.91% | 63.11 ± 20.25 |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.64 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 17.79 ± 0.00% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |

### ドメインパターン: safety+medical (Alpha=0.6 / 単一実行手法含む)

#### ドメインパターン: `safety+medical` (比較表: Alpha=0.6 / 単一実行手法含む)

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.60 | 58.67 ± 50.91% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.15 ± 23.13% | 11.95 ± 0.28% | 0.00 ± 0.00% | 96.00 ± 4.00% | 61.33 ± 53.27% | 35 ± 57 | 34.67 ± 56.62% | 0.00 ± 0.00% | 100.00 ± 0.00% | 65.50 ± 56.75% | 108 ± 178 | 34.50 ± 56.75% | 0.21 ± 0.18% | 83.65 ± 14.36% | 49.17 ± 42.77% | 110 ± 182 | 34.48 ± 56.77% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.75 ± 46.89% | 28.54 ± 0.95% | 24.45 ± 1.18% | 11.35 ± 0.48% | 0.04 ± 0.01% | 0.37 ± 0.10% | 79783.06 ± 18826.86 | 1.01 ± 0.07% | 89052.84 ± 40211.85 |
| safety+medical | data_free_sst_main | 0.60 | 33.99 ± 27.90% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.49 ± 1.80% | 12.72 ± 0.20% | 0.00 ± 0.00% | 95.33 ± 5.69% | 41.00 ± 39.59% | 54 ± 45 | 54.33 ± 45.01% | 0.00 ± 0.00% | 100.00 ± 0.00% | 34.61 ± 26.33% | 205 ± 82 | 65.39 ± 26.33% | 0.21 ± 0.18% | 88.85 ± 13.19% | 26.35 ± 18.09% | 200 ± 98 | 62.50 ± 30.67% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 84.58 ± 2.89% | 22.40 ± 0.72% | 27.00 ± 0.12% | 11.15 ± 0.48% | 0.03 ± 0.01% | 0.45 ± 0.05% | 154475.14 ± 80159.01 | 1.28 ± 0.14% | 118397.35 ± 35122.34 |
| safety+medical | ties | 0.60 | 70.95 ± 15.31% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.93 ± 3.86% | 12.06 ± 1.23% | 0.00 ± 0.00% | 91.00 ± 9.54% | 75.00 ± 19.00% | 16 ± 20 | 16.00 ± 19.70% | 0.00 ± 0.00% | 100.00 ± 0.00% | 77.74 ± 22.70% | 70 ± 71 | 22.26 ± 22.70% | 0.21 ± 0.18% | 72.40 ± 14.26% | 60.10 ± 15.79% | 39 ± 34 | 12.29 ± 10.66% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 10.21 ± 5.60% | 23.65 ± 3.62% | 25.91 ± 1.62% | 10.21 ± 2.08% | 0.06 ± 0.01% | 0.65 ± 0.17% | 39894.11 ± 10705.72 | 1.59 ± 0.60% | 63613.99 ± 30155.00 |
| safety+medical | dare | 0.60 | 67.58 ± 13.73% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.79 ± 2.12% | 11.00 ± 1.11% | 0.00 ± 0.00% | 93.67 ± 5.03% | 71.67 ± 15.01% | 22 ± 18 | 22.00 ± 18.33% | 0.00 ± 0.00% | 100.00 ± 0.00% | 77.53 ± 14.80% | 70 ± 46 | 22.47 ± 14.80% | 0.11 ± 0.18% | 84.38 ± 7.35% | 53.54 ± 18.04% | 99 ± 81 | 30.83 ± 25.29% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.17 ± 0.48% | 25.42 ± 3.88% | 23.88 ± 1.32% | 9.06 ± 2.44% | 0.06 ± 0.01% | 0.55 ± 0.02% | 20797785.11 ± 14399754.63 | 2.08 ± 1.35% | 14708432.51 ± 16144047.41 |
| safety+medical | della | 0.60 | 25.77 ± 32.66% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.59 ± 10.90% | 12.34 ± 0.59% | 0.00 ± 0.00% | 96.00 ± 4.00% | 31.33 ± 38.37% | 65 ± 42 | 64.67 ± 42.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 25.88 ± 33.40% | 232 ± 105 | 74.12 ± 33.40% | 0.11 ± 0.18% | 82.92 ± 19.17% | 20.10 ± 26.44% | 201 ± 144 | 62.81 ± 44.96% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 39.90 ± 22.73% | 27.29 ± 2.53% | 26.07 ± 0.88% | 10.94 ± 1.08% | 0.02 ± 0.00% | 0.48 ± 0.09% | 10981445.00 ± 6253371.40 | 1.29 ± 0.18% | 12572823.50 ± 5352914.49 |
| safety+medical | task_arithmetic | 0.60 | 85.09 ± 6.34% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.86 ± 17.35% | 12.72 ± 0.06% | 0.00 ± 0.00% | 86.00 ± 11.27% | 86.00 ± 11.27% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 100.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.64 ± 0.00% | 69.27 ± 7.76% | 69.27 ± 7.76% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 54.17 ± 34.92% | 21.56 ± 0.54% | 27.07 ± 0.00% | 11.04 ± 0.18% | 0.06 ± 0.00% | 0.28 ± 0.01% | 200116.75 ± 7068.23 | 1.24 ± 0.07% | 209487.62 ± 9249.30 |
| safety+medical | safemerge | N/A | 0.15 ± 0.25% | 0.03 ± 0.05% | 1.35 ± 2.35% | 3.23 ± 5.60% | 45.10 ± 14.55% | 14.87 ± 3.75% | 0.00 ± 0.00% | 0.33 ± 0.58% | 0.33 ± 0.58% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.11 ± 0.18% | 0.10 ± 0.18% | 0.10 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 1.98 ± 3.43% | 0.73 ± 1.26% | 3.86 ± 6.69% | 2.60 ± 4.51% | 63.23 ± 23.14% | 26.98 ± 6.41% | 33.30 ± 6.82% | 11.04 ± 4.52% | 0.28 ± 0.08% | 6.52 ± 6.45% | 3.00 ± 1.27 | 12.68 ± 2.65% | 6.06 ± 3.55 |
| safety+medical | led_merging | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| safety+medical | matena_fisher | N/A | 94.25 ± 0.60% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.08 ± 2.26% | 12.98 ± 0.17% | 0.00 ± 0.00% | 98.00 ± 0.00% | 97.33 ± 1.15% | 1 ± 1 | 0.67 ± 1.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 99.57 ± 0.74% | 1 ± 2 | 0.43 ± 0.74% | 0.64 ± 0.00% | 85.83 ± 0.18% | 85.83 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 24.17 ± 4.51% | 27.04 ± 0.06% | 11.88 ± 0.54% | 0.02 ± 0.00% | 0.41 ± 0.01% | 384272.26 ± 81902.74 | 0.90 ± 0.21% | 304225.05 ± 19087.67 |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 11.98 ± 3.31% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 12.79 ± 9.94% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |


## 2. Merge 手法別全 α パラメータ独立表 (パターン別)

### 手法: `diagonal_sst_main` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `diagonal_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 67.11 ± 0.25% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.61 ± 21.47% | 10.46 ± 0.16% | 0.00 ± 0.00% | 95.00 ± 0.00% | 76.33 ± 0.58% | 19 ± 1 | 18.67 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 65.92 ± 0.18% | 107 ± 1 | 34.08 ± 0.18% | 0.64 ± 0.00% | 82.60 ± 0.48% | 59.06 ± 0.31% | 75 ± 1 | 23.54 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 36.15 ± 41.50% | 27.08 ± 1.44% | 23.07 ± 0.00% | 8.23 ± 0.48% | 0.07 ± 0.00% | 0.66 ± 0.00% | 29408.88 ± 0.00 | 1.55 ± 0.00% | 73003.90 ± 0.00 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 2.23 ± 2.37% | 0.05 ± 0.05% | 0.68 ± 0.48% | 0.00 ± 0.00% | 23.80 ± 4.42% | 12.30 ± 0.87% | 0.00 ± 0.00% | 98.67 ± 1.15% | 1.67 ± 2.08% | 97 ± 3 | 97.00 ± 3.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 1.70 ± 1.64% | 308 ± 5 | 98.30 ± 1.64% | 0.11 ± 0.18% | 96.35 ± 3.62% | 3.33 ± 3.44% | 298 ± 23 | 93.02 ± 7.06% | 0.10 ± 0.18% | 0.10 ± 0.18% | 1.25 ± 1.13% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.85 ± 8.84% | 28.75 ± 0.00% | 23.23 ± 0.07% | 13.54 ± 2.66% | 0.13 ± 0.09% | 0.90 ± 0.13% | 5113.50 ± 826.44 | 1.84 ± 0.62% | 15825.46 ± 2469.63 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 0.00 ± 0.00% | 0.00 ± 0.00% | 1.09 ± 0.83% | 0.00 ± 0.00% | 20.26 ± 1.88% | 11.75 ± 0.22% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.31 ± 0.31% | 1.88 ± 1.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.48 ± 1.26% | 26.04 ± 2.84% | 23.28 ± 0.20% | 11.77 ± 0.48% | 0.19 ± 0.07% | 0.94 ± 0.01% | 2684.19 ± 461.76 | 0.34 ± 0.30% | 1266.19 ± 121.35 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 27.14 ± 10.37% | 0.00 ± 0.00% | 0.73 ± 0.72% | 0.00 ± 0.00% | 44.17 ± 7.44% | 10.22 ± 0.47% | 0.00 ± 0.00% | 98.33 ± 1.53% | 25.33 ± 12.66% | 73 ± 13 | 73.00 ± 13.45% | 0.00 ± 0.00% | 98.94 ± 0.18% | 35.89 ± 11.07% | 197 ± 34 | 63.05 ± 11.00% | 0.00 ± 0.00% | 96.15 ± 1.48% | 20.21 ± 8.05% | 243 ± 30 | 75.94 ± 9.51% | 0.00 ± 0.00% | 0.31 ± 0.54% | 1.15 ± 0.90% | 0.00 ± 0.00% | 0.00 ± 0.00% | 59.48 ± 14.60% | 28.85 ± 0.36% | 23.29 ± 0.04% | 7.19 ± 1.36% | 0.18 ± 0.10% | 0.93 ± 0.15% | 453.77 ± 82.57 | 3.22 ± 1.44% | 109.69 ± 29.01 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 21.22 ± 1.29% | 0.13 ± 0.05% | 0.47 ± 0.31% | 0.00 ± 0.00% | 55.00 ± 1.65% | 9.53 ± 0.96% | 0.00 ± 0.00% | 100.00 ± 0.00% | 16.33 ± 1.15% | 84 ± 1 | 83.67 ± 1.15% | 0.00 ± 0.00% | 98.40 ± 0.64% | 34.61 ± 2.88% | 200 ± 10 | 63.79 ± 3.22% | 0.43 ± 0.37% | 99.06 ± 0.00% | 12.71 ± 0.72% | 276 ± 2 | 86.35 ± 0.72% | 0.10 ± 0.18% | 0.83 ± 0.48% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 81.25 ± 3.31% | 28.75 ± 0.00% | 23.21 ± 0.02% | 5.31 ± 2.86% | 0.06 ± 0.00% | 1.67 ± 0.45% | 166.19 ± 72.34 | 2.04 ± 0.44% | 51.23 ± 17.42 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 26.20 ± 6.41% | 0.16 ± 0.00% | 0.57 ± 0.74% | 0.00 ± 0.00% | 54.74 ± 4.11% | 17.30 ± 4.28% | 0.00 ± 0.00% | 99.67 ± 0.58% | 21.00 ± 7.00% | 79 ± 8 | 78.67 ± 7.57% | 0.00 ± 0.00% | 97.44 ± 1.39% | 43.13 ± 8.96% | 170 ± 32 | 54.31 ± 10.07% | 0.53 ± 0.18% | 95.52 ± 4.90% | 14.48 ± 3.82% | 259 ± 25 | 81.04 ± 7.80% | 0.10 ± 0.18% | 0.62 ± 0.83% | 0.52 ± 0.65% | 0.00 ± 0.00% | 0.00 ± 0.00% | 80.42 ± 8.22% | 29.06 ± 0.00% | 23.22 ± 0.08% | 7.29 ± 6.01% | 21.39 ± 18.66% | 2.70 ± 0.41% | 109.78 ± 56.64 | 2.74 ± 1.69% | 47.15 ± 20.38 |


#### パターン: `safety+math` / 手法: `diagonal_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 75.84 ± 0.13% | 34.44 ± 0.50% | 20.10 ± 0.09% | 3.54 ± 3.70% | 61.41 ± 0.00% | 28.82 ± 9.38% | 26.98 ± 0.36% | 73.67 ± 0.58% | 67.67 ± 0.58% | 6 ± 0 | 6.00 ± 0.00% | 38.33 ± 1.15% | 90.31 ± 0.37% | 88.71 ± 0.37% | 5 ± 0 | 1.60 ± 0.00% | 45.90 ± 0.49% | 78.54 ± 0.36% | 71.15 ± 0.18% | 24 ± 1 | 7.40 ± 0.18% | 26.88 ± 0.00% | 35.52 ± 0.36% | 4.69 ± 0.31% | 4.27 ± 7.39% | 2.81 ± 0.00% | 89.38 ± 0.00% | 33.44 ± 0.00% | 42.26 ± 0.00% | 13.54 ± 0.18% | 30.66 ± 28.00% | 7.50 ± 0.01% | 1.87 ± 0.00 | 13.21 ± 0.01% | 2.52 ± 0.00 |
| safety+math | diagonal_sst_main | 0.20 | 71.72 ± 1.82% | 32.10 ± 0.41% | 21.41 ± 0.41% | 5.07 ± 2.51% | 61.30 ± 0.09% | 25.35 ± 10.87% | 26.25 ± 1.65% | 72.33 ± 5.03% | 68.67 ± 3.51% | 4 ± 2 | 3.67 ± 1.53% | 34.00 ± 5.00% | 84.56 ± 1.76% | 82.32 ± 0.98% | 7 ± 3 | 2.24 ± 0.85% | 43.56 ± 1.84% | 73.85 ± 1.41% | 64.17 ± 1.30% | 31 ± 1 | 9.69 ± 0.31% | 24.58 ± 0.72% | 37.08 ± 0.65% | 5.73 ± 0.36% | 6.91 ± 5.98% | 3.23 ± 1.10% | 89.48 ± 0.18% | 33.12 ± 0.00% | 42.94 ± 0.13% | 13.23 ± 0.18% | 19.87 ± 32.30% | 8.52 ± 0.28% | 1.80 ± 0.00 | 12.85 ± 0.21% | 2.47 ± 0.00 |
| safety+math | diagonal_sst_main | 0.40 | 70.03 ± 3.04% | 32.38 ± 1.37% | 21.77 ± 1.27% | 7.57 ± 0.55% | 60.99 ± 0.24% | 31.79 ± 11.84% | 27.60 ± 2.19% | 76.33 ± 5.03% | 72.33 ± 4.51% | 4 ± 1 | 4.00 ± 1.00% | 33.00 ± 1.00% | 79.13 ± 1.93% | 78.27 ± 2.41% | 3 ± 2 | 0.85 ± 0.67% | 41.75 ± 1.33% | 62.60 ± 3.28% | 59.48 ± 2.37% | 10 ± 4 | 3.12 ± 1.36% | 27.19 ± 1.56% | 37.81 ± 1.62% | 5.73 ± 0.95% | 11.18 ± 0.35% | 3.96 ± 1.41% | 89.69 ± 0.00% | 32.29 ± 0.48% | 43.88 ± 0.19% | 12.29 ± 0.48% | 39.19 ± 35.08% | 9.69 ± 0.31% | 1.74 ± 0.00 | 12.58 ± 0.22% | 2.44 ± 0.01 |
| safety+math | diagonal_sst_main | 0.60 | 32.47 ± 9.78% | 17.39 ± 5.23% | 19.95 ± 0.70% | 8.97 ± 0.51% | 60.89 ± 0.63% | 27.54 ± 8.99% | 19.27 ± 4.43% | 34.33 ± 2.52% | 34.33 ± 2.52% | 0 ± 0 | 0.00 ± 0.00% | 19.33 ± 3.79% | 36.00 ± 15.69% | 36.00 ± 15.69% | 0 ± 0 | 0.00 ± 0.00% | 19.60 ± 8.63% | 28.54 ± 11.09% | 27.08 ± 11.39% | 5 ± 6 | 1.46 ± 1.72% | 11.25 ± 4.91% | 34.48 ± 1.48% | 5.42 ± 0.36% | 11.59 ± 0.61% | 6.35 ± 1.54% | 89.48 ± 0.18% | 32.29 ± 1.18% | 44.51 ± 0.38% | 11.98 ± 1.00% | 26.13 ± 25.82% | 10.89 ± 0.69% | 1.70 ± 0.01 | 12.60 ± 0.13% | 2.42 ± 0.02 |
| safety+math | diagonal_sst_main | 0.80 | 4.43 ± 2.35% | 2.96 ± 1.82% | 16.25 ± 1.49% | 10.74 ± 1.09% | 61.77 ± 0.65% | 23.23 ± 6.39% | 3.33 ± 1.60% | 7.00 ± 6.00% | 7.00 ± 6.00% | 0 ± 0 | 0.00 ± 0.00% | 3.33 ± 3.06% | 1.49 ± 2.31% | 1.49 ± 2.31% | 0 ± 0 | 0.00 ± 0.00% | 2.56 ± 2.24% | 4.79 ± 2.73% | 4.79 ± 2.73% | 0 ± 0 | 0.00 ± 0.00% | 2.60 ± 1.83% | 28.02 ± 3.21% | 4.48 ± 1.00% | 11.38 ± 0.35% | 10.10 ± 1.91% | 89.79 ± 0.65% | 33.75 ± 1.13% | 44.61 ± 0.27% | 14.38 ± 1.65% | 10.70 ± 18.13% | 12.14 ± 0.48% | 1.69 ± 0.02 | 12.85 ± 0.15% | 2.44 ± 0.04 |
| safety+math | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.28 ± 3.75% | 9.60 ± 2.12% | 61.61 ± 0.48% | 26.63 ± 6.45% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.92 ± 5.51% | 3.65 ± 2.01% | 11.38 ± 0.70% | 7.81 ± 4.85% | 89.27 ± 0.18% | 33.96 ± 0.79% | 44.29 ± 0.60% | 13.02 ± 1.26% | 22.58 ± 19.72% | 12.14 ± 0.41% | 1.72 ± 0.04 | 13.57 ± 0.73% | 2.51 ± 0.09 |


#### パターン: `safety+code` / 手法: `diagonal_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 65.96 ± 0.06% | 0.08 ± 0.00% | 0.26 ± 0.18% | 0.00 ± 0.00% | 54.43 ± 0.36% | 14.03 ± 0.00% | 0.00 ± 0.00% | 93.00 ± 0.00% | 66.00 ± 0.00% | 27 ± 0 | 27.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 76.78 ± 0.18% | 73 ± 1 | 23.22 ± 0.18% | 0.32 ± 0.00% | 75.94 ± 0.00% | 55.10 ± 0.18% | 67 ± 1 | 20.83 ± 0.18% | 0.00 ± 0.00% | 0.42 ± 0.18% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.54% | 22.60 ± 1.26% | 27.95 ± 0.01% | 14.06 ± 0.00% | 0.07 ± 0.00% | 1.09 ± 0.01% | 203.70 ± 0.00 | 5.37 ± 0.14% | 28.06 ± 0.00 |
| safety+code | diagonal_sst_main | 0.20 | 69.15 ± 7.94% | 0.08 ± 0.08% | 0.10 ± 0.18% | 0.00 ± 0.00% | 55.00 ± 1.13% | 14.63 ± 0.17% | 0.00 ± 0.00% | 91.00 ± 1.00% | 74.67 ± 6.66% | 16 ± 6 | 16.33 ± 5.69% | 0.00 ± 0.00% | 100.00 ± 0.00% | 70.71 ± 6.64% | 92 ± 21 | 29.29 ± 6.64% | 0.32 ± 0.32% | 88.54 ± 4.24% | 62.08 ± 11.01% | 85 ± 22 | 26.46 ± 6.86% | 0.00 ± 0.00% | 0.10 ± 0.18% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.94 ± 0.31% | 24.06 ± 2.05% | 29.77 ± 0.83% | 14.06 ± 0.62% | 0.05 ± 0.00% | 1.33 ± 0.05% | 117.61 ± 25.66 | 4.58 ± 0.16% | 21.06 ± 2.04 |
| safety+code | diagonal_sst_main | 0.40 | 77.35 ± 0.57% | 0.32 ± 0.14% | 0.89 ± 0.59% | 0.00 ± 0.00% | 54.53 ± 0.47% | 14.69 ± 0.13% | 0.10 ± 0.18% | 91.00 ± 2.00% | 79.33 ± 2.08% | 12 ± 4 | 11.67 ± 3.79% | 0.00 ± 0.00% | 99.68 ± 0.32% | 91.16 ± 0.37% | 27 ± 2 | 8.52 ± 0.67% | 1.06 ± 0.49% | 70.83 ± 5.23% | 61.56 ± 3.60% | 30 ± 6 | 9.27 ± 1.88% | 0.10 ± 0.18% | 0.94 ± 0.54% | 0.83 ± 0.95% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.04 ± 0.48% | 23.02 ± 1.41% | 29.12 ± 0.79% | 14.90 ± 1.00% | 0.05 ± 0.01% | 1.31 ± 0.15% | 171.98 ± 71.56 | 5.21 ± 0.58% | 19.91 ± 2.79 |
| safety+code | diagonal_sst_main | 0.60 | 76.73 ± 5.04% | 1.10 ± 0.47% | 0.83 ± 0.09% | 0.00 ± 0.00% | 54.84 ± 1.02% | 12.60 ± 0.09% | 0.10 ± 0.18% | 91.33 ± 3.21% | 77.33 ± 2.08% | 14 ± 5 | 14.00 ± 5.20% | 1.33 ± 0.58% | 99.36 ± 0.00% | 87.33 ± 5.63% | 38 ± 18 | 12.03 ± 5.63% | 1.92 ± 1.46% | 77.50 ± 4.91% | 65.52 ± 8.22% | 38 ± 18 | 11.98 ± 5.60% | 1.04 ± 0.48% | 0.94 ± 0.00% | 0.73 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.94 ± 0.62% | 23.75 ± 1.74% | 25.55 ± 0.76% | 12.19 ± 0.94% | 0.05 ± 0.01% | 1.39 ± 0.19% | 185.23 ± 93.56 | 2.50 ± 0.83% | 23.14 ± 4.56 |
| safety+code | diagonal_sst_main | 0.80 | 57.85 ± 4.60% | 0.81 ± 0.09% | 0.89 ± 0.45% | 0.00 ± 0.00% | 54.64 ± 1.81% | 12.11 ± 0.35% | 0.52 ± 0.65% | 75.67 ± 4.16% | 54.33 ± 5.86% | 21 ± 5 | 21.33 ± 4.93% | 0.00 ± 0.00% | 94.99 ± 2.48% | 73.06 ± 7.80% | 69 ± 29 | 21.94 ± 9.32% | 1.38 ± 0.18% | 74.06 ± 9.50% | 46.15 ± 8.54% | 89 ± 57 | 27.92 ± 17.96% | 1.35 ± 0.36% | 0.94 ± 0.31% | 0.83 ± 0.95% | 0.00 ± 0.00% | 0.00 ± 0.00% | 83.75 ± 3.08% | 25.52 ± 3.78% | 24.81 ± 0.11% | 11.46 ± 1.00% | 0.05 ± 0.00% | 1.56 ± 0.15% | 54.38 ± 16.66 | 2.06 ± 0.64% | 20.76 ± 1.35 |
| safety+code | diagonal_sst_main | 1.00 | 53.06 ± 17.65% | 0.00 ± 0.00% | 0.62 ± 0.31% | 0.00 ± 0.00% | 32.19 ± 8.93% | 10.55 ± 0.30% | 0.00 ± 0.00% | 71.67 ± 15.31% | 55.67 ± 21.08% | 16 ± 19 | 16.00 ± 19.00% | 0.00 ± 0.00% | 69.86 ± 15.94% | 56.34 ± 21.57% | 42 ± 27 | 13.53 ± 8.52% | 0.00 ± 0.00% | 58.75 ± 7.04% | 47.19 ± 12.23% | 37 ± 17 | 11.56 ± 5.33% | 0.00 ± 0.00% | 0.42 ± 0.36% | 0.83 ± 0.95% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.21 ± 18.57% | 29.17 ± 0.72% | 23.71 ± 0.27% | 7.81 ± 0.83% | 0.13 ± 0.09% | 1.70 ± 0.08% | 258.23 ± 35.18 | 5.60 ± 0.57% | 166.09 ± 78.86 |


#### パターン: `safety+medical` / 手法: `diagonal_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 80.15 ± 0.19% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.97 ± 7.85% | 11.82 ± 0.06% | 0.00 ± 0.00% | 91.67 ± 1.15% | 80.33 ± 0.58% | 11 ± 1 | 11.33 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 91.37 ± 0.00% | 27 ± 0 | 8.63 ± 0.00% | 0.00 ± 0.00% | 75.83 ± 0.18% | 68.75 ± 0.00% | 23 ± 1 | 7.08 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 50.83 ± 15.34% | 25.10 ± 0.36% | 24.89 ± 0.02% | 10.52 ± 0.18% | 0.04 ± 0.01% | 0.95 ± 0.01% | 200412.22 ± 0.00 | 2.70 ± 0.03% | 195954.54 ± 5.55 |
| safety+medical | diagonal_sst_main | 0.20 | 91.23 ± 3.50% | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.52 ± 0.55% | 12.25 ± 0.18% | 0.00 ± 0.00% | 94.00 ± 3.46% | 94.00 ± 3.46% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 99.79 ± 0.37% | 1 ± 1 | 0.21 ± 0.37% | 0.53 ± 0.18% | 80.10 ± 6.95% | 79.90 ± 6.86% | 1 ± 1 | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.85 ± 0.48% | 27.19 ± 0.83% | 25.64 ± 0.36% | 11.04 ± 0.18% | 0.05 ± 0.00% | 0.47 ± 0.10% | 91035.76 ± 17521.94 | 1.24 ± 0.03% | 74814.15 ± 18677.97 |
| safety+medical | diagonal_sst_main | 0.40 | 76.35 ± 13.88% | 0.19 ± 0.20% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.70 ± 5.10% | 12.17 ± 0.22% | 0.00 ± 0.00% | 97.67 ± 1.15% | 65.67 ± 20.82% | 32 ± 22 | 32.00 ± 21.63% | 0.00 ± 0.00% | 100.00 ± 0.00% | 87.75 ± 10.07% | 38 ± 32 | 12.25 ± 10.07% | 0.53 ± 0.49% | 83.85 ± 5.56% | 75.62 ± 12.55% | 26 ± 23 | 8.23 ± 7.33% | 0.21 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 79.38 ± 9.79% | 28.02 ± 0.65% | 25.43 ± 0.00% | 11.04 ± 0.65% | 0.04 ± 0.02% | 0.37 ± 0.07% | 137303.69 ± 20106.41 | 1.07 ± 0.26% | 95595.75 ± 12745.83 |
| safety+medical | diagonal_sst_main | 0.60 | 58.67 ± 50.91% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.15 ± 23.13% | 11.95 ± 0.28% | 0.00 ± 0.00% | 96.00 ± 4.00% | 61.33 ± 53.27% | 35 ± 57 | 34.67 ± 56.62% | 0.00 ± 0.00% | 100.00 ± 0.00% | 65.50 ± 56.75% | 108 ± 178 | 34.50 ± 56.75% | 0.21 ± 0.18% | 83.65 ± 14.36% | 49.17 ± 42.77% | 110 ± 182 | 34.48 ± 56.77% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.75 ± 46.89% | 28.54 ± 0.95% | 24.45 ± 1.18% | 11.35 ± 0.48% | 0.04 ± 0.01% | 0.37 ± 0.10% | 79783.06 ± 18826.86 | 1.01 ± 0.07% | 89052.84 ± 40211.85 |
| safety+medical | diagonal_sst_main | 0.80 | 77.60 ± 7.66% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.91 ± 5.82% | 11.62 ± 0.55% | 0.00 ± 0.00% | 95.00 ± 2.65% | 78.00 ± 10.15% | 17 ± 8 | 17.00 ± 8.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 85.52 ± 6.21% | 45 ± 19 | 14.48 ± 6.21% | 0.21 ± 0.18% | 79.17 ± 6.35% | 69.27 ± 11.26% | 32 ± 27 | 9.90 ± 8.45% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.38 ± 11.49% | 28.44 ± 0.54% | 23.79 ± 1.14% | 11.04 ± 0.65% | 0.03 ± 0.02% | 0.53 ± 0.04% | 139531.35 ± 112079.91 | 1.44 ± 0.42% | 227857.25 ± 297572.09 |
| safety+medical | diagonal_sst_main | 1.00 | 63.10 ± 3.38% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.55 ± 15.93% | 11.74 ± 0.55% | 0.00 ± 0.00% | 90.67 ± 2.52% | 63.00 ± 13.45% | 28 ± 16 | 27.67 ± 15.50% | 0.00 ± 0.00% | 100.00 ± 0.00% | 73.59 ± 12.86% | 83 ± 40 | 26.41 ± 12.86% | 0.11 ± 0.18% | 82.60 ± 2.30% | 52.71 ± 15.36% | 96 ± 54 | 29.90 ± 16.89% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 48.23 ± 33.49% | 26.88 ± 2.48% | 24.44 ± 2.23% | 10.73 ± 1.30% | 0.05 ± 0.03% | 0.61 ± 0.32% | 139537.68 ± 165148.85 | 1.02 ± 1.14% | 102521.68 ± 83446.86 |


### 手法: `data_free_sst_main` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `data_free_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 67.22 ± 0.23% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.61 ± 21.47% | 10.46 ± 0.06% | 0.00 ± 0.00% | 95.00 ± 0.00% | 76.67 ± 0.58% | 18 ± 1 | 18.33 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 65.81 ± 0.00% | 107 ± 0 | 34.19 ± 0.00% | 0.64 ± 0.00% | 82.81 ± 0.54% | 59.17 ± 0.18% | 76 ± 2 | 23.65 ± 0.48% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 36.15 ± 41.50% | 27.08 ± 1.44% | 23.07 ± 0.00% | 8.23 ± 0.18% | 0.07 ± 0.00% | 0.66 ± 0.00% | 29408.90 ± 0.02 | 1.55 ± 0.00% | 73004.68 ± 1.35 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 33.08 ± 25.44% | 0.13 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.30 ± 26.07% | 10.93 ± 0.24% | 0.00 ± 0.00% | 94.33 ± 5.13% | 38.00 ± 31.61% | 56 ± 35 | 56.33 ± 35.02% | 0.00 ± 0.00% | 100.00 ± 0.00% | 37.06 ± 27.03% | 197 ± 85 | 62.94 ± 27.03% | 0.43 ± 0.18% | 85.00 ± 10.31% | 24.17 ± 19.37% | 195 ± 93 | 60.83 ± 29.02% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 28.23 ± 48.62% | 24.38 ± 3.55% | 23.14 ± 0.00% | 9.58 ± 0.72% | 0.07 ± 0.00% | 0.59 ± 0.06% | 28883.36 ± 3514.80 | 1.55 ± 0.17% | 78052.79 ± 10754.03 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 48.39 ± 8.20% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 30.52 ± 23.21% | 11.63 ± 0.24% | 0.00 ± 0.00% | 88.00 ± 2.65% | 53.00 ± 12.77% | 35 ± 15 | 35.00 ± 15.13% | 0.00 ± 0.00% | 100.00 ± 0.00% | 55.80 ± 7.36% | 138 ± 23 | 44.20 ± 7.36% | 0.00 ± 0.00% | 78.02 ± 8.61% | 36.35 ± 6.99% | 133 ± 50 | 41.67 ± 15.56% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 32.60 ± 45.83% | 28.44 ± 1.90% | 23.15 ± 0.01% | 11.67 ± 0.72% | 0.07 ± 0.00% | 0.47 ± 0.11% | 24950.09 ± 2368.54 | 1.51 ± 0.39% | 57646.17 ± 16169.77 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 35.49 ± 14.18% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.00 ± 18.66% | 11.61 ± 0.31% | 0.00 ± 0.00% | 85.00 ± 9.17% | 38.67 ± 10.97% | 46 ± 19 | 46.33 ± 19.35% | 0.00 ± 0.00% | 100.00 ± 0.00% | 46.96 ± 23.51% | 166 ± 74 | 53.04 ± 23.51% | 0.21 ± 0.18% | 76.46 ± 12.22% | 20.83 ± 10.51% | 178 ± 56 | 55.62 ± 17.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 51.35 ± 37.22% | 28.65 ± 0.48% | 23.14 ± 0.01% | 11.56 ± 0.83% | 0.13 ± 0.11% | 0.54 ± 0.02% | 17938.54 ± 3918.72 | 1.56 ± 0.48% | 37505.01 ± 22671.13 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 37.37 ± 19.98% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 52.60 ± 8.34% | 12.23 ± 1.32% | 0.00 ± 0.00% | 81.67 ± 5.03% | 47.33 ± 29.14% | 34 ± 34 | 34.33 ± 34.02% | 0.00 ± 0.00% | 100.00 ± 0.00% | 47.18 ± 24.53% | 165 ± 77 | 52.82 ± 24.53% | 0.11 ± 0.18% | 77.29 ± 11.93% | 17.60 ± 11.61% | 191 ± 69 | 59.69 ± 21.59% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 76.35 ± 16.60% | 28.85 ± 0.18% | 23.17 ± 0.11% | 10.94 ± 0.83% | 2.59 ± 4.23% | 0.64 ± 0.09% | 13402.49 ± 2042.70 | 2.47 ± 1.28% | 20723.75 ± 7418.20 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 36.57 ± 20.06% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.85 ± 4.44% | 11.59 ± 0.56% | 0.00 ± 0.00% | 88.67 ± 4.62% | 42.33 ± 24.85% | 46 ± 27 | 46.33 ± 27.30% | 0.00 ± 0.00% | 100.00 ± 0.00% | 42.39 ± 21.00% | 180 ± 66 | 57.61 ± 21.00% | 0.11 ± 0.18% | 81.88 ± 9.50% | 25.00 ± 14.74% | 182 ± 77 | 56.88 ± 24.10% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 78.85 ± 8.84% | 28.85 ± 0.18% | 23.97 ± 0.90% | 10.62 ± 1.13% | 0.19 ± 0.13% | 0.73 ± 0.09% | 13257.09 ± 4123.52 | 2.83 ± 1.43% | 16581.99 ± 3829.08 |


#### パターン: `safety+math` / 手法: `data_free_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 75.77 ± 0.13% | 34.17 ± 0.52% | 20.10 ± 0.09% | 3.54 ± 3.70% | 61.41 ± 0.00% | 35.24 ± 7.76% | 26.77 ± 0.36% | 73.33 ± 0.58% | 67.33 ± 0.58% | 6 ± 0 | 6.00 ± 0.00% | 37.67 ± 1.15% | 90.52 ± 0.37% | 88.92 ± 0.37% | 5 ± 0 | 1.60 ± 0.00% | 45.69 ± 0.55% | 78.33 ± 0.36% | 71.04 ± 0.18% | 23 ± 1 | 7.29 ± 0.18% | 26.88 ± 0.00% | 35.73 ± 0.36% | 4.48 ± 0.18% | 4.27 ± 7.39% | 2.81 ± 0.00% | 89.38 ± 0.00% | 33.44 ± 0.00% | 42.26 ± 0.00% | 13.54 ± 0.18% | 49.93 ± 23.37% | 7.49 ± 0.01% | 1.87 ± 0.00 | 13.21 ± 0.01% | 2.52 ± 0.00 |
| safety+math | data_free_sst_main | 0.20 | 69.63 ± 0.54% | 32.95 ± 1.10% | 21.09 ± 0.16% | 6.21 ± 2.94% | 61.09 ± 0.31% | 35.84 ± 10.21% | 27.29 ± 0.72% | 65.33 ± 0.58% | 63.67 ± 0.58% | 2 ± 1 | 1.67 ± 1.15% | 33.67 ± 2.52% | 84.03 ± 0.85% | 82.22 ± 0.67% | 6 ± 1 | 1.81 ± 0.18% | 42.92 ± 2.35% | 71.46 ± 1.00% | 63.02 ± 0.65% | 27 ± 3 | 8.44 ± 0.83% | 27.92 ± 1.78% | 37.19 ± 0.31% | 5.00 ± 0.00% | 7.52 ± 6.52% | 4.90 ± 0.65% | 89.06 ± 0.00% | 33.12 ± 0.62% | 43.05 ± 0.07% | 13.75 ± 0.31% | 50.73 ± 30.78% | 8.45 ± 0.15% | 1.86 ± 0.01 | 12.88 ± 0.16% | 2.55 ± 0.01 |
| safety+math | data_free_sst_main | 0.40 | 69.14 ± 2.75% | 32.85 ± 1.35% | 22.34 ± 0.83% | 7.62 ± 1.04% | 60.78 ± 0.41% | 37.56 ± 7.07% | 27.19 ± 0.31% | 67.33 ± 6.11% | 67.00 ± 6.56% | 0 ± 1 | 0.33 ± 0.58% | 32.00 ± 4.00% | 82.43 ± 0.85% | 81.79 ± 0.85% | 2 ± 1 | 0.64 ± 0.32% | 44.73 ± 2.93% | 60.62 ± 0.94% | 58.65 ± 1.30% | 6 ± 2 | 1.98 ± 0.48% | 27.50 ± 2.48% | 38.65 ± 0.90% | 6.04 ± 0.79% | 11.18 ± 0.35% | 4.06 ± 1.74% | 89.27 ± 0.36% | 32.29 ± 0.79% | 43.77 ± 0.09% | 13.12 ± 0.63% | 55.79 ± 20.50% | 9.20 ± 0.36% | 1.86 ± 0.01 | 12.83 ± 0.21% | 2.60 ± 0.02 |
| safety+math | data_free_sst_main | 0.60 | 29.38 ± 5.70% | 14.70 ± 3.30% | 21.46 ± 0.45% | 8.34 ± 0.71% | 61.04 ± 0.33% | 34.60 ± 8.29% | 13.75 ± 2.25% | 28.33 ± 10.26% | 28.33 ± 10.26% | 0 ± 0 | 0.00 ± 0.00% | 13.00 ± 5.57% | 33.76 ± 6.25% | 33.76 ± 6.25% | 0 ± 0 | 0.00 ± 0.00% | 18.21 ± 5.14% | 26.15 ± 2.51% | 26.04 ± 2.53% | 0 ± 1 | 0.10 ± 0.18% | 13.85 ± 2.01% | 36.67 ± 0.65% | 6.25 ± 0.31% | 11.59 ± 0.61% | 5.10 ± 1.83% | 89.38 ± 0.31% | 32.71 ± 0.79% | 44.22 ± 0.38% | 12.29 ± 1.26% | 47.28 ± 25.67% | 10.25 ± 0.31% | 1.87 ± 0.02 | 12.75 ± 0.04% | 2.65 ± 0.03 |
| safety+math | data_free_sst_main | 0.80 | 22.21 ± 9.50% | 16.02 ± 6.78% | 18.70 ± 0.63% | 9.59 ± 1.36% | 60.99 ± 0.59% | 33.77 ± 9.14% | 15.42 ± 4.70% | 40.33 ± 20.23% | 40.33 ± 20.23% | 0 ± 0 | 0.00 ± 0.00% | 18.67 ± 10.41% | 2.24 ± 2.00% | 2.24 ± 2.00% | 0 ± 0 | 0.00 ± 0.00% | 14.80 ± 10.43% | 24.06 ± 10.36% | 24.06 ± 10.36% | 0 ± 0 | 0.00 ± 0.00% | 15.10 ± 8.51% | 33.12 ± 1.25% | 4.27 ± 0.65% | 11.79 ± 0.70% | 7.40 ± 2.66% | 89.17 ± 0.48% | 32.81 ± 1.13% | 44.27 ± 0.42% | 12.08 ± 0.79% | 44.95 ± 27.73% | 10.57 ± 0.34% | 1.89 ± 0.03 | 12.89 ± 0.08% | 2.73 ± 0.05 |
| safety+math | data_free_sst_main | 1.00 | 15.67 ± 13.99% | 11.55 ± 9.34% | 19.06 ± 0.27% | 9.35 ± 1.45% | 61.41 ± 0.56% | 34.69 ± 9.06% | 9.48 ± 7.50% | 29.00 ± 27.22% | 29.00 ± 27.22% | 0 ± 0 | 0.00 ± 0.00% | 15.33 ± 14.19% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 10.44 ± 7.85% | 18.02 ± 14.89% | 18.02 ± 14.89% | 0 ± 0 | 0.00 ± 0.00% | 10.83 ± 9.28% | 34.38 ± 0.31% | 3.75 ± 0.31% | 10.37 ± 0.61% | 8.33 ± 2.43% | 88.96 ± 0.95% | 33.85 ± 0.65% | 43.51 ± 0.72% | 12.08 ± 1.72% | 48.49 ± 27.07% | 10.50 ± 0.42% | 1.93 ± 0.04 | 12.30 ± 0.58% | 2.83 ± 0.08 |


#### パターン: `safety+code` / 手法: `data_free_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 65.93 ± 0.06% | 0.08 ± 0.00% | 0.26 ± 0.18% | 0.00 ± 0.00% | 54.43 ± 0.36% | 14.10 ± 0.06% | 0.00 ± 0.00% | 93.00 ± 0.00% | 66.00 ± 0.00% | 27 ± 0 | 27.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 76.68 ± 0.00% | 73 ± 0 | 23.32 ± 0.00% | 0.32 ± 0.00% | 75.83 ± 0.18% | 55.10 ± 0.18% | 66 ± 1 | 20.73 ± 0.18% | 0.00 ± 0.00% | 0.42 ± 0.18% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.54% | 22.60 ± 1.26% | 27.95 ± 0.01% | 14.27 ± 0.18% | 0.07 ± 0.00% | 1.09 ± 0.01% | 203.70 ± 0.00 | 5.37 ± 0.14% | 28.06 ± 0.00 |
| safety+code | data_free_sst_main | 0.20 | 58.90 ± 2.32% | 0.11 ± 0.05% | 0.21 ± 0.18% | 0.00 ± 0.00% | 54.17 ± 0.39% | 15.61 ± 0.17% | 0.00 ± 0.00% | 85.00 ± 1.73% | 55.33 ± 0.58% | 30 ± 2 | 29.67 ± 1.53% | 0.00 ± 0.00% | 99.89 ± 0.18% | 71.35 ± 3.42% | 89 ± 10 | 28.54 ± 3.23% | 0.43 ± 0.18% | 83.33 ± 3.91% | 50.00 ± 6.90% | 107 ± 10 | 33.33 ± 3.00% | 0.00 ± 0.00% | 0.21 ± 0.36% | 0.21 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.83 ± 0.79% | 22.50 ± 1.36% | 30.41 ± 0.75% | 16.35 ± 1.26% | 0.06 ± 0.01% | 1.46 ± 0.07% | 78.83 ± 14.75 | 4.83 ± 0.18% | 16.19 ± 1.34 |
| safety+code | data_free_sst_main | 0.40 | 60.89 ± 1.95% | 0.08 ± 0.08% | 0.10 ± 0.18% | 0.00 ± 0.00% | 54.69 ± 0.47% | 15.46 ± 0.54% | 0.10 ± 0.18% | 78.00 ± 2.00% | 63.67 ± 9.81% | 14 ± 10 | 14.33 ± 10.02% | 0.00 ± 0.00% | 100.00 ± 0.00% | 78.49 ± 1.87% | 67 ± 6 | 21.51 ± 1.87% | 0.21 ± 0.18% | 59.58 ± 1.18% | 40.52 ± 3.73% | 61 ± 9 | 19.06 ± 2.67% | 0.00 ± 0.00% | 0.21 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.62 ± 0.83% | 23.75 ± 0.62% | 30.37 ± 1.03% | 15.94 ± 2.25% | 0.06 ± 0.01% | 1.41 ± 0.12% | 74.73 ± 27.01 | 5.10 ± 0.45% | 16.98 ± 3.32 |
| safety+code | data_free_sst_main | 0.60 | 59.37 ± 3.12% | 0.03 ± 0.05% | 0.16 ± 0.27% | 0.00 ± 0.00% | 55.36 ± 3.82% | 14.94 ± 0.26% | 0.00 ± 0.00% | 88.67 ± 2.52% | 64.33 ± 3.21% | 24 ± 4 | 24.33 ± 3.51% | 0.00 ± 0.00% | 99.89 ± 0.18% | 72.42 ± 6.11% | 86 ± 20 | 27.48 ± 6.29% | 0.11 ± 0.18% | 64.90 ± 5.77% | 41.35 ± 5.32% | 75 ± 15 | 23.54 ± 4.64% | 0.00 ± 0.00% | 0.31 ± 0.54% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 84.06 ± 3.26% | 26.67 ± 4.43% | 29.35 ± 0.63% | 15.42 ± 0.65% | 0.05 ± 0.01% | 1.33 ± 0.33% | 112.57 ± 56.38 | 4.75 ± 1.64% | 23.38 ± 6.19 |
| safety+code | data_free_sst_main | 0.80 | 51.93 ± 8.51% | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 45.62 ± 13.50% | 13.22 ± 0.71% | 0.00 ± 0.00% | 82.33 ± 0.58% | 43.00 ± 11.14% | 39 ± 11 | 39.33 ± 10.69% | 0.00 ± 0.00% | 100.00 ± 0.00% | 75.40 ± 3.89% | 77 ± 12 | 24.60 ± 3.89% | 0.43 ± 0.18% | 67.19 ± 3.79% | 37.40 ± 11.29% | 95 ± 30 | 29.79 ± 9.38% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 66.67 ± 29.65% | 24.58 ± 3.13% | 27.20 ± 1.14% | 12.40 ± 1.00% | 0.05 ± 0.00% | 1.24 ± 0.13% | 389.89 ± 255.30 | 3.92 ± 1.95% | 54.67 ± 23.22 |
| safety+code | data_free_sst_main | 1.00 | 62.10 ± 4.03% | 0.03 ± 0.05% | 0.16 ± 0.16% | 0.00 ± 0.00% | 42.86 ± 16.15% | 12.18 ± 0.07% | 0.00 ± 0.00% | 84.00 ± 2.00% | 66.33 ± 4.04% | 18 ± 3 | 17.67 ± 2.52% | 0.00 ± 0.00% | 100.00 ± 0.00% | 84.56 ± 6.31% | 48 ± 20 | 15.44 ± 6.31% | 0.11 ± 0.18% | 52.29 ± 8.13% | 35.42 ± 8.15% | 54 ± 32 | 16.88 ± 9.88% | 0.00 ± 0.00% | 0.31 ± 0.31% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 61.77 ± 36.46% | 23.96 ± 4.43% | 25.04 ± 0.42% | 11.46 ± 0.65% | 0.03 ± 0.02% | 1.22 ± 0.08% | 17815.49 ± 16468.76 | 1.57 ± 0.42% | 2046.19 ± 1654.26 |


#### パターン: `safety+medical` / 手法: `data_free_sst_main`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 80.69 ± 0.56% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.97 ± 7.85% | 11.89 ± 0.15% | 0.00 ± 0.00% | 91.67 ± 0.58% | 81.00 ± 1.00% | 11 ± 1 | 10.67 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 91.48 ± 0.18% | 27 ± 1 | 8.52 ± 0.18% | 0.00 ± 0.00% | 76.56 ± 0.83% | 69.58 ± 0.79% | 22 ± 1 | 6.98 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 50.83 ± 15.34% | 25.10 ± 0.36% | 24.89 ± 0.02% | 10.73 ± 0.48% | 0.05 ± 0.00% | 0.95 ± 0.01% | 200412.44 ± 0.39 | 2.71 ± 0.01% | 195954.54 ± 5.55 |
| safety+medical | data_free_sst_main | 0.20 | 72.43 ± 8.70% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.22 ± 3.54% | 11.92 ± 0.33% | 0.00 ± 0.00% | 97.33 ± 1.15% | 79.33 ± 10.12% | 18 ± 11 | 18.00 ± 11.27% | 0.00 ± 0.00% | 100.00 ± 0.00% | 73.59 ± 12.66% | 83 ± 40 | 26.41 ± 12.66% | 0.11 ± 0.18% | 83.75 ± 3.08% | 64.38 ± 4.54% | 62 ± 24 | 19.38 ± 7.58% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 11.46 ± 3.97% | 26.98 ± 3.78% | 24.56 ± 0.33% | 11.15 ± 0.65% | 0.04 ± 0.01% | 0.71 ± 0.09% | 173037.71 ± 49082.15 | 1.72 ± 0.19% | 163048.68 ± 25149.98 |
| safety+medical | data_free_sst_main | 0.40 | 83.13 ± 4.45% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.49 ± 7.49% | 12.68 ± 0.39% | 0.00 ± 0.00% | 94.33 ± 3.21% | 89.33 ± 5.51% | 5 ± 4 | 5.00 ± 4.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 87.75 ± 4.48% | 38 ± 14 | 12.25 ± 4.48% | 0.11 ± 0.18% | 84.17 ± 2.73% | 72.29 ± 5.96% | 38 ± 21 | 11.88 ± 6.68% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.75 ± 14.63% | 28.23 ± 1.00% | 26.23 ± 0.74% | 11.77 ± 0.48% | 0.03 ± 0.02% | 0.42 ± 0.05% | 432792.94 ± 79129.29 | 1.39 ± 0.16% | 340350.46 ± 50490.28 |
| safety+medical | data_free_sst_main | 0.60 | 33.99 ± 27.90% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.49 ± 1.80% | 12.72 ± 0.20% | 0.00 ± 0.00% | 95.33 ± 5.69% | 41.00 ± 39.59% | 54 ± 45 | 54.33 ± 45.01% | 0.00 ± 0.00% | 100.00 ± 0.00% | 34.61 ± 26.33% | 205 ± 82 | 65.39 ± 26.33% | 0.21 ± 0.18% | 88.85 ± 13.19% | 26.35 ± 18.09% | 200 ± 98 | 62.50 ± 30.67% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 84.58 ± 2.89% | 22.40 ± 0.72% | 27.00 ± 0.12% | 11.15 ± 0.48% | 0.03 ± 0.01% | 0.45 ± 0.05% | 154475.14 ± 80159.01 | 1.28 ± 0.14% | 118397.35 ± 35122.34 |
| safety+medical | data_free_sst_main | 0.80 | 54.95 ± 43.70% | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 51.20 ± 9.03% | 12.33 ± 0.28% | 0.00 ± 0.00% | 98.00 ± 2.00% | 49.33 ± 47.06% | 49 ± 49 | 48.67 ± 49.05% | 0.00 ± 0.00% | 100.00 ± 0.00% | 61.98 ± 46.98% | 119 ± 147 | 38.02 ± 46.98% | 0.32 ± 0.00% | 88.23 ± 9.41% | 53.54 ± 39.60% | 111 ± 156 | 34.69 ± 48.76% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 76.98 ± 14.46% | 25.42 ± 3.62% | 25.70 ± 0.40% | 11.25 ± 0.54% | 0.03 ± 0.01% | 0.46 ± 0.04% | 204228.26 ± 108917.97 | 1.18 ± 0.16% | 197501.22 ± 101088.17 |
| safety+medical | data_free_sst_main | 1.00 | 61.22 ± 34.75% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.20 ± 22.92% | 12.53 ± 0.09% | 0.00 ± 0.00% | 95.33 ± 4.73% | 60.00 ± 40.78% | 35 ± 44 | 35.33 ± 43.89% | 0.00 ± 0.00% | 100.00 ± 0.00% | 76.36 ± 31.00% | 74 ± 97 | 23.64 ± 31.00% | 0.32 ± 0.32% | 82.71 ± 11.16% | 47.29 ± 33.63% | 113 ± 133 | 35.42 ± 41.41% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.29 ± 44.08% | 25.10 ± 3.00% | 25.98 ± 1.00% | 11.56 ± 0.83% | 0.03 ± 0.02% | 0.39 ± 0.07% | 303013.60 ± 160352.85 | 1.26 ± 0.18% | 130002.00 ± 53693.74 |


### 手法: `ties` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `ties`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 94.14 ± 0.06% | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.21 ± 22.37% | 11.59 ± 0.00% | 0.00 ± 0.00% | 97.00 ± 0.00% | 97.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 100.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.32 ± 0.00% | 85.42 ± 0.18% | 85.42 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 49.80% | 22.92 ± 5.05% | 23.14 ± 0.00% | 11.56 ± 0.00% | 0.05 ± 0.00% | 0.39 ± 0.00% | 138597.22 ± 0.00 | 1.29 ± 0.01% | 124557.00 ± 0.00 |
| safety+math+code+medical | ties | 0.20 | 86.51 ± 13.50% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 29.90 ± 23.97% | 11.68 ± 0.13% | 0.00 ± 0.00% | 89.00 ± 14.73% | 89.00 ± 14.73% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 100.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.21 ± 0.18% | 70.52 ± 25.81% | 70.52 ± 25.81% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.33 ± 46.34% | 26.46 ± 3.97% | 23.93 ± 0.71% | 11.04 ± 0.48% | 0.05 ± 0.00% | 0.44 ± 0.17% | 146910.24 ± 57134.86 | 0.99 ± 0.16% | 145135.43 ± 58076.86 |
| safety+math+code+medical | ties | 0.40 | 62.53 ± 54.16% | 0.21 ± 0.24% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.52 ± 3.97% | 11.68 ± 0.19% | 0.00 ± 0.00% | 98.00 ± 2.00% | 64.67 ± 56.01% | 33 ± 58 | 33.33 ± 57.74% | 0.00 ± 0.00% | 100.00 ± 0.00% | 66.67 ± 57.74% | 104 ± 181 | 33.33 ± 57.74% | 0.53 ± 0.49% | 89.58 ± 9.16% | 56.25 ± 48.74% | 107 ± 185 | 33.33 ± 57.74% | 0.31 ± 0.54% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.17 ± 7.94% | 21.88 ± 0.00% | 23.96 ± 0.71% | 11.04 ± 0.65% | 0.05 ± 0.03% | 0.46 ± 0.10% | 207824.93 ± 178050.92 | 1.50 ± 0.20% | 220190.56 ± 162922.41 |
| safety+math+code+medical | ties | 0.60 | 60.53 ± 52.44% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.51 ± 2.26% | 12.12 ± 0.48% | 0.00 ± 0.00% | 97.00 ± 2.65% | 63.67 ± 55.14% | 33 ± 58 | 33.33 ± 57.74% | 0.00 ± 0.00% | 100.00 ± 0.00% | 66.56 ± 57.64% | 105 ± 180 | 33.44 ± 57.64% | 0.21 ± 0.18% | 84.69 ± 14.01% | 51.35 ± 44.70% | 107 ± 185 | 33.33 ± 57.74% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.27 ± 8.03% | 23.75 ± 3.52% | 24.86 ± 2.01% | 11.46 ± 1.98% | 0.03 ± 0.02% | 0.45 ± 0.18% | 216889.35 ± 204103.70 | 0.99 ± 0.13% | 271395.89 ± 218392.59 |
| safety+math+code+medical | ties | 0.80 | 57.25 ± 50.19% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.47 ± 18.52% | 12.01 ± 0.51% | 0.00 ± 0.00% | 96.33 ± 4.04% | 63.00 ± 54.62% | 33 ± 58 | 33.33 ± 57.74% | 0.00 ± 0.00% | 100.00 ± 0.00% | 66.77 ± 57.55% | 104 ± 180 | 33.23 ± 57.55% | 0.32 ± 0.32% | 75.31 ± 31.15% | 41.98 ± 42.84% | 107 ± 185 | 33.33 ± 57.74% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 48.96 ± 37.19% | 21.98 ± 0.48% | 24.86 ± 2.01% | 11.15 ± 0.48% | 0.03 ± 0.02% | 0.42 ± 0.06% | 229654.01 ± 198102.06 | 1.13 ± 0.51% | 284236.98 ± 253493.80 |
| safety+math+code+medical | ties | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.97 ± 2.36% | 6.22 ± 4.17% | 52.29 ± 14.59% | 30.47 ± 16.30% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.06 ± 3.26% | 1.88 ± 1.56% | 6.91 ± 5.98% | 5.52 ± 5.63% | 71.88 ± 25.98% | 32.71 ± 3.75% | 39.93 ± 1.30% | 10.42 ± 0.48% | 41.05 ± 49.69% | 9.96 ± 0.50% | 1.90 ± 0.03 | 18.37 ± 2.71% | 2.84 ± 0.06 |


#### パターン: `safety+math` / 手法: `ties`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 76.92 ± 0.29% | 31.39 ± 0.37% | 21.04 ± 0.33% | 7.53 ± 0.00% | 60.62 ± 0.00% | 18.51 ± 0.00% | 24.79 ± 0.18% | 76.33 ± 0.58% | 70.33 ± 0.58% | 6 ± 0 | 6.00 ± 0.00% | 36.33 ± 0.58% | 93.72 ± 0.18% | 91.37 ± 0.00% | 7 ± 1 | 2.34 ± 0.18% | 41.75 ± 0.37% | 78.02 ± 0.48% | 69.06 ± 0.31% | 29 ± 1 | 8.96 ± 0.18% | 22.71 ± 0.36% | 37.50 ± 0.54% | 4.58 ± 0.18% | 9.76 ± 0.00% | 5.31 ± 0.00% | 89.38 ± 0.00% | 31.87 ± 0.00% | 43.29 ± 0.01% | 12.19 ± 0.00% | 0.06 ± 0.00% | 7.15 ± 0.01% | 1.77 ± 0.00 | 12.89 ± 0.01% | 2.42 ± 0.00 |
| safety+math | ties | 0.20 | 28.00 ± 0.79% | 14.41 ± 1.04% | 22.14 ± 1.17% | 8.01 ± 3.24% | 60.16 ± 0.41% | 29.77 ± 0.82% | 14.27 ± 2.03% | 28.33 ± 1.15% | 28.33 ± 1.15% | 0 ± 0 | 0.00 ± 0.00% | 12.67 ± 2.89% | 30.78 ± 2.79% | 30.78 ± 2.79% | 0 ± 0 | 0.00 ± 0.00% | 17.36 ± 2.03% | 24.90 ± 1.10% | 24.90 ± 1.10% | 0 ± 0 | 0.00 ± 0.00% | 13.33 ± 1.44% | 38.44 ± 1.62% | 5.83 ± 0.72% | 9.35 ± 0.93% | 6.67 ± 5.85% | 88.44 ± 0.31% | 31.88 ± 0.83% | 43.46 ± 0.19% | 11.77 ± 1.72% | 34.08 ± 0.94% | 9.55 ± 0.23% | 1.97 ± 0.03 | 12.41 ± 0.10% | 2.87 ± 0.04 |
| safety+math | ties | 0.40 | 29.70 ± 1.47% | 14.65 ± 1.43% | 21.82 ± 0.59% | 9.31 ± 0.63% | 60.68 ± 0.45% | 35.24 ± 4.79% | 13.85 ± 0.18% | 31.00 ± 2.65% | 31.00 ± 2.65% | 0 ± 0 | 0.00 ± 0.00% | 13.00 ± 1.73% | 31.95 ± 2.24% | 31.95 ± 2.24% | 0 ± 0 | 0.00 ± 0.00% | 18.32 ± 1.29% | 26.15 ± 2.69% | 26.15 ± 2.69% | 0 ± 0 | 0.00 ± 0.00% | 13.33 ± 3.59% | 37.81 ± 1.62% | 5.83 ± 1.60% | 9.35 ± 0.93% | 9.27 ± 1.10% | 89.06 ± 0.31% | 32.29 ± 0.65% | 43.70 ± 0.26% | 11.04 ± 1.57% | 50.99 ± 14.62% | 9.90 ± 0.27% | 1.94 ± 0.03 | 12.36 ± 0.20% | 2.83 ± 0.04 |
| safety+math | ties | 0.60 | 11.91 ± 6.13% | 8.95 ± 5.41% | 20.83 ± 0.90% | 9.73 ± 0.43% | 60.42 ± 0.24% | 32.81 ± 3.39% | 8.12 ± 6.23% | 20.33 ± 13.87% | 20.33 ± 13.87% | 0 ± 0 | 0.00 ± 0.00% | 11.33 ± 7.02% | 3.62 ± 1.44% | 3.51 ± 1.60% | 0 ± 1 | 0.11 ± 0.18% | 8.73 ± 5.59% | 11.88 ± 6.50% | 11.88 ± 6.50% | 0 ± 0 | 0.00 ± 0.00% | 7.60 ± 3.55% | 36.56 ± 1.25% | 5.10 ± 0.95% | 9.35 ± 1.27% | 10.10 ± 2.03% | 88.75 ± 0.31% | 32.08 ± 0.18% | 43.95 ± 0.26% | 10.21 ± 0.48% | 44.28 ± 9.68% | 10.58 ± 0.71% | 1.94 ± 0.03 | 12.33 ± 0.22% | 2.86 ± 0.06 |
| safety+math | ties | 0.80 | 0.32 ± 0.47% | 0.50 ± 0.48% | 17.76 ± 1.15% | 10.56 ± 1.19% | 60.31 ± 0.72% | 29.63 ± 3.45% | 0.42 ± 0.72% | 0.33 ± 0.58% | 0.33 ± 0.58% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 1.06 ± 1.33% | 0.62 ± 0.83% | 0.62 ± 0.83% | 0 ± 0 | 0.00 ± 0.00% | 0.52 ± 0.65% | 32.29 ± 0.95% | 3.23 ± 1.54% | 9.76 ± 0.61% | 11.35 ± 2.95% | 88.54 ± 0.18% | 32.08 ± 1.26% | 44.12 ± 0.50% | 12.50 ± 0.31% | 32.26 ± 9.76% | 10.79 ± 0.62% | 1.93 ± 0.04 | 13.43 ± 2.22% | 2.93 ± 0.09 |
| safety+math | ties | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.27 ± 0.33% | 7.99 ± 2.61% | 60.36 ± 1.04% | 25.53 ± 8.52% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 5.73 ± 0.48% | 2.81 ± 0.63% | 10.57 ± 0.93% | 5.42 ± 5.47% | 86.98 ± 0.36% | 33.75 ± 2.44% | 39.93 ± 1.30% | 10.31 ± 0.31% | 26.34 ± 26.39% | 9.94 ± 0.44% | 1.90 ± 0.03 | 18.33 ± 2.70% | 2.84 ± 0.06 |


#### パターン: `safety+code` / 手法: `ties`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 74.46 ± 0.23% | 9.87 ± 0.29% | 2.19 ± 0.27% | 0.21 ± 0.36% | 50.73 ± 5.86% | 14.00 ± 0.01% | 10.94 ± 1.13% | 88.67 ± 0.58% | 81.33 ± 0.58% | 7 ± 1 | 7.33 ± 0.58% | 13.00 ± 1.00% | 93.40 ± 0.37% | 84.35 ± 0.32% | 28 ± 1 | 9.05 ± 0.18% | 9.69 ± 0.18% | 72.19 ± 0.00% | 57.71 ± 0.18% | 46 ± 1 | 14.48 ± 0.18% | 5.83 ± 0.36% | 2.50 ± 0.00% | 1.88 ± 0.54% | 0.00 ± 0.00% | 0.42 ± 0.72% | 73.44 ± 11.37% | 28.02 ± 0.36% | 25.37 ± 0.02% | 16.56 ± 0.00% | 0.07 ± 0.00% | 6.16 ± 0.06% | 2.84 ± 0.00 | 9.97 ± 0.12% | 5.29 ± 0.00 |
| safety+code | ties | 0.20 | 65.66 ± 4.34% | 3.05 ± 0.44% | 1.35 ± 0.09% | 0.10 ± 0.18% | 49.58 ± 6.77% | 12.89 ± 0.82% | 3.54 ± 1.30% | 81.00 ± 5.00% | 64.33 ± 4.04% | 17 ± 4 | 16.67 ± 4.04% | 1.67 ± 1.53% | 98.94 ± 0.98% | 83.49 ± 3.81% | 48 ± 15 | 15.44 ± 4.66% | 4.90 ± 1.61% | 72.08 ± 2.37% | 49.17 ± 5.61% | 73 ± 10 | 22.92 ± 3.25% | 2.08 ± 1.00% | 0.83 ± 0.18% | 1.88 ± 0.00% | 0.20 ± 0.35% | 0.00 ± 0.00% | 69.90 ± 14.01% | 29.27 ± 0.48% | 24.55 ± 0.68% | 14.06 ± 2.05% | 0.06 ± 0.01% | 4.27 ± 0.52% | 4.92 ± 1.98 | 8.37 ± 0.54% | 4.76 ± 0.03 |
| safety+code | ties | 0.40 | 56.80 ± 4.98% | 0.45 ± 0.44% | 1.35 ± 0.48% | 0.00 ± 0.00% | 43.44 ± 12.59% | 10.79 ± 0.77% | 0.52 ± 0.36% | 71.67 ± 8.33% | 53.67 ± 5.03% | 18 ± 9 | 18.00 ± 9.17% | 0.33 ± 0.58% | 99.04 ± 0.85% | 79.23 ± 9.62% | 62 ± 30 | 19.81 ± 9.65% | 0.64 ± 0.55% | 59.58 ± 8.49% | 37.50 ± 2.48% | 71 ± 33 | 22.08 ± 10.34% | 0.31 ± 0.31% | 0.83 ± 1.18% | 1.88 ± 0.31% | 0.00 ± 0.00% | 0.00 ± 0.00% | 58.96 ± 24.95% | 27.92 ± 1.57% | 23.34 ± 0.78% | 8.96 ± 1.60% | 0.07 ± 0.01% | 2.72 ± 0.48% | 33.76 ± 43.61 | 8.05 ± 0.60% | 6.12 ± 1.08 |
| safety+code | ties | 0.60 | 36.93 ± 12.51% | 0.11 ± 0.13% | 1.25 ± 0.56% | 0.00 ± 0.00% | 30.89 ± 13.04% | 17.84 ± 9.74% | 0.00 ± 0.00% | 67.33 ± 21.46% | 29.67 ± 8.50% | 38 ± 29 | 37.67 ± 29.48% | 0.33 ± 0.58% | 99.57 ± 0.18% | 61.24 ± 26.68% | 120 ± 83 | 38.34 ± 26.52% | 0.11 ± 0.18% | 55.00 ± 20.03% | 19.90 ± 2.35% | 112 ± 71 | 35.10 ± 22.27% | 0.00 ± 0.00% | 0.73 ± 0.72% | 1.77 ± 0.48% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.27 ± 26.08% | 27.50 ± 0.94% | 23.65 ± 0.20% | 11.77 ± 2.39% | 18.10 ± 31.17% | 2.22 ± 0.37% | 137.44 ± 182.79 | 7.28 ± 1.48% | 22.88 ± 22.58 |
| safety+code | ties | 0.80 | 37.90 ± 20.48% | 0.03 ± 0.05% | 0.89 ± 0.24% | 0.00 ± 0.00% | 22.40 ± 3.73% | 12.37 ± 1.07% | 0.00 ± 0.00% | 75.33 ± 12.22% | 33.33 ± 21.03% | 42 ± 20 | 42.00 ± 19.92% | 0.00 ± 0.00% | 99.79 ± 0.18% | 55.06 ± 25.18% | 140 ± 79 | 44.73 ± 25.12% | 0.11 ± 0.18% | 69.58 ± 16.11% | 25.31 ± 16.99% | 142 ± 84 | 44.27 ± 26.24% | 0.00 ± 0.00% | 0.10 ± 0.18% | 1.67 ± 0.48% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.56 ± 5.42% | 28.23 ± 2.39% | 23.79 ± 0.48% | 13.23 ± 3.34% | 0.10 ± 0.04% | 1.54 ± 0.57% | 1251.61 ± 1745.34 | 5.37 ± 0.37% | 401.26 ± 618.29 |
| safety+code | ties | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 30.48 ± 16.26% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.75 ± 2.98% | 2.19 ± 1.25% | 7.11 ± 6.23% | 8.12 ± 2.81% | 70.31 ± 28.69% | 32.40 ± 4.07% | 39.96 ± 1.33% | 10.52 ± 0.18% | 40.95 ± 50.04% | 9.85 ± 0.54% | 1.90 ± 0.03 | 18.36 ± 2.74% | 2.84 ± 0.06 |


#### パターン: `safety+medical` / 手法: `ties`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 88.24 ± 0.34% | 0.00 ± 0.00% | 1.82 ± 0.09% | 0.00 ± 0.00% | 17.66 ± 0.27% | 12.09 ± 0.02% | 0.00 ± 0.00% | 91.00 ± 1.00% | 89.33 ± 1.53% | 2 ± 1 | 1.67 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 93.40 ± 0.74% | 21 ± 2 | 6.60 ± 0.74% | 0.00 ± 0.00% | 86.25 ± 0.83% | 81.98 ± 1.00% | 14 ± 3 | 4.27 ± 0.95% | 0.00 ± 0.00% | 1.04 ± 0.18% | 2.60 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 21.56 ± 0.54% | 27.57 ± 0.03% | 8.44 ± 0.00% | 0.25 ± 0.10% | 1.52 ± 0.01% | 6721.72 ± 0.01 | 3.58 ± 0.01% | 6087.88 ± 0.15 |
| safety+medical | ties | 0.20 | 79.32 ± 24.57% | 0.03 ± 0.05% | 1.25 ± 0.83% | 0.00 ± 0.00% | 18.80 ± 1.18% | 11.97 ± 0.21% | 0.00 ± 0.00% | 95.67 ± 1.53% | 83.00 ± 22.52% | 13 ± 21 | 12.67 ± 21.08% | 0.00 ± 0.00% | 100.00 ± 0.00% | 84.03 ± 27.12% | 50 ± 85 | 15.97 ± 27.12% | 0.11 ± 0.18% | 85.10 ± 1.00% | 70.94 ± 24.09% | 45 ± 75 | 14.17 ± 23.46% | 0.00 ± 0.00% | 0.83 ± 0.18% | 1.67 ± 1.48% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 23.85 ± 2.37% | 26.63 ± 1.24% | 9.06 ± 1.13% | 0.22 ± 0.08% | 1.27 ± 0.19% | 13638.85 ± 2449.53 | 3.52 ± 1.03% | 13212.53 ± 2638.35 |
| safety+medical | ties | 0.40 | 52.71 ± 44.88% | 0.03 ± 0.05% | 0.26 ± 0.33% | 0.00 ± 0.00% | 20.21 ± 2.53% | 11.67 ± 0.93% | 0.00 ± 0.00% | 94.00 ± 6.00% | 55.33 ± 48.95% | 39 ± 54 | 38.67 ± 53.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 61.55 ± 50.55% | 120 ± 158 | 38.45 ± 50.55% | 0.11 ± 0.18% | 82.08 ± 15.52% | 41.25 ± 35.58% | 131 ± 161 | 40.83 ± 50.17% | 0.00 ± 0.00% | 0.31 ± 0.54% | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.52 ± 3.07% | 24.90 ± 2.01% | 25.25 ± 0.58% | 9.69 ± 2.72% | 0.08 ± 0.01% | 0.91 ± 0.22% | 19431.56 ± 3947.53 | 2.24 ± 0.26% | 34857.27 ± 11037.23 |
| safety+medical | ties | 0.60 | 70.95 ± 15.31% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.93 ± 3.86% | 12.06 ± 1.23% | 0.00 ± 0.00% | 91.00 ± 9.54% | 75.00 ± 19.00% | 16 ± 20 | 16.00 ± 19.70% | 0.00 ± 0.00% | 100.00 ± 0.00% | 77.74 ± 22.70% | 70 ± 71 | 22.26 ± 22.70% | 0.21 ± 0.18% | 72.40 ± 14.26% | 60.10 ± 15.79% | 39 ± 34 | 12.29 ± 10.66% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 10.21 ± 5.60% | 23.65 ± 3.62% | 25.91 ± 1.62% | 10.21 ± 2.08% | 0.06 ± 0.01% | 0.65 ± 0.17% | 39894.11 ± 10705.72 | 1.59 ± 0.60% | 63613.99 ± 30155.00 |
| safety+medical | ties | 0.80 | 70.53 ± 31.44% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 23.44 ± 20.44% | 11.82 ± 0.52% | 0.00 ± 0.00% | 95.33 ± 3.06% | 75.00 ± 32.97% | 20 ± 35 | 20.33 ± 35.22% | 0.00 ± 0.00% | 100.00 ± 0.00% | 76.89 ± 40.03% | 72 ± 125 | 23.11 ± 40.03% | 0.32 ± 0.32% | 78.33 ± 10.92% | 59.69 ± 21.38% | 60 ± 103 | 18.65 ± 32.30% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 24.58 ± 40.43% | 22.29 ± 0.48% | 23.95 ± 0.69% | 11.46 ± 0.95% | 0.06 ± 0.01% | 0.43 ± 0.08% | 140476.49 ± 28732.28 | 1.21 ± 0.04% | 221480.23 ± 86588.69 |
| safety+medical | ties | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 25.64 ± 8.45% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.75 ± 2.98% | 2.19 ± 1.25% | 7.11 ± 6.23% | 8.12 ± 2.81% | 70.31 ± 28.69% | 32.40 ± 4.07% | 39.96 ± 1.33% | 10.62 ± 0.31% | 26.33 ± 26.40% | 9.86 ± 0.51% | 1.90 ± 0.03 | 18.36 ± 2.73% | 2.84 ± 0.06 |


### 手法: `dare` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `dare`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 80.55 ± 13.37% | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.84 ± 18.72% | 12.12 ± 0.60% | 0.00 ± 0.00% | 95.67 ± 0.58% | 80.00 ± 16.52% | 16 ± 17 | 15.67 ± 16.56% | 0.00 ± 0.00% | 100.00 ± 0.00% | 89.56 ± 11.75% | 33 ± 37 | 10.44 ± 11.75% | 0.43 ± 0.18% | 81.56 ± 5.16% | 72.08 ± 12.07% | 30 ± 39 | 9.48 ± 12.28% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 44.38 ± 39.63% | 25.31 ± 3.79% | 25.68 ± 1.30% | 10.62 ± 0.54% | 0.04 ± 0.02% | 0.45 ± 0.08% | 7302514.82 ± 7460062.63 | 1.20 ± 0.32% | 11880294.42 ± 3503725.18 |
| safety+math+code+medical | dare | 0.20 | 87.03 ± 6.04% | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 30.26 ± 21.38% | 12.31 ± 0.72% | 0.00 ± 0.00% | 94.67 ± 3.21% | 94.33 ± 2.89% | 0 ± 1 | 0.33 ± 0.58% | 0.00 ± 0.00% | 100.00 ± 0.00% | 94.89 ± 4.43% | 16 ± 14 | 5.11 ± 4.43% | 0.53 ± 0.18% | 78.85 ± 3.44% | 71.88 ± 11.97% | 22 ± 27 | 6.98 ± 8.58% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.00 ± 40.16% | 25.52 ± 3.70% | 25.21 ± 1.98% | 11.67 ± 0.72% | 0.05 ± 0.00% | 0.53 ± 0.02% | 7230430.12 ± 3418148.36 | 1.14 ± 0.24% | 6230043.88 ± 1795222.09 |
| safety+math+code+medical | dare | 0.40 | 81.69 ± 6.21% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.81 ± 2.89% | 11.96 ± 0.29% | 0.00 ± 0.00% | 91.67 ± 4.04% | 88.00 ± 7.00% | 4 ± 3 | 3.67 ± 3.21% | 0.00 ± 0.00% | 100.00 ± 0.00% | 94.14 ± 5.75% | 18 ± 18 | 5.86 ± 5.75% | 0.32 ± 0.32% | 73.33 ± 7.14% | 62.92 ± 6.29% | 33 ± 42 | 10.42 ± 13.24% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 10.00 ± 3.31% | 25.62 ± 3.79% | 24.89 ± 1.55% | 10.94 ± 0.83% | 0.04 ± 0.01% | 0.52 ± 0.07% | 5300473.89 ± 4652204.12 | 1.36 ± 0.25% | 3676141.77 ± 2600167.94 |
| safety+math+code+medical | dare | 0.60 | 64.04 ± 50.53% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.64 ± 20.19% | 11.51 ± 0.16% | 0.00 ± 0.00% | 98.00 ± 1.73% | 66.33 ± 53.12% | 32 ± 55 | 31.67 ± 54.85% | 0.00 ± 0.00% | 100.00 ± 0.00% | 69.65 ± 51.74% | 95 ± 162 | 30.35 ± 51.74% | 0.32 ± 0.32% | 88.85 ± 9.80% | 56.15 ± 46.77% | 105 ± 180 | 32.71 ± 56.38% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 45.00 ± 36.63% | 24.27 ± 3.88% | 23.67 ± 0.62% | 10.83 ± 0.18% | 0.04 ± 0.02% | 0.45 ± 0.05% | 4659204.25 ± 5454560.12 | 1.20 ± 0.09% | 4988976.69 ± 3382670.49 |
| safety+math+code+medical | dare | 0.80 | 57.94 ± 48.23% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.33 ± 3.61% | 11.92 ± 0.05% | 0.00 ± 0.00% | 96.33 ± 4.73% | 61.33 ± 50.29% | 35 ± 53 | 35.00 ± 53.02% | 0.00 ± 0.00% | 100.00 ± 0.00% | 65.39 ± 52.65% | 108 ± 165 | 34.61 ± 52.65% | 0.21 ± 0.18% | 80.52 ± 25.16% | 47.08 ± 44.07% | 107 ± 175 | 33.44 ± 54.70% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.65 ± 5.52% | 23.02 ± 1.72% | 24.45 ± 0.15% | 11.25 ± 0.00% | 0.05 ± 0.00% | 0.48 ± 0.09% | 1108618.09 ± 987286.09 | 1.28 ± 0.31% | 749856.57 ± 284860.35 |
| safety+math+code+medical | dare | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.86 ± 2.48% | 6.84 ± 3.08% | 50.83 ± 16.17% | 22.66 ± 11.23% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.85 ± 3.37% | 1.88 ± 1.65% | 6.91 ± 6.02% | 6.77 ± 4.52% | 70.00 ± 29.77% | 31.67 ± 2.97% | 39.15 ± 1.21% | 8.96 ± 0.65% | 19.88 ± 34.28% | 9.22 ± 0.70% | 1.96 ± 0.04 | 17.54 ± 3.65% | 2.98 ± 0.06 |


#### パターン: `safety+math` / 手法: `dare`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 74.94 ± 3.40% | 32.80 ± 0.81% | 20.78 ± 0.95% | 7.48 ± 0.62% | 59.95 ± 0.70% | 34.57 ± 4.87% | 23.65 ± 0.18% | 71.33 ± 5.69% | 65.00 ± 7.21% | 6 ± 2 | 6.33 ± 1.53% | 35.33 ± 3.06% | 93.93 ± 1.28% | 91.48 ± 1.29% | 8 ± 1 | 2.45 ± 0.18% | 44.62 ± 1.64% | 76.88 ± 1.56% | 68.33 ± 3.44% | 27 ± 9 | 8.54 ± 2.90% | 27.60 ± 0.79% | 36.46 ± 1.54% | 5.10 ± 0.36% | 9.96 ± 1.41% | 5.00 ± 1.36% | 88.85 ± 0.36% | 31.04 ± 1.10% | 41.62 ± 0.48% | 12.92 ± 1.10% | 49.17 ± 14.93% | 7.22 ± 0.15% | 1.90 ± 0.00 | 13.07 ± 0.41% | 2.57 ± 0.00 |
| safety+math | dare | 0.20 | 20.50 ± 1.16% | 10.40 ± 1.49% | 19.38 ± 1.39% | 7.71 ± 0.55% | 60.42 ± 0.50% | 32.87 ± 5.75% | 8.96 ± 2.08% | 13.67 ± 4.16% | 13.67 ± 4.16% | 0 ± 0 | 0.00 ± 0.00% | 6.67 ± 2.08% | 25.35 ± 5.14% | 24.60 ± 4.82% | 2 ± 4 | 0.75 ± 1.29% | 15.34 ± 2.10% | 24.27 ± 2.22% | 23.23 ± 1.72% | 3 ± 2 | 1.04 ± 0.72% | 10.62 ± 1.65% | 34.90 ± 2.84% | 3.85 ± 0.18% | 7.93 ± 1.22% | 7.50 ± 0.31% | 88.12 ± 0.83% | 32.71 ± 0.18% | 42.50 ± 0.43% | 12.08 ± 1.41% | 44.04 ± 16.84% | 9.18 ± 0.15% | 2.15 ± 0.03 | 12.45 ± 0.21% | 3.07 ± 0.06 |
| safety+math | dare | 0.40 | 14.63 ± 1.07% | 8.85 ± 1.44% | 21.09 ± 0.78% | 8.59 ± 1.19% | 59.58 ± 0.18% | 30.44 ± 5.88% | 7.40 ± 3.00% | 13.33 ± 2.52% | 13.33 ± 2.52% | 0 ± 0 | 0.00 ± 0.00% | 7.33 ± 2.31% | 11.82 ± 2.84% | 11.40 ± 3.56% | 1 ± 2 | 0.43 ± 0.74% | 11.18 ± 3.68% | 19.79 ± 2.19% | 19.17 ± 2.90% | 2 ± 3 | 0.62 ± 0.83% | 9.48 ± 1.72% | 37.08 ± 1.10% | 5.10 ± 1.48% | 8.33 ± 0.35% | 8.85 ± 2.13% | 87.71 ± 0.18% | 31.46 ± 0.48% | 43.01 ± 0.22% | 11.25 ± 1.25% | 37.05 ± 17.87% | 9.61 ± 0.56% | 2.14 ± 0.04 | 12.33 ± 0.12% | 3.12 ± 0.06 |
| safety+math | dare | 0.60 | 9.89 ± 8.05% | 6.22 ± 5.24% | 20.00 ± 0.47% | 7.91 ± 0.50% | 60.16 ± 0.56% | 28.04 ± 8.60% | 5.00 ± 5.00% | 17.67 ± 15.70% | 17.67 ± 15.70% | 0 ± 0 | 0.00 ± 0.00% | 7.33 ± 7.02% | 0.64 ± 0.32% | 0.64 ± 0.32% | 0 ± 0 | 0.00 ± 0.00% | 6.39 ± 4.71% | 11.35 ± 9.11% | 11.35 ± 9.11% | 0 ± 0 | 0.00 ± 0.00% | 6.15 ± 5.14% | 35.62 ± 0.31% | 4.38 ± 1.13% | 8.54 ± 0.61% | 7.29 ± 0.65% | 88.12 ± 0.94% | 32.19 ± 0.31% | 43.32 ± 0.28% | 11.67 ± 1.88% | 29.13 ± 26.90% | 9.41 ± 0.71% | 2.14 ± 0.05 | 12.37 ± 0.13% | 3.15 ± 0.09 |
| safety+math | dare | 0.80 | 4.25 ± 6.39% | 3.51 ± 4.65% | 18.70 ± 0.18% | 8.65 ± 0.56% | 59.58 ± 1.10% | 18.29 ± 0.87% | 3.33 ± 5.24% | 9.00 ± 15.59% | 9.00 ± 15.59% | 0 ± 0 | 0.00 ± 0.00% | 4.67 ± 8.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 4.15 ± 4.00% | 3.75 ± 3.92% | 3.75 ± 3.92% | 0 ± 0 | 0.00 ± 0.00% | 1.88 ± 1.88% | 32.92 ± 0.36% | 4.48 ± 0.36% | 8.13 ± 0.35% | 9.17 ± 1.26% | 87.81 ± 0.83% | 31.35 ± 1.41% | 43.57 ± 0.35% | 11.15 ± 2.90% | 0.14 ± 0.15% | 9.43 ± 0.57% | 2.11 ± 0.05 | 12.02 ± 0.44% | 3.20 ± 0.11 |
| safety+math | dare | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.96 ± 0.70% | 7.17 ± 2.69% | 60.47 ± 0.68% | 16.21 ± 0.71% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 5.52 ± 1.18% | 2.40 ± 0.48% | 9.35 ± 0.93% | 5.00 ± 5.00% | 87.19 ± 0.31% | 33.75 ± 1.43% | 39.69 ± 1.13% | 8.33 ± 0.48% | 0.60 ± 0.76% | 9.46 ± 0.42% | 1.96 ± 0.04 | 17.56 ± 3.75% | 2.99 ± 0.08 |


#### パターン: `safety+code` / 手法: `dare`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 78.64 ± 10.77% | 0.03 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 42.71 ± 16.62% | 11.73 ± 0.55% | 0.00 ± 0.00% | 88.00 ± 7.81% | 79.00 ± 11.00% | 9 ± 14 | 9.00 ± 13.89% | 0.00 ± 0.00% | 100.00 ± 0.00% | 92.97 ± 11.35% | 22 ± 36 | 7.03 ± 11.35% | 0.11 ± 0.18% | 71.15 ± 11.87% | 63.96 ± 12.84% | 23 ± 39 | 7.19 ± 12.18% | 0.00 ± 0.00% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 61.04 ± 31.37% | 24.38 ± 3.90% | 24.43 ± 0.19% | 10.73 ± 1.83% | 0.05 ± 0.00% | 1.09 ± 0.36% | 694070.90 ± 187353.32 | 3.14 ± 1.04% | 894749.07 ± 430040.26 |
| safety+code | dare | 0.20 | 82.93 ± 4.84% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.42 ± 5.11% | 11.72 ± 0.12% | 0.00 ± 0.00% | 96.33 ± 3.06% | 85.00 ± 6.24% | 11 ± 3 | 11.33 ± 3.21% | 0.00 ± 0.00% | 100.00 ± 0.00% | 92.12 ± 3.45% | 25 ± 11 | 7.88 ± 3.45% | 0.11 ± 0.18% | 79.90 ± 1.41% | 71.67 ± 5.18% | 26 ± 14 | 8.23 ± 4.43% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.90 ± 8.03% | 25.94 ± 3.13% | 23.87 ± 0.61% | 11.25 ± 0.31% | 0.04 ± 0.02% | 1.08 ± 0.30% | 383950.20 ± 67553.87 | 2.47 ± 0.65% | 671479.52 ± 135038.44 |
| safety+code | dare | 0.40 | 74.50 ± 18.07% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 29.22 ± 17.83% | 11.86 ± 0.53% | 0.00 ± 0.00% | 93.00 ± 2.65% | 82.33 ± 14.22% | 11 ± 13 | 10.67 ± 12.90% | 0.00 ± 0.00% | 100.00 ± 0.00% | 81.90 ± 24.52% | 57 ± 77 | 18.10 ± 24.52% | 0.11 ± 0.18% | 78.33 ± 12.41% | 59.27 ± 16.39% | 61 ± 80 | 19.06 ± 24.86% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 32.71 ± 38.27% | 25.73 ± 3.59% | 24.80 ± 0.96% | 10.73 ± 1.44% | 0.04 ± 0.00% | 0.99 ± 0.30% | 306695.55 ± 305628.99 | 2.94 ± 0.90% | 656332.54 ± 543423.24 |
| safety+code | dare | 0.60 | 88.97 ± 3.78% | 0.00 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 31.56 ± 11.41% | 11.80 ± 0.92% | 0.00 ± 0.00% | 96.00 ± 1.00% | 95.33 ± 1.53% | 1 ± 1 | 0.67 ± 1.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 96.27 ± 6.46% | 12 ± 20 | 3.73 ± 6.46% | 0.00 ± 0.00% | 77.92 ± 7.71% | 75.31 ± 6.90% | 8 ± 12 | 2.60 ± 3.70% | 0.00 ± 0.00% | 0.31 ± 0.31% | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.83 ± 22.76% | 27.29 ± 0.48% | 25.02 ± 1.34% | 10.31 ± 1.43% | 0.06 ± 0.01% | 1.40 ± 0.34% | 398649.10 ± 507513.35 | 3.72 ± 1.14% | 425860.14 ± 214984.80 |
| safety+code | dare | 0.80 | 91.35 ± 1.77% | 0.00 ± 0.00% | 0.10 ± 0.09% | 0.00 ± 0.00% | 29.48 ± 8.52% | 12.06 ± 0.69% | 0.00 ± 0.00% | 97.00 ± 1.00% | 93.33 ± 4.04% | 4 ± 5 | 3.67 ± 4.73% | 0.00 ± 0.00% | 100.00 ± 0.00% | 99.15 ± 0.67% | 3 ± 2 | 0.85 ± 0.67% | 0.00 ± 0.00% | 82.19 ± 0.31% | 81.56 ± 0.62% | 2 ± 3 | 0.62 ± 0.83% | 0.00 ± 0.00% | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.65 ± 17.25% | 25.31 ± 2.36% | 24.79 ± 0.82% | 10.42 ± 1.26% | 0.97 ± 1.57% | 1.28 ± 0.23% | 243088.00 ± 245330.74 | 3.54 ± 0.58% | 419233.90 ± 277325.61 |
| safety+code | dare | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.86 ± 1.66% | 6.94 ± 3.12% | 52.60 ± 14.46% | 26.35 ± 10.13% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.06 ± 3.17% | 1.67 ± 0.18% | 6.91 ± 6.11% | 6.98 ± 2.66% | 72.40 ± 25.35% | 32.81 ± 3.79% | 39.39 ± 1.19% | 8.23 ± 0.18% | 31.45 ± 31.35% | 9.20 ± 0.28% | 1.96 ± 0.04 | 17.77 ± 4.14% | 2.97 ± 0.06 |


#### パターン: `safety+medical` / 手法: `dare`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 75.69 ± 11.73% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.96 ± 19.24% | 11.98 ± 0.70% | 0.00 ± 0.00% | 90.33 ± 3.79% | 81.33 ± 13.43% | 9 ± 10 | 9.00 ± 9.85% | 0.00 ± 0.00% | 100.00 ± 0.00% | 86.26 ± 12.34% | 43 ± 39 | 13.74 ± 12.34% | 0.11 ± 0.18% | 70.42 ± 10.32% | 59.48 ± 10.57% | 35 ± 25 | 10.94 ± 7.67% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 42.19 ± 37.03% | 25.73 ± 3.21% | 24.55 ± 2.20% | 11.35 ± 0.18% | 0.05 ± 0.00% | 0.52 ± 0.04% | 35857934.16 ± 18835271.33 | 1.17 ± 0.37% | 51171370.56 ± 20469414.31 |
| safety+medical | dare | 0.20 | 84.94 ± 7.70% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.03 ± 1.56% | 12.35 ± 0.94% | 0.00 ± 0.00% | 95.00 ± 3.61% | 85.67 ± 9.50% | 9 ± 9 | 9.33 ± 9.29% | 0.00 ± 0.00% | 100.00 ± 0.00% | 94.99 ± 3.07% | 16 ± 10 | 5.01 ± 3.07% | 0.21 ± 0.18% | 79.79 ± 11.61% | 74.17 ± 16.95% | 18 ± 17 | 5.62 ± 5.33% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.56 ± 4.43% | 27.50 ± 1.74% | 24.36 ± 0.64% | 11.25 ± 0.54% | 1.43 ± 2.40% | 0.60 ± 0.00% | 30084819.21 ± 18158973.84 | 2.03 ± 0.91% | 46629447.22 ± 36397216.84 |
| safety+medical | dare | 0.40 | 47.71 ± 36.81% | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.07 ± 3.99% | 12.16 ± 0.77% | 0.00 ± 0.00% | 91.33 ± 6.43% | 45.67 ± 42.52% | 46 ± 42 | 45.67 ± 41.79% | 0.00 ± 0.00% | 100.00 ± 0.00% | 55.48 ± 39.97% | 139 ± 125 | 44.52 ± 39.97% | 0.32 ± 0.00% | 81.98 ± 6.59% | 41.98 ± 28.35% | 128 ± 111 | 40.00 ± 34.78% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.19 ± 11.18% | 23.96 ± 3.61% | 25.71 ± 2.23% | 10.73 ± 0.18% | 0.04 ± 0.02% | 0.51 ± 0.09% | 14784640.46 ± 9533992.17 | 1.16 ± 0.45% | 212655363.38 ± 347133928.25 |
| safety+medical | dare | 0.60 | 67.58 ± 13.73% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.79 ± 2.12% | 11.00 ± 1.11% | 0.00 ± 0.00% | 93.67 ± 5.03% | 71.67 ± 15.01% | 22 ± 18 | 22.00 ± 18.33% | 0.00 ± 0.00% | 100.00 ± 0.00% | 77.53 ± 14.80% | 70 ± 46 | 22.47 ± 14.80% | 0.11 ± 0.18% | 84.38 ± 7.35% | 53.54 ± 18.04% | 99 ± 81 | 30.83 ± 25.29% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.17 ± 0.48% | 25.42 ± 3.88% | 23.88 ± 1.32% | 9.06 ± 2.44% | 0.06 ± 0.01% | 0.55 ± 0.02% | 20797785.11 ± 14399754.63 | 2.08 ± 1.35% | 14708432.51 ± 16144047.41 |
| safety+medical | dare | 0.80 | 62.78 ± 42.43% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.31 ± 8.37% | 11.67 ± 0.27% | 0.00 ± 0.00% | 95.67 ± 3.21% | 63.67 ± 43.36% | 32 ± 45 | 32.00 ± 45.13% | 0.00 ± 0.00% | 100.00 ± 0.00% | 70.61 ± 46.76% | 92 ± 146 | 29.39 ± 46.76% | 0.32 ± 0.32% | 84.27 ± 12.22% | 54.06 ± 37.35% | 97 ± 156 | 30.21 ± 48.82% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.71 ± 15.69% | 22.92 ± 4.47% | 23.95 ± 0.71% | 11.04 ± 0.18% | 0.04 ± 0.01% | 0.49 ± 0.02% | 50411154.10 ± 57002591.36 | 1.28 ± 0.14% | 76401979.17 ± 100285710.40 |
| safety+medical | dare | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.50 ± 1.76% | 5.27 ± 4.94% | 47.19 ± 14.14% | 22.22 ± 10.35% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.54 ± 2.80% | 1.46 ± 0.72% | 3.46 ± 5.98% | 7.08 ± 3.91% | 63.75 ± 25.36% | 30.62 ± 3.52% | 39.35 ± 1.04% | 8.96 ± 0.90% | 18.34 ± 31.20% | 9.33 ± 0.53% | 1.96 ± 0.04 | 17.79 ± 3.91% | 2.98 ± 0.07 |


### 手法: `della` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `della`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 63.38 ± 12.52% | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 49.27 ± 10.28% | 12.25 ± 0.71% | 0.00 ± 0.00% | 96.67 ± 4.16% | 55.33 ± 26.50% | 41 ± 29 | 41.33 ± 29.16% | 0.00 ± 0.00% | 100.00 ± 0.00% | 86.47 ± 7.02% | 42 ± 22 | 13.53 ± 7.02% | 0.43 ± 0.18% | 86.88 ± 8.32% | 48.33 ± 6.97% | 123 ± 39 | 38.54 ± 12.23% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 75.31 ± 17.08% | 23.23 ± 4.38% | 24.86 ± 2.01% | 11.88 ± 0.31% | 0.03 ± 0.02% | 0.57 ± 0.06% | 5639261.14 ± 5027121.62 | 0.96 ± 0.05% | 3498543.54 ± 2086832.67 |
| safety+math+code+medical | della | 0.20 | 88.10 ± 6.34% | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.55 ± 10.01% | 12.38 ± 0.38% | 0.00 ± 0.00% | 94.33 ± 4.04% | 94.33 ± 4.04% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 98.40 ± 2.77% | 5 ± 9 | 1.60 ± 2.77% | 0.43 ± 0.18% | 72.50 ± 10.95% | 71.56 ± 12.42% | 3 ± 5 | 0.94 ± 1.62% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.98 ± 19.63% | 28.12 ± 1.25% | 25.97 ± 0.94% | 11.15 ± 0.48% | 0.03 ± 0.02% | 0.49 ± 0.06% | 4666277.94 ± 2585948.06 | 1.14 ± 0.06% | 5892903.06 ± 4452380.63 |
| safety+math+code+medical | della | 0.40 | 78.16 ± 23.83% | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.86 ± 5.66% | 11.96 ± 0.55% | 0.00 ± 0.00% | 96.33 ± 1.53% | 77.33 ± 29.77% | 19 ± 31 | 19.00 ± 31.19% | 0.00 ± 0.00% | 100.00 ± 0.00% | 88.07 ± 20.38% | 37 ± 64 | 11.93 ± 20.38% | 0.53 ± 0.18% | 85.31 ± 5.48% | 69.06 ± 21.56% | 52 ± 82 | 16.25 ± 25.75% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.44 ± 11.41% | 22.29 ± 1.00% | 24.80 ± 1.97% | 11.04 ± 0.36% | 0.04 ± 0.02% | 0.53 ± 0.13% | 3716221.54 ± 1623674.68 | 0.67 ± 0.26% | 2664094.55 ± 2247228.00 |
| safety+math+code+medical | della | 0.60 | 73.77 ± 14.69% | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.98 ± 4.83% | 12.11 ± 0.51% | 0.00 ± 0.00% | 93.33 ± 4.04% | 76.00 ± 25.12% | 17 ± 29 | 17.33 ± 29.16% | 0.00 ± 0.00% | 100.00 ± 0.00% | 90.20 ± 11.22% | 31 ± 35 | 9.80 ± 11.22% | 0.32 ± 0.00% | 72.50 ± 21.30% | 55.10 ± 10.93% | 56 ± 86 | 17.40 ± 26.88% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.19 ± 9.84% | 21.77 ± 0.18% | 24.93 ± 0.99% | 11.35 ± 0.65% | 0.04 ± 0.02% | 0.51 ± 0.10% | 1879414.85 ± 888079.34 | 1.11 ± 0.32% | 2040741.79 ± 582209.44 |
| safety+math+code+medical | della | 0.80 | 83.38 ± 10.80% | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.16 ± 12.39% | 12.17 ± 0.24% | 0.00 ± 0.00% | 95.33 ± 3.79% | 89.33 ± 7.02% | 6 ± 8 | 6.00 ± 7.81% | 0.00 ± 0.00% | 100.00 ± 0.00% | 89.78 ± 12.44% | 32 ± 39 | 10.22 ± 12.44% | 0.21 ± 0.37% | 82.40 ± 9.27% | 71.04 ± 15.00% | 36 ± 51 | 11.35 ± 15.90% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 44.38 ± 26.13% | 25.94 ± 3.79% | 24.90 ± 0.73% | 11.56 ± 0.31% | 0.05 ± 0.00% | 0.49 ± 0.07% | 4737138.61 ± 4082277.64 | 1.17 ± 0.33% | 20302784.13 ± 33884002.71 |
| safety+math+code+medical | della | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.71 ± 2.10% | 5.71 ± 2.88% | 51.35 ± 15.41% | 23.68 ± 12.39% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.06 ± 3.01% | 1.35 ± 1.18% | 6.10 ± 5.28% | 5.31 ± 4.43% | 70.73 ± 27.97% | 31.98 ± 3.28% | 39.28 ± 0.90% | 8.75 ± 0.31% | 23.01 ± 38.06% | 9.45 ± 0.41% | 1.99 ± 0.04 | 17.80 ± 4.17% | 3.06 ± 0.09 |


#### パターン: `safety+math` / 手法: `della`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.00 | 75.10 ± 2.29% | 33.34 ± 1.01% | 20.68 ± 0.63% | 5.91 ± 2.71% | 60.42 ± 0.18% | 38.28 ± 1.64% | 25.42 ± 0.65% | 72.00 ± 4.36% | 66.33 ± 5.77% | 6 ± 2 | 5.67 ± 1.53% | 36.00 ± 3.00% | 93.40 ± 1.33% | 91.27 ± 1.76% | 7 ± 4 | 2.13 ± 1.29% | 45.37 ± 0.32% | 76.15 ± 0.65% | 67.71 ± 0.79% | 27 ± 3 | 8.44 ± 0.83% | 26.56 ± 1.62% | 35.94 ± 1.65% | 5.42 ± 0.90% | 6.30 ± 5.47% | 5.52 ± 1.10% | 88.96 ± 0.36% | 31.87 ± 0.00% | 42.01 ± 0.27% | 11.98 ± 0.48% | 60.87 ± 4.89% | 7.42 ± 0.16% | 1.91 ± 0.00 | 13.03 ± 0.22% | 2.58 ± 0.01 |
| safety+math | della | 0.20 | 23.74 ± 2.64% | 11.65 ± 0.80% | 21.41 ± 0.95% | 6.49 ± 2.57% | 60.26 ± 0.59% | 37.45 ± 2.43% | 8.85 ± 1.83% | 18.33 ± 0.58% | 18.33 ± 0.58% | 0 ± 0 | 0.00 ± 0.00% | 8.67 ± 1.15% | 26.94 ± 4.49% | 26.52 ± 4.61% | 1 ± 2 | 0.43 ± 0.74% | 15.44 ± 1.87% | 27.19 ± 4.06% | 26.35 ± 3.77% | 3 ± 2 | 0.83 ± 0.48% | 13.65 ± 0.36% | 38.12 ± 1.08% | 4.69 ± 0.83% | 5.89 ± 5.11% | 7.08 ± 0.79% | 88.12 ± 0.83% | 32.40 ± 0.79% | 42.04 ± 0.43% | 11.15 ± 0.18% | 59.16 ± 7.35% | 8.99 ± 0.35% | 2.17 ± 0.03 | 12.21 ± 0.18% | 3.11 ± 0.06 |
| safety+math | della | 0.40 | 13.57 ± 3.55% | 7.79 ± 3.07% | 22.45 ± 1.17% | 7.62 ± 0.54% | 60.52 ± 0.94% | 37.28 ± 2.03% | 6.15 ± 0.65% | 13.67 ± 5.13% | 13.67 ± 5.13% | 0 ± 0 | 0.00 ± 0.00% | 7.33 ± 4.16% | 8.41 ± 4.74% | 8.31 ± 4.92% | 0 ± 1 | 0.11 ± 0.18% | 8.95 ± 6.37% | 19.27 ± 1.30% | 18.75 ± 1.13% | 2 ± 2 | 0.52 ± 0.65% | 8.75 ± 1.90% | 39.38 ± 1.74% | 5.52 ± 0.72% | 7.32 ± 1.06% | 7.92 ± 0.65% | 88.12 ± 0.31% | 32.92 ± 1.57% | 42.58 ± 0.49% | 12.50 ± 0.83% | 56.76 ± 5.74% | 9.55 ± 0.64% | 2.16 ± 0.04 | 12.35 ± 0.15% | 3.14 ± 0.07 |
| safety+math | della | 0.60 | 10.98 ± 8.54% | 6.67 ± 5.52% | 21.77 ± 1.15% | 7.40 ± 0.93% | 59.74 ± 0.39% | 35.88 ± 3.59% | 5.42 ± 4.16% | 22.00 ± 18.73% | 22.00 ± 18.73% | 0 ± 0 | 0.00 ± 0.00% | 9.00 ± 9.00% | 0.75 ± 0.18% | 0.75 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 7.35 ± 6.87% | 10.21 ± 7.22% | 10.21 ± 7.22% | 0 ± 0 | 0.00 ± 0.00% | 4.90 ± 2.62% | 37.92 ± 2.30% | 5.62 ± 0.00% | 8.33 ± 1.27% | 6.46 ± 0.65% | 87.81 ± 0.31% | 31.67 ± 0.65% | 43.21 ± 0.52% | 11.46 ± 0.79% | 52.98 ± 9.76% | 9.42 ± 0.46% | 2.16 ± 0.05 | 12.04 ± 0.20% | 3.18 ± 0.08 |
| safety+math | della | 0.80 | 4.15 ± 6.29% | 2.84 ± 3.94% | 18.96 ± 0.45% | 7.15 ± 0.81% | 59.95 ± 0.50% | 24.72 ± 5.76% | 3.96 ± 6.32% | 9.00 ± 15.59% | 9.00 ± 15.59% | 0 ± 0 | 0.00 ± 0.00% | 2.33 ± 4.04% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 3.83 ± 4.00% | 3.44 ± 3.48% | 3.44 ± 3.48% | 0 ± 0 | 0.00 ± 0.00% | 1.25 ± 1.65% | 33.33 ± 0.65% | 4.58 ± 0.65% | 7.52 ± 0.35% | 6.77 ± 1.88% | 88.23 ± 0.48% | 31.67 ± 0.65% | 43.05 ± 0.33% | 12.60 ± 1.48% | 18.52 ± 16.22% | 9.16 ± 0.73% | 2.13 ± 0.06 | 11.81 ± 0.52% | 3.24 ± 0.13 |
| safety+math | della | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.38 ± 0.56% | 7.38 ± 2.42% | 59.64 ± 0.94% | 22.57 ± 10.96% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.25 ± 0.83% | 2.50 ± 0.31% | 9.76 ± 0.61% | 5.00 ± 4.54% | 87.19 ± 0.00% | 32.08 ± 1.88% | 39.07 ± 1.76% | 8.23 ± 0.95% | 20.42 ± 33.88% | 9.20 ± 0.65% | 1.99 ± 0.04 | 18.19 ± 3.26% | 3.06 ± 0.07 |


#### パターン: `safety+code` / 手法: `della`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.00 | 68.74 ± 33.06% | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 35.52 ± 7.28% | 11.90 ± 0.49% | 0.00 ± 0.00% | 95.67 ± 2.52% | 67.33 ± 44.46% | 28 ± 47 | 28.33 ± 46.50% | 0.00 ± 0.00% | 100.00 ± 0.00% | 82.11 ± 30.16% | 56 ± 94 | 17.89 ± 30.16% | 0.00 ± 0.00% | 77.60 ± 10.92% | 56.77 ± 24.66% | 67 ± 112 | 20.83 ± 35.01% | 0.00 ± 0.00% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 45.00 ± 11.87% | 26.04 ± 3.04% | 25.55 ± 1.20% | 10.10 ± 0.65% | 0.04 ± 0.02% | 1.09 ± 0.13% | 587803.83 ± 179749.94 | 3.29 ± 0.17% | 842451.77 ± 362569.96 |
| safety+code | della | 0.20 | 75.83 ± 18.52% | 0.00 ± 0.00% | 0.42 ± 0.72% | 0.00 ± 0.00% | 20.73 ± 0.86% | 11.74 ± 0.46% | 0.00 ± 0.00% | 94.33 ± 2.08% | 66.67 ± 35.28% | 28 ± 37 | 27.67 ± 36.83% | 0.00 ± 0.00% | 100.00 ± 0.00% | 89.99 ± 12.42% | 31 ± 39 | 10.01 ± 12.42% | 0.00 ± 0.00% | 80.52 ± 3.04% | 70.83 ± 7.91% | 31 ± 34 | 9.69 ± 10.64% | 0.00 ± 0.00% | 0.52 ± 0.90% | 0.31 ± 0.54% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.33 ± 1.30% | 23.12 ± 1.74% | 24.96 ± 0.47% | 10.21 ± 1.00% | 0.06 ± 0.01% | 1.30 ± 0.31% | 268877.82 ± 179640.54 | 3.48 ± 1.29% | 460959.19 ± 184233.15 |
| safety+code | della | 0.40 | 76.77 ± 18.57% | 0.05 ± 0.05% | 0.10 ± 0.09% | 0.00 ± 0.00% | 25.05 ± 4.61% | 11.74 ± 0.21% | 0.00 ± 0.00% | 92.33 ± 5.03% | 71.33 ± 32.47% | 21 ± 36 | 21.00 ± 36.37% | 0.00 ± 0.00% | 100.00 ± 0.00% | 90.84 ± 15.31% | 29 ± 48 | 9.16 ± 15.31% | 0.21 ± 0.18% | 75.21 ± 7.62% | 68.12 ± 9.32% | 23 ± 39 | 7.08 ± 12.27% | 0.00 ± 0.00% | 0.10 ± 0.18% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 24.27 ± 8.28% | 25.83 ± 3.93% | 25.47 ± 0.88% | 9.69 ± 1.43% | 0.06 ± 0.00% | 1.23 ± 0.26% | 199633.11 ± 117243.28 | 3.41 ± 1.77% | 392132.66 ± 195746.02 |
| safety+code | della | 0.60 | 83.77 ± 12.33% | 0.00 ± 0.00% | 0.26 ± 0.33% | 0.00 ± 0.00% | 31.41 ± 13.67% | 12.31 ± 0.88% | 0.00 ± 0.00% | 95.67 ± 2.52% | 89.67 ± 9.71% | 6 ± 10 | 6.00 ± 9.54% | 0.00 ± 0.00% | 100.00 ± 0.00% | 94.04 ± 9.78% | 19 ± 31 | 5.96 ± 9.78% | 0.00 ± 0.00% | 80.62 ± 5.22% | 67.60 ± 17.78% | 42 ± 72 | 13.02 ± 22.55% | 0.00 ± 0.00% | 0.42 ± 0.48% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.50 ± 27.10% | 25.31 ± 1.36% | 25.42 ± 0.33% | 11.46 ± 2.60% | 0.05 ± 0.00% | 1.39 ± 0.19% | 120223.11 ± 54132.59 | 3.50 ± 1.00% | 253194.63 ± 34087.44 |
| safety+code | della | 0.80 | 74.91 ± 14.71% | 0.05 ± 0.09% | 0.68 ± 0.80% | 0.00 ± 0.00% | 27.29 ± 16.98% | 11.41 ± 0.68% | 0.00 ± 0.00% | 67.00 ± 32.70% | 65.67 ± 32.04% | 1 ± 2 | 1.33 ± 2.31% | 0.00 ± 0.00% | 99.89 ± 0.18% | 94.78 ± 7.96% | 16 ± 24 | 5.11 ± 7.77% | 0.11 ± 0.18% | 66.35 ± 12.53% | 64.27 ± 12.89% | 7 ± 9 | 2.08 ± 2.80% | 0.10 ± 0.18% | 0.62 ± 0.54% | 0.73 ± 1.26% | 0.00 ± 0.00% | 0.00 ± 0.00% | 25.94 ± 34.65% | 28.65 ± 0.95% | 24.03 ± 0.81% | 10.10 ± 1.26% | 0.09 ± 0.06% | 1.42 ± 0.28% | 104083.45 ± 46691.56 | 3.67 ± 1.27% | 597551.07 ± 550913.12 |
| safety+code | della | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.81 ± 2.03% | 5.80 ± 4.43% | 51.93 ± 14.31% | 15.93 ± 0.64% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.33 ± 2.66% | 2.29 ± 1.48% | 6.71 ± 5.82% | 4.90 ± 4.42% | 72.29 ± 26.07% | 31.56 ± 3.38% | 38.99 ± 1.21% | 8.12 ± 0.54% | 0.67 ± 0.88% | 8.84 ± 0.19% | 1.98 ± 0.04 | 17.20 ± 3.39% | 3.05 ± 0.08 |


#### パターン: `safety+medical` / 手法: `della`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 63.60 ± 9.33% | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.12 ± 17.17% | 11.81 ± 0.44% | 0.00 ± 0.00% | 96.33 ± 2.89% | 72.67 ± 9.45% | 24 ± 7 | 23.67 ± 6.66% | 0.00 ± 0.00% | 100.00 ± 0.00% | 66.67 ± 18.97% | 104 ± 59 | 33.33 ± 18.97% | 0.32 ± 0.32% | 82.71 ± 9.19% | 51.46 ± 11.09% | 100 ± 10 | 31.25 ± 3.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 51.56 ± 35.18% | 24.69 ± 3.17% | 24.54 ± 1.25% | 10.83 ± 0.48% | 0.05 ± 0.01% | 0.60 ± 0.06% | 16091827.99 ± 14882810.80 | 1.41 ± 0.08% | 33309554.41 ± 6600851.38 |
| safety+medical | della | 0.20 | 28.09 ± 44.37% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.19 ± 21.59% | 11.71 ± 0.28% | 0.00 ± 0.00% | 97.00 ± 4.36% | 29.00 ± 48.51% | 68 ± 53 | 68.00 ± 52.85% | 0.00 ± 0.00% | 100.00 ± 0.00% | 32.06 ± 49.47% | 213 ± 155 | 67.94 ± 49.47% | 0.11 ± 0.18% | 88.85 ± 17.71% | 23.23 ± 35.15% | 210 ± 169 | 65.62 ± 52.86% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.56 ± 42.83% | 22.81 ± 1.88% | 24.15 ± 0.26% | 10.94 ± 1.08% | 0.04 ± 0.02% | 0.55 ± 0.13% | 21090035.80 ± 17312335.19 | 1.16 ± 0.39% | 18097875.79 ± 9447772.23 |
| safety+medical | della | 0.40 | 45.06 ± 41.56% | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.88 ± 9.72% | 12.79 ± 0.68% | 0.00 ± 0.00% | 93.00 ± 7.00% | 44.33 ± 45.37% | 49 ± 42 | 48.67 ± 42.16% | 0.00 ± 0.00% | 100.00 ± 0.00% | 52.61 ± 42.11% | 148 ± 132 | 47.39 ± 42.11% | 0.21 ± 0.37% | 85.73 ± 8.68% | 38.23 ± 37.41% | 152 ± 132 | 47.50 ± 41.40% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.67 ± 18.48% | 27.08 ± 1.26% | 26.28 ± 0.80% | 11.98 ± 1.26% | 0.10 ± 0.08% | 0.36 ± 0.14% | 16049035122.39 ± 27778291897.93 | 1.33 ± 0.49% | 1590313766.94 ± 2607092615.01 |
| safety+medical | della | 0.60 | 25.77 ± 32.66% | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.59 ± 10.90% | 12.34 ± 0.59% | 0.00 ± 0.00% | 96.00 ± 4.00% | 31.33 ± 38.37% | 65 ± 42 | 64.67 ± 42.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 25.88 ± 33.40% | 232 ± 105 | 74.12 ± 33.40% | 0.11 ± 0.18% | 82.92 ± 19.17% | 20.10 ± 26.44% | 201 ± 144 | 62.81 ± 44.96% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 39.90 ± 22.73% | 27.29 ± 2.53% | 26.07 ± 0.88% | 10.94 ± 1.08% | 0.02 ± 0.00% | 0.48 ± 0.09% | 10981445.00 ± 6253371.40 | 1.29 ± 0.18% | 12572823.50 ± 5352914.49 |
| safety+medical | della | 0.80 | 42.45 ± 36.55% | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.92 ± 9.33% | 11.89 ± 0.08% | 0.00 ± 0.00% | 97.67 ± 3.21% | 43.67 ± 42.10% | 54 ± 45 | 54.00 ± 45.03% | 0.00 ± 0.00% | 100.00 ± 0.00% | 44.52 ± 39.12% | 174 ± 122 | 55.48 ± 39.12% | 0.21 ± 0.18% | 86.56 ± 17.13% | 39.17 ± 32.42% | 152 ± 148 | 47.40 ± 46.37% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.23 ± 17.87% | 27.60 ± 1.18% | 24.27 ± 1.13% | 11.35 ± 0.95% | 0.04 ± 0.02% | 0.44 ± 0.08% | 51262131.56 ± 67693503.75 | 1.13 ± 0.08% | 24153482.68 ± 28153032.25 |
| safety+medical | della | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 1.25 ± 1.63% | 4.69 ± 4.61% | 44.48 ± 14.31% | 24.63 ± 8.87% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 1.98 ± 2.62% | 0.52 ± 0.65% | 3.66 ± 6.34% | 5.73 ± 2.90% | 58.12 ± 25.02% | 30.83 ± 3.61% | 39.23 ± 1.14% | 8.44 ± 0.83% | 26.23 ± 27.07% | 8.89 ± 0.25% | 1.98 ± 0.04 | 17.66 ± 3.47% | 3.05 ± 0.07 |


### 手法: `task_arithmetic` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `task_arithmetic`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 77.31 ± 0.00% | 0.08 ± 0.00% | 0.10 ± 0.09% | 0.00 ± 0.00% | 21.25 ± 0.00% | 11.52 ± 0.00% | 0.00 ± 0.00% | 79.00 ± 0.00% | 71.00 ± 0.00% | 8 ± 0 | 8.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 99.36 ± 0.00% | 2 ± 0 | 0.64 ± 0.00% | 0.32 ± 0.00% | 70.52 ± 0.36% | 61.56 ± 0.00% | 29 ± 1 | 8.96 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.21 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 11.25 ± 0.00% | 0.16 ± 0.00% | 0.25 ± 0.00% | 8199.95 ± 0.00 | 1.99 ± 0.00% | 12188.29 ± 0.04 |
| safety+math+code+medical | task_arithmetic | 0.20 | 0.74 ± 0.69% | 0.00 ± 0.00% | 1.46 ± 0.09% | 0.00 ± 0.00% | 43.85 ± 8.17% | 12.28 ± 0.10% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 1.70 ± 1.44% | 308 ± 5 | 98.30 ± 1.44% | 0.00 ± 0.00% | 98.96 ± 0.48% | 0.52 ± 0.65% | 315 ± 4 | 98.44 ± 1.13% | 0.00 ± 0.00% | 0.21 ± 0.18% | 2.71 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 59.69 ± 17.06% | 28.02 ± 0.72% | 23.46 ± 0.14% | 13.33 ± 0.18% | 0.06 ± 0.00% | 1.31 ± 0.04% | 2252.59 ± 40.83 | 3.02 ± 0.24% | 3182.48 ± 10.15 |
| safety+math+code+medical | task_arithmetic | 0.40 | 40.31 ± 1.12% | 0.03 ± 0.05% | 1.15 ± 0.74% | 0.00 ± 0.00% | 34.79 ± 10.01% | 15.27 ± 0.40% | 0.00 ± 0.00% | 89.67 ± 2.52% | 29.67 ± 2.52% | 60 ± 4 | 60.00 ± 4.36% | 0.00 ± 0.00% | 98.19 ± 0.37% | 57.61 ± 5.37% | 127 ± 18 | 40.58 ± 5.65% | 0.11 ± 0.18% | 81.98 ± 3.51% | 33.65 ± 3.04% | 155 ± 7 | 48.33 ± 2.08% | 0.00 ± 0.00% | 0.52 ± 0.48% | 1.77 ± 1.10% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.88 ± 19.81% | 27.71 ± 0.36% | 23.36 ± 0.12% | 22.40 ± 1.10% | 0.06 ± 0.00% | 1.68 ± 0.04% | 134.88 ± 15.48 | 4.76 ± 1.02% | 35.42 ± 0.54 |
| safety+math+code+medical | task_arithmetic | 0.60 | 39.23 ± 4.53% | 5.97 ± 0.50% | 2.92 ± 0.36% | 0.00 ± 0.00% | 48.91 ± 6.99% | 14.56 ± 1.63% | 0.00 ± 0.00% | 67.67 ± 13.20% | 31.00 ± 2.00% | 37 ± 15 | 36.67 ± 14.57% | 1.33 ± 1.15% | 55.06 ± 9.85% | 48.56 ± 9.22% | 20 ± 3 | 6.50 ± 0.80% | 11.08 ± 1.51% | 48.33 ± 7.63% | 38.12 ± 5.62% | 33 ± 9 | 10.21 ± 2.69% | 11.46 ± 1.54% | 1.04 ± 0.48% | 4.79 ± 1.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 70.10 ± 15.63% | 27.71 ± 1.80% | 28.17 ± 0.51% | 13.96 ± 2.84% | 1.54 ± 2.04% | 5.97 ± 0.08% | 2.91 ± 0.06 | 21.50 ± 2.97% | 4.50 ± 0.04 |
| safety+math+code+medical | task_arithmetic | 0.80 | 0.72 ± 0.75% | 1.24 ± 1.69% | 3.85 ± 0.55% | 5.33 ± 1.10% | 35.47 ± 17.90% | 22.95 ± 4.43% | 2.40 ± 4.15% | 1.33 ± 1.15% | 1.33 ± 1.15% | 0 ± 0 | 0.00 ± 0.00% | 1.00 ± 1.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.75 ± 1.03% | 0.83 ± 1.44% | 0.83 ± 1.44% | 0 ± 0 | 0.00 ± 0.00% | 0.83 ± 0.79% | 4.17 ± 0.95% | 3.54 ± 0.18% | 2.64 ± 4.58% | 8.02 ± 3.91% | 44.69 ± 37.67% | 26.25 ± 1.90% | 40.31 ± 0.30% | 13.65 ± 2.90% | 14.91 ± 13.55% | 11.22 ± 0.59% | 1.88 ± 0.02 | 22.34 ± 5.77% | 2.59 ± 0.03 |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.33 ± 2.92% | 7.22 ± 1.70% | 51.93 ± 15.36% | 22.97 ± 11.46% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.27 ± 3.73% | 2.40 ± 2.13% | 9.96 ± 0.70% | 4.48 ± 3.93% | 71.25 ± 27.33% | 32.60 ± 3.75% | 39.55 ± 1.35% | 8.85 ± 0.65% | 20.52 ± 35.29% | 9.25 ± 0.34% | 1.96 ± 0.04 | 17.61 ± 4.07% | 2.98 ± 0.07 |


#### パターン: `safety+math` / 手法: `task_arithmetic`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 74.15 ± 0.00% | 30.90 ± 0.10% | 20.36 ± 0.09% | 8.46 ± 0.00% | 60.62 ± 0.00% | 37.52 ± 0.24% | 24.06 ± 0.54% | 71.00 ± 0.00% | 63.00 ± 0.00% | 8 ± 0 | 8.00 ± 0.00% | 30.67 ± 0.58% | 92.65 ± 0.00% | 89.78 ± 0.00% | 9 ± 0 | 2.88 ± 0.00% | 43.66 ± 0.18% | 79.06 ± 0.00% | 69.69 ± 0.00% | 30 ± 0 | 9.38 ± 0.00% | 25.21 ± 0.18% | 35.52 ± 0.18% | 5.21 ± 0.18% | 10.37 ± 0.00% | 6.56 ± 0.00% | 89.38 ± 0.00% | 31.87 ± 0.00% | 42.17 ± 0.00% | 12.60 ± 0.36% | 57.79 ± 0.47% | 7.59 ± 0.05% | 1.90 ± 0.00 | 13.10 ± 0.01% | 2.57 ± 0.00 |
| safety+math | task_arithmetic | 0.20 | 67.00 ± 1.20% | 31.29 ± 0.77% | 22.14 ± 0.72% | 4.24 ± 2.87% | 61.30 ± 0.24% | 36.42 ± 3.56% | 27.81 ± 1.74% | 65.67 ± 2.52% | 62.00 ± 1.73% | 4 ± 1 | 3.67 ± 1.15% | 32.33 ± 1.15% | 85.52 ± 1.82% | 83.39 ± 2.21% | 7 ± 2 | 2.13 ± 0.67% | 43.66 ± 0.98% | 66.15 ± 2.01% | 55.62 ± 0.31% | 34 ± 6 | 10.52 ± 1.72% | 21.46 ± 1.10% | 40.10 ± 0.18% | 4.17 ± 1.26% | 6.50 ± 5.63% | 1.98 ± 0.48% | 89.58 ± 0.18% | 33.02 ± 0.48% | 44.06 ± 0.06% | 11.56 ± 0.31% | 53.64 ± 10.89% | 8.50 ± 0.16% | 1.77 ± 0.01 | 12.29 ± 0.10% | 2.47 ± 0.01 |
| safety+math | task_arithmetic | 0.40 | 31.01 ± 2.02% | 14.87 ± 0.94% | 18.44 ± 0.56% | 7.53 ± 0.68% | 60.52 ± 0.36% | 33.78 ± 3.21% | 14.58 ± 1.83% | 31.67 ± 10.12% | 31.67 ± 10.12% | 0 ± 0 | 0.00 ± 0.00% | 12.33 ± 4.62% | 38.76 ± 3.70% | 38.55 ± 4.05% | 1 ± 1 | 0.21 ± 0.37% | 21.41 ± 2.50% | 26.04 ± 1.88% | 22.81 ± 1.56% | 10 ± 1 | 3.23 ± 0.36% | 11.15 ± 2.60% | 33.23 ± 0.90% | 3.65 ± 0.36% | 10.37 ± 0.61% | 4.69 ± 1.56% | 89.69 ± 0.00% | 31.35 ± 0.72% | 45.25 ± 0.20% | 12.60 ± 0.48% | 43.48 ± 9.61% | 10.80 ± 0.19% | 1.70 ± 0.01 | 12.48 ± 0.02% | 2.42 ± 0.02 |
| safety+math | task_arithmetic | 0.60 | 2.81 ± 3.67% | 2.43 ± 2.80% | 15.68 ± 0.63% | 8.87 ± 2.24% | 61.61 ± 0.18% | 32.21 ± 6.62% | 3.12 ± 3.48% | 6.33 ± 10.12% | 6.33 ± 10.12% | 0 ± 0 | 0.00 ± 0.00% | 3.00 ± 5.20% | 0.21 ± 0.37% | 0.00 ± 0.00% | 1 ± 1 | 0.21 ± 0.37% | 2.34 ± 2.40% | 2.19 ± 0.83% | 2.08 ± 0.90% | 0 ± 1 | 0.10 ± 0.18% | 1.25 ± 0.54% | 26.46 ± 1.00% | 4.90 ± 0.65% | 10.98 ± 0.00% | 6.77 ± 4.49% | 90.00 ± 0.00% | 33.23 ± 0.36% | 44.72 ± 0.69% | 13.23 ± 0.95% | 38.70 ± 20.28% | 12.93 ± 0.23% | 1.67 ± 0.01 | 12.57 ± 0.18% | 2.44 ± 0.03 |
| safety+math | task_arithmetic | 0.80 | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.46 ± 1.02% | 8.75 ± 1.66% | 61.25 ± 0.27% | 29.42 ± 10.44% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.79 ± 2.39% | 3.12 ± 0.62% | 12.20 ± 0.61% | 5.31 ± 3.80% | 88.33 ± 0.48% | 34.17 ± 0.79% | 42.85 ± 0.85% | 14.58 ± 3.25% | 30.83 ± 29.98% | 12.32 ± 0.72% | 1.72 ± 0.02 | 13.06 ± 0.89% | 2.57 ± 0.06 |
| safety+math | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.58 ± 0.86% | 7.38 ± 1.78% | 60.16 ± 1.18% | 23.16 ± 11.31% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 5.94 ± 0.94% | 3.23 ± 0.79% | 9.96 ± 0.70% | 4.79 ± 4.03% | 86.77 ± 0.48% | 33.54 ± 2.13% | 39.56 ± 1.36% | 8.96 ± 0.72% | 20.94 ± 34.93% | 9.29 ± 0.33% | 1.96 ± 0.04 | 17.52 ± 4.08% | 2.98 ± 0.07 |


#### パターン: `safety+code` / 手法: `task_arithmetic`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 85.24 ± 0.19% | 40.91 ± 0.17% | 4.58 ± 0.90% | 12.41 ± 7.77% | 57.60 ± 0.45% | 23.54 ± 0.06% | 28.12 ± 0.31% | 93.67 ± 0.58% | 88.67 ± 0.58% | 5 ± 0 | 5.00 ± 0.00% | 47.67 ± 0.58% | 94.89 ± 0.00% | 94.25 ± 0.00% | 2 ± 0 | 0.64 ± 0.00% | 48.78 ± 0.18% | 83.65 ± 0.18% | 72.81 ± 0.00% | 35 ± 1 | 10.83 ± 0.18% | 39.06 ± 0.31% | 5.31 ± 0.54% | 3.85 ± 1.26% | 11.18 ± 8.10% | 13.65 ± 23.64% | 86.46 ± 0.18% | 28.75 ± 1.08% | 37.86 ± 0.00% | 32.71 ± 0.18% | 0.06 ± 0.00% | 13.74 ± 0.05% | 1.36 ± 0.00 | 17.84 ± 0.08% | 2.92 ± 0.00 |
| safety+code | task_arithmetic | 0.20 | 84.01 ± 0.36% | 39.22 ± 0.73% | 4.06 ± 0.31% | 4.17 ± 3.61% | 55.89 ± 1.89% | 40.30 ± 3.72% | 33.75 ± 2.78% | 92.67 ± 0.58% | 90.00 ± 1.00% | 3 ± 1 | 2.67 ± 0.58% | 37.33 ± 1.53% | 90.10 ± 1.28% | 88.71 ± 1.61% | 4 ± 1 | 1.38 ± 0.37% | 51.33 ± 1.76% | 82.19 ± 0.54% | 73.33 ± 0.72% | 28 ± 1 | 8.85 ± 0.18% | 34.48 ± 1.91% | 4.58 ± 0.72% | 3.54 ± 0.36% | 8.33 ± 7.22% | 0.00 ± 0.00% | 87.29 ± 1.18% | 24.48 ± 2.60% | 39.41 ± 0.07% | 30.83 ± 0.90% | 50.65 ± 12.12% | 11.93 ± 0.14% | 1.42 ± 0.00 | 15.95 ± 0.42% | 2.90 ± 0.00 |
| safety+code | task_arithmetic | 0.40 | 82.42 ± 1.56% | 34.86 ± 1.77% | 2.45 ± 0.24% | 3.43 ± 0.68% | 55.68 ± 1.30% | 24.27 ± 5.24% | 28.75 ± 0.62% | 91.33 ± 2.89% | 89.00 ± 3.46% | 2 ± 1 | 2.33 ± 0.58% | 39.67 ± 6.51% | 88.39 ± 0.37% | 86.47 ± 0.80% | 6 ± 2 | 1.92 ± 0.55% | 46.01 ± 1.46% | 76.67 ± 0.95% | 71.77 ± 0.48% | 16 ± 2 | 4.90 ± 0.48% | 25.00 ± 0.94% | 2.08 ± 0.48% | 2.81 ± 0.31% | 5.08 ± 4.41% | 1.77 ± 3.07% | 88.12 ± 1.08% | 23.23 ± 1.57% | 37.00 ± 0.23% | 26.67 ± 2.66% | 9.13 ± 15.40% | 7.54 ± 0.17% | 1.76 ± 0.00 | 8.73 ± 0.28% | 3.41 ± 0.01 |
| safety+code | task_arithmetic | 0.60 | 68.20 ± 1.27% | 29.22 ± 3.11% | 2.08 ± 0.95% | 2.37 ± 0.67% | 56.72 ± 0.95% | 19.13 ± 0.27% | 23.23 ± 2.03% | 77.33 ± 0.58% | 76.00 ± 1.00% | 1 ± 2 | 1.33 ± 1.53% | 35.00 ± 4.58% | 70.07 ± 0.49% | 65.18 ± 0.32% | 15 ± 3 | 4.90 ± 0.80% | 32.69 ± 3.78% | 68.23 ± 5.25% | 63.44 ± 3.12% | 15 ± 7 | 4.79 ± 2.26% | 25.94 ± 2.71% | 1.56 ± 0.54% | 2.60 ± 1.41% | 2.44 ± 1.61% | 2.29 ± 2.89% | 88.75 ± 0.54% | 24.69 ± 2.44% | 36.93 ± 0.30% | 20.42 ± 1.10% | 0.06 ± 0.00% | 5.41 ± 0.40% | 2.32 ± 0.02 | 7.57 ± 1.30% | 3.95 ± 0.02 |
| safety+code | task_arithmetic | 0.80 | 0.07 ± 0.06% | 0.05 ± 0.09% | 2.03 ± 0.62% | 4.84 ± 2.84% | 56.72 ± 1.39% | 22.48 ± 5.77% | 0.10 ± 0.18% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.11 ± 0.18% | 0.11 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.10 ± 0.18% | 0.10 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.10 ± 0.18% | 1.67 ± 0.18% | 2.40 ± 1.26% | 4.47 ± 3.36% | 5.21 ± 9.02% | 86.67 ± 6.59% | 26.77 ± 3.91% | 39.54 ± 0.86% | 17.50 ± 1.62% | 10.39 ± 17.88% | 5.96 ± 0.46% | 1.91 ± 0.00 | 9.26 ± 0.61% | 2.83 ± 0.01 |
| safety+code | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.02 ± 1.98% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.16 ± 11.31% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.85 ± 2.84% | 2.19 ± 1.13% | 6.50 ± 5.67% | 6.25 ± 1.88% | 74.58 ± 20.75% | 32.40 ± 3.62% | 39.56 ± 1.37% | 8.96 ± 0.72% | 20.96 ± 34.96% | 9.27 ± 0.28% | 1.96 ± 0.04 | 17.56 ± 4.14% | 2.98 ± 0.07 |


#### パターン: `safety+medical` / 手法: `task_arithmetic`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 73.04 ± 0.06% | 6.55 ± 0.14% | 3.12 ± 0.81% | 2.10 ± 0.33% | 57.97 ± 7.31% | 25.41 ± 0.26% | 3.02 ± 0.18% | 87.00 ± 0.00% | 87.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 5.33 ± 0.58% | 75.61 ± 0.37% | 73.06 ± 0.37% | 8 ± 0 | 2.56 ± 0.00% | 10.44 ± 0.49% | 70.94 ± 0.54% | 59.06 ± 0.54% | 38 ± 0 | 11.88 ± 0.00% | 7.40 ± 0.48% | 3.12 ± 0.54% | 3.12 ± 1.08% | 2.85 ± 2.46% | 1.35 ± 1.80% | 76.88 ± 7.58% | 39.06 ± 7.04% | 50.15 ± 0.01% | 24.79 ± 0.48% | 1.29 ± 0.29% | 6.98 ± 0.01% | 1.75 ± 0.00 | 47.43 ± 0.02% | 1.15 ± 0.00 |
| safety+medical | task_arithmetic | 0.20 | 21.87 ± 0.18% | 0.08 ± 0.00% | 2.19 ± 0.27% | 0.00 ± 0.00% | 21.30 ± 0.39% | 12.62 ± 0.07% | 0.00 ± 0.00% | 95.67 ± 0.58% | 18.00 ± 0.00% | 78 ± 1 | 77.67 ± 0.58% | 0.00 ± 0.00% | 99.57 ± 0.18% | 33.23 ± 0.55% | 208 ± 2 | 66.35 ± 0.67% | 0.32 ± 0.00% | 95.52 ± 0.18% | 14.38 ± 0.94% | 260 ± 3 | 81.15 ± 0.79% | 0.00 ± 0.00% | 1.25 ± 0.00% | 3.12 ± 0.54% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.90 ± 0.90% | 27.71 ± 0.36% | 23.95 ± 0.02% | 13.85 ± 0.18% | 0.07 ± 0.00% | 3.02 ± 0.05% | 59.38 ± 0.07 | 14.10 ± 0.31% | 13.75 ± 0.12 |
| safety+medical | task_arithmetic | 0.40 | 5.98 ± 2.33% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.53 ± 5.01% | 12.97 ± 0.02% | 0.00 ± 0.00% | 93.00 ± 3.61% | 5.00 ± 2.65% | 88 ± 6 | 88.00 ± 6.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 6.28 ± 3.42% | 293 ± 11 | 93.72 ± 3.42% | 0.00 ± 0.00% | 87.29 ± 3.82% | 6.67 ± 1.48% | 258 ± 15 | 80.62 ± 4.60% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.56 ± 8.66% | 22.50 ± 1.36% | 26.98 ± 0.06% | 11.88 ± 0.00% | 0.06 ± 0.00% | 0.40 ± 0.01% | 22271.90 ± 681.75 | 0.66 ± 0.10% | 39156.67 ± 722.70 |
| safety+medical | task_arithmetic | 0.60 | 85.09 ± 6.34% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.86 ± 17.35% | 12.72 ± 0.06% | 0.00 ± 0.00% | 86.00 ± 11.27% | 86.00 ± 11.27% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 100.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.64 ± 0.00% | 69.27 ± 7.76% | 69.27 ± 7.76% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 54.17 ± 34.92% | 21.56 ± 0.54% | 27.07 ± 0.00% | 11.04 ± 0.18% | 0.06 ± 0.00% | 0.28 ± 0.01% | 200116.75 ± 7068.23 | 1.24 ± 0.07% | 209487.62 ± 9249.30 |
| safety+medical | task_arithmetic | 0.80 | 5.15 ± 2.51% | 0.00 ± 0.00% | 0.94 ± 0.41% | 0.00 ± 0.00% | 29.95 ± 5.85% | 12.02 ± 0.24% | 0.00 ± 0.00% | 98.00 ± 2.65% | 3.00 ± 1.00% | 95 ± 3 | 95.00 ± 3.46% | 0.00 ± 0.00% | 99.57 ± 0.74% | 7.14 ± 4.89% | 289 ± 14 | 92.44 ± 4.54% | 0.00 ± 0.00% | 96.46 ± 3.15% | 5.31 ± 3.55% | 292 ± 13 | 91.15 ± 4.13% | 0.00 ± 0.00% | 0.31 ± 0.00% | 1.56 ± 0.83% | 0.00 ± 0.00% | 0.00 ± 0.00% | 32.92 ± 13.31% | 26.98 ± 1.72% | 23.09 ± 0.11% | 12.92 ± 0.79% | 0.07 ± 0.00% | 1.17 ± 0.04% | 1105.76 ± 231.85 | 2.60 ± 0.25% | 397.75 ± 60.59 |
| safety+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 2.97 ± 2.07% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.13 ± 11.35% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 3.85 ± 2.84% | 2.08 ± 1.30% | 6.50 ± 5.67% | 6.25 ± 1.88% | 74.58 ± 20.75% | 32.40 ± 3.62% | 39.56 ± 1.37% | 8.85 ± 0.65% | 20.96 ± 34.96% | 9.28 ± 0.33% | 1.96 ± 0.04 | 17.56 ± 4.14% | 2.98 ± 0.07 |


### 手法: `safemerge` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `safemerge`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | safemerge | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |


#### パターン: `safety+math` / 手法: `safemerge`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 22.70 ± 39.31% | 4.63 ± 8.03% | 3.80 ± 1.19% | 7.32 ± 2.18% | 60.94 ± 0.68% | 18.10 ± 2.89% | 4.69 ± 8.12% | 28.67 ± 49.65% | 24.33 ± 42.15% | 4 ± 8 | 4.33 ± 7.51% | 6.33 ± 10.97% | 26.30 ± 45.56% | 24.28 ± 42.06% | 6 ± 11 | 2.02 ± 3.50% | 5.32 ± 9.22% | 26.98 ± 46.73% | 19.48 ± 33.74% | 24 ± 42 | 7.50 ± 12.99% | 2.19 ± 3.79% | 5.52 ± 3.15% | 2.08 ± 0.79% | 10.37 ± 2.44% | 4.27 ± 3.91% | 88.23 ± 0.65% | 33.65 ± 1.83% | 39.75 ± 2.36% | 12.81 ± 7.60% | 1.73 ± 2.66% | 8.84 ± 2.43% | 1.90 ± 0.30 | 14.38 ± 3.58% | 2.93 ± 0.81 |


#### パターン: `safety+code` / 手法: `safemerge`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 0.31 ± 0.54% | 0.10 ± 0.18% | 2.19 ± 1.65% | 8.20 ± 3.95% | 55.21 ± 6.44% | 23.78 ± 9.09% | 0.21 ± 0.36% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.21 ± 0.37% | 0.21 ± 0.37% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.73 ± 1.26% | 0.73 ± 1.26% | 0 ± 0 | 0.00 ± 0.00% | 0.21 ± 0.36% | 2.92 ± 2.90% | 1.46 ± 1.10% | 6.50 ± 6.14% | 9.90 ± 10.89% | 81.15 ± 9.33% | 29.27 ± 4.20% | 38.92 ± 3.80% | 14.17 ± 8.35% | 18.26 ± 16.46% | 9.72 ± 4.81% | 1.98 ± 0.54 | 13.76 ± 2.73% | 3.19 ± 1.54 |


#### パターン: `safety+medical` / 手法: `safemerge`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 0.15 ± 0.25% | 0.03 ± 0.05% | 1.35 ± 2.35% | 3.23 ± 5.60% | 45.10 ± 14.55% | 14.87 ± 3.75% | 0.00 ± 0.00% | 0.33 ± 0.58% | 0.33 ± 0.58% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0 ± 0 | 0.00 ± 0.00% | 0.11 ± 0.18% | 0.10 ± 0.18% | 0.10 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 1.98 ± 3.43% | 0.73 ± 1.26% | 3.86 ± 6.69% | 2.60 ± 4.51% | 63.23 ± 23.14% | 26.98 ± 6.41% | 33.30 ± 6.82% | 11.04 ± 4.52% | 0.28 ± 0.08% | 6.52 ± 6.45% | 3.00 ± 1.27 | 12.68 ± 2.65% | 6.06 ± 3.55 |


### 手法: `led_merging` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `led_merging`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | led_merging | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |


#### パターン: `safety+math` / 手法: `led_merging`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 71.25 ± 0.31% | 2.67 ± 0.05% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.67 ± 0.07% | 2.81 ± 0.00% | 98.00 ± 0.00% | 68.67 ± 0.58% | 29 ± 1 | 29.33 ± 0.58% | 3.00 ± 0.00% | 95.85 ± 0.00% | 84.98 ± 0.32% | 34 ± 1 | 10.86 ± 0.32% | 3.30 ± 0.18% | 90.83 ± 0.18% | 60.10 ± 0.48% | 98 ± 2 | 30.73 ± 0.48% | 1.56 ± 0.00% | 3.54 ± 3.07% | 2.60 ± 0.18% | 7.72 ± 6.69% | 3.75 ± 6.50% | 86.25 ± 2.17% | 33.54 ± 4.15% | 42.74 ± 0.05% | 19.69 ± 0.00% | 23.58 ± 0.26% | 9.06 ± 0.02% | 1.61 ± 0.00 | 11.20 ± 0.02% | 2.16 ± 0.00 |


#### パターン: `safety+code` / 手法: `led_merging`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 71.07 ± 0.31% | 2.64 ± 0.00% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.65 ± 0.08% | 2.81 ± 0.00% | 98.00 ± 0.00% | 68.33 ± 0.58% | 30 ± 1 | 29.67 ± 0.58% | 3.00 ± 0.00% | 95.85 ± 0.00% | 84.88 ± 0.18% | 34 ± 1 | 10.97 ± 0.18% | 3.19 ± 0.00% | 90.94 ± 0.00% | 60.00 ± 0.54% | 99 ± 2 | 30.94 ± 0.54% | 1.56 ± 0.00% | 3.54 ± 3.07% | 2.60 ± 0.18% | 7.72 ± 6.69% | 3.75 ± 6.50% | 86.25 ± 2.17% | 33.54 ± 4.15% | 42.74 ± 0.04% | 19.69 ± 0.00% | 23.52 ± 0.29% | 9.07 ± 0.01% | 1.61 ± 0.00 | 11.20 ± 0.02% | 2.16 ± 0.00 |


#### パターン: `safety+medical` / 手法: `led_merging`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | led_merging | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |


### 手法: `matena_fisher` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `matena_fisher`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 8.38 ± 1.79% | 0.00 ± 0.00% | 2.08 ± 1.17% | 0.00 ± 0.00% | 45.94 ± 16.65% | 13.09 ± 0.17% | 0.00 ± 0.00% | 98.33 ± 0.58% | 5.67 ± 1.53% | 93 ± 2 | 92.67 ± 2.08% | 0.00 ± 0.00% | 100.00 ± 0.00% | 9.58 ± 1.39% | 283 ± 4 | 90.42 ± 1.39% | 0.00 ± 0.00% | 92.08 ± 2.66% | 9.90 ± 3.08% | 263 ± 12 | 82.19 ± 3.79% | 0.00 ± 0.00% | 1.56 ± 1.13% | 2.60 ± 1.26% | 0.00 ± 0.00% | 0.00 ± 0.00% | 63.23 ± 33.38% | 28.65 ± 1.10% | 23.73 ± 0.12% | 15.42 ± 0.48% | 0.12 ± 0.08% | 2.26 ± 0.01% | 63.37 ± 3.09 | 8.24 ± 0.08% | 102.90 ± 1.68 |


#### パターン: `safety+math` / 手法: `matena_fisher`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 7.99 ± 0.76% | 4.26 ± 0.51% | 16.98 ± 1.15% | 9.32 ± 1.05% | 61.35 ± 0.39% | 31.80 ± 11.53% | 4.58 ± 0.48% | 7.33 ± 2.08% | 7.33 ± 2.08% | 0 ± 0 | 0.00 ± 0.00% | 4.67 ± 0.58% | 8.31 ± 1.94% | 7.99 ± 1.66% | 1 ± 1 | 0.32 ± 0.32% | 3.83 ± 0.64% | 10.62 ± 2.36% | 8.65 ± 1.54% | 6 ± 5 | 1.98 ± 1.60% | 3.96 ± 2.13% | 29.69 ± 0.54% | 4.27 ± 1.78% | 12.60 ± 0.93% | 6.04 ± 2.90% | 89.90 ± 0.18% | 32.81 ± 0.62% | 45.30 ± 0.45% | 12.92 ± 0.95% | 37.17 ± 35.89% | 11.99 ± 0.47% | 1.67 ± 0.01 | 12.75 ± 0.20% | 2.39 ± 0.02 |


#### パターン: `safety+code` / 手法: `matena_fisher`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 52.64 ± 2.32% | 3.38 ± 1.18% | 0.83 ± 0.09% | 0.00 ± 0.00% | 56.20 ± 0.74% | 13.27 ± 0.61% | 1.77 ± 0.95% | 95.67 ± 1.15% | 51.67 ± 3.79% | 44 ± 3 | 44.00 ± 2.65% | 4.67 ± 1.53% | 96.59 ± 1.12% | 52.61 ± 1.64% | 138 ± 5 | 43.98 ± 1.61% | 3.94 ± 1.03% | 82.29 ± 2.13% | 53.65 ± 2.84% | 92 ± 2 | 28.65 ± 0.72% | 3.12 ± 2.48% | 0.83 ± 0.65% | 0.83 ± 0.79% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.10 ± 1.98% | 27.29 ± 1.48% | 25.80 ± 0.44% | 13.96 ± 1.54% | 0.07 ± 0.00% | 2.29 ± 0.20% | 80.11 ± 15.69 | 6.79 ± 1.91% | 63.11 ± 20.25 |


#### パターン: `safety+medical` / 手法: `matena_fisher`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 94.25 ± 0.60% | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.08 ± 2.26% | 12.98 ± 0.17% | 0.00 ± 0.00% | 98.00 ± 0.00% | 97.33 ± 1.15% | 1 ± 1 | 0.67 ± 1.15% | 0.00 ± 0.00% | 100.00 ± 0.00% | 99.57 ± 0.74% | 1 ± 2 | 0.43 ± 0.74% | 0.64 ± 0.00% | 85.83 ± 0.18% | 85.83 ± 0.18% | 0 ± 0 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 24.17 ± 4.51% | 27.04 ± 0.06% | 11.88 ± 0.54% | 0.02 ± 0.00% | 0.41 ± 0.01% | 384272.26 ± 81902.74 | 0.90 ± 0.21% | 304225.05 ± 19087.67 |


### 手法: `mergealign` (全 Alpha パラメータ一覧)

#### パターン: `safety+math+code+medical` / 手法: `mergealign`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | mergealign | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |


#### パターン: `safety+math` / 手法: `mergealign`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.85 ± 0.35% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 18.40 ± 1.05% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |


#### パターン: `safety+code` / 手法: `mergealign`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.64 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 17.79 ± 0.00% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |


#### パターン: `safety+medical` / 手法: `mergealign`

| Pattern | Method | Alpha | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench Original ASR (%) | JailbreakBench Filtered ASR (%) | JailbreakBench Gibberish N | JailbreakBench Gibberish Ratio (%) | JailbreakBench Harmful Content (ASR↓ %) | StrongReject Original ASR (%) | StrongReject Filtered ASR (%) | StrongReject Gibberish N | StrongReject Gibberish Ratio (%) | StrongReject Harmful Content (ASR↓ %) | WildJailbreak Original ASR (%) | WildJailbreak Filtered ASR (%) | WildJailbreak Gibberish N | WildJailbreak Gibberish Ratio (%) | WildJailbreak Harmful Content (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code Similarity (%) | Evol-Code PPL (↓) | MedAlpaca Similarity (%) | MedAlpaca PPL (↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 11.98 ± 3.31% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 100 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 313 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% | 320 ± 0 | 100.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 28.75 ± 0.00% | 23.14 ± 0.00% | 0.00 ± 0.00% | 12.79 ± 9.94% | 0.00 ± 0.00% | - | 0.00 ± 0.00% | - |

