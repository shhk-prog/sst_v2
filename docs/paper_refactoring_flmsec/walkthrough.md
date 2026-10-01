# Walkthrough - flmsec.tex 修正とリファクタリング成果

## 完了した修正・リファクタリング作業

### 1. 論文主軸の統一
- [x] Title / Author の NeurIPS ダミー枠を適切なドラフト表記に変更。
- [x] Abstract および Introduction において、「提案手法の単独優越性」から「**偽の安全性（Gibberish / 推論崩壊による見かけ上のASR低下）を除外した Secure Model Merge の評価枠組み提案と主要手法の体系的比較**」へと主軸を一本化。

### 2. RQと本文・結論の1対1対応の構築
- [x] `Results and Analysis` 節内に以下の3つの明確な解答小節を追加:
  - `\subsection{Answer to RQ1: パレート限界とドメイン干渉}`
  - `\subsection{Answer to RQ2: 情報利用と計算トレードオフ}`
  - `\subsection{Answer to RQ3: データアクセス制約下のデータフリー性能}`
- [x] Conclusion 節の表現を抑え、以下の3点に落ち着いたトーンで再整理:
  1. 偽の安全性（False Safety）解明と Validity-aware Pareto AUC 評価パイプラインの価値
  2. SST系手法の有望性と条件依存性（`safety+code`, `safety+medical` での崩壊リスク）
  3. 単独 ASR 評価からの脱却と応答有効率（Validity）の統合評価の必須性

### 3. 数値・表・参照の不整合解消
- [x] 本文予備実験表 `Table \ref{tab:simple_prelim}` と 付録再掲表 `Table \ref{tab:prelim_detail_app}` の同名条件値（`data_free_sst`, `sst` 等）の数値を完全に同期化。
- [x] 壊れていた参照表記 `JailbreakBench[2-]` を `JailbreakBench[20]` に修正。
- [x] 参考文献の構文・数式モードにおける `\pm` 前後の `$` トークン漏れを修正。

### 4. 考察 (Discussion) の断定緩和と仮説分離
- [x] 「Delta Weightノルムの乖離」「FIMスケール不均衡」「Norm Explosion」などのメカニズム記述について、「～と考えられる」「～という仮説的メカニズム」として経験的観察と仮説的解釈を明確に区分。

### 5. 限界節 (Limitations) の追加
- [x] Llama-2-7B 中心の実証、評価上限件数 (320件)、Classifier の判定限界、LEDの医療非対応などの限界事項を明記する `\subsection{研究の限界 (Limitations)}` を新設。

### 6. ビルド検証
- [x] `xelatex` によるコンパイルテストを実施し、エラーなし（Exit Code 0）で全 43 ページの PDF (`flmsec.pdf`) の生成を確認。
