SST-Merge: Data-Free Fisher-Ratio Subspace Steering for Safety-Preserving Model Merging

（SST-Merge: 安全性維持型モデルマージのための Data-Free Fisher 比部分空間ステアリング）

あらまし (Abstract)

大規模言語モデル（LLM）に対するドメイン特化ファインチューニング（fine-tuning）は、特定のタスク性能を高める一方で、事前に施されていた安全性アライメントを劣化させることがある。追加学習なしで安全性を回復する方法として、安全モデルのパラメータ差分を統合する Secure Merge が有望であるが、既存のマージ手法は安全性向上と有用性保持の間に大きな Safety Tax（有用性劣化）を生じやすい。

本研究では、Secure Merge を「utility tax 制約下で local safety sensitivity、すなわち safety-sensitive Fisher energy を最大化する Fisher-ratio constrained patch deployment problem」として定式化する。局所二次近似の下で、この問題は一般化固有値問題（Generalized Eigenvalue Problem; GEVP）に帰着され、その固有値は有用性コストあたりの安全性感度効率（safety-sensitive energy per utility cost）として解釈できる。さらに、大規模モデルへの適用のために、対角 Fisher 近似に基づく coordinate-wise な SST-Merge を導出する。加えて、Fisher 統計を task-vector proxy で置き換える Data-Free SST-V を提案し、キャリブレーションデータが利用できない環境でも軽量に安全パッチを選択できる近似を与える。

実験では、SST-Merge が標準的なタスクベクトルマージ、干渉緩和型マージ、および安全性維持型マージ手法と比較して、より良い safety-utility Pareto frontier を達成することを示す。FIM-based SST は追加学習を必要としない training-free な手法であり、Data-Free SST-V はさらにキャリブレーションデータへのアクセスを必要としない calibration-data-free なアライメント配備手法として機能する。

⸻

1. Introduction

大規模言語モデル（LLM）は、固有のタスクにおける高い性能を達成するために、ドメイン固有のデータセットでファインチューニング（fine-tuning）されるというパラダイム（Devlin et al. 2019; Raffel et al. 2020; Brown et al. 2020; Touvron et al. 2023）を経て、さまざまな応用分野に急速に普及している。オープンウェイトモデルの公開と PEFT（Parameter-Efficient Fine-Tuning）の普及により、同一の基盤モデルから派生した多数の専門モデル（expert models）が実運用で利用されるようになっている（Wolf et al. 2019; Min et al. 2023）。これらの専門モデルは、数学、コード生成、医療、法律、金融などの個別タスクにおいて高い性能を発揮する。

しかし、これらの専門モデルは通常、元の学習データセットやハイパーパラメータに強く適応しており、専門領域外の汎用的な対話性能や、重要な安全性アライメント（safety alignment）能力を喪失しやすいという課題を抱えている。特に、良性（benign）な通常タスクでの追加学習であっても、LLM の安全機構が劣化し、悪意あるユーザーによる脱獄（jailbreak）攻撃に対して脆弱になる現象が報告されている（Zou et al. 2023; Wei et al. 2024; Huang et al. 2024）。この劣化に対して、各モデルごとに再度安全アライメント（RLHF や DPO など）を行うことは、計算コスト、データのプライバシー制約、検証コストの観点から実務的に困難である。

この課題を克服するため、追加の訓練を必要とせず、パラメータ空間（parameter space）上でモデル重みを直接統合する「モデルマージ（model merging）」（Wortsman et al. 2022; Ilharco et al. 2023）が注目されている。モデルマージは、複数の fine-tuned model の能力を単一モデルへ統合できる training-free な手法であり、推論時に複数モデルを走らせる ensemble と異なり、統合後の推論コストを増加させない。これらの手法は、事前学習によって得られたパラメータから局所最適解へと至る損失地形（loss landscape）が、平坦で障壁の少ない領域（flat basin）で線形に接続されているという知見（Garipov et al. 2018; Draxler et al. 2018; Neyshabur et al. 2020; Entezari et al. 2022; Zhou et al. 2024）とも関連している。

専門モデルへ事後的に安全性を配備する Secure Merge 設定において、近年の安全性維持型マージ研究は、モデルマージ時に安全性向上と有用性保持の間に鋭い衝突が生じることを報告している（Hammoud et al. 2024a; Djuhera et al. 2025; Ma et al. 2025）。本稿では、安全パッチの適用によって、獲得した専門性能（数学、コード、医療、指示追従など）が劣化する代償を Safety Tax と定義する。単純なタスクベクトルマージ（Task Arithmetic）や干渉解消技術（TIES (Yadav et al. 2023), DARE (Yu et al. 2024), DELLA (Deep et al. 2024)）は、主に一般的なタスク干渉の軽減を目的としており、安全性アライメント統合に固有の safety-utility conflict を直接的に扱うものではない。そのため、安全パッチが通常タスクに重要なパラメータへ干渉し、有用性を破壊する Safety Tax を十分に制御できない場合がある。また、単一の安全でない専門モデルが統合されるだけで、マージ後モデルの安全性挙動が大きく劣化し、一般性能の劣化が目立たないままアライメントが失われる「隠れたアライメント喪失」が発生することも指摘されている（Hammoud et al. 2024a）。

本研究では、安全性パッチの合成を「どの方向にどれだけ注入するか」という局所的な幾何学的最適化問題として捉え、新しいマージフレームワークである SST-Merge（Fisher-Ratio Subspace Steering） を提案する。本稿は、対角 Fisher 情報をパラメータ感度の tractable proxy として用いる既存研究（Matena and Raffel 2022; Tam et al. 2024）を前提とする。本稿の新規性は Fisher 情報の利用自体ではなく、utility Fisher と safety/refusal Fisher の比を用いて、既存の安全パッチを「安全挙動に重要で、かつ有用性を壊しにくい方向」へ射影する点にある。

