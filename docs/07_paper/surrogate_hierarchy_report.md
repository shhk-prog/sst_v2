# SST-Merge 論文向け：Surrogate Hierarchy と検証方針の整理レポート

本稿は、レビュアーに「FIM の proxy の proxy の proxy」と読まれないようにするための**主張の階層**と、**理論で埋める部分／実験で埋める部分**、**最低限の追加実験**を一枚にまとめたメモである。

**追記版**：以下に**記号の定義**と、各段の**主要な数式**をできるだけ明示した。論文本文にそのまま流し込みやすい密度を意識している。

> **注**  
> 数式は、GitHub / VS Code / Obsidian / Typora などの **MathJax / KaTeX 対応 Markdown レンダラ**を想定している。

---

## 0. 記号と対象空間（最初に固定しておくと誤解が減る）

- $\theta \in \mathbb{R}^d$：**マージ対象の学習可能パラメータ**  
  実装では **LoRA / adapter 係数をベクトル化したもの**。$d$ はフル重みの次元ではない。

- 分布：良性（utility）$D_b$、有害（safety）$D_h$

- 損失：
  $$
  \mathcal{L}_t(\theta)=\mathbb{E}_{x\sim D_t}[\ell(x;\theta)],
  \qquad t\in\{b,h\}
  $$

- （経験的）Fisher：
$$
F_t(\theta)
=
\mathbb{E}_{x\sim D_t}\big[\nabla_\theta \ell(x;\theta)\,\nabla_\theta \ell(x;\theta)^\top\big],
\qquad t\in\{b,h\}
$$

  実装では、$F_t$ をミニバッチ勾配 $g_n$ の標本平均で推定する（経験的 Fisher）。  
  **一般には true Fisher や Hessian と一致しない**ため、本文では **「半正定値な局所感度計量」** として扱うのが安全。

- 数値安定化のため **$\varepsilon>0$** を入れ、以降は $F_b$ を **$F_b+\varepsilon I$** に置き換えたものを正定値として使う。

---

## 1. 問題意識：なぜ「理論だけ」「実験だけ」だと弱いか

- **理論だけ**：  
  Full GEVP と実装（座標マスク・タスクベクトル）の間のギャップを、数式の気持ちだけで埋めようとすると、仮定が強くなりすぎる。

- **実験だけ**：  
  下流タスクの数字が良くても、「何を近似しているのか」「なぜその手続きか」が説明できず、再現性・一般化の議論で詰まりやすい。

**通りやすい二段構え**は次のとおり。

| 区間 | 埋め方 |
|---|---|
| **Full FIM → Diagonal FIM** | **理論でかなり詰める**（座標制約付き surrogate としての厳密化＋摂動・eigengap） |
| **Diagonal FIM → Task Vector Proxy** | **弱い理論＋強い実験**（値の一致は主張しない。順位・二次形式の保存を測る） |

---

## 2. レビュアーに悪く見える「三階建て proxy」

現状の書き方によっては、次のように読まれる。

1. FIM 自体が真の曲率の **proxy**
2. 対角化がさらにその **近似**
3. タスクベクトルが **また proxy**

対策は、「すべて近似」と呼ぶのではなく、**何を厳密に言うか** と **何を surrogate と呼ぶか** を、言語レベルで分離すること。

---

## 3. 推奨フレーム：Surrogate Hierarchy（方針 A）

「Full が真理 → 次々に粗い近似」ではなく、次の三層に整理する。

| レベル | 名前 | 主張の芯 |
|---|---|---|
| **Full SST** | 理想形 | PSD な局所感度計量（理想化された $F_b,F_h$）上での **metric-based subspace selection**（ホワイト化 GEVP / Rayleigh 商） |
| **Diagonal SST** | 座標制約付き surrogate | 候補方向を**座標軸に制限**した上で、**同一の選別則**を解いた結果。Top-$k$ **固有空間**が Top-$k$ **座標**に退化する **exact special case** |
| **Data-free SST** | ランキング surrogate | Fisher 比の**数値そのもの**の再現ではなく、**高 ratio 座標の順位**（およびマスク手続き）をデータ非依存で保つ |

