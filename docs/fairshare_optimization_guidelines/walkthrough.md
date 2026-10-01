# 作業履歴 (Walkthrough)

## 実施内容

### 1. 実験結果の確認
- `/mnt/nas/home/hiromi/src/sst_v2/gpu` ディレクトリ内のCSVファイル群 (`benchmark_final_summary.csv`, `benchmark_vllm_summary.csv`) を読み込みました。
- また、コスト計算の根拠となる `benchmark_vllm_final.py` の実装を確認し、計算式 `(30 + cpu_cores) * elapsed` が使われていることを確認しました。

### 2. データ分析
- 新しいFairShare計算式においては、利用時間（walltime）が直接的にコストに掛かるため、単位時間当たりのスループットを上げることが最も重要であることが判明しました。
- 短い入力（例: 128トークン）では `batch_size=512`、中程度の入力（例: 512トークン）では `batch_size=384` が、コストパフォーマンス（`fairshare_cost_per_1k`）の観点から最も優れている設定であることが分かりました。

### 3. ドキュメントの作成
- 今後実験を行う際の注意事項や推奨設定をまとめた `fairshare_guidelines.md` を作成しました。
- ユーザールールに則り、本作業の履歴と計画を管理する `task.md`, `implementation_plan.md`, `walkthrough.md` を作成しました。
