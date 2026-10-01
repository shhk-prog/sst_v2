# 修正内容の確認 (Walkthrough): HarmBench公式template完全一致照合および件数厳格検査の是正 (R6)

## 1. 修正概要と指示書対照表

コミット `fb457ce4e49bacfb6830d9c97923fbd6f1076ba4` に対する残存修正指示書に基づき、以下の通り是正を完了しました。

| 項目 | 指示書の指摘事項 | 是正内容 | 検証結果 |
| :--- | :--- | :--- | :--- |
| **A: HarmBench Template** | Standardが4規則で公式（7規則）と不一致。テスト期待値も非公式版の手書き。 | `verify_harmbench_reference.py` を配備。公式リポジトリ（rev `37150ed7`）のASTから辞書定数を抽出し `harmbench_official.json` を生成。`eval_safety_v4.py` の `HARMBENCH_LLAMA2_CLS_PROMPT` を公式7規則（1359文字）に全文一致修正。 | `verify_harmbench_reference.py` 実行で Standard / Contextual / Fixture 全て `equal: true`、終了コード0 |
| **B: benchmark件数検査** | `n_unjudged` の欠測を0に補完していた。また `isinstance` と大小比較では NaN/Inf や負数、bool 値を排除できない。 | `validate_benchmark_counts` を実装。`type(...) is int` による厳格型検査を実施。欠測補完を撤廃し、`n_samples > 0`、`0 <= n_unjudged <= n_samples`、主選定 `n_unjudged == 0` を要求。 | 欠測・NaN/Inf・負数・小数の全パターンが `INSUFFICIENT_DATA` として即座に拒否されることをユニットテストで確認 |
| **C: コード実行停止（方針A）** | `execute_code=True` はモデル読込前に無条件拒否。 | 方針Aの受入条件を維持。変更不要。 | 変更なし（受入済み） |
| **主実験ゲート判定** | モデル適合性による NO_GO の厳格維持。 | E0 ゲート停止による `NO_GO` を厳格に維持。 | `run_v4_pipeline.py`（Primary）にて E0 不整合（max_position_embeddings, vocab_size 等）により `NO_GO` で安全停止 |

---

## 2. 修正詳細

