# SST-Merge V3 詳細実験設計レポート (Experiment Design Report)

本レポートは、良性タスク性能（Utility）と安全性能（Safety）のトレードオフ（Safety Tax）を幾何学的最適化問題として扱い、安全アライメントをモデルに統合する手法 **SST-Merge** およびそのデータフリー近似 **Data-Free SST-Merge** を検証するための実験環境設計とコードベースの技術的解説をまとめたものです。

---

## 1. 実験の全体設計 (Experimental Design)

本実験環境は、`/mnt/nas/home/hiromi/src/sst_v2/v3/kiro` の仕様・規約を完全に遵守し、AAA-27 投稿レベルの科学的・統計的厳密さで手法の優位性を実証することを目的に構築されています。

### 1.1 対象モデルとデータセット

ベースモデルとして `Llama-2-7B` を採用し、以下の 3 つのドメイン特化（Utility）モデルおよび 1 つの安全（Safety）モデルをマージ対象とします。

*   **ベースモデル**: `meta-llama/Llama-2-7b-hf`
*   **Math ドメインモデル**: `WizardLMTeam/WizardMath-7B-V1.0` (Llama-2-7Bベース)
*   **Code ドメインモデル**: `WizardLMTeam/WizardCoder-Python-7B-V1.0` (Llama-2-7Bベース)
*   **Medical ドメインモデル**: `medalpaca/medalpaca-7b` (Llama-2-7Bベース)
*   **Safety モデル**: `Llama-2-7B` に対し、`data/response_dataframe.csv` を用いて拒絶（Refusal）アライメントを学習させた独自モデル

### 1.2 実験マージパターン (4パターン)

1.  **Pattern A**: Safety model + Math
2.  **Pattern B**: Safety model + Code
3.  **Pattern C**: Safety model + Medical
4.  **Pattern D**: Safety model + Math + Code + Medical (4モデル統合)

### 1.3 評価指標

*   **Safety (ASR ↓ / Resistance ↑)**:
    *   **指標**: Attack Success Rate (ASR: 脱獄攻撃成功率)、Over-refusal Rate (過剰拒否率)。
    *   **ベンチマーク**: `HarmBench`, `JailbreakBench`, `StrongREJECT`, `WildJailbreak`。
*   **Utility (Task Accuracy ↑)**:
    *   **指標**: 各種タスクの正解率、指示追従率。
    *   **ベンチマーク**: `MMLU-Pro`, `MMLU`, `IFEval`, `GSM8K`, `MATH-500`, `MBPP`, `AlpacaEval 2`, `RepliQA`。

---

## 2. アブレーションスタディの設計 (Ablation Study)

提案手法の各モジュールの有効性を多角的に検証するため、以下の 2 つのカテゴリにまたがるアブレーションを実行します。

### 2.1 SST ratio (パラメータ重要度の基準)
FIMまたはパラメータ差分から抽出するパラメータ座標ごとの「効率比 $\lambda_i$」の基準を切り替えます。
*   **`Fh/Fb` (提案手法)**:
    *   FIMベース: $\lambda_i = \frac{f_{h,i}}{f_{b,i} + \varepsilon}$ (良性・有害のFisher情報の比率)
    *   Data-Freeベース: $\hat{\lambda}_i = \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2 + \varepsilon}$ (重み差分の二乗の比率)
*   **`Fh only` (Benign情報無視)**: $\lambda_i = f_{h,i}$ または $\phi_{h,i}$
*   **`1/Fb only` (Safety情報無視)**: $\lambda_i = \frac{1}{f_{b,i} + \varepsilon}$ または $\frac{1}{\phi_{b,i} + \varepsilon}$
*   **`magnitude` (絶対値ベース)**: $\lambda_i = |\Delta_{s,i}|$ (Safetyモデルの重み差分の絶対値)
*   **`random` (ランダム選択)**: $\lambda_i \sim \text{Uniform}(0, 1)$

### 2.2 Variants (マージ構成・マスク形式)
*   **マージ形式**:
    *   `additive` (加算): $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha (w_{\mathrm{layer}} \odot m \odot \Delta_s)$
    *   `interpolation` (補間): $\theta_{\mathrm{merged}} = (1-w)\odot\theta_{\mathrm{util}} + w\odot\theta_{\mathrm{safe}}$
*   **マスク形式**:
    *   `hard mask`: 上位 $k$ の座標を $1$、それ以外を $0$ とする二値マスク。
    *   `soft mask`: $m_i = \sigma\left(\frac{\log(\lambda_i + \delta)}{\tau}\right)$ による連続的確率マスク。
*   **レイヤー優先度**:
    *   `layer-wise on`: 層深さに応じた prior $w_{\mathrm{layer}}$ を適用。
    *   `layer-wise off`: $w_{\mathrm{layer}} = 1.0$ (均一)。
*   **FIMのデータサンプル数 $N$**:
    *   $N \in \{50, 100, 500, 1000\}$ のデータサイズで Fisher 情報を推定。
*   **`data-free proxy`**:
    *   データを使用する FIM-SST と、データを用いない Data-Free SST の性能比較。

---

## 3. 実験コードの技術的詳細解説 (Codebase Walkthrough)

