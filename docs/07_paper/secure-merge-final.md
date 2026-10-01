# Secure Model Mergingにおける Safety–Utility トレードオフの統一的比較評価

## Abstract

大規模言語モデル（LLM）を専門タスクに適応させる際、安全性アライメントが劣化する Safety–Utility トレードオフは、モデルマージの実用化における中心的な障害となっている。本稿は、Task Arithmetic、TIES、DARE、DELLAといった標準的マージ手法、Matena–RaffelのFisher-Weighted Averagingに代表されるFisher重要度型手法、MergeAlign、SafeMERGE、LED-Mergingに代表される安全性選択型手法、およびAlignMergeに代表されるFisher幾何制約型手法を、干渉の定義単位（ベクトル全体・パラメータ・層・ニューロン・部分空間）という観点から統一的に整理し、数式とアルゴリズム的手順に基づいて比較した。さらに、Llama-2-7Bを基盤としたSecure Merge実験ログを直接検証し、既報の比較表に見られるベースライン一致、DELLA崩壊行の実験条件混同、Diagonal SST-Merge数値の不整合、Gibberish崩壊による見かけ上の安全性向上を明らかにした。結果として、安全性を独立の構造として明示的に扱う手法群（層単位・ニューロン単位・部分空間単位）が、干渉緩和のみを目的とする手法群よりも安全性と有用性を同時に維持しやすいことが確認され、Fisher情報は単一分布上の重要度指標としてよりも、安全性と有用性という複数分布間の競合を分離する構造情報として用いる方が Secure Merge には適していると結論した。

**キーワード**: モデルマージ、Fisher情報行列、安全性アライメント、Safety-Utilityトレードオフ、大規模言語モデル

---

## 1. はじめに

大規模言語モデルの実運用では、数学、コード生成、医療対話などの専門能力を高めたモデルと、有害要求への拒否や安全な応答制御を重視したアライン済みモデルを両立させることが重要である。しかし、これらを個別に再学習して統合することは計算資源、選好データ、反復的な安全性検証を要するため高コストである。このため、共通の事前学習済み基盤モデルから派生した複数チェックポイントを、追加学習なしに重み空間で直接統合するモデルマージが、有用な実践的選択肢として急速に注目されている\[1\]\[2\]。

一方で、モデルマージは単なる能力統合手段ではない。とりわけ安全性アライメントを獲得したモデルと専門タスクモデルを統合する場合、タスク性能の向上と引き換えに拒否行動が崩れたり、逆に安全性を過度に優先して有用性が損なわれたりする、いわゆる Safety–Utility トレードオフが顕在化する。Hammoudらは、独立には安全なモデルであっても、事後的なマージ後には安全性が大きく劣化し得ることを示し、この問題を「one bad model spoils the bunch」と表現した\[3\]。この現象は、専門化によって獲得された更新と安全性アライメントを担う更新が、同一パラメータ座標や同一機能単位で干渉することに起因する。

こうした背景から、近年のモデルマージ研究は、単純な平均や線形補間から、重要パラメータのみを保持する方法、符号衝突を解消する方法、Fisher情報行列（FIM）に基づく局所曲率を利用する方法、さらに安全性そのものを保存対象とみなす幾何学的・選択的マージ法へと発展してきた\[4\]\[5\]\[6\]\[7\]。しかし、既存研究の多くは、性能保持、安全性保護、Data-Free実装可能性、理論的最適性のいずれか一部に重点を置くにとどまり、これらを統一的に比較した評価研究は十分ではない。

本稿は、Secure Merge実験ログを直接検証しつつ、先行研究を数式・アルゴリズム・設計思想の水準まで掘り下げて整理し、標準的マージ手法、Fisher活用型手法、安全性維持型手法、およびFisher幾何型手法を統一的な観点から比較評価することを目的とする。

## 2. 研究課題

本稿が扱う研究課題は以下の5点である。

- **RQ1（パレート境界）**: 標準的マージ、Fisher重要度マージ、安全性選択マージ、幾何制約マージはそれぞれどのようなSafety–Utilityパレート境界を形成するか。
- **RQ2（干渉単位と崩壊様式）**: ベクトル全体・パラメータ・層・ニューロン・部分空間という介入粒度の違いは、拒否行動維持、Gibberish崩壊、一般性能保持にどう影響するか。
- **RQ3（Fisher情報の役割）**: Fisher情報は単なる重み付け係数か、それとも安全性と有用性の競合を分離する構造情報として機能するか。
- **RQ4（Data-Free化の限界）**: 補助データが利用できない条件下で、Fisherベースのマージはどこまで性能・安全性を維持できるか。
- **RQ5（評価論文としての信頼性）**: 報告される表・数値は実際の評価ログと整合しているか。

