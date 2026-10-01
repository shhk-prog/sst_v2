# 修正内容の確認 (Walkthrough): code_eval メトリクスキャッシュの分離

## 概要
HumanEval 評価時において、`code_eval` メトリクスが `~/.cache/huggingface/metrics/code_eval` 内の `.arrow` ファイルを並列プロセス間で奪い合い `[Errno 2] No such file or directory` が発生していた問題を、プロセスごとの一意な `HF_METRICS_CACHE` ディレクトリへ隔離することで解決しました。

## 変更点

### 1. スクリプトの改修
- [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
  - 起動時に `/tmp/hf_metrics_cache_{pid}_{uuid}` を作成し `HF_METRICS_CACHE` に自動設定。
  - リトライ処理時に `HF_METRICS_CACHE` を新規ディレクトリに更新。

## 効果
- 並列に複数プロセスで HumanEval / MBPP 等のコード生成評価を実行しても、`.arrow` ファイルが他プロセスによって消去される事故が防げます。
