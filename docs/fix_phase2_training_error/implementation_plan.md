# Fine-tuning Phase 2 実行エラーの修正計画

`run_phase2.sh` の実行時に発生していると思われるエラーを修正します。調査の結果、以下の主要な問題が特定されました。

## 特定された問題点
1. **CUDAバージョンの不一致**:
   - 仮想環境 (`venv_sst`) にインストールされている PyTorch は CUDA 13.0 用 (`2.11.0+cu130`) ですが、システムの NVIDIA ドライバー/CUDA バージョンは 12.4 です。
   - これにより `torch.cuda.is_available()` が `False` となり、GPU を使用した学習ができません。
2. **Hugging Face 認証の設定不足**:
   - `src/.env` に `HUGGINGFACE_HUB_TOKEN` が設定されていますが、実行スクリプト (`run_phase2.sh`) および Python スクリプト (`run_lora_ft.py`) でこの `.env` ファイルが読み込まれていません。
3. **出力先パスの問題**:
   - ユーザーが実行したコマンドの出力リダイレクト先 `/mnt/nas/home/hiromi/src/sst_v2/docs/sst_experiment` が作成されていない、またはパスに問題がある可能性があります。

## ユーザーへの確認事項
> [!IMPORTANT]
> - PyTorch の再インストールには時間がかかる場合があります。
> - `src/.env` のトークンが Llama-3 へのアクセス権を持っていることを前提とします。

## 提案する変更内容

### 1. 環境の修正
#### 仮想環境での PyTorch 再インストール
CUDA 12.4 に対応した PyTorch を再インストールします。
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
```

### 2. スクリプトの改善
#### [MODIFY] [run_phase2.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_phase2.sh)
- `src/.env` を読み込み、`HUGGINGFACE_HUB_TOKEN` を環境変数として export する処理を追加します。
- ログ出力を改善し、標準エラー出力もリダイレクトするように案内します。

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)
- GPU が利用可能かどうかをチェックし、利用できない場合は明確なエラーを出すようにガードを追加します。
- `python-dotenv` がインストールされている場合は、スクリプト内でも `.env` を読み込むようにします。

## 実行手順
1. 仮想環境の修正 (PyTorch の再インストール)
2. Hugging Face 認証の確認
3. 実行コマンドの修正と再実行

## 検証計画
- `python -c "import torch; print(torch.cuda.is_available())"` が `True` になることを確認。
- 小規模なデータセットまたは 1 ステップのみの実行で、モデルのロードと学習の開始を確認。
