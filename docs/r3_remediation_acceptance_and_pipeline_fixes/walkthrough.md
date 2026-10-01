# 改修内容の確認 (Walkthrough): R3是正の受入確認および残存修正対応

## 1. 監査対応の基本方針と判定結果

- **主実験判定**: **`NO_GO` を維持**
  - E0（tokenizer/RoPE 不整合および重み構造）ゲートによる停止は正当であり、未是正のまま主実験へ進めることはありません。
  - 今回の改修により、「採点環境と実測接続の厳密化」に関する残存事項を完全に是正しました。
- **コミット識別子の分離記録**:
  - `baseline_commit`: `0d9220539f2256d4ee9dbfd2744101848f1f633e`（短縮 `0d92205`，前々回監査対象）
  - `tested_commit`: `1d1b34d0b7d0f4976974079e6aa3ab79d1cf4a65`（作業ツリーでの是正コードを適用した検証対象）

---

## 2. 実行環境および検証コマンド結果の記録

指示書第8項の指定手順に従い、作業ツリーにて全検証コマンドを実行し、正常終了を確認しました。

### 2.1 コミットハッシュ確認
```bash
git rev-parse HEAD
# 出力: 1d1b34d0b7d0f4976974079e6aa3ab79d1cf4a65
```

### 2.2 作業ツリー状態
```bash
git status --short
# 出力:
#  M v4/scripts/analysis/e1_selector.py
#  M v4/scripts/analysis/reaggregate_v3_logs.py
#  M v4/scripts/eval/eval_safety_v4.py
#  M v4/scripts/eval/eval_utility_v4.py
#  M v4/scripts/mergers/base_merger.py
#  M v4/scripts/mergers/merge_cli.py
#  M v4/scripts/mergers/proposed_intervention_merge.py
#  M v4/tests/test_e0_audit_gate.py
#  M v4/tests/test_proposed_intervention_merge.py
```

### 2.3 全 Python コードの構文検査
```bash
v3/venv_v3/bin/python -m compileall -q v4
# 終了コード: 0 (SyntaxError 0件)
```

### 2.4 CLI ヘルプ表示確認
```bash
v3/venv_v3/bin/python v4/scripts/mergers/merge_cli.py --help
# 終了コード: 0
# options:
#   -h, --help            show this help message and exit
#   --method METHOD
#   --output_dir OUTPUT_DIR
#   --utility_model UTILITY_MODEL
#   --safety_model SAFETY_MODEL
#   --base_model BASE_MODEL
#   --method_kwargs METHOD_KWARGS
#   --track {primary,diagnostic}
#   --e0_manifest E0_MANIFEST
#   --fim_u FIM_U         Path to utility model FIM tensor file (.pt)
#   --fim_s FIM_S         Path to safety model FIM tensor file (.pt)
```

### 2.5 回帰テストスイートの実行結果
```bash
PYTHONPATH=v4/scripts:. v3/venv_v3/bin/python v4/scripts/run_v4_pipeline.py --smoke_test
# 終了コード: 0
# 
# ======================================================================
# RUNNING SECURE MERGE V4 REGRESSION TEST SUITE
# ======================================================================
# 
# --- Running: v4/tests/test_e0_audit_gate.py ---
# Ran 16 tests in 1.381s: OK
# [PASS] v4/tests/test_e0_audit_gate.py passed.
# 
# --- Running: v4/tests/test_utility_parser.py ---
# Ran 3 tests in 0.000s: OK
# [PASS] v4/tests/test_utility_parser.py passed.
# 
# --- Running: v4/tests/test_e1_selector.py ---
# Ran 5 tests in 0.000s: OK
# [PASS] v4/tests/test_e1_selector.py passed.
# 
# --- Running: v4/tests/test_characteristic_analyzer.py ---
# Ran 2 tests in 0.004s: OK
# [PASS] v4/tests/test_characteristic_analyzer.py passed.
# 
# --- Running: v4/tests/test_controlled_intervention.py ---
# Ran 3 tests in 0.011s: OK
# [PASS] v4/tests/test_controlled_intervention.py passed.
# 
# --- Running: v4/tests/test_proposed_intervention_merge.py ---
# Ran 6 tests in 0.002s: OK
# [PASS] v4/tests/test_proposed_intervention_merge.py passed.
# 
# >>> ALL REGRESSION TESTS PASSED! <<< (全35テスト合格)
```