### 2.1 HarmBench公式リビジョンとの機械的照合
- **参照元**: CAIS公式 HarmBench 固定リビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の `eval_utils.py`
- **スクリプト**: [verify_harmbench_reference.py](file:///mnt/nas/home/hiromi/src/sst_v2/verify_harmbench_reference.py)
- **抽出fixture**: [v4/tests/fixtures/harmbench_official.json](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/fixtures/harmbench_official.json)
- **修正ファイル**: [v4/scripts/eval/eval_safety_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_safety_v4.py)
- **テストファイル**: [v4/tests/test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py)

#### `verify_harmbench_reference.py` 実行結果:
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
**判定: 全3項目完全一致、終了コード 0**

---

### 2.2 件数・未判定数の厳格検査（欠測補完の撤廃）
- **対象ファイル**: [v4/scripts/analysis/e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py)

#### 実装内容:
```python
def validate_benchmark_counts(metrics: Dict[str, Any], label: str) -> Tuple[bool, Optional[str]]:
    """
    R5 Directive: Strictly validates sample counts and unjudged counts:
    - Counts must be exact JSON integers (type is int, rejecting bool, float, NaN, Inf, None).
    - n_samples > 0.
    - 0 <= n_unjudged <= n_samples.
    - For primary selection: n_unjudged must be exactly 0 (unjudged samples are not tolerated).
    """
    n = metrics.get("n_samples")
    if n is None:
        n = metrics.get("n_total")
    if n is None:
        n = metrics.get("sample_len")
    if n is None:
        n = metrics.get("n")

    # type is int rejects bool (in Python, isinstance(True, int) is True, but type(True) is bool)
    if type(n) is not int or n <= 0:
        return False, f"INVALID_SAMPLE_COUNT_{label.upper()}"

    u = metrics.get("n_unjudged")
    if type(u) is not int or not (0 <= u <= n):
        return False, f"INVALID_UNJUDGED_COUNT_{label.upper()}"

    if u != 0:
        return False, f"UNJUDGED_SAMPLES_{label.upper()}({u}/{n})"

    return True, None
```

#### 合成入力による分岐再現結果:
| 入力条件 | 旧判定 | 指示書の期待値 | 修正後の判定 | 判定理由 |
| :--- | :--- | :--- | :--- | :--- |
| 正常な件数（n_samples=100, n_unjudged=0） | FEASIBLE | FEASIBLE | **FEASIBLE** | 条件を満たすため適格 |
| スカラー形式 | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **INSUFFICIENT_DATA** | UNSUPPORTED_BENCHMARK_SCHEMA |
| n_samples = 0 / 欠測 | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **INSUFFICIENT_DATA** | INVALID_SAMPLE_COUNT |
| n_unjudged = 1 | INSUFFICIENT_DATA | INSUFFICIENT_DATA | **INSUFFICIENT_DATA** | UNJUDGED_SAMPLES |
| **n_unjudged が欠測** | **FEASIBLE** (0補完) | **INSUFFICIENT_DATA** | **INSUFFICIENT_DATA** | **INVALID_UNJUDGED_COUNT** |
| **n_samples = NaN / Inf** | **FEASIBLE** | **INSUFFICIENT_DATA** | **INSUFFICIENT_DATA** | **INVALID_SAMPLE_COUNT** |
| **n_unjudged = -1 / NaN** | **FEASIBLE** | **INSUFFICIENT_DATA** | **INSUFFICIENT_DATA** | **INVALID_UNJUDGED_COUNT** |

---

## 3. 回帰テスト・スモークテスト結果

全 6 テストスイート（37 件のテスト）を実行し、すべて **PASS** することを確認しました。

```text
Ran 18 tests in 2.651s
OK
[PASS] v4/tests/test_e0_audit_gate.py passed.

--- Running: v4/tests/test_utility_parser.py ---
Ran 3 tests in 0.000s
OK
[PASS] v4/tests/test_utility_parser.py passed.

--- Running: v4/tests/test_e1_selector.py ---
Ran 5 tests in 0.000s
OK
[PASS] v4/tests/test_e1_selector.py passed.

--- Running: v4/tests/test_characteristic_analyzer.py ---
Ran 2 tests in 0.004s
OK
[PASS] v4/tests/test_characteristic_analyzer.py passed.

--- Running: v4/tests/test_controlled_intervention.py ---
Ran 3 tests in 0.011s
OK
[PASS] v4/tests/test_controlled_intervention.py passed.

--- Running: v4/tests/test_proposed_intervention_merge.py ---
Ran 6 tests in 0.002s
OK
[PASS] v4/tests/test_proposed_intervention_merge.py passed.

>>> ALL REGRESSION TESTS PASSED! <<<
```

---

## 4. 主実験パイプライン (Primary Track) の実行結果

主実験パイプライン [v4/scripts/run_v4_pipeline.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/run_v4_pipeline.py) を実行し、E0 ゲート停止（`NO_GO`）が正常に機能していることを確認しました。

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
Auditing [safety_lora_seed42]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/safety_lora_seed42
Auditing [safety_full_seed42]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed42
Auditing [safety_lora_seed43]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/safety_lora_seed43
Auditing [safety_full_seed43]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed43
Auditing [safety_lora_seed44]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/safety_lora_seed44
Auditing [safety_full_seed44]: /mnt/nas/home/hiromi/src/sst_v2/v3/models/temp_safety_full_seed44

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
  Reason: Primary gate NO_GO: Math domain failed compatibility: config.max_position_embeddings, tokenizer.vocab_size; Code domain failed compatibility: config.max_position_embeddings, config.rope_scaling.rope_theta, tokenizer.vocab_size, tokenizer.bos_token_id
======================================================================

[FATAL AUDIT FAILURE] Primary benchmark gate is NO_GO. Halting execution.
```

**結論**: 実モデルの構成不整合が正しく検出され、後続ステージへの進行が安全に遮断されています。
