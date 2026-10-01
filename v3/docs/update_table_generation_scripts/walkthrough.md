# Walkthrough: Update Table Generation Scripts

## 概要
`scripts/analysis/generate_flmsec_hyo.py` を修正し、`flmsec.tex` と同一の「Safety表」「Utility表」形式（Conditional ASR, VRR, VSRの指標を含む）でLaTeXコードが出力されるように対応を行いました。

## 変更内容
1. **安全性指標の追加計算処理の実装**:
   - `generate_flmsec_hyo.py` の `extract_safety_harmful_asr` 関数を更新し、JSONファイルから `original_asr`, `conditional_asr`, `vrr` (Valid Response Rate), `vsr` (Valid Safety Rate) を抽出および計算して辞書形式で返すようにしました。
2. **表定義（Headers）の分割**:
   - 元々1つのテーブルとして出力されていた `DISPLAY_HEADERS_MAIN` に加え、`DISPLAY_HEADERS_MAIN_SAFETY` および `DISPLAY_HEADERS_MAIN_UTILITY` を新たに定義し、出力する列を `flmsec.tex` の要件に合わせました。
3. **データ集計処理（`aggregate_main`）の更新**:
   - 辞書形式で返されるようになった安全性指標のリストをパースし、各評価（Original, Conditional, VRR, VSR）ごとの平均と標準偏差を計算するよう処理を書き換えました。
4. **Markdown/LaTeX 出力ロジックの修正**:
   - 「メイン実験 (Alpha=0.6)」の出力部分において、ベースモデル (`Base (...)`) とマージ手法 (`dare`, `della` 等) のデータを結合し、`flmsec.tex` と同一の順序になるよう対応しました。
   - `format_latex_val` の欠損値出力を `N/A` から `---` に変更しました。
   - 最終的に `Safety表` と `Utility表` の2種類のテーブルがセットで出力されるように変更しました。

## 動作確認結果
- venv環境 (`venv_v3`) 上で `generate_flmsec_hyo.py` の実行を行いました。
- 約13,000ファイルの JSON のパースおよび集計が正常に完了し、`docs/flmsec/flmsec_hyo_vllm_latex.md` に結果が出力されることを確認しました。
- 出力された LaTeX のコードは、現在の `flmsec.tex` の表定義と一致しており、列名や値の表現（`---` 等）も正しく反映されていることを確認しました。
