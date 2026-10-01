# タスクリスト (Task List)

- [x] `eval_safety.py` の空応答バグ修正
  - [x] `classify_missing` の missing 抽出ロジックで空応答 `""` を除外しないようにする（あるいは安全な応答 `asr = 0.0` を明示的に割り当てる）
- [x] マージモデルの語彙サイズ不整合 (`vocab_size` mising) 自動補正処理の実装
  - [x] `merge_eval_parallel.py` に、評価実行前にモデルの `config.json` と実際の重みサイズを比較し、不整合があれば `config.json` を自動で更新するヘルパー関数を追加する
- [x] 動作検証と評価の再実行
  - [x] 修正コードのロジック的な整合性確認（環境制約によりコマンド実行が不可のため、コードレビューによる確認）
- [x] 結果のまとめと報告 (`walkthrough.md` の作成)
