% ===================================================================
% SST-Merge 改稿版：先行研究を考慮した関連研究 + 提案手法の再構築
% 対象セクション：Section 2（関連研究）および Section 3（提案手法）の主要部分
% ===================================================================

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\section{関連研究}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\subsection{Jailbreak攻撃}
A \emph{Jailbreak attack}~\cite{huang2024trustllm} は，敵対的に設計されたプロンプト $P'$ によってモデルの安全制約を迂回し，有害な出力を誘発する攻撃であり，外部ガードレールによる表層フィルタでは本質的に防ぎきれない場合がある~\cite{zou2023universal, wei2024jailbroken}．

\subsection{モデルマージの基礎}
model mergeは，同一ベースモデルから派生した複数のFine-Tuningモデルのパラメータを統合し，単一モデルとして動作させる技術であり，追加学習なしに能力を合成できる点が実用的である~\cite{yang2024model}．

最も基礎的な枠組みは，モデル間の重みを線形平均するweight averaging（model soup）~\cite{wortsman2022model}と，事前学習重みとの差分（タスクベクトル）を加算するTask Arithmetic~\cite{Ilharco2022EditingMW}である．これらはシンプルで扱いやすい一方，タスク間干渉が生じやすい．この問題に対し，タスクベクトルの疎化（DARE~\cite{yu2024language}），符号衝突の回避（TIES~\cite{yadav2023ties}），重要度に基づく選別（Model Breadcrumbs~\cite{davari2024model}）など，干渉を緩和する発展手法が提案されている．

\subsection{Fisher情報行列を用いたモデルマージ}

\paragraph{FWA（Fisher-Weighted Averaging）~\cite{matena2022merging}.}
モデルマージにFisher情報行列（FIM）を初めて本格的に導入した手法である．ラプラス近似に基づき，各パラメータの重要度を対応するFIM対角成分で近似し，重要なパラメータを優先的に保持する加重平均（FWA）を定式化した：
\begin{equation}
\theta_{\mathrm{merged}} = \left(\sum_i F_i\right)^{-1} \sum_i F_i \theta_i.
\label{eq:fwa}
\end{equation}
FWAはモデル統合時の破滅的忘却を抑制する有効な基礎を与えるが，良性（utility）分布に対するFIMのみを用いるため，安全性（safety）の強化に向けて「どの方向にパッチを注入すべきか」を定式化する枠組みを持たない．

\paragraph{不確実性に基づく勾配整合~\cite{daheim2023model}.}
FWAにおける対角FIM依存は，モデル間の勾配方向のミスマッチを考慮できないという限界を持つ．同手法は予測の不確実性を用いて勾配ベクトルを整合させることでこの問題に対処するが，依然として単一の目的（性能保持）のみを最適化する設計であり，Safety--Utilityの競合という二目的問題には対応していない．

\paragraph{Fisher Mask Nodes~\cite{wan2024fishing}.}
FIMを用いてタスクごとに重要なノード（ニューロン）を特定し，それをマスクとして扱うことでタスク間の干渉を物理的に遮断する手法である．本研究のTop-$k$マスクと形式上類似するが，重要なのはマスクの選別基準である：Fisher Mask NodesはUtility保持のための単一FIMを用いてノードを選ぶのに対し，本手法のマスクは「\emph{良性Fisherによるコストと有害FisherによるGainの比}（安全／有用コスパ）」を基準とする．すなわち同一形式のマスクであっても，目的関数が根本的に異なる．

\paragraph{Fisher-Weighted Median~\cite{drift-median}.}
FWAのような加重平均は，極端なFIM値を持つ外れ値パラメータに挙動が左右されやすいという問題を持つ．同手法はFisher重み付き中央値を採用してロバスト性を向上させるが，Safety--Utilityのジレンマ（Safety Tax）を明示的な最適化問題として扱う枠組みは持っていない．実際，最近の査読では「新規性はFIMとMedianの組み合わせにすぎない」という批判が寄せられており，既存手法の組み合わせという印象を与えやすい設計といえる~\cite{drift-median}．

\paragraph{Dynamic Fisher via Bayesian Optimization~\cite{lee2025dynamic}.}
ベイズ最適化（BO）によりFIMに基づくマージのハイパーパラメータを自動探索する手法であり，手動調整の困難さを解消する．しかし，何を最適化するか（目的関数）は単一タスク性能のままであり，Safety--Utilityの競合を二目的として同時に扱う枠組みには至っていない．

\subsection{Safety--Utilityトレードオフへの取り組み}

近年，LLMにおけるfine-tuningやモデルマージが安全性アライメントを劣化させるという問題（Safety Tax / Alignment Tax）が注目されている~\cite{qi2023fine, chen2025fundamental}．以下では，このトレードオフに直接取り組む先行研究を概観する．

\paragraph{Domain \& Alignment Vectors~\cite{bhatt2024domain}.}
ドメイン特化タスクベクトルと，安全性維持のためのアライメントベクトルを別々に抽出し，線形結合することでSafety--Utilityのトレードオフを制御しようとする手法である．本研究と方向性が近いが，結合はスカラー係数による全体的な比例制御に留まり，パラメータごとに「Safetyへの貢献度とUtilityへのダメージ」を計量する枠組みを持たない．

