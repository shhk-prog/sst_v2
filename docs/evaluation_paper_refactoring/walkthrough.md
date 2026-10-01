# 修正内容の確認 (Walkthrough)

`flmsec_standalone.tex` を「提案論文」のフォーマットから「評価論文」としての構成へ修正する作業が完了しました。ユーザーの要望に沿って、以下の主要な変更を加えています。

## 1. 評価指標 (Terminology) の統一
- 導入部および評価指標のセクションにおいて、`Original ASR`, `Conditional ASR`, `Valid Response Rate (VRR)`, `Valid Safety Rate (VSR)` の定義を明確化しました。
- 原稿全体の `Filtered ASR` を `Conditional ASR` に置換し、表記の揺れを統一しました。
- 重複して表示されていた `Safety Ave [Harmful Content]` について、`[Original ASR]` と実質的に同義であったため、テーブルから統合・削除を行い、表記をスッキリさせました。

## 2. Validity（応答有効性）判定規則の厳密化
- `HarmBench Classifier` は主に「意味的な安全性」の分類器であり、無効応答自体を検証するものではないというユーザーからの指摘を反映しました。
- 評価プロトコルのセクションにおいて、「(i) 空出力、(ii) プロンプトの反復、(iii) 特殊トークンの反復、(iv) 解釈不能な出力」という4つの明示的なヒューリスティックによるValidity判定基準を追記しました。
- 「HarmBench ClassifierによってGibberishが正常に実際の攻撃成功ではない（Safe）と判定された」といった、不正確または誤解を招く記述を削除・修正しました。

## 3. 順位変動表（Ranking Variation Table）の新設
- 実験結果のセクションに、評価指標をOriginal ASRのみからValidity-aware評価に切り替えたことで手法の順位と解釈がどう変動したかを示す表 (`Table 1`) を新設しました。
- 再分類された条件数を記述する段落に、プレースホルダーとして `$N, M, K$` を配置しています（後ほど実際の数値を埋め込んでください）。
- 再評価後の4分類 (`Validly safe`, `False safe`, `False unsafe`, `Unsafe but functional`) を整理するLaTeXテーブルを追加しました。

## 4. 構成と背景の整理・拡充
- `\section{関連研究}` を `\section{関連研究と比較対象}` に変更し、各Merge手法（TIES, DARE, MergeAlign, AlignMerge等）のメカニズムをより詳細に記述しました。SST-Merge系の手法をあくまでも「局所感度比を用いた客観的な比較対象の1つ」として位置づけています。
- `\section{評価について}` のセクションを拡充し、**予備実験（単一評価器の限界の確認）**と**本実験（Validity-awareプロトコルによる再評価）**の目的・実験条件（用いたモデルやシード値、マージ係数など）を明確に分割して記載しました。
- 考察セクションに、「評価条件やドメインの組み合わせによって全ての評価を両立できる単一の手法は存在しない」という「勝者なし（No Free Lunch in Secure Merge）」の結論を追記しました。

## 5. 結論（まとめ）の補強とアブレーションの枠組み
- `\section{まとめ}` の末尾に、Validity-aware評価がもたらす再分類の意義（MergeAlignのFalse Safe化、Task ArithmeticのValidly Safeとしての再評価など）を強調する段落を追記しました。
- 付録に `Validity-aware評価枠組みの頑健性（Ablation Study）` のセクションを新設し、今後判定閾値や評価モデルを変更した際の感度分析を記述できる枠組みを用意しました。

以上の変更により、原稿は特定のMerge手法の提案ではなく、「Secure Mergeにおける無効応答の課題を指摘し、妥当な評価枠組みを提唱する」評価論文としてのロジックに転換されました。
未定の数値パラメータ ($N, M, K$) 等については、最終的な実験データに基づいてプレースホルダーを置換してください。
