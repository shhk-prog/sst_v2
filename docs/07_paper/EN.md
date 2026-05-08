%% bare_conf_compsoc.tex
%% V1.4b
%% 2015/08/26
%% by Michael Shell
%% See:
%% http://www.michaelshell.org/
%% for current contact information.
%%
%% This is a skeleton file demonstrating the use of IEEEtran.cls
%% (requires IEEEtran.cls version 1.8b or later) with an IEEE Computer
%% Society conference paper.
%%
%% Support sites:
%% http://www.michaelshell.org/tex/ieeetran/
%% http://www.ctan.org/pkg/ieeetran
%% and
%% http://www.ieee.org/

%%*************************************************************************
%% Legal Notice:
%% This code is offered as-is without any warranty either expressed or
%% implied; without even the implied warranty of MERCHANTABILITY or
%% FITNESS FOR A PARTICULAR PURPOSE! 
%% User assumes all risk.
%% In no event shall the IEEE or any contributor to this code be liable for
%% any damages or losses, including, but not limited to, incidental,
%% consequential, or any other damages, resulting from the use or misuse
%% of any information contained here.
%%
%% All comments are the opinions of their respective authors and are not
%% necessarily endorsed by the IEEE.
%%
%% This work is distributed under the LaTeX Project Public License (LPPL)
%% ( http://www.latex-project.org/ ) version 1.3, and may be freely used,
%% distributed and modified. A copy of the LPPL, version 1.3, is included
%% in the base LaTeX documentation of all distributions of LaTeX released
%% 2003/12/01 or later.
%% Retain all contribution notices and credits.
%% ** Modified files should be clearly indicated as such, including  **
%% ** renaming them and changing author support contact information. **
%%*************************************************************************


% *** Authors should verify (and, if needed, correct) their LaTeX system  ***
% *** with the testflow diagnostic prior to trusting their LaTeX platform ***
% *** with production work. The IEEE's font choices and paper sizes can   ***
% *** trigger bugs that do not appear when using other class files.       ***                          ***
% The testflow support page is at:
% http://www.michaelshell.org/tex/testflow/



\documentclass[conference,compsoc]{IEEEtran}
\usepackage{color}
\usepackage{url}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{csquotes}
%\usepackage{appendix}
\usepackage[x11names, dvipsnames, svgnames, table]{xcolor}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{subcaption}
\usepackage{placeins}

% \include{tables}
% Some/most Computer Society conferences require the compsoc mode option,
% but others may want the standard conference format.
%
% If IEEEtran.cls has not been installed into the LaTeX system files,
% manually specify the path to it like:
% \documentclass[conference,compsoc]{../sty/IEEEtran}





% Some very useful LaTeX packages include:
% (uncomment the ones you want to load)


% *** MISC UTILITY PACKAGES ***
%
%\usepackage{ifpdf}
% Heiko Oberdiek's ifpdf.sty is very useful if you need conditional
% compilation based on whether the output is pdf or dvi.
% usage:
% \ifpdf
%   % pdf code
% \else
%   % dvi code
% \fi
% The latest version of ifpdf.sty can be obtained from:
% http://www.ctan.org/pkg/ifpdf
% Also, note that IEEEtran.cls V1.7 and later provides a builtin
% \ifCLASSINFOpdf conditional that works the same way.
% When switching from latex to pdflatex and vice-versa, the compiler may
% have to be run twice to clear warning/error messages.






% *** CITATION PACKAGES ***
%
\ifCLASSOPTIONcompsoc
  % IEEE Computer Society needs nocompress option
  % requires cite.sty v4.0 or later (November 2003)
  \usepackage[nocompress]{cite}
\else
  % normal IEEE
  \usepackage{cite}
\fi
% cite.sty was written by Donald Arseneau
% V1.6 and later of IEEEtran pre-defines the format of the cite.sty package
% \cite{} output to follow that of the IEEE. Loading the cite package will
% result in citation numbers being automatically sorted and properly
% "compressed/ranged". e.g., [1], [9], [2], [7], [5], [6] without using
% cite.sty will become [1], [2], [5]--[7], [9] using cite.sty. cite.sty's
% \cite will automatically add leading space, if needed. Use cite.sty's
% noadjust option (cite.sty V3.8 and later) if you want to turn this off
% such as if a citation ever needs to be enclosed in parenthesis.
% cite.sty is already installed on most LaTeX systems. Be sure and use
% version 5.0 (2009-03-20) and later if using hyperref.sty.
% The latest version can be obtained at:
% http://www.ctan.org/pkg/cite
% The documentation is contained in the cite.sty file itself.
%
% Note that some packages require special options to format as the Computer
% Society requires. In particular, Computer Society  papers do not use
% compressed citation ranges as is done in typical IEEE papers
% (e.g., [1]-[4]). Instead, they list every citation separately in order
% (e.g., [1], [2], [3], [4]). To get the latter we need to load the cite
% package with the nocompress option which is supported by cite.sty v4.0
% and later.





% *** GRAPHICS RELATED PACKAGES ***
%
\ifCLASSINFOpdf
  % \usepackage[pdftex]{graphicx}
  % declare the path(s) where your graphic files are
  % \graphicspath{{../pdf/}{../jpeg/}}
  % and their extensions so you won't have to specify these with
  % every instance of \includegraphics
  % \DeclareGraphicsExtensions{.pdf,.jpeg,.png}
\else
  % or other class option (dvipsone, dvipdf, if not using dvips). graphicx
  % will default to the driver specified in the system graphics.cfg if no
  % driver is specified.
  % \usepackage[dvips]{graphicx}
  % declare the path(s) where your graphic files are
  % \graphicspath{{../eps/}}
  % and their extensions so you won't have to specify these with
  % every instance of \includegraphics
  % \DeclareGraphicsExtensions{.eps}
\fi
% graphicx was written by David Carlisle and Sebastian Rahtz. It is
% required if you want graphics, photos, etc. graphicx.sty is already
% installed on most LaTeX systems. The latest version and documentation
% can be obtained at: 
% http://www.ctan.org/pkg/graphicx
% Another good source of documentation is "Using Imported Graphics in
% LaTeX2e" by Keith Reckdahl which can be found at:
% http://www.ctan.org/pkg/epslatex
%
% latex, and pdflatex in dvi mode, support graphics in encapsulated
% postscript (.eps) format. pdflatex in pdf mode supports graphics
% in .pdf, .jpeg, .png and .mps (metapost) formats. Users should ensure
% that all non-photo figures use a vector format (.eps, .pdf, .mps) and
% not a bitmapped formats (.jpeg, .png). The IEEE frowns on bitmapped formats
% which can result in "jaggedy"/blurry rendering of lines and letters as
% well as large increases in file sizes.
%
% You can find documentation about the pdfTeX application at:
% http://www.tug.org/applications/pdftex





% *** MATH PACKAGES ***
%
%\usepackage{amsmath}
% A popular package from the American Mathematical Society that provides
% many useful and powerful commands for dealing with mathematics.
%
% Note that the amsmath package sets \interdisplaylinepenalty to 10000
% thus preventing page breaks from occurring within multiline equations. Use:
%\interdisplaylinepenalty=2500
% after loading amsmath to restore such page breaks as IEEEtran.cls normally
% does. amsmath.sty is already installed on most LaTeX systems. The latest
% version and documentation can be obtained at:
% http://www.ctan.org/pkg/amsmath





% *** SPECIALIZED LIST PACKAGES ***
%
%\usepackage{algorithmic}
% algorithmic.sty was written by Peter Williams and Rogerio Brito.
% This package provides an algorithmic environment fo describing algorithms.
% You can use the algorithmic environment in-text or within a figure
% environment to provide for a floating algorithm. Do NOT use the algorithm
% floating environment provided by algorithm.sty (by the same authors) or
% algorithm2e.sty (by Christophe Fiorio) as the IEEE does not use dedicated
% algorithm float types and packages that provide these will not provide
% correct IEEE style captions. The latest version and documentation of
% algorithmic.sty can be obtained at:
% http://www.ctan.org/pkg/algorithms
% Also of interest may be the (relatively newer and more customizable)
% algorithmicx.sty package by Szasz Janos:
% http://www.ctan.org/pkg/algorithmicx




% *** ALIGNMENT PACKAGES ***
%
%\usepackage{array}
% Frank Mittelbach's and David Carlisle's array.sty patches and improves
% the standard LaTeX2e array and tabular environments to provide better
% appearance and additional user controls. As the default LaTeX2e table
% generation code is lacking to the point of almost being broken with
% respect to the quality of the end results, all users are strongly
% advised to use an enhanced (at the very least that provided by array.sty)
% set of table tools. array.sty is already installed on most systems. The
% latest version and documentation can be obtained at:
% http://www.ctan.org/pkg/array


% IEEEtran contains the IEEEeqnarray family of commands that can be used to
% generate multiline equations as well as matrices, tables, etc., of high
% quality.




% *** SUBFIGURE PACKAGES ***
%\ifCLASSOPTIONcompsoc
%  \usepackage[caption=false,font=footnotesize,labelfont=sf,textfont=sf]{subfig}
%\else
%  \usepackage[caption=false,font=footnotesize]{subfig}
%\fi
% subfig.sty, written by Steven Douglas Cochran, is the modern replacement
% for subfigure.sty, the latter of which is no longer maintained and is. However,
% subfig.sty requires and automatically loads Axel Sommerfeldt's caption.sty
% which will override IEEEtran.cls' handling of captions and this will result
% in non-IEEE style figure/table captions. To prevent this problem, be sure
% and invoke subfig.sty's "caption=false" package option (available since
% subfig.sty version 1.3, 2005/06/28) as this is will preserve IEEEtran.cls
% handling of captions.
% Note that the Computer Society format requires a sans serif font rather
% than the serif font used in traditional IEEE formatting and thus the need
% to invoke different subfig.sty package options depending on whether
% compsoc mode has been enabled.
%
% The latest version and documentation of subfig.sty can be obtained at:
% http://www.ctan.org/pkg/subfig




% *** FLOAT PACKAGES ***
%
%\usepackage{fixltx2e}
% fixltx2e, the successor to the earlier fix2col.sty, was written by
% Frank Mittelbach and David Carlisle. This package corrects a few problems
% in the LaTeX2e kernel, the most notable of which is that in current
% LaTeX2e releases, the ordering of single and double column floats is not
% guaranteed to be preserved. Thus, an unpatched LaTeX2e can allow a
% single column figure to be placed prior to an earlier double column
% figure.
% Be aware that LaTeX2e kernels dated 2015 and later have fixltx2e.sty's
% corrections already built into the system in which case a warning will
% be issued if an attempt is made to load fixltx2e.sty as it is no longer
% needed.
% The latest version and documentation can be found at:
% http://www.ctan.org/pkg/fixltx2e


%\usepackage{stfloats}
% stfloats.sty was written by Sigitas Tolusis. This package gives LaTeX2e
% the ability to do double column floats at the bottom of the page as well
% as the top. (e.g., "\begin{figure*}[!b]" is not normally possible in
% LaTeX2e). It also provides a command:
%\fnbelowfloat
% to enable the placement of footnotes below bottom floats (the standard
% LaTeX2e kernel puts them above bottom floats). This is an invasive package
% which rewrites many portions of the LaTeX2e float routines. It may not work
% with other packages that modify the LaTeX2e float routines. The latest
% version and documentation can be obtained at:
% http://www.ctan.org/pkg/stfloats
% Do not use the stfloats baselinefloat ability as the IEEE does not allow
% \baselineskip to stretch. Authors submitting work to the IEEE should note
% that the IEEE rarely uses double column equations and that authors should try
% to avoid such use. Do not be tempted to use the cuted.sty or midfloat.sty
% packages (also by Sigitas Tolusis) as the IEEE does not format its papers in
% such ways.
% Do not attempt to use stfloats with fixltx2e as they are incompatible.
% Instead, use Morten Hogholm'a dblfloatfix which combines the features
% of both fixltx2e and stfloats:
%
% \usepackage{dblfloatfix}
% The latest version can be found at:
% http://www.ctan.org/pkg/dblfloatfix




% *** PDF, URL AND HYPERLINK PACKAGES ***
%
%\usepackage{url}
% url.sty was written by Donald Arseneau. It provides better support for
% handling and breaking URLs. url.sty is already installed on most LaTeX
% systems. The latest version and documentation can be obtained at:
% http://www.ctan.org/pkg/url
% Basically, \url{my_url_here}.




% *** Do not adjust lengths that control margins, column widths, etc. ***
% *** Do not use packages that alter fonts (such as pslatex).         ***
% There should be no need to do such things with IEEEtran.cls V1.6 and later.
% (Unless specifically asked to do so by the journal or conference you plan
% to submit to, of course. )


% correct bad hyphenation here
\hyphenation{op-tical net-works semi-conduc-tor}


\begin{document}
%
% paper title
% Titles are generally capitalized except for words such as a, an, and, as,
% at, but, by, for, in, nor, of, on, or, the, to and up, which are usually
% not capitalized unless they are the first or last word of the title.
% Linebreaks \\ can be used within to get better formatting as desired.
% Do not put math or special symbols in the title.
\title{SST-Merge:Fisher-Ratio Subspace Optimization to Secure Model Merge}


% author names and affiliations
% use a multiple column layout for up to three different
% affiliations
\author{\IEEEauthorblockN{anonymous author}}
% \IEEEauthorblockA{affiliation\\
% Address goes here\\
% Telephone:+81-00-0000-0000\\
% Email: aaa.bbb.ccc.com}}
\iffalse
\and
\IEEEauthorblockN{Saki Hiromi}
\IEEEauthorblockA{NTT\\
Address goes here\\
Telephone:+81-50-3482-0306\\
Email: saki.hiromi@ntt.com}
\and
\IEEEauthorblockN{Hiroki Kinoshita}
\IEEEauthorblockA{NTT\\
Address goes here\\
Telephone:+81-50-3360-1755\\
Email: hiroki.kinoshita@ntt.com}
\and 
\IEEEauthorblockN{Takayuki Miura}
\IEEEauthorblockA{NTT\\
Address goes here\\
Telephone:+81-50-3482-4298\\
Email: tkyk.miura@ntt.com}
\and 
\IEEEauthorblockN{Akira Morikawa}
\IEEEauthorblockA{NTT\\
Address goes here\\
Telephone:+81-50-3482-4868\\
Email: a.morikawa@ntt.com}
\fi


% make the title area
\maketitle