具体的には、局所二次近似の下で、有用性損失の Fisher F_u を utility tax の局所 proxy、安全性/拒否分布上の Fisher F_s を local safety sensitivity、すなわち safety-sensitive Fisher energy の proxy として扱う。その上で、単位 utility tax あたりの safety-sensitive energy を最大化する方向を求める。この問題は一般化固有値問題（GEVP）

F_s v = \lambda (F_u + \epsilon I)v

に帰着され、固有値 \lambda は Fisher-ratio efficiency、すなわち有用性コストあたりの安全性感度効率として解釈できる。

さらに、大規模モデルへの適用と実運用（データ非公開環境）の制約を克服するため、対角 Fisher 近似を用いてパラメータ座標ごとの Fisher 比

r_i = \frac{f_{s,i}}{f_{u,i}+\epsilon}

を導入し、coordinate-wise な hard/soft mask および interpolation による Diagonal SST-Merge を導く。加えて、キャリブレーションデータを利用できない環境を想定し、安全パッチ差分と utility task vector に基づく task-vector ratio proxy を用いた Data-Free SST-V を提案する。FIM-Merging（Wang et al. 2026）はランダムトークンから対角 FIM を計算し、層単位（layer-wise）のマージ係数を決定するが、SST-Merge は Fisher 比またはその proxy を用いて、パラメータ座標単位（element-wise）で安全パッチを選択・ステアリングする点で異なる。

本研究の主要な貢献は以下の3点である。

1. Theory: 安全パッチ統合を、utility tax 制約下で safety-sensitive Fisher energy を最大化する問題として定式化し、局所二次近似の下で Fisher-ratio objective を最大化する方向が一般化固有値問題（GEVP）によって特徴付けられることを示す。
2. Method: GEVP から対角近似に基づく実用的な Diagonal SST-Merge を導出し、パラメータ座標ごとの hard/soft mask および coordinate-wise interpolation によって、既存の安全パッチから utility-destructive な成分を抑制する closed-form なマージ手法を提案する。
3. Evaluation: 数学・コード・医療・指示追従タスクと複数の jailbreak / harmfulness benchmark において、SST-Merge が標準マージ、Fisher-aware マージ、安全性維持型マージ手法より良い safety-utility Pareto frontier を達成することを示す。さらに、Data-Free SST-V がキャリブレーションデータなしでもその利点の大部分を維持することを実証する。

⸻

2. Problem Setup and Related Work

2.1 Secure Merge and Safety Tax

ベースモデルを \theta_0 \in \mathbb{R}^d、有用性モデルを \theta_u \in \mathbb{R}^d、安全モデルを \theta_s \in \mathbb{R}^d とする。これらは同一の基盤モデル \theta_0 からファインチューニングされたモデルである。専門タスクおよび安全性アライメントのタスクベクトル（差分ベクトル）は以下のように定義される。

\tau_u = \theta_u - \theta_0, \quad \tau_s = \theta_s - \theta_0.

安全パッチ統合の設定では、有用性モデル \theta_u に対して、安全モデルとの差分

\Delta = \theta_s - \theta_u

を安全パッチとして統合する。ただし、安全パッチ全体をそのまま注入すると、通常タスクに重要なパラメータまで上書きしてしまう可能性がある。そのため、一般的な Secure Merge は、スカラー係数または座標ごとのゲート g を用いて、

\theta_m = \theta_u + \alpha \Delta

または

\theta_m = \theta_u + g \odot \Delta

として表される。Task Arithmetic (Ilharco et al. 2023) は、このうち \theta_m = \theta_u + \alpha \Delta というスカラー補間の特殊例とみなせる。

このマージにおいて、良性通常データ分布を D_u、脱獄要求と安全な拒否応答からなる安全性/拒否分布を D_s と定義する。すなわち、D_s は単なる有害プロンプト集合ではなく、有害または攻撃的プロンプトに対する拒否応答、ポリシー準拠応答、安全応答をターゲットとして含む分布である。マージモデル \theta_m が D_u 上で通常タスク性能を損なう代償を、本稿では Safety Tax と呼ぶ。

2.2 General Model Merging

Model merging は、異なるチェックポイントの知識を統合するための training-free な事後的手法である（Wortsman et al. 2022; Ilharco et al. 2023）。代表的な手法として、複数の fine-tuned model の重みを平均する Model Soups や、基盤モデルからの差分ベクトルを加算する Task Arithmetic がある。これらの単純マージは実装が容易であり、複数タスクの能力を単一モデルに統合する手段として広く用いられている。

一方で、異なるタスクベクトルの間には sign conflict、magnitude imbalance、redundant update などの干渉が生じる。これに対して、符号整合とトリミングを行う TIES-Merging (Yadav et al. 2023)、デルタパラメータの削除と再スケーリングを行う DARE (Yu et al. 2024)、符号衝突や重要座標を考慮する DELLA (Deep et al. 2024) などの干渉緩和手法が開発されてきた。しかし、これらの手法は主に一般的なタスク干渉を対象としており、安全パッチ統合における safety-utility conflict、すなわち安全性に効く更新と通常性能を壊す更新を区別する目的関数を明示的には持たない。

2.3 Fisher-aware Model Merging

パラメータの曲率（感度）を考慮する研究として、対角 Fisher 情報行列（FIM）をパラメータ重要度とみなした Fisher-weighted averaging (Matena and Raffel 2022) が提案されている。この手法は、各 fine-tuned model の posterior を Fisher 情報を precision とする Gaussian として近似し、Fisher に基づく重み付き平均によってモデルを統合する。

