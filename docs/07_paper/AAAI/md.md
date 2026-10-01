## 1. はじめに (Introduction)

大規模言語モデル（LLM）は、汎用的な事前学習の後に特定のドメイン（数学、コード生成、医療対話など）でファインチューニングを施すことで、当該タスクにおいて飛躍的な性能向上を達成するというパラダイムのもとで急速に普及してきた。Hugging Face をはじめとするモデルリポジトリには、こうしたドメイン特化のファインチューニング済み専門モデル（expert models）が既に数百万規模で公開されており、研究者や実務者は目的に応じてこれらを自由に組み合わせて利用できる環境が整いつつある。[^1]

しかし、この専門化には重大な副作用が伴う。特定タスク向けにファインチューニングされたモデルは、そのタスクに過剰適合する一方で、事前学習段階や instruction tuning、RLHF などを通じて獲得された安全性アライメント（safety alignment）を著しく喪失しやすいことが、複数の実証研究によって指摘されている。良性（benign）なデータセットのみを用いた追加学習であっても、モデルの安全機構が意図せず劣化し、悪意あるユーザーによるジェイルブレイク（jailbreak）攻撃に対して脆弱になる現象が繰り返し報告されている。この安全性の劣化に対し、各専門モデルごとに RLHF や DPO などの安全性アライメント手続きを再度実施することは、計算コスト、必要データ量、そして訓練データのプライバシー制約の観点から実務上極めて困難である。

こうした背景のもと、追加学習や検証データへのアクセスを必要とせず、パラメータ空間（parameter space）上で複数のモデルの重みを直接統合する「モデルマージ（Model Merging）」という枠組みが強い注目を集めている。モデルマージは、独立にファインチューニングされたモデル間でも、事前学習パラメータから局所最適解に至る損失地形（loss landscape）が平坦で障壁のない領域（flat basin）によって線形に接続され得るという知見に支持されており、Model Soups に代表される重み平均化手法から、タスクベクトル（task vector）の加減算によってモデルの振る舞いを編集する Task Arithmetic に至るまで、多様な手法が提案されてきた。[^2][^1]

とりわけ、事後的に安全性を専門モデルへ配備する「Secure Merge」（安全性統合マージ）の設定においては、近年の研究によりモデルマージ時に安全性の回復と有用性（タスク性能）の保持との間に鋭いトレードオフが生じることが繰り返し報告されている。単純なタスクベクトルマージや、干渉緩和を目的とした TIES、DARE、DELLA といった手法は、そもそも安全性統合を想定した設計になっておらず、安全パッチが通常タスクのパラメータ更新と干渉し、有用性を大きく破壊してしまう問題を十分に制御できない。さらに、単一の安全性が損なわれた専門モデルをマージに含めるだけで、マージ後モデルの安全性挙動全体が崩壊し、ジェイルブレイク成功率（Attack Success Rate: ASR）が急激に増加する一方、一般的なタスク性能の劣化は目立たないという「隠れたアライメント喪失（hidden alignment loss）」が生じることも指摘されている。[^3]

本研究は、こうした課題認識のもと、標準的なタスクベクトルマージ手法（Task Arithmetic, TIES, DARE, DELLA）と、安全性維持を明示的に目的としたマージ手法（MergeAlign, SafeMERGE, LED-Merging, Matena & Raffel の Fisher Weighted Averaging）を、大規模かつ多角的なベンチマークデータセット群を用いて統一的な条件下で比較評価することを目的とする。個別の新規手法の優劣を主張することよりも、既存の代表的マージパラダイム群が「安全性能（ASRの低下）」と「有用性保持（タスク精度の維持）」という二軸のトレードオフ空間において、それぞれどのような特性・限界・頑健性を示すのかを、体系的かつ再現可能な評価プロトコルのもとで明らかにすることに主眼を置く。

## 2. 研究の動向 (Related Work Trends)

### 2.1 モデルマージの一般的発展

