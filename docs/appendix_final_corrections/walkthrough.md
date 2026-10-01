# Appendix Final Corrections: Walkthrough

## 実施内容 (Changes Made)

ユーザーの指定された必須および推奨修正リストに従い、`v3/docs/flmsec/flmsec.tex` と `v3/scripts/analysis/compute_safety_diagnostics.py` の修正を行いました。

### 1. `compute_safety_diagnostics.py` の修正
Valid Safety Rate (VSR) の計算が「全応答に対する安全かつ有効な応答の割合」ではなく、「有効応答に対する安全な応答の割合（1 - Conditional ASR）」になっていた問題を修正しました。
`vsr = (valid_n - harmful_valid) / total` に修正し、`seed`ごとのVSRを計算した後に平均と標準偏差を取るようにしました。これにより、標準偏差が正確に反映されるようになりました。修正後、スクリプトを実行して再計算したVSRの値をLaTeXの表に反映しました。

### 2. `flmsec.tex` への反映事項
- **MergeAlignの `---` の説明**:
  Table 13および14のキャプションに、MergeAlignの出力形式がGibberish判定の前提を満たさず全応答が無効（VRR=0%）となったため、Conditional ASRおよびValid Safety Rateが算出できなかった旨を明記しました。
- **主表の安全性指標の対象の定義と単位**:
  Table 13および14のヘッダに `(\%)` や `(\downarrow\%)`, `(\uparrow\%)` などを追加し、キャプション内に `Safety Ave` の対象（HarmBench, JailbreakBench, StrongReject, WildJailbreakのマクロ平均）とVRR、VSRの定義を追記しました。
- **予備実験と主実験の $\alpha$ が違う問題**:
  予備実験節の冒頭に、$\alpha$ の定義が主実験と異なる旨の指定文言を挿入しました。
- **多重ドメイン表の Note 列**:
  Table 14 (多重ドメイン) の `Note` 列を削除し、代わりに表のキャプションに「極端なドメイン性能の低下やPPLの逸脱といった有用性の激しい変動が観測された」旨を文章として追記しました。PPLに関する記述は別の診断指標として言及されています。
- **Case Studyの表と文章追記**:
  定性的補助分析である旨の指定された解釈文言を追記し、表との1対1対応の意図を明確にしました。
- **PPLの定義**:
  PPL計算時のtokenizer、truncation、padding/mask、chat templateの有無に関する設定を付録の記述に追記しました。
- **AUCの解釈の追記**:
  Observed-range AUCとEndpoint-extended AUCの違いについて、「観測範囲外の補完仮定に影響されるため、併せて解釈する。単一のAUC値に基づく一般的な手法順位づけは行わない」という指定文言を追記しました。
- **label重複の解消**:
  `\label{tab:base_models}` と `\label{tab:base_models_seeds}` がそれぞれ2箇所で重複していたため、付録側のラベル名を `\label{tab:base_models_app}` 等に変更して重複を解消しました。

## テスト内容と結果 (What was tested & Validation results)
- スクリプトがエラーなく動作し、VSRが100%スケールで正しく再計算されることを確認しました。
- `flmsec.tex` に対するPythonスクリプトを用いた文字列置換がエラーなく完了し、LaTeX構文として正しい状態であることを確認しました。
- LaTeX内の重複ラベルエラーを解消しました。