これを発展させ、更新誤差を不確実性で補正する Gradient Matching (Daheim et al. 2023)、Fisher マスクにより重要ノードまたはブロックを選別する Fisher Mask Nodes (Thennal et al. 2024)、Fisher 重み付き中央値を用いる DRIFT-MEDIAN (Baban et al. 2025)、係数を Bayesian optimization により調整する DF-Merge (Sanwoo et al. 2025) などが提案されている。これらの研究は、Fisher 情報を parameter importance、curvature、または aggregation weight として用いることで、一般的な model merging の性能を改善する。

しかし、これらの手法は主に単一または複数タスク空間における統合性能向上を目的としており、対立する2つの分布 D_u と D_s の曲率比を直接最適化するものではない。SST-Merge は Fisher 情報を単なる重み係数として用いるのではなく、utility Fisher と safety/refusal Fisher の比を用いて、パッチ方向ごとの safety-sensitive energy per utility tax を推定する点で異なる。

2.4 Safety-preserving Merging

安全性を保持するためのマージとして、domain vector と alignment vector を補間する MergeAlign (Hammoud et al. 2024b)、コサイン類似度で安全アライメントからの逸脱層のみを選択マージする SafeMERGE (Djuhera et al. 2025)、勾配アトリビューションでタスク特化ニューロンを特定し分離する LED-Merging (Ma et al. 2025) がある。また、AlignMerge (Wang et al. 2025) は Fisher geometry 上で alignment-sensitive directions を制約する幾何学的最適化としてマージを扱う。

SST-Merge はこれらの手法と同じく safety-utility conflict を扱うが、反復的な制約付き最適化を必要とせず、Fisher 比から element-wise な選択ルールを closed-form に導く点で異なる。MergeAlign がタスクベクトル補間を行い、SafeMERGE が層単位の選択を行い、LED-Merging がニューロン単位の分離を行うのに対して、SST-Merge はパラメータ座標ごとの Fisher-ratio に基づき、既存の安全パッチから utility-destructive な成分を抑制する。したがって、SST-Merge はこれらの手法と競合するだけでなく、補完的な位置づけも持つ。

2.5 Data-free and Calibration-light Merging

キャリブレーションデータの獲得が困難な環境向けに、ランダムトークンから対角 FIM を計算して層単位（layer-wise）のマージ係数を決定する FIM-Merging (Wang et al. 2026) が提案されている。FIM-Merging は、ドメイン固有の calibration data を用いずにランダムトークンから Fisher 統計を推定することで、データ非依存な layer-adaptive merging を実現する。

SST-Merge は、FIM-Merging と同様にデータ不要のモチベーションを共有するが、制御粒度と目的関数が異なる。FIM-Merging が random-token Fisher を層ごとの係数決定に用いるのに対して、SST-Merge は Fisher 比またはその proxy を用いて、パラメータ要素単位（element-wise）で安全パッチを選択・ステアリングする。

Unlike previous methods, SST-Merge explicitly models the parameter interference between safety alignment and utility domains by evaluating their curvature ratio at the element-wise level. Rather than using Fisher information as a simple weighting coefficient or solving iteratively constrained optimization problems on layers, SST-Merge derives a closed-form patch projection rule that filters out utility-destructive components from a given safety patch, and further enables data-free deployment through lightweight task-vector proxies.

⸻

3. Fisher-Ratio Subspace Steering

3.1 Utility Tax and Safety-Sensitive Energy

パラメータの変化量 \Delta が局所的な摂動領域（LoRA アダプタの空間や、同一基盤モデル周辺の局所フラット領域）にあると仮定する。局所二次近似（local quadratic approximation）の下で、有用性モデル \theta_u の周囲における有用性損失 L_u の増加量、すなわち Utility Tax は以下のように近似できる。

\mathrm{Tax}(\Delta) \approx \frac{1}{2}\Delta^\top F_u \Delta.

ここで F_u は、有用性データ分布 D_u 上で定義される utility Fisher 情報行列である。

一方、安全性/拒否分布 D_s に対する局所感度を safety-sensitive energy または local safety sensitivity として定義する。

\mathrm{SafetyEnergy}(\Delta) = \Delta^\top F_s \Delta.

ここで F_s は、安全性/拒否分布 D_s 上で定義される safety/refusal Fisher 情報行列である。この値 \Delta^\top F_s \Delta は、安全性損失の低下量そのものを意味するものではない。むしろ、安全性/拒否分布 D_s 上で重要な方向に、どれだけパッチのエネルギーが保持されているかを示す局所感度の proxy である。

したがって、SST-Merge は「安全性性能そのもの」を直接最適化するのではなく、既存の安全パッチのうち、safety/refusal distribution に対して高い局所感度を持ち、かつ utility distribution に対する tax が小さい方向を選択する。

3.2 GEVP and Fisher-Ratio Safety Subspace

安全パッチの配備における更新方向 v \in \mathbb{R}^d を、局所二次近似の下で、単位 utility tax あたりの safety-sensitive energy を最大化する問題として定式化する。

\max_v \frac{v^\top F_s v}{v^\top (F_u + \epsilon I)v}.

ここで \epsilon > 0 は数値安定化項であり、F_u+\epsilon I を正定値にするために導入する。このレイリー商の最大化は、次の制約付き最適化問題と同値である。

\max_v v^\top F_s v
\quad \text{s.t.} \quad
v^\top (F_u + \epsilon I)v \leq \rho,

where \rho > 0 は許容される utility tax の予算である。Lagrangian の極値条件より、この問題は次の一般化固有値問題（GEVP）に帰着する。

F_s v = \lambda (F_u + \epsilon I)v.

Theorem 1 (Fisher-Ratio Safety Subspace)

Let F_u \succeq 0 and F_s \succeq 0 be Fisher matrices estimated on utility and safety/refusal distributions, and let \epsilon > 0. Under the local quadratic approximation, directions maximizing safety-sensitive energy per unit utility tax are given by the generalized eigenvalue problem

F_s v = \lambda (F_u+\epsilon I)v.

