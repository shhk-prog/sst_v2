# タスク概要: vLLM 使用時のログ・結果保存先ディレクトリ分岐 (logs/vllm, results/vllm)

## 背景
ユーザーの要求により、`vLLM` バックエンド（`--use_vllm`）を利用して評価を実行した場合、ログおよび結果ファイルの保存先を従来の `logs/` や `results/` 直下ではなく、`logs/vllm/` および `results/vllm/` 配下に分離・保存するように変更する。

## 目的
1. vLLM バックエンドでの実行結果・ログを通常 HuggingFace バックエンドでの結果と明確に分離・整理する。
2. 並列評価実行スクリプト (`merge_eval_parallel.py`, `run_base_eval_parallel.py`) および個別評価スクリプト (`eval_utility.py`, `eval_safety.py` 等) において、`--use_vllm` 指定時に保存先パスを `results/vllm/...` および `logs/vllm/...` へ自動的に振り分ける。

## タスク一覧
- [x] `v3/scripts/merge_eval_parallel.py` の `result_dir` および `log_dir` の vLLM 対応
- [x] `v3/scripts/run_base_eval_parallel.py` の `result_dir` および `log_dir` の vLLM 対応
- [x] 各個別評価スクリプト (`eval_utility.py`, `eval_safety.py`, `eval_instruction_datasets.py`, `eval_alpaca.py`) で `--use_vllm` 時の `output_file` パス補正処理の追加
- [x] ドキュメント (`docs/vllm_output_dir_fix/`) の整備
