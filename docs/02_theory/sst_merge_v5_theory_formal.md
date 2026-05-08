# SST-Merge v5: 理論の形式的定式化と解説

**Safety Subspace Task-Merge — 実装 v5 に完全対応した理論的記述**

---

## 概要（Abstract）

本稿では、**SST-Merge v5** の理論を数式に基づいて形式的に定式化し、実装との対応を明示する。SST-Merge は、有用性（Utility）アダプターと安全性（Safety）アダプターをマージする際に、**Fisher Information Matrix (FIM)** と**一般化固有値問題 (GEVP)** を用いて、Safety の付与による Utility の劣化（Safety Tax）を抑えつつ、安全性を付与する手法である。v5 実装では、(i) データ依存・データフリーの 2 種の FIM 計算、(ii) 対角 GEVP による固有値と Safety マスクの計算、(iii) 加算型・補間型の 2 種のマージ式、(iv) Layer-wise 重み、を一貫して扱う。以下では、問題設定から各ステップの数式、そして実装との対応までを論文風に詳述する。

---

## 1. 導入と問題設定

### 1.1 記号と前提

- **ベースモデル**: パラメータ $\theta_{\mathrm{base}} \in \mathbb{R}^d$ の因果言語モデル。
- **Utility アダプター**: 有用タスク（例: 質問応答）にファインチューニングした LoRA パラメータ $\theta_{\mathrm{util}} \in \mathbb{R}^d$（または差分 $\tau_{\mathrm{util}} = \theta_{\mathrm{util}} - \theta_{\mathrm{base}}$）。
- **Safety アダプター**: 安全性タスク（例: 有害プロンプトへの拒否）にファインチューニングした LoRA パラメータ $\theta_{\mathrm{safe}} \in \mathbb{R}^d$（または差分 $\tau_{\mathrm{safe}}$）。
- **マージ結果**: $\theta_{\mathrm{merged}} \in \mathbb{R}^d$。LoRA の場合はマージされたアダプター重みを指す。

添字 $i \in \{1,\ldots,d\}$ はパラメータ（または flatten したときの 1 次元インデックス）を表す。ベクトル・テンソルの要素ごとの積は $\odot$（Hadamard 積）で表す。

### 1.2 目的の定式化

マージにおいて達成したい 2 つの目的は次のように表現できる。

1. **Safety の付与**: 有害データ $D_{\mathrm{harm}}$ 上での「拒否」などの安全性指標を高める。
2. **Utility の維持**: 良性データ $D_{\mathrm{benign}}$ 上での有用性（タスク性能）をベース/Utility モデルに近く保つ。

両者は一般にトレードオフの関係にあり、Safety を一様に強めると Utility が低下する（**Safety Tax**）。SST-Merge の考え方は、**パラメータごとに「Safety に効くが Utility には効きにくい方向」を特定し、その方向にのみ Safety を強く適用する**ことである。その「方向」と強さを、FIM と GEVP で定量化する。

### 1.3 アプローチの流れ（高レベル）

1. **FIM の計算**: Utility 用データで $F_{\mathrm{benign}}$、Safety 用データで $F_{\mathrm{harm}}$ を求める（データなしの場合は後述の近似）。
2. **GEVP の求解**: $F_{\mathrm{harm}} v = \lambda \, F_{\mathrm{benign}} v$ を解き、各パラメータに対応する固有値 $\lambda_i$ を得る。
3. **Safety マスク**: $\lambda_i$ から $m_i \in [0,1]$ を計算する（高い $\lambda_i$ → $m_i$ を大きく）。
4. **マージ**: $m_i$ と層重み $w_{\mathrm{layer}}$、全体重み $\alpha$ を用いて $\theta_{\mathrm{merged}}$ を定義する（加算型または補間型）。

以下、各ステップを数式と実装対応で記述する。

---

## 2. Fisher Information Matrix（FIM）の定式化

### 2.1 定義と役割

モデルの条件付き分布を $p(y|x,\theta)$、対数尤度を $\ell(\theta; x, y) = \log p(y|x,\theta)$ とする。**Fisher Information Matrix** $F(\theta) \in \mathbb{R}^{d \times d}$ は

$$
F(\theta)
= \mathbb{E}_{(x,y) \sim \mathcal{D}}
\left[
  \nabla_\theta \ell(\theta; x,y)
  \,\big(\nabla_\theta \ell(\theta; x,y)\big)^{\top}
\right]
$$

