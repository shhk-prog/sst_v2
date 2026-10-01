# Implementation Plan: SafeMERGE 再現パイプラインの実装

## 目的
SafeMERGEの論文実験を再現するため、Llama-2モデルに対して「タスク特化型（GSM8Kなど）」および「安全性特化型」の2つのLoRAアダプタを自前で学習（ファインチューニング）し、最後にそれらをマージする一連のパイプラインを実装する。

## Proposed Changes

### 1. ファインチューニング用スクリプトの作成
#### [NEW] `finetune_lora.py`
Hugging Face の `trl` (SFTTrainer) や `peft` を用いて、LoRAアダプタを学習する汎用スクリプトを作成します。
- 引数でデータセット（`gsm8k`, 安全性データセット等）や出力先ディレクトリを指定可能にする。
- GSM8K用のプロンプトフォーマット（Question/Answer）および、安全性データセット（指示に対する安全な拒否・回答）のフォーマットを適宜切り替えて処理するロジックを実装。

### 2. 再現用シェルスクリプトの作成
#### [NEW] `run_safemerge_pipeline.sh`
以下の3ステップを自動で連続実行するシェルスクリプトを作成します。
1. **GSM8Kアダプタの学習**: `finetune_lora.py` を実行し、結果を `outputs/gsm8k_lora` に保存。
2. **安全性アダプタの学習**: 安全性データセット（例: `PKU-Alignment/PKU-SafeRLHF` の安全側データ）を用いて `finetune_lora.py` を実行し、`outputs/safety_lora` に保存。
3. **SafeMERGEの実行**: `python baseline/SafeMERGE/get_safemerge_model.py` に対して、上記2つのローカルディレクトリを `--finetuned_model_id` および `--safety_model_id` として渡し、マージモデルを出力する。

## 確認事項 (User Review Required)
> [!IMPORTANT]
> 以下の点についてご確認をお願いします。
> 1. 学習には `trl`, `datasets`, `accelerate` などのライブラリを使用します。環境に不足しているパッケージは適宜インストールしてよろしいでしょうか？
> 2. 学習（LoRA）にはGPUのVRAMを消費します。リソース制約を抑えるため、8-bit量子化などを利用した学習（QLoRA）も実装に組み込んだ方がよろしいでしょうか？
> 3. 安全性用の学習データセットとして、標準的な `PKU-Alignment/PKU-SafeRLHF` などをデフォルトで用いる想定ですが、もし特定のデータセットを使いたいなどのご要望があればお知らせください。
