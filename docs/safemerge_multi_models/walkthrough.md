# Walkthrough: SafeMERGE 多モデル展開実験

## 目的
SafeMERGE論文で評価されている他のモデル（Llama-3.1-8B, Qwen2-7B, Qwen2.5-7B）に対しても、Llama-2 と同じ条件で「タスク学習」「安全性学習」「マージ」「GSM8K・安全性評価」を全自動で実行する仕組みを構築しました。

## 実装内容
1. **[run_safemerge_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_safemerge_pipeline.sh)**
   - ハードコーディングされていたモデル名を引数として受け取るように改修しました。
   - `Usage: ./run_safemerge_pipeline.sh <ALIGNED_MODEL_ID> <UNALIGNED_MODEL_ID>`
   - 実行結果のアダプタは、引数で渡されたモデル名ごとの専用フォルダ（例: `outputs/Llama-3.1-8B-Instruct/gsm8k_lora`）に自動で振り分けて保存されるように修正しています。

2. **[run_evaluation.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_evaluation.sh)**
   - 評価スクリプトも同様に、対象モデル名を引数に取るように修正し、モデルごとの専用フォルダからアダプタをロードするように改修しました。

3. **[run_all_models.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_all_models.sh)**
   - 上記のスクリプト群を統括するマスタースクリプトを新規作成しました。
   - スクリプト内に定義されたモデルペア配列（アラインメント済みモデルと未アラインメントモデルのセット）を順番に読み込み、自動で全工程をループ処理します。

## 確認事項・利用方法
> [!NOTE]
> ターミナルで `baseline/SafeMERGE` フォルダに移動し、以下のコマンドを実行するだけで複数のモデルに対する実験と評価がすべて自動で走ります。
> ```bash
> bash run_all_models.sh
> ```

> [!WARNING]
> - このスクリプトは非常に処理時間がかかります（1つのモデルにつき学習から評価まで数十分〜数時間）。
> - また、各モデルの重みファイルと生成される LoRA アダプタにより数十 GB のディスク容量と、一時的な VRAM を消費します。リソースにご注意ください。
> - （初回実行時）Llama-3.1 などを Hugging Face からダウンロードするには、Hugging Face 上で Llama-3.1 の利用規約に同意済みの `HF_TOKEN` が設定されている必要があります。