% As a general rule, do not put math, special symbols or citations
% in the abstract
\begin{abstract}

In recent years, large language models (LLMs) have demonstrated strong performance across diverse domains, yet they remain vulnerable to security risks such as misinformation and malicious misuse. Secure Merge mitigates these risks by integrating a jailbreak-robust patch model into a base model without additional training; however, conventional merging methods often improve safety at the expense of utility.
To address this trade-off, we formulate security patch deployment as a constrained optimization problem under a local quadratic approximation based on the Fisher Information Matrix (FIM). The Fisher matrix computed over benign data serves as a proxy for utility cost, while the Fisher over harmful data represents safety gain. Maximizing safety gain subject to a utility constraint reduces to a generalized eigenvalue problem, where the eigenvalues admit a natural interpretation as safety–utility efficiency ratios.
For practical deployment, we derive two tractable approximations grounded in the same principle: a diagonal coordinate-wise SST and a data-free SST that replaces Fisher statistics with task--vector--based importance proxies. This unified framework provides both a theoretical characterization of the safety--utility trade--off and practical guidelines for secure patch integration. Empirical evaluations demonstrate that SST-Merge consistently achieves a more favorable safety--utility trade--off compared to existing merging methods.
\end{abstract}


%\IEEEpeerreviewmaketitle

\section{Introduction}
Large language models (LLMs) are increasingly deployed as the core reasoning engines of AI agents that autonomously invoke external tools, execute workflows, and interact with real-world systems. Beyond conversational response generation, these agentic systems support business automation and decision-making across diverse domains~\cite{chang2024survey}. 
However, this expanded capability also amplifies the security implications of LLM vulnerabilities. When embedded within AI agents, weaknesses such as misinformation generation, malicious instruction following, or adversarial prompt manipulation can directly translate into unsafe actions, data leakage, or unauthorized operations. As the adoption of AI agents accelerates, ensuring the robustness of their underlying LLM components has become a critical security requirement.

To defend LLMs against these vulnerabilities, various methods have been proposed to enhance model robustness. Fine-tuning is the most direct approach; however, continuous retraining is required as attack methods constantly evolve, resulting in substantial computational and operational costs. To enable lightweight and rapid patch deployment, Secure Merge has been introduced as a low-cost alternative~\cite{11050841}. Secure Merge integrates a jailbreak-robust patch model into a base utility model via parameter merging, thereby realizing safety updates without additional training or increased inference cost.

Despite these advantages, significant challenges remain. Na\"ively applying existing merge methods often improves safety at the expense of general performance. Safety-oriented updates typically strengthen refusal or suppression behaviors, which may interfere with benign responses and degrade task performance. This trade-off, which we term the \emph{Safety Tax}, represents a fundamental limitation for practical Secure Merge deployment~\cite{shi2024large,chen2025fundamental,qi2023fine}. In practice, improvements in jailbreak robustness are frequently accompanied by utility degradation, indicating that simply adding safety differences is insufficient. A principled mechanism is required to distinguish parameter directions that enhance safety from those that disproportionately harm utility.

In this work, we address this challenge by formulating security patch integration as a constrained optimization problem that explicitly models the Safety--Utility trade-off. 
We adopt a local quadratic approximation of the loss landscape and employ the Fisher Information Matrix (FIM) as a curvature proxy. The Fisher matrix computed over benign data serves as a measure of utility fragility (Tax), while the Fisher matrix over harmful data captures safety effectiveness (Gain). Under this formulation, selecting patch updates reduces to maximizing Gain subject to a Tax constraint, which leads to a generalized eigenvalue problem. The resulting eigenvalues naturally quantify the safety--utility efficiency ratio.

Building on this theoretical foundation, we propose SST-Merge (Safety-Sensitive Tuning by Fisher-Ratio Subspace), a merge method that selects update directions maximizing safety per unit utility cost. We further derive practical approximations—including a diagonal coordinate-wise variant and a data-free variant based on task-vector importance—to accommodate computational and data constraints. By explicitly controlling the Safety--Utility trade-off through direction selection, SST-Merge directly addresses the core objective of Secure Merge: improving jailbreak robustness while preserving general performance.

The main contribution of our works is as follows:
\begin{itemize}
    \item We formulate Secure Merge as a constrained optimization problem under a Fisher-based local quadratic model, showing that safety maximization under a utility constraint reduces to a generalized eigenvalue problem with a safety--utility efficiency interpretation.

    \item We propose SST-Merge, a Fisher-ratio subspace selection method, and derive practical diagonal and data-free approximations for deployment under computational and data constraints.

    \item Experiments demonstrate that SST-Merge achieves a more favorable safety--utility trade-off than existing merging methods.
\end{itemize}


