# SST-Merge V3 実験環境構築 実装計画 (Implementation Plan) - 改訂版

本計画は、ユーザーのリクエストに基づき、`/mnt/nas/home/hiromi/src/sst_v2/v3` に SST-Merge および Data-Free SST-Merge の実験環境を1から再構築するためのものです。
アブレーション・スタディに関する詳細要件を反映し、実験の完全性と規約の遵守（`kiro`）を徹底します。

---

## 1. 実験の設計・構成

### 1.1 対象モデルとデータセット
ベースモデルには `meta-llama/Llama-2-7b-hf` を使用し、以下の各ドメイン特化モデルとのマージを行います。

- **Math**: `meta-llama/Llama-2-7b-hf` -> `WizardLMTeam/WizardMath-7B-V1.0`
- **Code**: `meta-llama/Llama-2-7b-hf` -> `WizardLMTeam/WizardCoder-Python-7B-V1.0`
- **Medical**: `meta-llama/Llama-2-7b-hf` -> `medalpaca/medalpaca-7b`
- **Safety**: `meta-llama/Llama-2-7b-hf` に `v3/data/response_dataframe.csv` を用いて SFT (LoRA) を施した独自モデル

### 1.2 評価マージパターン (4パターン)
- **Pattern A**: Safety model + Math
- **Pattern B**: Safety model + Code
- **Pattern C**: Safety model + Medical
- **Pattern D**: Safety model + Math + Code + Medical (4モデル統合)

### 1.3 評価指標
- **Safety**: HarmBench, JailbreakBench, StrongREJECT, WildJailbreak (ASRおよび過剰拒否率の測定)
- **Utility**: MMLU-Pro, MMLU, IFEval, GSM8K, MATH-500, MBPP, AlpacaEval 2, RepliQA / Alpaca

---

## 2. 提案手法（SST-Merge）およびアブレーションの設計

SST-Merge は、パラメータ選別の基準となる「効率比 $\lambda_i$」と、「マージ方法（バリアント）」によって制御されます。本実験環境では以下のアブレーションを網羅して実行します。

### 2.1 SST ratio (パラメータ重要度の基準)
- **`Fh/Fb` (SST-Merge提案手法)**:
  - FIMベース: $\lambda_i = \frac{f_{h,i}}{f_{b,i} + \varepsilon}$
  - Data-Freeベース: $\hat{\lambda}_i = \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2 + \varepsilon}$
- **`Fh only` (Benign情報無視)**:
  - $\lambda_i = f_{h,i}$ (または $\phi_{h,i}$)
- **`1/Fb only` (Safety情報無視)**:
  - $\lambda_i = \frac{1}{f_{b,i} + \varepsilon}$ (または $\frac{1}{\phi_{b,i} + \varepsilon}$)
- **`magnitude` (絶対値ベース)**:
  - $\lambda_i = |\Delta_{s,i}|$ (Safetyモデルの重み差分の絶対値)
- **`random` (ランダム)**:
  - $\lambda_i \sim \text{Uniform}(0, 1)$

### 2.2 Variants (マージ構成・マスク形式)
- **マージ形式**:
  - **`additive` (加算)**: $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha (w_{\mathrm{layer}} \odot m \odot \Delta_s)$
  - **`interpolation` (補間)**: $w = \text{clip}(\alpha (w_{\mathrm{layer}} \odot m), 0, 1)$、$\theta_{\mathrm{merged}} = (1-w)\odot\theta_{\mathrm{util}} + w\odot\theta_{\mathrm{safe}}$
- **マスク形式**:
  - **`hard mask`**: $\lambda_i$ の上位 $k$ 座標のマスク $m_i = 1$、その他は $0$
  - **`soft mask`**: $m_i = \sigma\left(\frac{\log(\lambda_i + \delta)}{\tau}\right)$
- **レイヤー優先度**:
  - **`layer-wise on`**: レイヤーの特性（lm_head, Attention, FFN 等）に応じた prior $w_{\mathrm{layer}}$ を乗算する
  - **`layer-wise off`**: すべてのレイヤーで $w_{\mathrm{layer}} = 1.0$ とする
- **FIMのデータサンプル数 $N$**:
  - $N \in \{50, 100, 500, 1000\}$ のデータサイズで Fisher 情報を推定し、推定精度と性能の関係を分析する
- **`data-free proxy` (データフリー近似の評価)**:
  - データを用いて FIM を算出する SST-Merge と、データを用いずにタスクベクトル差分の比率を Proxy とした Data-Free SST-Merge の性能比較

---

## 3. 実装予定のファイル構成 (`v3/`)

- **`v3/requirements.txt`**: 依存関係（`transformers`, `peft`, `mergekit`, `lm-eval` 等）
- **`v3/configs/config.yaml`**: アブレーションスイープパラメータを含む実験設定ファイル
- **`v3/scripts/data_prep.py`**: FIM用および評価用データセットの取得と配置
- **`v3/scripts/fine_tuning.py`**: `response_dataframe.csv` を用いた Safety model の LoRA SFT
- **`v3/scripts/merge.py`**: SST-Merge / Data-Free SST-Merge の各種アブレーション対応ロジックおよび公式 `mergekit` の実行ラッパー
- **`v3/scripts/eval_safety.py`**: 安全性評価（ASR）の実行と判定
- **`v3/scripts/eval_utility.py`**: `lm-evaluation-harness` を用いた性能評価
- **`v3/scripts/pareto_auc.py`**: アブレーション結果を統合したパレート境界および AUC の算出と可視化

---

## 4. 科学的厳密性と `kiro` 規約の遵守
- `steering_hook.py` にて、Data-Free 実行時のファイル IO 遮断、および評価用データセットと FIM 推定/学習用データセットの完全分離を動的に検証します。
- 比較手法（Task Arithmetic, TIES, DARE等）は、独自実装コードのフォールバックを禁止し、公式 `mergekit` の YAML 連携を強制します。

---

## 5. 検証計画
- ダミーデータまたは少数の座標を用いたユニットテストにより、`Fh/Fb`, `Fh only`, `1/Fb only`, `magnitude`, `random` のマスキング処理および `additive`/`interpolation` による重みマージが理論通りにパラメータを選択することを確認します。
