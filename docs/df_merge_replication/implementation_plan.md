# df-merge 再現実験 実装計画

Sanwoo Lee et al. (NAACL 2025) による論文 **"Dynamic Fisher-weighted Model Merging via Bayesian Optimization"** (`df-merge`) の再現実験を行い、結果の正確性と再現性を検証する計画です。

> [!IMPORTANT]
> **環境上の制約と実行方法について**
> 現在、エージェント環境（Antigravity IDE）のコマンド実行機能において `sandbox not available with IDE command terminal` というエラーが発生しており、エージェント側から直接コマンドを起動できません。
> そのため、本計画におけるコマンド実行ステップは、**ユーザーご自身のターミナルで実行していただく**形で進めます。
> エージェントはファイルの編集やコードの修正、実行結果の解析、およびレポートの自動生成を担当します。

---

## 概要

`baseline/df-merge` ディレクトリのコードを用い、6つのタスク（paws, qasc, quartz, story_cloze, wiki_qa, winogrande）におけるモデルファインチューンを行い、その後 `df-merge` によるモデルマージおよび評価を行う再現実験を実行します。
仮想環境は、指示通り `/mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge` 配下に作成し、他の手法と依存関係が競合しないクリーンな環境で実験を行います。

---

## 提案する手順（ユーザー様での実行をお願いします）

### 1. 仮想環境の作成とセットアップ
`baseline/df-merge` 配下に専用の仮想環境 `venv_df` (Python 3.12推奨) を作成し、依存関係をインストールします。以下のコマンドをターミナルで実行してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge

# 1. 仮想環境の作成 (Python 3.12ベース)
python3.12 -m venv venv_df

# 2. pip, setuptools, wheel の更新
./venv_df/bin/python -m pip install --upgrade pip setuptools wheel

# 3. Poetry を用いた依存関係のインストール
# (Poetry がインストールされている場合。--no-root で現在のパッケージ自体のインストールはスキップ)
poetry env use ./venv_df/bin/python
poetry install

# 4. もし Poetry でエラーが出る、または Poetry がインストールされていない場合の pip による直接インストール
./venv_df/bin/python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
./venv_df/bin/python -m pip install transformers==4.48.1 datasets==3.2.0 numpy==2.2.2 pandas==2.2.3 accelerate==1.3.0 bayesian-optimization==2.0.3 matplotlib==3.10.0 seaborn==0.13.2 ipykernel==6.29.5

# 5. promptsource パッケージのインストール
git clone https://github.com/bigscience-workshop/promptsource.git
./venv_df/bin/python -m pip install -e promptsource
```

### 2. データセットのダウンロード
`story_cloze` などの不足しているデータセットをダウンロードします。
（※`download_dataset.py` は、ダウンロード先を `./dataset` にするようにエージェント側で修正済みです。また、モデル `t5-base` / `t5-large` はすでに `models/` 配下に存在するため、モデルダウンロードはスキップ可能です）

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge
./venv_df/bin/python download_dataset.py
```
> [!NOTE]
> `story_cloze` データセットは Hugging Face 側でのライセンス承諾や手動ダウンロードが必要な場合があります。もし `download_dataset.py` で `story_cloze` のダウンロードに失敗した場合は、残りの5つのデータセットで再現実験を進めるか、手動でのデータ配置を検討します。

### 3. モデルのファインチューニング (Single-Task Fine-Tuning)
5つのデータセットそれぞれに対して `t5-base` をファインチューニングします。
実行にはGPUが必要です。バックグラウンドで実行し、ログを保存します。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge
mkdir -p logs

# ファインチューンを順次実行 (バックグラウンド実行)
nohup sh -c '
model_name_or_path=t5-base
config_path=./configs/t5-single-task.yaml
experiment_name=default
seed=42

for dataset in paws qasc quartz wiki_qa winogrande
do
    echo "Starting finetune for $dataset..."
    ./venv_df/bin/python src/finetune.py --dataset $dataset --model_name_or_path $model_name_or_path --config_path $config_path --experiment_name $experiment_name --seed $seed
done
' > logs/finetune_all.log 2>&1 &
```
進捗は以下のコマンドで確認できます。
```bash
tail -f logs/finetune_all.log
```

### 4. DF-Mergeの実行と評価
ファインチューニングされたチェックポイントを使って、モデルマージ（DF-Merge）を実行し評価を行います。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge

# DF-Merge の実行 (Expected Improvement, story_clozeを除外)
./venv_df/bin/python src/df-merge.py --ckpt_root experiments/finetune/default/ckpt --model_name_or_path t5-base --seed 42 --acquisition_fn ei --experiment_name merge --use_fisher --datasets paws qasc quartz wiki_qa winogrande > logs/df_merge_ei.log 2>&1 &
```

---

## 変更・修正予定ファイル

### [MODIFY] [download_dataset.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/df-merge/download_dataset.py)
- データセットのダウンロード先を `.dataset` から `./dataset` に変更し、リーダー側の読み込みパスと一貫性を持たせました。(修正済み)

---

## 検証計画

### 手動検証
- ユーザー様のターミナルで実行していただいた各ログ（`logs/finetune_all.log`, `logs/df_merge_ei.log`）を確認し、エラーなく完了しているかを検証します。
- `experiments/df-merge/merge/metrics/t5-base/ei/use_fisher_True/seed42/metrics.json` に出力される評価結果（精度情報）を読み込み、論文での報告値や期待される性能維持率と比較します。
- 検証結果を `docs/df_merge_replication/walkthrough.md` にまとめます。
