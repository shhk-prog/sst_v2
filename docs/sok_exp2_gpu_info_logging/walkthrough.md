# 修正内容の確認 (Walkthrough): SoK 実証 2 実行 GPU 情報の自動記録

## 記録される GPU 情報と保存先
1. **seed 別 GPU 詳細 JSON**: `v5/outputs/sok_exp2/gpu_info_seed{42,43,44}.json`
   - 記録項目: `hostname`, `slurm_job_id`, `cuda_visible_devices`, `nvidia_smi_gpus`（`index`, `name`, `uuid`, `pci_bus_id`, `memory_total`, `driver_version`）, `torch_gpus`（`name`, `total_memory_gb`, `compute_capability`）, `torch_version`, `torch_cuda_version`, `vllm_version`, `timestamp_utc`
2. **実行ログ**: `v5/outputs/sok_exp2/logs/local_launcher.log`（起動時 `nvidia-smi` 一覧）および `local_task{0,1,2}.log`（`[GPU Info]` 行）
3. **モデル別メタデータ**: 各 `v5/models/fp32_sst_math/*/merge_metadata.json` の `execution_env`
4. **最終解析レポート**: `v5/outputs/sok_exp2/exp2_analysis_summary.{md,json}` の「実行 GPU 環境の記録」表に自動転記

## 検証結果
- `bash -n v5/scripts/slurm_fp32_sst_math.sh`, `bash -n v5/scripts/run_local_fp32_sst_math.sh`: 正常
- `py_compile` および `pytest v5/tests -q`: 全 58 件合格
