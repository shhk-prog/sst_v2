# サンプルサイズ別 Slurm 並列実行設定 (Walkthrough)

ご要望いただいた **サンプルサイズ (50, 100, 500)** をそれぞれ **1 GPU ずつ割り当てて 3 並列** で Slurm ジョブ (`sbatch`) 実行するスクリプト群を構築しました。

---

## 1. 構築スクリプト一覧

1. **[slurm_ablation_sample_size.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/slurm_ablation_sample_size.sh)**:
   - Slurm Job Array (`--array=0-2`) スクリプト。
   - Task 0 ➔ `sample_size = 50` (1 GPU)
   - Task 1 ➔ `sample_size = 100` (1 GPU)
   - Task 2 ➔ `sample_size = 500` (1 GPU)
   - `PYTHONPATH=.` を自動ロードし `ModuleNotFoundError` を防止。
2. **[submit_ablation_sample_sizes.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/submit_ablation_sample_sizes.sh)**:
   - ジョブ一括投入＆ログディレクトリ自動生成スクリプト。

---

## 2. 実行手順

ターミナルにて以下のコマンドを実行するだけで、3 つの GPU で 3 つのサンプルサイズが同時に並列実行されます：

```bash
# 実行権限の付与
chmod +x scripts/slurm_ablation_sample_size.sh scripts/submit_ablation_sample_sizes.sh

# 3並列ジョブの投入
./scripts/submit_ablation_sample_sizes.sh
```

### ジョブ状態の確認コマンド

```bash
# 実行中ジョブの確認
squeue -u $USER

# ログの確認
tail -f logs/slurm_ablation_<JOB_ID>/sample_size_*.log
```
