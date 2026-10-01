# Implementation Plan: SafeMERGE 多モデル展開実験

## 目的
SafeMERGE の論文（arXiv:2503.17239）で評価されている他のモデル（Llama-3.1, Qwen2, Qwen2.5 等）に対しても同様の実験（学習・マージ・評価）を連続して実行できる仕組みを構築する。

## 課題とアプローチ
SafeMERGE では、「アラインメント済みモデル（Instruct/Chat）」と「未アラインメントのベースモデル（Base）」の重みの差分を利用して安全な部分空間を計算します。そのため、モデルごとに正しいペアを指定して実行できる仕組みが必要です。

| アラインメント済みモデル (Aligned) | ベースモデル (Unaligned) |
|---|---|
| `meta-llama/Llama-3.1-8B-Instruct` | `meta-llama/Llama-3.1-8B` |
| `Qwen/Qwen2-7B-Instruct` | `Qwen/Qwen2-7B` |
| `Qwen/Qwen2.5-7B-Instruct` | `Qwen/Qwen2.5-7B` |

## Proposed Changes

### 1. パイプラインスクリプトの汎用化
現在 `Llama-2-7b` にハードコーディングされているスクリプトを、引数で任意のモデルペアを受け取れるように改修します。
- **[MODIFY] `run_safemerge_pipeline.sh`**: 
  - 引数 `$1` (Aligned Model) と `$2` (Unaligned Model) を受け取るように変更。
  - 出力先ディレクトリもモデル名ごとに切り替わるよう（例: `outputs/Llama-3.1-8B-Instruct/gsm8k_lora`）に動的化。
- **[MODIFY] `run_evaluation.sh`**: 
  - 同様に引数で対象のモデル名と、評価対象となるアダプタのパスを受け取れるように変更。

### 2. 全自動実行バッチスクリプトの作成
- **[NEW] `run_all_models.sh`**: 
  - 論文で検証されている複数のモデル（Llama-3.1, Qwen2, Qwen2.5）を配列で定義し、forループで順番に「タスク学習 → 安全性学習 → SafeMERGE → 評価」の全工程を自動実行するマスタースクリプトを作成します。

## 確認事項 (User Review Required)
> [!IMPORTANT]
> 1. **モデルへのアクセス権限**: Llama-3.1 などを Hugging Face からダウンロードするには、Hugging Face 上で Llama-3.1 の利用規約に同意し、アクセス権を得ているアカウントの `HF_TOKEN` が必要になります。アカウントの準備は問題ないでしょうか？
> 2. **実行時間とストレージ容量**: 3つの7B〜8Bモデルの学習・推論を連続で行うため、かなり長時間の処理になり、保存される LoRA アダプタの容量も増えます。VRAM やディスク容量に懸念があれば、対象モデルを1つに絞って試すことも可能です。
> 3. Qwen モデルの実行も含まれますが、`get_safemerge_model.py` 等にはすでに Qwen のバイアス（1D tensor）をスキップするロジックが組み込まれているため、そのまま動作する見込みです。
