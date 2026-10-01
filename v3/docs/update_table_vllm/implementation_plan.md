# 実装計画 (Implementation Plan)

## 背景と目的
`flmsec_standalone_nosst2.tex` 内の「表1：評価前後で解釈が変わる代表例」は、vLLMの最新実験結果と一致していない部分がありました。ユーザーの要望に基づき、この表の数値をvLLMの正しい実験結果に書き換えます。

## 修正内容
1. **vLLMの結果の反映**：
   - `Task Arithmetic (safety+math)` の Conditional ASR、VSR などの数値を、`new_vsr_results.txt` に記載されている最新の数値（CA: 2.48, VSR: 97.44）に更新します。
2. **「Unsafe but functional」の例の差し替え**：
   - 元の表では `LED-Merging (safety+code)` が「Unsafe but functional（Original ASRは低いがCAが高い）」の代表例とされていました。しかしvLLMの最新結果では、同手法のCAは 3.64% と低く、この解釈に合致しなくなっています。
   - そこで、よりこの解釈に適した `Task Arithmetic (safety+code)`（Original ASR: 29.17%, Conditional ASR: 30.53%, VSR: 66.18%）に差し替え、表と本文の記述を更新します。

## 対象ファイル
- `/Users/saki/lab/src/sst_v3/docs/flmsec/flmsec_standalone_nosst2.tex`
