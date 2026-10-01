# タスクリスト

- [x] マージ時間とピークGPUメモリのログ抽出方法の調査
  - `models/merged/sst_merge_v3_main_*` のディレクトリ内にある `runtime_profile.json` を調査。
- [x] 表作成・挿入スクリプトの実装 (`scripts/analysis/generate_gpu_table.py`)
  - 実測マージ時間（`total_merge_execution`ステージの`elapsed_sec`）の平均を計算。
  - ピークGPUメモリ（`total_merge_execution`ステージの`gpu_max_memory_allocated_gb`）の平均を計算。
  - 計算結果からLaTeX形式の表を生成。
- [x] Markdownファイルの更新
  - スクリプトで `/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.md` 内の `\label{tab:gpu}` を含む表を正規表現で置換。
- [x] スクリプトの実行と検証
  - スクリプトを実行し、正常にドキュメントが更新されたことを確認。
