# Task: 必須benchmark個別指標のnull拒否検査の復元 (R7)

## 概要
コミット `8fe3ddc45660f94e1ca5318f4e8cc0e66c65bfb3` において、HarmBench の公式 7 規則 fixture 照合および件数検査（`validate_benchmark_counts`）、コード実行停止（方針A）が受入確認された。
しかし、件数検査への置換時に以前存在していた「必須指標（`asr_all`, `asr_valid`, `vrr`）の null / 範囲拒否」が削除されており、件数が揃っていれば個別指標が欠測していても通過してしまうという回帰不具合が確認された。
本タスクでは、該当検査を復元し、追加回帰テストおよび全回帰テスト、主実験トラック（E0ゲート停止）の整合性を検証する。

## タスクリスト
- [x] 追加回帰テスト `test_e1_required_metric_regression.py` の配備と不具合の最小再現（27 failures の確認）
- [x] `v4/scripts/analysis/e1_selector.py` の `evaluate_feasible_region_strict` 内で、必須 benchmark ごとの `asr_all`, `asr_valid`, `vrr` の null / 無効値拒否チェックを復元
- [x] `test_e1_required_metric_regression.py` の実行（全 7 テストが PASS することの確認）
- [x] 公式照合スクリプト `verify_harmbench_reference.py` の再実行確認（終了コード 0）
- [x] スモークテスト・全回帰テストスイート（37 件）の実行（全テスト PASS 確認）
- [x] 主実験トラック（Primary Track）の実行と E0 ゲート停止（`NO_GO`）の正常挙動確認
- [x] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の作成と報告
