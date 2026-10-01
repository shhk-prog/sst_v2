# 論文本文への画像組み込みと考察のアップデート (Walkthrough)

## 修正内容

論文原稿 (`flmsec.md`) の該当セクションに、これまでに調整を重ねた3パネル図を挿入し、内容に沿った考察を記述しました。

### 1. 画像の挿入とキャプション
- `\subsection{臨界点転移と偽の安全性の排除}` 直下に、`![...](pareto_three_panel.png)` で画像を挿入しました。
- キャプション（`*Figure 2: ...*`）内に、以下の重要な注釈を盛り込みました。
  - **パネル(b)のUtilityに関する注記**: "values above 100% indicate utility improvements relative to the $\alpha=0$ model"
  - **パネル(c)のAUCに関する注記**: "Note: The x-axis in panel (c) is truncated to highlight the differences between methods"
  これにより、読者の誤解を防ぎ、査読に対しても堅牢な表現となりました。

### 2. 考察本文のアップデートと整形
- 過去の1パネル時代（「グラフ横軸はUtility(GSM8K Acc)、縦軸はSafety...」）の古い記述を削除しました。
- また、誤って混入していた `###6.2...` などの不自然な見出しテキストを削除しました。
- 3つのパネル(a, b, c)の情報を総合した考察へと書き換えました。
  - **パネル(a)**: 臨界点転移（$\alpha=0.6$ から $\alpha=0.8$ でのASRの激減）とアライメント幾何理論の整合性。
  - **パネル(b)**: その強度においても推論機能（Utility Retention）が高く維持されている事実。
  - **パネル(c)**: 「偽の安全性（完全崩壊）」を排除した、真のValidity-aware Pareto AUCにおけるSST-Mergeの最良のトレードオフ。

## 確認事項
`flmsec.md` の対象セクションが自然な流れで更新され、意図された内容がすべて反映されていることを確認しました。