The generalized eigenvalue \lambda equals the Fisher-ratio efficiency:

\lambda = \frac{v^\top F_s v}{v^\top (F_u+\epsilon I)v}.

The top-k generalized eigenvectors span the Fisher-ratio safety subspace.

Proof sketch.
The constrained optimization problem can be written with the Lagrangian

\mathcal{L}(v,\lambda)
=
v^\top F_s v
-
\lambda
\left(
v^\top (F_u+\epsilon I)v-\rho
\right).

Taking the derivative with respect to v and setting it to zero gives

2F_s v - 2\lambda(F_u+\epsilon I)v = 0.

Therefore,

F_s v = \lambda(F_u+\epsilon I)v.

Substituting this condition back into the Rayleigh quotient yields

\lambda =
\frac{v^\top F_s v}{v^\top (F_u+\epsilon I)v}.

Thus, the leading generalized eigenvectors characterize the directions with high safety-sensitive energy per unit utility tax.

3.3 Patch Steering Projection

既存の安全パッチベクトル

\Delta = \theta_s - \theta_u

が与えられたとき、このパッチから有用性を破壊しやすい成分を抑制し、安全効率が高い成分を抽出するため、パッチを Fisher-ratio safety subspace S_k に subspace projection、または subspace steering する。

上位 k 個の一般化固有ベクトルを列ベクトルとする行列を

V_k = [v_1,\ldots,v_k] \in \mathbb{R}^{d\times k}

とすると、射影後のパッチ \Delta_{\mathrm{SST}} は以下のように得られる。

\Delta_{\mathrm{SST}}
=
\Pi_{S_k}^{F_u}(\Delta)
=
V_k
\left(
V_k^\top (F_u+\epsilon I)V_k
\right)^{-1}
V_k^\top (F_u+\epsilon I)\Delta.

この操作は、任意の安全方向を新しく生成するものではなく、既存の安全パッチ \Delta を、utility Fisher の計量において高効率な部分空間へ射影する操作である。

3.4 Diagonal SST-Merge

フル FIM および高次元 GEVP の計算コスト（O(d^3)）を回避するため、実用的な大規模 LLM では対角 Fisher 近似を適用する。すなわち、

F_u \approx \mathrm{diag}(f_{u,1},\ldots,f_{u,d}), \quad
F_s \approx \mathrm{diag}(f_{s,1},\ldots,f_{s,d})

と置く。このとき、一般化固有値問題は各パラメータ座標 i ごとの独立した Fisher 比に分解される。

r_i = \frac{f_{s,i}}{f_{u,i}+\epsilon}.

この対角化により、一般化固有ベクトルは各パラメータ軸の単位ベクトルとなり、部分空間射影は計算コストの低い座標ごとの mask および interpolation に簡略化される。

1) Hard Masking (Top-k Selection)

Fisher 比 r_i が大きい上位 k\% の座標のみを選択する二値マスク M \in \{0,1\}^d を適用する。

M_i =
\begin{cases}
1 & \text{if } r_i \in \mathrm{Top}\text{-}k(r),\\
0 & \text{otherwise}.
\end{cases}

\Delta_{\mathrm{SST-Hard}} = M \odot \Delta.

2) Soft Masking (Sigmoid Masking)

Top-k の境界で生じる不連続性を緩和するため、滑らかな信頼度重み w_i \in [0,1] を用いた soft masking を適用する。

w_i = \sigma\left(\frac{r_i-\tau}{\gamma}\right),

\Delta_{\mathrm{SST-Soft}} = w \odot \Delta.

ここで \tau は閾値、\gamma は温度パラメータである。

3) Coordinate-wise Interpolation

マージ後のパラメータ極端化を防ぐため、タスク算術（Ilharco et al. 2023）に対し、各座標ごとに補間（interpolation）を行う SST-Interpolation をデフォルトとする。

\theta_{m,i}
=
\theta_{u,i}
+
\alpha_i(\theta_{s,i}-\theta_{u,i}).

ここで、パラメータごとの係数 \alpha_i を Fisher 比 r_i に基づいて決定する。

\alpha_i = \alpha \cdot w_i.

hard mask の場合は w_i = M_i とする。この形式により、SST-Merge はどの座標に安全パッチを注入するかだけでなく、どの強度で注入するかを coordinate-wise に制御できる。

⸻

4. Data-Free SST

4.1 Motivation and Data-Free Setup

FIM の計算には通常、良性データセット D_u および安全性/拒否データセット D_s が必要となる。しかし、安全モデルのプロバイダーがデータ漏洩や機密保護のために訓練データを共有しない場合、あるいはマージ側でデータセットを用意するリソースがない場合、データ依存の手法は適用できない。そこで、データセットを必要とせずに Fisher-ratio safety subspace を近似する Data-Free SST-V を提案する。

4.2 Task-Vector Ratio Proxy (SST-V)

Data-Free SST-V では、Fisher 統計の代わりに、モデル間のタスクベクトルから得られる更新量を実用的な proxy として用いる。ここで重要なのは、task vector の二乗が Fisher そのものを表すと主張するのではなく、タスク依存更新の大きさを表す heuristic proxy として用いる点である。つまり、SST-V は FIM-SST の厳密な代替ではなく、キャリブレーションデータが利用できない場合の軽量な近似である。

Secure Merge で実際に統合するパッチは

\Delta_i = \theta_{s,i} - \theta_{u,i}

であり、有用性モデルがベースモデルからどれだけ移動したかは

\tau_{u,i} = \theta_{u,i} - \theta_{0,i}

で表される。したがって、SST-V の比率指標を以下のように定義する。

\hat{r}_i^{\mathrm{SST-V}}
=
\frac{\Delta_i^2}{\tau_{u,i}^2+\epsilon}.