こう書くと、「同じものを段階的に粗くした」とは言い切らずに済む。

### 3.0 Full SST の理想形（何を「厳密に」主張するか）

**Tax / Gain（局所二次モデル）** を、正定値な benign 計量 $F_b\succ 0$ と非負値な harm 計量 $F_h\succeq 0$ 上の二次形式で書く。

$$
\mathrm{Tax}(\Delta\theta)=\tfrac12\,\Delta\theta^\top F_b\,\Delta\theta,
\qquad
\mathrm{Gain}(\Delta\theta)=\Delta\theta^\top F_h\,\Delta\theta
$$

> Gain の係数 $1/2$ は最大化では定数なので省略してよい。

**制約付き最大化（SST の骨格）**：
$$
\max_{\Delta\theta\in\mathbb{R}^d}\ \Delta\theta^\top F_h\,\Delta\theta
\quad\text{s.t.}\quad
\Delta\theta^\top F_b\,\Delta\theta \le c
$$

**一般化 Rayleigh 商**と **一般化固有値問題（GEVP）**：
$$
R(\Delta\theta)
:=
\frac{\Delta\theta^\top F_h\,\Delta\theta}{\Delta\theta^\top F_b\,\Delta\theta},
\qquad
F_h v=\lambda\,F_b v
$$

正定値 $F_b$ の下で、制約がアクティブな内点解の「最も効率の良い方向」は、**$R$ を最大化する方向**として GEVP の最大固有値に対応する固有方向に帰着する。

要点は、**比（コスパ） = 一般化固有値** という読み替えができることにある。

**Safety subspace（上位 $k$ 次元）**：  
$F_h v=\lambda F_b v$ の上位 $k$ 個の固有値に対応する一般化固有ベクトル $v_1,\ldots,v_k$ が張る空間を $\mathcal{S}_k$ とし、パッチ差分 $\Delta_s$ を（例えば $F_b$ 計量に整合した射影で）$\mathcal{S}_k$ へ射影して注入する。これが **Full SST の理想手続き**である。

### 3.1 補足：LoRA とパラメータ空間

- 理論の $\theta$ は、フル 8B 重み空間から書き始めるより、**学習対象の adapter（LoRA）係数ベクトル**に合わせる方が自然である。
- Fisher も、その $\theta$ 上の勾配統計として定義する。

### 3.2 補足：経験的 Fisher と「曲率」

- 経験的 Fisher は **true Fisher や Hessian と一般には一致しない**。
- したがって、防御的な言い方は **「Hessian の近似」** より **「PSD な局所感度 metric」** である。

### 3.3 補足：Full → Diagonal の「飛び」をさらに減らす任意の一段（ブロック対角）

層（または LoRA モジュール）$\ell=1,\ldots,L$ に分割し、各ブロック内だけ相関を残す：

$$
F_t \approx \operatorname{blkdiag}\!\left(F_t^{(1)},\ldots,F_t^{(L)}\right),
\qquad t\in\{b,h\}
$$

各ブロックサイズが小さいなら、そのブロック内で **完全な GEVP** や **ホワイト化作用素**を計算できる。  
そのため、**Full（全次元）** と **座標対角** の間の **中間の説明変数** として強い。

---

## 4. 「飛躍」が三つある：どこをどう埋めるか

### 4.1 飛躍 1：Full SST（GEVP）→ いきなり座標比 Top-$k$

#### 4.1.1 ホワイト化：GEVP を「通常の」固有空間問題に寄せる

正定値 $F_b \succ 0$ に対し、$\Delta\theta = F_b^{-1/2} w$ と置くと、一般化 Rayleigh 商は次のように書ける。

$$
R(\Delta\theta)=\frac{\Delta\theta^\top F_h\,\Delta\theta}{\Delta\theta^\top F_b\,\Delta\theta}=\frac{w^\top \big(F_b^{-1/2} F_h F_b^{-1/2}\big) w}{w^\top w}.
$$

