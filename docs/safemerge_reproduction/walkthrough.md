# Walkthrough: SafeMERGE 再現パイプラインの実装

## 目的
SafeMERGE の実験（タスク用LoRAと安全性用LoRAを個別に学習させ、最後にそれらをマージする手法）をローカル環境で再現するための仕組みを構築しました。

## 実装内容
1. **[finetune_lora.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/finetune_lora.py)**
   - Hugging Face の `trl.SFTTrainer` や `peft` を用いて、Llama-2 モデルの LoRA アダプタをファインチューニングするスクリプトです。
   - `--dataset` 引数として `gsm8k` と `safety` を受け付けるようにしています。
     - `gsm8k` を指定した場合は、問題文と解答を用いたタスク学習が行われます。
     - `safety` を指定した場合は、`PKU-Alignment/PKU-SafeRLHF` データセットを用いた安全性学習（安全とラベルされた方の回答を使用）が行われます。
   - VRAMを節約するため、デフォルトで `--use_qlora` を用いると `BitsAndBytesConfig` (8-bit量子化) が有効になります。

2. **[run_safemerge_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_safemerge_pipeline.sh)**
   - 上記のスクリプトと SafeMERGE のスクリプトを一連の流れとして実行するパイプラインシェルスクリプトです。
   - 以下の3ステップを自動で順番に実行します：
     1. `gsm8k` のファインチューニング → `./outputs/gsm8k_lora` に保存
     2. `safety` のファインチューニング → `./outputs/safety_lora` に保存
     3. `get_safemerge_model.py` を実行 → `./outputs/safemerge_model` に最終的なマージモデルを出力

## 確認事項・利用方法
> [!NOTE]
> スクリプトは `baseline/SafeMERGE` フォルダ内に作成されています。
> ターミナルで `cd /mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE` を実行し、以下のコマンドで全体のパイプラインを実行できます。
> ```bash
> bash run_safemerge_pipeline.sh
> ```

> [!WARNING]
> ファインチューニングを実行するには、`trl`, `datasets`, `bitsandbytes`, `accelerate` などのライブラリが必要です。まだインストールされていない場合は、実行前に以下のようなコマンドでインストールをお願いいたします。
> ```bash
> pip install trl datasets bitsandbytes accelerate
> ```
