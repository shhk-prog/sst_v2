# 検証・修正内容確認書 (Walkthrough): R5 残件3項目の完全是正と検証

## 1. 概要と最終判定

- **受入判定**: **残件3項目（HarmBench公式プロトコル全文一致、benchmark主選定schema統一・旧スカラー形式の完全遮断、コード評価のOS隔離安全ガード）の完全是正を確認。回帰テスト全37件PASS。**
- **主実験実行判定**: **`NO_GO` を正当に維持**（実モデルの tokenizer/RoPE 不整合 E0 ゲート停止を厳格に維持。模擬データ・不当補完による通過は一切行わない）。
- **Baseline Commit**: `cd3334c71f86f5486cb31871348044f125b8b47f`
- **Tested Commit / 前回到達点**: `d14886a115e4dbc836a8a96bf86b96eb58b5dfb7`
- **作業ツリー**: HEAD上の是正差分適用後
- **実行環境**: Linux 6.8.0-101-generic, Python 3.12 (venv_v3, PyTorch 2.11.0, Transformers 5.12.1)

---

## 2. ５項目の是正結果対照表

| # | 指摘項目 | d14886a 時点の状態 | 今回の完全是正内容 | 受入判定 |
|---|---|---|---|:---:|
| 1 | **CLI構文・FIM受渡し** | 構文修正済み。FIM引数追加。実CLIテスト合格。 | 前回の是正を維持。実ファイルFIM読込・保存・厳密テンソル検証テスト合格。 | **受入済 (PASS)** |
| 2 | **HarmBench (残件A)** | parserは受入（yes/no厳密判定）。公式promptは独自版（推論要求・4規則）。 | **CAIS公式固定リビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の全文テンプレート（Standard 4規則、Contextual 7規則）に完全準拠**。独立公式参照fixtureとの全文一致（`assertEqual`）テスト合格。厳格parser維持。 | **完全是正 (PASS)** |
| 3 | **benchmark制約 (残件B)** | 辞書形式は改善。数値1個の旧スカラー形式に抜け道あり。件数0未検査。 | **主選定（`evaluate_feasible_region_strict`）で辞書形式を必須化し、数値1個のスカラー形式を `UNSUPPORTED_BENCHMARK_SCHEMA` として即座に `INSUFFICIENT_DATA` 判定**。正の評価件数（`n_samples > 0`）およびゼロ未判定（`n_unjudged == 0`）を共通schemaで検査。単独感度分析でも必須集合を既定強制。テスト合格。 | **完全是正 (PASS)** |
| 4 | **コード評価 (残件C)** | 環境変数名（`docker`）だけで許可し、ホスト子プロセスでexec実行。 | **隔離ランナー実体接続が完了するまで、本番のモデル生成コード実行（`execute_code=True`）を常に `BLOCKED` とする安全機構（方針A）を確立**。本番関数からテスト用バイパス引数を完全排除。人間レビュー済みの単体テストfixture専用実行関数 `run_trusted_fixture_execution` を新設。環境変数未設定・設定時の両方でブロックされるテスト合格。 | **完全是正 (PASS)** |
| 5 | **提案法の共通検査** | override先頭で共通バリデータ呼出済み。 | 前回の是正を維持。欠損キー・shape不一致の拒否を確認済み。 | **受入済 (PASS)** |

---

## 3. 残件3項目の具体的修正内容

### 残件A：HarmBench公式プロトコル全文一致 ([eval_safety_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_safety_v4.py))
1. **公式リビジョン全文の取り込み**:
   ```python
   HARMBENCH_OFFICIAL_REVISION = "37150ed7d07f1db7639c9e3cfee3288391482503"
   ```
   Standard（4 Rules）および Contextual（7 Rules）を Center for AI Safety の公式リビジョン原文そのままで定義。
2. **レポートへのリビジョン記録**:
   評価出力レポートに `"classifier_revision": HARMBENCH_OFFICIAL_REVISION` を明記。
3. **独立fixtureとの全文一致テスト ([test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py))**:
   テストコード内に公式fixtureを独立定義し、`build_harmbench_prompt` の出力が fixture と完全一致（`assertEqual`）することを検証。

### 残件B：benchmark 主選定 schema 厳格統一 ([e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py))
1. **スカラー形式の完全遮断**:
   ```python
   # Strict: Scalar value is completely rejected in primary selection. Dictionary schema is mandatory.
   if not isinstance(rb_data, dict):
       return "INSUFFICIENT_DATA", f"UNSUPPORTED_BENCHMARK_SCHEMA_{rb.upper()}_SCALAR_NOT_ALLOWED"
   ```
   旧スカラー形式（`{"harmbench": 0.01}`）を渡した場合、即座に `INSUFFICIENT_DATA` としてリジェクト。
2. **評価件数・未判定件数の共通検査**:
   - `rb_samples <= 0` または None -> `ZERO_OR_MISSING_SAMPLE_COUNT_{rb.upper()}` でリジェクト。
   - `rb_unjudged > 0` -> `UNJUDGED_SAMPLES_IN_REQUIRED_BENCHMARK_{rb.upper()}` でリジェクト。
