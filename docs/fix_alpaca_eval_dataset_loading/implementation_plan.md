# AlpacaEval データセットロード時のエラー修正計画

Hugging Face `datasets` ライブラリのアップデートに伴い、Pythonロードスクリプトを使用したデータセットの読み込みがサポートされなくなりました。これにより、`tatsu-lab/alpaca_eval` を `load_dataset` で読み込む際に "Dataset scripts are no longer supported" エラーが発生します。
この問題を回避するため、ロードスクリプトを経由せず、直接リポジトリの JSON ファイルを読み込むように修正します。

## User Review Required

> [!NOTE]
> ロード方法を JSON の直接ロードに変更しますが、取得されるデータセットの内容（alpaca_eval の 805 個の評価用プロンプト）は同一であるため、評価結果に影響はありません。

## Open Questions

特にありません。

## Proposed Changes

### Script Changes

---

#### [MODIFY] [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py)
- データセットのロード部分において、最初にリポジトリ上の `alpaca_eval.json` を直接 JSON 形式でロードするように変更し、失敗した場合に従来のロードスクリプト形式にフォールバックするロジックを実装します。

---

## Verification Plan

### Automated Tests
- なし

### Manual Verification
- 修正後、エラーが発生していた評価コマンドを実行し、データセットが正常にダウンロード・ロードされ、スコアの算出が正常に完了することを確認します。
  - `/mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/bin/python v3/scripts/eval_alpaca.py --model_path WizardLMTeam/WizardMath-7B-V1.0 --output_file results/raw/base_WizardMath_alpaca_eval2.json --limit 10`
