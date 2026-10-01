# タスク概要: evaluate キャッシュ競合 (Cache Collision) エラーの修正

## 背景
並列評価タスク実行時、`lm_eval.simple_evaluate()` において Hugging Face `evaluate` モジュールのキャッシュ競合による以下のエラーが発生し、リトライ状態に入る場合がある。

```text
[eval_utility] simple_evaluate failed (attempt 1/3): Error in finalize: another evaluation module instance is already using the local cache file. Please specify an experiment_id to avoid collision between distributed evaluation module instances.
```

## 目的
1. `v3/scripts/eval/eval_utility.py` の並列実行時にプロセスごとにユニークな `experiment_id` (`HF_EVALUATE_EXPERIMENT_ID`) を割り当て、キャッシュ衝突を防止する。
2. キャッシュ衝突時の再試行処理にランダムなバックオフ（ジッター）を追加し、リトライ成功率を高める。

## タスク一覧
- [x] `v3/scripts/eval/eval_utility.py` でプロセスごとのユニークな `HF_EVALUATE_EXPERIMENT_ID` を自動生成・設定
- [x] `simple_evaluate` の例外キャッチ時にリトライウェイトのランダム化（ジッター）を導入
- [x] ドキュメント (`docs/eval_cache_collision_fix/`) の整備