で定義される。$F$ はパラメータ空間における**対数尤度の曲率（感度）**を表し、$F_{ii}$ が大きいパラメータ $\theta_i$ は、データ分布の下で損失（負の対数尤度）の変化に敏感であると解釈できる。

### 2.2 対角近似（実装で使用）

v5 では **対角近似** を用いる。すなわち

$$
F_{ij} \approx 0 \quad (i \neq j), \qquad
F_{ii}
= \mathbb{E}\left[
  \left( \frac{\partial \ell}{\partial \theta_i} \right)^2
\right].
$$

言語モデルで自己教師あり（next-token prediction）を行う場合、サンプル $b$ における損失は $\mathcal{L}_b = -\sum_t \log p(y_t | y_{<t}, x; \theta)$ の形であり、$\nabla_\theta \mathcal{L}_b$ が勾配である。**実装では、複数サンプルに対する勾配の分散を対角 FIM の近似として用いる**:

$$
\widehat{F}_{ii}
= \frac{1}{N-1} \sum_{b=1}^{N}
\left( g_{b,i} - \bar{g}_i \right)^2 + \varepsilon
\approx \mathrm{Var}_{b}\big( g_{b,i} \big) + \varepsilon,
$$

ここで $g_{b,i}$ はサンプル $b$ における $\theta_i$ の勾配、$\bar{g}_i = \frac{1}{N}\sum_b g_{b,i}$、$\varepsilon$ は正則化（例: `regularization=1e-6`）である。平均が 0 に近い場合は

$$
\widehat{F}_{ii} \approx \frac{1}{N} \sum_{b=1}^{N} g_{b,i}^2 + \varepsilon
$$

とも解釈できる。実装では `gradients_stack.var(dim=0) + self.regularization` により、全パラメータを flatten したベクトルに対する**対角 FIM ベクトル** $\widehat{F} \in \mathbb{R}^d$ を求めている（`FIMCalculator.compute_fim`）。

### 2.3 二つの FIM：$F_{\mathrm{benign}}$ と $F_{\mathrm{harm}}$

- **$F_{\mathrm{benign}}$**: Utility 用データ $D_{\mathrm{benign}}$（例: RepliQA, Alpaca）上で、**Utility アダプターを載せたモデル**の勾配から計算する。パラメータ $i$ が「有用性タスクでどれだけ効いているか」の指標となる。
- **$F_{\mathrm{harm}}$**: Safety 用データ $D_{\mathrm{harm}}$（例: 有害プロンプト＋拒否応答）上で、**Safety アダプターを載せたモデル**の勾配から計算する。パラメータ $i$ が「安全性タスクでどれだけ効いているか」の指標となる。

両者とも同じパラメータ順（同じキー順・flatten 順）で格納し、後段の GEVP で要素ごとに対応させる（実装では LoRA パラメータのみを対象とし、キーでソートして順序を揃える）。

---

## 3. 一般化固有値問題（GEVP）の定式化

### 3.1 一般形と Rayleigh 商

**一般化固有値問題** を

$$
F_{\mathrm{harm}} \, v = \lambda \, F_{\mathrm{benign}} \, v
$$

とする。$F_{\mathrm{benign}}, F_{\mathrm{harm}}$ が正定値対称であるとき、固有値 $\lambda$ は **Rayleigh 商** として

$$
\lambda = \frac{v^{\top} F_{\mathrm{harm}} \, v}{v^{\top} F_{\mathrm{benign}} \, v}
$$

と表され、この商を最大（最小）にする $v$ が最大（最小）固有値に対応する固有ベクトルである。

### 3.2 対角 FIM の場合の閉形式解

**命題 3.1（対角 GEVP の解）**  
$F_{\mathrm{benign}} = \mathrm{diag}(f_1,\ldots,f_d)$、$F_{\mathrm{harm}} = \mathrm{diag}(h_1,\ldots,h_d)$ を正対角行列とする。GEVP $F_{\mathrm{harm}} v = \lambda F_{\mathrm{benign}} v$ の固有対は、各 $i \in \{1,\ldots,d\}$ に対して

$$
\lambda_i = \frac{h_i}{f_i}, \qquad v_i = e_i
$$

