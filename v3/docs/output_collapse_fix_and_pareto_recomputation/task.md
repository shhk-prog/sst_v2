# タスクリスト: コード・医療・多重マージの出力崩壊修正と Pareto Frontier 再計算

## 目的
SST（Selective Sparse Tuning）の主張を単一マージ（safety+math）からコード・医療・多重マージ（safety+math+code+medical等）に拡張し、論文の主要結論とするため、出力崩壊原因を修正し正常応答のみで Pareto frontier を再計算する。

---

## 課題の背景と分析
1. **現状の主張限界**:
   - `safety+math`（2ドメイン単一マージ）では一定の Safety-Utility 制御能力を示している。
   - しかし、`safety+code`, `safety+medical`, および `safety+math+code+medical`（4ドメイン多重マージ）では高い比率で出力崩壊（Gibberish / 無限ループ / PPL暴騰）が発生している。
2. **崩壊応答による評価の歪み**:
   - 崩壊応答（Gibberish）は HarmBench などの有害性判定で「Harmful=No (ASR↓=0%)」と判定されてしまい、「モデルが壊れているだけなのに極めて安全」という偽の指標値（見かけ上の ASR 低下）を生む。
   - その結果、従来の Pareto frontier や AUC 計算が著しく歪んでいる。

---

## タスク一覧

- [x] **Task 1: 出力崩壊のメカニズム解析とデータ分析**
  - [x] 各ドメイン（Code, Medical）および多重マージにおける Gibberish 出力のログ・PPL・Delta Weight ノルムの比較分析
  - [x] Fisher 情報行列（FIM）および Delta Weight のスケール不均衡の特定

- [ ] **Task 2: 出力崩壊を防ぐマージアルゴリズムの修正・正則化**
  - [ ] **Fisher Normalization / Standardized SST**: 各ドメインの Fisher 情報行列のスケール標準化
  - [ ] **Delta Weight Norm Clipping / Rescaling**: 多重マージ時の重み増幅（Norm Explosion）抑制
  - [ ] **Layer-wise Adaptive Scaling**: コード・医療等の高ノルム層に対する適応的スケーリング

- [x] **Task 3: 正常応答（Valid Responses）判定・フィルタリング基準の構築**
  - [x] Gibberish Ratio, Entropy, Repetition, PPL に基づく正常応答フィルタリングロジックの定義
  - [x] 崩壊応答（Invalid）を「ASR=0%」として誤評価させず「評価対象外（Filtered out）」として取り扱う集計パイプラインの実装

- [x] **Task 4: Pareto Frontier & AUC の再計算パイプライン改修**
  - [x] 正常応答率（Valid Response Ratio）を加味した Fair Pareto Frontier 計算スクリプトの作成 (`v3/scripts/analysis/pareto_auc.py` の拡張)
  - [x] 各マージ手法（SST, TIES, DARE, Task Arithmetic, DELLA 等）における正常応答のみの Pareto frontier 再描画と AUC 評価機能の実装

- [ ] **Task 5: 実証実験と検証・ドキュメント作成**
  - [ ] 修正後のモデルでの推論・評価の実行
  - [x] 最終的な `walkthrough.md` および比較レポートの更新・作成
