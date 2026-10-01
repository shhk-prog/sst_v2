# WizardCoderモデルのHugging Faceリポジトリ名修正計画

WizardCoder-Python-7B-V1.0 のHugging Faceリポジトリ名が誤って `WizardLMTeam/WizardCoder-Python-7B-V1.0` と指定されているため、ロード時に 404 エラーが発生します。
これを正しいリポジトリ名 `WizardLM/WizardCoder-Python-7B-V1.0` に修正します。

## User Review Required

> [!NOTE]
> 設定ファイルの修正であり、プログラム of 動作やマージロジックへの影響はありません。

## Open Questions

特にありません。

## Proposed Changes

### Configuration and Script Changes

---

#### [MODIFY] [config.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config.yaml)
- `models.domain_models.code` の値を `WizardLMTeam/WizardCoder-Python-7B-V1.0` から `WizardLM/WizardCoder-Python-7B-V1.0` に修正します。

#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/test_steering_hook.py)
- テスト内で検証するモデル名を `WizardLM/WizardCoder-Python-7B-V1.0` に変更します。

#### [MODIFY] [llama2_sst_experiment.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v2/configs/aaai27/llama2_sst_experiment.yaml)
- `code_model` の値を `WizardLM/WizardCoder-Python-7B-V1.0` に修正します。

#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)
- テスト内で検証するモデル名を `WizardLM/WizardCoder-Python-7B-V1.0` に変更します。

#### [MODIFY] [download_llama2_resources.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/data_prep/download_llama2_resources.py)
- `code` モデルのリポジトリ名を `WizardLM/WizardCoder-Python-7B-V1.0` に修正します。

---

## Verification Plan

### Automated Tests
- 以下のコマンドで、修正後の `steering_hook` テストが正常に通過することを確認します。
  - `python -m unittest v3/scripts/test_steering_hook.py`
  - `python -m unittest v2/scripts/test_steering_hook.py`

### Manual Verification
- 修正後、`eval_safety.py` もしくは `lm_eval` の実行時に 404 Client Error が解消され、モデルが正しくロードされることを確認します。
