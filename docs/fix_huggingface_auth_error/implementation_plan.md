# Implementation Plan: Hugging Face Gated Repo Errorの修正

## 目的
`SafeMERGE` フレームワークで利用されている `get_safemerge_model.py` スクリプトおよび `utils.py` の実行時に発生する、Hugging Face の認証エラー（`401 Client Error: Unauthorized / GatedRepoError`）を解消する。

## 課題の背景
Llama-2 のような Gated Repo（アクセス制限のあるリポジトリ）からモデルや設定ファイルをダウンロードする場合、Hugging Face アカウントでの認証情報（トークン）が必要となる。しかし、既存のコードでは `AutoModelForCausalLM.from_pretrained()` や `PeftModel` 関連のロード処理でトークンが渡されていなかったため、ログイン済みであっても認証エラーが発生していた。

## 修正内容
1. **`get_safemerge_model.py` の修正**
   - 実行環境の環境変数 `HF_TOKEN` またはキャッシュされたログイン情報を自動的に利用できるよう、モデル読み込み時に `token=os.environ.get("HF_TOKEN", True)` を追加する。
   - `AutoModelForCausalLM.from_pretrained`
   - `PeftModel.from_pretrained`
   - `peft_model.load_adapter`

2. **`utils.py` の修正**
   - SafeLoRA用に行列を算出する `compute_safelora_projection_matrices` 関数内で `AutoModelForCausalLM.from_pretrained` が呼ばれているため、ここにも同様の `token` 指定を追加する。
   - `os` モジュールのインポートを追加する。

## 確認手順
ターミナル上で再度元のコマンドを実行し、エラーが発生せずに正常にモデルのマージ処理が進むことを確認する（※実行前に `huggingface-cli login` によるログインまたは `HF_TOKEN` のエクスポートが完了していることを前提とする）。
