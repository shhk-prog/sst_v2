# Walkthrough: Hugging Face Gated Repo Errorの修正

## 修正の概要
ユーザーがLlama-2のようなアクセス制限のあるリポジトリ（Gated Repo）をロードする際に発生した `401 Unauthorized` のエラーを修正しました。Hugging Faceのモデルをロードする関数で認証情報が利用されるように修正を加えました。

## 行った変更内容
1. **[get_safemerge_model.py](file:///mnt/nas/home/hiromi/src/sst_v2/SafeMERGE/get_safemerge_model.py)**
   - `AutoModelForCausalLM.from_pretrained`、`PeftModel.from_pretrained`、および `peft_model.load_adapter` に対して、`token=os.environ.get("HF_TOKEN", True)` 引数を追加しました。これにより、キャッシュされた認証トークンまたは環境変数 `HF_TOKEN` が自動的に使用されるようになります。

2. **[utils.py](file:///mnt/nas/home/hiromi/src/sst_v2/SafeMERGE/utils.py)**
   - 先頭に `import os` を追加しました。
   - `compute_safelora_projection_matrices` 内でベースモデルとアライメント済みモデルを読み込む `AutoModelForCausalLM.from_pretrained` の呼び出し部分に `token=os.environ.get("HF_TOKEN", True)` を追加しました。

## ユーザーへの確認事項
> [!NOTE]
> この修正により、スクリプトはユーザーの環境変数 `HF_TOKEN` や、`huggingface-cli login` によって保存された認証情報（キャッシュ）を利用してモデルにアクセスするようになります。
> 実行する際は、ご自身のHugging Faceアカウントに該当モデル（例: `meta-llama/Llama-2-7b-chat-hf`）へのアクセス権限があり、かつターミナル上で `huggingface-cli login` 等によるログインが完了していることをご確認ください。

修正後のスクリプトを再度実行していただき、問題なく動作するかご確認ください。
