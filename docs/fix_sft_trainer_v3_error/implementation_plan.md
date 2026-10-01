# SFTTrainer の dataset_text_field 引数エラー修正計画

## 概要
`v3/scripts/fine_tuning.py` の実行時に、`SFTTrainer` の初期化部分で以下のエラーが発生しています。
```
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field'
```
これは、使用している `trl` ライブラリのバージョン（v1.7.0等）において、`dataset_text_field` や `max_seq_length` などの設定項目が `SFTTrainer` の直接の引数から削除され、`SFTConfig` （`TrainingArguments` のサブクラス）で定義する仕様に変更されたためです。

本計画では、`SFTConfig` をインポートし、`TrainingArguments` の代わりに `SFTConfig` を使用してこれらのパラメータを設定することで、エラーを解消します。

## Proposed Changes (提案される変更点)

### [fine_tuning.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fine_tuning.py)

#### [MODIFY] [fine_tuning.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fine_tuning.py)
- `trl` から `SFTTrainer` に加えて `SFTConfig` をインポートします。
- `TrainingArguments` で行っていたトレーニング設定を `SFTConfig` に変更し、引数を `dataset_text_field="text"`、`max_length=512` に修正します。
- `SFTTrainer` の引数から `dataset_text_field`, `max_seq_length`, `tokenizer` を削除し、代わりに `processing_class=tokenizer` を指定します。

### [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)

#### [MODIFY] [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
- Step 1 の Fine-Tuning 実行コマンドにおいて、シードごとに異なる出力先を指定するように `--output_dir` 引数を追加します。
  ```python
  # 変更前
  cmd = [
      sys.executable, "scripts/fine_tuning.py",
      "--config", args.config,
      "--seed", str(seed)
  ]
  
  # 変更後
  cmd = [
      sys.executable, "scripts/fine_tuning.py",
      "--config", args.config,
      "--seed", str(seed),
      "--output_dir", f"{config['models']['safety_model_dir']}_seed{seed}"
  ]
  ```

### [merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py)

#### [MODIFY] [merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py)
- 安全モデル（SFTモデル）をロードする際に、渡された `--seed` を用いて、対応するシード専用のディレクトリからロードするように変更します。
  ```python
  # 変更前
  safety_model_path = config["models"]["safety_model_dir"]
  
  # 変更後
  safety_model_path = f"{config['models']['safety_model_dir']}_seed{args.seed}"
  ```

## Verification Plan (検証計画)

### Automated Tests
現在 sandbox terminal を使用した直接のコマンド実行が制限されているため、本修正パッチを適用した状態でユーザー環境にて実行していただき、以下の点を確認します。
- `TypeError` が解消され、正常にトレーニングが開始されること。
- シード値ごとの安全モデル出力フォルダ（`models/safety_lora_seed42` 等）が正常に生成されること。
- マージ実行時に、対応するシードの安全モデルがロードされてマージされること。

### Manual Verification
- 修正コード適用後にスクリプト `run_experiments.py` を実行して、各フェーズが正常に走ることを確認する。

## 履歴 (Revision History)

### 2026-07-03 追記: SFTConfig の引数エラーへの対処
1回目の修正後、`SFTConfig` 初期化時に以下のエラーが発生しました：
```
TypeError: SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'
```
調査の結果、`trl` (v1.7.0等) の `SFTConfig` クラスでは、パラメータ名が `max_seq_length` ではなく `max_length` に変更されていることが判明しました。
そのため、`max_seq_length=512` を `max_length=512` へ修正しました。

### 2026-07-03 追記: SFTTrainer の tokenizer 引数エラーへの対処
2回目の修正後、`SFTTrainer` 初期化時に以下のエラーが発生しました：
```
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'tokenizer'
```
調査の結果、最新の `trl` では `SFTTrainer` の引数 `tokenizer` が `processing_class` に変更されていることが判明しました。
そのため、`tokenizer=tokenizer` を `processing_class=tokenizer` へ修正しました。

### 2026-07-03 追記: シード上書きバグへの対処
シード値ごとの実験において、安全モデルの出力先が一律 `models/safety_lora` となっていたため、シード間で学習結果が上書きされてしまうバグを修正します。
- `run_experiments.py` で `fine_tuning.py` に `--output_dir` 引数を追加（`_seed{seed}` サフィックスを付与）。
- `merge.py` でロードする安全モデルのパスを `_seed{args.seed}` に変更。