である。ここで $e_i$ は第 $i$ 成分のみ 1 の標準基底ベクトル。正則化を入れた形では

$$
\lambda_i = \frac{h_i}{f_i + \varepsilon}, \quad \varepsilon > 0.
$$

**証明の概要**: 対角行列のとき $(F_{\mathrm{harm}} - \lambda F_{\mathrm{benign}}) v = 0$ は成分ごとに $(h_i - \lambda f_i) v_i = 0$ となる。$v_i \neq 0$ とすると $\lambda = h_i / f_i$ で、$v = e_i$ が対応する固有ベクトルである。□

v5 ではこの閉形式をそのまま用いる:

$$
\boxed{
\lambda_i = \frac{F_{\mathrm{harm}, i}}{F_{\mathrm{benign}, i} + \varepsilon}
}
$$

実装: `eigenvalues = F_harm / (F_benign + self.regularization)`（`GEVPSolver.solve_gevp_diagonal`）。

### 3.3 固有値 $\lambda_i$ の解釈

- **$\lambda_i$ が大きい**: $F_{\mathrm{harm}, i}$ が相対的に大きい → パラメータ $i$ は Safety タスクに敏感。$F_{\mathrm{benign}, i}$ が相対的に小さい → Utility タスクにはあまり敏感でない。  
  → **このパラメータに Safety を強く適用しても、Utility への悪影響が小さい。**

- **$\lambda_i$ が小さい**: Utility に敏感で Safety には相対的に鈍感。  
  → **このパラメータは Utility を保つため、Safety の適用を控える（マスク $m_i$ を小さくする）。**

したがって、$\lambda_i$ を「Safety を適用してよい度合い」の指標として使い、これに基づいてマスク $m_i$ を定める。

---

## 4. Safety マスクの計算

$\lambda_i$ は非負だがスケールや外れ値の影響を受けやすいため、そのまま使わず **[0,1] に正規化したマスク** $m_i$ を定義する。v5 では **ソフトマスク** と **ハードマスク（Top-k）** の 2 通りを実装している。

### 4.1 ソフトマスク（デフォルト）

外れ値に強くするため **対数スケール** で正規化する。

1. **対数変換**  
   $\tilde{\lambda}_i = \log(\lambda_i + \delta)$（$\delta = 10^{-10}$ などで数値安定化）。

2. **パーセンタイルによるクリップ正規化**  
   $\tilde{\lambda}$ の 5% 点を $p_5$、95% 点を $p_{95}$ とする。実装では `torch.quantile(log_eigenvalues, 0.05)` および `0.95`。  
   正規化値:
   $$
   n_i = \frac{\tilde{\lambda}_i - p_5}{p_{95} - p_5}.
   $$
   $p_{95} = p_5$ のときは $n_i = 0.5$ とするなどのフォールバックを実装。

3. **クリップ**  
   $$
   \boxed{
   m_i = \mathrm{clamp}(n_i,\, 0,\, 1).
   }
   $$
   実装: `normalized = (log_eigenvalues - p5) / (p95 - p5); normalized = torch.clamp(normalized, 0.0, 1.0)`（`GEVPSolver.compute_safety_mask`、`top_k_ratio is None` のとき）。  
   大規模時はメモリ節約のため、`log_eigenvalues` のサンプルでパーセンタイルを計算している。

### 4.2 ハードマスク（Top-k）

$k = \lfloor \mathrm{len}(\lambda) \times \mathrm{top\_k\_ratio} \rfloor$ とし、$\lambda_i$ が**上位 $k$ 個**に入るときのみ Safety を適用する:

$$
\boxed{
m_i = \begin{cases}
1 & \text{if } \lambda_i \in \mathrm{Top\text{-}}k(\lambda), \\
0 & \text{otherwise}.
\end{cases}
}
$$

実装: `k = int(len(eigenvalues) * top_k_ratio)`, `mask[sorted_indices[:k]] = 1.0`。

---

## 5. マージ式の定式化（加算型・補間型）

Safety の全体強度を $\alpha \in [0,1]$、パラメータ $i$ が属する層の重みを $w_{\mathrm{layer}}(i) \in \mathbb{R}^+$ とする。v5 では LoRA パラメータ名に応じて `LAYER_WEIGHTS` から $w_{\mathrm{layer}}$ を取得する（後述）。

