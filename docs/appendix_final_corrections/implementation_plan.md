# Appendix Final Corrections

本文Appendix（flmsec.tex）における必須修正および推奨修正についての対応計画です。

## User Review Required
この計画書の内容に基づき、修正を進めてよろしいかご確認ください。特に、スクリプトを実行してValid Safety Rate（VSR）の再計算を行い、得られた値をLaTeXに反映する点についてご留意ください。

## Open Questions
特になし。

## Proposed Changes

### `v3/docs/flmsec/flmsec.tex`
1. **MergeAlignの --- の説明**: 表`tab:evaluation_main_alpha=0.6`および多重ドメインの表の注釈として、MergeAlignの評価が全て無効応答（Gibberish等）となったため、Conditional ASRおよびValid Safety Rateが計算できず、参考値のみの記載とした旨を明記します。
2. **Valid Safety Rateの再計算結果の反映**: Pythonスクリプトを修正・実行し、正しい定義（VSR = VRR × (1 - Conditional ASR)）に基づいて再計算された各シードごとのVSRから平均・標準偏差を算出し、表の数値を更新します。
3. **安全性指標の定義と単位**: 表注にSafety Aveの対象（HarmBench, JailbreakBench, StrongReject, WildJailbreakのマクロ平均）とVRR、VSRの定義を追記します。列ヘッダに`(\%)`を追加します。
4. **予備実験と主実験の $\alpha$ の違い**: 予備実験節の冒頭に、$\alpha$ の定義が主実験と異なる旨の指定文言を挿入します。
5. **多重ドメイン表のNote列**: Note列の曖昧な「Utility」表記を削除し、表の下に文章として注釈を移動します。
6. **多重ドメインのPPL列**: 診断用として多重ドメインのPPLを残すため、本文の記述を調整し、必要に応じて補助表の構成を確認します。
7. **Case Study表の対応**: Diagonal SST等の各行が手法名・出力妥当性・危害追従・解釈で1対1に対応するよう調整し、指定文言を本文に追記します。
8. **PPLの定義**: PPLの計算設定（tokenizer, truncation, padding, chat templateの有無等）を付録に明記します。
9. **AUCに関する最終確認**: Endpoint-extended AUCとObserved-range AUCの違いについて、指定された解釈文言を追記します。

### `v3/scripts/analysis/compute_safety_diagnostics.py`
- VSRの計算式が `1 - Conditional ASR` に相当するものになっていたため、各seedごとに `(valid_n - harmful_valid) / total` を計算するように修正します。

## Verification Plan
### Automated Tests
- `compute_safety_diagnostics.py` を実行して数値を出し、正しく標準偏差が算出されていることを確認します。
### Manual Verification
- LaTeXファイルが正しくコンパイルできる状態か確認します。