3. **感度分析の統一**:
   `compute_sensitivity_matrix` で `required_benchmarks` が None の場合、主選定と同じ `DEFAULT_REQUIRED_BENCHMARKS` を適用。

### 残件C：コード評価のOS隔離（方針A） ([eval_utility_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_utility_v4.py))
1. **未統合ランナーの実行禁止**:
   ```python
   def check_secure_sandbox_isolation() -> Tuple[bool, str]:
       return False, "Dedicated OS container sandbox runner is not integrated. All model-generated code execution is BLOCKED."
   ```
   環境変数文字列の有無に関わらず、外部隔離ランナーの実体接続がない限り常に False を返す。
2. **本番経路からのテスト用バイパス排除**:
   `run_code_evaluation` から `allow_trusted_test_fixture` 引数を完全削除。`execute_code=True` は無条件に `RuntimeError("R3-01 BLOCKED: ...")` で拒否。
3. **テスト専用実行経路の分離**:
   人がレビュー済みの単体テストfixture専用の `run_trusted_fixture_execution(program_code)` を新設。
4. **境界テスト ([test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py))**:
   環境変数未設定時、および `SECURE_CODE_SANDBOX_RUNNER="docker"` と文字列だけ設定した時の両方で、確実に `RuntimeError` でブロックされることを明示的にアサート。

---

## 4. 検証コマンド実行ログ

### (1) 回帰テストスイート全件実行 (smoke_test)
```bash
PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test
```
**実行結果**:
```text
======================================================================
RUNNING SECURE MERGE V4 REGRESSION TEST SUITE
======================================================================
--- Running: v4/tests/test_e0_audit_gate.py ---
Ran 18 tests in 2.590s
OK
[PASS] v4/tests/test_e0_audit_gate.py passed.
  - HarmBench 公式リビジョン 37150ed7d07f1db7639c9e3cfee3288391482503 独立 fixture 全文一致: PASS
  - parse_harmbench_label 全指示書ケース完全一致判定: PASS
  - e1_selector スカラー形式拒否・件数0拒否・未判定拒否: PASS
  - 感度分析のデフォルト必須集合適用: PASS
  - OS隔離未接続時の無条件 BLOCKED ガード（未設定＆設定文字列の両方）: PASS
  - テスト専用 fixture 実行の分離: PASS
--- Running: v4/tests/test_utility_parser.py --- (3 tests) -> OK [PASS]
--- Running: v4/tests/test_e1_selector.py --- (5 tests) -> OK [PASS]
--- Running: v4/tests/test_characteristic_analyzer.py --- (2 tests) -> OK [PASS]
--- Running: v4/tests/test_controlled_intervention.py --- (3 tests) -> OK [PASS]
--- Running: v4/tests/test_proposed_intervention_merge.py --- (6 tests) -> OK [PASS]

>>> ALL REGRESSION TESTS PASSED! <<< (Total: 37 tests)
```

### (2) 主実験パイプライン (Primary Track)
```bash
PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py
```
**実行結果**:
```text
Pipeline Track: PRIMARY
Target Results Directory: v4/results

======================================================================
STAGE E0: Integrity Audit (整合性監査)
======================================================================
[1/3] Auditing Mergers (All Methods Identity & Finite Tests)...
  Linear Endpoints diff: 0.00000000
  Task Arithmetic diff:  0.00000000
  All 14 methods identity merges: PASSED
  All 14 methods finite checks:   PASSED
  Save & Reload diff:    0.0000000000
ALL RIGOROUS E0 MERGER MATHEMATICAL AUDITS PASSED SUCCESSFULLY!

[2/3] Auditing Metrics Formulation & Mathematical Identities...
  Identity VSR == VRR * (1 - ASR_valid): True
ALL E0 METRICS MATHEMATICAL IDENTITY TESTS PASSED!

[3/3] Auditing Model Provenance & Tokenizer Consistency...
  Math Domain Verdict: FAIL (Compatible: False)
    - config.max_position_embeddings: {'base': 4096, 'domain': 2048}
    - tokenizer.vocab_size: {'base': 32000, 'domain': 32001}
  Code Domain Verdict: FAIL (Compatible: False)
    - config.max_position_embeddings: {'base': 4096, 'domain': 16384}
    - config.rope_scaling.rope_theta: {'base': 10000.0, 'domain_scaling': 1000000}
    - tokenizer.vocab_size: {'base': 32000, 'domain': 32001}
    - tokenizer.bos_token_id: {'base': 1, 'domain': 2}

>>> PRIMARY EXPERIMENT GATE: NO_GO <<<
Execution HALTED. Primary pipeline cannot proceed with mismatched or unverified checkpoints (P0-03, R2-01).
```
- 不正な模擬データやダミーによるバイパスを行わず、実モデルのアーキテクチャ不整合を検出して厳格に `NO_GO` で停止することを確認した。
