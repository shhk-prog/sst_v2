# flmsec.tex後半の修正計画

論文「flmsec.tex」の後半部分（付録以降）を、指定された構成案（4役割への整理）と、各項目の修正指示に基づいて改訂します。

## 構成の再編
現在の付録のセクションを以下の順序と名称に再編します。
1. `\section{予備実験の詳細結果}` (維持)
2. `\section{主実験の詳細結果}` (旧：メイン実験の詳細結果と崩壊分析の補足)
3. `\section{偽の安全性の追加分析}` (旧：偽の安全性（推論崩壊）の詳細分析とPareto AUC)
4. `\section{計算資源とデータ要件}` (旧：計算効率とデータ要件の詳細比較)
5. `\section{Seed別およびalpha別の完全結果}` (旧：Detailed Experimental Results and Analysis...)

## 修正内容

### 1. 予備実験の修正（探索的分析への格下げ）
- 本文冒頭に「本節の予備実験は、単一評価器と限定的な有用性指標に基づく探索的分析である。 したがって、本節のRaw ASRを用いて各手法の安全性を比較・順位づけることは目的としない。 本研究の主要な安全性結論は、複数ベンチマーク、有効応答率、および Valid Safety Rateを用いた主実験に基づく。」を追記。
- 表ヘッダの「Gibberish Ratio (崩壊率$\uparrow$ \%)」を「\textbf{Gibberish Ratio (\(\downarrow\))}」に変更。
- 表注に「TrustLLM Raw ASRは当該評価器の出力に基づく未補正スコアであり、 主実験で用いるOriginal ASR、Conditional ASR、およびValid Safety Rateとは 異なる探索的指標である。」を追記。
- 既存手法を「安全ではない」「崩壊している」等と断定する表現を「予備実験では、出力崩壊により単一の自動評価器のスコアが高くも低くも偏る可能性が観察された。」に置き換え。

### 2. 主実験の詳細表
- 表ヘッダを前半の定義と統一します。
    - `Safety Ave [Harmful Content]` → `Safety Ave [Original ASR]`
    - `Filtered ASR` または類似の指標 → `Conditional ASR`
    - `Gibberish Ratio` または類似の指標 → `Valid Response Rate` または明確な `\downarrow` 指標
- 極端なPPLに関する注意書きを本文または表注に追加：「PPLが極端に大きい条件は、専門データへの適合度が低いことに加え、 merge後の出力分布の崩壊を反映する可能性がある。 このため、PPLは通常の有用性比較だけでなく、 モデル崩壊の補助的診断指標として解釈する。」
- 「多重ドメインmerge（safety+math+code+medical）」に関する分析を `\subsection{Multi-domain merging}` として独立させ、主張を限定する文（本研究の2モデルSecure Mergeの結論を、多重ドメイン設定へ直接一般化するものではない）を追加します。

### 3. 偽の安全性分析
- 「相転移」「臨界点」「力学閾値」といった断定表現を削除または「安全性・有用性指標は、探索した離散的な$\alpha$に対して 非線形に変化する傾向を示した...」というマイルドな表現に置き換えます。
- **[DELETE]** 旧AUC表（Table 14: Validity-aware Pareto AUCの比較, SST 0.2935等）を完全に削除します。関連する本文、順位づけ、SSTが圧倒的とする表現も削除します。
- Case Study（Table 15）の前に「本事例は定量的な安全性比較を目的とするものではなく...」の注記を追加。
- Case Studyの表形式を「Method / Output validity / Harmful compliance / Interpretation」の形式（Valid/Invalid等）へ客観化して再構築します。

### 4. 計算資源とデータ要件
- 計算量表（Table 16）の注記に、$K, N, P, C_{\text{backward}}$の定義を追加します。
- Data-Free SSTの行を修正：`Importance / Mask Calc.`を`Task-vector ratio computation and Top-\(k\) selection`とし、`Merge Execution`は`\mathcal{O}(KP)`、`Total Time Complexity`を`\mathcal{O}(KP)` to `\mathcal{O}(KP\log P)`とします。
- GPUメモリ0.00 GBに関する注記「0.00 GBはGPUメモリ消費がゼロであることを意味せず...」を確認・維持します。
- 「Data-Freeは低コスト」という断定を避け、「本実装・測定環境ではmerge時間を短縮した。 ただし、重みを読み込んで座標別処理を行うため、 ピークGPUメモリは必ずしも低下しない。」に変更します。

### 5. Seed別およびalpha別の完全結果
- 冒頭文を指示通りに書き換えます（「本付録後半では、主実験の集約結果を再現可能な形で補足する...」）。
- Seedごとの頑健性に関する強い断定を「seed間の変動は手法およびmergeパターンに依存した。 一部の疎化・サンプリング系手法では大きな変動が観察されたが、 SST系を含む全手法について、特定のドメイン・merge強度では 大きなばらつきが生じ得る。」に弱めます。
- Alpha sweepの「0.4–0.6で崩壊」という一般化を削除し、「探索した$\alpha$の範囲では、性能の変化位置と方向は、 手法およびmergeパターンによって異なった。」に変更します。
- セクション配下の大量のシード別・alpha別テーブルのヘッダについても、可能な限り `[Original ASR]` 等の新名称へ置換します。

## Verification Plan
1. `flmsec.tex` 内を `grep_search` 等で再確認し、旧AUCに関する記述や「臨界点」等の表現が残っていないか検証します。
2. テーブルの列名がすべて統一されたことを確認します。
3. LaTeXコンパイルエラー（Syntax error）が発生しないよう、変更を加えた箇所の文法をチェックします。

これでよろしければ、このプランに基づいてファイルの書き換えを実行します。
