# Hugging Face 認証エラーの修正計画

Llama-3 などのゲート付き（Gated）モデルにアクセスする際の 401 Unauthorized エラーを解決します。

## ユーザーレビューが必要な項目
- **Hugging Face トークンの取得**: [Hugging Face Settings](https://huggingface.co/settings/tokens) から Read トークンを取得し、`.env` ファイルに設定する必要があります。
- **モデルへのアクセス許可**: [Llama-3-8B-Instruct のページ](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) で利用規約に同意し、アクセス許可を得ている必要があります。

## 提案される変更

### [Component] 環境設定と学習スクリプトの修正

#### [NEW] [.env](file:///mnt/nas/home/hiromi/src/sst_v2/.env)
Hugging Face トークンを保存するための環境変数ファイルを作成します（テンプレートからコピー）。

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)
`.env` ファイルを読み込む処理を追加し、認証情報を自動的に使用するようにします。

## 検証計画

### 自動テスト
- `run_phase2.sh` を再度実行し、モデルのロードが正常に開始されることを確認します。

### 手動確認
- エラーログに 401 Unauthorized が出なくなることを確認します。
