# 実装計画: SoK 実証 2 実行 GPU 情報の自動記録

## 目的
GPU 種別やドライバ・CUDA・vLLM バージョンによる評価ドリフトを追跡可能にするため、各 seed の実行時に使用した物理 GPU の詳細情報を自動で構造化保存し、最終解析レポートへ自動転記する。

## 変更ファイル（すべて `v5/` 配下）
1. `v5/scripts/slurm_fp32_sst_math.sh`: 起動直後に `nvidia-smi`（index, name, uuid, pci.bus_id, memory.total, driver_version）および PyTorch/CUDA/vLLM バージョンを取得し、ログ出力と `v5/outputs/sok_exp2/gpu_info_seed${SEED}.json` への原子保存を追加。
2. `v5/scripts/run_local_fp32_sst_math.sh`: 起動時のノード全体 GPU 一覧を `local_launcher.log` へ記録。
3. `v5/scripts/merge_fp32_sst_math.py`: 各モデルの `merge_metadata.json` に `execution_env` フィールドを追加。
4. `v5/scripts/analyze_sok_exp2.py`: `gpu_info_seed*.json` を自動読み込みし、`exp2_analysis_summary.md`（第 5 節: 実行 GPU 環境の記録）および `exp2_analysis_summary.json` へ収録。
