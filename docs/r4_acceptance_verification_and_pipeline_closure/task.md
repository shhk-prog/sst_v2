# タスクリスト: R4 是正受入確認と残存修正の完遂

## 目的
ユーザーからの「５項目の是正受入確認・残存修正指示書」に基づき、以下の3大残件の完全是正、実機テストの合格、およびパイプライン状態（主実験 NO_GO 維持、診断・接続テストの成功）を確認・文書化する。

## 追跡対象 Commit
- **Baseline Commit**: `0d9220539f2256d4ee9dbfd2744101848f1f633e`
- **Tested Commit / 親Commit**: `cd3334c71f86f5486cb31871348044f125b8b47f`
- **作業ツリー**: HEAD上の是正差分適用後

---

## タスク進捗

- [x] **残件A：HarmBench公式仕様とラベル解析の完全一致化**
  - [x] 公式 `LLAMA2_CLS_PROMPT`（Rules全文含む）およびContextual版プロンプトの完全準拠実装 (`v4/scripts/eval/eval_safety_v4.py`)
  - [x] 純粋関数 `parse_harmbench_label` による厳密な完全一致判定（"yes or no", "probably no", "not sure" 等を `None` 未判定化）
  - [x] 実パーサー直接呼出による受入テスト (`v4/tests/test_e0_audit_gate.py`)
- [x] **残件B：必須benchmarkとnullの厳格検査**
  - [x] `DEFAULT_REQUIRED_BENCHMARKS` を定義し、runner / selector / 感度分析へ明示的に受渡し (`v4/scripts/analysis/e1_selector.py`, `v4/scripts/run_v4_pipeline.py`)
  - [x] 個別指標 (`asr_all`, `asr_valid`, `vrr`) が `None` / 不正値の場合の `INSUFFICIENT_DATA` 厳格判定（「Noneなら検査しない」の完全撤廃）
  - [x] 再集計器 (`reaggregate_v3_logs.py`) での欠測判定に `asr_valid` を追加、除外平均の撤廃
  - [x] 生ログ → parse → reaggregate → select のファイル一貫接続テスト (`v4/tests/test_e0_audit_gate.py`)
- [x] **残件C：コード評価のOS隔離とガード**
  - [x] 未隔離ホスト上での任意モデル生成コード実行を `BLOCKED` とする安全機構 (`v4/scripts/eval/eval_utility_v4.py`)
  - [x] プロセスグループ分離 (`os.setpgrp` / `os.killpg`)、環境変数消去、ソケット無効化
  - [x] `NOT_EVALUATED` 存在時の主指標 `pass_at_1` 未完了化（`None`）と coverage 明示
  - [x] 未隔離環境でのブロック挙動の受入テスト (`v4/tests/test_e0_audit_gate.py`)
- [x] **接続テストとパイプライン検証**
  - [x] 実 CLI (`merge_cli.py::run_merge`) による FIM テンソル読込・結合・保存・完全性検証テスト
  - [x] 全 6 テストスイート（36 件）の smoke_test 実行と PASS 確認
  - [x] 主実験パイプラインが E0 不整合ゲートにより正当に `NO_GO` で停止することの確認
- [x] **監査レポート・ドキュメント作成**
  - [x] `task.md` 作成
  - [x] `implementation_plan.md` 作成
  - [x] `walkthrough.md` 作成
