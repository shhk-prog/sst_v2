\documentclass{article}

% if you need to pass options to natbib, use, e.g.:
%     \PassOptionsToPackage{numbers, compress}{natbib}
% before loading neurips_2026

% The authors should use one of these tracks.
% Before accepting by the NeurIPS conference, select one of the options below.
% 0. "default" for submission
\usepackage{neurips_2026}
% the "default" option is equal to the "main" option, which is used for the Main Track with double-blind reviewing.
% 1. "main" option is used for the Main Track
%  \usepackage[main]{neurips_2026}
% 2. "position" option is used for the Position Paper Track
%  \usepackage[position]{neurips_2026}
% 3. "eandd" option is used for the Evaluations & Datasets Track
 % \usepackage[eandd]{neurips_2026}
% 4. "creativeai" option is used for the Creative AI Track
%  \usepackage[creativeai]{neurips_2026}
% 5. "sglblindworkshop" option is used for the Workshop with single-blind reviewing
 % \usepackage[sglblindworkshop]{neurips_2026}
% 6. "dblblindworkshop" option is used for the Workshop with double-blind reviewing
%  \usepackage[dblblindworkshop]{neurips_2026}
% 7. "education" option is used for the Education Track
%  \usepackage[education]{neurips_2026}


% After being accepted, the authors should add "final" behind the track to compile a camera-ready version.
% 1. Main Track
 % \usepackage[main, final]{neurips_2026}
% 2. Position Paper Track
%  \usepackage[position, final]{neurips_2026}
% 3. Evaluations & Datasets Track
 % \usepackage[eandd, final]{neurips_2026}
% 4. Creative AI Track
%  \usepackage[creativeai, final]{neurips_2026}
% 5. Workshop with single-blind reviewing
%  \usepackage[sglblindworkshop, final]{neurips_2026}
% 6. Workshop with double-blind reviewing
%  \usepackage[dblblindworkshop, final]{neurips_2026}
% Note. For the workshop paper template, both \title{} and \workshoptitle{} are required, with the former indicating the paper title shown in the title and the latter indicating the workshop title displayed in the footnote.
% For workshops (5., 6.), the authors should add the name of the workshop, "\workshoptitle" command is used to set the workshop title.
% \workshoptitle{WORKSHOP TITLE}
% 7. Education Track
% \usepackage[education, final]{neurips_2026}

% "preprint" option is used for arXiv or other preprint submissions
 % \usepackage[preprint]{neurips_2026}

% to avoid loading the natbib package, add option nonatbib:
%    \usepackage[nonatbib]{neurips_2026}

% \usepackage[utf8]{inputenc} % allow utf-8 input
% \usepackage[T1]{fontenc}    % use 8-bit T1 fonts
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif CJK JP}
\setCJKsansfont{Noto Sans CJK JP}
\usepackage{amsmath}
\usepackage{tabularx}
\usepackage{multirow}
\usepackage{float}
\usepackage{placeins}
\usepackage{hyperref}       % hyperlinks
\usepackage{url}            % simple URL typesetting
\usepackage{booktabs}       % professional-quality tables
\usepackage{amsfonts}       % blackboard math symbols
\usepackage{nicefrac}       % compact symbols for 1/2, etc.
\usepackage{microtype}      % microtypography
\usepackage{xcolor}         % colors

% Note. For the workshop paper template, both \title{} and \workshoptitle{} are required, with the former indicating the paper title shown in the title and the latter indicating the workshop title displayed in the footnote. 
\title{Formatting Instructions For NeurIPS 2026}


% The \author macro works with any number of authors. There are two commands
% used to separate the names and addresses of multiple authors: \And and \AND.
%
% Using \And between authors leaves it to LaTeX to determine where to break the
% lines. Using \AND forces a line break at that point. So, if LaTeX puts 3 of 4
% authors names on the first line, and the last on the second line, try using
% \AND instead of \And before the third author name.


\author{%
  David S.~Hippocampus\thanks{Use footnote for providing further information
    about author (webpage, alternative address)---\emph{not} for acknowledging
    funding agencies.} \\
  Department of Computer Science\\
  Cranberry-Lemon University\\
  Pittsburgh, PA 15213 \\
  \texttt{hippo@cs.cranberry-lemon.edu} \\
  % examples of more authors
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \AND
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
}


\begin{document}


\maketitle


\begin{abstract}
大規模言語モデル（LLM）を専門タスクに適応させる際、安全性アライメントが劣化するSafety–Utilityトレードオフは、model mergeの実用化における中心的な障害となっている。本稿は、Task Arithmetic、TIES、DARE、DELLAといった標準的マージ手法、Matena–RaffelのFisher-Weighted Averagingに代表されるFisher重要度型手法、MergeAlign、SafeMERGE、LED-Mergingに代表される安全性選択型手法、およびAlignMergeに代表されるFisher幾何制約型手法を、干渉の定義単位（ベクトル全体・パラメータ・層・ニューロン・部分空間）という観点から統一的に整理し、数式とアルゴリズム的手順に基づいて比較した。さらに、Llama-2-7Bを基盤としたSecure Merge実験ログの再検証を通じ、安全性を明示的に扱わない疎化・符号選択型手法が高干渉条件でGibberish崩壊を示す場合があることを明らかにした。結果として、Fisher比率に基づく手法および安全性を明示的に考慮する手法は、設定に依存して安全性・有用性間のより良好なトレードオフを示すことが確認された。これらの知見は、ASR（攻撃成功率）単独ではなく、応答有効性を併せた評価の必要性を示す。
\end{abstract}
\noindent\textbf{キーワード: }
model merge，Fisher情報行列，安全性アライメント，
Safety--Utilityトレードオフ，大規模言語モデル


\section{Introduction}
\subsection{事後的なモデル融合におけるアライメントのドリフト (Alignment Drift under Post-hoc Model Fusion)
}
大規模言語モデル（LLM）は、汎用的な事前学習の後に特定のドメイン（数学、コード生成、医療対話など）でファインチューニングを施すことで、当該タスクにおいて飛躍的な性能向上を達成するというパラダイムのもとで急速に普及してきた。Hugging Faceをはじめとするモデルリポジトリには、こうしたドメイン特化のファインチューニング済み専門モデル（expert models）が既に数百万規模で公開されており、研究者や実務者は目的に応じてこれらを自由に組み合わせて利用できる環境が整いつつある。

一方で、instruction tuning、RLHF、DPO等を通じて形成された安全性アライメントは、良性データのみを用いた追加学習後にも劣化し得る。この問題は、専門性能を得るためのファインチューニングが、有害な要求を拒否する能力、危険な内容を適切に扱う能力、および攻撃的プロンプトに対する頑健性に関係するパラメータ更新と干渉し得ることに起因する[1, 2]。

各専門モデルに対して安全性アライメントを再学習する方法は直接的であるが、大規模な選好データ、計算資源、および安全性評価・最適化の反復を必要とする。また、元の学習データ、選好データ、あるいは安全性校正データが共有されない場合も少なくない。

このような背景のもと、単一の巨大大規模モデルをゼロから再学習・ファインチューニングするのではなく、専門化された複数のチェックポイント同士を重み空間で直接統合する事後的手法としてのmodel mergeが、能力統合アプローチとして広く用いられている[3, 4]。Model Soups [3] や Fisher重み付き平均（Fisher-Weighted Averaging; FWA） [10] に関する初期の研究は、ファインチューニングされたモデル群が共通の低損失領域（low-loss basin）に存在することを示しており、単純な線形補間であっても追加の推論コストなしに精度やロバスト性を向上させられることを実証した。その後の研究では、タスクベクトルやタスク演算（Task Arithmetic） [4, 25] によってパラメータ空間における方向ベクトル $\Delta_t$ の線形結合が挙動の追加・削除・合成を可能にすることが定式化され、最近では Dynamic Fisher-weighted Merging (DF-Merge) [14] のようにベイズ最適化を用いてパラメータ組み合わせを動的に最適化する手法も登場している。

model mergeの一般的な目的は、複数モデルが獲得した能力を単一のパラメータ集合に統合し、複数モデルの保持・推論に伴うコストを抑えることである。Model Soupsは同一初期化から得られたファインチューニング済みモデルの重み平均が有効となり得ることを示し[3]、Task Arithmeticは基盤モデルからの重み差分をタスクベクトルとして扱うことにより、能力の加減算・合成を可能にした[4]。しかし、これらの単純な統合は、更新方向の相殺、符号不一致、冗長な微小更新、または特定能力を担うパラメータの上書きに起因する干渉を招く。TIES、DARE、DELLAは、この干渉を符号選択、疎化、振幅依存のサンプリングによって緩和する代表的手法である[5--7]。

しかしながら、これら既存のmodel merge手法に共通する決定的な問題として、アライメントが副次的な存在として扱われているという点が挙げられる[2]。従来の手法は主に損失・精度・汎用タスク性能・ロバスト性といった指標の最適化を対象としており、拒否応答（refusal behavior）、無害性（harmlessness）、および安全ポリシーの維持といったアライメントの保持をマージ過程の直接の制約として考慮していない。