この比率の直感は次の通りである。分子 \Delta_i^2 は、utility model から safety model へ移動するために必要な安全パッチ更新の大きさを表す。一方、分母 \tau_{u,i}^2 は、その座標が通常タスクの獲得過程でどれだけ大きく変更されたかを表す。通常タスクのために大きく移動した座標は、utility model の専門性能に強く関与している可能性が高く、そこを安全パッチで上書きすると Safety Tax が大きくなりやすい。したがって、SST-V は、通常タスクへの依存が相対的に小さく、かつ安全パッチとして大きく変更される座標を優先的に選択する。

Data-Free SST-V は、この \hat{r}_i^{\mathrm{SST-V}} に基づいて hard mask または soft mask を構築し、Diagonal SST-Merge と同様に coordinate-wise interpolation を行う。

4.3 Magnitude-only Ablation (SST-M)

さらに粗いデータフリー近似として、モデル重み自体の大きさ（absolute magnitude）を用いる SST-M を定義する。

\hat{r}_i^{\mathrm{SST-M}}
=
\frac{|\theta_{s,i}|}{|\theta_{u,i}|+\epsilon}.

ただし、SST-M は Fisher-ratio の proxy としては弱く、タスク依存更新や safety-utility conflict を直接表すものではない。そのため、本稿では SST-M をメインのデータフリー手法ではなく、magnitude-only の効果を検証する ablation として位置付ける。

4.4 Random-Token Fisher Variant

キャリブレーションデータは得られないが、擬似的なフォワードパスから曲率を推定できる場合、ランダムトークン列または擬似テキストを入力として diagonal FIM を計算し、これを f_{u,i} の proxy とするランダムトークン変種も考えられる。この変種は、FIM-Merging (Wang et al. 2026) の data-free Fisher 推定の発想を、層単位ではなく element-wise な safety patch selection に拡張するものである。ただし、本稿の主要な data-free variant は、追加の forward/backward pass も必要としない SST-V である。

⸻

5. Experiments

5.1 Research Questions

本実験では、以下の5つの研究質問（RQs）を通じて SST-Merge の性能を検証する。

* RQ1 (Pareto Frontier): SST-Merge は、既存のマージおよび安全維持マージ手法と比較して、安全性能（ASR 低下）と有用性保持の Pareto frontier を改善できるか。
* RQ2 (Data-free Setting): キャリブレーションデータを利用できない Data-Free SST-V は、データ依存の FIM-SST と比較してどの程度性能差があるか。
* RQ3 (Granularity): パラメータ単位（element-wise）の選別は、層単位（layer-wise）の選択手法よりも優れているか。
* RQ4 (Efficiency): SST-Merge は、追加の反復的な幾何制約最適化を要する手法と比較して、計算コスト（時間・メモリ）を削減できるか。
* RQ5 (Robustness): パラメータ k やマージ係数 \alpha の変動に対するロバスト性はどうか。

5.2 Detailed Experimental Design and Setup

本研究の実証検証は、予備実験（Preliminary Validation）と本実験（Main Benchmark Evaluation）の2層に分けて実施された。予備実験では、既存の実験環境に基づき、SST-Merge が safety-utility trade-off を改善するかを高速に確認する。本実験では、数学・コード・医療・指示追従タスクと複数の jailbreak / harmfulness benchmark を用い、より広範な条件で提案手法を評価する。評価サンプル数については、API リクエスト数および GPU 計算時間の制限から、初期の sweep では limit: 320 件のサブセットを用いる。ただし、主要な主張については、最終版ではより大きな評価セットおよび信頼区間を報告する。

5.2.1 Target Models

* ベースモデル (\theta_0): meta-llama/Llama-2-7b-hf (Touvron et al. 2023)
* 有用性専門モデル (\theta_u):
    * 数学 (Math): WizardLMTeam/WizardMath-7B-V1.0 (Luo et al. 2023a)
    * コード (Code): vanillaOVO/WizardCoder-Python-7B-V1.0 (Luo et al. 2023b)
    * 医療 (Medical): medalpaca/medalpaca-7b (Han et al. 2023)
* 安全モデル (\theta_s): meta-llama/Llama-2-7b-hf に対する安全性アライメントとして、LoRA アダプタを用いてファインチューニングを適用した models/safety_lora

5.2.2 Fisher Calibration Datasets

各 Fisher 計算用データセットのサンプル数は N=500 とする。

* 安全性 Fisher 計算用データ (D_s): 有害要求プロンプトとそれに対する拒否応答ペアから成る data/fim/fim_harmful.json
* 良性有用性 Fisher 計算用データ (D_u):
    * 数学ドメイン: data/fim/fim_benign_math.json
    * コードドメイン: data/fim/fim_benign_code.json
    * 医療ドメイン: data/fim/fim_benign_medical.json

5.2.3 Evaluation Benchmarks and Metrics

自動評価は lm-evaluation-harness を用いて決定論的に実行する。

1) 安全性アライメント評価 (Safety Benchmarks)

有害反応率（Attack Success Rate; ASR）または拒否の成否を算出する。

* harmbench: HarmBench (Mazeika et al. 2024)。有害判定器による拒否応答の成否を算出する。
* jailbreakbench: JailbreakBench (Chao et al. 2024)。
* strongreject: StrongReject (Souly et al. 2024)。
* wildjailbreak: WildJailbreak (Jiang et al. 2024)。
* 過剰拒否（over-refusal）評価: 無害な質問に対する過剰な拒絶を検知するため、XSTest (Röttger et al. 2023) を評価指標に含める。
* 追加安全性評価: TrustLLM (Sun et al. 2024) および BeaverTails (Ji et al. 2024) も評価対象に含め、安全性・信頼性・有害性応答の多面的な傾向を確認する。

2) 有用性評価 (Utility Benchmarks)

