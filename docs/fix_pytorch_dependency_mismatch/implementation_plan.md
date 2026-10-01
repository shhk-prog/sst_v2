# 実装計画: PyTorch 依存関係のミスマッチに伴う NCCL エラーの修正

`import torch` の実行時に `ImportError: /.../libtorch_cuda.so: undefined symbol: ncclCommWindowDeregister` が発生し、評価やファインチューニングの実行がすべて異常終了する問題を解決します。

## ユーザーレビューが必要な項目
特になし。PyTorch とそのファミリー（torchvision, torchaudio）のバージョンを、現在指定されている `2.4.1`（CUDA 12.1）に完全に統一してクリーンインストールし直します。

## オープンな質問
特になし。

## 提案される変更

### 環境構築および依存関係の修正

#### [MODIFY] [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)
- `run_full_pipeline.sh` 自体に変更を加える必要はありませんが、検証と実行前に仮想環境（`venv_sst`）のパッケージ構成をクリーンにする必要があります。

## 検証計画

### 手動確認
1. 仮想環境内で `torch`, `torchvision`, `torchaudio` を `2.4.1` 互換バージョン（`torch==2.4.1+cu121`, `torchvision==0.19.1+cu121`, `torchaudio==2.4.1+cu121`）に統一して再インストールします。
2. `python -c "import torch; print(torch.__version__)"` がエラーなしで実行できることを確認します。
3. パイプラインを再起動し、ログに `ImportError` が出力されないことを確認します。
