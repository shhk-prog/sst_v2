# 実装計画: code_eval (.arrow) メトリクスキャッシュ競合防止

## 1. 概要
`lm_eval` の `code_eval` メトリクスがデフォルトの共有ディレクトリ `~/.cache/huggingface/metrics` に一時データ (`.arrow`) を作成するため、複数の評価プロセスが同時に実行されると、他プロセスによって `.arrow` ファイルが削除・上書きされ `[Errno 2] No such file or directory` が発生します。
プロセス固有の `HF_METRICS_CACHE` 一時ディレクトリを設定・隔離することで根本解決を図ります。

## 2. 変更予定内容

### [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)

#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
1. スクリプト冒頭で `os.environ["HF_METRICS_CACHE"]` を `os.getpid()` と `uuid` で一意なディレクトリ（`/tmp/hf_metrics_cache_...`）に設定。
2. リトライ処理時に `HF_METRICS_CACHE` ディレクトリを自動更新・クリーン生成。

## 3. 検証計画
- `v3/scripts/eval/eval_utility.py` の動作確認および設定値の確認。