---

## 3. 指示書課題に対する修正詳細と受入条件対照

| 課題項目 | 指摘内容 | 是正内容 | 受入検証結果 |
|---|---|---|---|
| **1. merge_cli.py 構文 & FIM実受渡し (R3-06)** | `--track` の閉じ括弧欠落による SyntaxError。CLI 引数 `--fim_u`, `--fim_s` のファイル読込と merger への受渡し漏れ。 | 閉じ括弧を修正。`run_merge` に FIM パス引数を追加し、`torch.load` したテンソル辞書を `merge_state_dicts` へ供給。`BaseMerger` で重みキー別に取り出して `merge_tensors` へ渡すよう改修。 | 小型テンソルを用いた陽性 Fisher 加重平均手計算一致テスト `test_fisher_merger_positive_cli_weighting` が PASS。CLI `--help` 正常。 |
| **2. HarmBench 呼出引数・公式テンプレート (R3-02)** | 第5位置引数に `device` を渡していたため `context="cpu"` と誤束縛され文脈に混入。独自テンプレートと startswith による誤判定（"not sure" が無害になる）。 | `evaluate_harmfulness_harmbench` の `context` と `device` をキーワード専用引数（`*`）化。公式 `LLAMA2_CLS_PROMPT` 準拠。曖昧フレーズ（"not sure", "no idea" 等）を除外し正規化後の有効ラベル（"yes", "no"）への完全一致のみ判定。 | `test_harmbench_device_and_strict_labels` でキーワード引数強制および曖昧ラベルの未判定化を検証し PASS。 |
| **3. benchmark 別制約の再集計結果接続 (R3-03 / R3-05)** | 再集計器が出力する `safety_metrics_per_benchmark` を selector が読めず空辞書判定。未判定 benchmark を除外して平均する経路の存在。 | `e1_selector.py` が `safety_metrics_per_benchmark` を含む全キーに対応。再集計器で 1 つでも benchmark に未判定・欠測があれば `INSUFFICIENT_DATA` とする厳格化。新 v4 評価出力を読み戻せるアダプターを接続。 | `test_reaggregate_to_selector_end_to_end_rejects_spike_and_missing` で 20% スパイクの不適格（`INFEASIBLE`）および欠落の `INSUFFICIENT_DATA` を検証し PASS。 |
| **4. コード評価のプロンプト結合順・空テスト拒絶 (R3-01)** | completion 単体を先に compile するため `return a + b` が構文エラーで落ちる。test なしでコード実行成功だけで PASSED になる。プロセス制限不足。 | `extract_code_block` でインデントを保持。`prompt + code + test + check()` を組み立ててから構文検査・実行。空テストは `NOT_EVALUATED` とし PASSED に加算しない。CPU リミットおよびネットワーク遮断（`socket.socket`）を適用。 | `test_eval_utility_humaneval_completion_and_empty_test` でインデント保持結合の PASS および空テスト拒絶を検証し PASS。 |
| **5. 提案法 override の欠損キー共通検査 (R3-04 / R3-07)** | 提案法独自の `merge_state_dicts` で safety 側にキーが欠損している場合に utility 側をコピーして続行していた。 | `validate_state_dicts` を共通関数として実装し、`ProposedInterventionMerger.merge_state_dicts` の先頭で呼び出し、欠損キー（`missing_in_s`）および形状不一致を厳格に拒否。 | `test_proposed_merger_rejects_missing_safety_keys_and_shape_mismatch` で欠損キーと形状不一致の拒絶を検証し PASS。 |

---

## 4. 結論
指示書に示された受入テスト 1〜8（構文、FIM陽性試験、HumanEval結合・空テスト拒否、OS隔離多層防御、HarmBenchプロトコル、一貫接続試験、提案法共通バリデーション、コミット識別子分離）のすべてを達成しました。主実験は E0 ゲートによる `NO_GO` を堅持しつつ、採点・選定パイプラインの厳密化を完了しました。
