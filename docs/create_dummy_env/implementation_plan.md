# ダミーの.envファイル作成計画

## 目的
`v2` ディレクトリまたはプロジェクトにおいて、Hugging Faceモデルのダウンロードや実験ログの記録などに必要な環境変数のひな形（ダミー値）を提供する `.env` ファイルを作成する。

## 実装内容
1. `sst_v2/.env` （プロジェクト直下）に以下の環境変数のダミーを設定したファイルを作成し、v1・v2両方で参照可能にする。
   - `HF_TOKEN`: Llama-3などのHugging Faceの制限付きモデルにアクセスするためのトークン
   - `WANDB_API_KEY`: Weights & Biasesによる学習ログ記録のためのAPIキー
   - `OPENAI_API_KEY`: LLMを用いた評価等で使用する場合のAPIキー

2. ドキュメント作成ルールの遵守
   - `docs/create_dummy_env/` ディレクトリ配下に `task.md`, `implementation_plan.md`, `walkthrough.md` を作成し、日本語で記録を残す。
