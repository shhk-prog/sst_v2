# Task List: flmsec.tex 論文リファクタリングと不整合修正

## フェーズ 1: 構造と主張の一本化（比較評価論文への統一）
- [x] Abstract / Introduction のトーン調整（SST-Merge強振から「偽の安全性を排除する評価枠組みと既存手法の体系的比較」へ主軸を明確化）
- [x] Title / Author / Affiliation の NeurIPS ダミー表記解除・適切な草稿表記への更新

## フェーズ 2: RQと本文・結論の1対1対応強化
- [x] Results 節内に `Answer to RQ1`, `Answer to RQ2`, `Answer to RQ3` を新設
- [x] RQ1（パレート境界・構造差・ドメイン干渉と限界）への直接的解答の記載
- [x] RQ2（符号・振幅ヒューリスティクス vs Fisher/幾何の計算・性能・頑健性トレードオフ）への解答節の整理
- [x] RQ3（データアクセス制約下での Data-Free 手法の有効性と限界）への解答節の整理
- [x] Conclusion 節の主張を抑え、条件依存性（safety+code, safety+medicalでの低下など）を含めた安定したトーンへ書き改める

## フェーズ 3: 数値・表・参照・記法の不整合の解消
- [x] 予備実験表 (`tab:simple_prelim` と `tab:prelim_detail_app`) の同名条件値（`data_free_sst`, `sst` 等）の数値整合性チェックと修正
- [x] `JailbreakBench[2-]` や `\cite{...}` の破損箇所の特定と修正
- [x] `MergeAlign`, `SafeMERGE`, `LED-Merging` などの本文参照キーと 参考文献 (References) リストの対応ズレ修正
- [x] Baseモデル表記、Safety ASR値等の簡易表と詳細表の完全同期

## フェーズ 4: 考察 (Discussion) の断定緩和と論理構造整理
- [x] 「Delta Weightノルム乖離」「FIMスケール不均衡」「Norm Explosion」などの機序記述を「断定」から「仮説的解釈・示唆」へ調整
- [x] 「理論的主張」「経験的観察」「仮説的解釈」の3要素の記述切り分け

## フェーズ 5: 構成整理と限界節 (Limitations) の新設
- [x] Related Work と Methods の記述重複の解消（手法詳細は Methods、位置づけは Related Work）
- [x] Limitations 節の追加（Llama-2-7B中心、評価件数上限320、Classifier依存性、LEDの医療非対応など）
- [x] Raw Pareto AUC と Validity-aware Pareto AUC の定義早期化
- [x] 偽の安全性（Gibberish判定基準、フィルタ規則）の厳密定義追記

## フェーズ 6: 検証と Walkthrough の作成
- [x] LaTeX コンパイル確認 (`xelatex` でのビルド成功、43ページPDF生成確認)
- [x] `walkthrough.md` の作成と保存 (`docs/paper_refactoring_flmsec/walkthrough.md`)
