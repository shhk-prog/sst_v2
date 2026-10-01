# Walkthrough - Slurm H100 モデル単位並列マージ評価

評価対象の全マージ済みモデルを **モデル 1 つ 1 つ独立した 1-GPU ジョブ** として Slurm に投入するモデル単位並列評価スクリプトを構築しました。

## 作成・変更ファイル

### 1. [slurm_merge_eval_by_model.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/slurm_merge_eval_by_model.sh)
- **概要**: 1モデルにつき GPU 1枚を要求して並列実行する sbatch スクリプト。
- **SBATCH ヘッダー設定**:
  - `#SBATCH --partition=h100`
  - `#SBATCH --qos=interactive_nofs`
  - `#SBATCH --cpus-per-task=16`
  - `#SBATCH --gres=gpu:1`
  - `#SBATCH --output=logs/slurm_merge_%A/eval_model_%a.log`
  - `#SBATCH --error=logs/slurm_merge_%A/eval_model_%a.err`

### 2. [submit_merge_eval_by_model.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/submit_merge_eval_by_model.sh)
- 評価対象モデルの総数を自動カウントし、1モデル＝1タスク (`--array=0-N`) として一括投入するスクリプト。

### 3. [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)
- `--model_index` (指定インデックスのモデルのみを評価) および `--list_models` (全モデルの一覧表示) のオプションを追加。

---

## 使い方・実行方法

### 1. 実行権限の付与 (初回のみ)
```bash
cd v3
chmod +x scripts/slurm_merge_eval_by_model.sh scripts/submit_merge_eval_by_model.sh
```

### 2. モデル一覧のプレビュー・確認 (--dry-run)
```bash
./scripts/submit_merge_eval_by_model.sh --dry-run
```

### 3. モデル単位で Slurm に一括投入 (1モデル = 1ジョブ)
```bash
# デフォルト (BATCH_SIZE=32) で全モデル一括投入
BATCH_SIZE=32 ./scripts/submit_merge_eval_by_model.sh --submit
```

### 4. 特定のモデル 1 つだけをピンポイントで投入・評価したい場合 (例: index=5 のモデル)
```bash
sbatch --array=5 scripts/slurm_merge_eval_by_model.sh
```
