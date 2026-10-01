# Task: HarmBench公式template完全一致照合および件数厳格検査の是正 (R6)

## 概要
コミット `fb457ce4e49bacfb6830d9c97923fbd6f1076ba4` において、方針A（コード実行停止）の受入が確定した。
残る2つの是正指示：
1. **HarmBench Standard Template の公式完全一致照合**:
   - 公式CAISリビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の `eval_utils.py` 内 `LLAMA2_CLS_PROMPT["prompt"]` は4規則ではなく7規則。
   - `verify_harmbench_reference.py` を配備し、公式リポジトリから取得したASTリテラルと全文一致を検査、公式fixture `v4/tests/fixtures/harmbench_official.json` を保存・照合する。
2. **Benchmark件数・未判定数の厳格検査**:
   - `n_unjudged` の欠測を0に補完する処理（`get("n_unjudged", 0)`）を完全撤廃。
   - 件数（`n_samples`）および未判定件数（`n_unjudged`）を厳格なJSON整数（`type(...) is int`）として検証。
   - `n_samples > 0`、`0 <= n_unjudged <= n_samples`、主選定では `n_unjudged == 0` を要求し、欠測・NaN・Inf・負数・小数を即座に `INSUFFICIENT_DATA` として拒否。
3. **主実験ゲート判定の維持**:
   - 実モデル tokenizer/RoPE 不整合による E0 ゲート停止（`NO_GO`）を正当に維持。

## タスクリスト
- [x] 公式照合スクリプト `verify_harmbench_reference.py` の配備および公式fixture `v4/tests/fixtures/harmbench_official.json` の抽出・保存
- [x] `v4/scripts/eval/eval_safety_v4.py` の `HARMBENCH_LLAMA2_CLS_PROMPT` を公式7規則テキスト（1359文字）に修正
- [x] `verify_harmbench_reference.py` による全文一致（Standard / Contextual / Fixture）検証（終了コード0）
- [x] `v4/scripts/analysis/e1_selector.py` の `validate_benchmark_counts` 実装と `n_unjudged` 欠測補完の撤廃
- [x] `v4/tests/test_e0_audit_gate.py` および `v4/tests/test_e1_selector.py` のユニットテスト更新
- [x] スモークテスト・回帰テスト全スイート（37件）のPASS確認
- [x] 主実験パイプライン（Primary Track）の E0 ゲート停止（`NO_GO`）確認
- [x] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の作成と報告