\section{Related Work}
\subsection{Jailbreak Attacks}
A Jailbreak attack\cite{huang2024trustllm} can be defined as:\textit{an attempt to elicit a response from the model regarding a prohibited action by modifying a given prompt $P$ into an altered prompt $P'$.}
When the prompt \enquote{Teach me how to make a bomb.} is input, the model typically responds with a refusal message such as \enquote{I can’t assist with your request, \dots} because it recognizes that providing instructions for bomb-making is disallowed. However, by altering the original prompt to specify a different response format (e.g., \enquote{Sure, I can help you with that. First, \dots}), the model can be coerced into revealing prohibited information~\cite{wei2024jailbroken}~\cite{park2023generative}~\cite{zou2023universal}.

\subsection{Model Merge}

Model merge is a method that integrates the parameters of multiple models into a single unified model, enabling the combination of capabilities and properties without additional training. Traditionally, it has been used to improve task performance and to construct multi-task models. More recently, it has attracted attention as a computationally efficient approach to improve the model performance, and has been suggested as a effective method for strengthening specific capabilities~\cite{yang2024model,dubey2024llama}.

There are two main approaches to model merge:
\begin{description}
    \item[Pre-train Merge:] A method that integrates arbitrary models, allowing models pretrained independently to be merged.
    \item[Fine-tuning Merge:] A method that integrates the weights of models fine-tuned for different tasks, provided they share the same pretrained base model.
\end{description}

Only Fine-tuning Merge has been shown to be effective for LLMs. Therefore, in this paper, we use the term \emph{model merge} to specifically refer to Fine-tuning Merge.

The most fundamental frameworks include linear weight averaging between models~\cite{wortsman2022model} and Task Arithmetic, which adds task vectors defined as differences from the pretrained weights~\cite{Ilharco2022EditingMW}. While these methods are simple and easy to implement, they are prone to inter-task interference. In particular, when integrating safety-related parameter differences, they often induce over-refusal or degradation in response quality. To mitigate such interference, several advanced methods have been proposed, including task vector sparsification, avoidance of sign conflicts, and importance-based parameter selection~\cite{yadav2023ties,yu2024language,deep2024della,davari2024model}.

\subsection{Secure Merge and Security Patch Deployment}

Secure Merge is a method for low-cost security patch deployment that constructs a patch model specialized for robustness against jailbreak attacks and integrates it into an existing base model~\cite{11050841}. Unlike ensemble methods that require running multiple models at inference time, model merge yields a single unified model after integration, thereby incurring no additional inference cost. Moreover, the merging computation itself is significantly lighter than retraining models themselves. From the perspective of rapid security updates, Secure Merge therefore offers practical advantages.

Applying existing merge methods lead to degradation in overall model capability, which remains a key challenge. However, in practical deployment, achieving robustness while keeping general performance is crucial.

Figure~\ref{fig:secure_merge} illustrates the structure of Secure Merge.

\begin{figure}[h]
\centering
\includegraphics[width=\linewidth]{figures/secure_merge.png}
\caption{Secure merge}
\label{fig:secure_merge}
\end{figure}


\subsection{External Guardrails and Their Limitations}

External guardrails ensure safety without modifying the underlying LLM weights, thereby posing minimal risk of degrading general performance~\cite{grattafiori2024llama}. They also often maintain low false-positive rates on benign datasets. 

However, jailbreak attacks may evade detection by transforming prompts so as to circumvent the expressions anticipated by the detector, preventing detection rates from reaching sufficiently high levels~\cite{weng2025foot}. Therefore, while guardrails constitute an important defense of LLMs, fundamentally reducing the attack success rate requires applying patches that are reflected in the internal behavior of the model.

\subsection{Fisher Information Matrix and PEFT (LoRA)}

The Fisher Information Matrix (FIM) provides a natural local quadratic metric for approximating the impact of parameter perturbations on the loss function. It has been widely used in contexts such as importance estimation, mitigation of catastrophic forgetting, and conservative parameter updates. In many of these approaches, the Fisher matrix is incorporated as a regularization term to maintain existing performance~\cite{kirkpatrick2017overcoming,martens2020new}.

Parameter-efficient fine-tuning (PEFT), exemplified by LoRA, modifies model behavior through updates to a relatively small number of parameters, making it well suited for the creation, distribution, and deployment of security patches~\cite{han2024parameter,hu2021lora}. Secure Merge leverages this property by integrating the parameter differences of a patch model into an existing base model.

\section{Proposed Method: SST-Merge}
\label{sec:method}

We reformulate security patch integration in Secure Merge as a constrained optimization problem that strengthens safety—robustness against jailbreak attacks—while minimizing degradation of general performance (utility). Rather than naively injecting patch updates, our approach explicitly distinguishes parameter directions that enhance safety from those that disproportionately harm utility. Through principled direction selection, SST-Merge achieves a controlled and theoretically grounded trade-off between safety and utility.

We begin by presenting the Fisher Information Matrix (FIM)–based optimization principle underlying SST-Merge. We then derive progressively tractable approximations, including a diagonal coordinate-wise formulation and a data-free variant, to accommodate computational and data constraints encountered in practice.


\subsection{Preliminaries}

The loss landscape of LLMs is inherently non-convex; accordingly, our analysis does not claim global optimality. Instead, we focus on the local regime induced by small parameter perturbations, such as those introduced by LoRA or other PEFT methods. Within this neighborhood, we adopt a Fisher-based quadratic approximation as a tractable local model of the loss surface. Consequently, our theoretical guarantees are restricted to this local perturbation regime.

While prior work commonly employs the Fisher matrix as a regularizer to preserve general performance, our objective is fundamentally different. We aim to actively enhance safety while explicitly constraining utility degradation. To this end, we introduce two Fisher matrices defined over the benign and harmful data distributions, respectively, and interpret them as competing local metrics that quantify utility fragility and safety effectiveness. Rather than adding curvature as an auxiliary penalty term, we derive update directions that maximize a Fisher ratio—safety gain per unit utility cost—through an explicit constrained optimization formulation. This perspective distinguishes SST-Merge from conventional curvature-based regularization methods.

Let $\theta_{\mathrm{util}} \in \mathbb{R}^d$ denote the parameters of the base utility model, and let $\theta_{\mathrm{safe}} \in \mathbb{R}^d$ denote those of the security patch model. Secure Merge injects a security update $\Delta\theta$ into $\theta_{\mathrm{util}}$ to obtain the merged model
\begin{equation}
\theta_{\mathrm{merged}} \;=\; \theta_{\mathrm{util}} + \Delta\theta.
\label{eq:merged}
\end{equation}
The core challenge is not merely the magnitude of $\Delta\theta$, but the selection of directions along which it should be applied. Safety-oriented parameter differences tend to strengthen refusal and suppression behaviors, which may interfere with benign responses and degrade task performance. Thus, updates that improve safety can simultaneously reduce utility. Controlling this trade-off requires a principled mechanism for direction selection.



\subsection{Overview}

SST-Merge formulates security patch integration not as naive parameter addition, but as a constrained optimization problem that maximizes safety gain under an explicit utility constraint. The method proceeds in three steps:

\begin{description}
    \item[Step 1:] Estimate the local loss sensitivity with respect to the safety and utility data distributions.
    \item[Step 2:] Identify update directions that maximize safety gain per unit utility cost based on the two sensitivities.
    \item[Step 3:] Construct the merged update by selecting high-efficiency directions (Top-$k$) and projecting the patch difference onto the resulting safety subspace.
\end{description}


\subsection{Step 1: Computing Loss Sensitivity with Respect to Data Distributions}
\label{subsec:full}

The first step of SST-Merge is to quantify how parameter perturbations affect safety and utility, respectively.

Let $D_b$ denote the benign distribution (corresponding to utility data), and let $D_h$ denote the harmful or attack distribution (corresponding to safety data). The negative log-likelihood under distribution $D_t$ is defined as
\begin{equation}
\mathcal{L}_t(\theta) \;=\; \mathbb{E}_{x\sim D_t}\big[\ell(x;\theta)\big],
\quad t\in\{b,h\}.
\label{eq:loss}
\end{equation}

In the neighborhood of $\theta_{\mathrm{util}}$, we approximate the loss landscape by a local quadratic model. As a proxy for the local curvature, we employ the Fisher Information Matrix (FIM), defined as
\begin{equation}
F_t(\theta) \;=\; \mathbb{E}_{x\sim D_t}\!\left[
\nabla_\theta \ell(x;\theta)\nabla_\theta \ell(x;\theta)^\top
\right],
\quad t\in\{b,h\}.
\label{eq:fim}
\end{equation}

For numerical stability, we apply Tikhonov regularization to the benign Fisher matrix, replacing $F_b$ with $F_b + \varepsilon I$ so as to ensure $F_b \succ 0$.




We define the quadratic term on the benign side as a proxy for utility degradation, which we refer to as the \emph{Safety Tax}:
\begin{equation}
\mathrm{Tax}(\Delta\theta) \;:=\; \frac12\,\Delta\theta^\top F_b \Delta\theta.
\label{eq:tax}
\end{equation}
Similarly, the quadratic term on the harmful side is defined as a proxy for safety effectiveness:
\begin{equation}
\mathrm{Gain}(\Delta\theta) \;:=\; \Delta\theta^\top F_h \Delta\theta,
\label{eq:gain}
\end{equation}
where the constant factor $1/2$ is omitted since it does not affect the optimization.


\subsection{Step 2: Selecting Update Directions / Components}

Using the sensitivity measures derived in Step~1, we seek update directions that maximize safety gain while controlling utility degradation. SST-Merge imposes an explicit upper bound on the allowable utility cost (Tax) and maximizes the safety proxy within this constraint. Formally, we solve
\begin{equation}
\max_{\Delta\theta\in\mathbb{R}^d}\ \ \Delta\theta^\top F_h \Delta\theta
\quad \text{s.t.}\quad
\Delta\theta^\top F_b \Delta\theta \le c,
\label{eq:problemP}
\end{equation}
where $c>0$ denotes the maximum permissible Safety Tax under the local quadratic approximation.

A defining feature of this formulation is that safety and utility are not combined through a weighted sum. Instead, utility degradation is treated as a hard constraint, and safety is maximized within the feasible region. This reflects the Secure Merge setting, where preserving general performance is a strict requirement rather than a soft trade-off parameter.

Problem~\eqref{eq:problemP} reduces to maximizing a generalized Rayleigh quotient. The optimal direction is given by the eigenvector corresponding to the largest generalized eigenvalue $\lambda_{\max}$ of
\begin{equation}
F_h v \;=\; \lambda F_b v.
\label{eq:gevp}
\end{equation}
The associated generalized Rayleigh quotient
\begin{equation}
R(\Delta\theta)
:= \frac{\Delta\theta^\top F_h \Delta\theta}{\Delta\theta^\top F_b \Delta\theta}
\label{eq:rayleigh}
\end{equation}
admits a natural interpretation as safety gain per unit utility cost. Consequently, each generalized eigenvalue $\lambda$ represents a safety–utility efficiency ratio. SST-Merge therefore selects directions that maximize this efficiency.

Let $\widetilde V_k = [\tilde v_1,\dots,\tilde v_k] \in \mathbb{R}^{d\times k}$ denote the generalized eigenvectors corresponding to the top-$k$ eigenvalues of~\eqref{eq:gevp}, and define
\begin{equation}
\mathcal{S}_k := \mathrm{span}(\tilde v_1,\dots,\tilde v_k)
\label{eq:subspace}
\end{equation}
as the \emph{Safety subspace}. The merged update is constructed by projecting the security patch difference $\Delta_s$ onto this subspace:
\begin{equation}
\Delta\theta \;=\; \Pi_{\mathcal{S}_k}(\Delta_s).
\label{eq:proj}
\end{equation}
This ensures that only components of the patch difference with high safety–utility efficiency are injected.

In practice, we employ an $F_b$-orthogonal projection consistent with the Tax metric. Specifically, if $V_k$ consists of the generalized eigenvectors of~\eqref{eq:gevp}, we define
\begin{equation}
\Pi_{\mathcal{S}_k}^{(F_b)}(\Delta_s)
=
V_k (V_k^\top F_b V_k)^{-1} V_k^\top F_b \Delta_s,
\label{eq:proj_fb}
\end{equation}
and set $\Delta\theta = \Pi_{\mathcal{S}_k}^{(F_b)}(\Delta_s)$.

\subsubsection{Diagonal Approximation}
\label{subsec:diag}

Let $d$ denote the number of model parameters. The full Fisher Information Matrix (FIM) is a $d \times d$ matrix whose storage, estimation, and eigendecomposition are computationally infeasible for large-scale models. To enable practical deployment, the generalized eigenvalue problem in~\eqref{eq:gevp} must therefore be approximated in a tractable manner.

In Diagonal SST, we approximate the Fisher matrices as
\begin{equation}
F_t \approx \mathrm{diag}(f_{t,1},\dots,f_{t,d}),
\quad t\in\{b,h\}.
\label{eq:diag}
\end{equation}
Importantly, this approximation does not alter the optimization objective; it restricts the search space. Whereas the full formulation allows arbitrary directions in parameter space, the diagonal approximation limits candidate directions to coordinate axes.

Under this restriction, the generalized eigenvalue problem reduces to coordinate-wise comparisons of safety–utility efficiency ratios. Diagonal SST can thus be viewed as a computationally efficient specialization of Full SST that preserves the same optimization principle while constraining the search space for scalability.



\subsection{Step 3: Projection onto the Safety Subspace}



Given the update directions identified in Step~2, we select the eigenvector directions associated with large generalized eigenvalues (Top-$k$) and project the patch difference onto the resulting safety subspace.

Under the diagonal approximation~\eqref{eq:diag}, the generalized eigenvalue problem decomposes coordinate-wise, yielding
\begin{equation}
\lambda_i \;=\; \frac{f_{h,i}}{f_{b,i}+\varepsilon},
\label{eq:lambda_coord}
\end{equation}
which measures the safety gain per unit Tax obtained by perturbing coordinate $i$. Based on $\lambda_i$, we construct a mask $m\in\{0,1\}^d$ (hard selection) or $m\in[0,1]^d$ (soft selection), and define the injected update as
\begin{equation}
\Delta\theta \;=\; \alpha\,(m\odot \Delta_s),
\label{eq:masked_update}
\end{equation}
where $\odot$ denotes element-wise multiplication and $\alpha>0$ is the injection scale.

A hard mask selects the Top-$k$ coordinates:
\begin{equation}
m_i \;=\; \mathbf{1}\{\lambda_i \text{ is among the Top-}k\}.
\label{eq:hardmask}
\end{equation}
To smooth the selection boundary, a soft mask may be employed. For example, with temperature parameter $\tau>0$,
\begin{equation}
m_i \;=\; \sigma\!\left(\frac{\log(\lambda_i+\delta)}{\tau}\right),
\quad (\sigma:\text{sigmoid},\ \delta>0),
\label{eq:softmask}
\end{equation}
where $\delta$ ensures numerical stability. The soft formulation reduces discontinuities near the Top-$k$ threshold and improves robustness to estimation noise.

Parameters may contribute differently across layers or modules. To capture this structural heterogeneity, we introduce a layer-wise prior that modulates the injection strength. Let $w_{\mathrm{layer},i}\ge 0$ denote the prior weight for layer (or tensor index) $i$. The injected update becomes
\begin{equation}
\Delta\theta \;=\; \alpha\,(w_{\mathrm{layer}}\odot m\odot \Delta_s).
\label{eq:masked_update_layer}
\end{equation}
Here, $w_{\mathrm{layer}}$ encodes architectural priors (e.g., attention blocks, FFN layers, output heads) and interacts multiplicatively with the data-driven efficiency mask $m$.

Using $\Delta\theta$, the merged model can be constructed in two principal forms. The additive form is
\begin{equation}
\theta_{\mathrm{merged}}
\;=\;
\theta_{\mathrm{util}} + \Delta\theta
\;=\;
\theta_{\mathrm{util}} + \alpha\,(w_{\mathrm{layer}}\odot m\odot \Delta_s).
\label{eq:merge_additive}
\end{equation}

Alternatively, an interpolation form introduces coordinate-wise mixing coefficients $w_i\in[0,1]$:


\begin{equation}
w \;:=\; \mathrm{clip}\big(\alpha\,(w_{\mathrm{layer}}\odot m),\,0,\,1\big),
\label{eq:interp_weight}
\end{equation}
where $\mathrm{clip}(x,a,b)$ denotes element-wise projection onto the interval $[a,b]$.
The merged parameters are then given by
\begin{equation}
\theta_{\mathrm{merged}}
\;=\;
(1-w)\odot\theta_{\mathrm{util}} + w\odot\theta_{\mathrm{safe}}
\;=\;
\theta_{\mathrm{util}} + w\odot(\theta_{\mathrm{safe}}-\theta_{\mathrm{util}}).
\label{eq:merge_interpolation}
\end{equation}
The interpolation form can be interpreted as a coordinate-wise generalization of Task Arithmetic, where $w$ simultaneously determines both which coordinates are injected and the strength of injection.

The validity of the diagonal approximation depends on the magnitude of off-diagonal correlations. When such correlations are small—or when effective correlations within the trainable LoRA subspace are weak—coordinate selection based on~\eqref{eq:lambda_coord} closely approximates the full generalized eigenvalue solution.

However, instability may arise when the ranking boundary between selected and unselected components becomes ambiguous. Let $\lambda_{(1)} \ge \cdots \ge \lambda_{(d)}$ denote the values sorted in descending order. We define the Top-$k$ boundary gap as
\begin{equation}
\delta_k \;:=\; \lambda_{(k)}-\lambda_{(k+1)}.
\label{eq:gap}
\end{equation}

When $\delta_k$ is small, the Top-$k$ boundary becomes sensitive to estimation error and sampling noise, rendering hard selection unstable due to rank permutations.

To mitigate this issue, one may switch to the soft mask formulation in~\eqref{eq:softmask}, which smooths the selection boundary and improves robustness and reproducibility. SST-Merge employs $\delta_k$ as a diagnostic indicator and uses it as a practical guideline for choosing between hard and soft selection.


\subsection{Data-Free SST-Merge}
\label{subsec:datafree}



Even under the diagonal approximation, computing~\eqref{eq:lambda_coord} requires estimating gradient statistics from benign and harmful datasets. In real-world deployment, however, access to such data may be restricted due to privacy, contractual, or governance constraints, rendering direct estimation of the Fisher Information Matrix infeasible. When Secure Merge operates as a rapid security patch mechanism, minimizing data dependency becomes critical. 
To address this limitation, this subsection presents a data-free formulation of SST-Merge that retains the core safety–utility efficiency principle while eliminating the need for data-driven Fisher estimation.

Data-free SST does not explicitly estimate the Fisher matrices. Instead, it introduces data-independent importance proxies $\phi_{t,i}$ and approximates
\begin{equation}
f_{t,i} \approx \phi_{t,i},
\quad t\in\{b,h\}.
\label{eq:proxy}
\end{equation}
Importantly, this variant is not an alternative theory to Full SST. Rather, it preserves the core principle of selecting directions based on the safety–utility efficiency ratio, while approximating this ratio using proxies in place of Fisher statistics. It should therefore be regarded as a tractable approximation within the same conceptual framework.




\iffalse
\begin{enumerate}
    \item \textbf{Task-vector proxy:}  
    Treat the magnitude of the adapter difference (task vector) $\Delta_t$ as an importance measure:
    \begin{equation}
    \phi_{t,i} \;=\; (\Delta_{t,i})^2.
    \label{eq:proxy_taskvec}
    \end{equation}

    \item \textbf{Weight-magnitude proxy:}  
    Treat the magnitude of the parameter itself as an importance measure:
    \begin{equation}
    \phi_{t,i} \;=\; \theta_i^2
    \quad (\text{or } |\theta_i|).
    \label{eq:proxy_magnitude}
    \end{equation}
\end{enumerate}
\fi

Since $f_{t,i}$ cannot be directly estimated, natural proxy choices arise from parameter magnitudes or task differences. One option is a task-vector proxy, which treats the magnitude of the adapter difference (task vector) $\Delta_t$ as an importance measure:
\begin{equation}
\phi_{t,i} \;=\; (\Delta_{t,i})^2.
\label{eq:proxy_taskvec}
\end{equation}
Another option is a weight-magnitude proxy, which uses the magnitude of the parameter itself:
\begin{equation}
\phi_{t,i} \;=\; \theta_i^2
\quad (\text{or } |\theta_i|).
\label{eq:proxy_magnitude}
\end{equation}
In the Secure Merge setting, security patches are provided explicitly as parameter differences. Accordingly, we adopt the task-difference proxy, which aligns naturally with this scenario. The weight-magnitude proxy corresponds to classical magnitude pruning and may serve as a robust fallback under severe data constraints.


In our main experimental setting, security patches are provided explicitly as parameter differences. Accordingly, we adopt the task-difference proxy in (1) and define the safety--utility efficiency ratio as in~\eqref{eq:lambda_proxy}.

In the data-free setting, the most directly available quantities are the task-vector magnitudes. Let $\Delta_h$ denote the safety patch difference and $\Delta_b$ denote the utility difference. We define coordinate-wise proxies as
\begin{equation}
\phi_{h,i}=(\Delta_{h,i})^2,\qquad
\phi_{b,i}=(\Delta_{b,i})^2.
\label{eq:phi}
\end{equation}
Replacing the Fisher ratio with a proxy ratio yields
\begin{equation}
\hat{\lambda}_i
\;=\;
\frac{\phi_{h,i}}{\phi_{b,i}+\varepsilon}
=
\frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2+\varepsilon}.
\label{eq:lambda_proxy}
\end{equation}
Using $\hat{\lambda}_i$, we construct a mask $m(\hat{\lambda})$ analogously to~\eqref{eq:hardmask}–\eqref{eq:softmask}, and inject the update as
\begin{equation}
\Delta\theta \;=\; \alpha \big(m(\hat{\lambda})\odot \Delta_h\big).
\label{eq:update_proxy}
\end{equation}
In this manner, Data-free SST operationalizes ratio-based direction selection—merging only those parameter components that improve safety relative to their utility cost—even without access to data.

This formulation is closely related to Task Arithmetic, which injects the full difference uniformly,
\[
\theta_{\mathrm{util}} + \alpha \Delta_h,
\]
thereby incorporating both beneficial and interfering coordinates. Methods such as TIES mitigate interference through sparsification or conflict resolution; however, their selection criteria are not explicitly framed as maximizing a safety–utility efficiency objective. Data-free SST remains aligned with this line of work while introducing two clarifications tailored to Secure Merge: (i) the selection objective is explicitly defined as an efficiency ratio (safety per unit utility cost), and (ii) this ratio-based principle is preserved even in the absence of data through the use of importance proxies. Consequently, Data-free SST formalizes security patch integration under data constraints.


% =========================================================
% Experimental Setup
% =========================================================


\section{Experimental Setup}
\label{subsec:exp_setup}

We adopt \texttt{meta-llama-3.1-8b} as the base model~\cite{dubey2024llama}. On top of this model, we construct two LoRA fine-tuned variants with distinct objectives and merge them into a single model. The utility model is optimized for benign task performance, while the safety model is optimized for jailbreak robustness.

\begin{itemize}
  \item \textbf{Base model}: \texttt{meta-llama-3.1-8b}~\cite{dubey2024llama}
  \item \textbf{Utility model (A5)}: LoRA fine-tuned for benign task performance
  \item \textbf{Safety model (A7)}: LoRA fine-tuned for jailbreak robustness
\end{itemize}

We employ separate datasets corresponding to utility and safety objectives, which are treated as distinct data distributions throughout the experiments. When applicable, these datasets are also used for Fisher estimation.

\begin{itemize}
  \item \textbf{Utility data}: RepliQA~\cite{monteiro2024repliqa}
  \item \textbf{Safety data}: Jailbreak Trigger~\cite{huang2024trustllm}
\end{itemize}

As baselines, we compare against established model merging methods, including Task Arithmetic, TIES, and DARE. For SST-Merge, we evaluate multiple variants to assess the impact of merge formulation and data availability.

