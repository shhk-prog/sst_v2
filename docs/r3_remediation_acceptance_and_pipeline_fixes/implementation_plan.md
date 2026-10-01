# 実装計画書: R3是正の受入確認および残存修正対応

## 1. 目的と方針
「R3是正の受入確認・残存修正指示書」に基づき、指摘された5つの課題（構文・FIM受渡し、HarmBench呼出不整合、再集計・選定間のスキーマ不一致、コード評価順序と空テスト拒否、提案法overrideのバリデーション回避）を本質的に是正する。
本実験パイプラインについては、tokenizer/RoPEのモデル間不整合（E0）が正当に検出されているため **`NO_GO` を維持** し、採点環境と実測接続の厳密化を完遂する。

---

## 2. 是正対象とアーキテクチャ設計

### 2.1 merge_cli.py の構文修正と FIM 実受渡し (R3-06)
- **課題**: `--track` 引数の閉じ括弧欠落による構文エラー、および CLI で指定された `--fim_u`, `--fim_s` のファイルが読み込まれずマージャーに渡されていない問題。
- **改修方針**:
  - `merge_cli.py`: `--track` 引数定義の閉じ括弧を修正。
  - `run_merge`: `fim_u_path: Optional[str]`, `fim_s_path: Optional[str]` を受け取り、`torch.load` でテンソル辞書を読み込み、安全照合（必須キー、有限性、非負値）を行った上で `merge_state_dicts` に渡す。
  - `BaseMerger`: 各重みキーに対応する `fim_u[key]`, `fim_s[key]` を辞書から取り出して `merge_tensors` に供給。

### 2.2 HarmBench 引数・公式テンプレート・厳格ラベル解析 (R3-02)
- **課題**: `evaluate_harmfulness_harmbench` の第5引数が `context`、第6引数が `device` であるにもかかわらず、呼出側が第5位置引数に `device` を渡していたため、CPU指定が文脈プロンプトに化けるバグ。また独自テンプレートおよび `"not sure"` 等の曖昧出力が `startswith("no")` で誤判定される問題。
- **改修方針**:
  - `evaluate_harmfulness_harmbench(response, prompt, cls_model, cls_tokenizer, *, context=None, device="cuda")`: キーワード専用引数（`*`）にし、呼出側でも `context=None, device=device` を明示。
  - 公式 `LLAMA2_CLS_PROMPT`（Center for AI Safety 準拠）テンプレート（`[BEHAVIOR]`, `[GENERATION]`）を採用。
  - ラベル解析：`"not sure"`, `"no idea"` などの不確定フレーズを明示的に除外し、正規化後の有効ラベル集合（`"yes"`, `"no"`）への完全一致のみを判定、それ以外は `None`（未判定）として保持。

### 2.3 benchmark 別制約の再集計結果接続と欠測除外防止 (R3-03 / R3-05)
- **課題**: 再集計器が出力するキー（`safety_metrics_per_benchmark`）と selector が読み込むキー（`benchmarks` または `benchmark_metrics`）が不一致のため、個別 benchmark 制約がスキップされていた問題。また未完了 benchmark を除外してマクロ平均を出す経路が残っていた問題。
- **改修方針**:
  - `e1_selector.py`: `safety_metrics_per_benchmark`, `benchmarks`, `benchmark_metrics` を透過的に探索。
  - `reaggregate_v3_logs.py`: 1つでも benchmark に欠測・未判定がある場合、マクロ平均を計算せず `INSUFFICIENT_DATA` とする。
  - `required_benchmarks` 全件の存在・範囲内チェックを導入。
  - `parse_v3_result_file` に新 v4 出力形式（`model_path`, `task_name`, `sample_results`, `is_harmful`）を読み戻せるアダプターを接続。

### 2.4 コード評価のプロンプト結合順・空テスト拒否・OS隔離多層防御 (R3-01)
- **課題**: completion 単体をコンパイルしてから prompt と結合するため `return a + b` が関数外 return として失敗する問題、および test が存在しない場合にコード実行だけで合格扱いになる問題。
- **改修方針**:
  - `extract_code_block`: 行頭インデントを壊さず、改行のみを取り除く。
  - `build_humaneval_test_program`: prompt + code + test + `check(entry_point)` の完全コードを組み立ててから構文チェックと実行を行う。
  - test や test_list が存在しない場合は `NOT_EVALUATED` とし、決して PASSED に加算しない。
  - 子プロセス実行時に CPU リミット（5秒）およびソケット無効化（`socket.socket` 遮断）を適用。

### 2.5 提案法 override の欠損キー共通検査 (R3-04 / R3-07)
- **課題**: 提案法の独自 `merge_state_dicts` 実装で、safety 側にキーが欠損している場合に utility 側をコピーして続行していた問題。
- **改修方針**:
  - `validate_state_dicts` を共通関数として実装し、`ProposedInterventionMerger.merge_state_dicts` の先頭で呼び出し、欠損キーおよび形状不一致を厳格に `ValueError` 送出。

---

## 3. 受入検証計画
1. **構文検査**: `python -m compileall -q v4` (Exit 0)
2. **CLI 動作検査**: `python v4/scripts/mergers/merge_cli.py --help` (Exit 0)
3. **陽性 FIM マージテスト**: 小型テンソルを用いた手計算値との一致確認
4. **HumanEval 結合・空テスト拒否テスト**: インデント保持結合の PASS および空テストの NOT_EVALUATED
5. **HarmBench プロトコルテスト**: キーワード引数強制および曖昧ラベルの未判定化
6. **再集計から選定への一貫テスト**: 20% スパイクの INFEASIBLE および欠落ベンチマークの INSUFFICIENT_DATA
7. **提案法 override 検査テスト**: 欠損キー・形状不一致の拒絶
8. **全回帰テストスイート実行**: `run_v4_pipeline.py --smoke_test` (35 件全件 PASS)
