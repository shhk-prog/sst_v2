# 修正内容の確認 (Walkthrough): 必須benchmark個別指標のnull拒否検査の復元 (R7)

## 1. 修正概要と指示書対照表

コミット `8fe3ddc45660f94e1ca5318f4e8cc0e66c65bfb3` に対する修正指示書に基づき、必須 benchmark の個別指標欠測拒否チェックを復元しました。

| 項目 | 指示書の指摘事項 | 是正内容 | 検証結果 |
| :--- | :--- | :--- | :--- |
| **A: HarmBench Template** | Standard/Contextual の 7 規則化、公式 fixture 照合。 | 受入確認済み（維持）。 | `verify_harmbench_reference.py` 実行で終了コード 0 を確認 |
| **B: 件数検査** | `validate_benchmark_counts` による厳格な整数型・範囲・0 件要求。 | 受入確認済み（維持）。 | 欠測・NaN/Inf・負数・小数の拒否を維持 |
| **C: コード実行停止（方針A）** | `execute_code=True` はモデル読込前に無条件拒否。 | 受入確認済み（維持）。 | 変更なし |
| **残件: 必須指標の null 拒否** | 件数検査への置換時に個別指標（`asr_all`, `asr_valid`, `vrr`）の null 検査が削除され、件数が揃っていれば指標欠測でも通過していた。 | `evaluate_feasible_region_strict` 内の必須 benchmark ループに、3 指標の `None` および `is_valid_ratio` 検査を復元。 | 追加回帰テスト `test_e1_required_metric_regression.py` を実行し、全テスト PASS を確認 |
| **主実験ゲート判定** | モデル適合性による NO_GO の厳格維持。 | E0 ゲート停止による `NO_GO` を厳格に維持。 | Primary Track にて E0 不整合により安全に停止（`NO_GO`） |

---

## 2. 修正差分

- **対象ファイル**: [v4/scripts/analysis/e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py)

```diff
--- a/v4/scripts/analysis/e1_selector.py
+++ b/v4/scripts/analysis/e1_selector.py
@@ -179,14 +179,21 @@ def evaluate_feasible_region_strict(
             if not isinstance(rb_data, dict):
                 return "INSUFFICIENT_DATA", f"UNSUPPORTED_BENCHMARK_SCHEMA_{rb.upper()}_SCALAR_NOT_ALLOWED"
 
-            rb_asr = rb_data.get("asr_all")
-            rb_valid = rb_data.get("asr_valid")
-            rb_vrr = rb_data.get("vrr")
             # Strict count check: exact integer, positive n_samples, 0 <= n_unjudged <= n_samples, zero unjudged
             valid_counts, count_err = validate_benchmark_counts(rb_data, rb)
             if not valid_counts:
                 return "INSUFFICIENT_DATA", count_err
 
+            # Require both valid counts and complete per-benchmark metrics.
+            for metric_name in ("asr_all", "asr_valid", "vrr"):
+                value = rb_data.get(metric_name)
+                if value is None or not is_valid_ratio(value):
+                    return (
+                        "INSUFFICIENT_DATA",
+                        f"NULL_OR_INVALID_REQUIRED_BENCHMARK_"
+                        f"{rb.upper()}_{metric_name.upper()}",
+                    )
+
     if isinstance(bench_breakdown, dict):
         for b_name, b_val in bench_breakdown.items():
             if not isinstance(b_val, dict):
```

---

## 3. 追加回帰テスト (`test_e1_required_metric_regression.py`) の結果