となる。

したがって、ホワイト化作用素
$$
B
:=
(F_b+\varepsilon I)^{-1/2} F_h (F_b+\varepsilon I)^{-1/2}
$$

に対して、$R$ の最大化は **$B$ の最大固有値に対応する固有ベクトル** $u_\star$（$w$ 空間）へ帰着する。  
$F_h v=\lambda F_b v$ の解とは、**$u=F_b^{1/2}v$** の対応で結びつく。

**要点**：  
「安全／有用コスパ」は **$B$ の固有値**として読める。

#### 4.1.2 対角 surrogate：座標制約を入れると Top-$k$ 固有空間が Top-$k$ 座標に退化する

推定対角を
$$
D_b=\operatorname{diag}(f_{b,1},\ldots,f_{b,d}),
\qquad
D_h=\operatorname{diag}(f_{h,1},\ldots,f_{h,d})
$$

とする。このとき

$$
B_{\mathrm{diag}}:=(D_b+\varepsilon I)^{-1/2} D_h (D_b+\varepsilon I)^{-1/2}=\operatorname{diag}(\lambda_1,\ldots,\lambda_d)
$$

ただし

$$
\lambda_i:=\frac{f_{h,i}}{f_{b,i}+\varepsilon}=\frac{(D_h)_{ii}}{(D_b)_{ii}+\varepsilon}
$$

である。

対角行列の固有ベクトルは標準基底 $e_i$ なので、$B_{\mathrm{diag}}$ の **上位 $k$ 固有空間**は
$$
\operatorname{span}\{e_i : i\in \operatorname{TopK}(\lambda)\}
$$

となる。

つまり、**「上位 $k$ 固有空間」 = 「上位 $k$ 座標」** が **厳密** に成立する。

#### 4.1.3 マスク注入（実装と直結）

パッチ差分 $\Delta_s$、マスク $m\in\{0,1\}^d$（または連続化した $m\in[0,1]^d$）、スケール $\alpha>0$ として

$$
\Delta\theta=\alpha\,(m\odot\Delta_s)
$$

とする。

Hard Top-$k$ なら
$$
m_i=\mathbb{1}\{i\in\operatorname{TopK}(\lambda)\}
$$

である。

#### 4.1.4 摂動と eigengap（理論的意味を $\delta_k$ に接続）

$B=B_{\mathrm{diag}}+E$、$E:=B-B_{\mathrm{diag}}$ と分解する。  
$B_{\mathrm{diag}}$ の固有値降順を $\lambda_{(1)}\ge\cdots\ge\lambda_{(d)}$ とすると、**Top-$k$ 境界の eigengap** は

$$
\gamma_k := \lambda_{(k)}(B_{\mathrm{diag}})-\lambda_{(k+1)}(B_{\mathrm{diag}})
$$

である。

$\|E\|$ が小さく、$\gamma_k$ が大きいとき、Davis–Kahan 型の主張により、「$B$ の上位 $k$ 固有空間」と「対角 surrogate が選ぶ座標集合」は近づきやすい、と書ける。

実装で使う
$$
\delta_k:=\lambda_{(k)}-\lambda_{(k+1)}
$$

は、上の $\gamma_k$ と同型に、**「境界が不安定 = 部分空間 / Top-$k$ 集合の推定が揺らぎやすい」** という理論説明を与えられる。

---

### 4.2 飛躍 2：対角 Fisher → タスクベクトル proxy

ここは **理論を強くしすぎない** のが重要である。

- **悪い主張**：  
  「タスクベクトル重要度は Fisher の近似」

- **良い主張**：  
  **linearized PEFT 近傍**において、タスクベクトル二乗比が **Fisher 比の座標順位を近似する ranking surrogate** として使える。

> **値の一致は主張しない。**

#### 4.2.1 座標比：Fisher 側とタスクベクトル側

