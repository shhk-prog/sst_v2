# 実装計画: LaTeX表のフォーマット修正

`flmsec_standalone_nosst2.tex` 内の表のフォーマットに合わせて、`generate_flmsec_hyo.py` の生成コードを修正します。

## 修正内容の概要
現在のPythonスクリプトによる自動生成LaTeXテーブルは、単純な `\begin{tabular}` や `l` `r` 列指定を用いており、`\multirow` 等のセルの結合や表ごとの罫線設定が不足しています。これを対象の `.tex` ファイルの書式に合わせます。

## Proposed Changes

### [generate_flmsec_hyo.py]

#### [MODIFY] `generate_flmsec_hyo.py` (file:///Users/saki/lab/src/sst_v3/scripts/analysis/generate_flmsec_hyo.py)
`format_latex_table` 関数を以下のように修正します。

1. **テーブル環境の初期化**
   - `\begin{table}[H]` を `\begin{table}[htbp]` に変更。
   - `\resizebox{\textwidth}{!}{...}` を削除。
   - テーブルの前処理として `\setlength{\tabcolsep}{3pt}` と `\renewcommand{\arraystretch}{1.06}` を追加。
   - `\begin{tabular}{...}` を `\begin{tabularx}{\textwidth}{...}` に変更。

2. **列指定 (col_spec) の動的生成**
   - ヘッダー (`cols`) を判別して `tabularx` 向けの設定を出力します。
   - `Method`: `>{\raggedright\arraybackslash}p{2.25cm}`
   - `Alpha`, `Seed`, `Pattern`, `Env`: `>{\centering\arraybackslash}p{0.90cm}`
   - 上記以外 (スコア等): `>{\centering\arraybackslash}X`

3. **セルの結合 (multirow) と罫線 (midrule)**
   - DataFrameの反復処理中、`Method`（または基準となる列）が連続する行の数をカウントし、ブロックの先頭行で `\multirow{行数}{*}{Method名}` を出力するようにします。
   - 2行目以降は該当セルを空にして `&` で繋ぎます。
   - `Method` が変わるタイミングで `\midrule` を挿入し、表の視認性を向上させます。

## Verification Plan

### Automated Tests
1. `python /Users/saki/lab/src/sst_v3/scripts/analysis/generate_flmsec_hyo.py` を実行する。
2. 出力された `docs/flmsec/flmsec_hyo_vllm_latex.md` を確認し、`\begin{tabularx}`、`\multirow`、`\setlength` などのフォーマットが意図した通りに出力されていることを確認する。

### Manual Verification
ユーザーに、出力された表形式が `flmsec_standalone_nosst2.tex` で意図されたものと一致しているか確認していただきます。
