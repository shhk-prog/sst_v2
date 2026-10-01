# 調査・計画書: Data-Free SST の全ベンチマーク評価整合性検証および修正

## 目的
`data_free_sst` における AlpacaEval 2, Safety ベンチマーク 4 種, および `code_humaneval` (HumanEval) ベンチマークの評価が正確に行われているかを包括的に検証し、修正を実施する。

## 実施した修正内容

### 1. AlpacaEval 2 の修正
- `eval_alpaca.py` のパースロジックを修正し、`leaderboard.csv` から対象モデルの真の勝率を取得するように改修。
- 全 334 個の評価 JSON を正しく更新。

### 2. Safety ベンチマーク 4 種の検証
- HarmBench, JailbreakBench, StrongREJECT, WildJailbreak の全4種について、分類器の正常動作およびパラメータ `alpha` に対する ASR（脱獄率）の綺麗な単調減少トレンド（高い評価整合性）を確認。

### 3. `code_humaneval` (HumanEval) の修正
- **`scripts/pareto_auc.py` の修正**:
  - スコア抽出リスト `preferred_keys` に `"pass@1,create_test"`, `"pass_at_1,none"`, `"pass_at_1"` などを追加。
  - `pass@1` / `pass_at_1` 系統の全キーを柔軟に検索するフォールバックロジックを追加し、集計時に HumanEval や MBPP のスコアが読み飛ばされないように改修。
- **`scripts/eval_utility.py` の修正**:
  - プロンプトの 4 スペースインデントに対し、モデル生成の 3 スペースインデントが結合して発生する `IndentationError`（Python構文エラー）を自動修復する `fix_humaneval_indentation` 関数を追加組み込み。
