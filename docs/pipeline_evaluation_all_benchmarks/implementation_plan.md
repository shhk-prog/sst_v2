# パイプライン評価結果の調査計画 (Implementation Plan)

本計画は、ユーザーによって実行されたフルパイプライン（BaseModelおよび3つのFTモデルのベンチマーク評価）の結果ログを確認し、各モデルの評価スコアをまとめて分析・考察するための計画です。

## 目的
`logs/full_pipeline_all_benchmarks_ep3.0_bs16_lr2.0e-5.log` の内容を精査し、以下の項目を達成します。
1. 各モデル（BaseModel, model1_math, model2_coding, model3_medicine）がすべての評価フェーズ（Phase 0 〜 3）を正常に完了したことを確認する。
2. lm-evaluation-harness、bigcode-evaluation-harness (MBPP)、TeleQnA などの評価結果スコアを抽出し、比較表を作成する。
3. 各モデルのスコアの変動（特に `model1_math` の TeleQnA 性能の崩壊や、`model2_coding` の挙動など）について技術的な要因を分析・考察する。

## 調査および確認のステップ

### 1. ログ末尾の確認
- パイプラインが途中でエラー終了することなく、最後まで正常に実行完了したかを確認する（完了済）。

### 2. 各モデルのスコア抽出
- **lm-evaluation-harnessの結果**: `minerva_math`, `gsm8k`, `cola`, `mnli`, `mrpc`, `pubmedqa`, `qnli`, `qqp`, `rte`, `sst2` などのタスクのテーブル値を抽出。
- **bigcode-evaluation-harnessの結果**: `mbpp` (pass@1) の結果を抽出。
- **TeleQnAの結果**: カテゴリ別および全体の Final accuracy を抽出。
- **Safety評価の結果**: 評価の実行ステータスを確認。

### 3. 特異なスコア挙動の分析
- `model1_math` の TeleQnA スコアが 4.52% と極端に低い原因を、実際の出力結果ファイル（`TeleQnA_answers.txt`）を参照して特定する（完了済）。
- `model2_coding` や `model3_medicine` の TeleQnA スコアと他タスクのトレードオフについて考察する。

## 検証プラン
- 抽出したデータに基づいて、Markdown形式 of サマリーテーブルを作成し、Walkthroughドキュメントに記録します。
