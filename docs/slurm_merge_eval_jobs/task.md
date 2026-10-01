# Task: sbatch (Slurm) による並列マージ評価ジョブの構築

## 目的
`python scripts/merge_eval_parallel.py --config configs/config_main.yaml --seeds 42 43 --limit 320 --gpus 0,1,2 --resume` の実行を Slurm (sbatch) で並列実行できるように対応する。

## 要件
- 種別/パラメータ組み合わせ:
  - seeds: `42`, `43`, `44` (3種類)
  - patterns:
    - `safety+math`
    - `safety+code`
    - `safety+medical`
    - `safety+math+code+medical`
    (4種類)
- 各ジョブは **GPU 1枚 (`--gres=gpu:1`)** を要求する独立したジョブとしてキューに積まれる。
- 空いている GPU リソースに対して 12 個のジョブが 1 つずつ順次割り振られて並列実行される。


## 成果物
1. Slurm Job Array スクリプト `v3/scripts/slurm_merge_eval_array.sh`
2. 個別投入用・一括投入スクリプト `v3/scripts/submit_merge_eval_jobs.sh`
3. 関連ドキュメント (`task.md`, `implementation_plan.md`, `walkthrough.md`)
