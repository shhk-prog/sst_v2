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

---

## 5. 診断トラック実行結果（過去ログ再集計・欠測判定・依存ブロックの検証）

過去ログの健全な分析および診断のため、`--track diagnostic` を明示した場合のみ実行される診断トラックの完全実行結果です。

```text
$ v4/scripts/run_v4_pipeline.py --track diagnostic

Pipeline Track: DIAGNOSTIC
Target Results Directory: v4/results/diagnostic_track

======================================================================
STAGE E0: Integrity Audit (整合性監査)
======================================================================
  [1/3] Mergers Mathematical Audit: PASSED
  [2/3] Metrics Identities (VSR == VRR * (1 - ASR_valid)): PASSED
  [3/3] Model Provenance Audit: Math=UNVERIFIED, Code=UNVERIFIED
  >>> PRIMARY EXPERIMENT GATE: NO_GO <<<
  [DIAGNOSTIC TRACK ACTIVE] Continuing execution in diagnostic mode (outputs quarantined to diagnostic_track/).

======================================================================
STAGE E1: Baseline Re-aggregation & Constrained Selection
======================================================================
[Diagnostic Track] Scanning empirical JSON logs in v3/results...
Found 25806 result files. Binding safety and utility evaluations by normalized Candidate ID...

[Diagnostic Track Completed]:
  standard_baseline_track    -> Total Candidates: 325 | Measured BOTH Safety & Utility: 324
  exploratory_sst_track      -> Total Candidates: 564 | Measured BOTH Safety & Utility: 558
  domain_baseline_track      -> Total Candidates:   6 | Measured BOTH Safety & Utility:   0
  safety_baseline_track      -> Total Candidates:   9 | Measured BOTH Safety & Utility:   0
Summary saved to: v4/results/diagnostic_track/e1_comparison/diagnostic_reaggregation_summary.json

[E1 Rigorous Constrained Selection Summary]:
  math_mergealign          -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_led                 -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_legacy_task_arithmetic_linear_patch -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_safemerge           -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_dare                -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_della               -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_ties                -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  math_fisher              -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_dare                -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_led                 -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_legacy_task_arithmetic_linear_patch -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_mergealign          -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_safemerge           -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_fisher              -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_della               -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  code_ties                -> INSUFFICIENT_DATA (Required metrics like benign VRR or overrefusal unmeasured in raw logs)
  ... (全23グループ全てで INSUFFICIENT_DATA を判定)

>>> STAGE E1 COMPLETED <<<

======================================================================
STAGE E2: Characteristic Measurement (実重み特性測定)
======================================================================
[STAGE E2 BLOCKED] Production characteristic analysis requires --model-m and --model-u checkpoint paths.
To run regression tests on weight analysis logic, run: v3/venv_v3/bin/python v4/tests/test_characteristic_analyzer.py

======================================================================
STAGE E3: Controlled Intervention Study (統制介入実験)
======================================================================
[STAGE E3 BLOCKED] Controlled intervention requires real checkpoints via --model-u and --model-s.
To run regression tests on exact matching and norm shrinkage, run: v3/venv_v3/bin/python v4/tests/test_controlled_intervention.py

======================================================================
STAGE E4: Behavior-Intervention Guided Constrained Merge
======================================================================
[STAGE E4 BLOCKED] Empirical calibration map not provided or not found: None
Stage E4 requires empirical behavioral calibration measurements from Stage E3 (P0-05, P1-03).
Hardcoded or uncalibrated weights are rejected in production mode.

======================================================================
STAGE E5: Independent Validation & Ablation (独立検証とアブレーション)
======================================================================
Recorded E5 Status: NOT_RUN in v4/results/diagnostic_track/e5_validation/ablation_summary.json
Stage E5 will be executed once empirical candidate models and test splits are evaluated.

>>> STAGE E5 COMPLETED (STATUS: NOT_RUN) <<<
```

### 総括
- 未測定データの補完（`overrefusal=0.04` や `vrr_benign` の有害VRR流用）が完全に排除され、過去ログはすべて **`INSUFFICIENT_DATA`** として厳格に記録されました。
- 実測データが存在しない E2〜E5 は **`BLOCKED`** / **`NOT_RUN`** として明示的に停止・記録され、偽りの「実験完了」や固定辞書による優越性報告が完全に根絶されました。

---

## 4. 追加是正の実施状況 (R2-04, R2-08)

### ① R2-04: ゲート迂回防止と SafetyFT 重み実体験証
1. **単独ステージ実行時の E0 ゲート強制**:
   - `run_v4_pipeline.py --stage e1` などの個別ステージ指定時であっても、`primary` トラックでは事前に `v4/results/e0_audit/model_manifest.json` の存在と合格ステータス（`primary_experiment_verdict == "GO"`）を検証。
   - 不整合または未監査の場合は即座に **Exit 1** で実行を遮断（HALT）。
