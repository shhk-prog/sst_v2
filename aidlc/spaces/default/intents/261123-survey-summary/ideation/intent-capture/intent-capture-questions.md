# 意図の把握と整理 — 確認質問

## Sources

- [desc] Initial description: "大規模調査のまとめ"
- [scope] Workflow-selected scope: `poc`.

## Q1. [研究者] まとめる対象の調査はどれですか？

依頼文だけでは対象の調査が特定できません。docs/ には 175 件のトピックがあり、直近は Secure Merge v4 関連（legacy E1・スクリーニング、math パイロット、E0 互換性監査など）、その前は FLMSec / AAAI 論文向けの評価作業が並んでいます。

A. Secure Merge v4 の一連の調査（E0 互換性監査、math パイロット・本番 E1、legacy E1 とスクリーニング、v3 資産再利用監査など）
B. FLMSec / AAAI 論文向けの評価・表作成（v3 系の結果）
C. SST-Merge 全体（v1〜v4）を横断した調査
D. Not yet defined
X. Other (please specify)

[Answer]: X. FLMSEC 論文に使った v3 の大規模調査。論文は v3/論文/FLMSEC、論文に使った結果はすべて v3/results/vllm。調査内容は、様々な merge 手法で secure merge を試し、セキュリティ 1 タスクと特化性能 3 タスクで性能を測ったもの。
**Mode:** chat

## Q2. [研究者] このまとめは誰が、何のために読みますか？

読み手によって、書く粒度と前提知識の置き方が変わります。

A. 自分用の振り返り、次の実験計画の土台
B. 共同研究者・指導教員への報告
C. 論文（本文・付録）に使う材料
D. Not yet defined
X. Other (please specify)

[Answer]: X. 大規模調査の結果から secure merge に最も適した新しい merge 手法を提案するための材料。secure merge の提案論文は v3/論文/DLSP_hiromi2。
**Mode:** chat

## Q3. [研究者] どんな形で仕上げたいですか？

A. docs/<topic>/ 配下の Markdown レポート1本（implementation_plan / task / walkthrough の慣例に沿う）
B. Markdown レポート ＋ 結果表を元データから再生成するスクリプト
C. スライド（発表用）
D. Not yet defined
X. Other (please specify)

[Answer]: B. docs/<topic>/ 配下の Markdown レポート、レポートに加えて v3/results/vllm から表を再生成するスクリプト。v5 フォルダを作り、何を行うフォルダか README に明記した上で作業を進める。
**Mode:** chat

## Q4. [研究者] 何ができていれば「まとめ」として成功ですか？

最後の確認ステップで何を突き合わせるかが、この答えで決まります。

A. 載せた数値がすべて元の結果ファイル・レポートまで辿れる
B. 主要な結論と未解決の課題が短時間で把握できる
C. A と B の両方
D. Not yet defined
X. Other (please specify)

[Answer]: X. 大規模調査の内容を確認し、結果から secure merge に適した要素を抜き出せていること。
**Mode:** chat

## Q5. [研究者] 今回のまとめで「やらないこと」は何ですか？

poc として進める前提で、このまとめに含めない作業を決めておきます。

A. 新しい実験（GPU ジョブ）の実行
B. 論文本文の書き換え
C. A と B の両方
D. None
X. Other (please specify)

[Answer]: X. 新しい実験（GPU ジョブ）の実行や、論文本文の書き換えは行わない。既存の結果は編集しない。
**Mode:** chat

## Q6. [研究者] 今回の到達点はどこまでですか？

「適した要素を抜き出す」ところで止めるか、それを組み合わせた新手法の案まで書くかで、成果物の中身が変わります。

A. 要素の抽出まで（どの merge 手法のどの性質が、セキュリティ維持と特化性能の両立に効いているかの分析）
B. 要素の抽出 ＋ それを組み合わせた新しい merge 手法の設計案（アルゴリズムの文章・擬似コードまで）
C. B に加えて、新手法の実装コード（実行はしない）
D. Not yet defined
X. Other (please specify)

