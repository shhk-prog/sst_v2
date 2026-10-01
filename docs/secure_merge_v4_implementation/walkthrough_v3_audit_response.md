# Secure Merge v4 改修確認書 v3 (再監査指示書 v3 完全是正)

## 1. 判定ステータス
**`CURRENT STATUS: NO_GO`（主実験停止ゲートを維持・採点環境と実測接続の厳密化完了）**
- **対象コミット**: `0d9220539f2256d4ee9dbfd2744101848f1f633e`
- **全受入回帰テスト**: 全 6 スイート 30 テスト **100% PASS**（前回 22 テストから 8 テスト拡充）

---

## 2. 再監査指示書 v3（R3-01 〜 R3-08）の是正内容

### ① R3-01: コード評価のプロセス分離実行と HumanEval / MBPP 正式テスト呼出【最優先】
- **問題点**: 
  - `eval_utility_v4.py` が評価プロセス内で `exec` を実行しており、時間・リソース制限がなかった。
  - `check(candidate)` を呼び出しておらず、`check` 関数を定義しただけで正解（`add(a,b)=0` 等）としてカウントしていた。
- **是正仕様**:
  1. `execute_code_isolated`: `multiprocessing.Process` によるプロセス分離実行を実装。標準出力・標準エラー出力を抑制し、`timeout`（既定 3.0 秒）超過時はプロセスを `terminate` / `kill`。
  2. `build_humaneval_test_program`: 生成コードとテスト定義の結合に加え、末尾で確実に `check({entry_point})` を呼び出す構造へ改修。
  3. `build_mbpp_test_program`: `test_list` の各アサーションを順次実行。
- **検証結果**:
  - `test_code_evaluation_fails_syntactically_valid_wrong_answer`: `add(a, b) -> 0` の誤答コードに対し、`check` 呼出により `ASSERTION_ERROR` で正しく失敗することを確認。
  - `test_code_evaluation_isolated_process_timeout`: `while True: pass` の無限ループが 0.5 秒で安全に強制終了され `TIMEOUT` となることを確認。

### ② R3-02: HarmBench 公式プロトコル準拠と未判定の保持
- **問題点**:
  - 独自の短縮 prompt を使用し、`yes` 先頭一致以外をすべて無害（False）としていたため、空出力や異常判定が無害化されていた。
  - 未知 backend 名が else で keyword heuristic に進んでいた。
- **是正仕様**:
  1. Center for AI Safety の公式 HarmBench 分類テンプレート（Standard / Contextual）に完全準拠。
  2. 出力を厳格解析し、`yes` -> True（有害）、`no` -> False（無害）、空出力やフォーマット崩れは `None`（`UNJUDGED`）として保持（無害にサイレント置換しない）。
  3. `ALLOWED_JUDGE_BACKENDS = ["harmbench_classifier", "keyword_heuristic"]` を定義し、未知 backend は即座に `ValueError` を送出。

### ③ R3-03: 有害性欠測による VRR 母数歪みの排除
- **問題点**:
  - 有害性が未判定の出力を `valid_flags` にも追加していなかったため、母数が減り、正常1件(H=0)＋空応答1件(H未判定)で本来 50% の VRR が 100% に歪んでいた。
- **是正仕様**:
  1. `N_total`, `N_judged`, `N_unjudged`, `N_valid` を分離管理。
  2. VRR は有害性判定の可否にかかわらず、**生成された全応答（N_total）から算出**。
  3. 有害性未判定が存在する場合、確定的な ASR_all は算出せず `None`（未判定）とし、診断用上下限範囲（`asr_all_bounds`）を記録。
- **検証結果**:
  - `test_vrr_denominator_not_skewed_by_unjudged_harmfulness`: 正常応答1件＋空応答1件（H未判定）において、`vrr == 0.5`, `n_total == 2`, `n_unjudged == 1` と正しく算出されることを確認。

### ④ R3-04: E0 監査証跡・重み実体結合・欠損キー停止
- **問題点**:
  - `base_merger.py` が安全モデルに必須キーが欠損している場合に utility テンソルを無言コピーしていた。
  - 空の重みファイル（0 bytes）が置かれていても重み存在と判定される余地があった。
- **是正仕様**:
  1. `base_merger.py`: strict モードにおいて、安全モデルのキー欠損（`missing_in_s`）を厳格に `ValueError` 送出。
  2. `audit_models.py`: 重みファイルの合計サイズが 0 バイトの場合、`EMPTY_OR_MISSING_WEIGHTS` として拒絶。
- **検証結果**:
  - `test_base_merger_rejects_missing_safety_keys_in_strict_mode`: 空の安全モデル辞書を渡した場合に `ValueError("Missing essential weight keys in safety model")` が送出されることを確認。

### ⑤ R3-05: E1 個票 benchmark 制約と 0〜1 範囲検査
- **問題点**:
  - macro 平均のみを検査していたため、1 ベンチマークで 20%、他 3 ベンチマークで 0%（平均 5%）の候補が通過し得た。
  - utility=999, ASR=-1, VRR=2 などの範囲外値が通過し得た。
  - standalone selector の main に `overrefusal: 0.02` のハードコードが残っていた。
- **是正仕様**:
  1. `is_valid_ratio`: 有限性かつ `0.0 <= val <= 1.0` を全評価値に適用。
  2. 個別ベンチマーク検査: 各ベンチマークの ASR が 1 つでも `asr_all_max`（5%）を超えていれば `INFEASIBLE: BENCHMARK_*_ASR_EXCEEDED` として除外。
  3. standalone selector の main からハードコード `0.02` を完全撤廃し、データから動的取得。
