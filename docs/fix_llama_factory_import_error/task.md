# タスクリスト

LLaMA-Factory のインポートエラー修正と、FT学習スクリプトのエラーハンドリング追加に関するタスクです。

- [ ] LLaMA-Factory `v0.9.0` へのチェックアウトと依存関係の再適用 (ユーザーによるコマンド実行)
- [x] run_model1_math.sh に `set -e` を追加 (モデル1学習スクリプト)
- [x] run_model2_coding.sh に `set -e` を追加 (モデル2学習スクリプト)
- [x] run_model3_medicine.sh に `set -e` を追加 (モデル3学習スクリプト)
- [ ] LLaMA-Factory の動作確認 (`llamafactory-cli --help` によるインポート確認)
- [ ] パイプラインの再実行による動作確認
