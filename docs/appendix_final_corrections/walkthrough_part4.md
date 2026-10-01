# Appendix Final Corrections Part 4: Walkthrough

## 1. 予備実験節の全表の完全復旧と注意書きの追加
以前の自動修正スクリプトにより、主実験の指標で誤って上書きされてしまっていた予備実験のすべての表（詳細平均表、シード別表、$\alpha$スイープ表など）を対象に、バックアップファイル（`flmsec_0818.tex`）の予備実験セクション全体を抽出し、完全に元の状態に復元しました。
これにより、すべての予備実験表が元の3列（`TrustLLM Raw ASR`, `Gibberish Ratio`, `BeaverTails Utility`）の正しいログ数値に戻っています。

また、予備実験の各表の列名を以下の通り統一しました。
`\textbf{TrustLLM Raw ASR (\%)} \quad \textbf{Gibberish Ratio (\(\downarrow\), \%)} \quad \textbf{BeaverTails Utility Score (\(\uparrow\), \%)}`

さらに、当該セクションの冒頭に以下の注意書きを挿入しました。
> 「本節の予備実験は、TrustLLMおよびBeaverTailsを用いた探索的分析である。TrustLLM Raw ASR、Gibberish Ratio、およびBeaverTails Utility Scoreは、主実験で定義したOriginal ASR、Conditional ASR、Valid Response Rate、Valid Safety Rateとは異なる評価パイプラインに基づく。したがって、予備実験の数値を主実験の安全性指標と直接比較しない。」

## 2. 主実験表（MergeAlign）の欠損値理由と計算順序の注記
Table 13（主要merge手法の詳細評価指標）の表注（キャプション）に、以下の2点を明記しました。
- **MergeAlignが`---`となっている理由**: 「MergeAlignは、生成出力の形式が本研究のGibberish判定および安全性評価パイプラインの前提を満たさず、全応答が無効（Valid Response Rateが0\%）となったため、Conditional ASRおよびValid Safety Rateは算出しない。Original ASRおよび有用性指標のみを参考値として報告する。」
- **標準偏差の計算妥当性**: 「Valid Safety Rateは各seedおよび各ベンチマークについて先に算出し、その後にベンチマーク平均およびseed間平均・標準偏差を計算した。」

## 3. AUC記述の表記統一
論文本文中および付録の記述において、「正常応答のみに基づく Validity-aware Pareto AUC」となっていた旧表現をすべて「Valid Safety Rateに基づくValidity-aware Pareto AUC」に置換し、用語の統一を図りました。

## 4. 主実験表（Table 13）の Safety / Utility 分割
可読性を高めるため、元の10列あった Table 13 を以下の2つの表に分割しました。
- **Table A (Safety diagnostics)** (`tab:evaluation_main_alpha=0.6_safety`): Pattern, Method, Safety Ave [Original ASR], Safety Ave [Conditional ASR], Valid Response Rate, Valid Safety Rate
- **Table B (Utility)** (`tab:evaluation_main_alpha=0.6_utility`): Pattern, Method, Math Ave, Code Ave, Medical Ave, General/Inst Ave
（Pythonスクリプトで元の表データと結合指標データを正しくマージし、LaTeXファイルに再出力しています）

## 5. 多重ドメイン（Table 14）のNote明確化
多重ドメインの評価表（`tab:evaluation_main_alpha=0.6_multi`）について、末尾のNote列に `Utility degradation observed` という具体的なラベルを適用し、キャプション内にその定義（「有用性の著しい低下が観測された条件を示す」）を追加しました。

## 6. Case Study表の整理と確認
Case Studyの表（`tab:yugaioutou_rei`）が、ご提示いただいた以下の対応関係（1手法1行）通りになっていることをLaTeXソースレベルで再構成・検証しました。
- `Diagonal SST`: Valid / No / Safe refusal
- `TIES`: Valid / Partial/Yes / Refusal followed by compliance
- `DARE/DELLA`: Valid/Invalid / Undetermined / Repetition/partial refusal
- `Data-Free SST`: Valid / No / Safe refusal
- `Task Arithmetic`: Valid / No / Safe refusal
- `SafeMERGE`: Valid / No / Safe refusal
- `LED-Merging`: Invalid / Undetermined / Prompt repetition

## 7. コンパイル確認
すべての修正適用後、`xelatex` にて `flmsec.tex` をコンパイルし、LaTeXのエラーなしで `flmsec.pdf` が正常に生成できることを確認しました（途中の `\pm` エラーも `$\pm$` へ自動置換して修正済みです）。
