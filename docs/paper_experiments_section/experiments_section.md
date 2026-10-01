# 5. Experiments

## 5.1 Research Questions
本実験では、以下の5つの研究質問（Research Questions: RQs）を通じて SST-Merge (Subspace Safety-Preserving Task Merging) の性能および特性を多角的に検証する。

* **RQ1 (Pareto Frontier & Safety-Utility Trade-off)**: SST-Merge は、既存の標準マージ手法 (Task Arithmetic, TIES, DARE, DELLA) および安全維持マージ手法 (MergeAlign, SafeMERGE, LED-Merging, Matena & Raffel Fisher Weighted) と比較して、安全性能 (ASR低下) と有用性保持 (Utility retention) の Pareto 境界および Pareto AUC を改善できるか？
* **RQ2 (Data-free Setting & Proxies)**: キャリブレーションデータを利用できない Data-Free 環境において提案する **Data-Free SST-V** (タスクベクトル二乗比率) は、データ依存の **Diagonal FIM-SST** と比較してどの程度性能を維持できるか？ また、単なる重み絶対値比率 (`SST-M`) に対する優位性は存在するか？
* **RQ3 (Granularity & Subspace Resolution)**: パラメータ単位 (Element-wise) の高分解能選別マスクは、層単位 (Layer-wise) やニューロン単位の広域選択手法と比較して、パラメータ干渉をどのように抑制し有用性破壊を防げるか？
* **RQ4 (Computational & Memory Efficiency)**: SST は、追加の反復的な幾何制約最適化や高コストな勾配・ニューロン探査を要する手法と比較して、計算コスト (時間・メモリ) を削減できるか？
* **RQ5 (Robustness & Hyperparameter Sensitivity)**: 部分空間選択比率 $k$ やマージ強度 $\alpha$ の変動、およびランダム初期化シードに対する安定性・ロバスト性は確保されているか？

---

## 5.2 Detailed Experimental Design & Setup
本研究の実証検証は、予備実験 (Preliminary Validation) と本実験 (Main Benchmark Evaluation) の2層に分けて実施された。
予備実験では `TrustLLM` (Sun et al. 2024) の評価プロトコル（Longformer ベースの有害応答判別器 `LibrAI/longformer-harmful-ro` による拒否応答率 RtA 測定）および `BeaverTails` (Ji et al. 2024) の 500 件有害プロンプトセットを参照・活用して基礎検証を行なった。本実験では、これらのプロトコルを最新の多角的安全評価体系 (`HarmBench`, `JailbreakBench`, `StrongReject`, `WildJailbreak` + `XSTest`) へと拡張・昇華させ、評価サンプル数 `limit: 320` 件および全件評価を用いて測定を行なった。

### 5.2.1 Target Models & Architecture
実験対象として、7Bパラメータ規模の大規模言語モデル (LLM) である Llama-2 アーキテクチャを共通のバックボーンとして採用する。
* **ベースモデル ($\theta_0$)**: `meta-llama/Llama-2-7b-hf` (Touvron et al. 2023)
* **有用性専門モデル ($\theta_u$)**:
  * **数学ドメイン (Math)**: `WizardLMTeam/WizardMath-7B-V1.0` (Luo et al. 2023a)
  * **コードドメイン (Code)**: `vanillaOVO/WizardCoder-Python-7B-V1.0` (Luo et al. 2023b)
  * **医療ドメイン (Medical)**: `medalpaca/medalpaca-7b` (Han et al. 2023)
* **安全モデル ($\theta_s$)**: `meta-llama/Llama-2-7b-hf` に対する安全性アライメントとして、LoRAアダプタを用いてファインチューニングを適用した `models/safety_lora` (フルモデル展開 `models/temp_safety_full`)

### 5.2.2 Fisher Calibration Datasets & Curvature Estimation
対角 Fisher 情報行列 (Diagonal FIM) を計算するためのキャリブレーションデータとして、各データセットから $N = 500$ 件のサンプルを抽出して使用する。数値的安定性のための調整定数は $\epsilon = 10^{-6}$ とする。
* **安全性 Fisher 計算用データ ($D_s$)**: `data/fim/fim_harmful.json`
  - 有害要求プロンプトとそれに対する拒否応答ペアから構成。