モデルマージの起源は、同一の初期化・アーキテクチャから独立にファインチューニングされた複数のチェックポイントの重みを単純に平均化する Model Soups にさかのぼる。この考え方は、確率的近似における平均化理論（Polyak–Ruppert averaging）や、SGD の重み平均によって汎化性能が向上するという Stochastic Weight Averaging（SWA）の知見とも関連づけられる。これに続き、Ilharco らはファインチューニング済みモデルとベースモデルの差分である「タスクベクトル」を定義し、これに対する加算・減算・線形結合といった算術演算によってモデルの振る舞いを編集できることを示す Task Arithmetic を提案した。Task Arithmetic は \(\tau = \theta_{\text{fine}} - \theta_{\text{base}}\) というタスクベクトルの概念を導入し、複数タスクの合成（マルチタスク化）や特定能力の除去（機械アンラーニング）を、追加学習なしに実現する枠組みを提供した。[^4][^1][^2]

しかし、複数のタスクベクトルを単純に加算するアプローチは、パラメータ間の干渉（interference）によって深刻な性能劣化を招くことが明らかになった。この干渉は主に、(a) 冗長な微小パラメータ値による干渉と、(b) 異なるモデル間でのパラメータ符号（正負）の不一致による干渉の2種類に分類される。この課題に対処するため、TIES-Merging は「Trim（微小変化のリセット）」「Elect Sign（符号の多数決による統一）」「Disjoint Merge（合意した符号のパラメータのみの平均化）」という3段階の手続きを提案し、複数のモダリティ・ドメイン・モデル規模にわたって既存手法を上回る性能を報告した。[^5][^6]

一方、DARE（Drop And REscale）は、ファインチューニングによって生じるデルタパラメータの90〜99%を確率的にランダムに削除しても、生存パラメータを適切にリスケールする限りモデル能力がほとんど損なわれないという「デルタパラメータの極端な冗長性」を実証的に発見した。これはファインチューニングにより獲得される「知識」が実際にはごく一部の高振幅なパラメータ変化に集中しており、残りの大部分は干渉の原因となるノイズに近いという知見を示すものであり、Task Arithmetic や TIES の前処理として組み合わせることで、複数の専門モデル（例：WizardLM、WizardMath、Code Alpaca）を単一モデルへ干渉なく統合できることが示された。[^7][^8][^9]

DELLA-Merging はこれをさらに発展させ、パラメータの大きさに応じてドロップ確率を可変にする新しい枝刈り手法「MAGPRUNE」を提案した。MAGPRUNE は、パラメータをその絶対値の大きさで順位付けし、振幅の小さいパラメータほど高いドロップ確率を割り当てたうえで、生存パラメータを \(1/(1-p)\) 倍にリスケールすることで元の埋め込みを近似する。この手法は DARE や TIES に対して優位性を示すことが報告されている。[^10]

### 2.2 Fisher 情報に基づくマージ

モデルパラメータの重要度（感度）を定量的に扱う枠組みとして、Matena と Raffel は対角 Fisher 情報行列（Fisher Information Matrix: FIM）を用いてモデルパラメータの事後分布をガウス近似し、その精度（precision）を Fisher 情報として重み付けする「Fisher Merging」を提案した。この手法は、各モデルの事後分布をラプラス近似によりガウス分布として捉え、複数モデルの重み付き結合を、事後分布の同時尤度を近似的に最大化する操作として定式化する点に特徴がある。ロバストなファインチューニングやモデルアンサンブルの設定において、単純平均に対する性能向上が実証された。[^11][^12]

この考え方はその後、複数の方向へ発展している。Daheim らは、更新誤差を不確実性で補正する Uncertainty-based Gradient Matching を提案し、Thennal らは Fisher マスクにより重要ニューロンのみを選別する Fisher Mask Nodes を提案した。さらに、Fisher 重み付き中央値を用いる DRIFT-MEDIAN や、マージ係数をベイズ最適化によって動的に決定する DF-Merge（Dynamic Fisher-weighted Model Merging via Bayesian Optimization）など、Fisher 情報を単一タスク空間内でのマージ精度向上に活用する研究が継続的に提案されている。これらの手法は基本的に単一タスク統合の文脈における性能改善を目的としており、後述するような「安全性」と「有用性」という対立する2つの分布間の曲率比を明示的に最適化する枠組みではない点に留意する必要がある。[^13][^14][^15]