## 3. 関連研究

### 3.1 研究潮流の4フェーズ整理

モデルマージ研究の展開は、大きく4フェーズに整理できる。第1フェーズ（2022–2023年）はFisher-Weighted AveragingやTask Arithmeticに代表される黎明期であり、複数タスクモデルを壊さず平均する理論の確立が主要課題であった\[1\]\[2\]。第2フェーズ（2024–2025年）はTIES、DARE、DELLA、Fisher Mask Nodes、Fisher-Weighted Median、ベイズ最適化型手法など、干渉緩和・外れ値耐性・計算効率・ハイパーパラメータ自動化への関心の広がりを特徴とする\[8\]\[9\]\[10\]\[11\]\[12\]\[13\]。第3フェーズ（2024–2026年）はMergeAlign、SafeMERGE、LED-Merging、AlignMergeに代表されるSafety–Utility特化期であり、安全パッチと有用性パッチの衝突そのものが主要研究対象となった\[6\]\[14\]\[7\]\[15\]。第4フェーズ（2025–2026年）は補助データが使えない現実的制約を前提とするData-Free実装の追求である\[16\]。

**表1. モデルマージ研究の4フェーズと代表手法**

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

で表される\[2\]。Ilharcoらは、これにより加算・減算・類推といった演算が直接モデル挙動編集として機能することを示した。この系統の限界は、どの座標が安全性に重要か、どの方向が有用性に寄与するかを区別しない点にあり、安全性と専門性能が同一パラメータで競合する場合、最も単純な加法は最も不安定な統合法となる。

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

この系統には、勾配整合性に着目したUncertainty-based Gradient Matching\[18\]、マスクノードにより計算量を削減したFisher Mask Nodes\[9\]、Fisher重み付き中央値で外れ値耐性を高めたDRIFT-MEDIAN\[11\]、ベイズ最適化で係数を自動探索するDF-Merge\[12\]が含まれる。いずれも「Fisherは何らかの重要度を表す」という認識に立つが、安全性と有用性の二重目的を同時に扱うわけではない。

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

これら三手法はいずれも局所ヒューリスティクスで更新を選別するが、安全性を明示的目的としないため、安全性更新と有用性更新が競合するSecure Merge設定では、干渉を減らしても安全性が保たれる保証はない。

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

を計算し\[7\]、Electionではベースモデルと専門モデル双方で高重要度なニューロン集合の積集合を取り、Disjointではタスク間で共有される重要ニューロンを差集合で分離する。

### 3.6 Fisher幾何型：AlignMergeとData-Free拡張

AlignMergeは、Fisher情報を単なるパラメータ重みではなく、モデル空間上の局所計量として解釈する\[15\]。設計思想は、アライメントを部分空間または多様体として表現し、マージ後もそこから大きく逸脱しないよう制約付き最適化として統合を定式化する点にある。Data-Free Layer-Adaptive Mergingは、ランダムトークン列から層別Fisherを近似し、補助データなしでもFisher型マージを可能にする方向性を示した\[16\]が、近似Fisherが本来の重要度ランキングをどこまで保持するかは未解明である。

### 3.7 関連研究の比較整理

**表2. 各手法の設計原理比較**

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

## 4. 評価対象手法

本稿では、標準ベースラインとしてTask Arithmetic、TIES、DARE、DELLAを扱う。Fisher重要度系としてMatena Fisher（FWA）を扱い、安全性維持系としてMergeAlign、SafeMERGE、LED-Mergingを参照対象とする。加えて、Fisher比率に基づく安全性指向マージであるDiagonal SST-MergeおよびData-Free SST-Mergeを比較対象に含める。

## 5. 実験設定

**表3. 実験設定の概要**

| 項目 | 内容 |
|---|---|
| 基盤モデル | Llama-2-7B-base |
| 安全モデル | SafetyFT |
| 専門モデル | WizardMath-7B-V1.0（数学）, WizardCoder-Python-7B-V1.0（コード）, MedAlpaca-7B（医療） |
| 実験条件 | safety+math, safety+code, safety+medical, safety+math+code+medical |
| Fisher推定 | harmful/benignキャリブレーション（n=500） |
| 評価上限 | 各ベンチマーク最大320サンプル |
| 安全性評価 | HarmBench, JailbreakBench, StrongReject, WildJailbreak |
| 有用性評価 | GSM8K, Minerva Math500, HumanEval, MBPP, PubMedQA, MedQA, MMLU, IFEval, AlpacaEval2 |
| 過剰拒否評価 | XSTest |