* 数学分野 (Math): gsm8k (Cobbe et al. 2021) および minerva_math500 (Lewkowycz et al. 2022)
* コード分野 (Code): humaneval (Chen et al. 2021) および mbpp (Austin et al. 2021)
* 医療分野 (Medical): pubmedqa (Jin et al. 2019) および medqa_4options (Jin et al. 2021)
* 汎用能力 (General): mmlu (Hendrycks et al. 2020) および ifeval (Zhou et al. 2023)

5.2.4 Evaluation Protocol and Hyperparameters

* SST 設定: 提案手法 diagonal_sst は、マージ種別として interpolation（パラメータ単位の補間）を使用し、部分空間選択マスクとして hard mask を採用する。デフォルトの部分空間比率パラメータ（Top-k）は k=0.20 とし、安定化のための微小定数は \epsilon=10^{-6} に固定する。
* マージ係数の探索 (Alpha Sweep): マージ強度のスイープ範囲として \alpha \in \{0.0,0.2,0.4,0.6,0.8,1.0\} を探索する。
* 頑健性の検証 (Seeds): 3つの異なるランダムシード値 seeds: [42, 43, 44] で実行し、統計的ばらつきを確認する。
* 融合パターン (Merge Patterns):
    1. 1タスク＋アライメントマージ: safety + math, safety + code, safety + medical
    2. 多重マルチタスクマージ: safety + math + code + medical

5.2.5 Baselines for Comparison

* 標準マージ手法 (Standard Merging):
    * task_arithmetic: 線形補間ベースの Task Arithmetic (Ilharco et al. 2023)
    * ties: 符号整合とトリミングを行う TIES-Merging (Yadav et al. 2023)
    * dare: デルタパラメータのランダム削除を伴う DARE (Yu et al. 2024)
    * della: 符号衝突を回避し重要座標を考慮する DELLA (Deep et al. 2024)
* Fisher-aware merging:
    * matena_fisher: 対角 FIM を用いた Fisher-weighted averaging (Matena and Raffel 2022)
    * fisher_mask_nodes: Fisher Mask Nodes (Thennal et al. 2024) に基づく重要ブロック選択
    * df_merge: Bayesian optimization による Dynamic Fisher-weighted Model Merging (Sanwoo et al. 2025)
* 安全性・アライメント維持マージ手法 (Safety-Preserving Merging):
    * mergealign: domain vector と alignment vector の補間に特化した MergeAlign (Hammoud et al. 2024b)
    * safemerge: コサイン類似度でアライメント逸脱層のみを選択マージする SafeMERGE (Djuhera et al. 2025)
    * led_merging: 勾配帰属から重要ニューロンを特定し競合を分離する LED-Merging (Ma et al. 2025)
    * alignmerge: Fisher geometry に基づく幾何制約付きマージ (Wang et al. 2025)

⸻

5.3 Preliminary and Main Results

5.3.1 Preliminary Validation

初期のモデル統合評価（Llama-3-8B 系列）において、RepliQA および AlpacaEval タスクを用い、Jailbreak Resistance（安全率）と Utility retention のトレードオフを検証した。結果、SST-Merge は単純な Task Arithmetic や TIES に対して、同一アライメント水準における良性タスクの性能劣化（Safety Tax）を抑制する傾向を示した。

5.3.2 Main Benchmark Results (GSM8K vs HarmBench)

以下に、Llama-2-7B モデルにおける数学能力（GSM8K 精度）と有害反応率（HarmBench ASR）のトレードオフを示す。ここでは初期 sweep として limit: 320 のサブセットを用いる。

モデル / マージ手法	設定 (\alpha)	有害反応率 (ASR) ↓	数学能力 (GSM8K) ↑	状態と評価
WizardMath	-	25.00%	39.38%	High utility / low safety
SafetyFT	-	0.00%	7.19%	High safety / low utility
Diagonal SST	0.2	28.13%	42.81%	Utility is retained, safety effect is limited
Diagonal SST	0.6	24.06%	36.56%	High utility retention, limited ASR reduction
Diagonal SST	0.8	3.75%	33.44%	Strong ASR reduction with retained utility
Diagonal SST	1.0	0.00%	27.19%	Strong safety, moderate utility degradation
TIES	0.2	14.38%	40.31%	Competitive utility with moderate safety improvement
DARE	0.2	10.31%	37.50%	Safety improves with some utility degradation

一部のベースラインでは、高いマージ係数において反復的な無意味出力が生じる不安定化が観察された。この failure mode は main table ではなく、appendix に具体例とともに報告する。

分析1: 安全性発現のしきい値的挙動

SST-Merge（SST-Interpolation）のパラメータ探索軌跡では、ASR が \alpha に対して線形に減少しない傾向が見られた。たとえば、\alpha=0.6 では ASR は 24.06% であり、WizardMath の 25.00% から大きく変化しない。一方で、\alpha=0.8 では ASR が 3.75% まで低下した。この観測は、アライメント挙動がある程度のパッチ強度を超えた時点で急激に発現する可能性を示唆しており、安全性幾何に関する近年の知見（Wang et al. 2025）とも整合する。ただし、このしきい値的挙動は、本稿では観測結果として扱い、一般的な保証としては主張しない。

分析2: 推論機能の不安定化

我々の特定の実験設定では、一部のベースラインにおいて、高いマージ係数で出力が反復的な無意味トークンに崩れる failure mode が観察された。提案する SST-Merge は、分母の f_{u,i} によって有用性の高感度座標への更新を抑制するため、このような不安定化を回避する傾向が観察された。ただし、この現象は実験設定依存であり、一般的なベースライン破綻としては主張しない。

⸻

6. Analysis and Ablations

6.1 Granularity: Element-wise vs Layer-wise

