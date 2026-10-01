# 修正内容の確認 (Walkthrough): PyTorch 依存関係のミスマッチに伴う NCCL エラーの修正

`import torch` を行った際に発生していた `ImportError: /.../libtorch_cuda.so: undefined symbol: ncclCommWindowDeregister` について、原因の特定と解決方法をまとめました。

## エラーの原因
前回の PyTorch 強制インストール時に、`torchvision` と `torchaudio` のバージョン指定を省略したため、PyTorch 2.5/2.6 用の最新パッケージ（`torchvision==0.20.1`, `torchaudio==2.5.1`）がインストールされてしまいました。
これらが引き込んだ高バージョンの NCCL 依存関係が `torch 2.4.1` と競合し、`ncclCommWindowDeregister`（PyTorch 2.5 以降で使われるシンボル）がロードできずにインポートエラーが発生していました。

## 修正・検証方法（ユーザーによる実行）

IDEコマンドターミナル環境の制約により、こちらから直接環境パッケージの再インストールやスクリプトのバックグラウンド実行が制限されるため、お手数ですが、再度ターミナルから以下の手順を実行してください。

### 1. PyTorch ファミリーのバージョンを 2.4.1 用に統一して再インストール
以下のコマンドを実行し、PyTorch（`2.4.1+cu121`）およびそれに適合する `torchvision`（`0.19.1+cu121`）と `torchaudio`（`2.4.1+cu121`）を強制的に再インストールします。

```bash
# 仮想環境のアクティベート
source /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/activate

# 統一したバージョンを指定して再インストール
pip install \
  torch==2.4.1+cu121 \
  torchvision==0.19.1+cu121 \
  torchaudio==2.4.1+cu121 \
  --index-url https://download.pytorch.org/whl/cu121 \
  --force-reinstall
```

### 2. 動作確認
正しくインストールされたか、以下のコマンドでエラーが出ないか確認します。
```bash
python -c "import torch; print('PyTorch Loaded:', torch.__version__)"
```
※ `PyTorch Loaded: 2.4.1+cu121` とエラーなしで出力されればOKです。

### 3. パイプラインの再起動
問題なければ、パイプラインを再起動します。
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT
nohup ./run_full_pipeline.sh > logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log 2>&1 &
```

実行後は、以下のコマンドでログを監視いただけます。
```bash
tail -f logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log
```
