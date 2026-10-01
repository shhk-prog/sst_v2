# Appendix Final Corrections Part 4: Implementation Plan

## 1. 予備実験の詳細表修復と導入文の修正
以前のスクリプトによって `tab:prelim_detail_app` と `tab:prelim_detail_seeds_app` に誤って主実験の指標列が混入してしまったため、バックアップファイル (`flmsec_0818.tex`) から該当の表を抽出し、元の3列（`TrustLLM Raw ASR`, `Gibberish Ratio`, `BeaverTails Utility`）の状態に復元します。
また、予備実験の冒頭に以下の注意書きを挿入します。
> 「本節の予備実験は、TrustLLMおよびBeaverTailsに基づく探索的評価である。ここで報告するTrustLLM Raw ASRおよびGibberish Ratioは、主実験で定義したOriginal ASR、Conditional ASR、Valid Response Rate、Valid Safety Rateとは異なる指標であり、直接比較しない。」

## 2. MergeAlignの欠損値明記の再確認
主実験の表注（キャプション等）に、MergeAlignの指標が `---` となっている理由（「出力形式が本研究の有効応答判定および安全性診断パイプラインの入力要件を満たさなかったため、Conditional ASR、Valid Response Rate、およびValid Safety Rateを算出しなかった」）が確実に記載されていることを確認し、必要があれば修正します。

## 3. Valid Safety Rateの計算順序の注記
主実験の表注に以下の文を追加し、標準偏差の算出方法が妥当であることを示します。
> 「Valid Safety Rateは各seedおよび各ベンチマークについて先に算出し、その後にベンチマーク平均およびseed間平均・標準偏差を計算した。」

## 4. Main Experimentの記述更新
「正常応答のみに基づく Validity-aware Pareto AUC」という旧表現をすべて検索し、「Valid Safety Rateに基づくValidity-aware Pareto AUC」に統一して置換します。

## 5. 主実験表の分割（Safety と Utility）
読みやすさ向上のため、メイン実験表（Table 13等）を以下の2つの表に分割します。
- **Table A (Safety diagnostics)**: Pattern, Method, Original ASR, Conditional ASR, Valid Response Rate, Valid Safety Rate
- **Table B (Utility)**: Pattern, Method, Math Ave, Code Ave, Medical Ave, General/Inst Ave

## 6. 多重ドメインのNoteの明確化
多重ドメインの表（Table 14）において、PPLの異常やUtilityの低下を明確にするため、「Utility変動大」ではなく `PPL instability` や `Utility degradation observed` という具体的なラベルを用い、表注でこれらを定義します。

## 7. Case Studyの表のLaTeX上での確認
Case Studyの表（`tab:yugaioutou_rei`）について、各Methodが1行ずつ存在し、Output validity / Harmful compliance / Interpretation の列が正しく対応していること、および定性的補助分析である旨が明記されていることを確認します。

## Verification Plan
Pythonスクリプトを用いてLaTeXのテキスト置換・表の再構成および復元を行い、実行後に `flmsec.tex` 内の該当箇所を目視またはスクリプトでチェックして、LaTeX構文として正しくコンパイルできる状態か確認します。
