# 評価データセットのプロンプトと応答テキストの保存機能追加計画

`eval_instruction_datasets.py` の実行時において、各評価サンプルの具体的なプロンプト、正解レスポンス、モデルが実際に生成した応答テキスト、および個別の類似度スコアを JSON 結果ファイルに保存する機能を追加します。

## User Review Required

> [!NOTE]
> この変更により、出力される結果 JSON ファイルに詳細な生成ログ (`eval_details` キー) が追加されるため、ファイルサイズが大きくなります。ただし、個別の生成クオリティの検証が容易になります。

## Open Questions

特にありません。

## Proposed Changes

### Script Changes

---

#### [MODIFY] [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py)
- `compute_generation_metrics` 関数を変更し、平均類似度スコアとともに、各サンプルの `prompt`, `target`, `response` (生成された応答), `similarity` スコアの一覧を返すようにします。
- `main` 関数にて、返却された詳細ログを結果の `eval_details` フィールドに追加し、JSON ファイルに書き出すよう修正します。

---

## Verification Plan

### Automated Tests
- なし

### Manual Verification
- 修正後、評価スクリプトをサンプル制限（例: `--limit 2`）で実行し、生成された JSON ファイル内に個別プロンプトと応答のデータが含まれていることを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_instruction_datasets.py --model_path WizardLMTeam/WizardMath-7B-V1.0 --dataset evol_code --output_file results/raw/base_WizardMath_inst_evol_code_test.json --limit 2`
