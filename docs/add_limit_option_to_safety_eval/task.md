# タスクリスト

- [x] `v3/scripts/eval_safety.py` の `parse_args()` において、`--limit` 引数を追加する
- [x] 同スクリプトのプロンプトの読み込み部において、`limit` が正の場合に件数制限をかけるように修正する
- [x] `v3/scripts/run_experiments.py` 内で `eval_safety.py` を呼び出している4箇所すべてに `"--limit", str(args.limit)` 引数を追加する
- [x] 修正後の `eval_safety.py` を `--limit 2` で実行し、正しく2件のみで処理が完了するか検証する（ユーザー環境での実行を推奨）
