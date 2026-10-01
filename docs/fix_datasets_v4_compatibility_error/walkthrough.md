# 修正内容の確認 (Walkthrough): datasets v4 互換性エラー (TypeError) の修正

`lm-evaluation-harness` 実行時に `datasets==4.8.5` の内部バグにより `TypeError: must be called with a dataclass type or instance` が発生し、評価が強制終了していた問題を修正しました。

## 修正内容

### [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)
- パイプラインの依存関係インストールフェーズ（Phase -1）に以下を追加しました。
  ```bash
  pip install "datasets>=3.0.0,<4.0.0" --quiet
  ```
- これにより、`trl` が要求する `datasets>=3.0.0` と、`LLaMA-Factory` が要求する `datasets<=4.0.0` の両方を満たす安定バージョン（3.x 台）が強制的に適用され、互換性エラーおよび internal TypeError の両方を根本的に回避します。

## 検証方法（ユーザーによる実行）

IDEコマンドターミナル環境の制約により、こちらから直接バックグラウンドコマンドを実行して再開させることができません。お手数ですが、再度ターミナルから以下のコマンドを実行してパイプラインを再実行してください。

```bash
# 1. 仮想環境のアクティベートとディレクトリ移動
source /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/activate
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT

# 2. パイプラインのバックグラウンド実行
nohup ./run_full_pipeline.sh > logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log 2>&1 &
```

実行後、ログファイル `/mnt/nas/home/hiromi/src/sst_v2/utility_FT/logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log` を監視し、`BaseModel` の評価プロセスおよびファインチューニングが正常に進むことを確認してください。

```bash
tail -f logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log
```
