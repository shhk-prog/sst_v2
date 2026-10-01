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

## 2. Phase 2: 査読検証・Shortlist 確定の5大タスク
- [x] 2.1 **Human Validity 200件の二重盲検シート生成と評価ツールの実装**
  - ランダム150件＋難例50件のブラインドシート (`blinded_human_audit_sheet.json`) 生成完了
  - 評価集計スクリプト (`evaluate_human_audit.py`：Cohen's κ, Precision/Recall/F1) 実装完了
- [x] 2.2 **MATH500 込みの正式 Math Utility ($U_{math}$) および 3-Seed 固定主比較表の作成**
  - 実験計画書に準拠し、Development (seed42) で設定を1つ固定 $\to$ seed 42/43/44 に適用した 3-Seed Mean ± SD 表 (`formal_legacy_e1_table.json`) を出力完了
  - 表名を `Top Candidates Satisfying Harmful-Side Constraints by Combined Math Utility` へ厳格化
- [x] 2.3 **Linear Candidate-Level Canonical Behavioral Equivalence Test の実測検証**
  - `verify_linear_candidate_equivalence.py` により、`canonicalize(v3 Linear α=.6)` vs `v4 新マージ Linear α=.6` の比較を実行
  - 291/291全パラメータ一致、Tokenizer Input IDs一致、Greedy Generation一致率 **100% PASS** を実証
- [/] 2.4 **XSTest (Benign / Over-refusal) Shortlist 8モデル選定と評価実行**
  - 対象: Base, WizardMath, SafetyFT, Linear ($\alpha=0.6, 0.8$), Diagonal SST ($\alpha=0.8, 1.0$), TIES ($\alpha=0.8$)
  - `eval_overrefusal_v4.py` に基づき Benign VRR / Over-refusal を測定し、`HARMFUL_SIDE_FEASIBLE` から正式な `FULL_FEASIBLE` へ昇格
- [ ] 2.5 **Legacy E1 Final Table の確定と Canonical Production E1 / E2 移行ゲート判定**
