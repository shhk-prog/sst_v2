# Secure Merge v4 コード監査・修正指示書 是正完了報告 (Walkthrough v2)

## 1. 監査判定と基本方針の遵守

ユーザーより受領した「Secure Merge v4 コード監査・修正指示書」に基づき、以下の基本方針を厳格に適用しました。

- **実験ステータス**: **`NO_GO`**（本番モデルの tokenizer / RoPE 不整合により主実験は正当に停止）。
- **固定値・模擬データの完全排除**: 過去ログにあった `utility=0.63, ASR=0.028, VRR=0.98` 等の固定辞書や乱数テンソルによるトイ実行を本番経路から完全排除・隔離。
- **欠測値の補完禁止**: 欠測値（未測定の無害VRRや過剰拒否、utility）はすべて `null` として保持し、制約判定では **`INSUFFICIENT_DATA`** として厳格に不適格処理。
- **全回帰テストの通過**: `v4/tests/` 下に独立したテストスイートを作成し、全受入テストを通過。

---

## 2. P0 / P1 指摘事項の是正詳細と受入テスト結果

### 【P0-01】未測定の制約値を合格値で補完する処理の完全撤廃
- **確認された問題**: `vrr_benign = vrr_harmful`、`overrefusal = 0.04`、欠測 utility の `0.0` 補完など。
- **是正内容**:
  - `v4/scripts/analysis/reaggregate_v3_logs.py` および `v4/scripts/analysis/e1_selector.py` から補完ロジックを完全削除。
  - 未測定の指標は `None / null` で保持し、制約判定時に `INSUFFICIENT_DATA` を返出。
  - ステータスを `FEASIBLE` / `INFEASIBLE` / `INSUFFICIENT_DATA` / `OUT_OF_SCOPE` に明確に分離。
- **受入テスト**: `v4/tests/test_e1_selector.py`
  - 無害評価を含まない候補は、ASR=0・有害VRR=1でも `INSUFFICIENT_DATA`（`MISSING_OR_NON_FINITE_VRR_BENIGN`）となることを確認。
  - utility が欠測している候補は選定対象（argmax）から除外されることを確認。

### 【P0-02】v3 utility 保存形式と v4 インポーターの不一致解消
- **確認された問題**: `lm-evaluation-harness` の出力が辞書型（`results: {task: {...}}`）であるのに対し、v4 パーサーがリスト型以外を除外していたこと、およびファイル名サフィックスによる Candidate ID 不一致。
- **是正内容**:
  - `v4/scripts/analysis/reaggregate_v3_logs.py` に lm-eval 辞書型アダプターを実装（`exact_match`, `math_verify`, `acc`, `pass_at_1` 等のメトリクス抽出に対応）。
  - Candidate ID からタスクサフィックスを除去し、Safety 評価（JailbreakBench, HarmBench, StrongReject, WildJailbreak）と Utility 評価（Minerva Math, GSM8k, HumanEval 等）の完全バインドに成功。
  - 324 候補で Safety と Utility の実測データが正確に対応付けられました。
- **受入テスト**: `v4/tests/test_utility_parser.py`
  - 正答率 0.5 の lm-eval 形式最小 JSON から正確に 0.5 を復元。
  - 実 fixture（Minerva Math 500）からスコア 0.383624 を正確に復元。

### 【P0-03】E0 の不合格・未確認による主実験停止ゲートの実装
- **確認された問題**: `audit_models.py` が不整合を検出しても非ゼロ終了せず、runner 側も判定を読まずに通過していた。
- **是正内容**:
  - `v4/scripts/audit/audit_models.py`: Math/Code の vocab_size (32001 vs 32000), RoPE theta (1,000,000 vs 10,000), position embeddings (16,384 vs 4,096) の不整合を検知した場合、`PRIMARY EXPERIMENT GATE: NO_GO` を判定し `sys.exit(1)` で非ゼロ終了。
  - `v4/scripts/run_v4_pipeline.py`: manifest の判定を検証し、主実験トラック（`--track primary`）では E0 で確実に停止。
  - `v4/scripts/mergers/base_merger.py`: テンソル形状不一致の無言コピーを廃止し、厳格にエラーを送出。

### 【P0-04 & P1-02】E2・E3 乱数テストの完全分離と実重み・等パラメータ対照の実装
- **確認された問題**: `__main__` 内に seed 42 の 32×32 乱数テンソルテストが組み込まれ、ログに出力されていた。E3 ランダム対照がテンソル個数のみの一致でパラメータ数や種別が不一致だった。
- **是正内容**:
  - `v4/scripts/analysis/characteristic_analyzer.py`: トイ乱数テストを `v4/tests/` へ移管。実 checkpoint を直接読み込む CLI（`--model-m`, `--model-u` 等）を実装。
  - `v4/scripts/analysis/intervention_mapper.py`: 厳格なモジュール分類（attention, mlp, norm, embed, lm_head）を実装。
  - `v4/scripts/analysis/controlled_intervention.py`: ランダム対照サンプリング（Condition B/D）において、介入群（map_keys）と **テンソル種別および変更パラメータ数が完全に 1:1 で一致** するサンプリングアルゴリズムを実装。
