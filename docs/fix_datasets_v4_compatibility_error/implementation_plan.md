# 実装計画: datasets v4 互換性エラー (TypeError) の修正

`lm-evaluation-harness` での評価データロード時に、`datasets==4.8.5` の内部で `TypeError: must be called with a dataclass type or instance` が発生し、評価プロセスが異常終了する問題を解決します。

## ユーザーレビューが必要な項目
特になし。`datasets` のバージョンを 3.x 台にダウングレードしますが、これは `trl` (`>=3.0.0` 要件) と `LLaMA-Factory` (`<=4.0.0` 要件) の両方を満たす安定バージョンとなります。

## オープンな質問
特になし。

## 提案される変更

### 環境構築および依存関係の修正

#### [MODIFY] [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)
- `datasets` のダウングレード処理（`pip install "datasets>=3.0.0,<4.0.0" --quiet`）をパイプライン起動前（Phase -1 内）に追加し、実行環境が確実に 3.x 台になるように保証します。

## 検証計画

### 手動確認
1. `datasets` をダウングレードした環境で、`BaseModel` に対する `lm-evaluation-harness` 評価がエラーにならず実行されることをログで確認します。
