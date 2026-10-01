---
inclusion: always
---

# プロダクト・実験方針 (SST-Merge Steering Rules) - 最終決定版

## 1. SST-Mergeの理論と感度の物理的定義

SST-Merge（Safety-Sensitive Tuning by Fisher-Ratio Subspace）は、良性タスク性能（Utility）と安全性能（Safety）の競合（Safety Tax）を幾何学的最適化問題として扱い、セキュリティパッチ（Safety model）をベースモデルに統合するマージ手法です。

### 理論的定式化
良性分布（Utility）に対する負の対数尤度の感度（Fisher情報行列）を $F_b$、有害応答分布（Safety）に対する感度を $F_h$ と定義し、以下の制約付き最適化問題を解きます。

$$
\max_{\Delta\theta\in\mathbb{R}^d}\ \ \Delta\theta^\top F_h \Delta\theta
\quad \text{s.t.}\quad
\Delta\theta^\top F_b \Delta\theta \le c
$$

ここで $c > 0$ は許容する最大 Utility 劣化（Safety Tax）を示します。
この問題は、一般化固有値問題（GEVP） $F_h v = \lambda F_b v$ に帰着され、一般化固有値 $\lambda_i$ は「安全／有用コスパ（efficiency ratio）」を表します。

### Fisher情報の物理的定義における厳密な制約
- $F_h$ は安全性改善そのものを保証する量ではなく、**有害入力/攻撃分布（harmful / attack distribution）上での局所損失感度 proxy** です。
- 安全性を改善する具体的な方向性は、学習済みの安全パッチモデルとの差分である **Safety patch vector $\Delta_s$** によって与えられます。
- SST-Mergeは、パッチ差分 $\Delta_s$ のうち、**有害応答感度が高く（harmful-sensitive）、良性応答感度が低い（benign-insensitive）成分を最適化原理に基づいて選別**して注入します。

### 近似（Surrogate）手法
- **対角 SST (Diagonal SST)**: 座標ごとに $\lambda_i = \frac{f_{h,i}}{f_{b,i}+\varepsilon}$ を算出してマスクを作成。
- **データフリー SST (Data-Free SST)**: タスクベクトル（LoRA アダプタの差分）の二乗比を用いて座標順位（ランキング surrogate）を構築。
  $$
  \hat{\lambda}_i = \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2+\varepsilon}
  $$
  ※ Data-Free SST は FIM-SST の代替理論ではなく proxy 近似であるため、結果は FIM-based SST と分けて報告し、高 $\alpha$ 補間での推論崩壊（Collapse）検査を必須とします。

---

## 2. 実験設計と使用モデル

### 2.1 対象モデル
- **Main base model**: `meta-llama/Meta-Llama-3.1-8B-Instruct`
- **Cross-model validation**: `mistralai/Mistral-7B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`
- **先行研究比較用 (任意)**: `meta-llama/Llama-2-7b-chat-hf`

### 2.2 実験フェーズとベンチマーク

#### A. 現論文再現用ベンチマーク
- **Utilityデータ**: RepliQA, Alpaca
- **Safetyデータ**: Custom Jailbreak / Jailbreak Trigger
- **比較手法**: Task Arithmetic, TIES, DARE

#### B. AAAI投稿用拡張ベンチマーク
- **Utility評価**: MMLU, MMLU-Pro, IFEval, GSM8K, MATH-500, HumanEval, MBPP, AlpacaEval 2, MT-Bench
- **Safety評価**: HarmBench, JailbreakBench, StrongREJECT, WildJailbreak を主表とし、AdvBench, HELM-Safety, XSTest を補助表とする。

---

## 3. 実験データの役割分離ルール (Data Split Policy)

FIM推定の妥当性と評価の公平性を完全に保証するため、以下のデータセットは必ず互いに完全に分離し、重複を禁止します。

### データ分離の具体的割り当て表

| 用途 | 具体的なデータセット割り当て |
|---|---|
| **F_h (Harmful Fisher) 推定** | Custom Jailbreak / BeaverTails train dataset |
| **F_b (Benign Fisher) 推定** | RepliQA train / Alpaca train dataset |
| **Safety 評価用ベンチマーク** | HarmBench, JailbreakBench, StrongREJECT, WildJailbreak, HELM-Safety, AdvBench, XSTest |
| **Utility 評価用ベンチマーク** | MMLU-Pro, IFEval, GSM8K, MATH-500, HumanEval, MBPP, AlpacaEval 2, MT-Bench |