対角 Fisher の比：
$$
\lambda_i := \frac{f_{h,i}}{f_{b,i}+\varepsilon}
$$

タスクベクトル $\Delta_b,\Delta_h\in\mathbb{R}^d$（adapter 差分）からなる **data-free 比**：
$$
\hat\lambda_i := \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2+\varepsilon}
$$

主張の中心は、$\hat\lambda_i\approx \lambda_i$ ではなく、**順位**や **方向二次形式** がどこまで保たれるかである。

#### 4.2.2 弱い理論：線形化＋二次目標（仮定を明示して短く）

タスク $t$ の終点近傍で
$$
\delta_t^\star \in \arg\min_{\delta}\; g_t^\top\delta+\tfrac12\,\delta^\top H_t\delta+\tfrac{\lambda_{\mathrm{reg}}}{2}\|\delta\|^2
$$

と書けるなら、内点では
$$
\delta_t^\star=-(H_t+\lambda_{\mathrm{reg}}I)^{-1}g_t
$$

となる。

**強い仮定** のもとで、実更新 $\Delta_t$ がこの構造に近いなら、$(\Delta_{t,i})^2$ は「信号が乗った度合い」の粗い proxy になりうる、と止めるのが安全である。

一方、経験的 Fisher の対角は本質的に **勾配二乗モーメント**：
$$
f_{t,i}\approx \mathbb{E}_{x\sim D_t}\big[(\nabla_\theta \ell(x;\theta))_i^2\big]
$$

両者は一般に一致しないが、**座標重要度の目安**として関連しうる、という書き方に留める。

#### 4.2.3 方向二次形式に上げると「行列一致」を主張しなくて済む

対角 surrogate は
$$
u^\top D_t u=\sum_{i=1}^d f_{t,i}u_i^2,
\qquad
D_t:=\operatorname{diag}(f_{t,1},\ldots,f_{t,d})
$$

タスクベクトル surrogate は
$$
\Phi_t:=\operatorname{diag}\big((\Delta_{t,1})^2,\ldots,(\Delta_{t,d})^2\big),
\qquad
u^\top \Phi_t u=\sum_{i=1}^d (\Delta_{t,i})^2 u_i^2
$$

である。

ランダム方向 $u$ に対する $\big(u^\top D_h u,\;u^\top\Phi_h u\big)$ などの相関・誤差を見るのが、後述の実験 1 である。

**論文での推奨パッケージ**：

- **Assumption**：linearized PEFT / 局所的に歪みがならされる座標、など
- **Proposition（弱く）**：このときタスクベクトル量は **ranking surrogate になりうる**
- **Validation**：**実験で rank agreement** を確認する

**Layerwise prior の再解釈**：  
層（またはモジュール）$\ell(i)$ と正のスケール $s_b(\cdot),s_h(\cdot)$ を入れた **層正規化比** は

$$
\hat\lambda_i^{\mathrm{(norm)}}
:=
\frac{(\Delta_{h,i})^2/s_h(\ell(i))}{(\Delta_{b,i})^2/s_b(\ell(i))+\varepsilon}
$$

と書ける。

$s_\cdot$ を層内ノルムや平均二乗で取ると、layerwise weight は **レイヤー間スケール歪みの補正** と解釈できる。

### 4.3 飛躍 3：経験的 Fisher を「曲率」と呼び切ること

- **PSD 局所感度 metric** と書く
- 「$F_t = H_t$」とは書かない

厳密な Hessian $H_t(\theta)$ と一般に一致しないことを踏まえ、本文では例えば

$$
\mathrm{Tax}(\Delta\theta)\approx \tfrac12\,\Delta\theta^\top F_b\,\Delta\theta,
\qquad
\mathrm{Gain}(\Delta\theta)\approx \Delta\theta^\top F_h\,\Delta\theta
$$

のように、**二次形式で測る局所コスト / 利益**として位置づける。

---

## 5. さらに強くする任意パーツ：一般 Surrogate Consistency（補題）