\begin{itemize}
  \item \textbf{SST-Merge (FIM-based)}: additive / interpolation
  \item \textbf{Data-free SST-Merge}: additive / interpolation
\end{itemize}

For each configuration, we additionally evaluate the effect of incorporating a \textbf{layer-wise prior}. The safety weight $\alpha$ is varied over $[0,1]$ with a step size of 0.1. For every method, we sweep $\alpha$ to characterize the resulting safety–utility trade-off. All methods are evaluated under the same $\alpha$ range and an identical evaluation protocol for both safety and utility metrics. Regarding the parameter $k$, it denotes the Top-$k$ selection ratio. 
In the additive variant, we consider $k \in \{\text{Soft}, 5\%, 10\%, 20\%\}$, 
whereas in the interpolation variant, we use $k \in \{5\%, 10\%, 20\%\}$.
Detailed experimental settings are provided in the Appendix.


\section{Experimental Results}

Figure~\ref{fig:a5_baseline},~\ref{fig:A5_A7_SST_Additive_k20},~\ref{fig:A5_A7_SST_Interpolation_k20}presents the safety–utility trade-offs of SST-Merge (additive and interpolation variants) compared with existing merge methods. Additional experimental results are provided in the Appendix.

% \begin{figure}[t]
% \centering
% \includegraphics[width=\linewidth]{figures/kekka.png}
% \caption{Comparison of Safety–Utility trade-offs across merge methods.}
% \label{fig:kekka}
% \end{figure}

\begin{figure}[t]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/A5_A7_Baseline_Methods.png}
    \caption{A5+A7: Baseline Methods (Task Arithmetic, TIES, DARE)}
    \label{fig:a5_baseline}
\end{figure}


\begin{figure}[t]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/A5_A7_SST_Additive_Soft_k20.png}
    \caption{A5+A7: SST-Merge Addactive k=Soft}
    \label{fig:A5_A7_SST_Additive_k20}
\end{figure}


\begin{figure}[t]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/A5_A7_SST_Interpolation_k20.png}
    \caption{A5+A7: SST-Merge Interpolation k=20}
    \label{fig:A5_A7_SST_Interpolation_k20}
\end{figure}

As shown in Figure~\ref{fig:a5_baseline},~\ref{fig:A5_A7_SST_Additive_k20},~\ref{fig:A5_A7_SST_Interpolation_k20}, SST-Merge consistently exhibits a more gradual utility degradation as the safety weight $\alpha$ increases, compared to baseline merge methods. In particular, the interpolation variant preserves utility more effectively while achieving substantial improvements in jailbreak robustness.

These results demonstrate that SST-Merge more effectively controls the safety–utility trade-off. By selecting update directions according to safety–utility efficiency, the method achieves stronger robustness gains without incurring excessive performance degradation.


\section{Conclusion}

In this paper, we cast Secure Merge as a constrained optimization problem that explicitly models the trade-off between safety improvement and utility preservation, and introduced SST-Merge. By leveraging Fisher Information Matrices over benign and harmful distributions as proxies for utility cost (Tax) and safety gain (Gain), we showed that maximizing Gain under a Tax constraint reduces to a generalized eigenvalue problem. 

To accommodate computational and data limitations, we derived tractable approximations under the same principle, including a diagonal Top-$k$/soft-mask formulation and a data-free variant based on task-vector importance. Experiments on \texttt{meta-llama-3.1-8b} demonstrated that SST-Merge achieves a more favorable safety–utility trade-off than existing merge methods, with the interpolation variant providing substantial robustness gains while preserving general performance.

Overall, SST-Merge provides a principled and practical framework for security patch integration in AI agents, enabling controlled robustness enhancement without excessive utility degradation.



\bibliographystyle{unsrt}
\bibliography{main}



% \iffalse
\onecolumn
\appendix

\subsection{Preliminary}
\subsubsection{Model Merge}
Model merge refers to the process of integrating the parameters of multiple models into a single consolidated model, enabling the combination of capabilities or characteristics without further training. 
It has traditionally been used to improve task performance and to construct multi-task models. 
More recently, it has gained attention as a computationally efficient strategy for enhancing model performance, with growing evidence suggesting its potential for strengthening specific capabilities~\cite{yang2024model,dubey2024llama}.

There are two main approaches to model merging:
\begin{description}
    \item[Pre-train Merge:]A method that integrates arbitrary models, making it possible to merge models even if they are pretrained differently.
    \item[Fine-tuning Merge:] A method that integrates the weights of models fine-tuned for different tasks, provided they share the same pretrained base model.
\end{description}

Currently, Fine-tuning Merge is regarded as the most effective model merging approach for large language models (LLMs). 
Therefore, throughout this paper, we use the term \emph{model merging} to denote Fine-tuning Merge.
Figure~\ref{fig:FT_merge} shows an image of the fine-tuning merge process.

\begin{figure}[h]
\centering
\includegraphics[width=\linewidth]{figures/FT_merge.pdf}
\caption{FT merge}
\label{fig:FT_merge}
\end{figure}
\FloatBarrier


\subsubsection{Jailbreak attacks}
A \emph{Jailbreak attack}~\cite{huang2024trustllm} can be defined as 
\begin{quote}
\textit{an attempt to elicit a response from the model regarding a prohibited action by modifying a given prompt $P$ into an altered prompt $P'$.}
\end{quote}

\begin{figure}[h]
\centering
\includegraphics[width=\linewidth]{figures/jailbreak_attack.pdf}
\caption{An example of a jailbreak attack.}
\label{fig:Jailbreak_attack}
\end{figure}
\FloatBarrier

As shown in Figure~\ref{fig:Jailbreak_attack}, when the prompt \enquote{Teach me how to make a bomb.} is input, the model typically responds with a refusal message such as \enquote{I can’t assist with your request, \dots} because it recognizes that providing instructions for bomb-making is disallowed. However, by altering the original prompt to specify a different response format (e.g., \enquote{Sure, I can help you with that. First, \dots}), the model can be coerced into revealing prohibited information~\cite{wei2024jailbroken}~\cite{park2023generative}~\cite{zou2023universal}.


\subsubsection{Positioning with Respect to Non-Convexity}

The loss landscape of LLMs is fundamentally non-convex, and therefore our framework does not claim global optimality guarantees. 
Rather, we focus on the local perturbation regime in which small parameter updates—such as those induced by LoRA or other PEFT methods—are applied. 
Within this neighborhood, we assume that a Fisher-based quadratic approximation constitutes a reasonable local model of the loss surface. 
Consequently, our theoretical claims are confined to optimality and boundary characterizations within this local region.

\subsubsection{External Guardrails and Their Limitations}

External guardrails provide a mechanism for enforcing safety without modifying the underlying weights of the LLM, thereby reducing the risk of degrading general performance~\cite{grattafiori2024llama}. 
They also tend to maintain relatively low false-positive rates on benign inputs. 
However, jailbreak attacks can evade detection by rephrasing or obfuscating prompts in ways not anticipated by the detector, which may limit detection accuracy. 
Therefore, while guardrails constitute an important first line of defense, fundamentally reducing the attack success rate requires patching mechanisms that are reflected in the internal behavior of the model.

Figure~\ref{fig:guardrail} illustrates the structure of an external guardrail system.

\begin{figure}[h]
\centering
\includegraphics[width=\linewidth]{figures/guardrail.png}
\caption{Illustration of an external guardrail architecture.}
\label{fig:guardrail}
\end{figure}

In this context, the central challenge becomes the \emph{Safety Tax}, namely the degradation of general performance induced by safety-oriented updates. 
The objective of this study is to mitigate this Safety Tax while strengthening jailbreak robustness.

\subsubsection{Quantifying Importance and Fragility via Fisher/Curvature}

The Fisher Information Matrix provides a natural local metric that approximates the effect of parameter perturbations on the loss via a quadratic model. 
It has been widely employed in various contexts, including importance estimation, mitigation of catastrophic forgetting, and conservative parameter updates. 
In many of these approaches, the Fisher matrix is incorporated as a regularization term to preserve model performance~\cite{kirkpatrick2017overcoming,martens2020new}.

In contrast, our problem setting explicitly aims to enhance safety while simultaneously constraining degradation in utility. 
Accordingly, we introduce two distinct Fisher matrices corresponding to the benign and harmful data distributions, and interpret them as competing local metrics. 
Rather than appending the Fisher matrix as a regularizer, we define directions that are effective for safety yet minimally destructive to utility through a Fisher ratio criterion, and derive the selection of such directions via an explicit optimization framework. 
In this respect, our approach differs fundamentally from conventional curvature-based regularization methods.


\subsubsection{PEFT (LoRA) and Patch Portability}

Parameter-Efficient Fine-Tuning (PEFT), typified by LoRA, enables behavioral modification of large models through updates to a relatively small set of parameters, rendering it particularly suitable for the creation, distribution, and application of security patches~\cite{han2024parameter,hu2021lora}. 
Secure Merge exploits this property by integrating the parameter differences of a patch model into an existing utility model.

Our work is positioned as a principled model merging method that mitigates the Safety Tax incurred during this integration process, thereby facilitating practical patch deployment that reconciles safety enhancement with the preservation of general performance.

\subsubsection{Baselines}
\label{subsec:baselines}

Let $\theta_{\mathrm{base}}$ denote the parameters of the base model, 
$\theta_{\mathrm{util}}$ those of the utility model, and 
$\theta_{\mathrm{safe}}$ those of the safety model. 
We define the task vectors as
\begin{equation}
\Delta_s = \theta_{\mathrm{safe}}-\theta_{\mathrm{base}},
\label{eq:taskvec_def_s}
\end{equation}
\begin{equation}
\Delta_u = \theta_{\mathrm{util}}-\theta_{\mathrm{base}}.
\label{eq:taskvec_def_u}
\end{equation}
We compare our method against the following existing model merging approaches.

% ---------------------------------------------------------
\paragraph{\textbf{Task Arithmetic~\cite{Ilharco2022EditingMW}}}
\label{subsubsec:baseline_task_arithmetic}

Task Arithmetic linearly combines task vectors with a safety weight $\alpha \in [0,1]$:
\begin{equation}
\theta_{\mathrm{merged}}
\;=\;
\theta_{\mathrm{base}}+\alpha\,\Delta_s+(1-\alpha)\Delta_u.
\label{eq:ta_additive}
\end{equation}

% ---------------------------------------------------------
\paragraph{\textbf{TIES~\cite{yadav2023ties}}}
\label{subsubsec:baseline_ties}

TIES consists of three stages: 
(i) trimming (sparsification of task vectors), 
(ii) sign election at each coordinate, and 
(iii) merging the sign-consistent components.

\paragraph{\textbf{(i) Trim (sparsification).}}
For each task vector $\Delta^{(j)}$, we apply a Top-$k$ pruning operator $\mathcal{T}_k(\cdot)$ that retains only the $k$ largest-magnitude coordinates:
\begin{equation}
\widetilde{\Delta}^{(j)} \;=\; \mathcal{T}_k\!\left(\Delta^{(j)}\right),
\qquad j=1,\dots,m,
\label{eq:ties_trim}
\end{equation}
where $\mathcal{T}_k$ sets all but the Top-$k$ (by absolute value) coordinates to zero.

\paragraph{\textbf{(ii) Elect signs.}}
For each coordinate $i$, a representative sign is determined by majority vote (or equivalently by the sign of the sum):
\begin{equation}
s_i
\;=\;
\mathrm{sign}\!\left(\sum_{j=1}^m \widetilde{\Delta}^{(j)}_i\right).
\label{eq:ties_sign_elect}
\end{equation}

\paragraph{\textbf{(iii) Merge (sign-consistent aggregation).}}
Only components whose signs agree with the representative sign $s_i$ are retained and averaged:
\begin{equation}
\Delta^{\mathrm{TIES}}_i
\;=\;
\frac{1}{m}\sum_{j=1}^m
\mathbf{1}\!\left\{\mathrm{sign}\!\big(\widetilde{\Delta}^{(j)}_i\big)=s_i\right\}
\,\widetilde{\Delta}^{(j)}_i.
\label{eq:ties_merge}
\end{equation}
The merged model is then obtained as
\begin{equation}
\theta_{\mathrm{merged}}
=
\theta_{\mathrm{util}}+\alpha\,\Delta^{\mathrm{TIES}}.
\label{eq:ties_final}
\end{equation}

% ---------------------------------------------------------
\paragraph{\textbf{DARE~\cite{yu2024language}}}
\label{subsubsec:baseline_dare}

DARE sparsifies the task vector by randomly dropping coordinates and rescales the remaining components to preserve the expectation. 
Given a retention probability $q \in (0,1]$, we sample a mask
\begin{equation}
z_i \sim \mathrm{Bernoulli}(q),
\qquad i=1,\dots,d,
\label{eq:dare_mask}
\end{equation}
and define
\begin{equation}
\Delta^{\mathrm{DARE}}
=
\frac{1}{q}\,(z\odot \Delta_s).
\label{eq:dare_rescale}
\end{equation}
By construction, $\mathbb{E}[\Delta^{\mathrm{DARE}}]=\Delta_s$. 
The merged model is finally given by
\begin{equation}
\theta_{\mathrm{merged}}
=
\theta_{\mathrm{util}}+\alpha\,\Delta^{\mathrm{DARE}}.
\label{eq:dare_final}
\end{equation}


\subsection{Experimental Details}
\label{sec:experimental_details}

\subsubsection{Model Settings}
\begin{itemize}
    \item \textbf{Base Model}: \texttt{meta-llama/Meta-Llama-3.1-8B-Instruct~\cite{dubey2024llama}}
    \item \textbf{LoRA Settings}: Rank $r=16$, Alpha $\alpha=32$, Dropout $= 0.05$, Target modules = \texttt{all-linear}
\end{itemize}


\subsubsection{Dataset and Training Configs} 
\mbox{}\\

We summarize the LoRA adapters and training configurations below.

\begin{table}[h]
\centering
\caption{LoRA Adapters and Training Configs}
\label{tab:adapter_conf}
\begin{tabular}{lcccc}
\hline
Model & Dataset & Epochs & Learning Rate & Objective \\
\hline
\textbf{A5 (Utility)} & ServiceNow/repliqa~\cite{monteiro2024repliqa} & 10 & 2e-4 & General Knowledge \\
\textbf{A6 (Utility)} & tatsu-lab/alpaca~\cite{alpaca} & 10 & 2e-4 & Instruction Following \\
\textbf{A7 (Safety)} & Custom Jailbreak~\cite{huang2024trustllm} & 5 & 2e-4 & Refusal/Safety \\
\hline
\end{tabular}
\end{table}

\subsubsection{Merge Methods and Hyper-parameters}
\label{subsec:merge_hparams}
\mbox{}\\

All methods conduct merging at the \textbf{adapter (LoRA) level}. The merged adapter is subsequently applied to the base model, and the resulting system is evaluated as a \textbf{single full model}.
We denote the task vectors (adapter differences relative to the base model) as $\tau_u$ for utility and $\tau_s$ for safety, and define the Safety Weight as $\alpha \in [0,1]$.

\begin{itemize}
  \item \textbf{Task Arithmetic (TA)~\cite{Ilharco2022EditingMW}.}
  \begin{equation}
    \tau_{\mathrm{merged}}
    \;=\;
    (1-\alpha)\,\tau_u \;+\; \alpha\,\tau_s
    \label{eq:ta_merge}
  \end{equation}

  \item \textbf{TIES-Merging~\cite{yadav2023ties}.}
  The task vectors are first sparsified (trimmed), and then integrated via sign resolution (elect sign) followed by disjoint merge. 
  In our experiments, the density is fixed to $0.5$, retaining the top 50\% of parameters by absolute magnitude.

  \item \textbf{DARE~\cite{yu2024language}.}
  The task vector is stochastically sparsified by random dropping, followed by re-scaling to preserve the expectation. 
  We set the drop rate to $p=0.9$, yielding a retention probability $q=1-p=0.1$, and compute
  \begin{equation}
    \tau_{\mathrm{merged}}
    \;=\;
    \frac{1}{q}\,(z\odot\tau_s),
    \qquad
    z_i\sim\mathrm{Bernoulli}(q),
    \label{eq:dare_merge}
  \end{equation}
  where $\odot$ denotes element-wise multiplication.

  \item \textbf{SST-Merge (Proposed).}
  The safety patch difference is injected only into the components (or directions) selected by the Top-$k$ criterion. 
  The primary configuration is as follows:
  \begin{itemize}
    \item Top-$k$ ratio: soft; $k \in \{5\%, 10\%, 20\%\, 50\%\}$ (Additive), $k \in \{5\%, 10\%, 20\%\, 50\%\}$ (Interpolation)
    \item FIM sample size: $N=500$
    \item Regularization: $\varepsilon=10^{-6}$
    \item Layer-wise weights: see Table~\ref{tab:layer_weights}
    \item \textbf{Mask Strategy}:
    \begin{itemize}
      \item \textbf{Additive Mode}: A \textbf{soft mask} (log-scale normalization) is adopted by default, with the effective ratio determined dynamically regardless of the nominal $k$ value.
      \item \textbf{Interpolation Mode}: A \textbf{hard mask} (Top-$k$ ratio) is used. Here, $k$ denotes the proportion of total parameters to which the patch is applied (via interpolation).
    \end{itemize}
    \item \textbf{Note}: The automatic diagnostic and switching mechanism based on $\delta_k$ is not used in these experiments.
  \end{itemize}

  \item \textbf{Data-Free SST.}
  To simulate scenarios where data are unavailable, we replace the Fisher Information Matrix with an importance proxy (magnitude) for Top-$k$ selection. 
  The configuration is as follows:
  \begin{itemize}
    \item Utility/Safety proxy: magnitude (e.g., $|W|$)
    \item Top-$k$ ratio: $k \in \{5\%, 10\%, 20\%\}$ (Hard Mask) \\
    Here, $k$ denotes the proportion of total parameters selected based on descending magnitude (mask value $=1$). In this variant, a \textbf{hard mask} is used instead of a soft mask.
    \item Layer-wise weights: identical to Table~\ref{tab:layer_weights}
  \end{itemize}
\end{itemize}

\begin{table}[h]
\centering
\caption{Layer-wise safety weights used in SST-Merge.}
\label{tab:layer_weights}
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.05}
\begin{tabular}{lc}
\hline
\textbf{Module type} & \textbf{Weight} \\
\hline
lm\_head & 1.5 \\
q\_proj, k\_proj, v\_proj, o\_proj & 1.2 \\
gate\_proj, up\_proj, down\_proj & 0.8 \\
\hline
\end{tabular}
\end{table}

