# 実装計画書: HarmBench公式template完全一致照合および件数厳格検査の是正 (R6)

## 1. 背景と監査指示
コミット `fb457ce4e49bacfb6830d9c97923fbd6f1076ba4` において、方針A（コード実行停止）の受入が確定した。
残る2つの是正指示について、以下の通り是正を実施する：

1. **HarmBench Standard Template の公式完全一致照合**:
   - 公式CAISリビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の `eval_utils.py` では `LLAMA2_CLS_PROMPT["prompt"]` は4規則ではなく7規則。
   - 見出しは `[BEHAVIOR]:` / `[GENERATION]:`。
   - `verify_harmbench_reference.py` を配備し、外部Pythonを実行せずにAST解析によって公式リテラルを抽出。`v4/tests/fixtures/harmbench_official.json` へ書き出す。
   - `v4/scripts/eval/eval_safety_v4.py` 内の `HARMBENCH_LLAMA2_CLS_PROMPT` を公式7規則テキストへ更新し、空白も含めて完全一致させる。
   - `v4/tests/test_e0_audit_gate.py` 内の `OFFICIAL_STANDARD_FIXTURE` も公式リテラルへ更新し、 fixture JSON との照合を追加。

2. **Benchmark件数・未判定数の厳格検査**:
   - `v4/scripts/analysis/e1_selector.py` 内で `rb_unjudged = rb_data.get("n_unjudged", 0)` と未判定件数を0に補完していた処理を完全撤廃。
   - 新規に関数 `validate_benchmark_counts(metrics, label)` を導入。
   - `type(n) is not int or n <= 0` の場合は `INVALID_SAMPLE_COUNT_{label.upper()}` を返却（bool値やNaN/Inf、小数、0件、欠測を即座に排除）。
   - `type(u) is not int or not (0 <= u <= n)` の場合は `INVALID_UNJUDGED_COUNT_{label.upper()}` を返却（未判定数の欠測、負数、NaN/Inf、小数を即座に排除）。
   - 主選定において `u != 0` の場合は `UNJUDGED_SAMPLES_{label.upper()}` を返却。
   - 必須benchmarkおよび全benchmarkに対して本検査を適用。

3. **主実験ゲート判定の維持**:
   - 実モデル tokenizer/RoPE 不整合による E0 ゲート停止（`NO_GO`）を正当に維持。

## 2. 変更対象ファイル
- [verify_harmbench_reference.py](file:///mnt/nas/home/hiromi/src/sst_v2/verify_harmbench_reference.py): ユーザー提供の公式参照元検証スクリプト
- [v4/tests/fixtures/harmbench_official.json](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/fixtures/harmbench_official.json): 公式抽出fixture
- [v4/scripts/eval/eval_safety_v4.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/eval_safety_v4.py): HarmBench prompt定数（公式7規則）
- [v4/scripts/analysis/e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/analysis/e1_selector.py): `validate_benchmark_counts` 実装と厳格検査
- [v4/tests/test_e0_audit_gate.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e0_audit_gate.py): 公式プロンプト完全一致テストおよび件数不正パターンの回帰テスト
- [v4/tests/test_e1_selector.py](file:///mnt/nas/home/hiromi/src/sst_v2/v4/tests/test_e1_selector.py): テスト候補データへの件数付与

## 3. 検証手順
1. `python verify_harmbench_reference.py --repo-root . --write-fixture v4/tests/fixtures/harmbench_official.json` によるfixture抽出と全文一致確認（終了コード0）
2. `PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test` による全テスト（37件）PASS確認
3. `PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py` による主実験 E0 ゲート停止（`NO_GO`）確認