**設定**：部分空間 $\mathcal{U}\subseteq\mathbb{R}^d$ 上で、正定値 $F_b\succ 0$、$F_h\succeq 0$ と surrogate $\tilde F_b,\tilde F_h$ を考える。すべての $u\in\mathcal{U}$ に対し、相対誤差 $\eta_b,\eta_h\in[0,1)$ が存在して

$$
(1-\eta_b)\,u^\top F_b u
\;\le\;
u^\top \tilde F_b u
\;\le\;
(1+\eta_b)\,u^\top F_b u
$$

かつ

$$
(1-\eta_h)\,u^\top F_h u
\;\le\;
u^\top \tilde F_h u
\;\le\;
(1+\eta_h)\,u^\top F_h u
$$

が成り立つとする。

**真の Rayleigh 比**と **surrogate 比**を
$$
R(u):=\frac{u^\top F_h u}{u^\top F_b u},
\qquad
\tilde R(u):=\frac{u^\top \tilde F_h u}{u^\top \tilde F_b u}
$$

と定める。

**補題（挟み込み）**：  
上の仮定のもと、任意の $u\in\mathcal{U}$（$u^\top F_b u>0$）に対して

$$
\frac{1-\eta_h}{1+\eta_b}\,R(u)
\;\le\;
\tilde R(u)
\;\le\;
\frac{1+\eta_h}{1-\eta_b}\,R(u)
$$

が成り立つ。

**証明スケッチ**：  
分子は
$$
(1-\eta_h)u^\top F_h u\le u^\top\tilde F_h u\le(1+\eta_h)u^\top F_h u
$$

分母は
$$
(1-\eta_b)u^\top F_b u\le u^\top\tilde F_b u\le(1+\eta_b)u^\top F_b u
$$

である。正の量の割り算で不等式の向きが決まり、上界は「最大分子 / 最小分母」、下界は「最小分子 / 最大分母」で得られる。

**使い道**：  
$\tilde F$ を **対角 surrogate** でも **タスクベクトルから作った $\Phi$** でもよい。  
つまり、「$u^\top \tilde F u$ が $u^\top F u$ を乗法的に近似できれば、**比（Rayleigh）も同程度の誤差で保たれる**」と言える。

---

## 6. 実験で何を示すか（Full FIM 不要のものから）

論文の軸は次に移すと強い。

> **行列要素の一致ではなく、順位・部分空間・方向二次形式が surrogate でどこまで保たれるかに軸を移す。**

### 6.1 実験 1：Directional Quadratic-Form Fidelity（最優先）

SST の本質は、**方向 $u$ に沿った二次形式** $u^\top F_t u$ にある。

経験的 Fisher では、データ $x_n\sim D_t$、ミニバッチ勾配 $g_n:=\nabla_\theta\ell(x_n;\theta)$ に対し

$$
u^\top F_t u=\mathbb{E}_{x\sim D_t}\big[(g^\top u)^2\big]\approx\hat q_t(u):=\frac{1}{N}\sum_{n=1}^N (g_n^\top u)^2
$$

と推定できる。

> **full の $d\times d$ 行列を保存しなくても**、$\hat q_t(u)$ は勾配サンプルだけで推定できる。

対角 surrogate とタスクベクトル surrogate は、§4.2.3 より
$$
q_t^{\mathrm{diag}}(u)=u^\top D_t u,
\qquad
q_t^{\mathrm{task}}(u)=u^\top \Phi_t u
$$

である。

比較したい方向比の例（harm / benign）は
$$
r(u):=\frac{\hat q_h(u)}{\hat q_b(u)+\varepsilon},
\qquad
r^{\mathrm{diag}}(u):=\frac{q_h^{\mathrm{diag}}(u)}{q_b^{\mathrm{diag}}(u)+\varepsilon},
\qquad
r^{\mathrm{task}}(u):=\frac{q_h^{\mathrm{task}}(u)}{q_b^{\mathrm{task}}(u)+\varepsilon}
$$

である。