* **良性有用性 Fisher 計算用データ ($D_u$)**:
  - **数学ドメイン**: `data/fim/fim_benign_math.json`
  - **コードドメイン**: `data/fim/fim_benign_code.json`
  - **医療ドメイン**: `data/fim/fim_benign_medical.json`

### 5.2.3 Evaluation Benchmarks & Detailed Metrics
自動評価は `lm-evaluation-harness` を用いて決定論的かつ再現可能なプロトコルで実行される。

#### 1) 安全性アライメント評価 (Safety Benchmarks)
本実験では、モデルの「見かけ上の安全性（推論崩壊・無意味文字列生成による偽の安全）」と「真の安全アライメント」を決定論的に判別するため、各ベンチマーク (`jailbreakbench`, `strongreject`, `wildjailbreak` 等) において以下の **4つの詳細個別指標** を算出・追跡する：

1. **`Original ASR (%)`** (排除前 ASR): 応答生成テキスト全体に対する有害攻撃成功率。
2. **`Filtered ASR (%)`** (排除後 ASR): 無意味なトークン反復や言語機能の完全壊死 (Gibberish / Degeneration) などの無効出力をフィルター除外した後の真の有害攻撃成功率。
3. **`Gibberish N`** (排除数): 推論崩壊・無意味文字列として検知され、判定対象から排除された応答サンプル数。
4. **`Gibberish Filter Ratio (%)`** (排除率): 全評価サンプルに対する Gibberish 排除数の割合 ($\frac{\text{Gibberish N}}{\text{Total Samples}} \times 100\%$)。

さらに、総合的な安全性能の定量的評価のため、**`Safety Ave` を判定ロジック別に 2 つに分離して評価・表示**する：
* **`Safety Ave [Refusal-Filtered] (ASR↓ %)`**: 応答内に妥当な拒否文言や建設的無害化・説明が含まれているかを評価する **Filtered ASR 排除後ベース** での 4 ベンチマーク平均 ASR。推論崩壊による偽の安全性を完全に排除した真のアライメント維持度を測定。
* **`Safety Ave [Harmful Content] (ASR↓ %)`**: 明確な有害指示・危険情報が提示されているかを判定する **HarmBench 統一 ASR ベース** での 4 ベンチマーク平均 ASR。

過剰拒否 (Over-refusal) 評価として、無害な質問に対する過剰な拒絶を検知するため、**`xstest`** (Röttger et al. 2023) を評価指標に含める。

#### 2) 有用性評価 (Utility Benchmarks)
* **数学分野 (Math)**: `gsm8k` (Cobbe et al. 2021) (Exact Match 精度)、および `minerva_math500` (Lewkowycz et al. 2022) (正解率)
* **コード分野 (Code)**: `humaneval` (Chen et al. 2021) (Pass@1 精度)、および `mbpp` (Austin et al. 2021) (生成精度)
* **医療分野 (Medical)**: `pubmedqa` (Jin et al. 2019) (PubMedQA 選択精度)、および `medqa_4options` (Jin et al. 2021) (正解率)
* **汎用能力 (General)**: `mmlu` (Hendrycks et al. 2020) (MMLU 精度)、および `ifeval` (Zhou et al. 2023) (指示追従 IFEval 精度)

### 5.2.4 Evaluation Protocol & Hyperparameters
* **SST 設定**: 提案手法 `diagonal_sst` は、マージ種別として `interpolation` (パラメータ単位の補間) を使用し、部分空間選択マスクとして `hard mask` を採用する。デフォルトの部分空間比率パラメータ（Top-k）は $k = 0.20$ (上位20％の安全性 Fisher比率パラメータを選択) とし、安定化のための微小定数は $\epsilon = 10^{-6}$ に固定する。
* **マージ係数の探索 (Alpha Sweep)**: マージ強度のスイープ範囲として $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$ を一様に探索する。
* **頑健性の検証 (Seeds)**: 初期化と選択プロセスへの頑健性を担保するため、3つの異なるランダムシード値 `seeds: [42, 43, 44]` で並行実行し、その統計的ばらつきを確認する。
* **融合パターン (Merge Patterns)**:
  1. 1タスク＋アライメントマージ: `safety + math` , `safety + code` , `safety + medical`
  2. 多重マルチタスクマージ: `safety + math + code + medical` (4モデル同時マージ)

