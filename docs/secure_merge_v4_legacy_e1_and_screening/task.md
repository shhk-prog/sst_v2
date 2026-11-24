# タスクリスト: Secure Merge v4 実験計画書 Version 2.0 実行追跡 (secure_merge_v4_legacy_e1_and_screening)

## 状態凡例
- [ ] 未着手 (TODO)
- [/] 進行中 (IN_PROGRESS)
- [x] 完了 (DONE)

---

## 1. 全体ロードマップ進捗サマリー (Phase A 〜 Phase K)
- [x] **Phase A: v3 Global Screening (10 methods / 120 legacy candidates)**
  - 全10手法・120候補（126,360生成）の再採点および $U_{math}$ 算出完了
  - 出力: `v4/results/eval/legacy_e1/legacy_e1_math_comprehensive_summary.json`
- [/] **Phase B: Human Validity 200件 ＆ E0 / Canonical Production 準備**
  - 人手評価: 二重盲検シート (`blinded_human_audit_sheet.json`, 150 random + 50 hard) 生成完了、評価ツール (`evaluate_human_audit.py`) 実装完了
  - E0 / Canonical: `wizardmath_7b`, `safety_full_seed42` (vocab=32,000, RoPE=10,000) 整備完了
  - Linear Candidate-Level Equivalence: 291/291テンソル・トークナイザ・Greedy出力 100% 一致実証完了 (`linear_candidate_equivalence_report.json`)
- [x] **Phase C: Seed 42 Development で各手法 1 setting 固定 $\to$ 3-seed へ展開 (30候補確定)**
  - 全10手法の代表設定固定および 3-Seed Mean ± SD 正式表 (`formal_legacy_e1_table.json`, `comprehensive_multi_benchmark_e1_table.json`) 出力完了
- [/] **Phase D: Math Canonical Production (非Linear 9手法 × 1 setting × 3 seeds = 27 candidates + Linear 3 candidates = 30 candidates)**
  - Linear Safety-Patch (3候補: seed 42, 43, 44): FULL_REUSE 適用（再生成不要）
  - 非Linear 9手法 (27候補): canonical sources (`v4/results/models/canonical/`) から再マージ・保存
  - E0 Sanity check（パラメータ形状・vocab=32,000・NaN検証）実施
  - 30 Production candidates 確定
- [ ] **Phase E: 30 candidates + 3 reference models の Gate 2 (XSTest) ＆ 不足ベンチマーク評価**
  - XSTest (200 prompts, 6,600生成): Over-refusal $\le 10\%$, Benign VRR $\ge 95\%$ による Gate 2 検証
  - Safety 4種 (HarmBench, JailbreakBench, StrongReject, WildJailbreak) の不足確認
  - Math 2種 (GSM8K, MATH500)
  - General 4種 (IFEval, MMLU, MMLU-Pro, AlpacaEval2) の不足補完生成
- [ ] **Phase F: Gate 0–4 による正式 Math E1 確定 (Final Table)**
- [ ] **Phase G: E2 重み空間特性解析 (Weight-space characteristics)**
  - 成功モデル vs 3大失敗類型 (Safety Failure, Degeneration Failure, Utility Failure)
- [ ] **Phase H: E3 因果介入実験 (Causal intervention: 2×2対照・同一L2ノルム統制)**
- [ ] **Phase I: SafetyFT 2×2 ablation (Prompt+Response vs Response-only × Fixed vs Diverse refusal)**
- [ ] **Phase J: Code / Medical replication (E0適合モデルで同一10手法展開)**
- [ ] **Phase K: 必要な場合のみ E4 (Proposed merge) $\to$ E5 (Independent validation)**
