# タスク: ablation評価ジョブで0, 2, 10, 12, 20, 47がスキップされずに実行されている理由の解明

## 目的
Slurm ジョブ `102020` において、特定のアブレーションモデル評価インデックス（`0, 2, 10, 12, 20, 47`）がスキップ（`skip complete`）されずに実行（Running）されている原因を解明する。

## タスクリスト
- [x] 関連コード（`merge_eval_parallel.py`, `slurm_ablation_eval_by_model.sh` 等）の確認
- [x] ログファイル（`logs/slurm_ablation_102020/eval_model_*.log`）の内容確認
- [x] スキップ判定ロジック（`output_complete`, `find_latest_timestamped_file`, `alpaca_outputs_complete` 等）の解析
- [x] インデックス `0, 2, 10, 12, 20, 47` の対象モデルと生成ファイル（結果JSON）のステータス比較・原因分析
- [x] ユーザーへの詳細回答・報告ドキュメント作成
