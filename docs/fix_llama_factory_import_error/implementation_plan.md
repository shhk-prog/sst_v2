# LLaMA-Factory 起動時インポートエラーの修正計画（更新版）

`transformers` のアップグレードに伴い、PyTorch 2.4.1 ととの不整合による `ModuleNotFoundError: No module named 'torch.distributed.tensor.device_mesh'` が発生しました。

PyTorch のバージョンを 2.5 以上にアップグレードすると、環境内の `vllm` や `xformers` などのコンパイル済み依存パッケージが正常に動作しなくなる二次災害のリスクが極めて高いため、**PyTorch 2.4.1 を維持したまま解決するアプローチ**に変更します。

具体的には、LLaMA-Factory を PyTorch 2.4.1 や旧バージョンの transformers と互換性のある安定版である **`v0.9.0`** にチェックアウトし、依存関係を再設定します。

## ユーザーの確認・作業が必要な事項

> [!IMPORTANT]
> LLaMA-Factory ディレクトリで安定版タグ `v0.9.0` にチェックアウトし、再度依存関係パッケージを適用していただく必要があります。
> 以下のコマンドを順番に実行してください。
> 
> **実行していただきたいコマンド:**
> ```bash
> # 1. LLaMA-Factory を v0.9.0 にチェックアウト
> cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT/LLaMA-Factory
> git checkout v0.9.0
> 
> # 2. 仮想環境をアクティベートして依存関係を強制再適用
> source /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/activate
> pip install -e ".[torch,metrics]" --force-reinstall
> ```

## 提案する変更内容

すでに各学習スクリプト (`run_model*.sh`) への `set -e` の追加は完了しています。
追加のソースコード変更はありません。

## 検証計画

### 手動検証
1. ユーザー環境にて上記のダウングレード・再適用を実行します。
2. LLaMA-Factory が正常に起動できるか、以下のコマンドを実行して確認します。
   ```bash
   source /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/activate
   llamafactory-cli --help
   ```
   エラーが発生せず、ヘルプメッセージが表示されれば正常に修正されています。
3. その後、全体のパイプライン（`run_full_pipeline.sh`）を実行し、学習および評価が正常に動作することを確認します。
