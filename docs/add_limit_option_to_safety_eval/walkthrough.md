# 修正完了レポート (Walkthrough)

安全性評価（Safety Evaluation）において、有用性評価（Utility Evaluation）と同様に評価サンプル数の制限（`--limit`）を適用できるように機能拡張を行いました。

## 変更内容

### 修正されたファイル一覧

1. **安全性評価スクリプト**
   - [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)
     - 引数パーサーに `--limit`（デフォルト値 `0`、無制限）を追加しました。
     - 読み込んだ有害プロンプトのリストを、`limit` 値が指定された場合（`> 0`）にスライスして件数制限をかけるように修正しました。

2. **実験制御スクリプト**
   - [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
     - `eval_safety.py` を呼び出している4箇所すべてのコマンド引数構築部分に、`"--limit", str(args.limit)` を追加しました。これにより、実験スイープ全体において指定した制限件数が安全性評価にも正しく伝播されます。

## 検証

### 実行推奨検証コマンド
環境の制約（sandbox not available）により、エージェント側でのコマンド実行ができませんでした。
お手数ですが、以下のコマンドをローカル環境で実行し、指定した limit（例: `--limit 2`）の件数分のみ安全性評価が実行されることをご確認ください。

```bash
# WizardMath モデルを用いて harmbench タスクで 2 サンプルの安全性評価を実行
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_safety.py \
  --model_path WizardLMTeam/WizardMath-7B-V1.0 \
  --task harmbench \
  --output_file results/raw/base_WizardMath_harmbench_safety_test.json \
  --limit 2
```