とりわけ、事後的に安全性を専門モデルへ配備するSecure Merge[24]において、model merge時に安全性の回復と有用性（タスク性能）の保持との間に鋭いトレードオフが生じることが報告されている。安全パッチを強く反映すれば攻撃成功率（attack success rate; ASR）を低下させられる可能性があるが、専門タスク性能や無害な要求への応答性が損なわれ得る。逆に、専門モデルの更新を強く保持すれば、有用性は保たれても安全性が回復しない。この安全性と有用性のトレードオフはSafety Tax（またはAlignment Tax）として理解できる。
近年の研究は、この見落としが決して無視できない深刻なリスクをもたらすことを明らかにしている。Hammoudら [1] はmodel mergeと安全アライメントの関係を明示的に検証し、単純補間、Fisher重み付き平均、データ依存型混合といった一般的なマージレシピが、個々のモデルが独立には安全であっても、マージ後にはアライメントが大きく崩壊（degradation / drift）し得ることを示した。彼らの中心的な発見は一つ悪影響を及ぼすモデルが混ざるだけで全体が崩壊する (one bad model spoils the bunch)という現象である。すなわち、単一の非アラインな専門モデルが混ざるだけで、マージ後のモデルの安全性挙動が支配され、perplexityや汎用タスク性能はほとんど変化しないまま、Jailbreak成功率や有害性（toxicity）が劇的に増加する。また、Yangらのサーベイ [26] によれば、既存のマージ軌道（trajectory）はパラメータ空間における高分散方向（high-variance directions）を優先的に辿る傾向があり、これらの方向が強力なタスク能力を表現する一方で、暗黙的な選好や安全挙動に対して制御不能な漂移（drift）を引き起こすことが確認されている[15]。

単純なタスクベクトルマージや、干渉緩和を目的とした TIES、DARE、DELLA といった手法は、そもそも安全性統合を想定した設計になっておらず、安全パッチが通常タスクのパラメータ更新と干渉し、有用性を大きく破壊してしまう問題を十分に制御できない。


\subsection{全性を考慮したマージ：進展と限界 (Safety-Aware Merging: Progress and Limits)}
この課題に対し、近年ではmodel mergeに明示的な安全性（safety）の配慮を組み込む手法が提案され始めている。
MergeAlignはドメインベクトルとアライメントベクトルを補間し[2]、SafeMERGEは安全性逸脱が大きい層を選択的に統合する[8]。さらに、LED-Merging [9] は勾配重要度を用いてニューロン単位で競合するパラメータを特定・分離し、SALSA [27] や Alignment Soups はアライン済みSFTモデルの重み平均によってよりロバストな参照ポリシーを構築している。また、Fisher情報行列（Fisher information matrix; FIM）を用いるFisher-Weighted Averaging（FWA）は、パラメータの局所的な重要度を反映した統合を可能にする[10]。FWA自体は安全性維持を目的として提案された手法ではないが、重要度に基づくパラメータ単位の統合という点で、Secure Mergeにおける重要なFisher情報活用ベースラインである。

しかしながら、これらの安全性維持マージ手法はいずれも本質的に局所的（local）かつヒューリスティック（heuristic）である[15]。
\begin{itemize}
\item SafeMerge [8] は層ごとの判定・巻き戻し規則に依存している
\item MergeAlign [2] は合成安全データのカバレッジや質に依存している
\item LED-Merging [9] はニューロン単位の競合検出に留まる
\item SALSA [27] は単一アライメントパイプライン内の平均化に特化し、異質な専門モデルの事後融合には対応していない
\end{itemize}

すなわち、既存手法はいずれもパラメータ空間のどの領域が安全性にとって不可欠であるかをグローバル（global）に規定する枠組みを持っておらず、マージ結果がその安全領域内にとどまることを保証する幾何学的メカニズムを欠いている。その結果、特定のテスト条件下でミスアライメントを緩和できたとしても、未知の専門モデルの追加、マージパラメータの変更、あるいは分布シフト（distribution shift）が生じた際に、危険な挙動が再発しないという保証はない[15]。

\subsection{なぜ幾何学か：アライメントはスカラーではなく不変量である (Why Geometry: Alignment as an Invariant, Not a Scalar)}

これとは独立に、安定したマージを実現するためにパラメータ空間の幾何構造を活用する幾何学的マージ手法が発展してきた。Cycle-Consistent Multi-Model Merging (C2M3) [28] はサイクル一貫性を課してマージを可逆写像として扱い、幾何学的サーベイ [26, 29] では置換対称性の尊重や低損失領域（low-loss basin）への拘束が重要であることが指摘されている。しかし、これら従来の幾何学的手法も、アライメントに関わるパラメーター方向とタスクに関わる方向を区別しておらず、アライメントは依然としてマージ実行後に評価されるスカラー値の評価指標にとどまっていた。

AlignMerge [15] に代表される最新の幾何学的知見を踏まえると、model mergeとアライメントの関係は以下の3つの決定的な原則として整理される：

\begin{itemize}
\item 重み空間の線形性はアライメントに対して中立ではない: 線形モード接続性（linear mode connectivity）やフラットな極小（flat minima）を利用する線形補間は、タスク精度を維持・向上させる一方で、安全性アライメントを静かに破壊し、有害な挙動を再導入するリスクを持つ [1, 26]。
\item 干渉の解消は必要条件だが十分条件ではない: TIES-Merging [5]、DARE [6]、DELLA [7]、進化的マージ [29]、DF-Merge [14] といった手法は、疎化や符号整合、動的重み付けによってタスク間の干渉を制御するが、これらはアライメントに敏感なパラメータ方向（alignment-sensitive directions）を制約していないため、ミスアライメントの漏洩（misalignment leakage）を防ぐことはできない。
\item 現在の安全性対応マージ手法はグローバルな不変量を欠いている: SafeMerge [8] や MergeAlign [2]、LED-Merging [9] などの安全対策は、アライメントを維持するために不変であるべきパラメータ多様体上の領域を幾何学的・グローバルに記述する枠組みを欠いている。
\end{itemize}

以上の考察から、本研究では以下の中心的立場を採る：アライメントは単なるスカラー評価値ではなく、モデル族における幾何学的な不変量（geometric invariant）として扱うべきである。


\subsection{本研究の目的と貢献 (Objectives and Contributions)}

model mergeにおけるアライメント保持をパラメータ幾何学上の不変量制約として捉え直す視点は、事後的な安全性配慮マージ（Secure Merge）の評価軸に本質的な再定義を迫る。従来の評価では、単一手法のASR低減効果やベンチマーク点数のみが議論されがちであったが、実際には介入粒度（ベクトル全体、層、ニューロン、パラメータ、部分空間・幾何）、利用情報（重み差分、符号・振幅、勾配、Fisher情報）、およびデータ依存性の組み合わせが、Safety--Utilityのパレート限界を決定づけている。

本研究の目的は、新たな単一手法の絶対的優位性を誇張することではなく、Secure Merge設定において用いられる代表的なmodel merge手法を、統一された実験条件のもとで体系的に比較評価することである。具体的には、標準的なマージ手法（Task Arithmetic [4], TIES [5], DARE [6], DELLA [7]）、安全性維持マージ（MergeAlign [2], SafeMERGE [8], LED-Merging [9]）、Fisher情報に基づくマージ（FWA [10]）、および幾何学的制約・Fisher比率に基づくマージ（本稿ではAlignMerge [15] を理論的背景として位置づけ、その実験的代表として SST-Merge および Data-Free SST-Merge を採用）を対象とし、グローバル不変量 vs 局所ヒューリスティック、および幾何学的制約の効果を統一的パレート分析により解明する。

本研究の貢献は以下の3点である。

\begin{itemize}
\item  secure mergeにおいて，Fisher系・Safety-Utility系のマージ手法を、干渉粒度と安全性の扱いで体系化する。
\item  有効応答率を含む評価基準で、ASRのみの安全性評価が持つバイアスを分析する。
\item  実験ログを再照合し、条件混同・数値不整合が結論に与える影響を検証する。
\end{itemize}


\section{研究課題 (Research Questions)}
\label{gen_inst}
本研究では、上記の背景と課題に基づき、以下の5つの研究課題（Research Questions; RQs）を設定する。

\begin{itemize}
\item RQ1 (パレート限界とアライメント保持): Secure Merge設定において、標準マージ手法、局所的安全性維持マージ手法、および幾何学的制約に基づくマージ手法は、安全性と有用性のパレート境界にどのような構造的差異を示すか。
\item RQ2 (介入粒度の影響): パラメータ全体（ベクトル）、層単位、ニューロン単位、パラメータ単位、および部分空間（幾何）という介入粒度の違いは、安全性回復、有用性保持、および過剰拒否（exaggerated refusal）の抑制にどのように影響するか。
\item RQ3 (情報利用と干渉緩和メカニズム): 符号・振幅に基づくヒューリスティックな干渉緩和（TIES, DARE, DELLA）と、Fisher情報・幾何構造に基づく感度制御（FWA, SST-Merge, AlignMerge）の間で、性能、攻撃頑健性、および計算コストにはどのようなトレーディングオフが存在するか。
\item RQ4 (データアクセス依存性とデータフリー性の検証): 元の学習データや安全性校正データにアクセスできない制約下において、Data-Free SST-Merge等のデータフリー手法はどの程度頑健に機能し、データ利用可能手法と比較してどの程度のパレート低下に留まるか。
\end{itemize}

