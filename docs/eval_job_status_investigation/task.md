# タスクリスト: Slurm 評価ジョブ再投入の動作検証・修正・クリーンアップ

## 概要
ユーザーから「一度評価は全て終わったはずなのに、`submit_merge_eval_by_model.sh --submit` の実行後に `94901_200`, `94901_199` などの Slurm ジョブが実行中(R)になっている。評価が完了していなかったのか？」という疑問に対する調査・修正・クリーンアップ。

## タスク一覧
- [x] `./scripts/submit_merge_eval_by_model.sh` および `./scripts/slurm_merge_eval_by_model.sh` の実装調査
- [x] `./scripts/merge_eval_parallel.py` の `--resume` オプションの動作ロジック調査
- [x] ジョブ `94901` の実際の実行ログ (`v3/logs/slurm_merge_94901/eval_model_*.log`) の確認
- [x] ユーザーへの調査結果と理由の回答作成
- [x] `eval_alpaca.py` の `generate_batch` 名の未定義エラー (NameError) 修正
- [x] `eval_utility.py` の MMLU タイムスタンプ付き結果ファイルの自動検出・正規ファイルへのリネーム統合
- [x] `merge_eval_parallel.py` の `output_complete()` でのタイムスタンプ付きファイルの自動クリーンアップ・統一処理実装
- [x] 修正内容とクリーンアップ報告の作成 (`walkthrough.md`)
