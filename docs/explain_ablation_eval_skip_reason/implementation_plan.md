# 実装計画: Ablation評価ジョブスキップ不全の調査と原因報告

Slurm ジョブ array `102020` において、インデックス `0, 2, 10, 12, 20, 47` が全スキップ（`skip complete`）されずに実行状態（`R`）で滞留している理由をコードおよび生成結果ファイルの状況から調査・分析し、報告を作成します。

## ユーザーレビュー事項
- 今回は調査および現象の要因特定が目的であり、コードの修正・再投入自体は必要に応じてユーザーと確認の上実施します。

## 調査内容と明確になった原因

### 1. スキップ判定（Resume）の仕組み
`scripts/merge_eval_parallel.py` では `--resume` オプションが指定された場合、モデルごとの全15個の評価タスク（Safety 4種、Utility 8種、AlpacaEval 1種、Instruction 2種）に対して `output_complete(output_path, limit)` を実行します。

### 2. スキップ不全（再実行）の発生条件
`output_complete()` 関数は以下の条件を満たさない場合、`False` を返します：
- 結果 JSON ファイルが存在しない
- JSON 内の `"status"` が `"failed"` である
- `"completed"` が `true` でなく、かつ収集サンプル数 `count` が `limit`（320）未満である

### 3. 対象インデックスでの具象原因
- **インデックス 0 (`alpha0.0_n50`)**: 前回の実行時に `mbpp` タスクで `lm_eval` の例外（`std::length_error` 等）が発生し、`utility_code_mbpp.json` が `"status": "failed"` として記録されているため再実行された。
- **インデックス 2 (`alpha0.0_n500_..._additive`)**: `mbpp` 評価結果 JSON が存在せず未評価状態であったため再実行された。
- **インデックス 10, 12, 20, 47**: 上記と同様に過去の評価エラー（`"status": "failed"`）や未完了・未生成ファイルが存在するため再実行された。

## 検証結果
- スキップされたジョブ（インデックス 1, 3, 4 等）のログと、未スキップ ジョブ（0, 2, 10, 12, 20, 47）の出力ファイルステータスを比較検証完了。

## 作成・保存ドキュメント
- `docs/explain_ablation_eval_skip_reason/task.md`
- `docs/explain_ablation_eval_skip_reason/implementation_plan.md`
- `docs/explain_ablation_eval_skip_reason/walkthrough.md`