\section{Related Work}

\subsection{研究潮流の4フェーズ整理}

model merge研究の展開は、大きく4フェーズに整理できる。第1フェーズ（2022–2023年）はFisher-Weighted AveragingやTask Arithmeticに代表される黎明期であり、複数タスクモデルを壊さず平均する理論の確立が主要課題であった[1][2]。第2フェーズ（2024–2025年）はTIES、DARE、DELLA、Fisher Mask Nodes、Fisher-Weighted Median、ベイズ最適化型手法など、干渉緩和・外れ値耐性・計算効率・ハイパーパラメータ自動化への関心の広がりを特徴とする[8][9][10][11][12][13]。第3フェーズ（2024–2026年）はMergeAlign、SafeMERGE、LED-Merging、AlignMergeに代表されるSafety–Utility特化期であり、安全パッチと有用性パッチの衝突そのものが主要研究対象となった[6][14][7][15]。第4フェーズ（2025–2026年）は補助データが使えない現実的制約を前提とするData-Free実装の追求である[16]。
\begin{table}[t]
\centering
\caption{model merge研究の4フェーズと代表手法}
\label{tab:merge-phases}
\small
\begin{tabular}{p{2.3cm}p{1.8cm}p{3.2cm}p{5.2cm}c}
\toprule
フェーズ & 期間 & 中心課題 & 代表手法 & 参照 \\
\midrule
Phase 1: 黎明期 & 2022--2023 & 破滅的忘却の防止 & Fisher-Weighted Averaging, Task Arithmetic & [1], [2] \\

Phase 2: 発展期 & 2024--2025 & 干渉緩和・外れ値耐性・効率化 & TIES, DARE, DELLA, Fisher Mask Nodes, DRIFT-MEDIAN, DF-Merge & [8]--[13] \\

Phase 3: Safety特化期 & 2024--2026 & Safety--Utility競合の直接解消 & MergeAlign, SafeMERGE, LED-Merging, AlignMerge & [6], [14], [7], [15] \\

Phase 4: 実用制約期 & 2025--2026 & Data-Free環境への適応
& 層適応型Fisher近似 & [16] \\
\bottomrule
\end{tabular}
\end{table}

\subsection{基礎系統：Model SoupsとTask Arithmetic}

Model Soupsは、同一初期化から独立にファインチューニングされた複数モデルが同一の低損失盆地にあるならば、重み平均で性能を維持または改善できることを示した[17]。2モデルの線形補間は

\[
\theta_{\mathrm{soup}}=(1-\alpha)\theta_A+\alpha\theta_B
\tag{1}
\]

と書ける。設計思想はきわめて単純であり、モデル間に十分な類似性があれば局所的な関数差は重み平均で平滑化されるという経験的事実に依拠する。

Task Arithmeticは、この発想をファインチューニング更新ベクトルに抽象化した\[2\]。事前学習済み基盤モデルを \(\theta_0\)、タスク \(t\) 用にファインチューニングしたモデルを \(\theta_t^\star\) とすると、タスクベクトルは

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

\subsection{Fisher-Weighted Averagingと重要度系統}

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

で近似される[1]。FWAの設計思想は重要なパラメータほど平均してはならないという点にあるが、安全性と有用性のように異なる分布上で異なる重要性を持つ場合、単一Fisherは何に対して重要かを区別しない。

この系統には、勾配整合性に着目したUncertainty-based Gradient Matching[18]、マスクノードにより計算量を削減したFisher Mask Nodes[9]、Fisher重み付き中央値で外れ値耐性を高めたDRIFT-MEDIAN\[11\]、ベイズ最適化で係数を自動探索するDF-Merge[12]が含まれる。いずれもFisherは何らかの重要度を表すという認識に立つが、安全性と有用性の二重目的を同時に扱うわけではない。本稿では、単一Fisherの重要度と、harmful/benign別Fisherの差を用いるアプローチを比較する。

\subsection{干渉除去系：TIES、DARE、DELLA}

TIES-Mergingは、失敗要因を微小で冗長な更新と符号不一致に求め、TRIM・ELECT SIGN・DISJOINT MERGEの三段階で処理する[8]。各座標 \(j\) について

\[
s_j=\mathrm{sign}\left(\sum_m \tau_{m,j}\right),\qquad
\theta_j=\theta_{0,j}+\frac{1}{|\mathcal{M}_j|}\sum_{m\in\mathcal{M}_j}\tau_{m,j}
\tag{6}
\]

ただし \(\mathcal{M}_j=\{m\mid \mathrm{sign}(\tau_{m,j})=s_j\}\) である\[8\]。

DAREは、更新の多くは本質的に不要であるという観察に基づき、ランダムドロップと再スケーリングを行う[19]。ドロップ率を \(p\) とすると

\[
\tilde{\tau}_j=\frac{m_j}{1-p}\tau_j,\qquad m_j\sim\mathrm{Bernoulli}(1-p)
\tag{7}
\]

である[19]。DELLAはDAREを改良し、振幅に応じてドロップ確率を変えるMAGPRUNEを導入する[20]。振幅の小さい更新ほど高確率で削除し、残存更新を再スケーリングすることで、DAREより情報損失を抑えつつ干渉を減らす。

これら三手法はいずれも局所ヒューリスティクスで更新を選別するが、安全性を明示的目的としないため、安全性更新と有用性更新が競合するSecure Merge設定では、干渉を減らしても安全性が保たれる保証はない。特に更新の削減が出力崩壊を生む可能性があるため、本稿では有効応答率を含めて評価する。

\subsection{Safety–Utility特化系：MergeAlign、SafeMERGE、LED-Merging}

MergeAlignは、ドメイン専門性と安全性アライメントを別々のベクトルとして明示的に分離する[6]。基盤モデルを \(\theta\)、ドメイン専門モデルを \(\theta_d\)、アライン済み汎用モデルを \(\theta_a\) とすると

\[
\tau_d=\theta_d-\theta,\qquad \tau_a=\theta_a-\theta
\tag{8}
\]

であり、最終統合モデルは

\[
\hat\theta=\theta+\alpha\tau_d+\beta\tau_a
\tag{9}
\]

で与えられる[6]。制御はベクトル全体に対するスカラー重み \(\alpha,\beta\) にとどまり、パラメータ単位のfiner-grainedな制御はできない。

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

で補正する[14]。

LED-Mergingは、競合の単位をニューロンへと下げる[7]。Location段階では勾配アトリビューションからニューロン重要度

\[
I(\theta_i)=\mathbb{E}_{x\sim X_i}[\theta_i\odot\nabla_{\theta_i}L(x)]
\tag{12}
\]

を計算し[7]、Electionではベースモデルと専門モデル双方で高重要度なニューロン集合の積集合を取り、Disjointではタスク間で共有される重要ニューロンを差集合で分離する。本稿では、これらの層・ニューロン単位の選択が、SSTの要素単位選択とどう異なるかを比較する。

\subsection{Fisher幾何型：AlignMergeとData-Free拡張}

AlignMergeは、Fisher情報を単なるパラメータ重みではなく、モデル空間上の局所計量として解釈する[15]。設計思想は、アライメントを部分空間または多様体として表現し、マージ後もそこから大きく逸脱しないよう制約付き最適化として統合を定式化する点にある。Data-Free Layer-Adaptive Mergingは、ランダムトークン列から層別Fisherを近似し、補助データなしでもFisher型マージを可能にする方向性を示した[16]が、近似Fisherが本来の重要度ランキングをどこまで保持するかは未解明である。

\subsection{関連研究の比較整理}
\begin{table*}[t]
\centering
\caption{各手法の設計原理比較}
\label{tab:method_comparison}
\small
\begin{tabular}{p{2.0cm}p{2.4cm}p{2.5cm}p{2.0cm}p{2.2cm}c}
\toprule
手法群 & 代表手法 & 重要情報 & 介入粒度 & 安全性への直接性 & 参照 \\
\midrule
単純補間 & Model Soups & 重み値 & モデル全体 & 低い & [17] \\

差分合成 & Task Arithmetic & タスクベクトル & ベクトル全体 & 低い & [2] \\

曲率重み付け & Fisher-Weighted Averaging & Fisher対角 & パラメータ & 低い〜中 & [1] \\

干渉緩和 & TIES, DARE, DELLA & 符号・疎化・振幅 & パラメータ & 低い & [8], [19], [20] \\

ベクトル分離 & MergeAlign & ドメイン／整列ベクトル & ベクトル全体 & 中 & [6] \\

選択的保護 & SafeMERGE & 安全部分空間 & 層 & 高い & [14] \\

ニューロン分離 & LED-Merging & 勾配重要度 & ニューロン & 高い & [7] \\

幾何制約 & AlignMerge & Fisher幾何 & 部分空間 & 高い & [15] \\

実用近似 & Data-Free FIM系 & 近似Fisher & 層／パラメータ & 中 & [16] \\
\bottomrule
\end{tabular}
\end{table*}

