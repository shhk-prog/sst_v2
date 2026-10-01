# flmsec_hyo.md の生成に向けた実装計画

## 目標 (Goal)
実験結果（JSON）を集計し、論文の `docs/flmsec/flmsec_hyo.md` に LaTeX 風の Markdown テーブルとして結果を出力する Python スクリプト (`docs/flmsec/generate_flmsec_hyo.py`) を作成します。
作成した実験設計書 (`flmsec_experiment.md`) に基づき、予備実験、メイン実験、αスイープ、ベースモデルの各種結果をパースし、Seed (42, 43, 44) での標準偏差を含めた（`Mean ± Std`）形式で分かりやすく整理します。

## User Review Required

- **データ元ディレクトリと差異検証**: メイン・ベースの評価結果について、以下の2つのディレクトリからデータを読み込み、両者を区別して出力します。
  1. `results/vllm/debug_limit320`
  2. `results/normal/debug_limit320`
  これらを比較する形（例えば、Normalの行とvLLMの行を併記する、あるいは差分を示す列を追加するなど）で表を作成しますが、基本的には同じ表構造の中で `Env`（normal / vllm）のような区別カラムを設けて出力する予定です。

## 提案する変更 (Proposed Changes)

### docs/flmsec_table_generation
本タスクの進捗と計画を管理するドキュメント類を作成済み・更新します。
- **[MODIFY]** `docs/generate_flmsec_tables/task.md`
- **[MODIFY]** `docs/generate_flmsec_tables/walkthrough.md`
- **[NEW]** `docs/generate_flmsec_tables/flmsec_experiment.md` (作成済み)

### スクリプトの作成
既存の分析スクリプトの集計ロジックを統合し、`flmsec_hyo.md` に直接出力する専用スクリプトを作成します。
- **[NEW]** `docs/flmsec/generate_flmsec_hyo.py`
  - `normal` 環境と `vllm` 環境の両方のディレクトリを探索。
  - JSONファイルの探索と読み込み、環境ごとのラベル付け。
  - Seed間の平均と標準偏差（`Mean ± Std`）の計算。
  - 予備実験表（TrustLLM, BeaverTails）のマークダウン生成。
  - Main/Base/Alphaスイープ表（Safety, Math, Code, Medical, General の平均）のマークダウン生成。
  - 両環境の差異が視認できる形式（同手法同パターンの normal 行と vllm 行の併記）での出力。
  - 各表に「どのような実験か」を示す適切な題名を付与。

### markdownファイルの生成
- **[NEW]** `docs/flmsec/flmsec_hyo.md`
  - 上記スクリプトを実行することで自動生成される出力ファイル。

## 検証計画 (Verification Plan)

### 自動テスト / 実行
- ターミナルで `python docs/flmsec/generate_flmsec_hyo.py` を実行。
- エラーなく終了し、各ディレクトリ（normal / vllm）からデータが正しく抽出・計算されていることを確認。

### 手動検証 (Manual Verification)
- 生成された `flmsec_hyo.md` の中身を目視確認。
- 各表に予備実験、メイン、αスイープ、Baseである旨のタイトルがついていること。
- normalとvllmの結果が併記され、差分がないか（あるいはどのような差分があるか）が確認できること。
- `±` 記号を用いた標準偏差の形式が適用されていること。
- Latex風で綺麗にフォーマットされていること。