\paragraph{LED-Merging~\cite{yang2025led}.}
SafetyパッチとUtilityパッチをマージする際，同一パラメータ座標での衝突（Conflict）が性能劣化を引き起こすという問題を，Location・Election・Disjoint（LED）の3段階処理で解決する手法である．SafetyとUtilityの競合を直接扱う点で本研究と近い問題設定を持つが，その解法は「衝突を回避する」という消極的（排他的）アプローチであり，「コストを一定以下に抑えながらGainを最大化する」積極的な最適化ではない．排他的な処理（Disjoint）は，「SafetyもUtilityも同一座標で改善できる」可能性を原理的に排除してしまう．

\paragraph{SafeMERGE~\cite{ghosh2025safemerge}.}
fine-tuningやマージによって安全性アライメントが失われるという問題に対し，各層（Layer）が安全性に寄与する度合いを定量化し，「安全性に重要な層」を選択的に保護しながらマージする手法である．層別の選択的制御という考え方は本研究の層別重み（layer prior）と類似した動機を持つが，同手法は粒度が「層」単位であり，パラメータ単位で「安全／有用コスパ」を計量する枠組みは持たない．また，同手法はfine-tuningによって失われた安全性の回復を主な用途とし，本研究のように新たなSafetyパッチを積極的に注入するSecure Mergeシナリオとは想定が異なる．

\paragraph{AlignMerge~\cite{shi2025alignmerge}.}
FIMの幾何学的な等高線をアライメント保護の制約として導入し，その制約を満たす範囲でマージを実行する手法である．本研究と同様にFIMを幾何学的な道具として活用する点で最も接近した関連手法である．しかし，同手法の設計方針は「アライメントを壊さない（消極的制約）」であり，「どの方向がSafetyに最も効くか」を積極的に定式化・最適化する枠組みを持たない．すなわち，制約が守られた範囲内でのマージ方向の選別に目的関数（Gain最大化）が存在しない．本研究は，これに対して「良性FisherによるTax（コスト）と有害FisherによるGain（利益）の比」を一般化固有値問題（GEVP）として同時に最適化する枠組みを提供する点で，本質的に異なる．

\subsection{Data-Free制約への対応}

\paragraph{Data-Free Layer-Adaptive Merging~\cite{dao2026datafree}.}
FIMの計算には元の学習データが必要だが，実運用ではデータが非公開（Data-Free）な場合が多い．同手法はデータを使わずにFIMを近似し，さらに層ごとに適応的なマージ比率を採用することで，推論性能を維持したData-Free環境でのマージを実現した．本研究のData-Free SSTと同様にデータフリーなFIM近似を志向するが，同手法の近似は理論的な目的関数（Safety vs. Utilityのコスパ最大化）と接続されておらず，ヒューリスティックな層別調整に留まる．本研究では，これを「Full SSTのGEVP理論から導出されたランキングサロゲート」として体系化することで，近似の動機づけを理論的に正当化する．

\subsection{既存手法の本質的限界と本研究の動機}
\label{subsec:motivation}

上記の先行研究を整理すると，Safety--Utilityトレードオフへの取り組みは大きく二つのパラダイムに分類できる．

\begin{enumerate}
    \item \textbf{競合回避パラダイム}（LED-Merging, SafeMERGE）：SafetyとUtilityのパラメータ競合を「排他化」や「層の保護」で回避しようとする防衛的アプローチ．これらは「いかに壊さないか」を設計の中心に置く．
    \item \textbf{制約付き保護パラダイム}（AlignMerge）：FIMを制約として用い，アライメントを保ちながらマージする手法．「壊さない範囲でマージする」という発想であり，「どの方向でSafetyを最大化するか」という目的関数を持たない．
\end{enumerate}

本研究が提案するSST-Mergeは，これらとは本質的に異なる第三のパラダイムを提示する：

\begin{center}
\emph{「利益（Safety Gain）をコスト（Utility Tax）で割った比率を最大化する方向にパッチを注入する」}
\end{center}

この発想を一般化固有値問題（GEVP）として定式化することで，ヒューリスティックを排した理論的な最適性が保証される．具体的には，良性データ分布に対するFisher $F_b$（Utilityを壊す度合い）と有害データ分布に対するFisher $F_h$（Safetyに効く度合い）をそれぞれコストと利益の計量として用い，その比（安全／有用コスパ）が最大になる方向を数学的に特定する．既存手法がいずれもこの定式化に至っていない理由は，単一のFIMのみを使用する（FWA, AlignMerge等）か，あるいはFIMを全く用いないか（LED, SafeMERGE等）に留まっているためである．

さらに，Full FIMの計算が現実的でない場合の実装戦略として，対角近似（Diagonal SST）とデータフリー近似（Data-Free SST）を「同一のGEVP理論の制約緩和」として体系的に導出する．これにより，Data-Free Layer-Adaptiveのようなヒューリスティックな近似とは異なり，近似の動機づけを理論的に正当化できる．
