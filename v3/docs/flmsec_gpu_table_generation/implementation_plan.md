# 実装計画

## 目的
`flmsec.md` 内のTable 2（`tab:gpu`）の各マージ手法の実測マージ時間とピークGPUメモリを、実際のログ結果から自動的に取得し、表を更新するスクリプトを作成する。

## 実装内容
1. `models/merged/sst_merge_v3_main_*` の各マージ実行ディレクトリにある `runtime_profile.json` をパースし、各手法ごとに以下の数値を収集する。
   - `Average Merge Time`: `total_merge_execution` ステージの `elapsed_sec` を抽出。
   - `Peak GPU Memory`: `total_merge_execution` ステージの `gpu_max_memory_allocated_gb` を抽出。
2. 計算した平均値から、LaTeX形式のテーブル文字列を生成する。
3. `docs/flmsec/flmsec.md` を読み込み、対象のテーブル部分を正規表現で新しいテーブル文字列に置換して上書き保存する。

## ファイル
- `scripts/analysis/generate_gpu_table.py` (新規作成)

## 検証計画
スクリプトを実行し、ターミナル上に正しく集計された表が出力されること、および `flmsec.md` が期待通りに書き換わることを確認する。
