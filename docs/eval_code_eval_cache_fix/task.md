# タスク概要: code_eval (.arrow) メトリクスキャッシュ競合エラーの防止

## 背景
HumanEval 等のコード生成評価において、Hugging Face `evaluate` ライブラリの `code_eval` メトリクスが共有ディレクトリ `~/.cache/huggingface/metrics/` 下で `.arrow` 一時ファイルを生成・消去するため、並列実行時に以下のファイル不在エラー（`[Errno 2]`）が発生する。

```text
[Errno 2] No such file or directory: '/mnt/nas/home/hiromi/.cache/huggingface/metrics/code_eval/default/default_experiment-1-0.arrow'
```

## 目的
1. `v3/scripts/eval/eval_utility.py` にて、プロセス固有の独立した `HF_METRICS_CACHE` ディレクトリ（例: `/tmp/hf_metrics_cache_{pid}_{uuid}`）を設定し、並列実行時の `.arrow` キャッシュファイルの干渉・削除競合を完全に防止する。
2. リトライ時に `HF_METRICS_CACHE` も再更新し、堅牢性を向上させる。

## タスク一覧
- [x] `v3/scripts/eval/eval_utility.py` に `HF_METRICS_CACHE` のプロセス隔離設定を追加
- [x] 例外再試行処理にて `HF_METRICS_CACHE` の再生成を追加
- [x] ドキュメント (`docs/eval_code_eval_cache_fix/`) の整備