### 5.1 加算型マージ（Additive）

Utility を**そのまま残し**、Safety を**マスクに応じて上乗せ**する形である:

$$
\boxed{
\theta_{\mathrm{merged}, i}
= \theta_{\mathrm{util}, i}
+ \alpha \, w_{\mathrm{layer}}(i) \, m_i \, \theta_{\mathrm{safe}, i}.
}
$$

- $m_i$ が大きいパラメータほど Safety の寄与が大きい。
- $\alpha=0$ なら $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}}$、$\alpha=1$ かつ $m \equiv 1$ なら $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \theta_{\mathrm{safe}}$（Task Arithmetic 的な加算に近い）。

実装: `merged[key] = utility_val + (alpha * layer_weight * param_mask) * safety_val`（`SSTMerge._merge_with_mask`、Data-Free 版も同形）。

### 5.2 補間型マージ（Interpolation）

Utility と Safety の**凸結合**で、Task Arithmetic の補間形式に合わせる:

$$
w_i = \alpha \, w_{\mathrm{layer}}(i) \, m_i,
\qquad
\boxed{
\theta_{\mathrm{merged}, i}
= (1 - w_i) \, \theta_{\mathrm{util}, i}
+ w_i \, \theta_{\mathrm{safe}, i}.
}
$$

- $w_i \in [0,1]$ になるよう $\alpha$ や $m_i$ の設計に注意する（実装では $m_i \in [0,1]$ なので、$\alpha \le 1$ かつ $w_{\mathrm{layer}} \le 1$ なら $w_i \in [0,1]$）。
- $\alpha=1,\, m_i=1$ のとき $\theta_{\mathrm{merged}, i} = \theta_{\mathrm{safe}, i}$（完全に Safety に切り替え）。

実装: `safety_weight = alpha * layer_weight * param_mask`, `utility_weight = 1.0 - safety_weight`, `merged[key] = utility_weight * utility_val + safety_weight * safety_val`（`SSTMergeInterpolation._merge_with_mask_interpolation`、Data-Free 補間版も同形）。

### 5.3 加算型と補間型の対応表

| 項目 | 加算型 (Additive) | 補間型 (Interpolation) |
|------|-------------------|-------------------------|
| 式 | $\theta_u + \alpha w_{\mathrm{layer}} m \odot \theta_s$ | $(1 - w) \odot \theta_u + w \odot \theta_s$，$w = \alpha w_{\mathrm{layer}} m$ |
| Utility の扱い | 完全に保持し、Safety を加算 | 重み $(1-w)$ で保持 |
| $\alpha=1,\, m=1$ のとき | $\theta_u + \theta_s$ | $\theta_s$（完全切替） |
| 実装 | `sst_merge.py`, `sst_merge_data_free.py` (additive) | `sst_merge_interpolation.py`, `sst_merge_data_free.py` (interpolation) |

---

## 6. Data-Free における FIM 近似

学習データが使えない場合、v5 では **Data-Free** モードで、LoRA パラメータの**マグニチュードの二乗**を対角 FIM の近似とする:

$$
\boxed{
\widehat{F}_{ii}^{\mathrm{DF}}
= \theta_i^2 + \varepsilon.
}
$$

- 考え方: 更新が大きいパラメータほど「そのタスクで重要」とみなす（Magnitude Pruning 的な重要度）。
- Utility / Safety それぞれのアダプターについて上記を計算し、同じキー順で並べた $\widehat{F}_{\mathrm{benign}}^{\mathrm{DF}}$, $\widehat{F}_{\mathrm{harm}}^{\mathrm{DF}}$ を用意する。
- その後は **同じ GEVP** $\lambda_i = F_{\mathrm{harm},i} / (F_{\mathrm{benign},i} + \varepsilon)$ および同じマスク・マージ式を適用する。

実装: `FIMCalculatorDataFree.compute_fim_from_lora` で `fim = param.pow(2).flatten() + regularization` を連結。キーは `sorted(adapter_dict.keys())` でソートし、Utility と Safety で同一順序を保つ。

---

## 7. Layer-wise 重み $w_{\mathrm{layer}}$

層の種類によって「Safety を強く適用するか」「Utility を優先するか」を変えるため、パラメータ名に応じた係数 $w_{\mathrm{layer}}$ を掛ける。v5 の Data-Dependent 実装（`SSTMerge.LAYER_WEIGHTS`）では例えば:

| 層タイプ（キーに含まれる名前） | $w_{\mathrm{layer}}$ | 意図 |
|-------------------------------|----------------------|------|
| `lm_head` | 1.5 | 出力層: Safety を強め |
| `q_proj`, `k_proj`, `v_proj`, `o_proj` | 1.2 | Attention: Safety やや強め |
| `gate_proj`, `up_proj`, `down_proj` | 0.8 | FFN: Utility をやや優先 |

該当しない場合は 1.0。Data-Free 版では別の数値が設定されている場合があるが、考え方は同じで、**最終的な Safety の効き目**は

$$
w_{\mathrm{final}, i} = \alpha \, w_{\mathrm{layer}}(i) \, m_i
$$

となり、加算型なら $\theta_{\mathrm{merged}, i} = \theta_{\mathrm{util}, i} + w_{\mathrm{final}, i} \, \theta_{\mathrm{safe}, i}$、補間型なら $w_i = w_{\mathrm{final}, i}$ として $(1-w_i)\theta_{\mathrm{util}, i} + w_i \theta_{\mathrm{safe}, i}$ となる。

---

## 8. アルゴリズムの一覧（v5 対応）

以下、GEVP を用いる場合の共通フローをまとめる。

**入力**: Utility アダプター $\theta_{\mathrm{util}}$、Safety アダプター $\theta_{\mathrm{safe}}$、ハイパーパラメータ $\alpha$, $\varepsilon$, `top_k_ratio`（任意）、データ（Data-Dependent の場合）$D_{\mathrm{benign}}$, $D_{\mathrm{harm}}$。

1. **FIM の計算**
   - Data-Dependent: $D_{\mathrm{benign}}$ 上で Utility モデルの勾配から $\widehat{F}_{\mathrm{benign}}$、$D_{\mathrm{harm}}$ 上で Safety モデルの勾配から $\widehat{F}_{\mathrm{harm}}$ を対角近似（分散＋正則化）で計算。
   - Data-Free: $\widehat{F}_{\mathrm{benign}}^{\mathrm{DF}} = \theta_{\mathrm{util}}^2 + \varepsilon$、$\widehat{F}_{\mathrm{harm}}^{\mathrm{DF}} = \theta_{\mathrm{safe}}^2 + \varepsilon$（同一キー順で flatten）。

2. **GEVP（対角）**
   - $\lambda_i = \widehat{F}_{\mathrm{harm}, i} / (\widehat{F}_{\mathrm{benign}, i} + \varepsilon)$ を全 $i$ について計算。

3. **Safety マスク**
   - `top_k_ratio is None`: ソフトマスク $m_i = \mathrm{clamp}((\log(\lambda_i+\delta)-p_5)/(p_{95}-p_5), 0, 1)$。
   - 否则: ハードマスク（上位 Top-k のみ 1、それ以外 0）。

4. **マージ**
   - 加算型: $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha \, w_{\mathrm{layer}} \odot m \odot \theta_{\mathrm{safe}}$。
   - 補間型: $w = \alpha \, w_{\mathrm{layer}} \odot m$、$\theta_{\mathrm{merged}} = (1-w) \odot \theta_{\mathrm{util}} + w \odot \theta_{\mathrm{safe}}$。

**出力**: マージされたアダプター $\theta_{\mathrm{merged}}$。

---

## 9. 実装との対応表