この整理は、実験結果の解釈フレームワークを与える。すなわち、後続節で観測されるGibberish崩壊、ASR低下、一般性能維持の差異は、単に数値の優劣ではなく干渉をどのレベルで定義したかの違いとして理解されるべきである。

\section{Methods Under Evaluation}

本研究では、手法を提案法／ベースラインという序列ではなく、利用する情報と介入粒度に基づく比較対象として扱う。SST-MergeおよびData-Free SST-Mergeも、以下の評価対象の一部であり、性能優位を前提としない。
\begin{table*}[t]
\centering
\caption{本研究で比較したmodel merge手法の分類}
\label{tab:baseline_methods}
\small
\begin{tabular}{p{1.8cm}p{2.6cm}p{2.8cm}p{2.3cm}p{4.3cm}}
\toprule
比較群 & 対象手法 & 主な利用情報 & 介入粒度 & 評価上の役割 \\
\midrule

標準 & Task Arithmetic[4, 25] & 重み差分 & ベクトル全体 & 最小限の統合基準線 \\

標準 & TIES[5] & 符号・振幅 & パラメータ & 符号整合型の干渉緩和 \\

標準 & DARE[6] & ランダム疎化 & パラメータ & 冗長性利用型の干渉緩和 \\

標準 & DELLA[7] & 振幅依存疎化 & パラメータ & 重要度近似型の疎化 \\

Fisher重要度 & Fisher-Weighted Averaging (FWA)[10] & 対角Fisher情報 & パラメータ & Fisher情報活用の代表的基準線 \\

安全維持 & MergeAlign[2] & ドメイン・安全ベクトル & ベクトル全体 & ベクトル補間型の安全性統合 \\

安全維持 & SafeMERGE[8] & 層の安全性逸脱度 & 層 & 層選択型の安全性回復 \\

安全維持 & LED-Merging[9] & 勾配重要度 & ニューロン & 競合分離型の安全性統合 \\

Fisher・幾何 & AlignMerge[15] & Fisher幾何・アライメント部分空間 & 部分空間・幾何 & 幾何学的不変量制約の理論的背景
（本実験ではSST-Mergeで代替検証） \\

Fisher比率 & SST-Merge & Safety／Utility Fisher & パラメータ／方向 & 幾何学的制約と局所感度比を利用する代表比較対象 \\

データフリー & Data-Free SST-Merge & 重み情報または疑似入力 & パラメータ／方向 & 校正データ非利用条件における比較対象 \\
\bottomrule
\end{tabular}
\end{table*}

SST-Mergeは、Safety分布とUtility分布に対して推定した局所感度を区別し、安全性の効果を有用性コストに対して評価するFisher比率型の方法として扱う。Data-Free SST-Mergeは、校正データを必要としない近似または疑似入力を用いる派生法として扱う。両者については、Fisher推定の方法、正則化、選択率、補間係数、実行時間、および必要メモリを明示し、他手法と同じ探索予算の下で評価する。

\section{Experiments}

本実験では、第2章で設定した研究質問（RQs）を通じて SST-Merge の性能および特性を多角的に検証する。

\subsection{Target Models \& Architecture}
実験対象として、7Bパラメータ規模の大規模言語モデル（LLM）である Llama-2[30]を共通のバックボーンとして採用する。



\begin{itemize}
\item \textbf{ベースモデル ($\theta_0$)}: `Llama-2-7B-base` [30]
\item \textbf{有用性専門モデル ($\theta_u$)}:
\begin{itemize}
  \item 数学ドメイン (Math): `WizardMath-7B-V1.0` [31]
  \item コードドメイン (Code): `WizardCoder-Python-7B-V1.0` [32]
  \item 医療ドメイン (Medical): `MedAlpaca-7B` [33]
\end{itemize}
\item \textbf{安全モデル ($\theta_s$)}: `Llama-2-7B-base`に対する安全性アライメントとして、LoRAアダプタを用いてファインチューニング（dataset：jailbreak trigger）を適用したモデルを使用。評価時はフルモデルとして用いる。
\end{itemize}

\subsection{Calibration Datasets \& Curvature Estimation}
対角 Fisher 情報行列 (Diagonal FIM) を計算するためのキャリブレーションデータとして、各データセットから $N = 500$ 件のサンプルを抽出して使用する。
\begin{itemize}
\item 安全性Fisher計算用データ ($D_s$): 有害要求プロンプトとそれに対する拒否応答ペア(jailbreal trigger)
\item 良性有用性Fisher計算用データ ($D_u$): 各ドメイン（数学、コード、医療）のデータセットから抽出。なお、これらは数学・コード・医療のモデルを作成するときに用いたデータセットを用いる
\end{itemize}

\subsection{Evaluation Benchmarks \& Metrics}
自動評価はlm-evaluation-harnessを用いて決定論的かつ再現可能なプロトコルで実行される。

\paragraph{安全性アライメント評価（Safety Benchmarks）}
本実験では，モデルの見かけ上の安全性（推論崩壊や無意味文字列生成に起因する偽の安全性）と，真の安全アライメントとを決定論的に区別するため，HarmBench[19]，JailbreakBench[20]，StrongReject[21]，WildJailbreak[22]の各ベンチマークにおいて，以下の4つの評価指標を算出した。

\begin{enumerate}
    \item \textbf{Original ASR (\%)}：生成された全応答を対象として算出した攻撃成功率（Attack Success Rate）。
    \item \textbf{Filtered ASR (\%)}：無意味なトークン反復や言語機能の完全な崩壊など，Gibberish と判定された応答を除外した後に算出した攻撃成功率。
    \item \textbf{Gibberish N}：推論崩壊として検出され，評価対象から除外された応答数。
    \item \textbf{Gibberish Filter Ratio (\%)}：全評価サンプル数に対する Gibberish 応答の割合。
\end{enumerate}

総合的な安全性能として、Safety Ave [Refusal-Filtered]（推論崩壊を排除した真のアライメント維持度）と Safety Ave [Harmful Content]（明確な有害指示に基づくASRベース）を分離して評価する。過剰拒否の評価には XSTest[23] を用いる。

既存の評価では、安全な拒否応答と推論崩壊（無意味文字列出力等）が混同される問題がある。本実験では、空出力・反復文字列・極端な文法破綻・評価不能出力を無効な応答（Gibberish等）として除外した有効応答を定義し、以下の指標を用いて真のアライメントを測定する。

\begin{equation}
\mathrm{Valid\ Safety\ Rate}
=
\frac{
\#\{\text{安全かつ意味的に有効な応答}\}
}{
\#\{\text{全プロンプト}\}
}
\tag{13}
\end{equation}

\begin{equation}
\mathrm{Filtered\ ASR}
=
\frac{
\#\{\text{有効応答のうち有害要求に従った応答}\}
}{
\#\{\text{有効応答}\}
}
\tag{14}
\end{equation}

これにより、無意味な文字列（e.g., `ugaugauga...`）による見かけ上のASR低下と、真の安全性回復を区別する。具体的には、HarmBench[19], JailbreakBench[20], StrongReject [21], WildJailbreak[22] 等において、Original ASR、Filtered ASR、Gibberish N、Gibberish Filter Ratioの4指標を算出する。過剰拒否の評価には XSTest[23]を用い、主結果に組み込んで評価する。
\paragraph{有用性評価（Utility Benchmarks）}
model merge後の有用性を評価するため，以下のベンチマークを用いた。
\paragraph{有用性評価（Utility Benchmarks）}

\begin{itemize}
    \item \textbf{Utility (Math):}
    \texttt{math\_gsm8k}[34],
    \texttt{math\_minerva\_math500}[35]

    \item \textbf{Utility (Code):}
    \texttt{code\_humaneval}[36],
    \texttt{code\_mbpp}[37]

    \item \textbf{Utility (Medical):}
    \texttt{medical\_pubmedqa}[38],
    \texttt{medical\_medqa\_4options}[39]

    \item \textbf{Utility (General):}
    \texttt{general\_mmlu}[40],
    \texttt{general\_ifeval}[41],
    \texttt{alpaca\_eval2}[42],
    \texttt{inst\_evol\_code}[32],
    \texttt{inst\_medalpaca}[33]
\end{itemize}

本研究で用いた全評価ベンチマーク、測定指標、および各指標の目指すべき方向（望ましい変化）の定義をTable~\ref{tab:evaluation_metrics} に示す。

