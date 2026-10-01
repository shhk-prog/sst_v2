# 実装計画: vLLM 使用時のログ・結果保存ディレクトリ分離 (logs/vllm, results/vllm)

## 1. 概要
`--use_vllm` オプション指定時、ログファイルおよび評価結果ファイルの出力先をそれぞれ `logs/vllm/` および `results/vllm/` へ自動変更するように修正します。

## 2. 変更予定スクリプト

### 1. [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)
- `get_results_dir(limit, target="merged", use_vllm=False)`: `use_vllm` が `True` の場合、`results/vllm/...` を返す。
- `log_dir` 作成時に `use_vllm` が `True` の場合 `logs/vllm/...` を設定。

### 2. [run_base_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_base_eval_parallel.py)
- `get_results_dir(limit, use_vllm=False)`: `use_vllm` が `True` の場合、`results/vllm/...` を返す。
- `--use_vllm` 指定時に `--log_dir` のデフォルトが `logs/v3_base_eval_parallel` の場合、`logs/vllm/v3_base_eval_parallel` へ変更。

### 3. 個別評価スクリプト
- [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
- [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_safety.py)
- [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_instruction_datasets.py)
- [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_alpaca.py)
`--use_vllm` が有効で、`output_file` の先頭が `results/` の場合、`results/vllm/` に自動変換して保存。

## 3. 検証計画
- 各スクリプトのパース・パスマッピングテストを実施し、`results/vllm/...` および `logs/vllm/...` に保存先が変更されることを確認。
