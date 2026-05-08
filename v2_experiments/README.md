# SST-Merge 実験環境 V2 (トップ会議向け)

本ディレクトリ (`v2_experiments`) は、SST-Merge の優位性をトップ会議レベルの厳密さで証明するために、既存のコードベースに影響を与えずにゼロから構築された実験環境です。

## ディレクトリ構成

```text
v2_experiments/
├── README.md                  # 本ファイル（実行手順）
├── requirements.txt           # Pythonパッケージ依存関係
├── scripts/                   # 実行スクリプト群
│   ├── setup_env.sh           # Mergekit等の外部ツールインストール用
│   ├── data_prep/             # データセット準備
│   ├── fine_tuning/           # LoRA Fine-Tuning
│   └── merge/                 # マージ処理（提案手法 & Mergekit）
├── data/                      # ダウンロード・前処理されたデータセット（自動生成）
├── models/                    # 学習済みLoRAアダプタやマージ後のモデル（自動生成）
└── results/                   # 評価結果出力用ディレクトリ（自動生成）
```

---

## 実行手順 (Step-by-Step)

以下の手順に従って、実験パイプラインを実行してください。

### Step 1: 環境構築

まず、Pythonの依存パッケージをインストールします。

```bash
cd v2_experiments
pip install -r requirements.txt
```

次に、ベースラインのマージや評価に必要な外部リポジトリ (`Mergekit`, `lm-evaluation-harness`) をクローンし、セットアップします。

```bash
bash scripts/setup_env.sh
```

### Step 2: データセットの準備

Utility（金融ドメイン等）およびSafety（AdvBench/TrustLLM等）のデータをダウンロードし、SFT用にフォーマットします。

```bash
python scripts/data_prep/prepare_datasets.py
```
> ※ 実行後、`data/` ディレクトリに `utility_fpb.json` と `safety_advbench.json` 等が生成されます。

### Step 3: モデルのFine-Tuning (Utility & Safety)

ベースモデル（例: Llama-3-8B-Instruct）に対して、Utility用とSafety用のLoRAアダプタをそれぞれ学習させます。

**Utilityモデルの学習:**
```bash
python scripts/fine_tuning/run_lora_ft.py \
    --model_name_or_path "meta-llama/Meta-Llama-3-8B-Instruct" \
    --utility_dataset_path "data/utility_fpb.json" \
    --output_dir "models/utility_ft_model"
```

**Safetyモデルの学習 (純粋なSafety FT):**
```bash
python scripts/fine_tuning/run_lora_ft.py \
    --model_name_or_path "meta-llama/Meta-Llama-3-8B-Instruct" \
    --safety_dataset_path "data/safety_advbench.json" \
    --output_dir "models/safety_ft_model"
```

**比較手法: Direct Safety FT (Mixed FT & LR Sweep)**
単純な LoRA FT ベースラインとして、UtilityとSafetyデータを混合してFTする手法（Safety Taxの発生を確認するためのベースライン）も実行可能です。混合比率(`safety_mix_ratio`)や学習率(`learning_rate`)を変更してスイープを行います。

```bash
# 例: Safety 20%, Utility 80% の混合データで学習率 1e-4 で学習
python scripts/fine_tuning/run_lora_ft.py \
    --model_name_or_path "meta-llama/Meta-Llama-3-8B-Instruct" \
    --utility_dataset_path "data/utility_fpb.json" \
    --safety_dataset_path "data/safety_advbench.json" \
    --safety_mix_ratio 0.2 \
    --learning_rate 1e-4 \
    --output_dir "models/mixed_ft_s20_u80_lr1e4"
```

### Step 4: ベースラインマージの実行 (Mergekit利用)

公式の `Mergekit` を用いて、Task Arithmetic や TIES といったベースライン手法を実行します。

```bash
cd scripts/merge
bash run_mergekit.sh
cd ../..
```
> ※ スクリプト内の `BASE_MODEL` などのパスは、ご自身の環境のモデルパスに合わせて適宜修正してください。

### Step 5: SST-Merge (提案手法) の実行

`scripts/merge/sst_merge_core.py` は、提案手法のコアロジック（FIM計算とGEVPに基づくマージ）を含んでいます。
このファイルをインポートし、Step 3で作成したモデル群を読み込んでマージ処理を実行します。
（※ 後日、本番用の実行スクリプト `run_sst_merge.py` を追加実装し、詳細なパラメータスイープを行う予定です。）

### Step 6: 評価の実行

評価は、インストールした `lm-evaluation-harness` と `HarmBench` 公式実装等を用いて実施します。
（例：MMLUやGSM8Kの評価）

```bash
# lm-evaluation-harness の実行例
lm_eval --model hf \
    --model_args pretrained=models/merged/task_arithmetic_alpha05 \
    --tasks mmlu,gsm8k \
    --device cuda:0 \
    --batch_size 8
```