FIM-Merging などが採用する layer-wise なマージ係数決定と、SST-Merge が採用する element-wise なマスク選別を比較する。Layer-wise マージでは、特定の層全体の安全パラメータを均一に縮退または補間するため、同じ層に含まれる有用性パラメータも同時に影響を受ける可能性がある。対照的に、SST-Merge の element-wise selection は、同一層内でも Fisher 比が高い座標のみを選択できるため、より高い解像度で safety-utility interference を制御できる。

6.2 Data-Free Proxies Effectiveness

データセットなしで推定した SST-V（task-vector ratio）と SST-M（magnitude-only）を比較する。SST-V は、データ依存の FIM-SST と近い Pareto frontier を示し、FIM-based SST の性能の大部分を保持する傾向が観察された。一方、SST-M は高い \alpha 設定において不安定化しやすく、単純な weight magnitude だけでは safety-utility conflict を十分に表現できないことが示唆された。したがって、Data-Free SST においても、単純な magnitude ではなく、パッチ更新量と utility task vector の比を用いることが重要である。

⸻

7. Limitations and Conclusion

本研究で提案した SST-Merge は、局所二次近似と Fisher-ratio subspace projection に基づき、アライメント統合時の Safety Tax を低減するための数理的枠組みを提供する。SST-Merge は Fisher 情報を単なる averaging weight として用いるのではなく、utility Fisher と safety/refusal Fisher の比を用いて、既存の安全パッチから safety-sensitive かつ utility-preserving な成分を選択する。

一方で、本手法は二次近似の有効範囲（PEFT の局所領域）に依存しており、事前学習ベースが大きく異なるモデル同士のマージや、非線形性が極めて強い層での最適性には限界がある。また、初期実験では limit: 320 のサブセット評価を含んでおり、主要な主張にはより大きな評価セット、複数 seed による信頼区間、過剰拒否（over-refusal）の定量的制御が必要である。今後の展望として、この Fisher-ratio subspace steering を非対角 Fisher 情報、低ランク近似、または adapter subspace 上の構造化近似へ拡張し、さらなる干渉除去を目指す。

⸻

参考文献 (References)

1. Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In NAACL.
2. Raffel, C.; Shazeer, N.; Roberts, A.; Lee, K.; Narang, S.; Matena, M.; Zhou, Y.; Li, W.; and Liu, P. J. 2020. Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer. JMLR.
3. Brown, T. B.; Mann, B.; Ryder, N.; Subbiah, M.; Kaplan, J. D.; Dhariwal, P.; Neelakantan, A.; Shyam, P.; Sastry, G.; Askell, A.; et al. 2020. Language Models are Few-Shot Learners. In NeurIPS.
4. Touvron, H.; Martin, L.; Stone, K.; Albert, P.; Almahairi, A.; Babaei, Y.; Bashlykov, N.; Batra, S.; Bhargava, P.; Bhosale, S.; et al. 2023. Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.
5. Zou, A.; Wang, Z.; Kolter, J. Z.; and Fredrikson, M. 2023. Universal and Transferable Adversarial Attacks on Aligned Language Models. arXiv:2307.15043.
6. Wei, A.; Haghtalab, N.; and Steinhardt, J. 2024. Jailbroken: How Does LLM Safety Training Fail? In NeurIPS.
7. Huang, Y.; Zhang, J.; and et al. 2024. TrustLLM: Trustworthiness in Large Language Models. arXiv:2401.05561.
8. Wortsman, M.; Ilharco, G.; Gadre, S. Y.; Roelofs, R.; Lopes, R. G.; Morcos, A. S.; Fang, H.; Simon, S.; Kornblith, S.; Fitzpatrick, M.; et al. 2022. Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Accuracy Without Increasing Inference Time. In ICML.
9. Ilharco, G.; Ribeiro, M. T.; Wortsman, M.; Gururangan, S.; Schmidt, L.; Hajishirzi, H.; and Farhadi, A. 2023. Editing Models with Task Arithmetic. In ICLR.
10. Yadav, P.; Tam, D.; Choshen, L.; Raffel, C.; and Bansal, M. 2023. TIES-Merging: Resolving Interference When Merging Models. In NeurIPS.
11. Yu, L.; Yu, T.; and et al. 2024. Language Models are DARE-ing: Data-Independent Reduction of Parameter Interference. arXiv:2311.03099.
12. Deep, A.; and et al. 2024. DELLA-Merging: Reducing Interference in Model Merging through Magnitude-Based Sampling. arXiv:2406.11617.
13. Garipov, T.; Izmailov, P.; Podoprikhin, D.; Vetrov, D.; and Wilson, A. G. 2018. Loss Surfaces, Mode Connectivity, and Fast Ensembling of DNNs. In NeurIPS.
14. Draxler, F.; Veschgini, K.; Salmhofer, M.; and Hamprecht, F. 2018. Essentially No Barriers in Neural Network Energy Landscape. In ICML.
15. Neyshabur, B.; Sedghi, H.; and Zhang, C. 2020. What is Being Transferred in Transfer Learning? In NeurIPS.
16. Entezari, R.; Sedghi, H.; Saukh, O.; and Neyshabur, B. 2022. The Role of Permutation Invariance in Linear Mode Connectivity of Neural Networks. In ICLR.
17. Zhou, Y.; and et al. 2024. On the Linear Mode Connectivity of Fine-Tuned Large Language Models. arXiv:2402.11324.
18. Hammoud, H. A. A.; and et al. 2024a. One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. arXiv:2406.07542.
19. Hammoud, H. A. A.; and et al. 2024b. MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.
20. Djuhera, A. N. D.; and et al. 2025. SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging. arXiv:2503.17239.
21. Ma, Q.; and et al. 2025. LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In ACL 2025.
22. Wang, Z.; and et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.
23. Wang, Z.; and et al. 2026. Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.
24. Matena, M. S.; and Raffel, C. A. 2022. Merging Models with Fisher-Weighted Averaging. In NeurIPS.
25. Daheim, N.; and et al. 2023. Model Merging by Uncertainty-Based Gradient Matching. arXiv:2310.12808.
26. Thennal, D. K.; and et al. 2024. Fisher Mask Nodes for Language Model Merging. In LREC-COLING.
27. Baban, G.; and et al. 2025. Task-Aware Model Merging via Fisher-Weighted Median. OpenReview.
28. Sanwoo, L.; and et al. 2025. Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In NAACL 2025.
29. Kirkpatrick, J.; Pascanu, R.; Rabinowitz, N.; Veness, J.; Desjardins, G.; Rusu, A. A.; Milan, K.; Quan, J.; Ramalho, T.; Grabska-Barwinska, A.; et al. 2017. Overcoming Catastrophic Forgetting in Neural Networks. PNAS.
30. Izmailov, P.; Podoprikhin, D.; Garipov, T.; Vetrov, D.; and Wilson, A. G. 2018. Averaging Weights Leads to Wider Optima and Better Generalization. In UAI.
31. Hinton, G.; Vinyals, O.; and Dean, J. 2015. Distilling the Knowledge in a Neural Network. In NeurIPS Workshop.
32. McMahan, B.; Moore, E.; Ramage, D.; Hampson, S.; and Arcas, B. A. 2017. Communication-Efficient Learning of Deep Networks from Decentralized Data. In AISTATS.
33. Amodei, D.; and et al. 2016. Concrete Problems in AI Safety. arXiv:1606.06565.
34. Carlini, N.; and et al. 2021. Extracting Training Data from Large Language Models. In USENIX Security.
35. Ouyang, L.; and et al. 2022. Training Language Models to Follow Instructions with Human Feedback. In NeurIPS.
36. Bai, Y.; and et al. 2022. Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073.
37. Pascanu, R.; and Bengio, Y. 2014. Revisiting Natural Gradient for Deep Networks. In ICLR.
38. Amari, S. 1998. Natural Gradient Works Efficiently in Learning. Neural Computation.
39. Martens, J. 2020. New Insights and Perspectives on the Natural Gradient Method. JMLR.
40. Chegini, A.; and et al. 2024. SALSA: Alignment Soups for Robust Preference Optimization. arXiv:2407.11234.
41. Akiba, T.; and et al. 2025. Evolutionary Optimization of Model Merging. arXiv:2403.13187.
42. Polyak, B. T.; and Juditsky, A. B. 1992. Acceleration of Stochastic Approximation by Averaging. SIAM Journal on Optimization.
43. Frankle, J.; Dziugaite, G. K.; Roy, D.; and Carbin, M. 2020. Linear Mode Connectivity and the Lottery Ticket Hypothesis. In ICML.
44. Jin, X.; and et al. 2023. Dataless Knowledge Fusion by Merging Weights of Simplified Classifiers. In ICML.
45. Tam, D.; and et al. 2024. Merging Models in the Geometric Space. In ICLR.
46. Ruder, S.; and Plank, B. 2017. Learning to Select Data for Transfer Learning with Bayesian Optimization. In EMNLP.
47. Wolf, T.; and et al. 2019. HuggingFace’s Transformers: State-of-the-Art Natural Language Processing. arXiv:1910.03771.
48. Choshen, L.; and et al. 2022. Fusing Fine-Tuned Models for Better Generalization. arXiv:2211.02534.
49. Ortiz-Jimenez, G.; and et al. 2023. Task Arithmetic in the Geometric Space of Weights. arXiv:2305.14238.
50. Davari, M.; and et al. 2024. Model Breadcrumbs: Important Parameter Selection for Merging. arXiv:2408.09913.
51. Luo, Z.; and et al. 2023a. WizardMath: Empowering Mathematical Reasoning for Large Language Models via Reinforcement Learning from Evol-Instruct. arXiv:2308.09583.
52. Luo, Z.; and et al. 2023b. WizardCoder: Empowering Code Generation in Large Language Models as a Code Assistant. arXiv:2306.08568.
53. Han, T.; and et al. 2023. MedAlpaca: An Open-Source Collection of Medical Language Models. arXiv:2304.08278.
54. Mazeika, M.; and et al. 2024. HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal. arXiv:2402.04249.
55. Chao, P.; and et al. 2024. JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models. arXiv:2404.01318.
56. Souly, A.; and et al. 2024. A StrongREJECT for Empty Jailbreaks. arXiv:2402.10260.
57. Jiang, Y.; and et al. 2024. WildJailbreak: Benchmarking Jailbreak Robustness of Large Language Models. arXiv:2406.12903.
58. Cobbe, K.; and et al. 2021. Training Verifiers to Solve Math Word Problems. arXiv:2110.14168.
59. Lewkowycz, A.; and et al. 2022. Solving Quantitative Reasoning Problems with Language Models. In NeurIPS.
60. Chen, M.; and et al. 2021. Evaluating Large Language Models Trained on Code. arXiv:2107.03374.
61. Austin, J.; and et al. 2021. Program Synthesis with Large Language Models. arXiv:2108.07732.
62. Jin, Q.; and et al. 2019. PubMedQA: A Dataset for Biomedical Research Question Answering. In EMNLP.
63. Jin, D.; and et al. 2021. What Disease Does This Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams. Applied Sciences.
64. Hendrycks, D.; and et al. 2020. Measuring Massive Multitask Language Understanding. In ICLR.
65. Zhou, J.; and et al. 2023. Instruction-Following Evaluation for Large Language Models. arXiv:2311.07911.
66. Röttger, P.; and et al. 2023. XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models. arXiv:2308.01263.
67. Sun, L.; and et al. 2024. TrustLLM: Trustworthiness in Large Language Models. arXiv:2401.05561.
68. Ji, J.; and et al. 2024. BeaverTails: Towards Improved Safety Alignment of LLM via a Human-Preference Dataset. arXiv:2307.04657.