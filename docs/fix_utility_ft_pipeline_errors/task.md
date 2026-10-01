# タスクリスト: LLaMA-Factory の datasets バージョン競合エラーの修正

- [x] `run_full_pipeline.sh` に `export DISABLE_VERSION_CHECK=1` を追加して、LLaMA-Factory のバージョンチェックを回避する
- [ ] パイプライン `/mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh` をバックグラウンドで再実行する
- [ ] ログファイル `/mnt/nas/home/hiromi/src/sst_v2/utility_FT/logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log` を監視し、FT（Model 1〜3）がエラーを出さずに進むことを確認する
- [ ] 実行結果およびウォークスルーの作成