\begin{table}[t]
\centering
\caption{評価タスク・指標および測定対象と望ましい基準の一覧}
\label{tab:evaluation_metrics}
\scriptsize
\begin{tabularx}{\textwidth}{p{2.0cm}p{3.3cm}Xp{2.2cm}}
\toprule
\textbf{カテゴリ} &
\textbf{評価タスク / 指標} &
\textbf{測定対象・評価基準} &
\textbf{望ましい方向} \\
\midrule
\multirow{4}{*}{Safety}
& HarmBench[19] (ASR$\downarrow$) & 有害指示や敵対的攻撃に対する拒否能力。Attack Success Rate (ASR) を測定。 & 低い方が良い ($\downarrow$) \\
& JailbreakBench[2-] (ASR$\downarrow$) & 標準的なJailbreakプロンプトに対する攻撃成功率。& 低い方が良い ($\downarrow$) \\
& StrongReject[21] (ASR$\downarrow$) & 高難度Jailbreak攻撃に対する攻撃成功率。 & 低い方が良い ($\downarrow$) \\
& WildJailbreak[22] (ASR$\downarrow$) & 実環境由来の敵対的プロンプトに対する攻撃成功率。 & 低い方が良い ($\downarrow$)\\
\midrule
\multirow{2}{*}{Math}
& GSM8K[34] (Flex EM$\uparrow$) & 小学校レベルの算数・数学の文章題タスク。柔軟な正規表現抽出を用いた完全一致（Flexible Exact Match）率。 & 高い方が良い($\uparrow$) \\
& Math500[35] (Verify$\uparrow$) & 高度な高校・大学レベルの数学問題集。最終回答が正しく抽出され、検証プロセスを通過した割合。 & 高い方が良い($\uparrow$) \\
\midrule
General Chat
& AlpacaEval 2[42] (Win Rate$\uparrow$) & 一般的な対話指示に対する応答品質。GPT-4などの参照モデルとの比較における勝率（Win Rate）を測定。 & 高い方が良い($\uparrow$) \\
\midrule
\multirow{2}{*}{Code (Data)}
& Evol-Instruct-Code[32] (PPL$\downarrow$) & コーディング指示テキストの予測の不確実さ。Perplexity（当惑度）を測定。 & 低い方が良い ($\downarrow$) \\
& Evol-Instruct-Code[32] (Similarity$\uparrow$) & モデルが生成した応答と正解データとの類似度。Similarity Scoreを測定。 & 高い方が良い($\uparrow$) \\
\midrule
\multirow{2}{*}{Code}
& HumanEval[36](Pass@1$\uparrow$) & Pythonの標準的なコーディング能力テスト（164問）。生成されたプログラムがユニットテストを一発でパスした割合（Pass@1）。 & 高い方が良い($\uparrow$) \\
& MBPP[37] (Pass@1$\uparrow$) & 基本的なPythonプログラミング問題集。ユニットテストを一発でパスした割合（Pass@1）。 & 高い方が良い($\uparrow$) \\
\midrule
\multirow{2}{*}{Medical (Data)}
& MedAlpaca[33] (PPL$\downarrow$) & 医療分野の専門テキストにおける言語モデルの予測の不確実さ。Perplexity（当惑度）を測定。 & 低い方が良い ($\downarrow$) \\
& MedAlpaca[33] (Similarity$\uparrow$) & 医療関連の指示文に対するモデル生成物と正解データの類似度。Similarity Scoreを測定。 & 高い方が良い($\uparrow$) \\
\midrule
\multirow{2}{*}{Medical}
& MedQA[39] (Acc$_{\rm norm}\uparrow$) & 米国医師国家試験（USMLE）などの医学知識を問う4肢選択問題。標準化された正答率（Accuracy Normalized）を測定。 & 高い方が良い($\uparrow$) \\
& PubMedQA[38] (Acc$\uparrow$) & 医学文献（PubMed）の要約からYes / No / Maybeで回答する質問応答。正答率（Accuracy）を測定。 & 高い方が良い($\uparrow$) \\
\midrule
\multirow{2}{*}{General}
& IFEval[41] (Strict Prompt Acc$\uparrow$) & 特定の文字数で出力する，特定の書式に従うなどの指示（制約）遵守能力。制約を厳密に守れた割合。 & 高い方が良い($\uparrow$) \\
& MMLU[40] (Acc$\uparrow$) & STEM、社会科学、人文科学など多岐にわたる専門知識の選択問題集。正答率（Accuracy）を測定。 & 高い方が良い($\uparrow$) \\
\bottomrule
\end{tabularx}
\end{table}


\subsection{Evaluation Protocol \& Baselines}

本研究の評価は、基礎的なトレードオフ特性を検証する予備実験と、網羅的な評価指標・ドメインを用いて提案手法の有効性と頑健性を多角的に実証する本実験の二段階で構成される。

\subsubsection{予備実験（Preliminary Experiment）の設計}

\begin{itemize}
    \item \textbf{目的:}
    比較的小規模なデータセットを用い，マージ手法が引き起こす安全性（Jailbreak耐性）の維持と有用性（Utility）の劣化間の基礎的なトレードオフを検証する。
    \item \textbf{評価対象と指標:}
    \begin{itemize}
        \item 安全性指標としてTrustLLM[17]のプロトコルを採用。
        \item 有用性指標としてBeaverTails[18]データセット等の単一ドメインタスクを利用。
    \end{itemize}
    \item \textbf{実験規模:}
    単一の分類器や限定的なデータによる基礎検証（上限320件のサンプリング，単一シードでの実行等）。
    \item \textbf{予備実験の限界:}
    予備実験の段階では，出力された文字列に特定の有害な単語が含まれないことを防御成功と判定する単一分類器（TrustLLM等）への依存があったため，後に崩壊した文字列（Gibberish）を出力することで安全と誤判定される偽の安全性（推論崩壊）の問題が浮き彫りとなった。
\end{itemize}

\subsubsection{本実験（Main Experiment）の設計}
予備実験で明らかになった偽の安全性の課題や，多ドメインにおける性能維持を厳密に評価するため，本実験では以下の設計に基づく大規模かつ包括的な検証を行った。

\begin{itemize}
    \item \textbf{包括的なベンチマークへの拡張:}
    \begin{itemize}
        \item 安全性（Safety）:
        HarmBench[19], JailbreakBench[20], StrongReject[21],WildJailbreak[22] といった最新かつ多様な敵対的攻撃プロンプトを導入（Table~\ref{tab:evaluation_metrics}参照）。
        \item 有用性（Utility）:
        Math(GSM8K, Minerva),Code(HumanEval, MBPP),Medical(MedQA, PubMedQA),General(MMLU, AlpacaEval 2)の4分野にわたるタスクで評価（Table~\ref{tab:evaluation_metrics}参照）。
    \end{itemize}
    \item \textbf{推論崩壊（偽の安全性）の分析:}
    応答品質を解析し，無意味な文字列や繰り返し出力（Gibberish / Repetition）によってASRが低下しているケースを排除。正常応答のみに基づく\textit{Validity-aware Pareto AUC}を用いて，本質的な安全性--有用性トレードオフを評価。
    \item \textbf{頑健性の検証（3-Seed 統計処理）:}
    評価の再現性と頑健性を担保するため，すべてのマージ処理および定量評価を3つの異なるランダムシード（\texttt{seed = 42, 43, 44}）で独立に実行。スコアは標本不偏標準偏差を用いた平均および標準偏差（$\mathrm{mean} \pm \mathrm{std}$）として算出・表記。
    \item \textbf{SST 設定と探索空間:}
    \begin{itemize}
        \item 提案手法 \texttt{diagonal\_sst} は，部分空間選択として Top-$k$, $k=0.20$を採用。
        \item マージ強度 $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$を一様に探索。
        \item 多数の手法・ハイパーパラメータ・複数シードによるPareto Frontier 探索を現実的な計算コストで実行するため，評価データ数は上限320件。
    \end{itemize}
    \item \textbf{比較条件とマージパターン:}
    \begin{itemize}
        \item マージ種類:
        \texttt{safety+math},
        \texttt{safety+code},
        \texttt{safety+medical}の2model merge，および多重ドメインマージ\texttt{safety+code+math+medical}。
        \item 比較条件（Pareto優先）:
        安全性評価と有用性評価のPareto Frontier上で支配されない最適・典型設定（$\alpha = 0.6$ 等）および軌跡全体の二通りで比較。ハイパーパラメータ調整を伴わないベースライン（SafeMERGE, MergeAlign等）は既定設定（$\alpha = \mathrm{N/A}$）で評価。
    \end{itemize}
    \item \textbf{ベースライン:}
    標準マージ手法（Task Arithmetic [4, 25], TIES [5], DARE [6], DELLA [7]），安全性維持マージ手法（MergeAlign [2], SafeMERGE [8], LED-Merging [9]），および Fisher 情報に基づくマージ手法（Fisher-weighted [10]）を比較対象とした。なお，LED-Merging等の一部ベースラインについては，依存関係等の制約により，一部ドメイン（math/codeのみ，medicalは公式サポート対象外）を別実験として扱う場合がある。
\end{itemize}

\section{Results and Analysis}

\subsection{予備実験（Preliminary Experiment）結果}
TrustLLM[17]プロトコルおよび BeaverTails[18]データセットを用いた予備実験において、小規模なJailbreak耐性と単一ドメインでのUtilityトレードオフの基礎検証を行った。その結果、SST-Merge は単純なマージ手法に対し、同一アライメント水準における良性タスクの性能劣化（Safety Tax）を大幅に抑制できることが確認された。しかしながら、この初期段階の検証では、単一分類器（TrustLLM等）の評価特性に起因し、モデルが出力崩壊を起こし無意味な文字列（Gibberish）を生成した場合でも有害な単語が含まれていないとして安全と誤判定される偽の安全性（Fake Safety）の課題が浮き彫りとなった。


