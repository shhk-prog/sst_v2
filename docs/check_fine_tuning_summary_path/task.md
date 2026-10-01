# Task List

- [x] **MBPP 評価パイプラインのバグ修正**
  - `run_utility_eval.py` の `CODING_TASKS` で `mbpp` に `"no_chat_template": True` を追加
  - `run_lm_eval` 内で `no_chat_template` を判定し、`apply_chat_template` を制御する仕組みを実装
- [x] **Instruct モデル用 FT の設定修正**
  - `run_phase2_python.sh` で `MODEL` を `Meta-Llama-3-8B-Instruct` に変更
  - Alignment Tax（指示追従性の低下）を防ぐため、学習率を `2e-5`、エポック数を `3` に縮小
- [ ] **ターミナルでの学習・評価の再実行**
  - 修正したスクリプトを用いて、Instruct モデルベースの学習と評価を実行する

## 次のステップ（ユーザーによる実行）
以下のコマンドをターミナルで実行してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning
./run_phase2.sh
```

- [ ] `summarize_results.py` の実行確認
  - [ ] 作業ディレクトリを `v2/scripts/fine_tuning` としてコマンドを実行する
  - [ ] 実行がエラーなく完了することを確認する
  - [ ] 出力ファイル `v2/results/Llama-3-8B/lr2e-4_ep10/summary_report.md` が生成されていることを確認する
- [ ] 動作確認報告書の作成 (`walkthrough.md`)