2. **Merger CLI (`merge_cli.py`) の保護**:
   - `--track primary` 実行時に `--e0_manifest` の合格確認を強制。未監査モデルのマージ実行を防止。
3. **SafetyFT の dense 復元検証分離**:
   - `audit_models.py` において、単に config/tokenizer が読めた `LOADED` 状態と、重み実体（safetensors / bin）が存在し復元が確認された `DENSE_RESTORED_VERIFIED` 状態を明確に分離。

### ② R2-08: 評価器と既存手法の実装忠実性
1. **安全評価器 (`eval_safety_v4.py`)**:
   - `judge_backend` を引数および出力レポートに明示。
   - `"harmbench_classifier"`（Hugging Face HarmBench 13B 分類器モデル）と `"keyword_heuristic"`（CI/スモークテスト用）を明示分離し、分類器不在時のサイレントな置換を禁止（例外送出）。
2. **ユーティリティ評価器 (`eval_utility_v4.py`)**:
   - 数値抽出 math 評価に加え、HumanEval / MBPP 向けのコードブロック抽出（`extract_code_block`）およびサンドボックス実行採点アダプタ（`run_code_evaluation`）を追加。
3. **既存手法の実装忠実性 (`fisher_merger.py`, `safemerge.py`, `led_merger.py`)**:
   - `FisherMerger`: `strict_fim=True` の本番モードで FIM テンソルが存在しない場合に定数平均フォールバックを拒絶しエラー化。
   - `SafeMergeMerger`, `LEDMerger`: `FIDELITY_STATUS = "SIMPLIFIED_ADAPTATION"` をクラス属性および config メタデータに明記し、公式の勾配重要度や最適化投影を伴う完全実装とは区別される旨を明示。

---

## 5. 全受入回帰テスト実行結果 (全6スイート 22テスト 100% PASS)

```bash
$ PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test

======================================================================
RUNNING SECURE MERGE V4 REGRESSION TEST SUITE
======================================================================

--- Running: v4/tests/test_e0_audit_gate.py ---
......
----------------------------------------------------------------------
Ran 6 tests in 0.003s

OK
[PASS] v4/tests/test_e0_audit_gate.py passed.
  - test_hub_id_not_classified_as_local_directory: PASS (R2-01)
  - test_positive_test_perfect_pass_manifest_allows_primary: PASS (R2-02)
  - test_unverified_model_comparison_does_not_fabricate_discrepancies: PASS (R2-03)
  - test_concrete_discrepancies_detected_when_loaded: PASS (R2-03)
  - test_fisher_rejects_missing_fim_in_strict_mode: PASS (R2-08, P0-07)
  - test_code_evaluation_extraction_and_syntax: PASS (R2-08, P0-06)

--- Running: v4/tests/test_utility_parser.py ---
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
[PASS] v4/tests/test_utility_parser.py passed.
  - test_legacy_lm_eval_dict_extraction: PASS (P0-02)
  - test_sample_len_not_extracted_as_utility: PASS (R2-06 sample_len誤読防止)
  - test_unsupported_schema_returns_none: PASS (R2-06 fallback削除)

--- Running: v4/tests/test_e1_selector.py ---
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
[PASS] v4/tests/test_e1_selector.py passed.
  - test_e1_selector_feasible: PASS
  - test_insufficient_data_candidate_rejected: PASS (P0-01 欠測除外)
  - test_nan_or_infinite_utility_rejected: PASS (P1-04 NaN除外)
  - test_selector_per_domain_and_method: PASS (R2-07 ドメイン別選定)
  - test_unmeasured_overrefusal_domain_baseline: PASS (R2-05 基準値測定要求)

--- Running: v4/tests/test_characteristic_analyzer.py ---
..
----------------------------------------------------------------------
Ran 2 tests in 0.004s

OK
[PASS] v4/tests/test_characteristic_analyzer.py passed.
  - test_fp16_norm_overflow_prevention: PASS (P1-04 FP32計算)
  - test_zero_or_identical_models: PASS

--- Running: v4/tests/test_controlled_intervention.py ---
...
----------------------------------------------------------------------
Ran 3 tests in 0.011s

OK
[PASS] v4/tests/test_controlled_intervention.py passed.
  - test_random_control_parameter_and_shape_match: PASS (P1-02 等パラメータ対照)
  - test_bidirectional_norm_shrinkage: PASS (P1-02 双方向ノルム縮小)
  - test_all_condition_names_dispatch: PASS (R2-09 条件名バグ修正)

--- Running: v4/tests/test_proposed_intervention_merge.py ---
...
----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
[PASS] v4/tests/test_proposed_intervention_merge.py passed.
  - test_uncalibrated_merge_blocked: PASS (P0-05 未calibrate拒絶)
  - test_empty_or_zero_measurements_blocked: PASS (R2-09 空地図 BLOCKED)
  - test_dynamic_weight_assignment_and_group_norm_scaling: PASS (P1-03 群別上限スケーリング)

>>> ALL REGRESSION TESTS PASSED! <<<
```

