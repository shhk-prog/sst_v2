# AlpacaEval 実行時の .env 自動ロード機能追加計画

`sst_v2` フォルダの親ディレクトリ (`/mnt/nas/home/hiromi/src/`) にある `.env` ファイルから、OpenAI APIキーなどの環境変数を自動で読み取って設定する機能を `eval_alpaca.py` に追加します。

## User Review Required

> [!NOTE]
> `.env` に定義されている `OPENAI_API_KEY` が自動的にロードされ、AlpacaEval 2 の GPT-4 Turbo ジャッジ機能が正常に実行できるようになります。

## Open Questions

特にありません。

## Proposed Changes

### Script Changes

---

#### [MODIFY] [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py)
- スクリプトの `main()` 実行開始時に、親ディレクトリの `.env` ファイル（`/mnt/nas/home/hiromi/src/.env` など）を自動探索して環境変数をロードする `load_env_file()` ヘルパー関数を追加します。
- これにより、コマンド実行時に事前に `export OPENAI_API_KEY=...` を手動で行う必要がなくなります。

---

## Verification Plan

### Automated Tests
- なし

### Manual Verification
- 修正後、テスト用の評価スクリプトを少数のサンプル制限（例: `--limit 2`）で実行し、親ディレクトリの `.env` から API キーがロードされ、プレースホルダー結果ではなく実際の GPT-4 Turbo による判定スコアが算出されることを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_alpaca.py --model_path WizardLMTeam/WizardMath-7B-V1.0 --output_file results/raw/base_WizardMath_alpaca_eval2_test.json --limit 2`