### 2.3 安全性維持マージの発展

ファインチューニングによる安全性アライメントの劣化という課題が広く認識されるにつれ、モデルマージを安全性回復の手段として活用する研究が急速に発展した。Hammoud らは、専門モデル群の中にわずか1つでも安全性が損なわれたモデルが混入すると、マージ後モデルの安全性挙動全体が崩壊し、ジェイルブレイク成功率が爆発的に増加する一方で、一般タスク性能の劣化は目立たないという「隠れたアライメント喪失」現象を報告した。この知見を受けて同グループは、ドメインベクトルとアライメントベクトルを補間によって統合する MergeAlign を提案し、知識獲得と安全性の間のトレードオフをより良く制御できることを示した。[^16][^3]

SafeMERGE（Djuhera ら）は、安全性の劣化がモデル全体に一様に生じるのではなく、特定のレイヤーに局在するという観察に基づき、コサイン類似度基準を用いて安全アライメントから逸脱した度合いが大きいレイヤーのみを選択的に安全モデルの対応レイヤーとマージする、軽量な後処理フレームワークを提案した。具体的には、射影行列を用いてファインチューニング済みアダプタの重みが安全な参照からどれだけ逸脱しているかを測定し、コサイン類似度が閾値を下回った場合にのみ、ファインチューニング済みアダプタと安全アダプタを部分的な重み（例: 0.8対0.2）でマージする。複数の LLM とタスクにわたる実験で、有用性への影響を無視できる範囲に抑えつつ、有害出力を一貫して低減できることが報告されている。[^17][^18]

LED-Merging（Ma ら）は、レイヤー単位ではなくニューロン単位でのより細かい粒度の選択を行う三段階フレームワークである。すなわち、(1) 勾配ベースの重要度スコア \(I(\theta_i) = \mathbb{E}_{x \sim X_i}[\theta_i \odot \nabla_{\theta_i} L(x)]\) によりベースモデルとファインチューニング済みモデルの双方から重要なニューロンを特定する「Location」、(2) 双方で高スコアを示すニューロンの積集合を取る「Election」、(3) タスク間で重複する重要ニューロンを集合差演算によって排除し干渉を防ぐ「Disjoint Merging」の三段階から構成される。Llama-3-8B、Mistral-7B、Llama-2-13B など複数のモデルを対象とした実験では、HarmBench や GSM8K、MBPP などのベンチマークにおいて、既存のマージ手法に比して安全性指標を大幅に改善しつつ高い有用性を維持できることが報告されている。[^19][^20][^21]

### 2.4 評価枠組みの発展

安全性維持マージ手法の評価においては、ジェイルブレイク攻撃への頑健性を測定するベンチマークの整備が並行して進んでいる。初期の評価では、TrustLLM が提供する Longformer ベースの有害応答判別器を用いた拒否応答率（Refuse to Answer: RtA）測定や、BeaverTails の有害プロンプトセットが広く参照されてきた。近年ではこれに加え、HarmBench、JailbreakBench、StrongReject、WildJailbreak といった、より多様な攻撃手法・脅威モデルを網羅する標準化ベンチマークが整備されており、単一の指標に依存しない多角的な安全性評価が主流となりつつある。また、過剰拒否（over-refusal）、すなわち無害な質問に対してモデルが不必要に拒絶反応を示してしまう現象を検知する XSTest のような補完的ベンチマークも、安全性と有用性のバランスを正確に評価するうえで重要な役割を果たしている。

## 3. 比較手法のまとめ

本評価で対象とする8つのマージ手法は、「標準マージ手法群」と「安全性維持マージ手法群」の2つに大別される。以下の表に、各手法の中核メカニズムと粒度、主な特徴を整理する。

