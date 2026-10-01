# AAAI-27 実装・実験タスク管理 (Tasks Spec) - 最終決定版

本ドキュメントは、SST-MergeのAAAI-27採択に向けた具体的な開発、アブレーション、および実験手順の進捗を追跡するためのタスク管理表（Tasks Spec）です。

---

## 1. 具体的な開発・実験タスク一覧

### Phase 1: マージ基盤とフックの整備
- [ ] **レガシーカスタム実装の無効化と mergekit 強制**:
  - `v1/scripts/merging/baseline_merge.py` で mergekit 以外のフォールバックを排除し例外を送出する。
- [ ] **高度マージ手法の追加**:
  - `baseline_merge.py` または `run_mergekit.sh` に DELLA, Breadcrumbs, Fisher-weighted, RegMean, SafeMERGE, LED-Merging, MergeAlign などの公式 CLI yaml 出力を追加。
- [ ] **自動検証フックの同期・強化**:
  - `v2/scripts/steering_hook.py` にデータ重複チェック、Data-Free時の cached statistics 遮断、ベースモデル（Llama-3.1-8B）チェックを追加。
  - `v2/scripts/test_steering_hook.py` のテストケースを全網羅し、パスさせる。

### Phase 2: 新規評価・解析スクリプトの開発
- [ ] **YAML構成管理ファイルの作成**:
  - `v2/configs/aaai27/config_example.yaml` などの実験管理設定ファイルを定義。
- [ ] **`eval_safety_suite.py` の実装**:
  - HarmBench, JBB, StrongREJECT, WildJailbreak のプロンプト読み込みと推論一括実行ロジック。
  - 各判定器との連携による ASR 算出および生結果の JSON 保存。
- [ ] **`eval_utility_suite.py` の実装**:
  - `lm-evaluation-harness` をインポートし、MMLU-Pro, IFEval, GSM8K 等の評価を自動起動・集計する。
- [ ] **`pareto_auc.py` の実装**:
  - 各 $\alpha, k$ の ASR と Utility をパースし、Pareto frontier の AUC および **Safety@95% Utility** を自動計算する。
  - シード間の bootstrap CI、および paired bootstrap 統計検定を算出。
  - 解析結果プロット図（PDF/PNG）と概要 CSV の自動生成。

### Phase 3: 実験・アブレーションの自動実行
- [ ] **SFT LoRA 学習モデルの構築**:
  - Meta-Llama-3.1-8B-Instruct, Mistral-7B-Instruct, Qwen2.5-7B-Instruct の 3 モデルに対して、学習データと評価データを完全に分離した状態での LoRA 学習（Utility & Safety）。
- [ ] **実験グリッドの自動スイープ実行**:
  - 全 3 モデルに対し、12 手法 × 11 の $\alpha$ スイープ × 5 の $k$ スイープを実行。
- [ ] **SST内アブレーション（11項目）の自動実行**:
  - F_h only, 1/F_b only, magnitude, random, soft/hard, prior on/off, N-size, negative control 等の一括アブレーション。

### Phase 4: 図表の自動生成と論文用まとめ
- [ ] **AAAI 主表の自動生成**:
  - `pareto_auc.py` の結果から、指定された主表フォーマットを LaTeX テーブル形式で自動出力。
- [ ] **Pareto フロンティア曲線のプロット生成**:
  - SST-Merge が既存手法を大きくアウトパフォームしていることを示すグラフの自動描画。

---

## 2. 進捗状況の管理

各タスクは以下の記号で状態を管理します。
- `[ ]` 未着手
- `[/]` 進行中
- `[x]` 完了

進捗があり次第、本ドキュメントを更新し、実験の完全なる透明性と再現性を担保します。
