# 安全性データセット自動準備の統合計画

## 概要
`run_phase2.sh` において、安全性学習用・評価用データセットの存在チェックが不足していたため、`safety_combined_eval.json` が欠損した状態でファイントレーニングが評価なしで進行してしまっていました。
他のデータセットと同様に、必要なデータセット（学習用・評価用両方）が1つでも欠けている場合に自動的に `prepare_datasets.py` が呼び出され、データ準備が漏れなく完了するようにリファクタリングします。

## 提案される変更

### [fine_tuning]

#### [MODIFY] [run_phase2.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_phase2.sh)
既存の冗長な個別チェック（Finance、Coding、HarmBench のみ）を廃止し、すべての必要なデータセット（Finance, Coding, Safety, HarmBench, XSTest）を一元的に配列でループチェックする頑健なロジックにリファクタリングします。

## 検証計画

### 手動検証
1. 修正後のチェックロジックが正常に動作するか確認。
2. 実際に `prepare_datasets.py` を呼び出し、欠損していた `safety_combined_eval.json` が正しく生成されることを確認。