| 手法 | カテゴリ | 選択・統合の粒度 | 中核メカニズム |
|---|---|---|---|
| Task Arithmetic[^1] | 標準マージ | パラメータ全体（一様係数） | タスクベクトルの線形加算・減算 \(\theta_m = \theta_u + \alpha\Delta\) |
| TIES[^5] | 標準マージ | パラメータ単位 | Trim（微小値リセット）→Elect Sign（符号統一）→Disjoint Merge |
| DARE[^7][^8] | 標準マージ | パラメータ単位（ランダム） | デルタのランダムドロップ（90〜99%）とリスケール |
| DELLA[^10] | 標準マージ | パラメータ単位（magnitude順） | MAGPRUNE：振幅に応じた可変ドロップ確率とリスケール |
| MergeAlign[^16][^3] | 安全維持 | ベクトル全体（補間） | ドメインベクトルとアライメントベクトルの補間統合 |
| SafeMERGE[^17][^18] | 安全維持 | レイヤー単位 | コサイン類似度による逸脱レイヤーの選択的マージ |
| LED-Merging[^19][^21] | 安全維持 | ニューロン単位 | 勾配重要度によるLocation-Election-Disjointの3段階選別 |
| Matena & Raffel Fisher Weighted[^11][^12] | 安全維持（Fisher活用） | パラメータ単位（対角FIM） | 対角Fisher情報による重み付き平均（ラプラス近似） |

標準マージ手法群は共通して、安全性統合を明示的な目的として設計されていない点が特徴である。Task Arithmetic は最も単純な線形結合であり、パラメータ干渉に対する保護機構を持たない。TIES、DARE、DELLA はいずれも「干渉緩和」を目的とした前処理・選別ステップを持つが、その基準はいずれもタスクベクトル自体の統計的性質（符号の一致度、振幅の大きさ）に基づくものであり、安全性データ分布に対する感度を明示的に考慮しない。したがって、これらの手法を Secure Merge 設定に適用した場合、安全パッチとタスクベクトルの干渉が適切に制御されず、安全性の回復と有用性の保持のいずれか一方、あるいは両方が犠牲になりやすいと考えられる。[^8][^1][^5][^10]

一方、安全性維持マージ手法群は、いずれも「安全性に関わるパラメータ・レイヤー・ニューロンを特定し、選択的に統合する」という共通の設計思想を持つが、その選択粒度と判定基準は手法ごとに大きく異なる。MergeAlign はベクトル全体レベルでの補間という粗い粒度で介入する一方、SafeMERGE はレイヤー単位、LED-Merging はニューロン単位というより細かい粒度で介入する。Matena & Raffel の Fisher Weighted Averaging は、本来は単一タスク統合のための手法として提案されたものであるが、対角 Fisher 情報をパラメータ重要度の代理指標として用いる考え方は、安全性と有用性という対立する2つの目的間の重み付けにも応用可能であり、本評価では安全性維持の文脈における Fisher ベースのベースラインとして位置づける。[^16][^17][^19][^11]

これらの手法群を統一的なベンチマーク環境下で比較することにより、粒度（パラメータ／レイヤー／ニューロン／ベクトル全体）の違いが安全性-有用性のパレート境界にどのような影響を与えるか、また Fisher 情報などの曲率情報を用いる手法が単純な符号・振幅ベースの手法に対してどの程度の優位性を持つかを、定量的に明らかにすることが可能になる。

---

## References

