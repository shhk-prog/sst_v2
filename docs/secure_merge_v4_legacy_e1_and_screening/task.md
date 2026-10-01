# タスクリスト: v4 実験計画に基づく Legacy E1 スクリーニングおよびパイプライン構築 (secure_merge_v4_legacy_e1_and_screening)

## 状態凡例
- [ ] 未着手 (TODO)
- [/] 進行中 (IN_PROGRESS)
- [x] 完了 (DONE)

---

## 1. 方針と基盤整備
- [x] 1.1 実験計画書 v1.0（E0〜E5）の確定と二層分離方針の確立
  - **Legacy E1**: v3 の全手法・全responseをスクリーニングとして活用（全生成スキップで安価にtrade-off探索）
  - **Canonical Production E1**: E0合格の正規化モデルから上位候補のみを厳密検証
- [x] 1.2 全マージ手法（10手法）のファイル命名規則を自動吸収する探索・再採点エンジンの構築

## 2. Math Legacy E1 全手法スクリーニング再採点 (Phase A)
- [x] 2.1 全手法自動検出型再採点スクリプト `rescore_all_vllm_legacy.py` の実装
  - 対象: Linear, TIES, DARE, DELLA, SafeMerge, LED, Fisher, MergeAlign, Data-Free SST, Diagonal SST
  - 共通HarmBench Classifier + 厳格Validity (`is_response_valid`) による ASR_all, ASR_valid, VRR, VSR, Math Utility の一括算出完了
- [x] 2.2 全120候補（約126,000生成）の再採点完了および完全サマリー出力 (`v4/results/eval/legacy_e1/legacy_e1_math_comprehensive_summary.json`)
- [x] 2.3 Feasible Region（ASR_valid <= 5%, VRR >= 95%）を満たす有力候補の分析・特定 (`analyze_legacy_e1_screening.py`)
  - 1位: Diagonal SST ($\alpha=1.0$, GSM8K 18.8%)
  - 2位: Linear Safety-Patch ($\alpha=0.8$, GSM8K 16.9%)
  - 失敗類型の特定（LED/MergeAlign: 退化崩壊型、Fisher/Data-Free SST: 安全防御不足型）

## 3. 査読・検証対応準備 (Phase B)
- [x] 3.1 Human Validity 200件（ランダム150件＋難例50件）二重盲検アノテーションセットの生成 (`v4/results/eval/human_audit/`)
- [x] 3.2 上位候補に絞った Benign / Over-refusal（XSTest 200件）最小限生成計画の策定
- [x] 3.3 結果のまとめと `walkthrough.md` の作成