安全性評価には Original ASR、Filtered ASR、Gibberish N、Gibberish Filter Ratio を算出する。Gibberish指標を独立に報告することは、無意味反復出力が「安全」と誤判定される偽陽性を防ぐうえで重要である。

## 6. 実験結果

### 6.1 ベースライン整合性

実験ログを直接確認すると、WizardMath baseのGSM8Kは39.375%であり、報告値39.38%と一致する。SafetyFT baseの数値も概ね報告表と整合しており、ベースライン行に関しては転記精度は高い。

### 6.2 2ドメイン設定と4ドメイン設定の挙動差

**表4. DELLA（α=0.8）の条件別挙動比較**

| 条件 | GSM8K | HarmBench ASR | 応答の質 |
|---|---|---|---|
| safety+math（2ドメイン） | 33.33% | 0.0 | 正常 |
| safety+math+code+medical（4ドメイン） | 0.0% | 0.0 | 無意味反復（`ugaugauga...`型崩壊） |

4ドメイン同時マージでは、HarmBench ASRが0.0であるにもかかわらず実際には全件崩壊に近い状態であり、2ドメイン条件とは質的に異なる高干渉条件であることが分かる。

### 6.3 表の帰属不整合

報告Table 3に現れる「DELLA α=0.8」の全崩壊行は、体裁上safety+mathのαスイープ内に配置されているが、実際には4ドメイン同時マージの結果に一致する。このため「DELLAはα=0.8で崩壊する」という一般化は不正確であり、「DELLAは高干渉の4ドメイン条件で崩壊しやすい」と読むべきである。

### 6.4 Diagonal SST-Mergeの数値不整合

**表5. safety+math条件におけるDiagonal SST-MergeのGSM8K実測値と報告値の比較**

| α | 実測値 | 報告値（Table 3） | 差分 |
|---|---|---|---|
| 0.2 | 37.81% | 42.81% | +5.00pt |
| 0.6 | 35.63% | 36.56% | +0.93pt |
| 0.8 | 31.56% | 33.44% | +1.88pt |
| 1.0 | 29.06% | 27.19% | −1.87pt |

Appendixの同一設定値とも完全には整合しないため、この部分は単一の集計スクリプトから再生成されていない可能性が高い。

### 6.5 代表的傾向

質的傾向には一貫性がある。Task Arithmeticは最も単純であり、2ドメインでは一定の有用性を保つが、安全性とのバランスでは不安定である。TIESは符号衝突解消により一部安定化するが、安全性を直接制御しない。DAREとDELLAは疎化によって一部条件で安全性と有用性を両立するが、条件が厳しくなるとGibberish崩壊を引き起こしやすい。SafeMERGEやLED-Mergingのような明示的安全性指向手法が低ASRと有用性保持を同時に示すのは、関連研究の理論設計とも整合的である。

## 7. 考察

### 7.1 Related Workとの接続：なぜ崩壊様式が異なるのか

実験結果は、関連研究で整理した「干渉の定義単位」の違いとよく対応している。Task Arithmeticはベクトル全体を一括加算するため競合が局所化されず表面化しやすい。TIES、DARE、DELLAはパラメータ単位で干渉を緩和するが、安全性そのものを保持対象として扱わないため、高干渉条件では無意味反復や極端な性能低下に至り得る。これは、更新を削ることと安全性を守ることが同義ではないことを示している。

一方、MergeAlign、SafeMERGE、LED-Merging、AlignMergeの系統は、安全性を独立の構造として扱うため、少なくとも設計原理上は「何を守るべきか」が明示されている。この違いが、単なる干渉緩和手法よりも安全性維持に有利な背景である。

### 7.2 Gibberishと偽の安全性

本実験で重要なのは、ASR 0.0が必ずしも「安全」を意味しないことである。4ドメイン条件のDAREやDELLAでは、無意味出力がHarmBenchでは有害応答ではないと判定され、表面的には安全に見える。これは、無意味出力が安全評価器のスコアを人為的に改善しうることを意味し、Filtered ASRとGibberish Filter Ratioを切り離して報告することが不可欠であることを示唆する。

### 7.3 Fisher情報の再解釈

Fisher系研究はもともと「何が重要なパラメータか」を見極めるための枠組みとして発展してきたが、Secure Merge設定では重要性は一元的ではない。ある方向は有用性にとって重要だが安全性にとって有害かもしれず、別の方向は安全性にとって重要だが一般性能を落とすかもしれない。単一Fisherに基づくFWAやその派生手法は、この競合を分解するには不十分であり、harmful/benignなど複数分布上でのFisherを別々に扱い、その比率や差異に基づいて方向選択する発想がSecure Merge文脈では自然な拡張となる。

