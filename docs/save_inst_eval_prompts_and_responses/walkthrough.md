# 修正完了レポート (Walkthrough)

指示データセットの評価スクリプト `eval_instruction_datasets.py` において、評価統計値だけでなく、具体的な評価サンプルのプロンプト、ターゲット（正解）、モデルが生成した応答、および類似度スコアを JSON 結果ファイルに保存するように機能拡張しました。

## 変更内容

### 修正されたファイル一覧

1. **データセット評価スクリプト**
   - [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py)
     - `compute_generation_metrics` 関数が各サンプルの詳細情報（`prompt`, `target`, `response`, `similarity`）を収集してリストとして返却するよう変更しました。
     - `main` 関数で、このリストを結果辞書の `eval_details` キーとして追加し、JSON ファイルに出力するよう変更しました。

## 検証

### 実行推奨検証コマンド
環境の制約（sandbox not available）により、エージェント側でのコマンド実行ができませんでした。
お手数ですが、以下のコマンドをローカル環境で実行し、生成された JSON ファイルに `eval_details` が含まれ、プロンプトや応答が期待通りに保存されていることをご確認ください。

```bash
# WizardMath モデルを用いて evol_code データセットでの 2 サンプルの簡易評価を実行
/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_instruction_datasets.py \
  --model_path WizardLMTeam/WizardMath-7B-V1.0 \
  --dataset evol_code \
  --output_file results/raw/base_WizardMath_inst_evol_code_test.json \
  --limit 2
```
