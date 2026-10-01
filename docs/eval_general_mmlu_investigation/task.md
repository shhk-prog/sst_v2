# タスク: general_mmlu の評価妥当性調査

## 概要
General ドメインの標準知識評価タスク `general_mmlu` (Hendrycks MMLU) について、評価スクリプト、設定、メトリクス抽出、および実際の評価結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `mmlu` の評価方式 (loglikelihood / 4択対数尤度比較) とプロンプト設定の確認。
2. 実際に生成された評価結果 JSON (各ベースモデルおよびマージモデル) のスコア解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) におけるメトリクス取得処理の正確性の確認。
4. MMLU-Pro や IFEval との差分および正しく評価されているかの判断提示。
