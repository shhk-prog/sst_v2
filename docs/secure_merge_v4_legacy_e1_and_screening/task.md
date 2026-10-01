# タスクリスト: v4 実験計画に基づく Legacy E1 スクリーニングおよびパイプライン構築 (secure_merge_v4_legacy_e1_and_screening)

## 状態凡例
- [ ] 未着手 (TODO)
- [/] 進行中 (IN_PROGRESS)
- [x] 完了 (DONE)

---

## 1. 方針と基盤整備 (Phase 1 完了)
- [x] 1.1 実験計画書 v1.0（E0〜E5）の確定と二層分離方針の確立
  - **Legacy E1**: v3 観測データに基づく大規模スクリーニング（全生成スキップ）
  - **Canonical Production E1**: E0合格の正規化モデルから shortlisted candidates のみを厳密検証
- [x] 1.2 全マージ手法（10手法・120候補）のファイル命名規則を自動吸収する探索・再採点エンジンの構築
- [x] 1.3 暫定判定ラベルの厳密化（`HARMFUL_SIDE_FEASIBLE` および `Top feasible candidates by GSM8K` へ修正）

## 2. Phase 2: 査読検証・Shortlist 確定の5大タスク (進行中)
- [ ] 2.1 **Human Validity 200件のアノテーション・合議・精度評価パイプラインの構築**
  - ブラインドシート（150 random + 50 hard）に対するルールベース vs 人手判定の一致率・Confusion Matrix・F1 算出ツールの実装
- [ ] 2.2 **MATH500 込みの正式 Math Utility ($U_{math} = (\text{GSM8K} + \text{MATH500})/2$) の確定**
  - v3 の各候補から MATH500 スコアを抽出し、複合ユーティリティでのランキングを再確定
- [ ] 2.3 **XSTest (Benign / Over-refusal) Shortlist 8モデル選定と生成パイプラインの整備**
  - 対象: Base, WizardMath, SafetyFT, Linear ($\alpha=0.6, 0.8$), Diagonal SST ($\alpha=0.8, 1.0$), TIES ($\alpha=0.8$)
- [ ] 2.4 **Linear Canonical Behavioral Equivalence Test の実行確認**
  - `test_canonical_equivalence.py` による Linear の完全等価性実証
- [ ] 2.5 **Legacy E1 Final Table の出力と Canonical Production E1 移行ゲート判定**
