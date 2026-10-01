# AAAI-27 実験設計書 (Design Spec) - 最終決定版

本設計書は、SST-Mergeの実証実験において、FIM推定データの完全分離、YAML構成管理、および評価/解析パイプラインのアーキテクチャ設計を定義するものです。

---

## 1. 実験データの物理的役割分離 (Data Separation Design)

FIM (Fisher Information Matrix) 推定用のデータが評価用ベンチマークデータと重複し、評価データを事前に「カンニング」しているという疑念を排除するため、以下のようにデータを物理的に分離して実験を設計します。

```text
+---------------------------------------------------------------------------------+
|                                 ベンチマーク全体                                 |
+---------------------------------------------------------------------------------+
        |                                                 |
        v                                                 v
  【FIM推定・学習・チューニング用】              【評価ベンチマーク用（完全遮断）】
  - F_h 推定用: Custom Jailbreak /               - Safety 評価: HarmBench, JBB,
    BeaverTails train dataset                      StrongREJECT, WildJailbreak,
                                                   HELM-Safety, AdvBench
  - F_b 推定用: RepliQA train /                  - Utility 評価: MMLU-Pro, IFEval,
    Alpaca train dataset                           GSM8K, MATH-500, HumanEval,
                                                   MBPP, AlpacaEval 2, MT-Bench
  - LoRA 学習用: 独立した SFT subsets
```

### データ分離の具体的割り当て

| 用途 | 具体的なデータセット割り当て |
|---|---|
| **F_h 推定** | Custom Jailbreak / BeaverTails train |
| **Safety 評価** | HarmBench, JailbreakBench, StrongREJECT, WildJailbreak, HELM-Safety, AdvBench, XSTest |
| **F_b 推定** | RepliQA train / Alpaca train |
| **Utility 評価** | MMLU-Pro, IFEval, GSM8K, MATH-500, HumanEval, MBPP, AlpacaEval 2, MT-Bench |

- **FIM 推定用データセットの配置**: `v2/data/fim/` 配下に配置（例: `fim_harmful_beavertails.json`, `fim_benign_repliqa.json`）。
- **評価用データセットの配置**: `v2/data/eval/` 配下に配置（これらはマージやFIM推定の python 実行から物理的にアクセス不可とします）。
- **検証フックによる監視**: `steering_hook.py` が、`eval_dataset` と `fim_dataset` または `training_dataset` のパスが同じ物理パスを指している場合に例外を送出します。

---

## 2. 実験管理のYAML化設計 (`configs/aaai27/`)

実験設定のハードコーディングを一切排除するため、マージから評価までをすべて YAML 設定ファイルで定義・制御します。

### 構成スキーマ例 (`configs/aaai27/llama31_sst_config.yaml`)
```yaml
experiment:
  name: "llama31_sst_reproduction"
  seed: 42
  num_seeds: 3
  
model:
  base_model: "meta-llama/Meta-Llama-3.1-8B-Instruct"
  utility_lora: "models/utility_ft_model"
  safety_lora: "models/safety_ft_model"
  lora_config:
    rank: 16
    alpha: 32
    dropout: 0.05
    target_modules: "all-linear"

fim:
  benign_dataset: "data/fim/fim_benign_repliqa.json"
  harmful_dataset: "data/fim/fim_harmful_beavertails.json"
  sample_size: 500
  epsilon: 0.000001

merge:
  method: "diagonal_sst" # diagonal_sst, data_free_sst, ties, dare
  implementation: "official"
  alpha_sweep: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
  k_sweep: ["soft", 0.05, 0.10, 0.20, 0.50]

evaluation:
  safety_tasks: ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak", "helm_safety", "advbench"]
  utility_tasks: ["mmlu_pro", "mmlu", "ifeval", "gsm8k", "math_500", "human_eval", "mbpp", "alpaca_eval_2", "mt_bench"]
  eval_data_dir: "data/eval"
```

---

## 3. 新規評価・解析スクリプトのアーキテクチャ設計

### 3.1 `eval_safety_suite.py` (安全性評価一括実行)
- **入力**: マージ済みモデルのパス、`configs/aaai27/*.yaml`、評価用タスクリスト。
- **処理**: 
  - 各安全性ベンチマーク（HarmBench, JBB等）から攻撃用プロンプトを取得。
  - 推論（vLLM または HF pipeline を使用して効率化）を実行し、応答テキストを収集。
  - 各ベンチマークの公式評価判定器（HarmBench Classifier 等）を呼び出して ASR を算出。
- **出力**: `results/raw/<exp_name>_safety_raw.json`

### 3.2 `eval_utility_suite.py` (一般性能評価一括実行)
- **入力**: マージ済みモデルのパス、`configs/aaai27/*.yaml`、評価用タスクリスト。
- **処理**:
  - `lm-evaluation-harness` の API を内部でインポートまたはサブプロセスで呼び出す。
  - 指定されたタスク（`mmlu_pro`, `ifeval`, `gsm8k` 等）を同一条件（few-shot数、device等）で実行。
- **出力**: `results/raw/<exp_name>_utility_raw.json`

### 3.3 `pareto_auc.py` (パレート境界自動解析)
- **処理**:
  - `results/raw/` に保存された $\alpha, k$ スイープの ASR と Utility (MMLU-Pro等) の値をロード。
  - 手法ごとに Pareto frontier を抽出し、その下部面積（Pareto AUC）を算出。
  - 任意の Utility 保持率（例: 95%）時の ASR （＝ **Safety@95% Utility**）を補間計算。
  - シード間の統計処理（平均、標準偏差、bootstrap CI）を計算し、論文用プロットを `results/pareto/pareto_frontier.png` に出力。
- **出力**: `results/pareto/pareto_metrics_summary.csv`