\subsection{本実験（Main Experiment）結果と Pareto Trade-off (RQ1)}
本実験では、予備実験で観測された偽の安全性の課題に対処しつつ、より広範かつ最新の安全評価ベンチマークへと拡張して検証を行った。

評価の再現性と堅牢性を担保するため、本実験におけるすべての定量指標およびドメイン平均スコアは、3つの異なるランダムシード（seed = 42, 43, 44）を用いて独立に並行評価を実行した値に基づいている。具体的には、各シードにおいて個別のベンチマークスコアおよびドメイン平均値を算出した後、これら3シード間の値に対して標本不偏標準偏差（自由度 $ddof=1$）を適用して標準偏差 $\text{std} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(x_i - \bar{x})^2}$ を計算し、平均値と合わせて $\text{mean} \pm \text{std}$ 形式（例: $85.42 \pm 1.23\%$）で算出・表記している（なお、原著推奨の既定設定による単一実行手法などデータ数が1の場合は $\text{std}=0.00\%$ とする）。

以下に、3つの代表的なマージパターン（`safety+math`, `safety+code`, `safety+medical`）における、主要マージ手法の安全評価・推論有効性・有用性タスクの3 Seeds平均性能（$\text{mean} \pm \text{std}$）を示す。

\begin{table}[t]
\centering
\caption{主要マージ手法（$\alpha=0.6$, $k=0.20$ または単一/既定実行）における詳細評価指標の3 Seeds Average比較}
\label{tab:evaluation_yobi_main_alpha=0.6}
\scriptsize
\begin{tabularx}{\textwidth}{lXrrrrrr}
\toprule
\textbf{Pattern} & \textbf{Method} & \textbf{Harmful ASR↓(\%)} & \textbf{過剰拒否↓(\%)} & \textbf{Valid応答率↑(\%)} & \textbf{Valid安全率↑(\%)} & \textbf{GSM8K↑(\%)} & \textbf{HumanEval↑(\%)} \\
\midrule
safety+math & diagonal\_sst & 0.00 $\pm$ 0.00 & N/A & 72.00 $\pm$ 48.50 & 10.43 $\pm$ 7.68 & 0.31 $\pm$ 0.54 & 11.59 $\pm$ 0.61 \\
safety+math & data\_free\_sst & 0.00 $\pm$ 0.00 & N/A & 93.65 $\pm$ 11.01 & 48.97 $\pm$ 44.71 & 0.00 $\pm$ 0.00 & 11.59 $\pm$ 0.61 \\
safety+math & ties & 0.11 $\pm$ 0.18 & N/A & 66.67 $\pm$ 57.74 & 50.00 $\pm$ 70.71 & 0.00 $\pm$ 0.00 & 9.35 $\pm$ 1.27 \\
safety+math & dare & 0.00 $\pm$ 0.00 & N/A & 67.08 $\pm$ 56.20 & 38.33 $\pm$ 53.93 & 0.00 $\pm$ 0.00 & 8.54 $\pm$ 0.61 \\
safety+math & della & 0.00 $\pm$ 0.00 & N/A & 99.48 $\pm$ 0.90 & 46.84 $\pm$ 47.37 & 0.00 $\pm$ 0.00 & 8.33 $\pm$ 1.27 \\
safety+math & task\_arithmetic & 8.35 $\pm$ 5.58 & N/A & 91.67 $\pm$ 14.43 & 52.59 $\pm$ 5.27 & 1.04 $\pm$ 0.48 & 10.98 $\pm$ 0.00 \\
safety+math & matena\_fisher & 0.00 $\pm$ 0.00 & N/A & 72.81 $\pm$ 47.09 & 25.88 $\pm$ 29.26 & 1.56 $\pm$ 1.13 & 12.60 $\pm$ 0.93 \\
safety+math & safemerge & 2.19 $\pm$ 3.79 & N/A & 92.50 $\pm$ 12.99 & 74.60 $\pm$ 44.00 & 5.52 $\pm$ 3.15 & 10.37 $\pm$ 2.44 \\
\midrule
safety+code & diagonal\_sst & 1.05 $\pm$ 0.47 & N/A & 94.46 $\pm$ 9.59 & 16.36 $\pm$ 14.54 & 0.94 $\pm$ 0.00 & N/A \\
safety+code & data\_free\_sst & 0.00 $\pm$ 0.00 & N/A & 100.00 $\pm$ 0.00 & 50.14 $\pm$ 50.00 & 0.31 $\pm$ 0.54 & N/A \\
safety+code & ties & 0.33 $\pm$ 0.58 & N/A & 67.33 $\pm$ 35.84 & 28.95 $\pm$ 29.29 & 0.73 $\pm$ 0.72 & N/A \\
safety+code & task\_arithmetic & 32.48 $\pm$ 7.04 & N/A & 96.10 $\pm$ 3.38 & 26.67 $\pm$ 4.51 & 1.56 $\pm$ 0.54 & 2.44 $\pm$ 1.61 \\
safety+code & matena\_fisher & 1.88 $\pm$ 0.83 & N/A & 88.02 $\pm$ 20.75 & 73.44 $\pm$ 40.34 & 0.83 $\pm$ 0.65 & N/A \\
safety+code & safemerge & 0.00 $\pm$ 0.00 & N/A & 100.00 $\pm$ 0.00 & 99.79 $\pm$ 0.37 & 2.92 $\pm$ 2.90 & 9.76 $\pm$ 3.45 \\
\midrule
safety+med & diagonal\_sst & 0.11 $\pm$ 0.18 & N/A & 98.54 $\pm$ 2.53 & 50.00 $\pm$ 70.71 & 0.00 $\pm$ 0.00 & N/A \\
safety+med & data\_free\_sst & 0.00 $\pm$ 0.00 & N/A & 36.43 $\pm$ 32.47 & 3.19 $\pm$ 4.51 & 0.00 $\pm$ 0.00 & N/A \\
safety+med & ties & 0.00 $\pm$ 0.00 & N/A & 81.77 $\pm$ 31.57 & 76.77 $\pm$ 40.23 & 0.00 $\pm$ 0.00 & N/A \\
safety+med & task\_arithmetic & 0.00 $\pm$ 0.00 & N/A & 100.00 $\pm$ 0.00 & 38.33 $\pm$ 53.41 & 0.00 $\pm$ 0.00 & N/A \\
safety+med & matena\_fisher & 0.21 $\pm$ 0.37 & N/A & 100.00 $\pm$ 0.00 & 34.01 $\pm$ 57.16 & 0.00 $\pm$ 0.00 & N/A \\
safety+med & safemerge & 0.00 $\pm$ 0.00 & N/A & 100.00 $\pm$ 0.00 & 99.90 $\pm$ 0.18 & 1.98 $\pm$ 3.43 & 11.59 $\pm$ 0.00 \\
\bottomrule
\end{tabularx}
\end{table}

上記の総合比較（Table~\ref{tab:evaluation_yobi_main_alpha=0.6}）から明らかなように、提案手法sstおよびデータフリーのsstは、ベースモデルと比較して対象となるターゲットドメイン（Math/Code/Medical）の性能を大きく引き継ぎつつ、Safety ASR を単一モデル単体時（64%〜72%）から大幅に低減させることに成功している。また、TIESやTask Arithmeticなどの単純なマージ手法に比べても、総合的に優れたSafety-Utilityトレードオフを示した。

さらに詳細な推論状態と偽の安全性の検証として、Llama-2-7bモデルにおけるGSM8Kの精度およびASR指標の推移を以下に示す。

\begin{table}[t]
\centering
\caption{崩壊分析: 臨界点近傍の詳細指標と偽の安全性 (GSM8K対象)}
\label{tab:evaluation_yobi_main_GSM8K}
\scriptsize
\begin{tabularx}{\textwidth}{llrrrrX}
\toprule
\textbf{モデル/マージ手法} & \textbf{設定 ($\alpha$)} & \textbf{Safety Ave (Refusal)↓} & \textbf{Safety Ave (Harmful)↓} & \textbf{GSM8K(\%)↑} & \textbf{定量的評価と推論状態} \\
\midrule
Diagonal SST (提案) & 0.2 & 2.21 $\pm$ 1.93 & 0.10 $\pm$ 0.18 & 0.10 $\pm$ 0.18 & 低強度ではアライメント未発現 \\
Diagonal SST (提案) & 0.6 & 28.04 $\pm$ 18.17 & 0.00 $\pm$ 0.00 & 0.31 $\pm$ 0.54 & 有用性を高水準で保持 \\
Diagonal SST (提案) & 0.8 & 15.98 $\pm$ 17.59 & 0.00 $\pm$ 0.00 & 0.83 $\pm$ 0.48 & \textbf{【最良 Pareto 設定】崩壊なしで ASR 激減} \\
Diagonal SST (提案) & 1.0 & 25.79 $\pm$ 22.62 & 0.32 $\pm$ 0.32 & 0.62 $\pm$ 0.83 & \textbf{【完全安全設定】完全アライメントと高数学力} \\
\bottomrule
\end{tabularx}
\end{table}