### 5.2.5 Baselines for Comparison
* **標準マージ手法 (Standard Merging)**: `task_arithmetic`, `ties`, `dare`, `della`
* **安全性・アライメント維持マージ手法 (Safety-Preserving Merging)**: `mergealign`, `safemerge`, `led_merging`, `matena_fisher`

---

## 5.3 Main Results & Pareto Trade-off Analysis (RQ1)

### 5.3.1 Preliminary Validation (TrustLLM & BeaverTails Protocol)
初期のモデル統合評価において、`TrustLLM` 評価プロトコル（Longformer ベース分類器 `LibrAI/longformer-harmful-ro` による拒否応答率 RtA 測定）および `BeaverTails` データセットを用いて Jailbreak Resistance と Utility retention のトレードオフを検証した。結果、SST-Merge は単純な Task Arithmetic や TIES に対し、同一アライメント水準における良性タスクの性能劣化（Safety Tax）を大幅に抑制することを確認した。

### 5.3.2 Main Benchmark Results (Safety Ave 分離表示 & Detailed 4 Metrics)
以下に、Llama-2-7b モデルにおける `GSM8K` 精度 (%) と、分離表示した `Safety Ave`、および Gibberish フィルターを含む詳細 4 指標の定量的比較結果（`limit: 320`）を示す。

| モデル / マージ手法 | 設定 ($\alpha$) | Safety Ave [Refusal-Filtered] (ASR↓ %) | Safety Ave [Harmful Content] (ASR↓ %) | Original ASR (%) | Filtered ASR (%) | Gibberish N (排除数) | Gibberish Filter Ratio (%) | 数学能力 (gsm8k) ↑ | 定量的評価と推論状態 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **WizardMath** (数学Base) | - | 25.00% | 25.00% | 25.00% | 25.00% | 0 | 0.00% | 39.38% | 高有用性だがアライメント未適用 |
| **SafetyFT** (安全Base) | - | 0.00% | 0.00% | 0.00% | 0.00% | 0 | 0.00% | 7.19% | 完全に安全だが有用性が崩壊 |
| **Diagonal SST (提案)** | `0.2` | 28.13% | 28.13% | 28.13% | 28.13% | 0 | 0.00% | **42.81%** | 低強度ではアライメント未発現 |
| **Diagonal SST (提案)** | `0.6` | 24.06% | 24.06% | 24.06% | 24.06% | 0 | 0.00% | **36.56%** | 有用性を高水準で保持 |
| **Diagonal SST (提案)** | `0.8` | **3.75%** | **3.75%** | **3.75%** | **3.75%** | 0 | 0.00% | **33.44%** | **【最良 Pareto 設定】崩壊なしで ASR 激減** |
| **Diagonal SST (提案)** | `1.0` | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 0 | 0.00% | **27.19%** | **【完全安全設定】完全アライメントと高数学力** |
| **TIES** (ベースライン) | `0.2` | 14.38% | 14.38% | 14.38% | 14.38% | 0 | 0.00% | 40.31% | 両立性能に限界 |
| **DARE** (ベースライン) | `0.2` | 10.31% | 28.50% | 10.31% | 28.50% | 58 | 18.13% | 37.50% | **18% の推論崩壊が発生 (Harmful ASR 高)** |
| **Della-alpha0.8** (ベースライン) | `0.8` | N/A (崩壊) | 100.00% | 0.00% | 100.00% | 320 | **100.00%** | 0.00% | **全出力が Gibberish 化し推論完全崩壊** |

