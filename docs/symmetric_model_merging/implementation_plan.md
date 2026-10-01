# 論文準拠の対称マージ構成への修正計画

5つの感情分析タスク（imdb, yelp, rt, sst2, amazon）はすべて独立して `roberta-base` からファインチューニングされているため、マージの基準点（ベースライン）を `roberta-base` とし、5タスクすべてをマージ対象とする「対称なマージ構成」へ修正します。

## ユーザーレビューが必要な事項
ありません。

## 未解決の質問
ありません。

## 提案される変更

### [Component: Configuration and Scripts]

#### [NEW] [fisher_roberta_base_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_base_run.json)
- `roberta-base`（事前学習モデル）に対する Fisher 情報を推定するための設定ファイルを新規作成します。
- 推定用データセットには `imdb` の train データ（論文の pretraining 設定に準拠）を使用します。

#### [MODIFY] [run_model_merging_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/run_model_merging_pipeline.sh)
- 準備処理フェーズにおいて、`roberta-base` の Fisher 情報推定を実行するステップを追加します。
- マージコマンド（`uncertainty_based_gradient_matching.py`）の引数を修正し、ベースラインモデルを `roberta-base` に、マージ対象を IMDB を含む 5タスクすべてに変更します。
- `scaling_factors_ft` に imdb のデータサイズに対応する `25000` を追加します。

## 検証計画

### 手動確認
1. パイプライン実行スクリプト `./run_model_merging_pipeline.sh` を実行します。
2. マージされたモデルの各タスク上での最終評価が行われ、結果サマリーテーブルが出力されることを確認します。
3. マージ後の精度（Accuracy）が、非対称な構成の時と比較して向上していること、特に `imdb` タスクの性能劣化が解消されていることを確認します。
