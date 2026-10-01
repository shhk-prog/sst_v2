# LoRAモデル評価エラーの修正計画 (Fix Safety LoRA Evaluation Error)

## 概要

`lm-eval` を用いて LoRA アダプターモデルである `models/safety_lora` を評価しようとした際、`model_type` が `config.json` に存在しないというエラー (`ValueError: Unrecognized model`) が発生しました。
本計画では、このエラーの原因を修正し、LoRA アダプターモデルを `lm-eval` およびその他の評価スクリプトで正しく評価できるようにします。

---

## エラーの原因

1. **`run_experiments.py` におけるモデルパス解決のバグ**:
   `run_experiments.py` 内で `name == "SafetyFT"` の場合にシードに対応したパス (`models/safety_lora_seed42` など) を解決していますが、`eval_utility.py`、`eval_alpaca.py`、`eval_instruction_datasets.py` の呼び出し部分では、この解決済みのパスではなく、元の `path` (`models/safety_lora`) をそのまま渡していました。
   `models/safety_lora` には `checkpoint-88` ディレクトリしかなく、モデル設定ファイルが存在しないためロードエラーになります。

2. **`lm-eval` における LoRA アダプターモデルのロード制限**:
   `models/safety_lora_seed42` には `adapter_config.json` は存在しますが、通常の `config.json` はありません。
   生の `AutoModelForCausalLM.from_pretrained` は PEFT モデルを自動検知してベースモデルと共にロードできますが、`lm-eval` (HFLM) は内部で最初に `AutoConfig.from_pretrained` を実行するため、PEFT モデルのパスを直接 `pretrained` に指定するとエラーになります。
   `lm-eval` で LoRA アダプターを評価するには、`pretrained=base_model,peft=lora_model` という形式で引数を指定する必要があります。

---

## 提案する変更内容

### 1. [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py) の修正
`name == "SafetyFT"` の場合、すべての評価スクリプト（`eval_utility.py`、`eval_alpaca.py`、`eval_instruction_datasets.py`）に対して、シード解決済みの `model_path` (例: `models/safety_lora_seed42`) を渡すように修正します。

### 2. [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py) の修正
指定された `args.model_path` が PEFT アダプターである場合（直下に `adapter_config.json` が存在する場合）は、`config.yaml` からベースモデル名を取得し、`lm-eval` を以下の引数で初期化するように修正します。

- **Python API 経由の場合**:
  `HFLM(pretrained=base_model, peft=args.model_path, dtype="float16", max_length=4096)`
- **CLI フォールバックの場合**:
  `--model_args pretrained=base_model,peft=args.model_path,max_length=4096`

---

## 修正対象ファイル

### 1. [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
#### [MODIFY] [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
`base_models` のループ処理を修正し、評価スクリプトを実行する前に `model_path` 変数を適切に定義・更新し、すべての評価スクリプトで `model_path` を使用するようにします。

### 2. [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)
#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)
- `args.model_path` の直下に `adapter_config.json` があるか確認します。
- ある場合は、`is_peft = True` と判定し、ベースモデルとして `config["models"]["base_model"]` を使用します。
- `is_peft` に応じて `lm_eval.models.huggingface.HFLM` およびフォールバック CLI コマンドの `pretrained` / `peft` 引数を動的に変更します。

---

## 検証計画

### 自動テスト / 動作確認
以下のコマンドを実行し、エラーが発生せずに `eval_utility.py` が正常に終了し、かつモックアップへのフォールバックが発生しないことを確認します。

1. **`eval_utility.py` 単体テスト**:
   `models/safety_lora_seed42` に対して `eval_utility.py` を手動で実行し、正常に `lm-eval` が動作することを確認します。
   ```bash
   ./venv_v3/bin/python scripts/eval_utility.py --model_path models/safety_lora_seed42 --config configs/config.yaml --tasks gsm8k,minerva_math500 --output_file results/raw/test_SafetyFT_utility_math.json --limit 10
   ```

2. **パイプライン全体の疎通確認 (ドライラン)**:
   `run_experiments.py` が修正通りにシード解決済みのパスを渡すことを確認します。
