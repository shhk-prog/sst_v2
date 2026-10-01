# SFTTrainerのAPI変更に伴う修正

`trl` ライブラリのバージョンアップ（v1.4.0）により、`SFTTrainer` のコンストラクタ引数から `dataset_text_field` や `max_seq_length` が削除され、代わりに `SFTConfig` で設定する方式に変更されたようです。これに伴い、学習スクリプトを修正します。

## ユーザーレビューが必要な項目
- 特になし。標準的な `trl` のAPI変更への追従です。

## 提案される変更点

### [v2/scripts/fine_tuning/run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)
- `TrainingArguments` の代わりに `SFTConfig` をインポートし、使用するように変更します。
- `dataset_text_field` と `max_seq_length` を `SFTConfig` の引数に移動します。

## 検証計画

### 自動テスト
- `run_phase2.sh` を再度実行し、`SFTTrainer` の初期化エラーが解消され、学習が開始されることを確認します。
