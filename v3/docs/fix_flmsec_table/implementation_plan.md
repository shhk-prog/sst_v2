# FLMSEC LaTeX表崩れ修正と vllm 環境削除 計画

本計画は、ユーザーからの要求に基づき、以下の2点を行います。

## 1. 目的
- Anaconda 環境 `vllm` の削除
- `/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/FLMSEC_JP.pdf` の表崩れを解消するための、Pythonスクリプトの修正

## 2. 課題の分析
Pythonスクリプト (`generate_flmsec_hyo.py`) が生成する LaTeX の表コードにおいて、以下の課題が存在し、表の崩れやコンパイルエラーの原因となっていると考えられます。
1. **tabularx環境と R カラム指定子の使用**: 現在 `tabularx` 環境が使用され、列の指定に `R` が使われています。列名が非常に長いため、指定幅(`\textwidth`)に収まりきらず文字が重なったり、折り返しが不格好になるなど、レイアウトが崩れている可能性が高いです。
2. **キャプション内の特殊文字未エスケープ**: `\caption{}` の中にメソッド名（例: `diagonal_sst_main`）が含まれていますが、アンダースコア `_` などの特殊文字がエスケープされておらず、LaTeXの数式モードとして誤認され、コンパイルエラーやレイアウト崩れを引き起こすリスクがあります。

## 3. 提案する修正内容

### A. vllm 環境の削除
`conda env remove -n vllm -y` コマンドを実行し、不要な `vllm` 環境を削除します。

### B. Pythonスクリプト (`generate_flmsec_hyo.py`) の修正
表生成ロジック (`format_latex_table` メソッド) を以下の通り修正します。

#### [MODIFY] `generate_flmsec_hyo.py`
- **キャプション文字列のエスケープ処理追加**:
  ```python
  safe_title = title.replace("_", "\\_").replace("%", "\\%")
  ```
- **`tabularx` から `tabular` + `\resizebox` への変更**:
  表全体を `\resizebox{\textwidth}{!}{ ... }` で囲むことにより、自動的にページ幅に収まるよう縮尺を調整します。これにより、長い列名による表のはみ出しや崩れを防止します。
- **カラム指定子の変更**:
  `R` から標準の `r` (右揃え) に変更し、表の表示を整えます。

## 4. 検証計画
1. `generate_flmsec_hyo.py` を実行して、エラーなく Markdown および LaTeX コードが生成されることを確認します。
2. 生成された LaTeX コードにおいて、`\resizebox` が正しく適用され、キャプション内の特殊文字が適切にエスケープされていることを確認します。

## User Review Required
> [!IMPORTANT]
> - `generate_flmsec_hyo.py` の修正後、生成された表データを `flmsec.md` にどのように反映させるか（手動コピーか、別途コマンドがあるか）について、普段のワークフローがあれば教えてください。特に指定がない場合は、スクリプト実行により自動出力される内容を用いて `flmsec.md` の該当箇所を置換します。
> 
> 上記の計画で問題なければ、「承認 (Proceed)」あるいはそのまま進めるようご指示をお願いします。