1. [[2212.04089] Editing Models with Task Arithmetic](https://arxiv.org/abs/2212.04089) - G Ilharco 著 · 2022 · 被引用数: 1663 — We show that these task vectors can be modified and combined toget...

2. [[PDF] averaging weights of multiple fine-tuned models improves accuracy ...](https://proceedings.mlr.press/v162/wortsman22a/wortsman22a.pdf)

3. [Model Merging and Safety Alignment: One Bad ...](https://repository.kaust.edu.sa/server/api/core/bitstreams/c206ef07-1a7d-4a08-b65c-882db3d7935e/content)

4. [On Fairness of Task Arithmetic: The Role of Task Vectors](https://openreview.net/attachment?id=nAb0PEDDbS&name=pdf)

5. [TIES-Merging: Resolving Interference When Merging Models](https://arxiv.org/abs/2306.01708) - P Yadav 著 · 2023 · 被引用数: 1081 — View a PDF of the paper titled TIES-Merging: Resolving Interference ...

6. [[PDF] TIES-Merging: Resolving Interference When Merging Models | Semantic Scholar](https://www.semanticscholar.org/paper/TIES-Merging:-Resolving-Interference-When-Merging-Yadav-Tam/2651f0179874bd010f58d2c9fa7d118807c80977) - This paper proposes a method, TRIM, ELECT SIGN&MERGE (TIES-Merging), which introduces three novel st...

7. [Language Models are Super Mario: Absorbing Abilities ...](https://arxiv.org/abs/2311.03099) - L Yu 著 · 2023 · 被引用数: 774 — Language Models are Super Mario: Absorbing Abilities from Homologous Mod...

8. [dare.md](https://huggingface.co/datasets/tbukuai/hf-papers-wiki/raw/0961e6ca813cae3a9d6c621d07b72dba0972c985/sources/dare.md)

9. [論文紹介: Language Models are Super Mario: Absorbing ...](https://qiita.com/hiyoko1729/items/0b3482a3528d7d3347c4) - DAREを既存のモデルマージ手法の前処理として利用することで、パラメータの干渉を軽減し、マージの性能を向上させることができます。 例えば、Task ...

10. [DELLA-Merging: Reducing Interference in Model ...](https://arxiv.org/abs/2406.11617) - PT Deep 著 · 2024 · 被引用数: 80 — In this paper, we propose a new model merging technique, Drop and rEsc...

11. [Merging Models with Fisher-Weighted Averaging | ML Anthology](https://mlanthology.org/neurips/2022/matena2022neurips-merging/) - Averaging the parameters of models that have the same architecture and initialization can provide a ...

12. [Read Wonders: Merging Models with Fisher-Weighted Averaging](https://app.readwonders.com/article/303327-merging-models-with-fisher-weighted-averaging) - Read Wonders: It is shown that Fisher merging is competitive with gradient-based transfer learning a...

13. [[PDF] Dynamic Fisher-weighted Model Merging via Bayesian Optimization](https://aclanthology.org/2025.naacl-long.254.pdf)

14. [MODEL MERGING BY UNCERTAINTY-BASED GRADIENT ...](https://proceedings.iclr.cc/paper_files/paper/2024/file/327b9b8d4e45c3f81568e11ffc505f77-Paper-Conference.pdf)

15. [Fisher Mask Nodes for Language Model Merging](https://web3.arxiv.org/pdf/2403.09891)

16. [[PDF] Combining Domain and Alignment Vectors to ... - OpenReview](https://arxiv.org/pdf/2411.06824v2.pdf)

17. [SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging](https://aclanthology.org/2026.findings-acl.1761/) - Aladin Djuhera, Swanand Ravindra Kadhe, Farhan Ahmed, Syed Zawad, Holger Boche. Findings of the Asso...

18. [SafeMERGE/README.md at main · aladinD/SafeMERGE](https://github.com/aladinD/SafeMERGE/blob/main/README.md) - Code for SafeMERGE (ICLR 2025). Contribute to aladinD/SafeMERGE development by creating an account o...

19. [LED-Merging: Mitigating Safety-Utility Conflicts in Model ...](https://aclanthology.org/2025.acl-long.1055.pdf)

20. [[논문 리뷰] LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint](https://www.themoonlight.io/ko/review/led-merging-mitigating-safety-utility-conflicts-in-model-merging-with-location-election-disjoint) - 이 논문은 LED-Merging이라는 새로운 모델 병합 방법을 제안하여, 모델 병합 과정에서 발생하는 안전성과 유용성 간의 갈등 문제를 해결하고자 합니다. 이 방법은 주로 대규모 ...

21. [[Literature Review] LED-Merging: Mitigating Safety-Utility Conflicts in ...](https://www.themoonlight.io/en/review/led-merging-mitigating-safety-utility-conflicts-in-model-merging-with-location-election-disjoint) - The paper titled "LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-El...

