# タスクリスト: SoK 実証 2 実行 GPU 情報の自動記録

- [x] `v5/scripts/slurm_fp32_sst_math.sh` の冒頭に GPU・環境情報取得＆`gpu_info_seed{42,43,44}.json` 原子保存を追加
- [x] `v5/scripts/run_local_fp32_sst_math.sh` に起動時の `nvidia-smi` 全 GPU 一覧出力を追加
- [x] `v5/scripts/merge_fp32_sst_math.py` の各 `merge_metadata.json` に `execution_env`（ホスト名・GPU 名・CUDA/PyTorch バージョン）を追加
- [x] `v5/scripts/analyze_sok_exp2.py` が `gpu_info_seed*.json` を読み込み、`exp2_analysis_summary.{md,json}` に実行 GPU 環境一覧表を含めるよう更新
- [x] 構文チェック（`bash -n`, `py_compile`）と単体テスト（`pytest v5/tests -q`）の確認
