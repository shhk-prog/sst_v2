# 修正内容の確認 (Walkthrough): vLLM 実行時のログ・結果保存ディレクトリ分離

## 概要
`--use_vllm` オプションを有効にして評価を実行した際、ログおよび結果ファイルが `logs/vllm/` および `results/vllm/` 配下に自動保存されるように変更・対応を行いました。

## 変更されたスクリプトと内容

1. **[merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)**
   - `get_results_dir()`: `use_vllm=True` の場合に `results/vllm/...` を返却するよう拡張。
   - `log_dir`: `use_vllm=True` の場合に `logs/vllm/v3_merged_eval_parallel_...` へ出力先を変更。

2. **[run_base_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_base_eval_parallel.py)**
   - `get_results_dir()`: `use_vllm=True` の場合に `results/vllm/...` を返却するよう拡張。
   - `log_dir`: `use_vllm=True` の場合に `logs/vllm/v3_base_eval_parallel` へ出力先を変更。

3. **個別評価スクリプト**:
   - [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
   - [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_safety.py)
   - [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_instruction_datasets.py)
   - [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_alpaca.py)
   - `--use_vllm` 有効時、`output_file` のパスの先頭が `results/` の場合に自動で `results/vllm/` にルーティング・作成するように改善。

## 確認内容
- `--use_vllm` 付きで実行した場合と付かない場合で、出力先が `results/vllm/`・`logs/vllm/` と `results/`・`logs/` に正しく分離されることを確認しました。
