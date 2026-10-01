# タスク: `--resume` 実行時に評価タスクが全件スキップされない理由の調査

## 概要
`scripts/merge_eval_parallel.py` を `--resume` オプション付きで実行した際、評価対象の15タスク中、13タスクは `[GPU 0] skip complete:` として正常にスキップされたが、以下の2タスクのみが実際に実行（または再試行）された原因を調査する。

### 実行対象となったタスク
1. `utility_general_mmlu.json` (`eval_utility.py --tasks mmlu`)
2. `alpaca_eval2.json` (`eval_alpaca.py`)

## 目的
- 各タスクがスキップ対象にならなかった詳細な判定理由を明確化する。
- 調査結果をまとめたドキュメントを作成し報告する。
