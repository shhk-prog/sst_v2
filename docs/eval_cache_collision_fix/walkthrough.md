# 修正内容の確認 (Walkthrough): evaluate キャッシュ競合防止

## 概要
`lm_eval.simple_evaluate()` 実行時に発生していた Hugging Face `evaluate` モジュールのキャッシュ競合エラー（`another evaluation module instance is already using the local cache file`）に対して、プロセス固有の `experiment_id` 自動設定とジッター付きリトライ機構を導入しました。

## 変更点

### 1. スクリプトの改修
- [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
  - モジュール冒頭で `uuid` および `os.getpid()` を参照し、`HF_EVALUATE_EXPERIMENT_ID` をプロセス固有に初期化。
  - `simple_evaluate` 失敗時のリトライロジックにおいて、`HF_EVALUATE_EXPERIMENT_ID` を新しく再生成し、5〜15秒のランダムな待機時間（ジッター）を設定して再試行するように修正。

## 効果
- 並列評価実行時でもプロセス間でキャッシュファイルのロックが競合せず、円滑に評価が進行します。
