# datasets バージョン問題と警告抑制の修正計画 (Fix datasets version and suppress warnings)

## 概要

`alpaca_eval` 実行時に `RuntimeError: Dataset scripts are no longer supported, but found alpaca_eval.py` というエラーが発生し、判定処理が失敗しました。これは `datasets` パッケージのバージョン（3.x以降）が新しすぎるため、古いデータセットロードスクリプトが読み込めなくなっていることが原因です。

本計画では、仮想環境内の `datasets` バージョンを `2.19.2` にダウングレードし、併せて `eval_alpaca.py` 実行時の `max_new_tokens` に関する警告を抑制します。

---

## 提案する変更・対応内容

### 1. 依存関係のダウングレード
仮想環境内の `datasets` パッケージをダウングレードします。
AIのコマンド実行環境に制限があるため、ユーザーのターミナルにて以下のコマンドの実行をお願いします。
```bash
./venv_v3/bin/pip install "datasets==2.19.2"
```

### 2. [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py) の警告抑制
`model.generate()` において、`max_length` と `max_new_tokens` の両方が設定されているという警告（`Both max_new_tokens and max_length seem to have been set.`）を抑制するため、`generate()` 呼び出し時に `max_length=None` などの指定を行うか、引数を調整します。

---

## 検証計画

ダウングレードおよびコード修正後、再度以下のコマンドを実行し、エラーおよび警告が発生せずに評価結果が保存されることを確認します。
```bash
./venv_v3/bin/python scripts/eval_alpaca.py \
  --model_path models/safety_lora_seed42 \
  --output_file results/raw/base_SafetyFT_alpaca_eval2.json \
  --limit 10
```
