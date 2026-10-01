# 実装計画書: R5 残件3項目の完全是正とスキーマ統一

## 1. 背景と監査指摘事項
コミット `d14886a115e4dbc836a8a96bf86b96eb58b5dfb7` においてラベル解析や必須benchmark接続が改善されたものの、以下の3点について残件が指摘された：
1. **残件A (HarmBench公式プロトコル全文一致)**:
   プロンプトに独自の理由説明指示や4規則が残っており、CAIS公式固定リビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の指示・7規則と不一致。単に「Rulesが含まれる」だけでなく、独立した公式参照fixtureとの全文一致テストが必要。
2. **残件B (benchmark主選定schema統一)**:
   辞書形式の検査は追加されたが、数値1個のスカラー形式（例: `{"harmbench": 0.01}`）を受理してしまい、ASR_valid / VRR を迂回して FEASIBLE になる抜け道が残存。また評価件数0のチェック欠落や、単独感度分析での必須集合未適用。
3. **残件C (コード評価のOS隔離ガード)**:
   `SECURE_CODE_SANDBOX_RUNNER="docker"` 等の環境変数文字列だけで隔離OKと判定し、実体ランナー未接続のままホストexecに委譲していた。本番モデル生成コードの実行を常に BLOCKED とし、テスト用fixtureは専用経路へ完全分離することが必要。

---

## 2. 是正設計方針

### 2.1 HarmBench公式プロトコル全文準拠 ([eval_safety_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_safety_v4.py))
- **公式固定リビジョン**: `37150ed7d07f1db7639c9e3cfee3288391482503`
- **Standard プロンプト**: 公式 README / `eval_utils.py` の Standard 4規則全文を完全一致で定義。
- **Contextual プロンプト**: 公式 Contextual 7規則全文を完全一致で定義。
- **リビジョン記録**: 評価出力レポートに `"classifier_revision": HARMBENCH_OFFICIAL_REVISION` を明記。
- **検証テスト ([test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py))**: テストコード内に独立した公式参照 fixture を定義し、`build_harmbench_prompt` の出力が fixture と完全一致（`assertEqual`）することを検証。

### 2.2 benchmark 主選定 schema 厳格統一 ([e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py))
- **スカラー形式の完全拒否**:
  `evaluate_feasible_region_strict` において、`bench_breakdown` 内の各 benchmark 値が辞書型（`isinstance(val, dict)`）でない場合、即座に `status = "INSUFFICIENT_DATA"`, `reason = f"UNSUPPORTED_BENCHMARK_SCHEMA_{b_name.upper()}_SCALAR_NOT_ALLOWED"` としてリジェクト。
- **正の評価件数チェック**:
  `n_samples`（または `sample_len`, `n_total`, `n`）が None、非数値、または `<= 0` の場合、`"ZERO_OR_MISSING_SAMPLE_COUNT_{b_name.upper()}"` として `INSUFFICIENT_DATA`。
- **未判定件数チェック**:
  `n_unjudged > 0` の場合、`"UNJUDGED_SAMPLES_IN_REQUIRED_BENCHMARK_{b_name.upper()}"` として `INSUFFICIENT_DATA`。
- **単独感度分析の統一**:
  `compute_sensitivity_matrix` の冒頭で `if required_benchmarks is None: required_benchmarks = DEFAULT_REQUIRED_BENCHMARKS` を強制。

### 2.3 コード評価のOS隔離ガード（方針A） ([eval_utility_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_utility_v4.py))
- **未統合ランナーの実行禁止**:
  `check_secure_sandbox_isolation()` は、環境変数文字列の有無に関わらず、外部隔離ランナーの実体接続がない限り常に `(False, "Dedicated OS container sandbox runner is not integrated. All model-generated code execution is BLOCKED.")` を返す。
- **本番経路からのテスト用バイパス排除**:
  `run_code_evaluation` から `allow_trusted_test_fixture` 引数を完全削除。`execute_code=True` で呼び出された場合は無条件に `RuntimeError("R3-01 BLOCKED: ...")` を投げて実行を阻止。
- **テスト専用実行経路の新設**:
  人がレビュー済みの単体テスト用 fixture 実行関数 `run_trusted_fixture_execution(program_code: str, timeout: float = 3.0)` を新設。本番のモデル生成パイプラインから完全に分離する。
- **テストでの境界検証 ([test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py))**:
  環境変数未設定時、および `SECURE_CODE_SANDBOX_RUNNER="docker"` と文字列だけ設定した時の両方で、`check_secure_sandbox_isolation()` が False かつ `run_code_evaluation(execute_code=True)` がブロックされることを明示的にアサート。
