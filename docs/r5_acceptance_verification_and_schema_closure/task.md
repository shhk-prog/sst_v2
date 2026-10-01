# タスクリスト: R5 是正受入確認と残件3項目の完全是正

## 目的
ユーザーからの「R4是正の受入確認・残存修正指示書」に基づき、以下の3大残件の完全是正、厳密な単体・結合テストの合格、およびパイプライン状態（主実験 NO_GO 維持）を検証・文書化する。

## 追跡対象 Commit
- **Baseline Commit**: `cd3334c71f86f5486cb31871348044f125b8b47f`
- **Tested Commit / 前回到達点**: `d14886a115e4dbc836a8a96bf86b96eb58b5dfb7`
- **作業ツリー**: HEAD上の是正差分適用後

---

## タスク進捗

- [x] **残件A：HarmBench公式プロトコル全文一致と独立fixture検証**
  - [x] CAIS 公式固定リビジョン `37150ed7d07f1db7639c9e3cfee3288391482503` の Standard (4 Rules) および Contextual (7 Rules) テンプレート全文を取り込み (`v4/scripts/eval/eval_safety_v4.py`)
  - [x] レポート保存時に `classifier_revision` として公式リビジョンハッシュを記録
  - [x] 独立した公式参照 fixture との全文完全一致（`assertEqual`）テストを実装・合格 (`v4/tests/test_e0_audit_gate.py`)
  - [x] 純粋関数 `parse_harmbench_label` による厳格判定（全指示書テストケース網羅）を維持
- [x] **残件B：benchmark 主選定 schema 統一と旧スカラー形式の完全遮断**
  - [x] 主選定（`evaluate_feasible_region_strict`）において辞書形式を必須化し、数値1個のスカラー形式を `UNSUPPORTED_BENCHMARK_SCHEMA` として即座に `INSUFFICIENT_DATA` 判定 (`v4/scripts/analysis/e1_selector.py`)
  - [x] 正の評価件数（`n_samples > 0`）およびゼロ未判定（`n_unjudged == 0`）の厳格検査を実装
  - [x] 単独感度分析（`compute_sensitivity_matrix`）および CLI `main()` においても `DEFAULT_REQUIRED_BENCHMARKS` を既定で強制
  - [x] スカラー拒否、件数0拒否、未判定拒否の受入テストを実装・合格 (`v4/tests/test_e0_audit_gate.py`)
- [x] **残件C：コード評価のOS隔離（未接続ランナーの実行禁止・テスト専用経路の分離）**
  - [x] `check_secure_sandbox_isolation()` は、環境変数文字列の有無に関わらず、外部隔離ランナーの実体接続がない限り常に `(False, ...)` を返却 (`v4/scripts/eval/eval_utility_v4.py`)
  - [x] 本番のモデル生成コード評価（`run_code_evaluation`）では `allow_trusted_test_fixture` を完全削除し、`execute_code=True` を無条件に `BLOCKED`（RuntimeError）とする
  - [x] 人がレビュー済みのテスト fixture 専用実行関数 `run_trusted_fixture_execution` を新設し、テスト経路を本番から完全分離
  - [x] 未設定環境および `SECURE_CODE_SANDBOX_RUNNER="docker"` 設定時の両方で確実にブロックされる受入テストを実装・合格 (`v4/tests/test_e0_audit_gate.py`)
- [x] **回帰テストとパイプライン動作検証**
  - [x] 全 6 テストスイート（37 件）の smoke_test 実行と PASS 確認
  - [x] 主実験パイプライン（Primary Track）が E0 ゲートにより正当に `NO_GO` で停止することを確認
- [x] **監査レポート・ドキュメント作成**
  - [x] `task.md` 作成
  - [x] `implementation_plan.md` 作成
  - [x] `walkthrough.md` 作成