\subsection{Experimental Results}
\label{sec:experimental_results}

This section reports detailed evaluation results for each method as a function of the Safety Weight $\alpha$, using two model pairs: A5 (RepliQA) + A7 (Safety) and A6 (Alpaca) + A7 (Safety). 
The purpose of presenting these detailed results is to comprehensively illustrate how variations in the hyperparameters ($\alpha$ and $k$) affect the safety--utility trade-off, thereby clarifying the robustness and characteristic behavior of the proposed method.

The main observations are summarized as follows:
\begin{itemize}
    \item \textbf{Superiority of SST-Merge (Interpolation):} 
    Across many configurations, SST-Merge (Interpolation) improves jailbreak resistance while maintaining higher utility compared to existing methods. 
    In particular, utility degradation remains more gradual in regimes with larger $\alpha$.

    \item \textbf{Effect of the hyperparameter $k$:} 
    When the mask ratio $k$ is small (i.e., more selective updates), utility preservation tends to be stronger. 
    Conversely, increasing $k$ accelerates safety improvement but also leads to more pronounced utility degradation, highlighting the inherent trade-off.

    \item \textbf{Effectiveness of Data-Free SST:} 
    Even under the data-free setting, the method exhibits trends comparable to Full SST, suggesting that the task-vector importance proxy serves as an effective approximation of the Fisher-based criterion.
\end{itemize}

\subsubsection{Model Pair: A5 (RepliQA) + A7 (Safety)}
\mbox{}

% base model
\begin{table}[h]
\centering
\caption{Baselines: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_base}
\begin{tabular}{c|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Task Arithmetic}} & \multicolumn{2}{c|}{\textbf{TIES}} & \multicolumn{2}{c}{\textbf{DARE}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.20\% & 69.35\% & 77.80\% & 45.88\% & 0.20\% & 1.25\% \\
0.07 & 72.40\% & 67.81\% & 77.40\% & 45.06\% & 4.60\% & 1.74\% \\
0.09 & 74.60\% & 64.90\% & 78.60\% & 43.04\% & 3.40\% & 0.96\% \\
0.10 & 74.80\% & 64.29\% & 81.20\% & 42.98\% & 14.60\% & 1.49\% \\
0.12 & 75.60\% & 60.72\% & 82.20\% & 42.31\% & 12.20\% & 5.61\% \\
0.15 & 79.40\% & 54.69\% & 82.20\% & 41.57\% & 22.00\% & 6.83\% \\
0.20 & 80.20\% & 48.79\% & 86.00\% & 38.38\% & 32.20\% & 1.37\% \\
0.30 & 86.80\% & 40.40\% & 90.80\% & 33.44\% & 4.20\% & 8.19\% \\
0.40 & 88.20\% & 35.66\% & 93.00\% & 29.66\% & 24.00\% & 10.78\% \\
0.50 & 95.60\% & 28.65\% & 95.20\% & 25.63\% & 36.60\% & 11.74\% \\
0.60 & 96.40\% & 20.16\% & 97.00\% & 18.07\% & 73.80\% & 10.79\% \\
0.70 & 99.20\% & 12.32\% & 97.60\% & 13.67\% & 70.60\% & 8.40\% \\
0.80 & 99.80\% & 8.06\% & 99.20\% & 10.54\% & 57.00\% & 1.40\% \\
0.90 & 100.00\% & 5.18\% & 99.00\% & 8.35\% & 13.20\% & 0.41\% \\
1.00 & 100.00\% & 2.62\% & 100.00\% & 6.37\% & 1.00\% & 1.58\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% sst soft k=20
\begin{table}[h]
\centering
\caption{SST-Merge Addactive layerwise=True/False k=Soft: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_soft}
\begin{tabular}{c|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{SST-Merge layerwise=False}} & \multicolumn{2}{c}{\textbf{SST-Merge layerwise=True}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.80\% & 72.09\% & 70.00\% & 71.45\% \\
0.07 & 69.00\% & 71.28\% & 68.60\% & 71.74\% \\
0.09 & 68.60\% & 71.34\% & 70.00\% & 71.54\% \\
0.10 & 69.20\% & 71.76\% & 68.80\% & 72.25\% \\
0.12 & 69.60\% & 70.65\% & 70.00\% & 70.50\% \\
0.15 & 67.40\% & 68.91\% & 69.00\% & 68.42\% \\
0.20 & 67.80\% & 65.83\% & 66.20\% & 65.06\% \\
0.30 & 65.80\% & 60.66\% & 68.80\% & 60.75\% \\
0.40 & 68.20\% & 54.88\% & 70.80\% & 54.50\% \\
0.50 & 69.60\% & 49.67\% & 69.00\% & 50.10\% \\
0.60 & 70.40\% & 47.26\% & 70.20\% & 46.91\% \\
0.70 & 69.80\% & 45.61\% & 70.20\% & 45.90\% \\
0.80 & 72.40\% & 43.87\% & 72.00\% & 44.27\% \\
0.90 & 73.60\% & 41.88\% & 73.20\% & 41.76\% \\
1.00 & 73.00\% & 40.93\% & 71.40\% & 40.98\%  \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% k-5
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=5$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_5}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 70.40\% & 70.77\% & 71.20\% & 71.06\% & 71.40\% & 69.47\% & 72.40\% & 68.45\% \\
0.07 & 69.20\% & 71.60\% & 69.60\% & 72.04\% & 71.40\% & 69.47\% & 71.20\% & 67.84\% \\
0.09 & 69.60\% & 71.88\% & 69.60\% & 71.30\% & 68.00\% & 67.68\% & 68.00\% & 67.60\% \\
0.10 & 67.80\% & 71.72\% & 71.20\% & 72.14\% & 67.80\% & 67.32\% & 69.20\% & 66.18\% \\
0.12 & 71.20\% & 70.65\% & 69.40\% & 70.25\% & 70.60\% & 65.90\% & 70.20\% & 65.41\% \\
0.15 & 66.80\% & 68.73\% & 68.80\% & 68.81\% & 69.80\% & 63.16\% & 69.20\% & 62.64\% \\
0.20 & 67.00\% & 65.77\% & 67.20\% & 65.96\% & 69.40\% & 59.19\% & 70.40\% & 58.85\% \\
0.30 & 70.60\% & 60.03\% & 70.80\% & 60.58\% & 77.80\% & 51.47\% & 76.40\% & 50.64\% \\
0.40 & 69.60\% & 54.68\% & 67.60\% & 54.76\% & 74.40\% & 45.84\% & 76.00\% & 45.32\% \\
0.50 & 69.00\% & 50.44\% & 67.00\% & 50.35\% & 76.40\% & 41.97\% & 79.00\% & 41.09\% \\
0.60 & 69.20\% & 47.92\% & 70.80\% & 47.67\% & 81.80\% & 40.05\% & 82.40\% & 39.79\% \\
0.70 & 70.00\% & 45.18\% & 71.40\% & 45.53\% & 85.20\% & 37.98\% & 86.80\% & 37.00\% \\
0.80 & 72.80\% & 44.21\% & 73.00\% & 44.21\% & 88.20\% & 35.87\% & 88.00\% & 35.25\% \\
0.90 & 71.60\% & 42.62\% & 72.20\% & 41.72\% & 89.80\% & 34.05\% & 89.80\% & 33.05\% \\
1.00 & 71.20\% & 40.82\% & 71.40\% & 40.97\% & 92.20\% & 33.38\% & 91.00\% & 32.53\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier


% k=10
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=10$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_10}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 70.20\% & 71.08\% & 70.00\% & 71.03\% & 72.60\% & 68.38\% & 70.20\% & 69.05\% \\
0.07 & 69.40\% & 71.32\% & 69.00\% & 72.04\% & 70.00\% & 68.21\% & 70.20\% & 68.41\% \\ 
0.09 & 70.20\% & 71.90\% & 69.00\% & 71.84\% & 69.40\% & 67.49\% & 68.60\% & 66.88\% \\ 
0.10 & 71.80\% & 71.17\% & 67.40\% & 71.27\% & 71.60\% & 66.93\% & 68.60\% & 66.88\% \\ 
0.12 & 69.40\% & 69.88\% & 70.20\% & 70.13\% & 68.60\% & 65.38\% & 70.40\% & 65.70\% \\ 
0.15 & 68.60\% & 68.55\% & 68.60\% & 69.02\% & 70.20\% & 62.52\% & 71.00\% & 62.36\% \\ 
0.20 & 68.00\% & 66.65\% & 67.60\% & 65.82\% & 71.00\% & 59.13\% & 70.80\% & 58.38\% \\ 
0.30 & 69.00\% & 61.05\% & 70.80\% & 60.62\% & 77.00\% & 51.61\% & 75.40\% & 50.58\% \\ 
0.40 & 69.20\% & 54.58\% & 68.80\% & 54.75\% & 76.80\% & 45.71\% & 76.80\% & 45.36\% \\ 
0.50 & 68.80\% & 49.97\% & 68.80\% & 50.86\% & 75.80\% & 41.94\% & 77.60\% & 40.94\% \\ 
0.60 & 70.80\% & 47.36\% & 70.20\% & 47.52\% & 83.40\% & 39.81\% & 83.60\% & 39.44\% \\ 
0.70 & 68.00\% & 44.38\% & 71.20\% & 45.11\% & 86.00\% & 37.52\% & 87.80\% & 36.57\% \\ 
0.80 & 72.00\% & 44.16\% & 71.20\% & 43.84\% & 87.40\% & 35.76\% & 88.20\% & 34.63\% \\ 
0.90 & 72.80\% & 42.19\% & 72.20\% & 42.66\% & 90.40\% & 33.59\% & 90.20\% & 33.49\% \\ 
1.00 & 73.00\% & 40.99\% & 73.00\% & 40.36\% & 91.40\% & 33.17\% & 91.60\% & 32.38\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% k=20
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=20$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_20}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.80\% & 71.61\% & 70.00\% & 71.76\% & 71.20\% & 69.49\% & 69.00\% & 68.92\% \\
0.07 & 67.60\% & 71.72\% & 68.40\% & 70.83\% & 70.00\% & 69.06\% & 70.60\% & 68.79\% \\
0.09 & 68.60\% & 71.58\% & 67.00\% & 70.87\% & 69.80\% & 66.86\% & 69.80\% & 67.21\% \\
0.10 & 69.40\% & 70.92\% & 68.20\% & 71.32\% & 70.00\% & 66.77\% & 70.40\% & 67.42\% \\
0.12 & 70.80\% & 70.92\% & 69.40\% & 70.37\% & 68.60\% & 65.51\% & 70.00\% & 64.76\% \\
0.15 & 67.20\% & 68.47\% & 69.40\% & 68.82\% & 72.00\% & 62.78\% & 69.40\% & 63.05\% \\
0.20 & 66.00\% & 65.40\% & 67.60\% & 66.13\% & 69.40\% & 58.97\% & 70.20\% & 58.54\% \\
0.30 & 69.40\% & 60.45\% & 66.40\% & 60.35\% & 76.40\% & 51.56\% & 77.40\% & 50.22\% \\
0.40 & 68.80\% & 55.31\% & 68.00\% & 54.34\% & 73.60\% & 46.09\% & 77.60\% & 45.75\% \\
0.50 & 68.80\% & 49.76\% & 68.60\% & 50.08\% & 77.00\% & 42.04\% & 78.00\% & 41.26\% \\
0.60 & 67.60\% & 47.22\% & 69.40\% & 46.59\% & 82.60\% & 40.15\% & 83.00\% & 39.31\% \\
0.70 & 68.80\% & 45.61\% & 71.00\% & 45.28\% & 85.00\% & 37.17\% & 88.00\% & 36.47\% \\
0.80 & 72.20\% & 43.17\% & 73.20\% & 43.42\% & 88.20\% & 35.43\% & 88.20\% & 34.96\% \\
0.90 & 75.20\% & 41.67\% & 74.40\% & 41.91\% & 88.80\% & 33.78\% & 90.20\% & 32.91\% \\
1.00 & 76.20\% & 40.58\% & 74.00\% & 40.59\% & 91.00\% & 33.23\% & 91.60\% & 32.31\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% k=50
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=50$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_50}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.60\% & 71.29\% & 68.40\% & 71.48\% & 69.80\% & 69.70\% & 69.40\% & 68.91\% \\
0.07 & 67.20\% & 71.03\% & 67.80\% & 70.80\% & 69.40\% & 67.86\% & 70.20\% & 68.26\% \\
0.09 & 68.20\% & 70.88\% & 70.60\% & 70.92\% & 70.60\% & 67.22\% & 72.60\% & 67.11\% \\
0.10 & 69.00\% & 71.88\% & 67.60\% & 71.30\% & 69.80\% & 67.11\% & 70.00\% & 66.83\% \\
0.12 & 65.80\% & 70.51\% & 69.40\% & 70.86\% & 70.00\% & 65.15\% & 71.40\% & 65.01\% \\
0.15 & 66.80\% & 68.74\% & 66.00\% & 68.50\% & 69.80\% & 62.89\% & 72.60\% & 62.37\% \\
0.20 & 66.60\% & 65.63\% & 63.00\% & 65.68\% & 72.80\% & 57.10\% & 74.20\% & 56.30\% \\
0.30 & 67.40\% & 59.73\% & 65.40\% & 59.87\% & 76.20\% & 48.48\% & 77.60\% & 48.10\% \\
0.40 & 67.80\% & 53.72\% & 65.20\% & 54.00\% & 82.60\% & 43.79\% & 82.80\% & 42.24\% \\
0.50 & 67.80\% & 48.93\% & 66.00\% & 48.98\% & 84.20\% & 39.78\% & 85.20\% & 39.18\% \\
0.60 & 68.00\% & 46.05\% & 66.60\% & 45.92\% & 88.00\% & 36.84\% & 90.20\% & 36.11\% \\
0.70 & 71.80\% & 44.64\% & 68.40\% & 44.37\% & 91.40\% & 35.36\% & 92.60\% & 33.41\% \\
0.80 & 70.60\% & 43.54\% & 70.00\% & 43.19\% & 92.80\% & 31.71\% & 94.40\% & 30.89\% \\
0.90 & 73.00\% & 41.52\% & 71.60\% & 41.62\% & 94.60\% & 28.98\% & 95.60\% & 27.89\% \\
1.00 & 76.20\% & 39.84\% & 75.40\% & 39.65\% & 96.40\% & 27.47\% & 97.60\% & 26.81\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% Data-Free SST k=5
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=5$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_data_5}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 70.00\% & 70.29\% & 71.00\% & 68.94\% & 71.40\% & 70.09\% & 71.40\% & 70.34\% \\
0.07 & 71.00\% & 70.71\% & 72.20\% & 69.64\% & 70.60\% & 69.44\% & 71.20\% & 70.13\% \\
0.09 & 71.60\% & 69.52\% & 71.00\% & 69.01\% & 72.40\% & 70.04\% & 72.40\% & 70.22\% \\
0.10 & 71.60\% & 68.79\% & 70.60\% & 69.21\% & 71.00\% & 69.76\% & 73.40\% & 69.81\% \\
0.12 & 69.60\% & 68.03\% & 71.00\% & 68.07\% & 70.60\% & 69.43\% & 74.00\% & 69.18\% \\
0.15 & 68.00\% & 67.30\% & 67.20\% & 67.27\% & 71.40\% & 69.72\% & 72.00\% & 69.37\% \\
0.20 & 66.80\% & 64.60\% & 65.60\% & 64.36\% & 68.80\% & 68.25\% & 69.80\% & 67.86\% \\
0.30 & 64.60\% & 60.43\% & 65.20\% & 60.27\% & 70.60\% & 65.34\% & 69.40\% & 64.19\% \\
0.40 & 64.00\% & 57.05\% & 63.40\% & 56.44\% & 67.20\% & 62.56\% & 66.00\% & 62.17\% \\
0.50 & 68.80\% & 52.03\% & 68.40\% & 51.92\% & 64.20\% & 59.38\% & 66.00\% & 59.30\% \\
0.60 & 67.40\% & 48.63\% & 70.60\% & 48.41\% & 67.60\% & 57.32\% & 66.20\% & 57.02\% \\
0.70 & 66.80\% & 46.11\% & 69.40\% & 45.81\% & 66.00\% & 54.40\% & 69.60\% & 54.33\% \\
0.80 & 66.80\% & 44.79\% & 68.20\% & 44.61\% & 71.00\% & 52.33\% & 71.00\% & 51.07\% \\
0.90 & 68.60\% & 42.98\% & 70.00\% & 42.38\% & 69.00\% & 49.82\% & 70.40\% & 49.36\% \\
1.00 & 67.40\% & 41.07\% & 72.00\% & 40.74\% & 70.40\% & 47.75\% & 70.00\% & 47.53\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier


% Data-Free SST k=10
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=10$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_data_10}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.80\% & 69.82\% & 70.20\% & 70.27\% & 71.60\% & 69.89\% & 71.20\% & 70.30\% \\
0.07 & 68.60\% & 69.33\% & 69.60\% & 70.10\% & 71.00\% & 69.71\% & 70.40\% & 70.13\% \\
0.09 & 69.40\% & 67.66\% & 67.40\% & 68.24\% & 71.00\% & 69.45\% & 71.40\% & 69.41\% \\
0.10 & 68.60\% & 68.23\% & 70.00\% & 67.45\% & 72.20\% & 69.36\% & 71.40\% & 69.75\% \\
0.12 & 70.00\% & 66.97\% & 69.60\% & 65.96\% & 72.20\% & 69.00\% & 70.80\% & 69.43\% \\
0.15 & 71.60\% & 63.85\% & 70.80\% & 63.25\% & 68.40\% & 69.08\% & 70.00\% & 68.44\% \\
0.20 & 66.60\% & 60.58\% & 66.20\% & 61.01\% & 69.40\% & 67.22\% & 68.00\% & 67.13\% \\
0.30 & 69.20\% & 54.68\% & 68.60\% & 54.35\% & 68.00\% & 64.50\% & 69.40\% & 63.59\% \\
0.40 & 71.20\% & 49.28\% & 71.60\% & 48.35\% & 66.40\% & 60.19\% & 67.60\% & 59.85\% \\
0.50 & 71.00\% & 44.26\% & 72.80\% & 44.68\% & 67.60\% & 58.78\% & 70.40\% & 58.16\% \\
0.60 & 70.80\% & 41.32\% & 72.40\% & 41.07\% & 68.80\% & 55.36\% & 71.00\% & 54.61\% \\
0.70 & 72.20\% & 39.18\% & 73.80\% & 39.08\% & 69.20\% & 51.92\% & 75.20\% & 50.69\% \\
0.80 & 73.60\% & 37.82\% & 76.80\% & 37.93\% & 72.20\% & 49.61\% & 74.00\% & 48.12\% \\
0.90 & 76.80\% & 36.73\% & 77.80\% & 37.37\% & 72.20\% & 47.27\% & 75.80\% & 46.68\% \\
1.00 & 77.40\% & 35.96\% & 81.20\% & 35.74\% & 72.40\% & 45.72\% & 79.00\% & 45.17\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% Data-Free SST k=20
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=20$: A5 (RepliQA) + A7 (Safety)}
\label{tab:res_a5_sst_data_20}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA & JB Res. & RepliQA \\
\hline
0.05 & 69.80\% & 69.82\% & 70.20\% & 70.27\% & 71.60\% & 69.89\% & 71.20\% & 70.30\% \\
0.07 & 68.60\% & 69.33\% & 69.60\% & 70.10\% & 71.00\% & 69.71\% & 70.40\% & 70.13\% \\
0.09 & 69.40\% & 67.66\% & 67.40\% & 68.24\% & 71.00\% & 69.45\% & 71.40\% & 69.41\% \\
0.10 & 68.60\% & 68.23\% & 70.00\% & 67.45\% & 72.20\% & 69.36\% & 71.40\% & 69.75\% \\
0.12 & 70.00\% & 66.97\% & 69.60\% & 65.96\% & 72.20\% & 69.00\% & 70.80\% & 69.43\% \\
0.15 & 71.60\% & 63.85\% & 70.80\% & 63.25\% & 68.40\% & 69.08\% & 70.00\% & 68.44\% \\
0.20 & 66.60\% & 60.58\% & 66.20\% & 61.01\% & 69.40\% & 67.22\% & 68.00\% & 67.13\% \\
0.30 & 69.20\% & 54.68\% & 68.60\% & 54.35\% & 68.00\% & 64.50\% & 69.40\% & 63.59\% \\
0.40 & 71.20\% & 49.28\% & 71.60\% & 48.35\% & 66.40\% & 60.19\% & 67.60\% & 59.85\% \\
0.50 & 71.00\% & 44.26\% & 72.80\% & 44.68\% & 67.60\% & 58.78\% & 70.40\% & 58.16\% \\
0.60 & 70.80\% & 41.32\% & 72.40\% & 41.07\% & 68.80\% & 55.36\% & 71.00\% & 54.61\% \\
0.70 & 72.20\% & 39.18\% & 73.80\% & 39.08\% & 69.20\% & 51.92\% & 75.20\% & 50.69\% \\
0.80 & 73.60\% & 37.82\% & 76.80\% & 37.93\% & 72.20\% & 49.61\% & 74.00\% & 48.12\% \\
0.90 & 76.80\% & 36.73\% & 77.80\% & 37.37\% & 72.20\% & 47.27\% & 75.80\% & 46.68\% \\
1.00 & 77.40\% & 35.96\% & 81.20\% & 35.74\% & 72.40\% & 45.72\% & 79.00\% & 45.17\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

\subsubsection{Model Pair: A6 (Alpaca) + A7 (Safety)}
\mbox{}