$u$ を単位球上に一様、または各向同性ガウスで正規化して $M$ 本サンプルし、次を報告する。

- Pearson / Spearman
- 相対誤差 $\lvert r-r^{\mathrm{sur}}\rvert / \lvert r\rvert$
- $\log r$ の誤差
- 上位分位の方向集合の Jaccard overlap

### 6.2 実験 2：$\lambda_i$ と $\hat\lambda_i$ の Rank Agreement（Diagonal → Task Vector の主柱）

ベクトル
$$
\lambda=(\lambda_1,\ldots,\lambda_d)^\top,
\qquad
\hat\lambda=(\hat\lambda_1,\ldots,\hat\lambda_d)^\top
$$

の **順位**を比較する。

- **Spearman**：
  順位に置いたときの Pearson 相関
  $$
  \rho_{\mathrm{Spearman}}(\lambda,\hat\lambda)
  $$

- **Kendall $\tau$**：
  concordant / discordant ペア数から定義される順位一致度

- **Top-$k$ 集合一致**：
  $$
  S_k(\lambda):=\operatorname{TopK}(\lambda),\qquad
  S_k(\hat\lambda):=\operatorname{TopK}(\hat\lambda)
  $$

  に対し、
  $$
  \operatorname{Jaccard}_k=\frac{|S_k(\lambda)\cap S_k(\hat\lambda)|}{|S_k(\lambda)\cup S_k(\hat\lambda)|},\qquad\operatorname{Precision@}k=\frac{|S_k(\lambda)\cap S_k(\hat\lambda)|}{k}
  $$

- **層別評価**：
  添字集合を層ごとに制限して同様の $\rho,\tau$ を出す。  
  これにより、layer prior の効果検証にもつながる。

### 6.3 実験 3：小ブロックでの Full vs Diagonal

扱える小次元ブロック（例：1 層 `q_proj` の LoRA 部分）に制限して $F_b,F_h$、あるいは $B$ を **dense に構築**できるとする。  
そのブロックで

$$
\rho_{\mathrm{off}}
:=
\frac{\|B-B_{\mathrm{diag}}\|_F}{\|B\|_F}
$$

を報告し、さらに上位 $k$ 固有空間の

- 主角度
- Grassmann 距離
- eigengap $\gamma_k$

を出す。

### 6.4 実験 4：Approximation Ladder（下流）

同一の $(k,\alpha)$ で、手続き系列

- full
- block
- diagonal
- data-free

ごとに、Utility–Safety の **パレート曲線**と、選ばれた座標集合の **overlap**（Jaccard など）を並べる。

### 6.5 実験 5：FIM サンプル数 $N$ の安定性（Appendix 向き）

$N\in\{50,200,500,\ldots\}$ のように振り、例えば

$$
\operatorname{Spearman}\big(\lambda^{(N)},\lambda^{(N_{\max})}\big)
$$

や Top-$k$ overlap、下流指標をプロットする。

---

## 7. 時間がないときの「最低限 3 つ」

1. **本文の主張を変える**  
   - diagonal = 座標制約付き surrogate（exact special case）
   - data-free = ranking surrogate
   - Fisher = PSD 局所感度 metric

2. **Directional Quadratic-Form Fidelity**  
   Full FIM 不要で、本質に直撃する。

3. **Fisher 比 vs タスクベクトル比の Rank Agreement**  
   できれば layerwise の ablation も併せる。

---

## 8. 避けたい書き方（チェックリスト）

1. 「タスクベクトルは Fisher の近似」と **断言** しない。  
   → せいぜい **ranking surrogate / linearized PEFT** の語に留める。

2. **本文と Appendix で proxy の主役が違う** 状態を避ける。  
   例：本文は task vector、Appendix は magnitude 中心。  
   → **主役を task vector 比に統一**し、magnitude は baseline / ablation に下げる。

3. 対角を「Full の単なる計算近似」**だけ**と書かない。  
   → **座標制約付き subspace 選別の厳密解**として書く。

---

