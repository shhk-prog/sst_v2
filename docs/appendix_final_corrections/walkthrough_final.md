# Appendix 最終修正完了のご報告

ご指示いただいた最終確認および修正事項（1〜6番、ならびに旧指標・過剰表現の検索・削除）のすべてについて、`flmsec.tex`上の対応を完了いたしました。

## 修正内容

1. **予備実験表のヘッダ方向と表注**
   - 予備実験の詳細表について、列名を以下のように修正し方向を明示しました。
     - `\textbf{TrustLLM Raw ASR (\%)} & \textbf{Gibberish Ratio (\(\downarrow\), \%)} & \textbf{BeaverTails Utility Score (\(\uparrow\), \%)}`
   - 表注に「TrustLLM Raw ASRは予備実験における探索的な評価器出力であり、主実験のOriginal ASRおよびConditional ASRと直接比較しない。」という説明を追記しました。

2. **主実験のMergeAlign欠損理由の明示とN/Aの適用**
   - すべての主実験・パラメータ比較等の表で、MergeAlign手法の該当列（Conditional ASR, Valid Response Rate, Valid Safety Rate）が `---` となっていた箇所を `N/A` に変更しました。
   - メイン評価表の付近（キャプション・表注）に以下の理由を明記しました。
     - 「MergeAlignは、出力形式が本研究の有効応答判定および安全性診断パイプラインの入力要件を満たさなかったため、Conditional ASR、Valid Response Rate、およびValid Safety Rateを算出しなかった。」

3. **主実験の表注の追加**
   - 「Safety Ave [Original ASR]およびSafety Ave [Conditional ASR]は、HarmBench、JailbreakBench、StrongReject、WildJailbreakにおけるベンチマーク単位のマクロ平均である。Valid Response Rateは全安全性評価応答のうち有効応答と判定された割合、Valid Safety Rateは全安全性評価応答のうち有効かつ有害要求非追従と判定された応答の割合である。」という注記を、メイン評価表付近に追記しました。

4. **$\alpha=0$の予備実験の違いに関する注記**
   - 予備実験のセクションに、「予備実験における\(\alpha\)の挙動を、主実験で定義した直接差分型Secure Mergeの\(\alpha\)と同一視しない。」という説明を反映しました。

5. **Case Studyの定性的補助分析の明示とラベル定義**
   - Case Studyの表付近に、「Valid / Invalid は応答が要件を満たしているかを示し、No / Partial / Yes / Undetermined は有害要求への追従度（Harmful Compliance）を示す。」といった定義を追加しました。
   - 本文側にも「本節は定量比較ではなく定性的補助分析である。」と追記しました。

6. **AUCのUtility定義**
   - 対象ドメインのUtility計算に関する記載を以下の内容に完全に置き換えました。
     - 「\texttt{safety+math}ではGSM8KおよびMinerva Math 500の平均を、\texttt{safety+code}ではHumanEvalおよびMBPPの平均を、\texttt{safety+medical}ではMedQAおよびPubMedQAの平均を用いる。多重ドメインmergeではMath、Code、Medicalのドメイン別Utilityを等重みで平均する。PPLおよびSimilarity ScoreはAUCに含めない。」

## 最終検索チェック（旧指標・過剰表現の残存確認）

以下のキーワードについて検索を実行し、不適切な文脈で残っていないことを確認しました。
- `0.2935`, `0.2929`, `0.2914` : 検出なし
- `Safety Ave [Harmful Content]` : 検出なし
- `Filtered ASR` : 検出なし
- `真の安全性`, `相転移`, `臨界点`, `圧倒` : 検出なし
- `保証する` : 「この部分空間が安全性を保証する真の不変集合ではない」「数学的に保証することではなく」といった、手法の限界や前提を説明する適切な文脈でのみ2件使用されていることを確認しました。

## PDFの生成状態について
- 最終PDFコンパイル確認のため `pdflatex`, `lualatex`, `xelatex` でコンパイルを試行しました。
- `xelatex` で正常にコンパイルが通り、Case Studyなどの表組みが途切れずに配置されていることが確認できます。お手元でも最終PDFの出力をご確認いただければ幸いです。

以上でAppendix（`flmsec.tex`）の最終整形作業はすべて完了となります。