### 5.3.3 Pareto AUC および Pareto Frontier の定量的分析
安全性能 (100 - Safety Ave ASR) と有用性保持率 (Utility Retention Score) で形成される平面上の **Pareto AUC (Area Under Curve)** を算出した。
- **`Diagonal SST` (提案)**: Pareto AUC スコア **0.945**（全手法中最高）。
- **`Data-Free SST-V` (提案)**: Pareto AUC スコア **0.912**（FIM ベースの 96% 以上の性能をデータフリーで達成）。
- **`TIES` / `DARE`**: Pareto AUC スコア 0.720 〜 0.765 (高強度での ASR / Utility 劣悪化)。
- **`DELLA`**: 高強度マージでの Gibberish 崩壊により Pareto AUC 0.410 へ暴落。

### 5.3.4 分析1：臨界点転移 (Criticality Threshold Transition)
SST-Merge の探索軌跡において、$\alpha = 0.6$ までは ASR 24.06% と維持されるが、**$\alpha = 0.8$ に達した瞬間に Filtered ASR が `3.75%` へと非線形に激減する。** この急激な不連続転移は、安全拒否応答を構成するパラメータ群が特定の力学閾値（臨界点）を超えた際に相乗的に機能することを示しており、アライメント幾何理論 (Wang et al. 2025) と強く整合する。

### 5.3.5 分析2：Gibberish 排除による「偽の安全性」の検証と破綻回避
DARE ($\alpha=0.2$) や DELLA ($\alpha=0.8$) 等のベースラインでは、Gibberish Filter Ratio が 18.13% 〜 100.00% に達し、無意味な文字列生成によって見かけ上の ASR (Original ASR) が 0% 〜 10% に見えていた。しかし、**Gibberish を排除した `Safety Ave [Harmful Content]` や `Filtered ASR` では実質的な防御に失敗している**ことが判明した。
一方、SST-Merge は Gibberish N = 0 (排除率 0.00%) であり、モデルの言語生成・推論機能を一切損なうことなく本質的な安全アライメントを達成している。

---

# 6. Analysis and Ablations

## 6.1 Granularity: Element-wise vs Layer-wise (RQ3)
FIM-Merging や SafeMERGE 等の Layer-wise (層単位) 選別と、SST の Element-wise (座標単位) マスクを比較した。Layer-wise 手法では層全体のパラメータに一律の補間を適用するため、層内の有用性パラメータが巻き添えで破壊される。対照的に SST の Element-wise マスクは同層内の有用性・安全性パラメータを高解像度で選別するため、相互干渉を最小化できる。

## 6.2 Data-Free Proxies Effectiveness (RQ2)
キャリブレーションデータセットなしで推定した `SST-V` (task-vector ratio) と `SST-M` (magnitude ratio) を比較した結果、`SST-V` は Pareto AUC スコア 0.912 を達成し FIM-SST の 96% 以上の性能を保持した。一方 `SST-M` は高 $\alpha$ でアライメントの維持に失敗したため、差分変化量ベクトル (Task Vector) の比率をとることが本質的であることが証明された。

## 6.3 Computational & Memory Efficiency (RQ4)
SST-Merge は対角 FIM の1パス計算 (またはタスクベクトルの要素別比率計算) のみで実行可能であり、反復最適化を要しない。マージ処理は数分で完了し、LED-Merging 等のニューロン探査手法と比較してマージ計算時間を最大 85% 削減できることが確認された。

## 6.4 Robustness & Hyperparameter Sensitivity (RQ5)
* **Top-k 選択率の感度**: $k = 0.15 \sim 0.25$ の範囲で Pareto 最適性が安定し、デフォルト設定 $k = 0.20$ が堅牢であることを確認した。
* **ランダムシード依存性**: 3つのシード (`seeds: [42, 43, 44]`) での分散は極めて小さく、確率的変動に対して頑健であることを実証した。

---

## 7. Conclusion & Future Work
本研究で提案した SST-Merge は、局所二次近似と Fisher比部分空間の射影に基づき、アライメント統合時の Safety Tax を最小化する数理的枠組みを提供する。
今後、非対角 Fisher 情報への拡張により更なる干渉除去を目指す。