## 9. 論文にそのまま差し込める見出し案（セクション骨子）

### 3.x Approximation Hierarchy

1. Full SST：ideal metric-based subspace selection
2. Diagonal SST：Full と同型の選別則を、**座標制約 surrogate 上で解いた exact special case**
3. Data-free SST：linearized PEFT における **Fisher 比順位の ranking surrogate**

### 3.x.1 Surrogate Consistency（一般補題）

二次形式が LoRA 部分空間上で挟まれるなら、Rayleigh 比も挟まれる。

### 3.x.2 Why Diagonal Is Reasonable

- ホワイト化作用素
- eigengap
- $E=B-B_{\mathrm{diag}}$
- （任意）ブロック対角

### 3.x.3 Why Task-Vector Proxy Is Reasonable

- 線形化
- 勾配信号
- **順位**主張

> 定理より、Assumption + 検証の形が安全。  
> 未実施なら未実施と明記する。

### 4.x Empirical Validation of the Hierarchy

- directional quadratic forms
- rank agreement
- small-block comparison
- approximation ladder downstream
- （Appendix）$N$ 安定性

---

## 10. ひとことまとめ

- **近似値の一致**を主戦場にしない。
- **順位・部分空間・方向二次形式**が surrogate でどこまで保たれるかに軸を移す。
- **Full → Diagonal** は理論で厚く、**Diagonal → Task Vector** は弱い理論 + 順位 / 二次形式実験で支える、という二段構えがレビューでは通りやすい。

---

## 11. 付記：$F_b$ 直交射影と記号一覧（論文本文と揃える用）

### 11.1 Safety Subspace への射影（Full）

一般化固有ベクトルから列ベクトルを並べた
$$
V_k=[v_1,\ldots,v_k]\in\mathbb{R}^{d\times k}
$$

に対し、$F_b$ 計量に整合した射影は

$$
\Pi_{\mathcal{S}_k}^{(F_b)}(\Delta_s)
=
V_k\,(V_k^\top F_b V_k)^{-1}\,V_k^\top F_b\,\Delta_s,
\qquad
\Delta\theta=\Pi_{\mathcal{S}_k}^{(F_b)}(\Delta_s)
$$

である。

> $V_k^\top F_b V_k$ が正定値である区間で定義される。

### 11.2 記号クイックリファレンス

- $\theta$：adapter / LoRA 係数ベクトル（次元 $d$）
- $F_b,F_h$：benign / harm の（経験的）Fisher（PSD 局所感度）
- $\varepsilon$：数値安定化（$F_b+\varepsilon I$ など）
- $B$：ホワイト化作用素
  $$
  B=(F_b+\varepsilon I)^{-1/2}F_h(F_b+\varepsilon I)^{-1/2}
  $$
- $D_b,D_h$：対角 surrogate
  $$
  D_b=\operatorname{diag}(f_{b,i}),\qquad
  D_h=\operatorname{diag}(f_{h,i})
  $$
- $B_{\mathrm{diag}}$：
  $$
  B_{\mathrm{diag}}=(D_b+\varepsilon I)^{-1/2}D_h(D_b+\varepsilon I)^{-1/2}
  $$
- $\lambda_i$：座標比
  $$
  \lambda_i=\frac{f_{h,i}}{f_{b,i}+\varepsilon}
  $$
- $\Delta_b,\Delta_h$：utility / safety のタスクベクトル
- $\hat\lambda_i$：
  $$
  \hat\lambda_i=\frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2+\varepsilon}
  $$
- $D_t,\Phi_t$：対角 / タスク由来の二次形式用行列
  $$
  D_t=\operatorname{diag}(f_{t,i}),\qquad
  \Phi_t=\operatorname{diag}((\Delta_{t,i})^2)
  $$
- $\eta_b,\eta_h$：surrogate consistency（§5）の相対誤差

---

*本レポートは執筆用の内部整理メモであり、数式・用語は論文本文のラベル・記号と揃えて最終調整すること。*
