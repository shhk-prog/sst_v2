# タスクリスト: R3是正の受入確認および残存修正対応

## 概要
「R3是正の受入確認・残存修正指示書」で指摘された5大残存事項（構文・FIM受渡し、HarmBench引数・公式プロトコル、再集計とセレクターのスキーマ断絶、コード評価プロンプト結合順・空テスト拒絶、提案法overrideの欠損キー共通検査）を是正し、主実験 `NO_GO` を厳格に維持した上で全35件の回帰テストスイートを合格させる。

- **Baseline Commit**: `0d9220539f2256d4ee9dbfd2744101848f1f633e`（前々回監査対象）
- **Tested Commit**: `1d1b34d0b7d0f4976974079e6aa3ab79d1cf4a65`（作業ツリー修正適用対象）
- **主実験判定**: **`NO_GO` を維持**（実モデルの tokenizer/RoPE 不整合 E0 ゲート停止を正当に維持）

---

## タスク進捗

- [x] **1. merge_cli.py の構文エラー解消および FIM 実受渡し (R3-06)**
  - [x] `--track` 引数定義の閉じ括弧構文エラーの解消
  - [x] `run_merge` に `fim_u_path`, `fim_s_path` 引数を新設し、FIM テンソルファイルを読み込んで `merge_state_dicts` へ供給
  - [x] `BaseMerger.merge_state_dicts` でキー別 `fim_u[key]`, `fim_s[key]` を取り出して `merge_tensors` へ渡す
  - [x] 小型テンソルを用いた陽性 Fisher 加重平均手計算一致テストの追加・合格

- [x] **2. HarmBench 呼出引数・公式テンプレート・厳格ラベル解析 (R3-02)**
  - [x] `evaluate_harmfulness_harmbench` の `context` と `device` をキーワード専用引数（`*`）化し、位置引数による `device="cpu"` が `context="cpu"` に化けるバグを解消
  - [x] 公式 `LLAMA2_CLS_PROMPT`（`[BEHAVIOR]`, `[GENERATION]`）プロトコルにテンプレートを準拠
  - [x] `"not sure"`, `"no idea"` などの不確定フレーズを除外し、正規化後の有効ラベル（`"yes"`, `"no"`）への完全一致による厳格判定（曖昧な出力は未判定 `None` を保持）

- [x] **3. benchmark 別制約の再集計結果接続および欠測除外防止 (R3-03 / R3-05)**
  - [x] `e1_selector.py` が `safety_metrics_per_benchmark` を含む全プロデューサースキーマを透過的に読み込めるよう統一
  - [x] 1 benchmark でも未判定や欠測がある場合、再集計器がマクロ平均で除外して合格扱いにすることを防止（`INSUFFICIENT_DATA` を維持）
  - [x] `required_benchmarks` 全件の存在・完了・ASR_all・ASR_valid・VRR の範囲内検査
  - [x] 新 v4 評価出力（`model_path`, `task_name`, `sample_results`, `is_harmful`）を読み戻せるアダプターを `parse_v3_result_file` に接続
  - [x] 1 benchmark だけ ASR 20% で平均 5% の候補が不適格（`INFEASIBLE`）になることのエンドツーエンド検証

- [x] **4. コード評価のプロンプト結合順・空テスト拒絶・多層隔離 (R3-01)**
  - [x] `extract_code_block` で先頭インデントを壊さず、改行のみを取り除くよう改修
  - [x] HumanEval の completion 形式コード（`    return a + b`）を単体でコンパイルせず、`prompt + code + test` の完全形式を構築してから構文検査・実行
  - [x] テストスイート（`test` / `test_list`）が存在しない場合は `NOT_EVALUATED` とし、正解数に加算しないガードを実装
  - [x] 子プロセス実行時に CPU リミット（`resource.RLIMIT_CPU`）とネットワーク遮断（`socket.socket` 無効化）を適用

- [x] **5. 提案法 override の欠損キー共通検査 (R3-04 / R3-07)**
  - [x] 共通バリデータ関数 `validate_state_dicts` を `BaseMerger` から切り出し
  - [x] `ProposedInterventionMerger.merge_state_dicts` の先頭で `validate_state_dicts` を実行し、欠損キー（`missing_in_s`）および形状不一致を厳格に `ValueError` 送出
  - [x] 提案法 override における欠損キー・形状不一致の拒絶テストを追加・合格

- [x] **6. 総合受入検証および記録**
  - [x] `python -m compileall -q v4`: 構文エラー 0 件 (Exit 0)
  - [x] `python v4/scripts/mergers/merge_cli.py --help`: CLI 正常起動 (Exit 0)
  - [x] 全 6 回帰テストスイート（35 件）の全件合格確認 (`python v4/scripts/run_v4_pipeline.py --smoke_test`)
  - [x] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の整備
