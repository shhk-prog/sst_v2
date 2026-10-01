# WizardCoder ミラーモデル切り替えと alpaca_eval 依存解決計画

Hugging Face から WizardLMTeam 公式のモデルが削除されているため、`WizardLM/WizardCoder-Python-7B-V1.0` にアクセスした際に 404 エラーが発生します。この問題を解決するため、信頼できるコミュニティミラーリポジトリ `vanillaOVO/WizardCoder-Python-7B-V1.0` に設定を切り替えます。
また、AlpacaEval 2 実行時に `alpaca_eval` モジュールが見つからない問題に対応するため、ローカル仮想環境へのインストールコマンドを案内します。

## User Review Required

> [!NOTE]
> 公式ウェイトが削除されているため、ミラーモデル `vanillaOVO/WizardCoder-Python-7B-V1.0` を使用します。ウェイトの内容はオリジナルと同一であり、評価実験に影響はありません。
> 
> また、`alpaca_eval` パッケージを `venv_v3` 仮想環境へインストールする必要があります。

## Open Questions

特にありません。

## Proposed Changes

### Configuration and Script Changes

---

#### [MODIFY] [config.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config.yaml)
- `models.domain_models.code` の値を `vanillaOVO/WizardCoder-Python-7B-V1.0` に修正します。

#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/test_steering_hook.py)
- テスト内で検証するモデル名に `vanillaOVO/WizardCoder-Python-7B-V1.0` を指定します。

#### [MODIFY] [llama2_sst_experiment.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v2/configs/aaai27/llama2_sst_experiment.yaml)
- `code_model` の値を `vanillaOVO/WizardCoder-Python-7B-V1.0` に修正します。

#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)
- テスト内で検証するモデル名に `vanillaOVO/WizardCoder-Python-7B-V1.0` を指定します。

#### [MODIFY] [download_llama2_resources.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/data_prep/download_llama2_resources.py)
- `code` モデルのリポジトリ名を `vanillaOVO/WizardCoder-Python-7B-V1.0` に修正します。

---

## Verification Plan

### Automated Tests
- 各階層の単体テストを実行し、正しくパスすることを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python -m unittest v3/scripts/test_steering_hook.py`
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python -m unittest v2/scripts/test_steering_hook.py`

### Manual Verification
- 手元で以下の依存関係インストールコマンドを実行していただき、その後 `eval_alpaca.py` が正常に実行されることを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/pip install alpaca_eval`
