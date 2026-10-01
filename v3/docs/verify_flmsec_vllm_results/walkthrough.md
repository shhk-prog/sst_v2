# 修正内容の確認 (Walkthrough)

## 実施内容

1. **Baseモデル結果の追加**
   `flmsec.tex` 内の `\subsection{予備実験（Preliminary Experiment）結果}` セクションの直前に、vLLM環境で生成された最新のBaseモデル評価結果の表（`tab:base_models` および `tab:base_models_seeds`）を挿入しました。これにより、マージ前の基準となる性能を事前に確認できるようになりました。

2. **Appendix表の確認作業**
   - **`tab:prelim_detail_app` （予備実験）**: vLLM実行結果に基づく最新の生成スクリプト（`generate_flmsec_hyo.py`）から出力されたデータと一致していることを確認しました。Baseモデルの結果はスクリプトの仕様上 0.00 として正しく反映されています。
   - **`tab:evaluation_main_alpha=0.6` （メイン実験）**: メイン実験用の詳細評価指標の表として、正しくvLLMの結果が記載されていることを確認しました。
   - **`\label{fig:pareto_three_panel}`**: Paretoのトレードオフ図について、適切に参照設定がなされており、本文中の言及（Section 6 付近）とも整合していることを確認しました。
   - **その他のAppendix表**: 予備実験（TrustLLM/BeaverTails）とメイン実験（その他の指標）のデータが混同されることなく、それぞれ適切なラベル（例：`tab:prelim_...` と `tab:main_...`）で分類されていることを確認しました。
     また、専用のPythonスクリプト（`verify_table_contents.py`）を実行して、`flmsec.tex` 内の全124個のAppendix詳細表の中身が `flmsec_hyo_vllm_latex.md` の出力（vLLMでの結果）と一言一句違わず完全に一致していることを検証・確認しました。

3. **BaseモデルのSeed表示の修正 (追加対応)**
   ご指摘いただいた通り、ベースモデルの中でシードの違い（42, 43, 44）が存在するのは `SafetyFT` モデルのみであるため、`tab:base_models` と `tab:base_models_seeds` 内の `Base (MedAlpaca)` 等について誤って複数シード分として集計・出力されていた行を修正しました。これにより、Seedの違いは `SafetyFT` のみに正しく限定されました。

4. **本実験の設計に関する説明の拡充 (追加対応)**
   `\subsubsection{本実験（Main Experiment）の設計}` 内の「頑健性の検証（3-Seed 統計処理）」の項目について、シードとは具体的に「Safety FT時の乱数シードの違い」であり、同一データで獲得表現が異なる3つの独立したSafetyモデルを用いてマージ手法のばらつきを検証しているという旨を詳細に追記しました。

5. **Pareto分析の3パネル図の更新 (追加対応)**
   `generate_three_panel_plot.py` スクリプトの入力参照先を修正し、最新のvLLM結果ファイル（`flmsec_hyo_vllm_latex.md`）からパースするように調整した上で再実行しました。これにより、`flmsec.tex` 内で参照されている `pareto_three_panel.png` がvLLMベースの正しい結果に基づく図に更新されました。

6. **merge手法の詳細（提案手法 SST / Data-Free SST の数理解説と関連研究）の追加 (追加対応)**
   `flmsec.tex` 内の `\section{ベースライン手法の詳細}` を `\section{merge手法の詳細と関連研究}` に変更し、`AAAI.md` の記述に基づいた提案手法の詳細な解説および関連研究との比較を追加しました。
   - **関連研究と引用表記**: FIM-Merging や DF-Merge 等の既存手法の文献を追記し、SSTが反復最適化を要さない要素単位の制御であることの新規性を明記しました。引用は `flmsec.tex` のフォーマットに合わせて、全て `[Number]` 形式で統一しました（例: TIES[5], DARE[6], FIM-Merging[16]）。また、ユーザーの指示に基づき、General Model Mergingの文脈でMergeKitの引用（`MergeKit[43]`）を追加しました。
   - **SST**: Safety Tax と Gain の競合を一般化固有値問題（GEVP）として捉え、対角近似したFisher比率（$\lambda_i = \frac{f_{h,i}}{f_{b,i}+\varepsilon}$）を用いた Hard/Soft Masking および Coordinate-wise Interpolation の定式化を詳述しました。
   - **Data-Free SST**: キャリブレーションデータを不要にするため、タスクベクトル（アダプター差分）の二乗値 $\phi_{t,i} = (\Delta_{t,i})^2$ をFisher対角成分のランキングSurrogateとして用いる理論的根拠（有用性の獲得ベクトルに対するペナルティ）を追記しました。
   - **付録の参照修正**: 本文中でハードコードされていた付録への参照（付録A, B, C等）について、Appendix側の各セクションに `\label` を付与した上で、本文からは `付録\ref{app:target_models}` 等の形式による動的な参照に全て置き換えました。
   - **Appendix内の引用形式の統一**: Appendix内のモデルやデータセット、評価ベンチマーク（GSM8K[34]、HumanEval[36]、MMLU[40]など）の表記についても、本文と同様に `[Number]` 形式で引用が付与されるように修正しました。

7. **参考文献（References）の補完と本文への引用追加 (追加対応)**
   `AAAI.md` 側に記載されていたものの `flmsec.tex` から漏れていた約28件の参考文献（BERT[44], GPT-3[46], InstructGPT[60], Constitutional AI[61], Loss Surfaces[49]など）を `\section*{References}` セクションにすべて追記しました。
   また、追加した文献が孤立しないよう、`\section{Introduction}` セクションにおける背景・課題の文脈に合わせて適切な箇所で引用（例: `[44, 45, 46]`、`[60, 61]` 等）を行いました。

全ての表のデータソースは `vllm` の結果に統一されています。
