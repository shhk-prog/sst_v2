# タスクリスト

- `[x]` FIM用学習データと重複しない、インデックス1000以降のテストサンプリング設計
- `[x]` 専用評価スクリプト `scripts/eval_instruction_datasets.py` の作成
  - ロス/パープレキシティの計算ロジック
  - テキスト生成結果と正解ターゲット文の類似度（Sequence Similarity）の算出
- `[x]` `scripts/run_experiments.py` への統合（ベースモデル評価および全マージモデル評価）
- `[x]` `scripts/pareto_auc.py` の修正による評価結果（`inst_evol_code`, `inst_medalpaca`）のロード・分析対応
- `[ ]` 動作確認（テストランの実行）