> [!WARNING]
> 評価用ベンチマークのデータを、LoRAの学習、FIMの推定、あるいはハイパーパラメータ（$\alpha, k$）のチューニングや選択のために使用することは厳格に禁止します。

---

## 4. 必須比較手法と使用ルール

### 比較手法リスト
- **基本 Baseline**: Task Arithmetic, TIES-Merging, DARE
- **高度マージ Baseline**: DELLA, Model Breadcrumbs
- **Fisher / 曲率系**: Fisher-weighted averaging, RegMean / Fisher Mask Nodes
- **Safety-Aware マージ**: MergeAlign, SafeMERGE, LED-Merging, AlignMerge
- **非マージ / Guardrail**: Safety LoRA のみ, Utility LoRA のみ, Mixed SFT, Llama Guard (補助)

> [!IMPORTANT]
> 比較手法は、必ず**公式実装または著者公開のオリジナル実装**を使用してください。
> TIES / DARE / Task Arithmetic については、独自に Python 等で再実装したカスタムコードは一切使用せず、公式 `mergekit` を用いることを義務付けます。

---

## 5. 手法内アブレーション (Ablation Study)

提案手法 SST-Merge の各構成要素の有効性を実証するため、以下の 11 項目についてアブレーションを必須とします。
1. **F_h / F_b ratio (SST本体)**
2. **F_h only**
3. **1 / F_b only**
4. **|\Delta_s| top-k (Magnitude)**
5. **Random mask**
6. **Hard mask vs Soft mask**
7. **Additive vs Interpolation**
8. **Layer-wise prior あり / なし**
9. **Data-Free SST vs FIM-SST**
10. **FIM sample size** ($N \in \{50, 100, 500, 1000\}$)
11. **Harmful / Benign の入れ替え (Negative Control)**

> [!IMPORTANT]
> アブレーションにおいて、**F_h/F_b vs F_h only vs magnitude (|\Delta_s| top-k)** の比較は最重要であり、提案する幾何学的方向選別の有効性を実証する上で必須の検証項目です。

---

## 6. 実験指標 (Metrics) と統計的報告

- **主表のフォーマット**:
  `Method | HarmBench ASR↓ | JBB ASR↓ | StrongREJECT↓ | MMLU-Pro↑ | IFEval↑ | AlpacaEval↑ | Safety@95% Utility↑ | Pareto AUC↑`
- **主要指標**: ASR, Over-refusal Rate (on XSTest), Safety@95% Utility, Pareto AUC
- **統計的報告要件**:
  - 主要な実験は**最低 3 シード**で実行すること。
  - 結果は **mean ± std** で提示すること。
  - **95% Bootstrap 信頼区間 (CI)** および **Paired bootstrap test** を用い、SST-Merge と比較手法間の Pareto AUC および Safety@95% Utility の差が統計的に有意であることを示すこと。

---

## 7. 禁止事項（Steering Rules）

1. **比較手法におけるカスタム実装コードの使用禁止**
   - TIES, DARE などのマージに独自実装した Python コードを使用してはいけません（`mergekit` 等の標準公開コードを使用すること）。
2. **データフリー設定におけるデータ・統計量の漏洩（カンニング）の禁止**
   - Data-Free マージ時において、実データセット（JSON等）のロード、過去に計算した FIM キャッシュ、勾配キャッシュなどのデータセット由来の統計量を読み込んで使用してはいけません。
3. **cherry-pickingの禁止**
   - 最良の $\alpha, k$ の結果のみを本文に載せてはいけません。すべての $\alpha, k$ スイープ結果を保存し、Pareto 曲線または Appendix に完全に開示してください。
4. **乱数シードの固定と複数シード検証**
   - すべての実験で乱数シード（例: `seed=42`）を固定し、主要な実験結果は最低 3 つの異なるシードで再現・検証を行い、平均と標準偏差を報告してください。
5. **公式実装のcommit記録の義務化**
   - 使用した比較手法のパッケージやリポジトリの Git commit hash、パッケージバージョン、および実行時の完全なコマンドライン引数をメタデータとして記録・保存してください。
6. **archiveコード（`v1/` 配下）の使用禁止**
   - `v1/` ディレクトリ配下にある古いカスタムマージ実装やスクリプトを、`v2` 実験パイプラインから参照・インポートしてはいけません。
7. **評価データのチューニング利用禁止**
   - 評価ベンチマークデータを、FIM推定、LoRA学習、およびハイパーパラメータ選択に使用してはいけません。
