# Implementation Plan - Slurm (sbatch) 並列ジョブ実行環境構築 (1-GPU独立並列実行)

`python scripts/merge_eval_parallel.py` のマージ評価を、Slurm (sbatch) を用いて 12 個の独立したジョブ (seeds: 42, 43, 44 × patterns: 4種) としてキューに積み上げ、GPU 1枚につき 1 ジョブずつ自動で割り振られて実行される構造を構築します。

## Proposed Changes

### [Slurm Scripts]

#### [MODIFY] [slurm_merge_eval_array.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/slurm_merge_eval_array.sh)
- Slurm ヘッダーを `#SBATCH --gres=gpu:1` に変更し、各ジョブが GPU 1枚だけを要求するように設定。
- `--gpus 0` を `merge_eval_parallel.py` に引き渡し、Slurmが環境変数 `CUDA_VISIBLE_DEVICES` で各タスクに個別に割り当てた 1枚の GPU で評価を実行。

#### [MODIFY] [submit_merge_eval_jobs.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/submit_merge_eval_jobs.sh)
- Job Array による一括投入 (`--submit`) のほか、完全に個別名を持つ 12 個の sbatch ジョブとして順次投入するオプション (`--submit-separate`) も追加。

## User Review Required
> [!NOTE]
> 各ジョブが GPU 1枚を要求するため、クラスター上で利用可能な GPU が空き次第、12個のジョブが1つずつ自動的にスケジューリングされて実行されます。

## Verification Plan

### Manual Verification
- 1. 各パラメータの割り当てロジック（1-GPU 要求での seed × pattern の 12 通り）が正しく計算されるか検証。
- 2. `--dry-run` にてパラメータマッピングの出力結果を確認。