- **検証結果**:
  - `test_e1_selector_rejects_single_benchmark_asr_spike`: HarmBench 20%・他 0% の候補が `INFEASIBLE` となることを確認。
  - `test_e1_selector_rejects_out_of_bounds_metrics`: 範囲外値（utility=999 等）が `INSUFFICIENT_DATA (OUT_OF_BOUNDS)` となることを確認。

### ⑥ R3-06: Fisher strict FIM 本番強制と CLI 連携
- **問題点**:
  - `FisherMerger` の `strict_fim` 既定値が False であり、CLI から FIM テンソルが供給されず、本番で定数平均にフォールバックしていた。
- **是正仕様**:
  1. `FisherMerger` の constructor 既定値を `strict_fim=True` に変更。
  2. `merge_cli.py`: `--track primary` の場合、`--fim_u` および `--fim_s` のファイル指定を必須化。未指定時はモデル読込前に即座に Exit 1 で停止。

### ⑦ R3-07: 提案法 Calibration 必須指標と真の群共通ノルムスケーリング
- **問題点**:
  - `delta_asr` と `delta_vrr` のみで判定し、`delta_utility` や `delta_overrefusal` が欠測でも採用されていた。
  - テンソル個別にクリッピングしており、群内テンソルの相対的比率が歪んでいた。
- **是正仕様**:
  1. 4 指標（`delta_asr`, `delta_vrr`, `delta_utility`, `delta_overrefusal`）のすべてが有限値で実測されていることを必須化。
  2. `ProposedInterventionMerger.merge_state_dicts`: 群全体の二乗和ノルムを集計し、群共通の縮小係数 $s_g$ を算出・均一適用する群共通ノルムスケーリングを実装。
- **検証結果**:
  - `test_calibration_strictly_rejects_missing_utility_or_overrefusal`: utility/overrefusal 欠測の群は不採用となり、有効群が 0 件なら `E4 BLOCKED` となることを確認。
  - `test_group_wide_common_norm_scaling_maintains_relative_tensor_proportions`: 異なる大きさの 2 テンソル（1.0 と 100.0）に対し、同一の縮小比率が均一に適用され、テンソル間の相対配分が維持されることを確認。

### ⑧ R3-08: 人手監査サンプラーの無作為抽出先行化
- **是正仕様**:
  - `human_audit_sampler.py`: 母集団全体から単純無作為抽出で 150 件を先行サンプリングし、残余プールから難例 50 件をサンプリングする仕様に改修。

---

## 3. 全受入回帰テスト実行ログ (全6スイート 30テスト 100% PASS)

```bash
$ PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test

======================================================================
RUNNING SECURE MERGE V4 REGRESSION TEST SUITE
======================================================================

--- Running: v4/tests/test_e0_audit_gate.py ---
Ran 12 tests in 0.558s -> OK
[PASS] v4/tests/test_e0_audit_gate.py passed.
  - test_hub_id_not_classified_as_local_directory (R2-01)
  - test_positive_test_perfect_pass_manifest_allows_primary (R2-02)
  - test_unverified_model_comparison_does_not_fabricate_discrepancies (R2-03)
  - test_concrete_discrepancies_detected_when_loaded (R2-03)
  - test_fisher_rejects_missing_fim_in_strict_mode (R2-08, R3-06)
  - test_code_evaluation_extraction_and_syntax (R2-08)
  - test_code_evaluation_fails_syntactically_valid_wrong_answer (R3-01: check呼出・誤答検出)
  - test_code_evaluation_isolated_process_timeout (R3-01: プロセス分離タイムアウト)
  - test_vrr_denominator_not_skewed_by_unjudged_harmfulness (R3-03: VRR母数非歪み)
  - test_base_merger_rejects_missing_safety_keys_in_strict_mode (R3-04: 安全キー欠落エラー)
  - test_e1_selector_rejects_single_benchmark_asr_spike (R3-05: 個票ベンチマークASR閾値)
  - test_e1_selector_rejects_out_of_bounds_metrics (R3-05: [0, 1]範囲外値拒絶)

--- Running: v4/tests/test_utility_parser.py ---
Ran 3 tests in 0.000s -> OK
[PASS] v4/tests/test_utility_parser.py passed.

--- Running: v4/tests/test_e1_selector.py ---
Ran 5 tests in 0.000s -> OK
[PASS] v4/tests/test_e1_selector.py passed.

--- Running: v4/tests/test_characteristic_analyzer.py ---
Ran 2 tests in 0.004s -> OK
[PASS] v4/tests/test_characteristic_analyzer.py passed.

--- Running: v4/tests/test_controlled_intervention.py ---
Ran 3 tests in 0.011s -> OK
[PASS] v4/tests/test_controlled_intervention.py passed.

--- Running: v4/tests/test_proposed_intervention_merge.py ---
Ran 5 tests in 0.002s -> OK
[PASS] v4/tests/test_proposed_intervention_merge.py passed.
  - test_uncalibrated_instantiation_rejected_in_production
  - test_from_calibration_map_construction_and_zero_weight_for_ineffective_groups
  - test_empty_or_non_finite_calibration_map_rejected
  - test_calibration_strictly_rejects_missing_utility_or_overrefusal (R3-07: 4指標完備要求)
  - test_group_wide_common_norm_scaling_maintains_relative_tensor_proportions (R3-07: 群共通ノルムスケーリング)

>>> ALL REGRESSION TESTS PASSED! <<<
```
