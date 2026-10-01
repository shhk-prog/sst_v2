# Implementation Plan: 論文 Appendix 表の自動生成化と `\input` 化

## Goal Description
`flmsec.tex` の Appendix 等にハードコーディングされている複数の表について、スクリプト (`/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis` 配下) から実験結果を抽出し、個別の `.tex` ファイルとして書き出して `\input` で読み込む構成に変更します。これにより、実験結果の更新時にハードコードを書き直すことなく、スクリプトを再実行するだけで論文の表が更新されるようになります。

## 構成案
- 表の出力先ディレクトリ: `/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/tables/`

## Proposed Changes

### `v3/docs/flmsec/tables/` ディレクトリ
各種の表を出力するためのディレクトリを新規作成します。

### `generate_flmsec_hyo.py` の修正
現状、全ての表を結合して単一の `flmsec_hyo_vllm_latex.md` に書き出していますが、これを以下のように個別のファイルに分割して保存するよう修正します。
- `tab_base_models.tex`
- `tab_base_models_seeds.tex`
- `tab_prelim_detail_app.tex`
- `tab_evaluation_main_alpha_0.6_multi.tex` (多重ドメインの抽出ロジックを微調整し、該当フォーマットで出力)
- その他の各条件・手法別の表（Seed別、Alpha別）

### `generate_case_study.py` の修正
既に出力している Case Study 表と AUC 表の出力先・ラベルを修正します。
- `tab_yugaioutou_rei.tex` として保存
- `tab_auc_no_interpolation.tex` として保存

### `generate_gpu_table.py` の修正
Markdownファイルの直接置換処理を削除し、LaTeX形式の文字列をそのまま `tab_gpu.tex` としてファイルに出力するよう変更します。

### `calculate_observed_range_auc.py` または関連スクリプトの拡張
- `tab:task-arithmetic-single-point` (Task Arithmetic における唯一の支配されない点) を結果から抽出し、`tab_task_arithmetic_single_point.tex` として出力する機能を追加します。
- `tab:evaluation_yobi_main_GSM8K` (崩壊分析) の表を動的に抽出し、`tab_evaluation_yobi_main_GSM8K.tex` にLaTeX形式で出力する機能を追加します。

### `flmsec.tex` の修正
現在ハードコーディングされている各表（`\begin{table} ... \end{table}`）を削除し、代わりに `\input{tables/XXX.tex}` を挿入します。

## 実行および検証プラン
1. 修正した各スクリプトを `source venv_v3/bin/activate` の環境下で実行します。
2. `tables/` ディレクトリに意図した `.tex` ファイルが生成されていることを確認します。
3. `flmsec.tex` をコンパイル（または記載内容の確認）し、表が正しく読み込まれるかを確認します。

## User Review Required
このプランで進めてよろしいでしょうか？特に、`tab_task_arithmetic_single_point.tex` や `tab_evaluation_yobi_main_GSM8K.tex` の生成ロジックは、既存の出力内容（現状の `flmsec.tex` 内の数値）を再現するように新規実装・修正を行いますが、それで問題ないかご確認ください。