指示書同梱のテストスクリプト [test_e1_required_metric_regression.py](file:///mnt/nas/home/hiromi/src/sst_v2/test_e1_required_metric_regression.py) をリポジトリ直下に配置し、修正前後の挙動を確認しました。

### 修正前の実行結果（回帰不具合の再現）:
```text
Ran 7 tests in 0.005s
FAILED (failures=27)
```
個別指標が null / 欠落しているにもかかわらず `FEASIBLE` と判定されていたこと、および `select_best` や `sensitivity` で誤選定され得ることが 27 件の Failure として再現されました。

### 修正後の実行結果:
```bash
v3/venv_v3/bin/python test_e1_required_metric_regression.py --repo-root .
```
```text
Testing actual selector: /mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py
test_complete_candidate_remains_feasible (__main__.RequiredMetricRegression.test_complete_candidate_remains_feasible) ... ok
test_count_validation_is_preserved (__main__.RequiredMetricRegression.test_count_validation_is_preserved) ... ok
test_counts_alone_do_not_establish_complete_measurement (__main__.RequiredMetricRegression.test_counts_alone_do_not_establish_complete_measurement) ... ok
test_each_required_metric_rejects_null_and_absence (__main__.RequiredMetricRegression.test_each_required_metric_rejects_null_and_absence) ... ok
test_nonfinite_or_out_of_range_metric_is_rejected (__main__.RequiredMetricRegression.test_nonfinite_or_out_of_range_metric_is_rejected) ... ok
test_select_best_cannot_select_null_metric_candidate (__main__.RequiredMetricRegression.test_select_best_cannot_select_null_metric_candidate) ... ok
test_sensitivity_cannot_count_null_metric_candidate (__main__.RequiredMetricRegression.test_sensitivity_cannot_count_null_metric_candidate) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.003s

OK
```
**判定: 全 7 テストすべて OK（終了コード 0）**

---

## 4. 全回帰テストスイートの実行結果

```bash
PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test
```
```text
Ran 18 tests in 2.718s
OK
[PASS] v4/tests/test_e0_audit_gate.py passed.
[PASS] v4/tests/test_utility_parser.py passed.
[PASS] v4/tests/test_e1_selector.py passed.
[PASS] v4/tests/test_characteristic_analyzer.py passed.
[PASS] v4/tests/test_controlled_intervention.py passed.
[PASS] v4/tests/test_proposed_intervention_merge.py passed.

>>> ALL REGRESSION TESTS PASSED! <<<
```
全 6 テストスイート（37 件のテスト）がすべて **PASS** しました。

---

## 5. 公式テンプレート照合スクリプト (`verify_harmbench_reference.py`) の結果

```bash
v3/venv_v3/bin/python verify_harmbench_reference.py --repo-root .
```
```json
{
  "reference_url": "https://raw.githubusercontent.com/centerforaisafety/HarmBench/37150ed7d07f1db7639c9e3cfee3288391482503/eval_utils.py",
  "reference_revision": "37150ed7d07f1db7639c9e3cfee3288391482503",
  "reference_source_sha256": "46f1db751866848834d45d5128a18d4cc0a820828e89796ab51bc605d10c7058",
  "retrieval": "downloaded from pinned official URL",
  "local_source_path": "/mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_safety_v4.py",
  "local_source_sha256": "28c866414970d3f5707b4a927ea980bcb793a6cd325f863cb7e58a5385700946",
  "scope": "Literal templates only; no model or complete pipeline execution",
  "checks": [
    {
      "name": "HARMBENCH_LLAMA2_CLS_PROMPT",
      "equal": true,
      "local_characters": 1359,
      "official_characters": 1359,
      "local_sha256": "788f4f6aa1491c433c4da76c9140cfc30966cea3ff3875c4d0fcb336d92f60e0",
      "official_sha256": "788f4f6aa1491c433c4da76c9140cfc30966cea3ff3875c4d0fcb336d92f60e0"
    },
    {
      "name": "HARMBENCH_LLAMA2_CLS_PROMPT_CONTEXTUAL",
      "equal": true,
      "local_characters": 1401,
      "official_characters": 1401,
      "local_sha256": "5d6bb9e3cf4d1e5f3f7620093113222ee115af75b0b2913f00e4c7225ec9f219",
      "official_sha256": "5d6bb9e3cf4d1e5f3f7620093113222ee115af75b0b2913f00e4c7225ec9f219"
    },
    {
      "name": "OFFICIAL_STANDARD_FIXTURE",
      "equal": true,
      "local_characters": 1359,
      "official_characters": 1359,
      "local_sha256": "788f4f6aa1491c433c4da76c9140cfc30966cea3ff3875c4d0fcb336d92f60e0",
      "official_sha256": "788f4f6aa1491c433c4da76c9140cfc30966cea3ff3875c4d0fcb336d92f60e0"
    }
  ]
}
```
**判定: 全 3 項目完全一致、終了コード 0**

---

## 6. 主実験トラック (Primary Track) の E0 ゲート停止結果

```bash
PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py
```
```text
Pipeline Track: PRIMARY
Target Results Directory: v4/results

======================================================================
STAGE E0: Integrity Audit (整合性監査)
======================================================================
[1/3] Auditing Mergers (All Methods Identity & Finite Tests)...
ALL RIGOROUS E0 MERGER MATHEMATICAL AUDITS PASSED SUCCESSFULLY!

[2/3] Auditing Metrics Formulation & Mathematical Identities...
ALL E0 METRICS MATHEMATICAL IDENTITY TESTS PASSED!

[3/3] Auditing Model Provenance & Tokenizer Consistency...
Auditing [base]: meta-llama/Llama-2-7b-hf
Auditing [math_domain]: WizardLMTeam/WizardMath-7B-V1.0
Auditing [code_domain]: vanillaOVO/WizardCoder-Python-7B-V1.0
...
======================================================================
E0 MODEL INTEGRITY AUDIT RESULTS:
======================================================================
  Math Domain Verdict: FAIL (Compatible: False)
    Discrepancies:
      - config.max_position_embeddings: {'base': 4096, 'domain': 2048}
      - tokenizer.vocab_size: {'base': 32000, 'domain': 32001, 'note': 'Vocab expanded (e.g. [PAD] token added to index 32000)'}
  Code Domain Verdict: FAIL (Compatible: False)
    Discrepancies:
      - config.max_position_embeddings: {'base': 4096, 'domain': 16384}
      - config.rope_scaling.rope_theta: {'base': 10000.0, 'domain_scaling': 1000000}
      - tokenizer.vocab_size: {'base': 32000, 'domain': 32001, 'note': 'Vocab expanded (e.g. [PAD] token added to index 32000)'}
      - tokenizer.bos_token_id: {'base': 1, 'domain': 2}

  >>> PRIMARY EXPERIMENT GATE: NO_GO <<<
  Overall Verdict: FAIL
  Reason: Primary gate NO_GO: Math domain failed compatibility...; Code domain failed compatibility...
======================================================================
[FATAL AUDIT FAILURE] Primary benchmark gate is NO_GO. Halting execution.
```
**判定: 実モデルの不整合を正確に検出し、主実験を安全に停止（NO_GO 維持）**
