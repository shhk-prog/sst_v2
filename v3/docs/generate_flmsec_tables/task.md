# タスクリスト (flmsec_hyo.md の生成と拡張)

- [x] `scripts/analysis/generate_flmsec_hyo.py` の作成・機能拡張
  - [x] 予備実験（TrustLLM, BeaverTails）データのパースと集計機能
  - [x] メイン実験（Safety, Utility）のパースと集計機能
  - [x] Alphaスイープデータのパースと集計機能
  - [x] 抽出したデータを Mean ± Std にフォーマットする処理
  - [x] Markdownテーブルとして出力する処理
  - [x] **進捗（tqdm/ステップ）表示の追加**
  - [x] **`results/vllm/debug_limit320/merged` 配下の `utility_*` ネスト成果物 JSON のパース対応**
  - [x] **Baseモデル評価結果のメイン実験からの分離と独立別表化**
  - [x] **Perplexity 指標（`inst_evol_code`, `inst_medalpaca`）の抽出とテーブル追加**
  - [x] **`flmsec.md` のメインテキスト用「簡易版」表（Markdown / LaTeX）の追加**
  - [x] **`vllm` のみに絞った `flmsec_vllm_hyo.md` / `flmsec_vllm_hyo_latex.md` の生成機能追加**
- [x] スクリプトの実行と検証
- [x] `docs/flmsec/` 下の各結果ファイルが正しく出力されていることの確認