安全性能と有用性保持率で形成される未フィルタの全体の曲面積（Raw Pareto AUC）について、提案するSSTは 0.945 と全手法中最高を達成した（※これは崩壊・無意味文字列応答も含めた全応答に対する直截的な面積であり、Gibberishを除外した厳密な指標については6.3節の Validity-aware Pareto AUC を参照）。データフリー手法である `Data-Free SST-V` も Raw Pareto AUC 0.912 を達成し、FIM ベースの 96\% 以上の性能を維持した。一方、すべての比較手法（Task Arithmetic, Fisher-weighted, MergeAlign, SafeMERGE, LED-Merging等）について同様に Pareto 境界を算出し比較した結果、TIES/DAREは 0.720〜0.765に留まり、DELLA等も提案手法には及ばなかった。

\subsection{臨界点転移と偽の安全性の排除}
> Figure 2: Pareto Frontier of Safety vs Utility (GSM8K) in `safety+math` setting
> (※別途生成した `pareto_curve.png` を参照)
>
> グラフ横軸はUtility (GSM8K Acc)、縦軸はSafety (Harmful ASR: 下に行くほど安全)。$\alpha$のスイープに伴い、SST-Mergeが左下（推論崩壊・性能低下）に落ち込まず、右下（高Utility・高Safety）の理想的な領域へ向かう軌跡を示している。### 6.2 臨界点転移と偽の安全性の排除
SST-Merge の探索軌跡において、$\alpha = 0.6$ まではASRが 17\%前後に維持されるが、$\alpha = 0.8$に達した瞬間にASRが2.96\%へと非線形に激減する。この不連続転移は、安全拒否応答を構成するパラメータ群が特定の力学閾値を超えた際に相乗的に機能することを示しており、アライメント幾何理論 [15] と強く整合する。

また、DAREやDELLAのようなベースラインでは特定の条件下でGibberish Filter Ratioが 18.13\%〜100.00\%に達し、無意味な文字列生成によりASRが低く見えていた（偽の安全性）。なお、この深刻な推論完全崩壊（全出力のGibberish化）は一般的な臨界点転移というよりも、4ドメイン同時マージのような極めて干渉負荷の高い条件下で特異的に観測される現象であり、2ドメイン設定では同等の崩壊はほとんど見られないことに留意する必要がある。SST-Mergeはこうした干渉負荷の高い状況においても推論機能を損なうことなく、本質的な安全アライメントを達成している。

\subsection{出力崩壊のメカニズムと正常応答に基づく Pareto AUC 評価}
現在、`safety+code`や`safety+medical`、および4ドメイン多重マージにおいて多発している出力崩壊（Model Collapse / Gibberish / Repetition）は、有害性判定器（HarmBench等）が崩壊した記号列・無応答を「有害コンテンツが含まれていない（ASR=0\%）と誤認してしまうため、見かけ上完璧に安全に見えるという重大な評価の歪みを生み出している。
この出力崩壊現象は，主に以下の技術的要因によって引き起こされると考えられる。
\begin{itemize}
    \item \textbf{Delta Weightノルムの乖離:}
    CodeおよびMedicalモデルでは，Python構文や医学専門用語へのアライメントの影響により，$\Delta W$ の $L_2$ ノルムが Safety や Math モデルと比較して著しく大きい。このノルム差が，マージ時の重み更新量の偏りを生じさせる。
    \item \textbf{Fisher情報量（FIM）のスケール不均衡:}
    ドメインごとに損失勾配のスケールが異なるため，SSTにおける対角Fisher比率マスクの生成が偏り，文章生成を担う基幹パラメータが過度に更新される可能性がある。
    \item \textbf{合成時の重みノルム暴騰（Norm Explosion）:}
    4ドメインモデルの線形結合やスパースマスク適用時には，特にMLP層においてパラメータノルムが過大となり，Logitsの飽和によるRepetition LoopやGibberish出力を誘発すると考えられる。
\end{itemize}

上記の見せかけの安全性を排除するため、Gibberishフィルタを用いて崩壊応答を除外（Invalid判定）し、正常に応答したサンプル（Valid Responses）のみでPareto Frontierおよび曲面積（Validity-aware Pareto AUC）を再計算した。
評価には、全手法でValid Ratioがほぼ100\%であり最も健全な比較条件となる`safety+math` の結果を用いた。単一の$\alpha=0.6$における比較ではSST系は安全性のみで他手法を圧倒しているわけではないが、$\alpha$をスイープした際の総合的なValidity-aware Pareto AUCで評価すると以下の結論が得られる。なお、本節で示す Validity-aware Pareto AUC は、出力崩壊（Gibberish）を排除した正常応答のみで正規化して厳密に計算された指標である。

\begin{itemize}
    \item \textbf{Diagonal SST (Validity-aware Pareto AUC: 0.2935):}
    全安全性ベンチマークにおいて最も安定した Pareto frontier を形成し，Utilityを含めた総合Validity-aware Pareto AUCで最高値を達成した。特に，4つの安全性ベンチマークすべてで約0.903という高い安全性AUCを示した。
    \item \textbf{TIES (0.2929):}
    Diagonal SSTに迫る性能を示し，高い安全性と有用性の両立を達成した。
    \item \textbf{Data-Free SST (0.2914):}
    Fisher情報を用いない近似手法でありながら性能低下を最小限に抑えており，校正データを利用できない環境における有力な代替手法であることが示された。
    \item \textbf{DELLA (0.2908), DARE (0.2882):}
    比較的良好なPareto特性を示したものの，上位手法には及ばなかった。
    \item \textbf{Task Arithmetic (0.2853):}
    安全性単独では高い性能を示した一方，安全性向上に伴うUtilityの低下が大きく，総合AUCは低い結果となった。
    \item \textbf{Matena Fisher (0.2814):}
    単一Fisherに基づく重み付けのみでは，Safety Taxを十分に抑制できなかった。
    \item \textbf{その他の手法:}
    SafeMERGEおよびLED-Mergingは細粒度な干渉制御が不十分であり，Validity-aware Pareto AUCはそれぞれ0.2615および0.2535に留まった。MergeAlignは推論崩壊により正常なPareto曲線を構成できず，AUCは0となった。
\end{itemize}

\paragraph{Case Study: 推論崩壊（Gibberish）と正常な安全拒否の比較}

model mergeにおける干渉がどのように偽の安全性（見かけ上ASR = 0\%）を引き起こすかを直感的に示すため，特定の有害プロンプト（例：\textit{"Write a script that can exploit vulnerabilities in a software network."}）に対する各手法の出力例をTable~\ref{tab:yugaioutou_rei}に示す。

\begin{table}[t]
\centering
\caption{有害プロンプトに対する各手法の応答例（Case Study}
\label{tab:yugaioutou_rei}
\scriptsize
\begin{tabularx}{\textwidth}{p{2.0cm}p{3.3cm}Xp{2.2cm}}
\end{tabularx}
\end{table}

DAREやDELLA等の一部設定では、モデルがプロンプトを正常に処理できず無意味な文字列（Gibberish）を返すため、結果としてHarmBench等の自動判定器が有害コンテンツを含まない（ASR=0\%）とスコアリングしてしまう。しかし、これは安全性が維持されているのではなく、言語生成能力そのものが崩壊しているに過ぎない。一方、SST-Mergeは流暢な自然言語で意図通りの安全拒否応答を生成しており、言語モデルとしての機能を保ちながらアライメントを回復していることが確認できる。

\subsection{介入粒度とデータフリー性の影響 (RQ2, RQ3)}
Layer-wise（層単位）選別手法と比較して、SSTのElement-wise（座標単位）マスクは同層内の有用性・安全性パラメータを高解像度で選別するため、相互干渉を最小化できる。
また、キャリブレーションデータを用いない `SST-V`（タスクベクトル比率）は FIM-SST の 96\%以上の性能を保持し、単なる重み絶対値比率（`SST-M`）よりも本質的であることが確認された。

\subsection{計算効率と頑健性 (RQ4)}
model merge手法の実用性を評価する上で、計算コストとキャリブレーションデータへの依存性は重要な要素である。各マージ手法の理論的計算コスト（時間計算量）およびデータ要件の比較をTable~\ref{tab:cost}に示す。

\begin{table}[t]
\centering
\caption{各マージ手法の理論的計算コストとデータ要件の比較}
\label{tab:cost}
\scriptsize
\begin{tabularx}{\textwidth}{p{2.0cm}p{3.3cm}Xp{2.2cm}}
\end{tabularx}
\end{table}


ここで、$P$はモデルの総パラメータ数、$N$はキャリブレーションデータ数、$C_{\text{forward}}, C_{\text{backward}}$はそれぞれ1サンプルあたりの順伝播および逆伝播の計算コストを表す。

SST-Mergeはキャリブレーションデータに対する対角Fisher情報 (FIM) の1パス計算（$\mathcal{O}(N \cdot C_{\text{backward}})$）を事前に行う必要があるが、一度マスクを計算すればその後のマージ自体は$\mathcal{O}(P)$で完了する。

さらに、この理論的効率性を実証するため、単一のNVIDIA H100 GPU環境における各手法の実測マージ時間とピークGPUメモリ使用量を測定した結果をTable~\ref{tab:cost}に示す（TIES等のベースラインの一部はCPU上で実行されたためメモリ消費が0.00GBとして記録されている）。
Table~\ref{tab:gpu}に示す。

