# タスク: medical_pubmedqa の評価妥当性調査

## 概要
Medical ドメインの文献回答ベンチマーク `medical_pubmedqa` (bigbio/pubmed_qa) について、評価パイプライン、評価方式 (`multiple_choice` / 3択対数尤度比較)、メトリクス抽出、および実際の評価結果 JSON データを多角的に調査し、正しく評価が行われているかを検証する。

## 目標
1. `pubmedqa` の評価タスク構造と `multiple_choice` (`yes`/`no`/`maybe` の対数尤度比較) 判定動作の確認。
2. 各ベースモデル (MedAlpaca, SafetyFT, WizardMath, WizardCoder) の評価結果 JSON データの比較解析。
3. 集計スクリプト (`pareto_auc.py`, `generate_tables.py`) における `acc,none` の読み込み検証。
4. 正しく評価されているかの最終判断の提示。
