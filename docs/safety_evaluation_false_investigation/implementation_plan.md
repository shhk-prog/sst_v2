# 評価結果（completed: false）問題の全タスク調査および修正計画

ユーザーより追加でご指摘いただいた `alpaca_eval2`、`inst_evol_code`、`inst_medalpaca`、`general_mmlu` などのタスクについても調査を行い、発生しているすべての `completed: false`（エラー失敗）の根本原因を特定しました。

---

## 調査結果：3つの根本原因

調査の結果、エラーは以下の3つのいずれかに分類されることが判明しました。

### 原因①：Safety評価における空応答バグ (`Some samples are still unclassified.`)
* **対象タスク**: `wildjailbreak`, `strongreject`, `harmbench`, `jailbreakbench` などの安全評価タスクの一部モデル
* **詳細**: 
  マージモデルが崩壊している、あるいは非常に安全な状態であるために、プロンプトに対して何も出力せず即座にEOSトークンを返し、生成応答が空文字列 `""` になるケースがあります。
  現在の [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py#L361-L364) の実装では、応答が空文字列 `""`（Pythonで偽と判定される）であると、分類処理 (`missing` リスト) から除外されてしまいます。結果として該当サンプルの `asr` が `None` のまま残り、最終チェックで `RuntimeError: Some samples are still unclassified.` が発生して評価全体が失敗（`completed: false`）になります。

### 原因②：語彙サイズ不整合によるモデルロードエラー (`ignore_mismatched_sizes`)
* **対象タスク**: `inst_evol_code`, `inst_medalpaca`, `general_mmlu`, `alpaca_eval2` などのほぼすべてのタスク
* **対象モデル**: `task_arithmetic` 手法により `safety+code` や `safety+medical` などをマージしたモデル全般
* **詳細**: 
  `WizardCoder` など語彙サイズが 32001 のドメインモデルをマージした際、`mergekit`（`task_arithmetic` の `linear` マージ等）は語彙サイズを自動拡張し、出力される重みのテンソルサイズが `32001` になります。
  しかし、出力される `config.json` の `vocab_size` は `32000`（ベースモデル Llama-2 の値）のまま書き換えられないため、ロード時に `[32001, 4096] vs [32000, 4096]` のサイズ不整合が発生し、評価スクリプトでのモデルロードが失敗して `completed: false` になります。
  *(※ `ignore_mismatched_sizes=True` を指定してロードすると、不整合の起きた `lm_head` 等のレイヤー全体がランダム初期化されてしまう危険があるため、マージモデルの `config.json` の `vocab_size` を `32001` に書き換えることが正しい解決策となります。)*

### 原因③：OpenAI API クォータ不足・レートリミットエラー (`RateLimitError: 429`)
* **対象タスク**: `alpaca_eval2` の一部モデル
* **詳細**: 
  `alpaca_eval2` は GPT-4 をアノテーターとして評価を行いますが、APIキーのクォータ（料金上限）に達している、あるいはレートリミットの上限に達したため、API呼び出し時に 429 エラーとなり評価プロセス全体が失敗しています。
  *(※ これはスクリプト側ではなく、OpenAIアカウントの契約・残高に依存するエラーです。)*

---

## 提案する対策案

### 1. 空応答バグの修正 (対象: `eval_safety.py`)
`eval_safety.py` の分類対象選定ロジックを修正し、`response` が空文字列 `""` であっても無視せず、正しく処理（安全な応答として `asr = 0.0` を設定する）されるようにします。

### 2. config.json の vocab_size 自動補正処理の追加
マージモデル評価スクリプトを実行する際、ロードするモデルの `config.json` の `vocab_size` と、実際の重み（テンソル）のサイズに差がある場合、自動的に `config.json` を正しいサイズ（例: 32001）に更新する補正処理を評価ロード前（あるいはマージ完了直後）に追加します。これにより、重みのランダム初期化やロードエラーを一切防ぐことができます。

### 3. API制限に関する報告
クォータエラーについては、必要に応じて OpenAI API キーの設定や残高チャージを行っていただくよう報告します。

---

## 作業スケジュール

1. `eval_safety.py` を修正し、空の応答 `""` でも正常に ASR が算出されて評価が完了するようにする。
2. 評価実行スクリプト（または各ロード処理）において、マージモデルの `vocab_size` 不整合を検出し、自動で `config.json` を修正する処理を追加する。
3. エラーが発生していたモデル（特に `task_arithmetic` 関連や空応答が発生したモデル）を対象に評価を再実行し、`completed: true` になることを検証する。

---

## 成果物の保存場所
* 調査の進捗および最終結果は、以下のドキュメントにまとめます：
  * タスクリスト: `docs/safety_evaluation_false_investigation/task.md`
  * 修正内容の確認: `docs/safety_evaluation_false_investigation/walkthrough.md`