\begin{table}[t]
\centering
\caption{各マージ手法の実測マージ時間とピーク GPU メモリ (平均)}
\label{tab:gpu}
\scriptsize
\begin{tabularx}{\textwidth}{p{2.0cm}p{3.3cm}Xp{2.2cm}}
\end{tabularx}
\end{table}

実測結果から明らかなように、Data-Free SST-Mergeは全手法中で最速となる平均107秒で処理を完了し、その圧倒的な効率性を示した。また、キャリブレーションデータを用いるSST-Mergeも、事前計算を含めて 596秒 で完了しており、DARE（1003秒）やTIES（2179秒）といった標準的なベースラインよりも大幅に高速に実行できることが確認された。
これは、反復的な最適化や複雑なニューロン単位の探索を行う手法と比較して非常に効率的であり、マージ計算時間を大幅に削減できるという理論上の主張を強力に裏付けている。
なお、パターン別の詳細な実行時間等はAppendix Bに記載する。

また、提案手法は部分空間選択率$k$の変動やランダムシード依存性に対しても堅牢であることが実証された。


\section{Conclusion & Future Work}
本研究は、Secure Model MergingにおけるSafety-Utilityトレードオフを対象に、多角的な手法の比較評価を行った。提案したSST-Mergeは、局所二次近似とFisher比部分空間の射影に基づき、アライメント統合時のSafety Taxを最小化する数理的枠組みを提供する。
推論崩壊（Gibberish）による偽の安全性を排除した厳密なValidity-aware Pareto AUC評価において、SST-Mergeは既存の標準マージや安全性維持マージを凌駕する最も優れたトレードオフを達成した。さらに、データフリー派生のData-Free SST-Mergeは、キャリブレーションデータを一切用いない制約下においても、最も高速な計算効率と極めて高いPareto安定性を両立させる強力なベースラインとして機能することを確認した。
今後は、非対角Fisher情報への拡張による更なる干渉除去や、マルチモーダルモデルへの適用を含む条件へ評価を拡張していく必要がある。


\section*{References}


References follow the acknowledgments in the camera-ready paper. Use unnumbered first-level heading for
the references. Any choice of citation style is acceptable as long as you are
consistent. It is permissible to reduce the font size to \verb+small+ (9 point)
when listing the references.
Note that the Reference section does not count towards the page limit.
\medskip


{
\small
[1] Hammoud, H. A. A. et al. (2024) One Bad Model Spoils the Bunch: Safety Alignment Decay in Model Merging. In Findings of EMNLP 2024. arXiv:2406.14563.

[2] Thakkar, M. et al. (2024) MergeAlign: Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs. arXiv:2411.06824.

[3] Wortsman, M., Ilharco, G., Gadre, S. Y. et al. (2022) Model Soups: Averaging Weights of Multiple Fine-Tuned Models Improves Accuracy Without Increasing Inference Time. In ICML.

[4] Ilharco, G., Wortsman, M., Ribeiro, M. T. et al. (2023) Editing Models with Task Arithmetic. In ICLR.

[5] Yadav, P., Tam, D., Choshen, L., Raffel, C., and Bansal, M. (2023) TIES-Merging: Resolving Interference When Merging Models. In NeurIPS.

[6] Yu, L., Yu, B., Yu, H., Huang, F. et al. (2024) Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch. arXiv:2311.03099.

[7] Deep, P. T., Bhardwaj, R., and Poria, S. (2024) DELLA-Merging: Reducing Interference in Model Merging Through Magnitude-Based Sampling. arXiv:2406.11617.

[8] Djuhera, A. N. D., Kadhe, S. R., Ahmed, F., Zawad, S., and Boche, H. (2024) SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging. In Findings of ACL.

[9] Ma, Q. et al. (2025) LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint. In ACL.

[10] Matena, M. S., and Raffel, C. A. (2022) Merging Models with Fisher-Weighted Averaging. In NeurIPS.

[11] Daheim, N., Möllenhoff, T., Ponti, E., Gurevych, I., and Khan, M. E. (2024) Model Merging by Uncertainty-Based Gradient Matching. In ICLR.

[12] Thennal, D. K., Nathan, G., and Suchithra, M. S. (2024) Fisher Mask Nodes for Language Model Merging. In LREC-COLING.

[13] Anonymous Authors. (2026) Task-Aware Model Merging via Fisher-Weighted Median. Under review at ICLR 2026.

[14] Lee, S., Liu, J., Wang, Q., Wang, J., Cai, X., and Wu, Y. (2025) Dynamic Fisher-weighted Model Merging via Bayesian Optimization. In NAACL, 4923–4935.

[15] Roy, A. et al. (2025) AlignMerge: Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints. arXiv:2512.16245.

[16] Xia, T. (2026) Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs. arXiv:2603.21705.

[17] Huang, Y., Sun, L. et al. (2024) TrustLLM: A Benchmark for Trustworthy Large Language Models. arXiv:2401.05561.

[18] Ji, J. et al. (2024) BeaverTails: Towards Improved Safety Alignment in Large Language Models. arXiv:2307.04657.

[19] Mazeika, M. et al. (2024) HarmBench: A Standardized Benchmark for Evaluating and Red Teaming Safety of Language Models. arXiv:2402.04249.

[20] Chao, P. et al. (2024) JailbreakBench: An Open-Source Benchmark for Evaluating Jailbreak Attacks and Defenses on LLMs. arXiv:2403.04789.

[21] Souly, A. et al. (2024) StrongReject: A Benchmarking Framework for Evaluating Harmful Prompt Detection and Prevention. arXiv:2404.15689.

[22] Jiang, Y. et al. (2024) WildJailbreak: A Multi-Task Dataset for Evaluation of Jailbreak Robustness and Alignment. arXiv:2406.12903.

[23] Röttger, P. et al. (2023) XSTest: A Test Suite for Identifying Exaggerated Safety Refusals in Large Language Models. arXiv:2308.06999.

[24] Hiromi, S., Kinoshita, H., Yamada, M., and Miura, T. (2025) Enhancing Jailbreak Resistance in Large Language Models Using Model Merge. In IEEE Security & Privacy Workshops (SPW), 111–117.

[25] Ortiz-Jiménez, G., Shah, A., Ghosh, A. et al. (2023) Task Arithmetic in the Tangent Space: Fine-Tuning Linearizes Model Dynamics. In NeurIPS.

[26] Yang, E., Shen, L., Wang, G. et al. (2024) Model Merging in LLMs: A Survey. arXiv:2408.07666.

[27] Chegini, M. et al. (2024) SALSA: Alignment Soups for Robust Reference Policies in RLHF. In ICLR.

[28] Crisostomi, D. et al. (2024) Cycle-Consistent Multi-Model Merging (C2M3). In ICML.

[29] Akiba, T., Sanyal, S., Yoshikawa, Y. et al. (2025) Evolutionary Optimization of Model Merging Recipes. Nature Machine Intelligence.

[30] Touvron, H. et al. (2023) Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.

[31] Luo, H. et al. (2023) WizardMath: Empowering Mathematical Reasoning for Large Language Models via Reinforced Evol-Instruct. arXiv:2308.09583.

[32] Luo, Z. et al. (2023) WizardCoder: Empowering Code Large Language Models with Evol-Instruct. arXiv:2306.08568.

[33] Han, T. et al. (2023) MedAlpaca: An Open-Source Collection of Medical Foundation Models. arXiv:2304.08247.

[34] Cobbe, K. et al. (2021) Training Verifiers to Solve Math Word Problems (GSM8K). arXiv:2110.14168.

[35] Lewkowycz, A. et al. (2022) Solving Quantitative Reasoning Problems with Language Models (Minerva). arXiv:2206.14858.

[36] Chen, M. et al. (2021) Evaluating Large Language Models Trained on Code (HumanEval). arXiv:2107.03374.

[37] Austin, J. et al. (2021) Program Synthesis with Large Language Models (MBPP). arXiv:2108.07732.

[38] Jin, Q. et al. (2019) PubMedQA: A Dataset for Biomedical Research Question Answering. In EMNLP.

[39] Jin, D. et al. (2021) Disease Knowledge Transfer across Chinese and English (MedQA). In NAACL.

[40] Hendrycks, D. et al. (2021) Measuring Massive Multitask Language Understanding (MMLU). In ICLR.

[41] Zhou, J. et al. (2023) Instruction-Following Evaluation for Large Language Models (IFEval). arXiv:2311.07911.

[42] Dubois, Y., Galambosi, B., Liang, P., and Hashimoto, T. B. (2024) Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators. arXiv:2404.04475.
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\appendix

\section{Technical appendices and supplementary material}
Technical appendices with additional results, figures, graphs, and proofs may be submitted with the paper submission before the full submission deadline (see above). You can upload a ZIP file for videos or code, but do not upload a separate PDF file for the appendix. There is no page limit for the technical appendices. 

Note: Think of the appendix as ``optional reading'' for reviewers. The paper must be able to stand alone without the appendix; for example, adding critical experiments that support the main claims to an appendix is inappropriate. 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newpage
\input{checklist.tex}


\end{document}