[Answer]: B. 新しい merge 手法の設計案まで出す。それが既存と比べてどこがどう優れている可能性があるか、理論的・実験的数値を用いて説明できるようにする。（追加・Requested Changes Feedback より）一応提案した新しい merge 手法（sst-merge）があるが、大規模調査でうまく他の merge 手法との差が出せなかった。うまくいかなかった理由を結果から理論的、実験的に考察を追加する。
**Mode:** chat

## Q7. [研究者] レポートとスクリプトはどこに置きますか？

「docs/<topic>/ 配下のレポート」と「v5 フォルダで作業する」の両方をいただいたので、置き場所の関係を確認させてください。

A. レポートは v5/docs/<topic>/、表再生成スクリプトは v5/ 配下（v5 の中で完結させる）
B. レポートはリポジトリ直下の docs/<topic>/、表再生成スクリプトなどの成果物は v5/ 配下
C. 両方に置く（v5/ に本体、docs/<topic>/ に作業記録の implementation_plan / task / walkthrough）
D. Not yet defined
X. Other (please specify)

[Answer]: A. v5 の中で完結（レポートは v5/docs/<topic>/、表再生成スクリプトも v5/ 配下）

## Consolidated Summary Confirmation

- 対象：FLMSEC 論文に使った v3 の大規模調査（論文 v3/論文/FLMSEC、結果はすべて v3/results/vllm）。様々な merge 手法で secure merge を試し、セキュリティ 1 タスク・特化性能 3 タスクで測定 [Q1]
- 目的：secure merge（提案論文 v3/論文/DLSP_hiromi2）に最も適した新しい merge 手法を提案するための材料 [Q2]
- 成功条件：調査内容を確認し、結果から secure merge に適した要素を抜き出せていること [Q4]
- 到達点：新しい merge 手法の設計案まで。既存手法に比べどこがどう優れている可能性があるかを、理論と実験数値で説明できるようにする [Q6]
- 追加の考察：既に提案した SST-Merge が大規模調査で他の merge 手法と差を出せなかった理由を、結果から理論的・実験的に考察する [Q6]
- 形式：Markdown レポート ＋ v3/results/vllm から表を再生成するスクリプト。v5 フォルダを作り、README に目的を明記してから作業する [Q3]
- 置き場所：v5 の中で完結（レポートは v5/docs/<topic>/、スクリプトも v5/ 配下）[Q7]
- やらないこと：新しい実験（GPU ジョブ）の実行、論文本文の書き換え、既存結果の編集 [Q5]
- 読み手：依頼者本人と指導教員 [Q8]
- 新手法の採用判断：共同研究者と合議で決める [Q9]
- 報告：定例ミーティングで途中経過を報告する [Q10]

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

前回の仮定（読み手、新手法の採用を決める人、報告の要件）は追加質問 Q8〜Q10 に変換して回答を得たため、成果物に残る仮定はありません。

A. Accept assumptions
B. Convert to follow-up questions

[Answer]: B. Convert to follow-up questions

## Requested Changes Feedback

[Answer]: 一応提案した新しいmerge手法(sst-merge)があるが，大規模調査でうまく他のmerge手法との差が出せなかった．うまくいかなかった理由を結果から理論的，実験的に考察を追加して

## Q8. [研究者] このまとめを読むのは誰ですか？

読み手によって、前提知識の説明をどこまで書くかが変わります。

A. 依頼者本人のみ
B. 依頼者と共同研究者
C. 依頼者と指導教員（共同研究者を含む場合も）
D. Not yet defined
X. Other (please specify)

[Answer]: C. 本人と指導教員

## Q9. [研究者] 新手法を採用するかどうかは誰が決めますか？

設計案の結論をどこまで断定的に書くか（判断材料の提示か、推奨か）がこれで決まります。

A. 依頼者本人が決める
B. 依頼者が案を出し、指導教員が最終判断する
C. 共同研究者と合議で決める
D. Not yet defined
X. Other (please specify)

[Answer]: C. 共同研究者と合議

## Q10. [研究者] 報告の頻度や報告の場に要件はありますか？

A. 特になし（成果物が揃った時点で一度確認すれば十分）
B. 定例ミーティングで途中経過を報告する
C. 締切（学会投稿など）に合わせて仕上げる必要がある
D. Not applicable
X. Other (please specify)

[Answer]: B. 定例で途中報告
