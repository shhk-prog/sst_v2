# SST-Merge 論文 第5章 実験 (Experiments) リファイン・執筆タスク

## 目的
ユーザーから提示された「5. Experiments」の草稿構成（RQ1〜RQ5、5.2節の設定詳細、対象モデル、FIMデータ、評価指標、ベースライン等）に基づき、`/mnt/nas/home/hiromi/src/sst_v2/v3/scripts` の実実験構成・パラメータ・ベンチマーク結果を完全に紐付けた、学術論文品質の日本語「第5章 実験 (5. Experiments)」ドキュメントを構築・整備する。

## タスク一覧

### フェーズ 1: 初稿構築
- [x] **1. リポジトリ内実験構成・スクリプト詳細の精密精査**
  - `v3/configs/config_main.yaml` および `v3/scripts/` 配下（`run_experiments.py`, `merge.py`, `mergers/`, `eval/`）の設定値、モデル名、評価プロトコル、ベースライン手法を抽出・照合。
- [x] **2. ドキュメント保存フォルダ・管理ファイルの作成**
  - `docs/paper_experiments_section/` フォルダの作成。
  - `task.md`, `implementation_plan.md`, `walkthrough.md` の初期作成。
- [x] **3. 論文第5章「5. Experiments」完全版執筆**
  - **5.1 Research Questions (RQ1 ~ RQ5)** の詳細化とリファイン。
  - **5.2 Detailed Experimental Design & Setup**:
    - Target Models (Llama-2-7b-hf, WizardMath-7B, WizardCoder-Python-7B, medalpaca-7b, safety_lora)
    - Fisher Calibration Datasets (fim_harmful.json, fim_benign_*.json, N=500, epsilon=1e-6)
    - Evaluation Benchmarks & Metrics (Safety: HarmBench, JailbreakBench, StrongReject, WildJailbreak, XSTest; Utility: GSM8K, Minerva Math500, HumanEval, MBPP, PubMedQA, MedQA-4options, MMLU, IFEval)
    - Hyperparameters & Merge Settings (SST-Interpolation, hard mask, k=0.20, alpha sweep [0.0..1.0], seeds [42, 43, 44], 4 merge patterns)
    - Baselines (Standard: task_arithmetic, ties, dare, della / Safety: mergealign, safemerge, led_merging, matena_fisher)
  - **5.3 Preliminary & Main Benchmark Results (RQ1, RQ2)**:
    - パレート境界分析、閾値効果（Criticality threshold transition）、崩壊モードの回避メカニズム
  - **5.4 Detailed Ablation & Analytical Studies (RQ2, RQ3, RQ4, RQ5)**:
    - RQ2: Data-free SST-V vs FIM-SST vs SST-M
    - RQ3: Element-wise vs Layer-wise Granularity
    - RQ4: Computational Efficiency & Overhead Comparison
    - RQ5: Hyperparameter Sensitivity & Robustness ($k$, $\alpha$, seeds)

### フェーズ 2: 評価指標の精密化および TrustLLM 追加要望対応
- [x] **4. 安全性詳細 4 指標の組み込み**
  - `Original ASR (%)`, `Filtered ASR (%)`, `Gibberish N`, `Gibberish Filter Ratio (%)` の 4 指標の定義と定量分析テーブルへの組み込み。
- [x] **5. Safety Ave の 2 区分分離表示**
  - `Safety Ave [Refusal-Filtered] (ASR↓ %)` (Gibberish 排除後) と `Safety Ave [Harmful Content] (ASR↓ %)` (HarmBench 統一基準) への 2 区分分離と分析の追加。
- [x] **6. Pareto AUC の定量的分析の反映**
  - SST-Merge (0.945) vs Data-Free SST-V (0.912) vs Baselines の Pareto AUC 定量評価の明記。
- [x] **7. TrustLLM / BeaverTails の利用位置づけの解明と本文修正**
  - 予備実験 (Preliminary Evaluation) における `TrustLLM` 評価プロトコル（Longformer 分類器 `LibrAI/longformer-harmful-ro` による RtA 測定）および `BeaverTails` 500 サンプルセットの役割の明確化。
