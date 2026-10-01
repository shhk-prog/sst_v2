# 修正内容の確認 (Walkthrough) - LoRAモデル評価エラーの修正

LoRA アダプターモデル (`models/safety_lora_seed42` 等) の評価中に発生していた `ValueError: Unrecognized model` エラーおよびトークナイザーロードエラーの修正が完了しました。

---

## 実施した変更内容

### 1. [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py) の修正
- **問題点**: `name == "SafetyFT"` の場合にシードに対応したモデルパス (`models/safety_lora_seed42` など) を決定しているものの、`eval_utility.py`、`eval_alpaca.py`、`eval_instruction_datasets.py` の呼び出し部分では、このシード解決済みのパスではなく、シードなしのデフォルトパス (`models/safety_lora`) が渡されていました。このディレクトリにはモデル設定ファイルが存在しないため、ロードエラーを引き起こしていました。
- **修正内容**: `base_models` のループの先頭で `model_path` (シード解決済みのパス) を確定させ、そのループ内で呼び出されるすべての評価スクリプトに `model_path` を渡すように統一しました。

### 2. [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py) の修正
- **問題点**: `lm-eval` (HFLM) に LoRA アダプターモデルのパスを直接指定すると、`AutoConfig` を介した読み込み時に `config.json` が見つからずに `ValueError: Unrecognized model` エラーになります。
- **修正内容**:
  - 対象モデルの直下に `adapter_config.json` が存在するかどうかをチェックする処理を追加しました。
  - LoRA モデル (PEFT) であると判定された場合は、ベースモデルのパスを `configs/config.yaml` 内 of `base_model` (`meta-llama/Llama-2-7b-hf`) から取得し、`lm-eval` (HFLM/CLI) の引数として `pretrained=base_model, peft=lora_model_path` の形式で渡すように変更しました。

---

## 検証結果

### 1. `eval_utility.py` の単体テスト実行
手動で以下の検証コマンドを実行し、正常に `lm-eval` 経由での評価が完了することを確認しました。

```bash
./venv_v3/bin/python scripts/eval_utility.py \
  --model_path models/safety_lora_seed42 \
  --config configs/config.yaml \
  --tasks gsm8k,minerva_math500 \
  --output_file results/raw/test_SafetyFT_utility_math.json \
  --limit 10
```

- **生成された結果ファイル**: [test_SafetyFT_utility_math.json](file:///mnt/nas/home/hiromi/src/sst_v2/v3/results/raw/test_SafetyFT_utility_math.json)
  モックアップ結果へのフォールバックを回避し、`gsm8k` および `minerva_math500` の実際の評価メトリクスが正しく算出されて保存されていることを確認しました。

---

## その他：alpaca_eval_out フォルダについて

ご質問いただいた `results/raw/base_WizardMath_alpaca_eval2_alpaca_eval_out` が空の件について調査しました。

### 原因
- `venv_v3` 仮想環境内に `alpaca_eval` モジュールがインストールされていません。
- そのため、[base_WizardMath_alpaca_eval2.json](file:///mnt/nas/home/hiromi/src/sst_v2/v3/results/raw/base_WizardMath_alpaca_eval2.json) の内容には以下のエラーが記録されています。
  `"/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python: No module named alpaca_eval"`
- `eval_alpaca.py` では `alpaca_eval evaluate` コマンドを実行する直前に、出力ディレクトリとして空のフォルダを作成する設計になっているため、コマンドがモジュール未インストールにより即座に失敗した結果、空のフォルダだけが取り残されることになりました。
- **対策**: AlpacaEval 2 の評価を実行したい場合は、仮想環境に `pip install alpaca_eval` を実行してください。
