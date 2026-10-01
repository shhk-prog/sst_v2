# 調査・修正完了レポート: general_ifeval の評価検証・修正・クリーンアップ (Walkthrough)

## 1. 実施された修正の要約

### ① Chat Template（プロンプトフォーマット）の明示的適用
- **対象ファイル**: [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)
- **修正内容**:
  - コマンドライン引数に `--apply_chat_template` （デフォルト: `True`）および `--no_chat_template` を追加。
  - `HFLM` モデル初期化時および `build_model_args` 内で `apply_chat_template=True` を明示的に指定。
  - CLI フォールバック時にも `--apply_chat_template` フラグを付与。

### ② 無限ループ・生成テキスト反復の自動カットおよび再判定
- **対象ファイル**: [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py) / [fix_ifeval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fix_ifeval_jsons.py)
- **修正内容**:
  - `fix_ifeval_responses` 関数を新設。
  - 生成レスポンスから不要な停止・指示切替タグ（`[END]`, `[DONE]`, `### Instruction:` 等）を除去。
  - 同一行や同一文節が 2 回以上連続反復（ループ）している部分を検出・切断（Repetition Truncation）。

---

## 2. general_ifeval 結果 JSON のクリーンアップ確認

旧評価条件（Chat Template未適用）で生成された `general_ifeval` の結果 JSON ファイルの全削除が完了しました。

- **クリーンアップ実行結果**: **全 343 件の `general_ifeval` 結果 JSON ファイルをすべて削除完了**
- **最終検証**: `results/` ディレクトリ配下に `general_ifeval` に関連する JSON ファイルが存在しないことを確認（`No general_ifeval JSON files found`）。