| 理論（数式） | 実装（v5） | ファイル・メソッド |
|-------------|------------|---------------------|
| $\widehat{F}_{ii} = \mathrm{Var}_b(g_{b,i}) + \varepsilon$ | 勾配を収集し `var(dim=0) + regularization` | `core/sst_merge.py`: `FIMCalculator.compute_fim` |
| $F_{ii}^{\mathrm{DF}} = \theta_i^2 + \varepsilon$ | `param.pow(2).flatten() + regularization` | `core/sst_merge_data_free.py`: `FIMCalculatorDataFree.compute_fim_from_lora` |
| $\lambda_i = F_{\mathrm{harm},i} / (F_{\mathrm{benign},i} + \varepsilon)$ | `F_harm / (F_benign + self.regularization)` | `core/sst_merge.py`: `GEVPSolver.solve_gevp_diagonal` |
| ソフトマスク（対数＋パーセンタイル） | `log(eigenvalues+1e-10)`, `quantile(0.05/0.95)`, `clamp` | `GEVPSolver.compute_safety_mask`（`top_k_ratio is None`） |
| ハードマスク Top-k | `argsort(descending)`, `mask[:k]=1` | `GEVPSolver.compute_safety_mask`（`top_k_ratio` 指定時） |
| 加算型マージ | `utility_val + (alpha * layer_weight * param_mask) * safety_val` | `SSTMerge._merge_with_mask`, Data-Free `_merge_with_gevp` |
| 補間型マージ | `(1 - safety_weight) * utility + safety_weight * safety` | `SSTMergeInterpolation._merge_with_mask_interpolation`, Data-Free `_merge_with_gevp_interpolation` |
| Layer-wise | キー名に応じて `LAYER_WEIGHTS` を参照 | `SSTMerge.LAYER_WEIGHTS`, `_merge_with_mask` 内の `layer_weight` |

---

## 10. 議論と注意点

### 10.1 対角近似の妥当性

完全な FIM は $d \times d$ で大規模モデルでは扱いが難しい。対角近似は (i) 計算・メモリが軽い、(ii) パラメータごとの「重要度」を 1 スカラーで表現できる、という利点がある。一方で、パラメータ間の相関は無視されるため、厳密な GEVP の固有ベクトル（複数パラメータの線形結合）は得られず、**座標軸方向（各パラメータ単独）のみ**が考慮される。v5 ではこのトレードオフを許容し、対角解でマスクを構成している。

### 10.2 Safety Tax との関係

Safety を一様に強めると、Utility に重要なパラメータまで書き換わり、有用性が落ちる（Safety Tax）。SST-Merge では $\lambda_i$ が小さい（Utility に敏感な）パラメータには $m_i$ を小さくするため、それらの変更が抑えられ、**Safety Tax の低減**が期待できる。逆に $\lambda_i$ が大きいパラメータは「Safety 専用に近い」と解釈し、積極的に Safety を載せる。

### 10.3 Data-Free 近似の限界

Data-Free の $F_{ii} \approx \theta_i^2$ は、データ分布に依存しないため、真の FIM とは一致しない。特に「どの入力でそのパラメータが効くか」は反映されない。その分、データ収集・勾配計算が不要で高速であり、データが手に入らない場合のフォールバックとして有用である。

---

## 11. まとめ

- **問題**: Utility と Safety のトレードオフを、パラメータごとに「Safety に効くが Utility には効きにくい」方向に沿って制御したい。
- **手段**: (1) 対角 FIM で各パラメータの「Utility 感度」$F_{\mathrm{benign},i}$ と「Safety 感度」$F_{\mathrm{harm},i}$ を推定し、(2) 対角 GEVP で $\lambda_i = F_{\mathrm{harm},i}/F_{\mathrm{benign},i}$ を計算し、(3) $\lambda_i$ を [0,1] のマスク $m_i$ に変換し、(4) 加算型または補間型で $\alpha\, w_{\mathrm{layer}}\, m$ に応じて Safety を適用する。
- **v5 の選択肢**: Data-Dependent（勾配分散）／Data-Free（マグニチュード二乗）、加算／補間、ソフトマスク／Top-k、Layer-wise の有無を組み合わせた 4 パターン以上を実装でサポートしている。

以上の定式化に従うことで、SST-Merge v5 の挙動を数式と実装の対応から一貫して理解・検証できる。

---

## 参考文献・関連 work

- **Task Arithmetic**: タスクベクトルの加算によるマージ（SST-Merge の加算型は GEVP マスク付きの拡張とみなせる）。
- **TIES-Merging / DARE**: トリミング・符号選別・特異値に基づくマージ；SST-Merge は FIM と GEVP で「Safety vs Utility」の方向を明示的に扱う。
- **Fisher Information Matrix**: 推定論・自然勾配・Pruning における重要度指標として広く利用される。
- **一般化固有値問題**: 二つの二次形式の比（Rayleigh 商）の最適化と等価。

---

**作成日**: 2026-02-12  
**対応実装**: sst_merge_v5（`core/sst_merge.py`, `core/sst_merge_data_free.py`, `core/sst_merge_interpolation.py`）