- **受入テスト**:
  - `v4/tests/test_characteristic_analyzer.py`
  - `v4/tests/test_controlled_intervention.py`: キー数、パラメータ数、モジュール種別構成の完全一致と非重複を検証。

### 【P0-05 & P1-03】E4 の Calibration 依存化と E5 の NOT_RUN 記録
- **確認された問題**: `from_calibration_map` を呼ばずに verified と表示、E5 に固定値辞書（utility=0.63, ASR=0.028 等）が存在。
- **是正内容**:
  - `v4/scripts/mergers/proposed_intervention_merge.py`: 未 calibrate の既定重みによる初期化・保存を拒否（`PRODUCTION_MERGE_REJECTED`）。
  - `from_calibration_map`: E3 実測行動地図から動的構築。安全性改善のない領域や退化領域には厳格に重み `0.0` を付与。
  - `v4/scripts/run_v4_pipeline.py`: E4 は E3 実測地図がない場合は `BLOCKED` で停止。E5 は未見 Test 評価が未実行の場合は `NOT_RUN` として記録し、架空の数値を全廃。
  - `run_all_v4.py` を `run_v4_pipeline.py` の統一ラッパーとし、チェックの回避を防止。
- **受入テスト**: `v4/tests/test_proposed_intervention_merge.py`

### 【P1-04】FP16 実重みにおけるノルム・内積オーバーフローの防止
- **確認された問題**: FP16 の 256×256 の全要素 1.0 テンソルは二乗和が 65536 となり、FP16 最大値（65504）を超えて inf になる。
- **是正内容**:
  - 全てのノルム、差分、二乗和、内積、スケーリング計算を明示的に FP32 / FP64 で実行。
  - `scale_factor = min(target_norm / current_norm, 1.0)` により縮小方向のみ適用。
- **受入テスト**: `v4/tests/test_characteristic_analyzer.py`
  - 256×256 FP16 ones テンソルの二乗和が inf にならず、厳密に finite かつ正確なノルム 256.0 を返すことを確認。

---

## 3. 回帰テストスイート実行結果

```text
======================================================================
RUNNING SECURE MERGE V4 REGRESSION TEST SUITE
======================================================================

--- Running: v4/tests/test_utility_parser.py ---
Passed: lm-eval dict extraction restored exact 0.5 score.
Passed: parsed utility score 0.383624 accurately from fixture file.
ALL UTILITY PARSER ACCEPTANCE TESTS PASSED!
[PASS] v4/tests/test_utility_parser.py passed.

--- Running: v4/tests/test_e1_selector.py ---
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s
OK
[PASS] v4/tests/test_e1_selector.py passed.

--- Running: v4/tests/test_characteristic_analyzer.py ---
..
----------------------------------------------------------------------
Ran 2 tests in 0.004s
OK
[PASS] v4/tests/test_characteristic_analyzer.py passed.

--- Running: v4/tests/test_controlled_intervention.py ---
..
----------------------------------------------------------------------
Ran 2 tests in 0.004s
OK
[PASS] v4/tests/test_controlled_intervention.py passed.

--- Running: v4/tests/test_proposed_intervention_merge.py ---
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s
OK
[PASS] v4/tests/test_proposed_intervention_merge.py passed.

>>> ALL REGRESSION TESTS PASSED! <<<
```

---

## 4. 主実験パイプライン実行結果（E0 Gate による厳格停止）

```text
$ v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py

Pipeline Track: PRIMARY
Target Results Directory: v4/results

======================================================================
STAGE E0: Integrity Audit (整合性監査)
======================================================================
[1/3] Auditing Mergers (All Methods Identity & Finite Tests)... PASSED
[2/3] Auditing Metrics Formulation & Mathematical Identities... PASSED
[3/3] Auditing Model Provenance & Tokenizer Consistency...

======================================================================
E0 MODEL INTEGRITY AUDIT RESULTS:
======================================================================
  Math Domain Verdict: UNVERIFIED
  Code Domain Verdict: UNVERIFIED

  >>> PRIMARY EXPERIMENT GATE: NO_GO <<<
  Reason: Both math and code domains failed E0 integrity audit. Concrete discrepancies detected in vocab size, RoPE scaling, and special tokens. Primary comparison and new interventions must HALT to prevent degenerative conflation. Past logs may only be analyzed under diagnostic track.
======================================================================

[FATAL AUDIT FAILURE] Primary benchmark gate is NO_GO. Halting execution.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
>>> E0 GATE VERDICT: NO_GO for Primary Experiment Pipeline <<<
Domain checkpoints exhibit architectural/tokenizer discrepancies:
  - Math/Code vocab_size: 32001 (Base: 32000)
  - Code rope_theta: 1000000 (Base: 10000), max_position_embeddings: 16384 (Base: 4096)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Execution HALTED. Primary pipeline cannot proceed with mismatched checkpoints (P0-03).
```
(Exit Code: 1 により主実験の後続実行を完全停止)