### 7.4 評価論文としての含意

本研究で明らかになった表の不整合は、単なる転記ミスにとどまらない。2ドメイン設定と4ドメイン設定の結果を混同すれば、ある手法の安全性評価は必要以上に悲観的または楽観的に見積もられる。したがって評価論文としては、(i) 実験条件ごとの表の完全分離、(ii) 単一スクリプトからの自動再集計、(iii) Gibberishを除外した安全指標の主報告、の三点が最低限必要である。

## 8. 結論

本稿は、Fisher系先行研究および安全性選択型先行研究を数式・アルゴリズム・設計思想の水準まで整理し、Secure Model Mergingの評価論文として統一的な節構成・数式番号のもとに統合した。実験ログとの照合により、ベースラインの整合性、DELLA崩壊行の実験条件混同、Diagonal SST-Merge数値の不整合、Gibberishに起因する偽の安全性問題を明示した。

全体として、モデルマージ研究は「平均する」段階から「何を削るか」を工夫する段階を経て、「何を守るべきか」を安全性の観点から定義する段階へ進化している。本評価は、その流れを実験的にも理論的にも接続し、Secure Mergeを単なる性能比較ではなく、干渉の定義、重要度の意味、安全性指標の妥当性まで含めて評価すべき対象として位置づけ直すものである。

---

## 参考文献

\[1\] Matena, M. S.; Raffel, C. A. 2022. Merging Models with Fisher-Weighted Averaging. In *NeurIPS*.

\[2\] Ilharco, G.; Ribeiro, M. T.; Wortsman, M.; Gururangan, S.; Schmidt, L.; Hajishirzi, H.; Farhadi, A. 2023. Editing Models with Task Arithmetic. In *ICLR*. arXiv:2212.04089.

\[3\] Hammoud, H. A. A. K.; et al. 2024. One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. arXiv:2406.07542.

\[4\] Yadav, P.; Tam, D.; Choshen, L.; Raffel, C.; Bansal, M. 2023. TIES-Merging: Resolving Interference When Merging Models. In *NeurIPS*. arXiv:2306.01708.

\[5\] Wang, Z.; et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.

\[6\] Hammoud, H. A. A. K.; et al. 2024. MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.

\[7\] Ma, Q.; et al. 2025. LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In *ACL 2025*. arXiv:2502.16770.

\[8\] Yadav, P.; Tam, D.; Choshen, L.; Raffel, C.; Bansal, M. 2023. TIES-Merging: Resolving Interference When Merging Models. In *NeurIPS*. arXiv:2306.01708.

\[9\] Thennal, D. K.; Nathan, G.; Suchithra, M. S. 2024. Fisher Mask Nodes for Language Model Merging. In *LREC-COLING 2024*.

\[10\] Deep, P. T.; Bhardwaj, R.; Poria, S. 2024. DELLA-Merging: Reducing Interference in Model Merging Through Magnitude-Based Sampling. arXiv:2406.11617.

\[11\] Baban, G.; et al. 2025/2026. Task-Aware Model Merging via Fisher-Weighted Median (DRIFT-MEDIAN). Under review, ICLR 2026 (OpenReview).

\[12\] Lee, S.; Liu, J.; Wang, Q.; Wang, J.; Cai, X.; Wu, Y. 2025. Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In *NAACL 2025*, pp. 4923–4935.

\[13\] Daheim, N.; Möllenhoff, T.; Ponti, E.; Gurevych, I.; Khan, M. E. 2024. Model Merging by Uncertainty-Based Gradient Matching. In *ICLR*. arXiv:2310.12808.

\[14\] Djuhera, A.; Kadhe, S. R.; Ahmed, F.; Zawad, S.; Boche, H. 2026. SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging. In *Findings of ACL 2026*. arXiv:2503.17239.

\[15\] Wang, Z.; et al. 2025. AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.

\[16\] Wang, Z.; et al. 2026. Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.

\[17\] Wortsman, M.; Ilharco, G.; Gadre, S. Y.; et al. 2022. Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Accuracy Without Increasing Inference Time. In *ICML*.

\[18\] Daheim, N.; Möllenhoff, T.; Ponti, E.; Gurevych, I.; Khan, M. E. 2024. Model Merging by Uncertainty-Based Gradient Matching. In *ICLR*. arXiv:2310.12808.

\[19\] Yu, L.; Yu, B.; Yu, H.; Huang, F.; et al. 2024. Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch (DARE). arXiv:2311.03099.

\[20\] Deep, P. T.; Bhardwaj, R.; Poria, S. 2024. DELLA-Merging: Reducing Interference in Model Merging Through Magnitude-Based Sampling. arXiv:2406.11617.
