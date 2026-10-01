# Task List: 論文の必須修正（AUC、Seed表記、主表、比較条件）

- [ ] 1. Pareto AUCの定義と値の統一
  - [ ] 6.1節の `Pareto AUC` を `Raw Pareto AUC` に修正
  - [ ] 6.3節の `Pareto AUC` を `Validity-aware Pareto AUC` に修正
  - [ ] その他、曖昧な `Pareto AUC` の記述の検索と修正
- [ ] 2. 「3 Seeds Average」表記の修正
  - [ ] 5.4節、6.1節の表タイトル等から「3 Seeds Average」を削除
  - [ ] 「代表的な単一実行（seed=42）」または同等の記載へ変更
- [ ] 3. 主表 (Table 2) の再構成
  - [ ] 既存の列を破棄し、指定された列（Harmful ASR, XSTest, Valid response rate, Valid Safety Rate, GSM8K, HumanEval）に再構成
  - [ ] ユーザー回答に基づく数値の挿入（またはプレースホルダ）
- [ ] 4. 対象手法間の比較条件の明示
  - [ ] 5.4節などに「パレート優先」である旨を追記
