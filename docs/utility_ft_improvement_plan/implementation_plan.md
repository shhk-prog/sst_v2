# Utility Fine-Tuning 改善実装計画

Phase 2 / 2a で明らかになった「学習後半での過学習と repetition_collapse による HumanEval (OOD) の極端なスコア低下」および「評価フォーマットの非対称性」を解決し、Utility FT を成功させるための具体的な実装計画です。

## User Review Required

> [!IMPORTANT]
> 以下の実装方針で進めてよいかご確認をお願いします。
> 特に推論側での `repetition_penalty` の導入や、`base_with_template` を用いた評価フォーマットの統一など、評価の前提に影響を与える変更が含まれています。

## Open Questions

> [!WARNING]
> 1. **Target Modules の確認**: 現在の LoRA が全 linear レイヤー（`q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`）にかかっている想定ですが、これを一部（例: 注意機構のみ）に絞る実験も計画に含めますか？
> 2. **データの扱い**: `clean_coding_data.py` を用いた aggressive clean（Markdown 外の説明文を削除）したデータと、生データの両方を比較検証する方向で進めてよいですか？

---

## Proposed Changes

### 1. Fine-Tuning スクリプトの改修 (`run_phase2.sh`, `run_phase2_python.sh`)
完走版と Early Stopping (ES) 版が安全に比較・保存されるようにします。

- **RUN_NAME の分離**: 完走させる場合と ES を効かせる場合で、出力フォルダが上書きされないように `RUN_NAME` を固定・明示します。
- **Best Checkpoint の確実なデプロイ**: 
  - `load_best_model_at_end=True` を適用して終了した場合、最適な Checkpoint が自動ロードされます。
  - スクリプト上で `trainer_state.json` の `best_global_step` をパースするか、単に最終出力ディレクトリのモデルを `coding_lora_best` のように明示的にコピー・シンボリックリンクを張り、「どの epoch のモデルが採用されたか」を運用上明確にします。
- **ログの齟齬解消**: 「no early stopping」と表示されているのに実際には ES が効いている箇所など、スクリプトの echo メッセージを実態に合わせて修正します。

### 2. 評価フォーマットの非対称性の解消 (`run_utility_eval.py` 周辺)
学習分布（Templateあり）と推論分布（Templateなし）のズレが OOD 指標を歪めている可能性を排除します。

- **Base モデルの Template 適用評価**:
  - `base_with_template` の評価フェーズを `run_phase2.sh` 等に追加し、ベースモデルにも `--apply_chat_template` を適用した状態で HumanEval 等を実行し、FT後と公平に比較できるようにします。

### 3. データセットの Repetition Collapse 対策
過学習だけでなく、データ形式が原因でモデルが「コード生成後に説明を無限ループする」挙動を修正します。

- **Aggressive Clean の本格運用と検証**:
  - `clean_coding_data.py` を用いて「コードブロックのみ」を残したクリーンなデータセット（`utility_coding_python_clean.json`）を生成します。
  - クリーンなデータを用いた FT (ESあり) と、未クリーニングデータを用いた FT (ESあり) を並行評価し、Repetition Collapse の発生率を比較します。

### 4. 推論・評価プロセスの調整 (Generation Config)
データだけでなく推論パラメータ側から Repetition Collapse を抑え込みます。

- **Repetition Penalty の導入オプション**:
  - `run_utility_eval.py` 等で、lm-eval や vLLM 等のバックエンドに対して `repetition_penalty` (例: 1.05 〜 1.1) や `presence_penalty`、あるいは `temperature` の微調整を渡せる引数を追加します。

### 5. ハイパーパラメータの探索計画
GSM8K（推論能力）の低下を抑えつつコーディング能力を上げるため、適切なバランス点を探ります。

- 学習率とエポックのグリッド（例：lr=5e-5 〜 2e-4, patience=3〜5）をスクリプトで自動連続実行し、`eval_loss` カーブと最終 OOD スコアを JSONL に吐き出して俯瞰的に比較できる仕組みをオプションとして追加します。

---

## Verification Plan

### Automated Tests
1. **ES / Best Checkpoint の動作確認**: `--skip-eval` モードで短く学習を回し、正しく epoch途中の Best Checkpoint が `coding_lora_best` として保存されるか確認する。
2. **Template の適用検証**: `run_utility_eval.py` に対して Base モデル ＋ `--apply_chat_template` を実行し、エラーなく評価が完了するか確認する。

### Manual Verification
- ユーザーに `lr2e-4_ep10_python_clean` などの新規 RUN を手動実行していただき、HumanEval の pass@1 スコア向上および repetition collapse 割合の低下（分析スクリプト実行結果）を確認する。
