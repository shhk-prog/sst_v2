# タスクリスト: Ablation マージ処理における `steering_hook` インポートエラーの修正および評価ジョブアレイの追加

- [x] `steering_hook.py` を `scripts/tests/` から `scripts/` ディレクトリ直下に配置
- [x] `scripts/tests/test_steering_hook.py` のインポート処理を `scripts/steering_hook.py` を参照するように修正
- [x] `unittest` による単体テスト実行確認 (`scripts/tests/test_steering_hook.py`)
- [x] `scripts/merge.py` の動作確認（インポートエラーが解消したかの検証）
- [x] Ablation評価用ジョブアレイ並列投入スクリプトの作成 (`scripts/slurm_ablation_eval_array.sh` & `scripts/submit_ablation_eval_jobs.sh`)
- [x] Ablationモデル単位評価用ジョブアレイ並列投入スクリプトの作成 (`scripts/slurm_ablation_eval_by_model.sh` & `scripts/submit_ablation_eval_by_model.sh`)
- [x] Ablation評価結果の保存フォルダ構成（`ablation/sst`, `ablation/datafree`）の分類ロジック改修 (`scripts/merge_eval_parallel.py`)
- [x] 実装・検証結果のドキュメント化 (`docs/fix_ablation_merge_steering_hook/walkthrough.md`)
