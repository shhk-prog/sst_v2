# ビルド手順：v5

## 前提

- 実行場所: ワークスペース直下（`/mnt/nas/home/hiromi/src/sst_v2`）
- Python: `venv_sst/bin/python`（pytest 9.0.3、numpy 2.4.6、matplotlib 3.10.9、torch 2.12.0+cu130、safetensors 0.7.0 を確認済み。何も追加で入れていない）
- GPU は使わない。`v3/results/vllm` などの入力は読み取り専用

## 依存パッケージの導入

不要。v5 は `venv_sst` にあるパッケージだけで動く。足りないパッケージが出たときは、入れずに依頼者へ伝える。

## 環境設定

- 環境変数: 不要（検証スクリプトは `CUDA_VISIBLE_DEVICES=""` と `device="cpu"` を自分で固定する）
- 設定ファイル: `v5/pytest.ini`（`-p no:hydra_pytest` で、壊れた hydra の pytest プラグインだけを止める）

## ビルドコマンド

コンパイルが要る成果物はない（純粋な Python）。代わりに、構文の確認として次を実行する。

```
venv_sst/bin/python -m compileall -q v5/src v5/scripts v5/tests
```

## ビルドの確認

1. 上のコマンドが終了コード 0 で終わる
2. `venv_sst/bin/python v5/scripts/run_pipeline.py --dry-run` が、6 段階（inputs、v1_v9、v10_v11、tables、plots、ablation）のコマンドを表示し、何も書かずに終わる

## よくある問題

- `python -m pytest` が `Could not deserialize ATN with version` で止まる: hydra の pytest プラグインの不一致。`v5/pytest.ini` があれば止まらない。`v5` の外から実行すると設定が効かないので、ワークスペース直下から実行する
- `--execute` が拒否される: `--approved-by-user` が必要。実データの実行は、依頼者の許可を得てから行う
