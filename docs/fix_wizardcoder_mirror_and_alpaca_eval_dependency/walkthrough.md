# 修正完了レポート (Walkthrough)

Hugging Face の `WizardLMTeam` 組織モデルの削除による 404 エラー、および AlpacaEval 2 の実行に必要な `alpaca_eval` ライブラリの不足問題を解決するため、モデルの設定変更と依存パッケージの導入準備を行いました。

## 変更内容

### 修正されたファイル一覧

1. **v3 設定ファイル**
   - [config.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config.yaml)
     - `models.domain_models.code` の値をコミュニティミラーリポジトリである `vanillaOVO/WizardCoder-Python-7B-V1.0` に変更しました。

2. **v3 単体テスト**
   - [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/test_steering_hook.py)
     - 許可されるモデル名検証テスト内で、モデル名を `vanillaOVO/WizardCoder-Python-7B-V1.0` に更新しました。

3. **v2 設定ファイル**
   - [llama2_sst_experiment.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v2/configs/aaai27/llama2_sst_experiment.yaml)
     - `code_model` の値を `vanillaOVO/WizardCoder-Python-7B-V1.0` に変更しました。

4. **v2 単体テスト**
   - [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)
     - 許可されるモデル名検証テスト内で、モデル名を `vanillaOVO/WizardCoder-Python-7B-V1.0` に更新しました。

5. **v2 ダウンロードスクリプト**
   - [download_llama2_resources.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/data_prep/download_llama2_resources.py)
     - `code` モデルのリポジトリ名を `vanillaOVO/WizardCoder-Python-7B-V1.0` に更新しました。

## 検証

### 実行推奨コマンド
環境の制約（sandbox not available）により、エージェント側からパッケージインストールおよび評価の実行ができませんでした。
お手数ですが、以下の手順に従ってローカル環境で依存パッケージをインストールし、評価の再実行を行ってください。

#### 1. 依存関係のインストール (AlpacaEval 2 の実行に必要)
`venv_v3` 仮想環境の pip を使用して `alpaca_eval` をインストールしてください。
```bash
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/pip install alpaca_eval
```

#### 2. 単体テストの動作確認
設定変更により、検証テストがパスすることを確認します。
```bash
# v3
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python -m unittest v3/scripts/test_steering_hook.py

# v2
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python -m unittest v2/scripts/test_steering_hook.py
```
