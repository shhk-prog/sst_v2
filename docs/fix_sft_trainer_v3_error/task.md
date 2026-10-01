# タスクリスト：SFTTrainer の dataset_text_field 引数エラー修正

- `[x]` `v3/scripts/fine_tuning.py` の修正
  - `[x]` `from trl import SFTTrainer, SFTConfig` にインポートを修正
  - `[x]` `TrainingArguments` を `SFTConfig` に変更
  - `[x]` `SFTConfig` の引数に `dataset_text_field="text"` と `max_seq_length=512` を追加
  - `[x]` `SFTTrainer` の呼び出し部分から `dataset_text_field` と `max_seq_length` を削除
- `[x]` シード上書きバグの修正
  - `[x]` `v3/scripts/run_experiments.py` の修正（シード別出力 `--output_dir` 指定）
  - `[x]` `v3/scripts/merge.py` の修正（シード別ロード `_seed{seed}` 対応）
- `[/]` 動作確認（ユーザー環境での実行）
- `[ ]` `walkthrough.md` の作成と保存