### 3.1 `data_prep.py` (データの個別準備)
FIMの $F_b$ 推定用の良性データセットは、ドメインごとに完全に分離して準備されます。
*   **Math**: Hugging Face の `WizardLMTeam/WizardMath` から指示応答ペアを抽出し `fim_benign_math.json` に保存。
*   **Code**: `nickrosh/Evol-Instruct-Code-80k-v1` からコード指示ペアを抽出し `fim_benign_code.json` に保存。
*   **Medical**: `medalpaca/medical_meadow` から QA ペアを抽出し `fim_benign_medical.json` に保存。
*   **Harmful**: 安全アライメントデータ `/v3/data/response_dataframe.csv` を JSON に変換し `fim_harmful.json` に保存。

### 3.2 `fine_tuning.py` (Safety FT)
ベースモデル `Llama-2-7B` に対し、`response_dataframe.csv` を用いて LoRA（Rank=16, Alpha=32）による SFT を行います。
*   最新の `transformers` 互換性を考慮し、非推奨となった `evaluation_strategy` から `eval_strategy="no"` へ修正。
*   学習完了後、成果物ディレクトリにベースモデル名、ハイパーパラメータ、および Git Commit ID などのメタデータを `merge_metadata.json` として自動保存します。

### 3.3 `merge.py` (マージコアとSVD LoRAブリッジ)
SST-Merge、Data-Free SST-Merge、および全ベースライン手法を実行する中核コードです。

#### 1. FIM推定 (`estimate_fim`):
対象とする線形レイヤーの重み（`q_proj`, `v_proj` 等）に絞り、各サンプルの損失に対する勾配の2乗期待値を蓄積して対角 FIM を算出します。

#### 2. ドメイン別 FIM の合算:
Pattern D (4モデルマージ) の場合、Math, Code, Medical の各データから個別に $F_{b,\mathrm{math}}$, $F_{b,\mathrm{code}}$, $F_{b,\mathrm{medical}}$ を算出し、それらの平均をとることで、全ドメインの Utility 劣化を抑制する統合 Fisher 情報 $F_b$ を構築します。
$$F_b = \frac{\sum_{t \in \{\text{math}, \text{code}, \text{medical}\}} F_{b,t}}{3}$$
Data-Free の Proxy においても同様に、各ドメインのタスクベクトルの二乗平均を $\phi_b$ とします。
$$\phi_b = \frac{\sum_{t} (\Delta_{b,t})^2}{3}$$

#### 3. 異種モデル間の不整合を解決するブリッジ:
*   **SVD LoRA 変換 (`convert_full_to_lora`)**:
    `SafeMERGE` は LoRA アダプタ同士のマージを前提としています。そのため、ドメインモデル（フルパラメータ）とベースモデルの差分 $\Delta W$ を計算し、SVD（低ランク特異値分解）を用いて、PEFT (LoRA) アダプタ形式の重み（`lora_A`, `lora_B`）に動的に変換し、`SafeMERGE` に流し込みます。
*   **フルパラメータ化 (`merge_and_unload`)**:
    `LED-Merging` や `MergeAlign` はフルパラメータモデル同士をマージします。そのため、LoRA である `safety FT model` をベースモデルに一時的に統合してフルパラメータ化した `temp_safety_full` を作成し、外部スクリプトに渡します。

### 3.4 `run_experiments.py` (シーケンシャルランナー)
実験の実行フローを指定の順序に沿って一括で制御します。
1.  **SFT学習**: `fine_tuning.py` の実行。
2.  **マージ前（ベース）モデルの評価**: 4モデル（Math, Code, Medical, Safety）それぞれの ASR と lm-eval の実行。
3.  **モデルマージ**: 4パターン、全10手法（提案2、比較8）、およびアブレーションの実行。
4.  **マージ後モデルの評価**: 生成された全マージモデルの ASR と lm-eval の実行。
5.  **Pareto境界・AUC解析**: `pareto_auc.py` による最終可視化。

---

## 4. 規約遵守チェックリスト (Compliance Checklist)

| 規約項目 (`kiro`) | 実装での対応内容 | ステータス |
| :--- | :--- | :---: |
| **データ分割の物理的分離** | `data_prep.py` で FIM 推定用データを個別に配置し、評価用パスとの重複を `steering_hook.py` で動的に遮断。 | **遵守済** |
| **比較手法のカスタム排除** | TIES/DARE/Task Arithmetic/DELLA を `mergekit-yaml` で強制実行。カスタムコードへのフォールバックなし。 | **遵守済** |
| **Data-Free 実行時のデータ遮断** | `data_free_sst` 実行時に `steering_hook.enable_data_free_monitoring()` を呼び出し、組み込みの `open` をフックしてデータアクセスを遮断。 | **遵守済** |
| **乱数シードの固定と複数シード** | `seeds: [42, 43, 44]` による3シードループ実行と、`pareto_auc.py` による `mean ± std` 集計。 | **遵守済** |
| **メタデータの完全保存** | 学習・マージ成果物に `merge_metadata.json` を自動保存。 | **遵守済** |
| **図表の再生成可能性** | `pareto_auc.py` が生 JSON 結果を元にプロット（`pareto_frontier.png`）を再生成。 | **遵守済** |
