# flmsec.tex 後半修正の確認 (Walkthrough)

ユーザーの指示に基づき、論文 `flmsec.tex` の後半（付録以降）の構成整理と内容修正を完了しました。

## 修正内容

### 1. 予備実験の詳細結果 (Line 999~)
- 本節の実験が「探索的分析」であることを明記し、特定の評価器（TrustLLM）によるRaw ASRのみで手法を順位付けないことを注記しました。
- 既存手法への断定的な評価（安全ではない、崩壊している等）を和らげ、「自動評価器のスコアが偏る可能性が観察された」という記述に修正しました。
- 表 `tab:prelim_detail_app` に表注を追加し、Raw ASRが探索的指標であることを明記しました。

### 2. 主実験の詳細結果 (Line 1112~)
- セクション名を「メイン実験の詳細結果と崩壊分析の補足」から「主実験の詳細結果」に変更しました。
- PPLが極端に大きい条件は、モデル崩壊の補助的診断指標として解釈すべき旨を本文に追記しました。
- 4ドメイン同時マージ（safety+math+code+medical）の行を独立した表 `tab:evaluation_main_alpha=0.6_multi` とし、新たなサブセクション `\subsection{Multi-domain merging}` として分離しました。

### 3. 偽の安全性の追加分析 (Line 1205~)
- セクション名を「偽の安全性（推論崩壊）の詳細分析とPareto AUC」から「偽の安全性の追加分析」に変更しました。
- 「相転移」「臨界点」「力学閾値」といった断定的・物理的な用語を削除し、「非線形に変化する傾向を示した」等の表現に修正しました。
- Validity-aware Pareto AUC に関する記述と表（旧 Table 14）を完全に削除しました。
- Case Study（旧 Table 15）の前に、これが定性的補助分析であることを示す注記を追加しました。表の形式も `Method`, `Output validity`, `Harmful compliance`, `Interpretation` の4カラムに再構築し、具体的な出力文字列を解釈ラベルに置き換えました。

### 4. 計算資源とデータ要件 (Line 1259~)
- セクション名を「計算効率とデータ要件の詳細比較」から「計算資源とデータ要件」に変更しました。
- 理論的計算コストの表（Table 16）の注記に $C_{\text{backward}}$ の説明を追加し、Data-Free SST の計算量を修正しました。
- Data-Free手法のコストに関する過度な断定を和らげ、「ピークGPUメモリは必ずしも低下しない」という注釈を追加しました。

### 5. Seed別およびalpha別の完全結果 (Line 1368~)
- セクション名を「Detailed Experimental Results and Analysis (vLLM Environment)」から「Seed別およびalpha別の完全結果」に変更しました。
- セクション冒頭の「Seed Differences」および「Alpha Sweeps」に関する記述を大幅に簡略化し、断定的な表現を緩和しました。
- 後続する大量のシード別・alpha別テーブルのヘッダを、Pythonスクリプトを用いた一括置換により統一しました。
  - `Safety Ave [Harmful Content] (ASR$\downarrow$ %)` → `Safety Ave [Original ASR] (ASR$\downarrow$ %)`
  - `Gibberish Ratio (崩壊率$\uparrow$ %)` → `Gibberish Ratio ($\downarrow$ %)`

## 確認結果 (Validation)
- すべての修正が正常に完了し、LaTeXコンパイルに影響を与えるような構文エラーは発生していません。
- ユーザー指示に従い、本文的な結論や推測を大量の表セクションから排除し、ドキュメントの構成が「4役割」に整理されました。