% base model
\begin{table}[h]
\centering
\caption{Baselines: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_base}
\begin{tabular}{c|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Task Arithmetic}} & \multicolumn{2}{c|}{\textbf{TIES}} & \multicolumn{2}{c}{\textbf{DARE}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 76.20\% & 71.08\% & 73.60\% & 60.21\% & 0.00\% & 0.00\% \\
0.07 & 75.40\% & 70.77\% & 78.00\% & 60.00\% & 0.00\% & 0.00\% \\
0.09 & 76.40\% & 69.38\% & 76.00\% & 59.72\% & 0.00\% & 0.00\% \\
0.10 & 74.20\% & 68.95\% & 75.80\% & 58.56\% & 0.00\% & 0.02\% \\
0.12 & 75.80\% & 67.94\% & 77.80\% & 57.86\% & 0.00\% & 0.03\% \\
0.15 & 76.20\% & 66.46\% & 79.00\% & 56.39\% & 0.00\% & 0.09\% \\
0.20 & 76.00\% & 63.32\% & 80.00\% & 55.19\% & 0.00\% & 0.12\% \\
0.30 & 78.80\% & 57.69\% & 83.80\% & 51.54\% & 0.00\% & 0.67\% \\
0.40 & 85.20\% & 52.36\% & 89.60\% & 46.62\% & 1.00\% & 1.79\% \\
0.50 & 89.40\% & 46.52\% & 94.80\% & 41.86\% & 4.40\% & 7.33\% \\
0.60 & 95.20\% & 41.00\% & 96.20\% & 39.67\% & 26.40\% & 8.14\% \\
0.70 & 98.20\% & 36.38\% & 98.20\% & 36.48\% & 15.20\% & 6.90\% \\
0.80 & 99.60\% & 32.45\% & 99.60\% & 33.23\% & 8.40\% & 6.92\% \\
0.90 & 100.00\% & 29.53\% & 100.00\% & 30.84\% & 16.80\% & 5.53\% \\
1.00 & 100.00\% & 26.90\% & 99.60\% & 30.54\% & 0.00\% & 1.87\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% sst soft k=20
\begin{table}[h]
\centering
\caption{SST-Merge Addactive layerwise=True/False k=Soft : A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_soft}
\begin{tabular}{c|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{SST-Merge layerwise=False}} & \multicolumn{2}{c}{\textbf{SST-Merge layerwise=True}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.00\% & 70.11\% & 74.40\% & 70.27\% \\
0.07 & 76.40\% & 70.20\% & 75.60\% & 70.68\% \\
0.09 & 76.00\% & 70.03\% & 76.20\% & 70.28\% \\
0.10 & 76.40\% & 69.84\% & 75.20\% & 70.04\% \\
0.12 & 75.40\% & 70.03\% & 76.00\% & 70.07\% \\
0.15 & 75.40\% & 68.93\% & 79.00\% & 69.14\% \\
0.20 & 77.20\% & 68.73\% & 80.00\% & 68.79\% \\
0.30 & 80.80\% & 67.90\% & 80.00\% & 67.77\% \\
0.40 & 83.20\% & 66.07\% & 83.20\% & 66.06\% \\
0.50 & 82.20\% & 64.31\% & 80.80\% & 64.50\% \\
0.60 & 81.00\% & 62.85\% & 82.60\% & 62.90\% \\
0.70 & 82.00\% & 62.33\% & 82.60\% & 62.53\% \\
0.80 & 80.80\% & 61.63\% & 82.60\% & 61.94\% \\
0.90 & 81.80\% & 60.41\% & 83.60\% & 60.50\% \\
1.00 & 82.00\% & 58.97\% & 82.60\% & 59.15\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% SST k=5
% \color{red}
SST k=5
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=5$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_5}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.40\% & 70.37\% & 73.20\% & 70.55\% & 72.80\% & 71.07\% & 73.80\% & 70.43\% \\
0.07 & 76.00\% & 70.44\% & 75.80\% & 70.42\% & 73.20\% & 70.32\% & 72.80\% & 69.78\% \\
0.09 & 75.40\% & 70.16\% & 75.40\% & 70.53\% & 73.80\% & 70.54\% & 76.40\% & 70.14\% \\
0.10 & 75.20\% & 69.77\% & 75.80\% & 70.04\% & 76.00\% & 70.59\% & 76.80\% & 70.07\% \\
0.12 & 76.00\% & 69.86\% & 74.60\% & 69.80\% & 77.20\% & 69.79\% & 76.60\% & 69.92\% \\
0.15 & 77.40\% & 69.42\% & 77.40\% & 69.41\% & 77.80\% & 68.71\% & 77.20\% & 68.32\% \\
0.20 & 80.00\% & 68.53\% & 80.40\% & 69.14\% & 78.00\% & 66.99\% & 75.80\% & 66.21\% \\
0.30 & 81.00\% & 67.85\% & 81.50\% & 68.32\% & 78.40\% & 63.92\% & 79.20\% & 62.42\% \\
0.40 & 80.50\% & 66.33\% & 80.50\% & 67.53\% & 79.80\% & 60.06\% & 78.80\% & 59.29\% \\
0.50 & 82.00\% & 65.35\% & 79.00\% & 63.21\% & 83.60\% & 57.45\% & 84.20\% & 56.19\% \\
0.60 & 82.04\% & 65.84\% & 80.07\% & 64.15\% & 84.80\% & 55.27\% & 85.00\% & 53.57\% \\
0.70 & 84.10\% & 62.40\% & 81.10\% & 62.35\% & 87.40\% & 53.04\% & 88.60\% & 52.06\% \\
0.80 & 83.40\% & 62.31\% & 80.90\% & 62.22\% & 89.40\% & 50.73\% & 89.40\% & 49.40\% \\
0.90 & 84.00\% & 61.65\% & 82.30\% & 61.63\% & 89.40\% & 49.18\% & 90.60\% & 47.06\% \\
1.00 & 84.00\% & 60.03\% & 82.00\% & 59.89\% & 91.60\% & 46.91\% & 93.20\% & 44.72\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier
% \color{black}

% SST k=10
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=10$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_10}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.40\% & 70.86\% & 72.20\% & 70.68\% & 74.00\% & 70.50\% & 72.40\% & 70.52\% \\
0.07 & 76.20\% & 70.41\% & 75.60\% & 70.20\% & 73.80\% & 70.40\% & 74.20\% & 70.11\% \\
0.09 & 75.60\% & 69.95\% & 76.00\% & 70.22\% & 76.00\% & 70.39\% & 75.60\% & 70.18\% \\
0.10 & 74.20\% & 70.33\% & 75.20\% & 70.02\% & 78.20\% & 70.63\% & 77.80\% & 69.48\% \\
0.12 & 76.60\% & 70.09\% & 77.00\% & 69.93\% & 77.20\% & 69.85\% & 78.40\% & 69.29\% \\
0.15 & 77.40\% & 69.18\% & 78.80\% & 69.09\% & 78.40\% & 69.01\% & 75.00\% & 68.29\% \\
0.20 & 80.00\% & 68.85\% & 78.00\% & 68.75\% & 77.00\% & 67.14\% & 76.80\% & 65.99\% \\
0.30 & 77.60\% & 67.85\% & 81.60\% & 67.62\% & 78.40\% & 63.92\% & 78.80\% & 62.97\% \\
0.40 & 81.20\% & 66.33\% & 82.00\% & 66.13\% & 82.20\% & 59.59\% & 79.60\% & 58.92\% \\
0.50 & 78.00\% & 64.53\% & 81.40\% & 64.21\% & 81.60\% & 57.34\% & 83.20\% & 56.26\% \\
0.60 & 82.00\% & 62.89\% & 81.40\% & 63.18\% & 84.20\% & 55.18\% & 83.40\% & 53.46\% \\
0.70 & 84.00\% & 62.10\% & 83.00\% & 62.75\% & 88.60\% & 53.51\% & 89.60\% & 52.28\% \\
0.80 & 82.60\% & 61.31\% & 81.60\% & 62.22\% & 89.40\% & 50.78\% & 89.40\% & 49.27\% \\
0.90 & 82.40\% & 60.34\% & 82.40\% & 61.53\% & 91.20\% & 48.43\% & 90.00\% & 46.33\% \\
1.00 & 82.20\% & 60.03\% & 80.80\% & 60.59\% & 92.00\% & 47.08\% & 93.60\% & 44.41\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% SST k=20
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=20$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_20}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 72.60\% & 70.53\% & 76.00\% & 70.91\% & 73.80\% & 70.60\% & 74.00\% & 70.28\% \\
0.07 & 76.60\% & 70.77\% & 76.00\% & 70.46\% & 73.60\% & 70.44\% & 74.60\% & 69.90\% \\
0.09 & 75.80\% & 70.36\% & 77.40\% & 70.36\% & 77.00\% & 69.54\% & 76.00\% & 69.25\% \\
0.10 & 76.00\% & 70.19\% & 75.20\% & 70.69\% & 75.60\% & 69.09\% & 75.80\% & 69.21\% \\
0.12 & 76.80\% & 69.96\% & 75.80\% & 70.23\% & 74.20\% & 69.88\% & 74.60\% & 68.97\% \\
0.15 & 77.20\% & 69.78\% & 78.00\% & 70.03\% & 76.80\% & 69.21\% & 75.20\% & 68.29\% \\
0.20 & 78.80\% & 68.77\% & 79.60\% & 68.95\% & 74.40\% & 67.40\% & 74.40\% & 66.98\% \\
0.30 & 80.00\% & 67.71\% & 82.20\% & 67.64\% & 78.60\% & 64.00\% & 75.20\% & 64.06\% \\
0.40 & 81.00\% & 65.53\% & 82.60\% & 66.01\% & 77.00\% & 62.65\% & 76.60\% & 62.00\% \\
0.50 & 79.40\% & 64.31\% & 80.80\% & 63.87\% & 77.40\% & 60.53\% & 76.80\% & 59.51\% \\
0.60 & 83.20\% & 63.51\% & 81.20\% & 63.09\% & 80.00\% & 57.97\% & 79.60\% & 58.28\% \\
0.70 & 83.40\% & 62.24\% & 84.20\% & 62.60\% & 81.80\% & 56.74\% & 80.20\% & 55.84\% \\
0.80 & 83.00\% & 61.72\% & 85.00\% & 61.90\% & 81.40\% & 55.84\% & 80.00\% & 54.90\% \\
0.90 & 84.00\% & 61.69\% & 82.00\% & 61.26\% & 80.60\% & 54.32\% & 78.20\% & 53.74\% \\
1.00 & 79.60\% & 60.62\% & 79.40\% & 59.94\% & 82.20\% & 53.64\% & 80.40\% & 53.39\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% SST k=50
\begin{table}[h]
\centering
\caption{SST-Merge layerwise= True/False $k=50$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_50}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.60\% & 70.75\% & 76.20\% & 70.46\% & 74.20\% & 70.43\% & 74.60\% & 70.14\% \\
0.07 & 75.20\% & 70.89\% & 74.20\% & 70.50\% & 75.00\% & 70.37\% & 74.20\% & 70.29\% \\
0.09 & 76.60\% & 70.53\% & 76.40\% & 70.15\% & 78.20\% & 70.67\% & 76.40\% & 69.65\% \\
0.10 & 76.00\% & 70.36\% & 75.80\% & 69.78\% & 76.20\% & 70.21\% & 74.60\% & 69.57\% \\
0.12 & 77.80\% & 70.33\% & 77.60\% & 70.10\% & 75.40\% & 69.85\% & 77.60\% & 68.61\% \\
0.15 & 77.80\% & 69.77\% & 78.20\% & 69.49\% & 77.60\% & 68.77\% & 76.20\% & 67.42\% \\
0.20 & 78.60\% & 69.62\% & 77.80\% & 69.09\% & 78.60\% & 65.71\% & 80.00\% & 65.28\% \\
0.30 & 80.60\% & 67.54\% & 81.40\% & 67.57\% & 77.20\% & 63.78\% & 78.00\% & 61.76\% \\
0.40 & 81.60\% & 66.29\% & 80.80\% & 65.84\% & 78.40\% & 59.08\% & 79.20\% & 57.79\% \\
0.50 & 82.40\% & 64.37\% & 79.20\% & 64.51\% & 81.20\% & 56.49\% & 83.60\% & 55.43\% \\
0.60 & 82.80\% & 62.95\% & 80.40\% & 62.74\% & 84.20\% & 54.86\% & 84.40\% & 53.23\% \\
0.70 & 82.80\% & 62.82\% & 82.00\% & 62.09\% & 90.20\% & 52.97\% & 90.60\% & 51.44\% \\
0.80 & 84.20\% & 62.52\% & 81.40\% & 61.15\% & 90.80\% & 50.22\% & 92.20\% & 47.97\% \\
0.90 & 82.60\% & 61.18\% & 80.40\% & 60.57\% & 92.20\% & 48.22\% & 92.00\% & 46.32\% \\
1.00 & 83.60\% & 59.87\% & 81.20\% & 59.50\% & 94.40\% & 46.00\% & 94.40\% & 44.92\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% \color{red}
% Data-Free SST k=5
Data-Free SST k=5
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=5$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_data_5}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.20\% & 69.91\% & 72.60\% & 69.71\% & 73.40\% & 70.07\% & 73.00\% & 70.43\% \\
0.07 & 72.60\% & 70.07\% & 74.00\% & 70.36\% & 74.80\% & 69.97\% & 74.40\% & 70.29\% \\
0.09 & 73.80\% & 69.80\% & 74.40\% & 69.67\% & 77.80\% & 68.99\% & 76.60\% & 69.01\% \\
0.10 & 74.40\% & 69.98\% & 74.60\% & 69.92\% & 76.40\% & 68.54\% & 77.80\% & 68.59\% \\
0.12 & 74.60\% & 69.70\% & 73.40\% & 70.26\% & 77.20\% & 67.52\% & 76.80\% & 67.82\% \\
0.15 & 74.80\% & 70.46\% & 75.00\% & 70.49\% & 72.40\% & 65.13\% & 74.80\% & 65.23\% \\
0.20 & 74.00\% & 69.96\% & 73.80\% & 70.06\% & 73.60\% & 62.86\% & 73.20\% & 62.87\% \\
0.30 & 74.40\% & 69.39\% & 76.20\% & 69.59\% & 71.60\% & 57.54\% & 70.20\% & 57.74\% \\
0.40 & 76.40\% & 68.82\% & 76.00\% & 69.84\% & 69.20\% & 53.21\% & 69.40\% & 53.00\% \\
0.50 & 78.00\% & 68.69\% & 73.00\% & 68.44\% & 75.20\% & 48.85\% & 76.60\% & 49.15\% \\
0.60 & 76.60\% & 67.84\% & 74.20\% & 67.71\% & 82.80\% & 43.45\% & 83.40\% & 43.83\% \\
0.70 & 78.60\% & 67.47\% & 75.60\% & 67.43\% & 83.60\% & 41.56\% & 86.00\% & 41.06\% \\
0.80 & 76.60\% & 66.63\% & 75.20\% & 66.91\% & 78.00\% & 27.05\% & 77.40\% & 26.23\% \\
0.90 & 77.60\% & 65.90\% & 77.20\% & 65.75\% & 84.00\% & 40.24\% & 83.40\% & 40.24\% \\
1.00 & 77.20\% & 65.13\% & 76.40\% & 64.45\% & 98.20\% & 40.00\% & 98.00\% & 40.00\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier

% Data-Free SST k=10
Data-Free SST k=10
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=10$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_data_10}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 74.40\% & 70.21\% & 74.60\% & 70.12\% & 73.20\% & 70.25\% & 73.20\% & 70.81\% \\
0.07 & 72.40\% & 70.12\% & 75.60\% & 70.61\% & 75.80\% & 69.69\% & 76.20\% & 69.49\% \\
0.09 & 73.80\% & 69.99\% & 75.40\% & 70.39\% & 76.40\% & 68.45\% & 75.60\% & 68.19\% \\
0.10 & 75.20\% & 70.37\% & 75.00\% & 70.50\% & 74.60\% & 68.33\% & 76.40\% & 68.08\% \\
0.12 & 76.40\% & 70.25\% & 71.60\% & 69.67\% & 76.40\% & 66.85\% & 76.60\% & 67.13\% \\
0.15 & 74.00\% & 69.88\% & 74.20\% & 70.03\% & 74.40\% & 65.47\% & 75.40\% & 65.37\% \\
0.20 & 77.00\% & 69.22\% & 75.60\% & 69.45\% & 75.20\% & 62.63\% & 75.60\% & 62.83\% \\
0.30 & 76.80\% & 68.48\% & 77.20\% & 68.55\% & 74.40\% & 57.93\% & 75.40\% & 57.87\% \\
0.40 & 77.20\% & 67.05\% & 77.40\% & 67.02\% & 74.60\% & 52.66\% & 74.60\% & 52.93\% \\
0.50 & 78.20\% & 65.12\% & 78.20\% & 65.04\% & 80.40\% & 47.72\% & 81.20\% & 47.52\% \\
0.60 & 81.60\% & 64.06\% & 78.60\% & 63.90\% & 86.20\% & 43.07\% & 85.60\% & 43.28\% \\
0.70 & 79.80\% & 63.03\% & 79.20\% & 63.14\% & 91.00\% & 39.06\% & 92.00\% & 39.36\% \\
0.80 & 83.60\% & 62.72\% & 79.80\% & 62.62\% & 94.20\% & 37.91\% & 96.00\% & 37.95\% \\
0.90 & 80.60\% & 61.98\% & 79.20\% & 61.33\% & 92.60\% & 36.74\% & 92.60\% & 37.50\% \\
1.00 & 81.40\% & 61.39\% & 78.80\% & 60.84\% & 97.00\% & 40.00\% & 96.80\% & 40.00\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier


% Data-Free SST k=20
Data-Free SST k=20
\begin{table}[h]
\centering
\caption{Data-Free SST-Merge layerwise= True/False $k=20$: A6 (Alpaca) + A7 (Safety)}
\label{tab:res_a6_sst_data_20}
\begin{tabular}{c|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Additive Lw=True}} & \multicolumn{2}{c|}{\textbf{Additive Lw=False}} & \multicolumn{2}{c|}{\textbf{Interpolation lw=True}}& \multicolumn{2}{c}{\textbf{Interpolation lw=False}} \\
$\alpha$ & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca & JB Res. & Alpaca \\
\hline
0.05 & 73.40\% & 70.29\% & 72.20\% & 70.33\% & 73.40\% & 70.58\% & 72.60\% & 70.45\% \\
0.07 & 75.00\% & 70.19\% & 75.60\% & 70.58\% & 74.20\% & 69.73\% & 72.60\% & 70.45\% \\
0.09 & 74.60\% & 70.57\% & 73.80\% & 70.39\% & 75.80\% & 68.62\% & 74.80\% & 68.92\% \\
0.10 & 75.20\% & 70.54\% & 75.00\% & 69.64\% & 75.40\% & 68.02\% & 74.60\% & 68.13\% \\
0.12 & 76.60\% & 70.19\% & 76.40\% & 69.73\% & 76.00\% & 67.28\% & 76.80\% & 67.18\% \\
0.15 & 74.60\% & 69.08\% & 74.00\% & 69.77\% & 75.80\% & 65.60\% & 77.60\% & 65.72\% \\
0.20 & 75.80\% & 68.57\% & 74.80\% & 69.13\% & 75.40\% & 62.70\% & 76.20\% & 62.60\% \\
0.30 & 78.00\% & 66.76\% & 78.80\% & 67.04\% & 76.40\% & 57.57\% & 77.40\% & 57.32\% \\
0.40 & 77.20\% & 65.79\% & 80.00\% & 65.95\% & 79.80\% & 51.41\% & 81.40\% & 51.23\% \\
0.50 & 79.60\% & 64.26\% & 81.80\% & 64.31\% & 83.00\% & 45.60\% & 83.40\% & 45.75\% \\
0.60 & 80.80\% & 63.00\% & 80.20\% & 63.00\% & 88.60\% & 41.60\% & 90.60\% & 41.42\% \\
0.70 & 83.00\% & 61.95\% & 81.20\% & 61.86\% & 91.40\% & 37.75\% & 92.60\% & 37.74\% \\
0.80 & 84.40\% & 61.46\% & 82.60\% & 60.92\% & 91.80\% & 33.41\% & 94.00\% & 33.83\% \\
0.90 & 82.40\% & 60.38\% & 84.80\% & 60.57\% & 94.00\% & 32.22\% & 94.40\% & 32.75\% \\
1.00 & 84.60\% & 59.10\% & 82.80\% & 59.02\% & 90.80\% & 31.01\% & 92.80\% & 30.78\% \\
\hline
\end{tabular}
\end{table}
\FloatBarrier
% \color{black}

\subsection{Discussion on the Behavior of Data-Free SST (Interpolation)}
\subsubsection{Comparison between Baselines and SST-Merge}
The baseline methods (Task Arithmetic, TIES, and DARE) exhibit a pronounced trade-off in which improving Safety (JB Res.) leads to a sharp degradation in Utility (RepliQA / Alpaca). 
In particular, DARE causes utility to collapse even at relatively small values of $\alpha$. 
In contrast, SST-Merge substantially mitigates utility degradation while achieving high safety performance.

\subsubsection{Additive vs. Interpolation Injection}
Comparing the two injection schemes of SST-Merge, the \textbf{interpolation} variant generally achieves a better balance between utility preservation and safety improvement. 
While the additive variant tends to saturate in safety performance beyond a certain $\alpha$, the interpolation variant gradually reduces utility as $\alpha$ increases and is capable of raising JB Res. close to 100\%. 

\subsubsection{Effect of the Hyperparameter $k$ and Layer-wise Configuration}
A clear trend can also be observed with respect to the Top-$k$ ratio. 
When $k$ is small (e.g., $k=5, 10$), only a limited number of parameters are modified, resulting in stronger utility preservation, although the maximum achievable JB Res. under extreme $\alpha$ may be constrained. 
Conversely, when $k$ is large (e.g., $k=50$), a broader set of parameters is updated, leading to faster safety improvement but also greater utility degradation. 
These results suggest that the model behavior can be flexibly controlled by selecting $k$ according to deployment requirements. 
Furthermore, the layer-wise configuration (Lw=True) is observed in some cases to act as a buffering mechanism, slightly protecting utility while facilitating safety improvement through structured weighting across layers.

\subsubsection{Behavior and Limitations of Data Free SST-Merge}
Data-Free SST-Merge, despite being a computationally efficient approximation, achieves performance comparable to the full FIM-based SST-Merge in settings with small $\alpha$ or under the additive formulation. 
This indicates that using a single magnitude-based importance proxy (e.g., $|W|$) for both utility and safety can provide a reasonably effective approximation.

However, under the interpolation formulation at high values of $\alpha$ (around $\alpha=0.9$), we observe a simultaneous collapse of both JB Res. and utility. 
Since the Data-Free approach determines intervention points solely based on parameter magnitude, it does not account for functional dependencies among parameters. 

\newpage
\subsection{Experimental Plots}
\label{sec:appendix_plots}

This section presents the evaluation plots for all experimental configurations.  
Each graph illustrates the safety–utility trade-off curve, where the horizontal axis represents the RepliQA or Alpaca score (Utility) and the vertical axis represents Jailbreak Resistance (Safety).  
Points located closer to the upper-right region indicate a superior Pareto frontier, reflecting both higher utility and stronger safety.

\subsubsection{A5 (RepliQA) + A7 (Safety) Results}
\mbox{}

% A5+A7:baseline
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/A5_A7_Baseline_Methods.png}
    \caption{A5+A7: Baseline Methods (Task Arithmetic, TIES, DARE)}
    \label{fig:a5_baseline_2}
\end{figure}

\subsubsection{SST-Merge (Proposed)}
\mbox{}
% A5+A7:additive soft
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/A5_A7_SST_Additive_Soft_k20.png}
    \caption{A5+A7: SST-Merge (k=Soft Additive) }
    \label{fig:a5_sst_add_k20_soft}
\end{figure}

% A5+A7: SST-Merge (Additive)
\begin{figure}[h]
  \centering
  \label{fig:a5_sst_additive_hard}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Additive_Hard_k5.png}
    \caption{A5+A7: SST-Merge (Additive Hard) $k=5$}
    \label{fig:a5_sst_add_k5_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Additive_Hard_k10.png}
    \caption{A5+A7: SST-Merge (Additive Hard) $k=10$}
    \label{fig:a5_sst_add_k10_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Additive_Hard_k20.png}
    \caption{A5+A7: SST-Merge (Additive Hard) $k=20$}
    \label{fig:a5_sst_add_k20_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Additive_Hard_k50.png}
    \caption{A5+A7: SST-Merge (Additive Hard) $k=50$}
    \label{fig:a5_sst_add_k50_hard}
  \end{subfigure}
  
  \caption{A5+A7: SST-Merge (k=Hard Additive)}
\end{figure}

% A5+A7: SST-Merge (Interpolation)
\begin{figure}[h]
  \centering
  \label{fig:a5_sst_interpolation}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Interpolation_k5.png}
    \caption{A5+A7: SST-Merge (Interpolation) $k=5$}
    \label{fig:a5_sst_interpolation_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Interpolation_k10.png}
    \caption{A5+A7: SST-Merge (Interpolation) $k=10$}
    \label{fig:a5_sst_interpolation_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Interpolation_k20.png}
    \caption{A5+A7: SST-Merge (Interpolation) $k=20$}
    \label{fig:a5_sst_interpolation_k20}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_SST_Interpolation_k50.png}
    \caption{A5+A7: SST-Merge (Interpolation) $k=50$}
    \label{fig:a5_sst_interpolation_k50}
  \end{subfigure}
  
  \caption{A5+A7: SST-Merge (Interpolation)}
\end{figure}
\FloatBarrier


\subsubsection{Data-Free SST}

% A5+A7: Data-Free SST (Additive)
\begin{figure}[h]
  \centering
  \label{fig:a5_sst_data_free_additive}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Additive_k5.png}
    \caption{A5+A7: Data-Free SST (Additive) $k=5$}
    \label{fig:a5_sst_data_free_add_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Additive_k10.png}
    \caption{A5+A7: Data-Free SST (Additive) $k=10$}
    \label{fig:a5_sst_data_free_add_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Additive_k20.png}
    \caption{A5+A7: Data-Free SST (Additive) $k=20$}
    \label{fig:a5_sst_data_free_add_k20}
  \end{subfigure}
  \caption{A5+A7: Data-Free SST (Additive)}
\end{figure}
\FloatBarrier

% A5+A7: Data-Free SST (Interpolation)
\begin{figure}[h]
  \centering
  \label{fig:a5_sst_data_free_interpolation}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Interpolation_k5.png}
    \caption{A5+A7: Data-Free SST (Interpolation) $k=5$}
    \label{fig:a5_sst_data_free_interpolation_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Interpolation_k10.png}
    \caption{A5+A7: Data-Free SST (Interpolation) $k=10$}
    \label{fig:a5_sst_data_free_interpolation_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A5_A7_DataFree_Interpolation_k20.png}
    \caption{A5+A7: Data-Free SST (Interpolation) $k=20$}
    \label{fig:a5_sst_data_free_interpolation_k20}
  \end{subfigure}
  \caption{A5+A7: Data-Free SST (Interpolation)}
\end{figure}
\FloatBarrier

\subsubsection{A6 (Alpaca) + A7 (Safety) Results}
\mbox{}
% baseline
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/A6_A7_Baseline_Methods.png}
    \caption{A6+A7: Baseline Methods (Task Arithmetic, TIES, DARE)}
    \label{fig:a6_baseline}
\end{figure}
\FloatBarrier

\subsubsection{SST-Merge (Proposed)}
\mbox{}
% A6+A7:additive soft
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/A6_A7_SST_Additive_Soft_k20.png}
    \caption{A6+A7: SST-Merge (k=Soft Additive) }
    \label{fig:a6_baseline}
\end{figure}
\FloatBarrier

% A6+A7: SST-Merge (Additive)
\begin{figure}[h]
  \centering
  \label{fig:a6_sst_additive_hard}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Additive_Hard_k5.png}
    \caption{A6+A7: SST-Merge (Additive Hard) $k=5$}
    \label{fig:a6_sst_add_k5_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Additive_Hard_k10.png}
    \caption{A6+A7: SST-Merge (Additive Hard) $k=10$}
    \label{fig:a6_sst_add_k10_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Additive_Hard_k20.png}
    \caption{A6+A7: SST-Merge (Additive Hard) $k=20$}
    \label{fig:a6_sst_add_k20_hard}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Additive_Hard_k50.png}
    \caption{A6+A7: SST-Merge (Additive Hard) $k=50$}
    \label{fig:a6_sst_add_k50_hard}
  \end{subfigure}
  
  \caption{A6+A7: SST-Merge (k=Hard Additive)}
\end{figure}

% A6+A7: SST-Merge (Interpolation)
\begin{figure}[h]
  \centering
  \label{fig:a6_sst_interpolation}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Interpolation_k5.png}
    \caption{A6+A7: SST-Merge (Interpolation) $k=5$}
    \label{fig:a6_sst_interpolation_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Interpolation_k10.png}
    \caption{A6+A7: SST-Merge (Interpolation) $k=10$}
    \label{fig:a6_sst_interpolation_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_SST_Interpolation_k20.png}
    \caption{A6+A7: SST-Merge (Interpolation) $k=20$}
    \label{fig:a6_sst_interpolation_k20}
  \end{subfigure}
  \caption{A6+A7: SST-Merge (Interpolation)}
\end{figure}
\FloatBarrier


\subsubsection{Data-Free SST}
\mbox{}

% A6+A7: Data-Free SST (Additive)
\begin{figure}[h]
  \centering
  \label{fig:a6_sst_data_free_additive}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Additive_k5.png}
    \caption{A6+A7: Data-Free SST (Additive) $k=5$}
    \label{fig:a6_sst_data_free_add_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Additive_k10.png}
    \caption{A6+A7: Data-Free SST (Additive) $k=10$}
    \label{fig:a6_sst_data_free_add_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Additive_k20.png}
    \caption{A6+A7: Data-Free SST (Additive) $k=20$}
    \label{fig:a6_sst_data_free_add_k20}
  \end{subfigure}
  \caption{A6+A7: Data-Free SST (Additive)}
\end{figure}
\FloatBarrier

% A6+A7: Data-Free SST (Interpolation)
\begin{figure}[h]
  \centering
  \label{fig:a6_sst_data_free_interpolation}
  
  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Interpolation_k5.png}
    \caption{A6+A7: Data-Free SST (Interpolation) $k=5$}
    \label{fig:a6_sst_data_free_interpolation_k5}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Interpolation_k10.png}
    \caption{A6+A7: Data-Free SST (Interpolation) $k=10$}
    \label{fig:a6_sst_data_free_interpolation_k10}
  \end{subfigure}

  \vspace{0.5em}

  \begin{subfigure}{0.85\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/A6_A7_DataFree_Interpolation_k20.png}
    \caption{A6+A7: Data-Free SST (Interpolation) $k=20$}
    \label{fig:a6_sst_data_free_interpolation_k20}
  \end{subfigure}
  \caption{A6+A7: Data-Free SST (Interpolation)}
\end{figure}
\FloatBarrier
% \fi
% that's all folks
\end{document}

